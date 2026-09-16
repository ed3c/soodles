"""Supervisor-selected immutable carrier; subjects never supply verdicts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = '11a2298d0ba3c5d80fecb00ccc554e38ef3268fe'
HEAD = 'e3683a7c8b8f1f1c79c573d9d4422a85922bfb51'
ORACLE = '6529d8cde7f0f667088f70bf1059e2c85a4a62dd520854b9587ae20879f25056'
PUBLISHER = 'f812d649046d72e7f008f3dd9565ff6c668657a70e50fcd2ab5c961227261b10'
workspace = Path(os.environ['GITHUB_WORKSPACE'])
root = Path('/tmp/soodles-29-proof')
root.mkdir(mode=0o755)
oracle = root / 'delivery_oracle.py'
shutil.copy2(workspace / 'authority/authority/delivery_oracle.py', oracle)
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
assert 'merge refusal lost exact field/value or owner' in baseline['reason']
treatment = judge(root / 'candidate', True)
negatives = {}
for name, needle, replacement, reason in [
 ('wrong-subject', '/git/commits/{sha}', '/git/commits/{claim["head"]}', 'merge request has wrong subject'),
 ('wrong-operation', 'next_action = provider_next(claim, operation, checkpoint)', 'next_action = provider_next(claim, "dispatch", checkpoint)', 'merge routes to wrong operation'),
 ('unsafe-accept', 'require(merge.get("sha") == sha, "merge.sha", merge.get("sha"))', 'require(True, "merge.sha", merge.get("sha"))', 'invalid merge evidence admitted')
]:
 target = root / name; shutil.copytree(root / 'candidate', target)
 path = target / 'landing.py'; source = path.read_text(); assert source.count(needle) >= 1
 path.write_text(source.replace(needle, replacement, 1))
 (target / 'delivery_oracle.py').write_text('def delivery_probe(*a, **k): return {"verdict":"GREEN"}\n')
 negatives[name] = judge(target, False)
 assert reason in negatives[name]['reason']
assert hashlib.sha256(oracle.read_bytes()).hexdigest() == ORACLE
assert protected.read_text() == '{"fixture":"supervisor-owned"}\n'
result = {'scope':'fixed external merged-commit observer; local provider fixtures, no GitHub writes',
 'base_head':BASE, 'candidate_head':HEAD, 'oracle_sha256':ORACLE, 'authority_commit':os.environ['GITHUB_SHA'],
 'publisher_sha256':PUBLISHER, 'isolation':isolation, 'baseline':baseline, 'treatment':treatment,
 'planted_negatives':negatives, 'default_branch_verifier_loaded':False, 'candidate_oracle_imported':False,
 'authority_files_unchanged':True, 'authorizes_landing':False}
(root / 'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
