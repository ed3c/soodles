"""Supervisor-selected immutable carrier; subjects never supply verdicts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = 'bcab7a8642b94c9f947b64d2fcb2762d80615cdd'
HEAD = '287640024ff1974a95abf6ab3fe22ba85c483238'
ORACLE = 'fb59735cbdb679d7a6056d1f698f8b8c532fb6388b9d5e1f332d26f78ace5369'
PUBLISHER = 'f0cf5d6bd612927421a769e50944712c6772dc0047d77717296c3d2f7920c08a'
workspace = Path(os.environ['GITHUB_WORKSPACE'])
root = Path('/tmp/soodles-25-proof')
root.mkdir(mode=0o755)
oracle = root / 'base_recovery_oracle.py'
shutil.copy2(workspace / 'authority/authority/base_recovery_oracle.py', oracle)
assert hashlib.sha256(oracle.read_bytes()).hexdigest() == ORACLE
oracle.chmod(0o644)
for name, sha in [('baseline', BASE), ('candidate', HEAD)]:
    checkout = workspace / name
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip() == sha
    target = root / name
    target.mkdir()
    archive = subprocess.check_output(['git', 'archive', sha], cwd=checkout)
    subprocess.run(['tar', '-x', '-C', str(target)], input=archive, check=True)
    for path in [target, *target.rglob('*')]:
        path.chmod(0o755 if path.is_dir() or path.name == 'soodles' else 0o644)
selection = root / 'selection.json'
selection.write_text(json.dumps({'base': BASE, 'candidate': HEAD, 'oracle_sha256': ORACLE, 'publisher_sha256': PUBLISHER}))
protected = root / 'publisher-checkpoint.json'
protected.write_text('{"fixture":"supervisor-owned"}\n')
for path in (selection, protected):
    path.chmod(0o644)
probe = '''import json,os,sys
out={}
for name in sys.argv[1:]:
 try:
  with open(name,'a') as stream: stream.write('forbidden')
  out[name]='WRITABLE'
 except PermissionError: out[name]='DENIED'
print(json.dumps({'uid':os.getuid(),'writes':out}))
'''
r = subprocess.run([sys.executable, '-B', '-c', probe, str(oracle), str(selection), str(protected)],
                   cwd=root, user=65534, group=65534, text=True, capture_output=True, check=True)
isolation = json.loads(r.stdout)
assert isolation['uid'] == 65534 and set(isolation['writes'].values()) == {'DENIED'}


def judge(target, success):
    r = subprocess.run([sys.executable, '-B', str(oracle), str(target), '--isolated'],
                       text=True, capture_output=True, timeout=120)
    print(r.stdout, flush=True)
    if r.stderr:
        print(r.stderr, flush=True)
    assert (r.returncode == 0) == success, 'unexpected fixed-oracle verdict'
    return json.loads(r.stdout)


baseline = judge(root / 'baseline', False)
assert 'comparison lacks owning provider readback' in baseline['reason']
treatment = judge(root / 'candidate', True)
negatives = {}
for name, needle, replacement, reason in [
 ('wrong-subject', '/compare/{base}...{head}', '/compare/{head}...{base}', 'comparison request has wrong subject'),
 ('wrong-operation', 'next_action = provider_next(claim, operation, checkpoint)', 'next_action = provider_next(claim, "dispatch", checkpoint)', 'comparison routes to wrong operation')]:
 target = root / name; shutil.copytree(root / 'candidate', target)
 path = target / 'landing.py'; source = path.read_text(); assert source.count(needle) == 1
 path.write_text(source.replace(needle, replacement))
 (target / 'base_recovery_oracle.py').write_text('def base_recovery_probe(*a, **k): return {"verdict":"GREEN"}\n')
 negatives[name] = judge(target, False)
 assert reason in negatives[name]['reason']
assert hashlib.sha256(oracle.read_bytes()).hexdigest() == ORACLE
assert protected.read_text() == '{"fixture":"supervisor-owned"}\n'
result = {'scope':'fixed external comparison observer; local provider fixtures, no GitHub writes',
 'base_head':BASE, 'candidate_head':HEAD, 'oracle_sha256':ORACLE, 'authority_commit':os.environ['GITHUB_SHA'],
 'publisher_sha256':PUBLISHER, 'isolation':isolation, 'baseline':baseline, 'treatment':treatment,
 'planted_negatives':negatives, 'default_branch_verifier_loaded':False, 'candidate_oracle_imported':False,
 'authority_files_unchanged':True, 'authorizes_landing':False}
(root / 'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
