"""Supervisor-selected immutable carrier; subjects never supply verdicts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = '0256f2923e978b989e25df07c74db4370d343312'
HEAD = 'ff67a42834e664c59b5674cc892e9fac35e81bee'
ORACLE = '082dcda0fa2b941b4c266cb0c59a2b46ba76bb3a5aaaedecc8184e18e1df416d'
PUBLISHER = 'faaf6892ea1e14dfa31319aa5dcd92162cc471e3eaad8dfe1d215da5face6ccb'
workspace = Path(os.environ['GITHUB_WORKSPACE'])
root = Path('/tmp/soodles-19-proof')
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
assert 'explicit invalidation SIGKILL was not reached' in baseline['reason']
treatment = judge(root / 'candidate', True)
mutant = root / 'mutant'
shutil.copytree(root / 'candidate', mutant)
path = mutant / 'landing.py'
source = path.read_text()
needle = '        if state["writes_offered"] or state["phase"] not in {"admitted", "merge_pending", "readmission_pending"}:'
bad = '        if state["phase"] == "merge_pending":\n            state["writes_offered"] = []\n            state["delivery"]["status"] = "prepared"\n' + needle
assert source.count(needle) == 1
path.write_text(source.replace(needle, bad))
(mutant / 'base_recovery_oracle.py').write_text('def base_recovery_probe(*a, **k): return {"verdict":"GREEN"}\n')
negative = judge(mutant, False)
assert 'unknown write lacks readback refusal' in negative['reason']
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
