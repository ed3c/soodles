"""Supervisor-owned Issue #8 experiment carrier; never imported from the subject."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = '09e6e12804fc06a6b6ac52b0ddbfb347f74d7f4c'
SUBJECT = 'd1c98712ec92164bd6a1a3718e22d964ea5213c0'
ORACLE = 'da40093a1d3f180920dccdc9d562d95e64e2c2ece53a3490bd75c45e99c4f7ff'
BINARY = '9f1354bea227a5e71fa36260645fa6102f1474f9fba170f9a76ad9f6dd678472'
root = Path(__file__).resolve().parent
oracle = root / 'cleanup_lock_oracle.py'
workspace, binary, receipts = (Path(x).resolve() for x in sys.argv[1:4])
assert os.geteuid() == 0
receipts.mkdir(parents=True, exist_ok=True)
for path in (root, *root.rglob('*')):
    os.chown(path, 0, 0)
    path.chmod(0o755 if path.is_dir() else 0o644)
assert hashlib.sha256(oracle.read_bytes()).hexdigest() == ORACLE
assert hashlib.sha256(binary.read_bytes()).hexdigest() == BINARY
for folder, head in (('baseline', BASE), ('subject', SUBJECT)):
    observed = subprocess.check_output(['git', '-c', 'safe.directory=' + str(workspace / folder), '-C', str(workspace / folder), 'rev-parse', 'HEAD'], text=True).strip()
    assert observed == head, (folder, observed)
protected = Path('/tmp/issue8-protected')
protected.mkdir(mode=0o755)
selector, checkpoint = protected / 'selection.json', protected / 'checkpoint.json'
selector.write_text(json.dumps({'oracle': ORACLE, 'subject': SUBJECT, 'publisher': '577f1b2f3a7297a60e0adba44226b9fe96c4591847a308a0c83d9e8c0bcaa597'}))
checkpoint.write_text('{"fixture_only":true,"writes_offered":["merge","close"]}')
selector.chmod(0o644)
checkpoint.chmod(0o644)
paths = [oracle, selector, checkpoint]
before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
child = r'''
import json,os,sys
result={}
for p in sys.argv[1:]:
    try:
        with open(p,'ab') as f: f.write(b'candidate mutation')
    except PermissionError:
        result[p]='DENIED'
    else:
        result[p]='UNEXPECTED_WRITE'
print(json.dumps({'uid':os.getuid(),'writes':result}))
assert all(v=='DENIED' for v in result.values())
'''
restricted = ['setpriv','--reuid=65534','--regid=65534','--clear-groups','--no-new-privs']
result = subprocess.run(restricted + [sys.executable,'-I','-B','-c',child,*map(str,paths)], capture_output=True, text=True, check=True)
isolation = json.loads(result.stdout)
assert isolation['uid'] == 65534
(receipts / 'isolation.json').write_text(json.dumps(isolation,indent=2))

def probe(name, subject, expected_exit, reason=None):
    result = subprocess.run([sys.executable,'-I','-B',str(oracle),str(binary),str(subject),'--isolated'],
        text=True,capture_output=True,timeout=240)
    (receipts / (name + '.stdout.json')).write_text(result.stdout)
    (receipts / (name + '.stderr.txt')).write_text(result.stderr)
    assert result.returncode == expected_exit, (name,result.returncode,result.stdout,result.stderr)
    value = json.loads(result.stdout)
    if reason:
        assert reason in value.get('reason',''), (name,value)
    return value

baseline = probe('baseline', workspace / 'baseline', 1, 'cleanup.observation')
treatment = probe('treatment', workspace / 'subject', 0)
false_subject = protected / 'false-subject'
false_subject.mkdir()
script = false_subject / 'soodles'
script.write_text('#!' + sys.executable + '\n' + f'real={str(workspace / "subject/soodles")!r}\n' + r'''
import json,os,sys
from pathlib import Path
if sys.argv[1:3]==['landing','reconcile']:
    checkpoint=Path(sys.argv[3])
    state=json.loads(checkpoint.read_text())
    blocked=state.get('cleanup_blocked')
    if blocked and not os.path.lexists(blocked['ref_lock']):
        state.update(phase='resolved',classification='RESOLVED',local={'head':state['claim']['head'],'tree':state['claim']['tree']})
        checkpoint.write_text(json.dumps(state))
        print(json.dumps(state))
        sys.exit(0)
os.execv(real,[real]+sys.argv[1:])
''')
script.chmod(0o755)
(false_subject / 'cleanup_lock_oracle.py').write_text('def lock_recovery_probe(*args, **kwargs): return {"zero_residue": True, "authorizes_landing": True}\n')
negative = probe('false-success', false_subject, 1, 'false success retained branch')
after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert before == after
receipt = {'scope':'supervised fixed-oracle experiment; no provider writes or verifier promotion',
    'authority_commit':os.environ.get('GITHUB_SHA'), 'baseline_head':BASE,'candidate_head':SUBJECT,
    'oracle_sha256':ORACLE,'binary_sha256':BINARY,'candidate_oracle_imported':False,
    'default_branch_verifier_loaded':False,'authorizes_landing':False,
    'isolated_child_uid':65534,'isolation':isolation,'authority_files_unchanged':before==after,
    'baseline':baseline,'treatment_cases':treatment['cases'],'planted_negative':negative}
(receipts / 'proof.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2))
