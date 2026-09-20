"""External release-CLI refusal controls over disposable fixture copies."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile


HISTORICAL_ABSENT_PID = 2147483647


def isolate_captured_process_identities(root):
    """Retire captured PIDs only in the disposable execution copy."""
    adjustments = []
    sessions = Path(root) / '.noodle' / 'sessions'
    for path in sorted(sessions.glob('*/process.json')):
        process = json.loads(path.read_text())
        pid = process.get('pid')
        assert type(pid) is int and pid > 0, f'invalid captured pid: {path}'
        process['pid'] = HISTORICAL_ABSENT_PID
        path.write_text(json.dumps(process, separators=(',', ':')) + '\n')
        adjustments.append({
            'path': str(path.relative_to(root)),
            'captured_pid': pid,
            'scratch_pid': HISTORICAL_ABSENT_PID,
        })
    assert adjustments, 'no captured process identities found'
    return adjustments


def tree_digests(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(root).rglob('*')) if path.is_file()
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('binary')
    parser.add_argument('output')
    args = parser.parse_args()
    binary = str(Path(args.binary).resolve())
    fixture_root = Path(__file__).parent
    source = fixture_root / 'preserved-soodles-input'
    source_before = tree_digests(source)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    cases = []

    for name in ['wrong-digest', 'wrong-revision', 'admitted-ledger',
                 'valid-proposal', 'live-session', 'orphan-live-group']:
        with tempfile.TemporaryDirectory(prefix='noodle84-negative-') as scratch:
            root = Path(scratch) / 'control'
            shutil.copytree(source, root)
            adjustments = isolate_captured_process_identities(root)
            runtime = root / '.noodle'
            (root / '.noodle.toml').write_text('mode="manual"\n[server]\nenabled=false\n')
            state = json.loads((runtime / 'state.snapshot.json').read_text())
            proposal = json.loads((runtime / 'orders-next.json').read_text())
            subject = proposal['orders'][0]['id']
            revision = state['order_revision']
            process = None

            if name == 'admitted-ledger':
                effect = 'initial-admission-' + hashlib.sha256(subject.encode()).hexdigest()
                state['effect_ledger'].append({
                    'effect_id': effect,
                    'effect': {'effect_id': effect, 'type': 'initial_admission',
                               'payload': {'order_id': subject,
                                           'initial_revision': proposal['initial_revision']},
                               'created_at': '2026-09-17T00:00:00Z'},
                    'status': 'done', 'attempts': 1,
                    'result': {'effect_id': effect, 'status': 'completed', 'error': '',
                               'timestamp': '2026-09-17T00:00:00Z'},
                })
                (runtime / 'state.snapshot.json').write_text(json.dumps(state))
            if name == 'valid-proposal':
                proposal['initial_revision'] = revision
                (runtime / 'orders-next.json').write_text(json.dumps(proposal))
            if name in ('live-session', 'orphan-live-group'):
                code = ('import time; time.sleep(60)' if name == 'live-session' else
                        'import os,time; child=os.fork(); time.sleep(60) if child==0 else None')
                process = subprocess.Popen(
                    [sys.executable, '-c', code], start_new_session=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if name == 'orphan-live-group':
                    process.wait(timeout=5)
                session = 'external-live-guard'
                folder = runtime / 'sessions' / session
                folder.mkdir()
                (folder / 'process.json').write_text(json.dumps({
                    'pid': process.pid, 'session_id': session}))
                (folder / 'meta.json').write_text(json.dumps({
                    'status': 'exited', 'alive': False, 'runtime': 'process',
                    'session_id': session}))

            mailbox = (runtime / 'orders-next.json').read_bytes()
            before = (runtime / 'state.snapshot.json').read_bytes()
            digest = hashlib.sha256(mailbox).hexdigest()
            if name == 'wrong-digest':
                digest = '0' * 64
            if name == 'wrong-revision':
                revision = '0' * 32
            argv = [binary, '--project-dir', str(root), 'admission', 'retire',
                    digest, revision]
            try:
                completed = subprocess.run(
                    argv, cwd=root, capture_output=True, text=True, timeout=15)
                try:
                    result = json.loads(completed.stdout)
                except ValueError:
                    result = {}
                preserved = (
                    (runtime / 'orders-next.json').exists()
                    and (runtime / 'orders-next.json').read_bytes() == mailbox
                    and (runtime / 'state.snapshot.json').read_bytes() == before
                )
                expected = {
                    'wrong-digest': 'proposal_sha256 changed',
                    'wrong-revision': 'current_order_revision changed',
                    'admitted-ledger': 'owned, admitted',
                    'valid-proposal': 'currently valid',
                    'live-session': 'process or process group is present',
                    'orphan-live-group': 'process or process group is present',
                }[name]
                passed = (completed.returncode != 0
                          and result.get('status') == 'refused'
                          and preserved
                          and expected in result.get('invalid', ''))
                cases.append({
                    'case': name,
                    'argv': argv,
                    'exit': completed.returncode,
                    'stdout': completed.stdout,
                    'stderr': completed.stderr,
                    'preserved': preserved,
                    'historical_process_identity_adjustments': adjustments,
                    'passed': passed,
                })
            finally:
                if process:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    if process.poll() is None:
                        process.wait(timeout=5)

    receipt = {
        'scope': 'release CLI refusals over synthetic variants of preserved input; no production mutation',
        'binary_sha256': hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
        'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'original_fixture_unchanged': tree_digests(source) == source_before,
        'cases': cases,
        'passed': all(case['passed'] for case in cases),
        'authorizes_landing': False,
    }
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({
        'passed': receipt['passed'],
        'cases': [{key: value for key, value in case.items()
                   if key in ('case', 'passed', 'exit')} for case in cases],
    }))
    raise SystemExit(not receipt['passed'])


if __name__ == '__main__':
    main()
