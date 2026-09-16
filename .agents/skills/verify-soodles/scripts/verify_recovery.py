#!/usr/bin/env python3
"""Verify the existing recovery journeys and retain their exact scoped context."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import verify_runtime as runtime

ROOT, SKILL = runtime.ROOT, runtime.SKILL
require = runtime.require

# Behavioral obligations from the existing recipe, not a test-count gate.
# Additional cases are retained. Change these with an admitted behavior change.
REQUIRED_CASES = {
    'delivery': {'prepared_sigkill_resume', 'merge_commit_readback_recovery',
                 'lost_response_and_close_prepare_crash', 'dispatch_gap_unknown', 'concurrent_dispatch',
                 'legacy_unknown', 'head_drift', 'structured_owner_refusal', 'terminal_projection'},
    'base': {'comparison_owner_guidance', 'comparison_identity_before_guidance',
             'old_acceptance_invalidated', 'sigkill_invalidation_and_readmission',
             'offered_and_legacy_unknown', 'concurrent_readmission', 'same_base_supervised_amendment',
             'amendment_preserves_offered_and_legacy_unknown'},
    'cleanup-lock': {'lock_release', 'legacy_unknown', 'consumed_release', 'moved_after_block'},
    'cleanup': {'resume', 'moved_branch', 'foreign_checkout', 'unchanged_attempt', 'legacy_checkpoint'},
}


def journeys(binary):
    return [
        ('delivery', [sys.executable, '-B', 'delivery_oracle.py', '.']),
        ('base', [sys.executable, '-B', 'base_recovery_oracle.py', '.']),
        ('cleanup-lock', [sys.executable, '-B', 'cleanup_lock_oracle.py', str(binary), '.']),
        ('cleanup', [sys.executable, '-B', '-c',
                     'import json,sys; from cleanup_oracle import cleanup_recovery_probe; '
                     'print(json.dumps(cleanup_recovery_probe(sys.argv[1])))', str(binary)]),
    ]


def validate_result(name, result):
    require(isinstance(result, dict), f'{name}.receipt: expected an object')
    require(isinstance(result.get('scope'), str) and result['scope'].strip(), f'{name}.scope: absent')
    # The legacy cleanup producer has no authority field. Supply the wrapper's
    # explicit non-claim without rewriting the original result.
    authority = result.get('authorizes_landing', False if name == 'cleanup' else None)
    require(authority is False, f'{name}.authorizes_landing: expected false')
    cases = result.get('cases')
    require(isinstance(cases, list) and cases, f'{name}.cases: missing or empty evidence')
    require(all(isinstance(c, dict) and isinstance(c.get('case'), str) and c['case'] for c in cases),
            f'{name}.cases: missing case identity')
    require(len({c['case'] for c in cases}) == len(cases), f'{name}.cases: duplicate identity')
    indexed = {c['case']: c for c in cases}
    missing = REQUIRED_CASES[name] - indexed.keys()
    require(not missing, f'{name}.cases: missing required behaviors {sorted(missing)}')
    require(all(len(indexed[key]) > 1 for key in REQUIRED_CASES[name]),
            f'{name}.cases: case names without observations')
    # The owning oracles assert transitions. Here only enforce the receipt
    # obligations already required by the recovery recipe; no count ratchet.
    if name in ('cleanup-lock', 'cleanup'):
        require(result.get('provider_requests') == 0, f'{name}.provider_requests: expected zero')
        require(result.get('zero_residue') is True, f'{name}.zero_residue: not verified')
        require(all(c.get('control') == 'passed' and c.get('zero_residue') is True for c in cases),
                f'{name}.cases: missing passing cleanup evidence')
        controls = result.get('controls')
        require(isinstance(controls, list) and controls and all(
            isinstance(c, dict) and isinstance(c.get('argv'), list) and c['argv'] and
            type(c.get('exit')) is int and isinstance(c.get('stdout'), str) and isinstance(c.get('stderr'), str)
            for c in controls), f'{name}.controls: missing command evidence')
    if name == 'cleanup-lock':
        require(all(c.get('lock_refusal_before_deletion') is True for c in cases),
                'cleanup-lock.lock_refusal_before_deletion: not verified')


def complete(receipt, required):
    verified = [j['name'] for j in receipt['journeys'] if j['status'] == 'VERIFIED']
    require(len(verified) == len(required) and set(verified) == set(required),
            'journeys: incomplete or duplicate verification')


def drive(binary, output):
    binary, output = runtime.preflight(binary, output)
    output.mkdir(parents=True)
    planned = journeys(binary)
    receipt = {'schema': 1, 'feature': 'delivery-recovery', 'classification': 'FAILED',
               'authorizes_landing': False, 'trace': [],
               'journeys': [{'name': name, 'status': 'NOT_RUN'} for name, _ in planned],
               'cleanup': {'verified': False},
               'counter_scope': 'Driver-issued commands, including the nested runtime driver. Oracle-internal commands and Agent discovery are excluded; their available raw results are retained.',
               'non_claims': ['Agent skill consumption', 'Agent path-cost reduction', 'live provider delivery',
                              'Agent liveness', 'feedback injection', 'production scheduling']}
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ}

    def command(argv, kind, purpose):
        event = {'argv': [str(x) for x in argv], 'kind': kind, 'purpose': purpose,
                 'exit': None, 'expected_exit': 0, 'stdout': '', 'stderr': ''}
        receipt['trace'].append(event)
        started = time.monotonic()
        try:
            result = subprocess.run(event['argv'], cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                    text=True, capture_output=True, timeout=30)
            event.update(exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired as exc:
            for field, value in (('stdout', exc.stdout), ('stderr', exc.stderr)):
                event[field] = value.decode(errors='replace') if isinstance(value, bytes) else value or ''
            raise
        finally:
            event['seconds'] = time.monotonic() - started
        require(result.returncode == 0, f'{purpose}: exit={result.returncode}; no retry')
        return result.stdout

    try:
        context = runtime.drive(str(binary), output / 'runtime')
        receipt['context'] = context
        receipt['trace'].extend(context['trace'])
        require(context['classification'] == 'VERIFIED', 'runtime context: doctor or identity failed')
        receipt['candidate'] = context['candidate']
        receipt['method_sources'] = json.loads((SKILL / 'references/migration-sources.json').read_text())
        for index, (name, argv) in enumerate(planned):
            journey = receipt['journeys'][index]
            journey['status'] = 'FAILED'
            # The runtime driver's successful doctor covers the first drive.
            # Each subsequent short-lived drive gets a fresh doctor, as before.
            if index:
                observed = json.loads(command(['./soodles', 'runtime', 'check', binary], 'verification', name + ' doctor'))
                require(observed == context['runtime'], f'{name}.runtime: changed since context binding')
            result = json.loads(command(argv, 'verification', name + ' oracle'))
            journey['receipt'] = result
            validate_result(name, result)
            journey['status'] = 'VERIFIED'
        complete(receipt, [name for name, _ in planned])
        after = command(['git', 'rev-parse', 'HEAD', 'HEAD^{tree}'], 'readback', 'after source identity').splitlines()
        status = command(['git', 'status', '--porcelain', '--untracked-files=all'], 'readback', 'after source residue')
        require(after == [receipt['candidate']['head'], receipt['candidate']['tree']] and not status.strip(),
                'source: changed during recovery verification')
        receipt['cleanup'] = {'verified': True, 'scope': 'Owning oracles completed fixture teardown; cleanup probes reported zero residue. No independent cross-namespace PID claim.'}
        receipt['classification'] = 'VERIFIED'
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        receipt['failure'] = f'{type(exc).__name__}: {exc}; owner: verify-soodles delivery-recovery; supported help: verify_recovery.py --help'
    finally:
        receipt['counts'] = runtime.counts(receipt['trace'])
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', help='Absolute admitted Noodle binary path')
    parser.add_argument('output', help='Fresh evidence directory outside the checkout')
    args = parser.parse_args()
    try:
        receipt = drive(args.binary, args.output)
    except (ValueError, OSError) as exc:
        parser.error(f'{exc}; owner: verify-soodles delivery-recovery; supported help: {parser.prog} --help')
    print(json.dumps({k: receipt[k] for k in ('feature', 'classification', 'counts', 'cleanup', 'authorizes_landing')}))
    return 0 if receipt['classification'] == 'VERIFIED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
