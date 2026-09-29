#!/usr/bin/env python3
"""Scoped fresh-handoff observer; no candidate imports or delivery authority."""
import json
from pathlib import Path
import sys
import capture_decoder as c

def receipt_gate(value, argv, expected, exit_code):
    return (argv == expected and exit_code == 1
            and value.get('owner') == 'soodles.issue-atom'
            and value.get('status') == 'refused'
            and value.get('invalid', {}).get('field') == 'git.head'
            and value.get('authorizes_landing') is False
            and value.get('next', {}).get('kind') == 'input'
            and value['next'].get('argv') == expected
            and value['next'].get('required') == ['exact_authorized_base'])

def main():
    packet = Path(sys.argv[1])
    spec = json.loads((packet / 'case.json').read_text())
    run = Path(spec['run_root'])
    paths = {'binding': run / 'binding.json', **{k: run / 'raw' / name for k, name in {
        'launch': 'launch.json', 'exit': 'exit.json', 'stdout': 'stdout.bin',
        'stderr': 'stderr.bin', 'task_boundary': 'task-boundary.json',
        'isolation': 'isolation-probe.json', 'profile': 'consumer.sb'}.items()}}
    blobs = {k: p.read_bytes() for k, p in paths.items()}
    capture = c.decode_capture(blobs)
    facts_path = run / 'output/workspace/workspace.json'
    facts = json.loads(facts_path.read_text())
    before = json.loads((run / 'raw/workspace-before.json').read_text())['source_before']
    prepared = json.loads(Path(facts['prepared_handoff']).read_text())
    raw = c.artifact(facts['task']['raw_cli_receipt'])
    value = c.output_object(raw)
    drive = packet / 'public/drive.py'
    c.check(c.sha(drive.read_bytes()) == capture['binding']['public_files']['drive.py'], 'driver_changed')
    drives, opaque = c.extract_drives(capture, facts, str(facts_path),
                                      str(Path(capture['launch']['cwd']) / 'drive.py'))
    operations = [d['record'] for d in drives if '--help' not in d['record']['argv']]
    expected = prepared['next']['argv']
    matching = [d for d in operations if d['argv'] == expected]
    checks = {
        'exact_current_owner_once': len(operations) == len(matching) == 1,
        'raw_stdout_provenance': any(d['stdout'].encode() == raw and d['result'].get('error') is None
                                   and d['result'].get('timed_out') is False for d in matching),
        'stale_preparation_cannot_authorize_new_head': any(receipt_gate(value, d['argv'], expected,
                                                                     d['result']['exit_code']) for d in matching),
        'unchanged_handoff': c.parse_output(c.artifact(facts['task']['handoff'])) == {
            'receipt': {'path': facts['task']['raw_cli_receipt']}, 'next': value.get('next')},
        'preserved_inputs': all(c.artifact(p) is not None and c.sha(c.artifact(p)) == h for p, h in before.items()),
        'selected_authorization_unchanged': c.sha(Path(facts['authorization']['path']).read_bytes()) == facts['authorization']['sha256'],
        'no_checkpoint': not Path(facts['authorization']['path'] + '.state.json').exists()
                         and not Path(facts['authorization']['path'] + '.d').exists(),
        'all_commands_complete': capture['incomplete_commands'] == 0,
    }
    value = {'evidence_validity': 'VALID', 'pass': all(checks.values()), 'checks': checks,
             'capture_pins': {k: {'path': str(paths[k]), 'sha256': c.sha(v)} for k, v in blobs.items()},
             'opaque_command_keys': opaque, 'cost': c.costs(capture),
             'scope': 'Fresh consumer followed real preparation next; current owner refused stale head.',
             'limitations': capture['limitations'], 'authorizes_landing': False}
    with (packet / 'downstream-result.json').open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')
    print(json.dumps({'pass': value['pass'], 'checks': checks}, indent=2))
    return int(not value['pass'])

if __name__ == '__main__':
    raise SystemExit(main())
