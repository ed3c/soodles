"""Fixed disposable shared-owner input. Does not select a production owner."""
import contextlib,fcntl,io,json,os,sys,time
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
def main():
 source=Path(sys.argv[1]).resolve();case=sys.argv[2];out=Path(sys.argv[3]);out.mkdir(exist_ok=False)
 sys.path[:0]=[str(source),str(P)]
 import issue_atom as atom,soodles
 from fixture import Fixture,Provider
 f=Fixture();f.setUp();locks=[];calls={'supplier':0,'provider_reads':0,'provider_writes':0,'start':0}
 try:
  runtime=f.root/'.noodle';config=f.root/'.noodle.toml'
  if case=='same_owner':
   paths,state=f.startup_fixture()
   config.write_bytes((paths['envelope'].parent/'noodle.toml').read_bytes())
   state.update(issue={'number':131,'url':'https://github.com/ed3c/soodles/issues/131'},writes={},schema_version=1,publication=None,noodle_start={'status':'started','config_sha256':atom.digest_file(config)})
   atom.save_json(paths['state'],state)
   envspec=atom.read_json(paths['envelope'],'envelope');envspec['contract']=atom.issue_admission.parse_contract(f.authorization['issue']['body'])
   order={'stages':[{'status':'running','skill':'execute','provider':'codex','model':'fixture-model','prompt':json.dumps(atom.issue_execution.projection(envspec,state['envelope_sha256'],'supervised')),'attempts':[{'status':'running','session_id':'fixture-existing'}]}]}
   atom.save_json(runtime/'state.snapshot.json',{'state':{'orders':{'soodles-131':order}},'effect_ledger':[]})
  else:
   runtime.mkdir();config.write_text('owner = "retained"\n')
   f.authorization['host_config_sha256']=atom.digest_file(config)
   f.path.write_text(json.dumps(f.authorization));f.digest=atom.digest_file(f.path);f.env['SOODLES_AUTHORIZATION_SHA256']=f.digest
   active=case in ['foreign_live','foreign_stopped','foreign_checkpoint']
   snapshot={'state':{'orders':{'soodles-130':{'stages':[{'status':'running','attempts':[]}]}} if active else {}},'effect_ledger':[]}
   atom.save_json(runtime/'state.snapshot.json',snapshot)
   if case=='malformed_owner':(runtime/'state.snapshot.json').write_text('{broken')
   if case=='foreign_checkpoint':
    atom.save_json(atom.artifact_paths(f.path)['state'],{'schema_version':1,'authorization_sha256':f.digest,'phase':'issue','writes':{},'issue':None,'publication':None})
  held='noodle.lock' if case in ['same_owner','foreign_live','foreign_checkpoint'] else 'issue-atom.lock' if case=='entry_busy' else None
  if held:
   lock=(runtime/held).open('a+b');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(lock)
  before={name:atom.digest_file(runtime/name) if (runtime/name).exists() else None for name in ['state.snapshot.json','orders-next.json','control.ndjson']}
  config_before=atom.digest_file(config);paths=atom.artifact_paths(f.path);checkpoint_before=atom.digest_file(paths['state']) if paths['state'].exists() else None
  class Synthetic(Provider):
   def __init__(self,*a,**k):super().__init__()
   def issues(self):calls['provider_reads']+=1;return super().issues()
   def issue(self,n):calls['provider_reads']+=1;return super().issue(n)
   def create_issue(self,title,body):
    calls['provider_writes']+=1;v=super().create_issue(title,body);v['url']='https://api.github.com/repos/ed3c/soodles/issues/131';return v
  provider=Synthetic()
  if case=='same_owner':f.ready_issue(provider)
  def supplier(*a,**k):calls['supplier']+=1;return 'fixture-token'
  class Reached(Exception):pass
  def start(*a,**k):calls['start']+=1;raise Reached()
  stdout=io.StringIO();stderr=io.StringIO();boundary=None;started=time.monotonic();drive=atom.drive
  # Actual CLI and admission run. Only positive idle input is stopped at the
  # existing start boundary; refusal cases exercise the real ensure_noodle.
  extra=patch.object(atom,'ensure_noodle',side_effect=start) if case=='idle' else contextlib.nullcontext()
  with patch.dict(os.environ,{**f.env,'PATH':os.environ['PATH']},clear=True),patch.object(atom,'GitHubProvider',return_value=provider),patch.object(atom.provider_credential,'supply_token',side_effect=supplier),patch.object(sys,'argv',['soodles','atom','run',str(f.path)]),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr),patch.object(atom,'drive',side_effect=lambda path:drive(path,timeout=0)),extra:
   try:code=soodles.main()
   except Reached:code=0;boundary='existing_start'
  result={'case':case,'exit':code,'stdout':stdout.getvalue(),'stderr':stderr.getvalue(),'boundary':boundary,'calls':calls,'checkpoint_before':checkpoint_before,'checkpoint_after':atom.digest_file(paths['state']) if paths['state'].exists() else None,'proposal_created':(runtime/'orders-next.json').exists(),'existing_owner_unchanged':all(before[n]==(atom.digest_file(runtime/n) if (runtime/n).exists() else None) for n in before if n!='orders-next.json'),'config_unchanged':config_before==atom.digest_file(config),'elapsed_seconds':time.monotonic()-started,'authorizes_landing':False}
 finally:
  for lock in locks:lock.close()
  f.doCleanups()
 result['disposable_removed']=not f.outer.exists();(out/'process.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
