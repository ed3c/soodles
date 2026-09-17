from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path(__file__).parent;root=Path('/Users/neon/soodles');old=json.loads((r/'execution-envelope.json').read_text());state=json.loads((root/'.noodle/state.snapshot.json').read_text());stage=state['state']['orders']['soodles-44']['stages'][0];assert stage['status']=='review'
for attempt in stage['attempts']:
 pid=json.loads((root/'.noodle/sessions'/attempt['session_id']/'process.json').read_text())['pid']
 for target in [pid,-pid]:
  try:os.kill(target,0)
  except ProcessLookupError:pass
  else:raise RuntimeError('old writer remains')
assert subprocess.check_output(['git','status','--porcelain'],cwd=root/'.worktrees/soodles-44-0-execute')==b''
archive=r/'attempt1-installed';archive.mkdir()
for name in ['admission','backlog','execution-envelope.json','selection.json']:shutil.copy2(r/name,archive/name)
shutil.copytree(r/'provider',archive/'provider')
evidence=r/'worker-evidence-continuation';evidence.mkdir()
task='''Continue the ORIGINAL soodles-44 order and same clean 0cda9c2ee57ed598257048f50829fb36893d3b80 worktree. The first Agent physically proved authenticated HTTP200 then304 with identical44 Issue bytes/remaining6199, no-token refusal, and consumer16/16. It correctly emitted blocked because its redirect test could not bind localhost under the child sandbox. Its natural exit0 and failure are preserved. Do not reinterpret that child failure as GREEN and do not retry localhost or change permissions.
Your substantive bounded task is to review the preserved raw worker-evidence and the supervisor-reader-tests.json under /Users/neon/.codex/experiments/soodles44-delivery-20260917, which ran the SAME unchanged16 reader controls with actual exit0 on the supervisor carrier, including real redirect server. Confirm exact clean candidate, inspect redirect test and corresponding implementation, check live CLI raw outputs versus receipt identities/statuses, check cache absent, confirm all16 supervisor tests and16 child consumer tests passed, and name the distinct carriers/scope in a new handoff under worker-evidence-continuation. You may run short read-only commands; do not rerun full suites or model sessions. Do not edit source, commit, call provider, mint tokens, merge or close. Parent did not supply your outcome. If this evidence and code review substantiates the verification stage, emit ONE stage_message completed/blocking false using actual NOODLE_* identities and measured /Users/neon/.codex/experiments/noodle84-20260917/noodle-merged-ca81 after obtaining its actual help/schema. If any concrete unresolved inconsistency remains, emit blocked/blocking true. This is verification stage completion, not Issue resolution. Do not emit stage_yield or write an exit code. Return immediately after your own typed event. Deadline300seconds.'''
new={**old,'execution':{**old['execution'],'task':task}}
p=r/'execution-envelope-continuation.json';p.write_text(json.dumps(new,indent=2)+'\n');oldpin=hashlib.sha256((r/'execution-envelope.json').read_bytes()).hexdigest();pin=hashlib.sha256(p.read_bytes()).hexdigest()
for q in [r/'admission',r/'backlog',r/'provider/codex']:
 text=q.read_text().replace(str(r/'execution-envelope.json'),str(p)).replace(oldpin,pin);q.write_text(text);q.chmod(0o755)
selection={'envelope':str(p),'sha256':pin,'original_order':'soodles-44','source_head':new['execution']['source_head'],'scope':'inspect physical cross-carrier evidence; child localhost refusal retained','previous_envelope':str(r/'execution-envelope.json')};(r/'continuation-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
script=(r/'run.py').read_text().replace("out=r/'live';out.mkdir()","out=r/'live-continuation';out.mkdir()")
start=script.index('  # Existing owner initializes');end=script.index('  start=time.monotonic()',start)
replacement='''  selection=json.loads((r/'continuation-selection.json').read_text());e=json.loads(Path(selection['envelope']).read_text())
  import sys
  sys.path.insert(0,str(r/'installed'));from issue_admission import validate_issue;from issue_execution import fetch_issue,projection
  prior=os.environ.get('GH_TOKEN');os.environ['GH_TOKEN']=token
  try:binding=validate_issue(fetch_issue(44),e)
  finally:
   if prior is None:os.environ.pop('GH_TOKEN',None)
   else:os.environ['GH_TOKEN']=prior
  prompt=json.dumps(projection(binding,selection['sha256'],'supervised'),sort_keys=True)
  requests=[{'action':'mode','value':'manual'},{'action':'requeue','order_id':'soodles-44'},{'action':'edit-item','order_id':'soodles-44','prompt':prompt},{'action':'mode','value':'supervised'}]
  for request in requests:request['id']='issue44-continuation-'+uuid.uuid4().hex
  (out/'control-requests.json').write_text(json.dumps(requests,indent=2)+'\\n')
  with (runtime/'control.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   with (runtime/'control.ndjson').open('a') as f:
    for request in requests:f.write(json.dumps(request)+'\\n')
    f.flush();os.fsync(f.fileno())
'''
script=script[:start]+replacement+script[end:];script=script.replace('<480','<300').replace("'deadline_seconds':480","'deadline_seconds':300")
script=script.replace("if order and order['stages'][0]['status']", "if order and len(order['stages'][0]['attempts'])>1 and order['stages'][0]['status']")
(r/'run-continuation.py').write_text(script)
print(selection)
