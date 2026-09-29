#!/usr/bin/env python3
"""Supervisor readback of recorded native consumers; not a full platform audit."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ORACLE = Path('/Users/neon/.codex/experiments/authorization-oracle-ba7ygaqu')
sys.dont_write_bytecode = True
sys.path.insert(0, str(ORACLE / 'frozen'))
import issue_atom as frozen


def sha(data):
    return hashlib.sha256(data).hexdigest()


def observe(run):
    directory = Path(run['directory'])
    selection = json.loads(Path(run['selection']).read_text())
    requests = sorted((directory / 'raw').glob('*/request.json'),
                      key=lambda p: json.loads(p.read_text())['time_ns'])
    gates = {'raw_present': bool(requests), 'selection_digest': sha(Path(run['selection']).read_bytes()) == run['selection_sha256']}
    operations = []
    for path in requests:
        req = json.loads(path.read_text())
        result = json.loads((path.parent / 'result.json').read_text())
        out, err = (path.parent / 'stdout.bin').read_bytes(), (path.parent / 'stderr.bin').read_bytes()
        operations.append({'label': path.parent.name, 'argv': req['argv'], 'exit_code': result['exit_code'],
                           'error': result['error'], 'timed_out': result['timed_out'],
                           'stdout_bytes': len(out), 'stderr_bytes': len(err),
                           'elapsed_seconds': result['elapsed_seconds'],
                           'raw_digests_valid': sha(out) == result['stdout_sha256'] and sha(err) == result['stderr_sha256']})
    gates['raw_digests'] = bool(operations) and all(v['raw_digests_valid'] for v in operations)
    initial = json.loads(requests[0].read_text()) if requests else {}
    gates['initial_instruction_binding'] = initial.get('files_before', {}).get(run['instruction'], {}).get('sha256') == run['instruction_sha256']
    changed = []
    for rel, expected in run['before'].items():
        p = directory / rel
        observed = ('symlink:' + str(p.readlink())) if p.is_symlink() else sha(p.read_bytes()) if p.is_file() else None
        if observed != expected: changed.append(rel)
    gates['selected_bytes_unchanged'] = not changed
    gates['source_instruction_unchanged'] = sha(Path(run['instruction']).read_bytes()) == run['instruction_sha256']
    authorizations = []
    for path in (directory / 'output').glob('*.json'):
        try: value = json.loads(path.read_text())
        except ValueError: continue
        if isinstance(value, dict) and value.get('owner') == 'external-supervisor' and 'schema_version' in value:
            authorizations.append(path)
    auth_details = None
    if run['case'] != 'publisher_changed':
        gates['one_authorization'] = len(authorizations) == 1
        if len(authorizations) == 1:
            path = authorizations[0]
            try:
                value, digest = frozen.validate_authorization(path, sha(path.read_bytes()))
                gates['frozen_validator'] = True
                gates['selected_identity'] = all(value[key] == selection[key] for key in ('repository','issue','task','landing_owner')) and value['noodle'] == selection['carrier']['noodle'] and value['carrier'] == {key:selection['carrier'][key] for key in ('platform','codex')}
                control = Path(selection['control_root'])
                gates['derived_identity'] = value['control_root'] == str(control.resolve()) and value['host_config_sha256'] == (sha((control / '.noodle.toml').read_bytes()) if (control / '.noodle.toml').exists() else None)
                pins = [{'path':p, 'sha256':sha(subprocess.check_output(['git','show',value['base_head']+':'+p],cwd=control))} for p in selection['instruction_paths']]
                gates['instructions'] = value['schema_version'] == (3 if pins else 2) and value.get('instruction_pins',[]) == pins
                auth_details = {'path':str(path),'sha256':digest}
            except Exception as error:
                gates['frozen_validator'] = False
                auth_details = {'error':str(error)}
    else:
        gates['no_authorization'] = not authorizations
        # A changed publisher must be explicitly named in captured output, not inferred from silence.
        outputs = b'\n'.join((p.parent/'stdout.bin').read_bytes()+(p.parent/'stderr.bin').read_bytes() for p in requests).decode(errors='replace')
        gates['explicit_selected_publisher_refusal'] = any(s in outputs for s in ('landing_owner.verifier_sha256','unchanged_external_owner','publisher digest','publisher bundle'))
    return {'case':run['case'],'arm':run['arm'],'round':run.get('round',1),'source_head':run['source_head'],
            'gates':gates,'changed_preexisting_files':changed,'authorization':auth_details,
            'captured_operation_count':len(operations),
            'nonzero_or_unstarted':sum(v['exit_code'] != 0 for v in operations),
            'operations':operations,'status':'PASS' if all(gates.values()) else 'INCONCLUSIVE_OR_FAIL',
            'observation_scope':'recorded subprocesses plus independent final file bytes; not full platform transcript',
            'observed_model':None,'token_usage':None,'authorizes_landing':False}


def main():
    manifest = json.loads(Path(sys.argv[1]).read_text())
    results = [observe(run) for run in manifest['runs'] if (Path(run['directory'])/'answer.json').is_file()]
    print(json.dumps(results,indent=2))

if __name__ == '__main__': main()
