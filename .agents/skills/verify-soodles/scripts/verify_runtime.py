#!/usr/bin/env python3
"""Drive the runtime-admission CLI once and preserve a non-authorizing receipt."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time

SKILL = Path(__file__).resolve().parent.parent
ROOT = SKILL.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def preflight(binary, output):
    require(Path(binary).is_absolute(), f'invalid binary={binary!r}: supply an absolute path')
    output = Path(output).resolve()
    require(ROOT != output and ROOT not in output.parents,
            f'invalid output={str(output)!r}: use a directory outside the checkout')
    require(not output.exists(), f'invalid output={str(output)!r}: use a fresh directory')
    return Path(binary).resolve(), output


def resolved_skill(stdout, expected):
    rows = [line.split('\t') for line in stdout.splitlines() if line.split('\t')[0] == 'verify-soodles']
    require(len(rows) == 1, 'skill resolution: verify-soodles absent or ambiguous; inspect noodle skills list')
    row = rows[0]
    require(len(row) == 4 and row[2] == 'true' and Path(row[3]).resolve() == expected,
            'skill resolution: foreign path or missing SKILL.md; inspect noodle skills list')
    return {'name': row[0], 'search_path': row[1], 'path': row[3]}


def counts(events):
    readbacks = [tuple(e['argv']) for e in events if e['kind'] == 'readback']
    return {'top_level_commands': len(events),
            'unexpected_command_failures': sum(e['exit'] != e['expected_exit'] for e in events),
            'expected_refusals': sum(e['exit'] == e['expected_exit'] != 0 for e in events),
            'readback_invocations': len(readbacks),
            'repeated_readbacks': sum(n - 1 for n in Counter(readbacks).values()),
            'verification_invocations': sum(e['kind'] == 'verification' for e in events),
            'canonical_acceptance_invocations': sum(e['argv'][1:3] == ['acceptance', 'verify'] for e in events)}


def drive(binary, output):
    binary, output = preflight(binary, output)
    output.mkdir(parents=True)
    events = []
    receipt = {'schema': 1, 'feature': 'runtime-admission', 'classification': 'FAILED',
               'authorizes_landing': False, 'trace': events,
               'counter_scope': 'Only commands issued by this driver; excludes internal subprocesses, Agent discovery and provider landing. Repeated readbacks include required before/after identity guards.',
               'non_claims': ['Agent path-cost reduction', 'production scheduling', 'provider delivery', 'whole-app verification']}
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if key in os.environ}

    def command(argv, kind, purpose, expected=0):
        started = time.monotonic()
        event = {'argv': [str(x) for x in argv], 'kind': kind, 'purpose': purpose,
                 'exit': None, 'expected_exit': expected, 'stdout': '', 'stderr': ''}
        events.append(event)
        try:
            result = subprocess.run(event['argv'], cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=30)
            event.update(exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
        finally:
            event['seconds'] = time.monotonic() - started
        require(result.returncode == expected, f'{purpose}: unexpected exit={result.returncode}; no retry')
        return result.stdout, result.stderr

    def identity(when):
        value, _ = command(['git', 'rev-parse', 'HEAD', 'HEAD^{tree}'], 'readback', when + ' source identity')
        status, _ = command(['git', 'status', '--porcelain', '--untracked-files=all'], 'readback', when + ' source residue')
        require(not status.strip(), when + ': checkout is dirty')
        head, tree = value.splitlines()
        return {'head': head, 'tree': tree}

    scratch = None
    try:
        before = identity('before')
        receipt['candidate'] = before
        # Doctor is also the positive drive: do not repeat it merely to fill another section.
        positive, _ = command(['./soodles', 'runtime', 'check', binary], 'verification', 'doctor and positive admission')
        observed = json.loads(positive)
        lock = json.loads((ROOT / 'policy/runtime.lock.json').read_text())
        require(observed['observed_binary_sha256'] == lock['binary_sha256'] and
                observed['observed_version'] == lock['release'] and observed['authorizes_landing'] is False,
                'positive admission receipt differs from the locked identity')
        receipt['runtime'] = observed
        listing, warnings = command([binary, 'skills', 'list'], 'readback', 'resolve project skill')
        receipt['skill_resolution'] = resolved_skill(listing, SKILL)
        receipt['skill_resolution']['files_sha256'] = {
            str(p.relative_to(SKILL)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(SKILL.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
        receipt['skill_resolution']['warnings'] = warnings
        # This CLI has no resident process. Only this private directory needs teardown.
        with tempfile.TemporaryDirectory(prefix='soodles-verify-admission-') as tmp:
            scratch = Path(tmp)
            sentinel = scratch / 'executed'
            invalid = scratch / 'noodle'
            invalid.write_text('#!/bin/sh\ntouch ' + shlex.quote(str(sentinel)) + '\n')
            invalid.chmod(0o755)
            _, refusal = command(['./soodles', 'runtime', 'check', invalid], 'verification',
                                 'wrong digest rejected before execution', expected=1)
            require('invalid binary.sha256=' in refusal and './soodles runtime check --help' in refusal,
                    'negative control did not name the owning field and help')
            require(not sentinel.exists(), 'negative control executed the unadmitted binary')
            receipt['negative_control'] = {'expected_refusal': 'binary.sha256', 'sentinel_absent': True}
        require(not scratch.exists(), 'verification scratch survived cleanup')
        require(identity('after') == before, 'source identity changed during verification')
        receipt['classification'] = 'VERIFIED'
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        receipt['failure'] = f'{type(exc).__name__}: {exc}'
    finally:
        receipt['cleanup'] = {'scratch_removed': scratch is None or not scratch.exists(), 'resident_processes_started': 0}
        receipt['counts'] = counts(events)
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    require((output / 'receipt.json').is_file(), 'evidence absent after cleanup')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', help='Absolute path to the Noodle binary selected by policy/runtime.lock.json')
    parser.add_argument('output', help='Fresh evidence directory outside the checkout')
    args = parser.parse_args()
    try:
        receipt = drive(args.binary, args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({k: receipt[k] for k in ('feature', 'classification', 'counts', 'cleanup', 'authorizes_landing')}))
    return 0 if receipt['classification'] == 'VERIFIED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
