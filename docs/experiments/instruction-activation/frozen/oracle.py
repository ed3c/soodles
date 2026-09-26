"""External fixed process oracle; provider/Noodle-shaped state is disposable fixture data."""
import copy, hashlib, json, os, pathlib, subprocess, sys, traceback
SOURCE=pathlib.Path(sys.argv[1]).resolve(); OUT=pathlib.Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True,exist_ok=True)
FROZEN=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(SOURCE),str(FROZEN/'fixtures')]
import issue_admission as ia, issue_execution as ix, issue_atom as atom, supervisor_admission as sa
import test_supervisor_admission
test_supervisor_admission.ROOT=SOURCE
from test_supervisor_admission import SupervisorFixture
from test_issue_execution import IssueExecutionTests
from test_issue_atom import IssueAtomTests
sha=lambda b:hashlib.sha256(b).hexdigest()
results=[]
def case(name,fn):
 try: data=fn(); results.append({'case':name,'verdict':'PASS','observation':data})
 except Exception as e: results.append({'case':name,'verdict':'FAIL','error':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc()})
def refuse(fn, effect):
 try: fn()
 except (ia.AdmissionRefusal,atom.AtomRefusal) as e:
  assert not effect(), 'refusal left dependent effects'
  return {'invalid':e.invalid,'effect':False}
 raise AssertionError('invalid input was accepted')
def producer(mode):
 f=SupervisorFixture()
 try:
  p='.agents/skills/execute/SKILL.md'; b=subprocess.check_output(['git','show',f.head+':'+p],cwd=f.root)
  pin={'path':p,'sha256':sha(b)}; pins=[pin]
  if mode=='wrong_digest': pins=[{**pin,'sha256':'0'*64}]
  if mode=='missing_file': pins=[{**pin,'path':'missing.md'}]
  if mode=='duplicate': pins=[pin,pin]
  if mode=='traversal': pins=[{**pin,'path':'../escape.md'}]
  if mode=='empty': pins=[]
  output=f.external/'selected'
  if mode!='valid': return refuse(lambda:f.prepare('selected',instruction_pins=pins),output.exists)
  # Dirty checkout is deliberately irrelevant: use exact selected Git bytes.
  (f.root/p).write_text('UNSELECTED DIRTY INSTRUCTIONS\n')
  output,prepared=f.prepare('selected',instruction_pins=pins)
  env=json.loads((output/'envelope.json').read_text())
  expected={'source_head':f.head,'files':[{'path':p,'sha256':sha(b),'content':b.decode()}]}
  assert env['schema']==2 and env['execution']['instruction_context']==expected
  next_=ix.inspect_schedule(f.root,{**f.schedule_env,'SOODLES_ADMISSION_LAUNCHER':prepared['launcher']})['next']
  process_env={k:v for k,v in os.environ.items() if not k.startswith('NOODLE_')}
  process_env['FIXTURE_ISSUE_READBACK']=str(f.issue_path)
  completed=subprocess.run(next_['argv'],cwd=f.root,env=process_env,capture_output=True,text=True,timeout=30)
  (OUT/'producer-cli.json').write_text(json.dumps({'argv':next_['argv'],'exit':completed.returncode,'stdout':completed.stdout,'stderr':completed.stderr},indent=2)+'\n')
  assert completed.returncode==0, completed.stderr+completed.stdout
  proposal=json.loads((f.root/'.noodle/orders-next.json').read_text())
  prompt=json.loads(proposal['orders'][0]['stages'][0]['prompt'])
  assert prompt['instruction_context']==expected
  assert not f.child_marker.exists()
  return {'envelope_schema':env['schema'],'context':expected,'proposal_context_equal':True,'process_exit':completed.returncode,'child_started':False,'provider_transport_events':[],'scope':'real CLI with provider/owner fixtures'}
 finally:f.close()
