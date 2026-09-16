"""Supervisor-selected immutable carrier; subjects never supply verdicts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = '1dd502b796a4a686d414045cc140140dcadc9d70'
HEAD = '95d9a84b6c0d4f825233ae81e700816d6804f5e6'
ORACLE = '2fc755d463f44b5f36ebd87be45e2ac0a8d3f2b28bae55ed0edf1a45137f2fe2'
PUBLISHER = 'faaf6892ea1e14dfa31319aa5dcd92162cc471e3eaad8dfe1d215da5face6ccb'
workspace = Path(os.environ['GITHUB_WORKSPACE'])
root = Path('/tmp/soodles-21-proof')
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
assert 'start missing owner next readback' in baseline['reason']
treatment = judge(root / 'candidate', True)
mutant = root / 'mutant'
shutil.copytree(root / 'candidate', mutant)
path = mutant / 'landing.py'
source = path.read_text()
needle = 'state["phase"], input_next("readmit", ["claim", "readback"], path))'
bad = 'state["phase"], input_next("dispatch", ["claim", "readback"], path))'
assert source.count(needle) == 1
path.write_text(source.replace(needle, bad))
(mutant / 'delivery_oracle.py').write_text('def delivery_probe(*a, **k): return {"verdict":"GREEN"}\n')
negative = judge(mutant, False)
assert 'invalidated dispatch has conflicting route' in negative['reason']
terminal_mutant = root / 'terminal-mutant'
shutil.copytree(root / 'candidate', terminal_mutant)
tp = terminal_mutant / 'landing.py'
ts = tp.read_text()
needle = 'return response("advance", state, "stop", None)'
assert ts.count(needle) == 1
tp.write_text(ts.replace(needle, 'return response("advance", state, "readback", provider_next(claim, "advance", path))'))
terminal_negative = judge(terminal_mutant, False)
assert 'resolved checkpoint still requests readback' in terminal_negative['reason']
assert hashlib.sha256(oracle.read_bytes()).hexdigest() == ORACLE
assert protected.read_text() == '{"fixture":"supervisor-owned"}\n'
result = {'scope': 'fixed external process observer; local provider fixtures, no GitHub writes',
          'base_head': BASE, 'candidate_head': HEAD, 'oracle_sha256': ORACLE,
          'authority_commit': os.environ['GITHUB_SHA'], 'publisher_sha256': PUBLISHER,
          'isolation': isolation, 'baseline': baseline, 'treatment': treatment, 'planted_negative': negative, 'terminal_negative': terminal_negative,
          'default_branch_verifier_loaded': False, 'candidate_oracle_imported': False,
          'authority_files_unchanged': True, 'authorizes_landing': False}
(root / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
