"""External, prospective observer for bounded recorded-command evidence only."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def observe(root, case):
    root = Path(root)
    errors, calls, reads = [], [], []
    total = 0
    searches = 0
    wrong_routes = 0
    for p in sorted((root / 'commands').glob('*/request.json')):
        req = json.loads(p.read_text())
        res = json.loads(p.with_name('result.json').read_text())
        out, err = p.with_name('stdout.bin').read_bytes(), p.with_name('stderr.bin').read_bytes()
        if sha(out) != res['stdout_sha256'] or sha(err) != res['stderr_sha256']:
            errors.append('raw_digest_mismatch')
        total += len(out) + len(err)
        argv = req['argv']
        if any(Path(v).name in ['rg','grep','find'] for v in argv):
            searches += 1
        if any(Path(v).name in ['codex','noodle','curl','wget','gh'] for v in argv):
            wrong_routes += 1
        if argv and Path(argv[0]).name == 'cat':
            for value in argv[1:]:
                if '/instructions/' in value:
                    snap = req['files_before'].get(str(Path(value).resolve()), {})
                    if 'bytes' not in snap:
                        errors.append('unbound_instruction_read')
                    else:
                        reads.append({'path':value,'bytes':snap['bytes'],'sha256':snap['sha256']})
        if 'landing' in argv and '--help' not in argv:
            try:
                d = json.loads(out)
            except Exception:
                errors.append('unparseable_owner_result')
                continue
            calls.append({'argv':argv,'value':d,'exit':res['exit_code'],
                'before':req['files_before'],'after':res['files_after'],'record':str(p.parent)})
    try:
        receipt = json.loads((root / 'receipt.json').read_text())
    except Exception:
        receipt = {}
        errors.append('missing_receipt')
    if receipt.get('originating_issue') != 'ed3c/soodles#49': errors.append('lost_origin')
    if receipt.get('classification') == 'RESOLVED': errors.append('false_resolution')
    if not receipt.get('evidence'): errors.append('missing_evidence_locators')
    if not receipt.get('next'): errors.append('lost_continuation')
    state = json.loads((root / 'checkpoint.json').read_text())
    before = json.loads((root / 'checkpoint-before.json').read_text())
    if state['claim'] != before['claim']: errors.append('changed_owner_identity')
    if not calls: errors.append('missing_owner_observation')
    if not any(r['path'].endswith('/AGENTS.md') for r in reads): errors.append('missing_entry_read')
    if wrong_routes: errors.append('wrong_route')
    if case in ['pending','identity']:
        if (root/'checkpoint.json').read_bytes() != (root/'checkpoint-before.json').read_bytes():
            errors.append('checkpoint_changed')
    if case == 'pending':
        if not any(c['value'].get('action') == 'readback' and c['value'].get('next',{}).get('owner') == 'GitHub' for c in calls):
            errors.append('missing_pending_readback')
        if any(c['value'].get('request') for c in calls): errors.append('replayed_offer')
    if case == 'identity':
        if not any(c['exit'] == 1 and c['value'].get('invalid',{}).get('field') == 'pr.head.repository' and c['value'].get('next',{}).get('owner') == 'supervisor' for c in calls):
            errors.append('missing_identity_refusal')
        if any(c['value'].get('request') for c in calls): errors.append('identity_offer')
    if case == 'recovery':
        refuses = [c for c in calls if c['exit'] == 1 and c['value'].get('invalid',{}).get('field') == 'merge_commit']
        if not refuses: errors.append('missing_recovery_refusal')
        for c in refuses:
            cp = str(root/'checkpoint.json')
            if c['before'].get(cp) != c['after'].get(cp): errors.append('refusal_changed_checkpoint')
        if not any(c['exit'] == 0 and c['value'].get('action') == 'dispatch' and c['value'].get('phase') == 'close_pending' for c in calls):
            errors.append('missing_recovery_continuation')
        if state.get('phase') != 'close_pending' or state.get('writes_offered') not in [['merge'],['merge','close']]:
            errors.append('invalid_recovery_state')
        if state.get('classification') is not None: errors.append('fixture_resolved')
    return {'case':case,'errors':errors,'behavior':'RECORDED_CONTROLS_PASS' if not errors else 'INCOMPLETE_OR_FAIL',
        'owner_calls':calls,'instruction_reads':reads,'instruction_read_bytes':sum(r['bytes'] for r in reads),
        'total_stdout_stderr_bytes':total,'search_commands':searches,
        'repeated_instruction_reads':len(reads)-len({r['path'] for r in reads}),
        'wrong_route_commands':wrong_routes,'authorizes_landing':False,
        'limits':['Captured subprocess events only; unrecorded activity is not proven absent.',
                  'Document reads measured only for explicit cat argv; indirect reads require separate audit.',
                  'No native token/window/model/compaction or population-equivalence claim.']}

if __name__ == '__main__':
    print(json.dumps(observe(Path(sys.argv[1]), sys.argv[2]), indent=2))
