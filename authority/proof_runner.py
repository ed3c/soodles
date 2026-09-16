"""Supervisor-selected immutable carrier; subjects never supply verdicts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = 'defc1084de1a0d760cf145755efb39ea8850a410'
HEAD = 'f394a5de21528a34c33c9660f140a7a012326b5d'
ORACLE = 'dc6e1a0cfb6783edf78a3d979e1357af9ae62940d06430a35b37314d719d0545'
PUBLISHER = 'faaf6892ea1e14dfa31319aa5dcd92162cc471e3eaad8dfe1d215da5face6ccb'
workspace = Path(os.environ['GITHUB_WORKSPACE'])
root = Path('/tmp/soodles-16-proof')
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
assert 'invalid base.head' in baseline['reason']
treatment = judge(root / 'candidate', True)
mutant = root / 'mutant'
shutil.copytree(root / 'candidate', mutant)
path = mutant / 'landing.py'
source = path.read_text()
needle = '    if state["writes_offered"]:\n        return recovery_action(state, base)'
bad = '    if state["writes_offered"]:\n        state["writes_offered"] = []\n        state["delivery"]["status"] = "prepared"'
assert source.count(needle) == 1
path.write_text(source.replace(needle, bad))
(mutant / 'base_recovery_oracle.py').write_text('def base_recovery_probe(*a, **k): return {"verdict":"GREEN"}\n')
negative = judge(mutant, False)
assert 'unknown offer converted to readmission' in negative['reason']
assert hashlib.sha256(oracle.read_bytes()).hexdigest() == ORACLE
assert protected.read_text() == '{"fixture":"supervisor-owned"}\n'
result = {'scope': 'fixed external process observer; local provider fixtures, no GitHub writes',
          'base_head': BASE, 'candidate_head': HEAD, 'oracle_sha256': ORACLE,
          'authority_commit': os.environ['GITHUB_SHA'], 'publisher_sha256': PUBLISHER,
          'isolation': isolation, 'baseline': baseline, 'treatment': treatment, 'planted_negative': negative,
          'default_branch_verifier_loaded': False, 'candidate_oracle_imported': False,
          'authority_files_unchanged': True, 'authorizes_landing': False}
(root / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
