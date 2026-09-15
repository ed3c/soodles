"""Supervisor-selected carrier; never imported from candidate or mutable main."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE='ca3bfffb4b4da6dad1c969723043e62099eb0ef1'
HEAD='cc83bc30ab78409a6e767a2777b58ec5714892e4'
ORACLE='1aa119ef410698af1155b9d4839646b032ea92313a58e6cbd2ca28bc932d5e1f'
workspace=Path(os.environ['GITHUB_WORKSPACE'])
root=Path('/tmp/soodles-10-proof'); root.mkdir(); root.chmod(0o755)
oracle=root/'delivery_oracle.py'
shutil.copy2(workspace/'authority/authority/delivery_oracle.py',oracle)
assert hashlib.sha256(oracle.read_bytes()).hexdigest()==ORACLE
oracle.chmod(0o644)
for name,sha in [('baseline',BASE),('candidate',HEAD)]:
 checkout=workspace/name
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()==sha
 target=root/name; target.mkdir()
 archive=subprocess.check_output(['git','archive',sha],cwd=checkout)
 subprocess.run(['tar','-x','-C',str(target)],input=archive,check=True)
 for p in [target,*target.rglob('*')]:
  p.chmod(0o755 if p.is_dir() or p.name=='soodles' else 0o644)
selection=root/'selection.json'
selection.write_text(json.dumps({'base':BASE,'candidate':HEAD,'oracle_sha256':ORACLE}))
protected=root/'publisher-checkpoint.json'; protected.write_text('{"fixture":"supervisor-owned"}\n')
selection.chmod(0o644); protected.chmod(0o644)
probe="""import json,os,sys
out={}
for name in sys.argv[1:]:
 try:
  with open(name,'a') as f: f.write('forbidden')
  out[name]='WRITABLE'
 except PermissionError: out[name]='DENIED'
print(json.dumps({'uid':os.getuid(),'writes':out}))
"""
r=subprocess.run([sys.executable,'-B','-c',probe,str(oracle),str(selection),str(protected)],cwd=root,user=65534,group=65534,text=True,capture_output=True,check=True)
isolation=json.loads(r.stdout)
assert isolation['uid']==65534 and set(isolation['writes'].values())=={'DENIED'}
def judge(target, success):
 r=subprocess.run([sys.executable,'-B',str(oracle),str(target),'--isolated'],text=True,capture_output=True,timeout=120)
 print(r.stdout,flush=True)
 if r.stderr: print(r.stderr,flush=True)
 assert (r.returncode==0)==success, 'unexpected fixed-oracle verdict'
 return json.loads(r.stdout)
baseline=judge(root/'baseline',False)
assert 'cannot resume first dispatch' in baseline['reason']
treatment=judge(root/'candidate',True)
mutant=root/'mutant'; shutil.copytree(root/'candidate',mutant)
p=mutant/'landing.py'; source=p.read_text(); prefix,consumer=source.split('def dispatch(checkpoint, snapshot):',1)
needle='        state = delivery_state(path)\n        claim = state["claim"]'
bad='        state = delivery_state(path)\n        if state.get("delivery", {}).get("status") == "offered":\n            state["delivery"]["status"] = "prepared"\n            state["writes_offered"].pop()\n        claim = state["claim"]'
assert needle in consumer
p.write_text(prefix+'def dispatch(checkpoint, snapshot):'+consumer.replace(needle,bad,1))
# An always-green candidate oracle is also ignored by the external observer.
(mutant/'delivery_oracle.py').write_text('def delivery_probe(*a, **k): return {"verdict":"GREEN"}\n')
negative=judge(mutant,False)
assert 'duplicate merge dispatch admitted' in negative['reason']
assert hashlib.sha256(oracle.read_bytes()).hexdigest()==ORACLE
result={'scope':'fixed external delivery oracle; process faults and local provider fixture; no provider writes',
        'base_head':BASE,'candidate_head':HEAD,'oracle_sha256':ORACLE,
        'authority_commit':os.environ['GITHUB_SHA'],'publisher_sha256':'faaf6892ea1e14dfa31319aa5dcd92162cc471e3eaad8dfe1d215da5face6ccb',
        'isolation':isolation,'baseline':baseline,'treatment':treatment,'planted_negative':negative,
        'default_branch_verifier_loaded':False,'candidate_oracle_imported':False,
        'authority_files_unchanged':True,'authorizes_landing':False}
(root/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
