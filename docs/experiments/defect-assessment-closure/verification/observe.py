#!/usr/bin/env python3
"""Fixed fixture observer. No provider transport, model, or candidate evaluator."""
import hashlib,json,os,subprocess,sys,tempfile,time
from pathlib import Path
BASE=Path(__file__).resolve().parent

def digests(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

def child(source,case):
 sys.dont_write_bytecode=True
 sys.path.insert(0,source)
 import issue_atom as atom
 auth={'repository':'ed3c/soodles','issue':{'number':131},'control_root':'/fixture/control','base_head':'b'*40,'workflow':{'path':'.github/workflows/runtime.yml','job':'runtime','step':'acceptance'}}
 run={'id':9,'head_sha':'a'*40,'event':'pull_request','path':auth['workflow']['path'],'status':'completed','conclusion':'success'}
 job={'name':'runtime','status':'completed','conclusion':'success','steps':[{'name':'acceptance','status':'completed','conclusion':'success'}]}
 if case=='failed':run['conclusion']='failure'
 elif case=='queued':run.update(status='queued',conclusion=None)
 elif case=='foreign':run['head_sha']='c'*40
 elif case=='missing_job':job['name']='unrelated'
 class Provider:
  def __init__(self):self.calls=[]
  def workflow_runs(self,head):self.calls.append(['workflow_runs',head]);return {'workflow_runs':[run]}
  def jobs(self,run_id):self.calls.append(['jobs',run_id]);return {'jobs':[] if case=='queued' else [job]}
 provider=Provider()
 try:
  result=atom.select_run(provider,auth,'a'*40)
  receipt={'status':'observed','run':result[0],'jobs':result[1]}
 except atom.AtomRefusal as error:receipt=atom.refusal_output(error,'/fixture/selected.json')
 print(json.dumps({'receipt':receipt,'calls':provider.calls}))


def main():
 if len(sys.argv)==4 and sys.argv[1]=='--child':return child(sys.argv[2],sys.argv[3])
 freeze=json.loads((BASE/'freeze.json').read_text())
 for rel,expected in freeze.items():
  if hashlib.sha256((BASE/rel).read_bytes()).hexdigest()!=expected:raise RuntimeError('changed frozen input: '+rel)
 records=[]
 for arm in ('baseline','treatment'):
  source=BASE/arm;before=digests(source)
  for case in ('failed','queued','green','foreign','missing_job'):
   with tempfile.TemporaryDirectory(prefix='soodles-assessment-observer-') as directory:
    work=Path(directory);state_before=digests(work)
    argv=[sys.executable,'-I','-B',str(Path(__file__)), '--child',str(source),case]
    started=time.monotonic()
    process=subprocess.run(argv,cwd=work,env={'PATH':'/usr/bin:/bin','HOME':directory,'TMPDIR':directory},capture_output=True,text=True,timeout=30)
    record={'arm':arm,'case':case,'argv':argv,'exit':process.returncode,'stdout':process.stdout,'stderr':process.stderr,'elapsed_seconds':time.monotonic()-started,'source_unchanged':before==digests(source),'workspace_unchanged':state_before==digests(work)}
    if process.returncode==0:
     result=json.loads(process.stdout);r=result['receipt'];n=r.get('next',{})
     expected_calls=[['workflow_runs','a'*40]]+([] if case=='foreign' else [['jobs',9]])
     checks={'read_calls_only':result['calls']==expected_calls,'source_unchanged':record['source_unchanged'],'workspace_unchanged':record['workspace_unchanged']}
     if case=='failed':
      checks.update(refused=r['status']=='refused',no_retry='argv' not in n and 'request' not in r,non_authorizing=r.get('authorizes_landing') is False,known=n.get('known')=={'repository':'ed3c/soodles','issue':131,'control_root':'/fixture/control','base_head':'b'*40,'failed_head':'a'*40,'run_id':9,'workflow':{'path':'.github/workflows/runtime.yml','job':'runtime','step':'acceptance'}},assessment=n.get('assessment',{}).get('required_axes')==['product','fresh_behavior'] and n.get('assessment',{}).get('confirmation')=='after_candidate_selection')
     elif case=='missing_job':checks['refusal']=r.get('invalid',{}).get('field')=='github.workflow_job.count'
     elif case=='foreign':checks['no_foreign_adoption']=r.get('run') is None
     else:checks['observed']=r.get('status')=='observed' and r.get('run',{}).get('status')==('queued' if case=='queued' else 'completed')
     record['checks']=checks;record['classification']='PASS' if all(checks.values()) else 'FAIL'
    else:record['classification']='INCONCLUSIVE'
    records.append(record)
 out={'scope':'product owner fixture only; not fresh behavior, live GitHub, or delivery','records':records,'authorizes_landing':False}
 (BASE/'process-results.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'counts':{arm:{s:sum(r['arm']==arm and r['classification']==s for r in records) for s in ('PASS','FAIL','INCONCLUSIVE')} for arm in ('baseline','treatment')},'raw':str(BASE/'process-results.json'),'authorizes_landing':False}))

if __name__=='__main__':main()
