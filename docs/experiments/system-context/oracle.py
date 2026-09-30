"""Fixed external observer: subprocess and Git bytes; never import candidate verdicts."""
import hashlib,json,subprocess,sys,tempfile,shutil
from pathlib import Path

def digest(data):return hashlib.sha256(data).hexdigest()
def call(argv,cwd):
 p=subprocess.run(argv,cwd=cwd,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=60)
 return {'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def run(root, expected_path):
 root=Path(root).resolve();expected=json.loads(Path(expected_path).read_text())
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
 before=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=root)
 for item in expected:
  raw=subprocess.check_output(['git','show',head+':'+item['path']],cwd=root)
  assert digest(raw)==item['sha256'],('frozen instruction mismatch',item['path'])
 target='contracts/system-v1/instruction-context.md'
 p=call([str(root/'system-context'),target],root)
 assert p['exit']==0,p
 value=json.loads(p['stdout']);assert value['authorizes_landing'] is False
 assert value['source_head']==head
 files=value['instruction_context']['files']
 assert value['instruction_context']['source_head']==head
 assert [f['path'] for f in files]==['contracts/system-v1/common.md',target]
 assert value['instruction_paths']==[f['path'] for f in files]
 assert value['instruction_pins']==[{'path':f['path'],'sha256':f['sha256']} for f in files]
 for f in files:
  raw=subprocess.check_output(['git','show',head+':'+f['path']],cwd=root)
  assert f['sha256']==digest(raw) and f['content']==raw.decode()
 assert set(value['paths'])==set(value['instruction_paths'])
 calls=[p]
 for bad in ('contracts/system-v1/missing.md','../contracts/system-v1.md','/etc/passwd'):
  p=call([str(root/'system-context'),bad],root);calls.append(p)
  assert p['exit']!=0,p
  refused=json.loads(p['stdout']);assert refused['status']=='refused' and refused['authorizes_landing'] is False
  assert isinstance(refused['invalid'],dict) and isinstance(refused['next'],dict)
 p=call([str(root/'system-context'),'contracts/system-v1/recovery.md',target],root);calls.append(p)
 assert p['exit']==0,p
 multi=json.loads(p['stdout'])
 names=multi['instruction_paths'];assert len(names)==len(set(names))==4
 assert set(names)=={'contracts/system-v1/common.md','contracts/system-v1/landing.md','contracts/system-v1/recovery.md',target}
 assert names.index('contracts/system-v1/common.md')<names.index(target)
 assert names.index('contracts/system-v1/landing.md')<names.index('contracts/system-v1/recovery.md')
 after=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=root)
 assert before==after,'read changed candidate state'
 return {'classification':'PASS','source_head':head,'selected_bytes':sum(len(f['content'].encode()) for f in files),'selected_paths':value['instruction_paths'],'all_frozen_files':len(expected),'processes':calls,'source_status_unchanged':True,'authorizes_landing':False}
if __name__=='__main__':
 try:
  result=run(sys.argv[1],sys.argv[2]);code=0
 except Exception as e:
  result={'classification':'FAIL','error':str(e),'authorizes_landing':False};code=1
 print(json.dumps(result,indent=2));raise SystemExit(code)
