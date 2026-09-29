"""Fixed external owner-wait discriminator; disposable provider/process fixtures."""
import contextlib,copy,fcntl,hashlib,importlib.util,io,json,os,subprocess,sys
from pathlib import Path
from unittest.mock import patch
SOURCE=Path(sys.argv[1]).resolve();name=sys.argv[2];OUTPUT=Path(sys.argv[3]).resolve()
sys.path.insert(0,str(SOURCE));import issue_atom as atom
spec=importlib.util.spec_from_file_location('frozen_fixture',Path(__file__).with_name('fixture.py'));fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
f=fixture.IssueAtomTests();captured=io.StringIO()
with contextlib.redirect_stdout(captured),contextlib.redirect_stderr(captured):f.setUp()
try:
 paths,state=f.startup_fixture();binding=atom.read_json(paths['envelope'],'envelope');binding['contract']=atom.issue_admission.parse_contract(f.authorization['issue']['body']);oid=binding['execution']['order_id'];runtime=f.root/'.noodle';config=paths['envelope'].parent/'noodle.toml';(f.root/'.noodle.toml').write_bytes(config.read_bytes());pid=424242
 state.update(schema_version=1,issue={'number':131},writes={},publication=None,noodle_start={'status':'started','pid':pid,'argv':[str(config.parent/'start-noodle')],'config_sha256':atom.digest_file(config),'original_config':None})
 stage={'stage_index':0,'task_key':'execute','skill':'execute','provider':'codex','model':'fixture-model','runtime':'process','prompt':json.dumps(atom.issue_execution.projection(binding,state['envelope_sha256'],'supervised')),'status':'pending','attempts':None}
 if name=='own_running':stage.update(status='running',attempts=[{'attempt_id':oid+'-0-attempt-0','session_id':'fixture-writer','status':'running','worktree_name':oid+'-0-execute'}])
 sched={'order_id':'schedule','status':'active','stages':[{'stage_index':0,'task_key':'schedule','skill':'schedule','provider':'codex','model':'fixture-model','runtime':'process','prompt':'','status':'running','attempts':[{'attempt_id':'schedule-0-attempt-0','session_id':'fixture-scheduler','status':'running','worktree_name':''}]}]}
 snapshot={'state':{'orders':{'schedule':sched,oid:{'order_id':oid,'status':'active','stages':[stage]}}},'effect_ledger':[]}
 session=runtime/'sessions/fixture-scheduler';session.mkdir(parents=True);atom.save_json(session/'process.json',{'session_id':'fixture-scheduler','pid':424243})
 atom.save_json(session/'spawn.json',{'session_id':'fixture-scheduler','provider':'codex','model':'fixture-model','runtime':'process','skill':'schedule','worktree_path':str(f.root),'created_at':'2026-09-29T00:00:00Z'})
 atom.save_json(session/'meta.json',{'session_id':'fixture-scheduler','provider':'codex','model':'fixture-model','runtime':'process','status':'running','alive':True})
 if name=='own_running':
  writer=runtime/'sessions/fixture-writer';writer.mkdir();atom.save_json(writer/'process.json',{'session_id':'fixture-writer','pid':424244});atom.save_json(writer/'spawn.json',{'session_id':'fixture-writer','provider':'codex','model':'fixture-model','runtime':'process','skill':'execute','worktree_path':str(f.root/'.worktrees'/(oid+'-0-execute'))});atom.save_json(writer/'meta.json',{'session_id':'fixture-writer','status':'running','alive':True,'provider':'codex','model':'fixture-model','runtime':'process'})
 if name=='missing_admitted_order':snapshot['state']['orders'].pop(oid)
 if name=='stopped_loop':state['noodle_start']['stop_offered']=True
 if name=='foreign_spawn':atom.save_json(session/'spawn.json',{'session_id':'fixture-scheduler','provider':'codex','model':'fixture-model','runtime':'process','skill':'schedule','worktree_path':'/foreign'})
 if name=='foreign_order':snapshot['state']['orders']['foreign-22']={'order_id':'foreign-22','status':'active','stages':[{'status':'running','attempts':[]}]}
 if name=='foreign_config':(f.root/'.noodle.toml').write_text('foreign = true\n')
 if name=='unknown_start':state['noodle_start']['status']='offered'
 if name=='missing_pid':state['noodle_start'].pop('pid')
 if name=='wrong_scheduler_model':sched['stages'][0]['model']='foreign'
 if name=='malformed_scheduler_attempt':sched['stages'][0]['attempts']=[{'status':'running'}]
 if name=='wrong_order_projection':stage['prompt']='{}'
 if name=='missing_scheduler_process':(session/'process.json').unlink()
 if name=='wrong_scheduler_session':atom.save_json(session/'process.json',{'session_id':'another-session','pid':424243})
 if name=='multiple_scheduler_attempts':sched['stages'][0]['attempts'].append(dict(sched['stages'][0]['attempts'][0]))
 if name=='unknown_execute_status':stage['status']='unknown'
 atom.save_json(runtime/'state.snapshot.json',snapshot);atom.save_json(paths['state'],state)
 before={str(p):p.read_bytes() for p in [runtime/'state.snapshot.json',paths['state'],f.root/'.noodle.toml']};calls=[];real_run=subprocess.run;real_kill=os.kill
 expected=' '.join([f.authorization['noodle']['path'],'--project-dir',str(f.root),'start'])
 def run(argv,*args,**kwargs):
  if argv and argv[0]=='ps':
   calls.append({'fixture_process_read':list(argv)});return subprocess.CompletedProcess(argv,0,('foreign process' if name=='foreign_loop' else expected)+'\n','')
  return real_run(argv,*args,**kwargs)
 def kill(pid_,signal_):
  if signal_==0 and abs(pid_) in (424242,424243,424244):return None
  return real_kill(pid_,signal_)
 def forbidden(*args,**kwargs):calls.append({'forbidden_effect':True});raise AssertionError('provider/supplier must not be reached while waiting/refusing')
 with (runtime/'noodle.lock').open('a+b') as lock,patch.object(atom.subprocess,'run',side_effect=run),patch.object(atom.os,'kill',side_effect=kill),patch.object(atom.provider_credential,'supply_token',side_effect=forbidden),patch.object(atom,'ensure_noodle',side_effect=forbidden):
  if name!='unlocked_runtime':fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:result=atom.drive(f.path,timeout=0,environ=f.env)
  except atom.AtomRefusal as error:result=atom.refusal_output(error,f.path)
  except Exception as error:result={'exception':type(error).__name__,'message':str(error)}
 unchanged=all(p.read_bytes()==data for name_,data in before.items() for p in [Path(name_)])
 record={'case':name,'result':result,'calls':calls,'canonical_state_config_unchanged':unchanged,'authorizes_landing':False}
finally:f.doCleanups()
OUTPUT.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));sys.exit(1 if result.get('status')=='refused' else 0)