def worker(mode):
 f=IssueExecutionTests();f.setUp()
 try:
  if mode!='legacy':
   b=subprocess.check_output(['git','show',f.envelope['execution']['source_head']+':allowed.py'],cwd=f.root)
   context={'source_head':f.envelope['execution']['source_head'],'files':[{'path':'allowed.py','sha256':sha(b),'content':b.decode()}]}
   f.envelope['schema']=2;f.envelope['execution']['instruction_context']=context
   if mode=='bad_content':context['files'][0]['content']+='altered'
   if mode=='wrong_source':context['source_head']='0'*40
   if mode=='missing_context':del f.envelope['execution']['instruction_context']
   f.bind_envelope()
  if mode in ('bad_content','wrong_source','missing_context'):
   return refuse(lambda:f.admit('supervised'),lambda:(f.runtime/'orders-next.json').exists() or f.effect.exists())
  f.admit('supervised'); f.promote_fixture()
  stage=f.snapshot['state']['orders']['soodles-18']['stages'][0]
  if mode in ('dropped_prompt','changed_prompt'):
   prompt=json.loads(stage['prompt'])
   if mode=='dropped_prompt':del prompt['instruction_context']
   else:prompt['instruction_context']['files'][0]['content']+='altered'
   stage['prompt']=json.dumps(prompt);f.save_owner()
   return refuse(f.launch,f.effect.exists)
  launched=f.launch();assert f.effect.read_text()=='observed'
  return {'child_sentinel':'observed','context_present':'instruction_context' in json.loads(stage['prompt']),'session_id':launched['session_id'],'scope':'actual sentinel process; fixture Noodle state'}
 finally:f.doCleanups()
def authorization(mode):
 f=IssueAtomTests();f.setUp()
 try:
  p='.agents/skills/execute/SKILL.md';pin={'path':p,'sha256':sha((f.root/p).read_bytes())}
  f.authorization['schema_version']=3;f.authorization['instruction_pins']=[pin]
  if mode=='wrong_digest':pin['sha256']='0'*64
  if mode=='missing':f.authorization.pop('instruction_pins')
  f.path.write_text(json.dumps(f.authorization));digest=sha(f.path.read_bytes())
  if mode!='valid':return refuse(lambda:atom.validate_authorization(f.path,digest),lambda:f.path.with_name(f.path.name+'.state.json').exists())
  a,_=atom.validate_authorization(f.path,digest)
  # Use the existing owner seam, not a reconstructed supervisor invocation.
  issue={'number':131,'title':a['issue']['title'],'body':a['issue']['body'],'state':'open','updated_at':'2026-09-23T00:00:00Z','url':'https://api.github.com/repos/ed3c/soodles/issues/131','html_url':'https://github.com/ed3c/soodles/issues/131'}
  envelope,d=atom.create_envelope(a,issue,issue['body'],f.outer/'live/admission/envelope.json',environ={'NOODLES_TOKEN_COMMAND':'printf fixture-only'})
  assert envelope['schema']==2 and envelope['execution']['instruction_context']['files'][0]['sha256']==pin['sha256']
  return {'auth_schema':3,'envelope_schema':2,'owner_passthrough':True,'envelope_sha256':d}
 finally:f.doCleanups()
for m in ['valid','wrong_digest','missing_file','duplicate','traversal','empty']:case('producer_'+m,lambda m=m:producer(m))
for m in ['valid','legacy','bad_content','wrong_source','missing_context','dropped_prompt','changed_prompt']:case('worker_'+m,lambda m=m:worker(m))
for m in ['valid','wrong_digest','missing']:case('authorization_'+m,lambda m=m:authorization(m))
report={'oracle_sha256':sha(pathlib.Path(__file__).read_bytes()),'subject_root':str(SOURCE),'subject_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip(),'cases':results,'authorizes_landing':False,'network':'fixture-only; no provider transport'}
(OUT/'controls.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':sum(x['verdict']=='PASS' for x in results),'total':len(results),'results':str(OUT/'controls.json')}))
sys.exit(0 if all(x['verdict']=='PASS' for x in results) else 1)
