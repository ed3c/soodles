#!/usr/bin/env python3
"""Report observed experiment cost; never scores or adopts a candidate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DECODER = ROOT / 'evaluator/capture_decoder.py'
spec = importlib.util.spec_from_file_location('capture_decoder', DECODER)
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)


def pin(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def report():
    runs = []
    seen = set()
    for packet in sorted((ROOT / 'host/runs').iterdir()):
        case = packet / 'case.json'
        if not case.exists():
            runs.append({'packet': str(packet), 'status': 'no prepared case', 'cost': None})
            continue
        definition = json.loads(case.read_text())
        run = Path(definition['run_root'])
        if run in seen:
            raise ValueError('duplicate actual run root: ' + str(run))
        seen.add(run)
        paths = {'binding': run / 'binding.json', **{
            key: run / 'raw' / name for key, name in {
                'launch': 'launch.json', 'exit': 'exit.json', 'stdout': 'stdout.bin',
                'stderr': 'stderr.bin', 'task_boundary': 'task-boundary.json',
                'isolation': 'isolation-probe.json', 'profile': 'consumer.sb',
            }.items()
        }}
        entry = {'packet': str(packet), 'run_root': str(run), 'case': pin(case)}
        if not all(p.is_file() for p in paths.values()):
            runs.append({**entry, 'status': 'unsealed or incomplete capture', 'cost': None})
            continue
        try:
            capture = decoder.decode_capture({k: p.read_bytes() for k, p in paths.items()})
        except decoder.EvidenceError as error:
            runs.append({**entry, 'status': 'invalid capture', 'reason': str(error), 'cost': None})
            continue
        cost = decoder.costs(capture)
        result = packet / 'result.json'
        measured = json.loads(result.read_text()) if result.exists() else None
        runs.append({**entry, 'status': 'sealed', 'capture': {k: pin(p) for k, p in paths.items()},
                     'cost': cost, 'result': pin(result) if measured else None,
                     'behavior': measured.get('behavior') if measured else None})
    sealed = [r for r in runs if r['status'] == 'sealed']
    fields = ['input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
              'output_tokens', 'reasoning_output_tokens']
    totals = {}
    for field in fields:
        observations = []
        missing = 0
        for r in sealed:
            usage = r['cost']['whole_turn_usage']
            if not usage:
                missing += 1
                continue
            for event in usage:
                value = (event.get('usage') or {}).get(field)
                if type(value) is int and value >= 0:
                    observations.append(value)
                else:
                    missing += 1
        totals[field] = {'observed_sum': sum(observations), 'missing_observations': missing}
    elapsed = [r['cost']['host_elapsed_seconds'] for r in sealed]
    control_receipts = []
    for path in sorted((ROOT / 'verification').glob('*/receipt.json')):
        value = json.loads(path.read_text())
        control_receipts.append({'receipt': pin(path), 'elapsed_seconds': value.get('elapsed_seconds'),
                                 'exit': value.get('exit')})
    return {
        'scope': 'This experiment only; includes ended comparisons, training and blocked optimizer runs.',
        'authorizes_landing': False, 'decoder': pin(DECODER), 'runs': runs,
        'observed_totals': {'sealed_runs': len(sealed), 'other_runs': len(runs) - len(sealed),
                            'completed_commands': sum(r['cost']['completed_commands'] for r in sealed),
                            'sum_of_run_elapsed_seconds': sum(v for v in elapsed if isinstance(v, (int, float))),
                            'elapsed_missing_runs': sum(v is None for v in elapsed), 'usage': totals},
        'deterministic_control_receipts': control_receipts,
        'unknown': ['coordinator/design model usage', 'unrecorded setup time',
                    'human active time', 'final acceptance cost until its receipt exists'],
        'limitations': ['Elapsed sums are not wall-clock duration when runs overlap.',
                        'Cached input and reasoning tokens may be subsets; fields are never added together.',
                        'Unsealed/missing usage is unknown, never zero.',
                        'No pricing, net saving, break-even or behavior-improvement claim.'],
    }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: report_costs.py NEW_REPORT_PATH')
    target = Path(sys.argv[1])
    with target.open('x') as output:
        json.dump(report(), output, indent=2)
        output.write('\n')
    print(json.dumps({'report': str(target), 'sha256': pin(target)['sha256']}))
