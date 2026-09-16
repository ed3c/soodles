from pathlib import Path
import json,os,signal,subprocess,time,fcntl,uuid,shutil
r=Path(__file__).parent;root=Path('/Users/neon/soodles');runtime=root/'.noodle';out=r/'noodle-reconcile';out.mkdir()
assert (root/'.noodle.toml').read_text().startswith('mode = "manual"')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()=='e4b4a8487855b75ef2d47087019bb52c4d5ffd6c'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True)
assert subprocess.check_output(['git','rev-list','HEAD..soodles-18-0-execute','--count'],cwd=root,text=True).strip()=='0'
prior={p.name for p in (runtime/'sessions').iterdir()};start=time.monotonic()
request={'id':'soodles18-provider-landed-'+uuid.uuid4().hex,'action':'merge','order_id':'soodles-18'}
(out/'request.json').write_text(json.dumps(request,indent=2)+'\n')
with (runtime/'control.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 with (runtime/'control.ndjson').open('a') as target:
  target.write(json.dumps(request)+'\n');target.flush();os.fsync(target.fileno())
 fcntl.flock(lock,fcntl.LOCK_UN)
status='deadline';ack=None
with (out/'stdout.log').open('w') as stdout,(out/'stderr.log').open('w') as stderr:
 p=subprocess.Popen(['/Users/neon/.codex/experiments/noodle82-20260916/noodle','start'],cwd=root,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=stdout,stderr=stderr,start_new_session=True)
 (out/'launch.json').write_text(json.dumps({'argv':p.args,'cwd':str(root),'pid':p.pid,'mode':'manual','deadline_seconds':45},indent=2)+'\n')
 while time.monotonic()-start<45:
  if p.poll() is not None:status='loop_exited';break
  acks=[json.loads(x) for x in (runtime/'control-ack.ndjson').read_text().splitlines() if x]
  ack=next((x for x in acks if x.get('id')==request['id']),None)
  if ack:
   state=json.loads((runtime/'state.snapshot.json').read_text());order=state['state']['orders']['soodles-18']
   if ack.get('status')!='ok':status='control_refused';break
   if order['status']=='completed':status='original_order_completed';break
  time.sleep(.1)
 if p.poll() is None:p.send_signal(signal.SIGTERM);p.wait(timeout=15)
 final=json.loads((runtime/'state.snapshot.json').read_text());new={p.name for p in (runtime/'sessions').iterdir()}-prior
 report={'observation':status,'control_ack':ack,'loop_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'new_sessions':sorted(new),'order':final['state']['orders']['soodles-18'],'authorizes_landing':False}
 (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
 shutil.copy2(runtime/'state.snapshot.json',out/'state.snapshot.json');shutil.copy2(runtime/'control-ack.ndjson',out/'control-ack.ndjson')
 print(json.dumps({k:v for k,v in report.items() if k!='order'}))
 assert status=='original_order_completed' and not new and p.returncode==0
