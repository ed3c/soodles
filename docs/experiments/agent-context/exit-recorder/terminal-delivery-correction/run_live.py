from pathlib import Path
import json,os,signal,subprocess,time,fcntl,uuid,shutil
r=Path(__file__).parent;root=r/'control';runtime=root/'.noodle';out=r/'live';out.mkdir()
import hashlib
selection=json.loads((r/'judge-selection.json').read_text())
for name,digest in selection['files'].items():
 assert hashlib.sha256((r/'judge'/name).read_bytes()).hexdigest()==digest, name
assert hashlib.sha256((r/'installed/docs/experiments/agent-context/local/record_process.py').read_bytes()).hexdigest()==selection['files']['record_process.py']
assert not list((runtime/'sessions').glob('*/process.json')), 'fresh control root must have no previous session'

d=json.loads((r/'worker-doctor.json').read_text());expected=str(root/'.worktrees/soodles-39-0-execute')
assert d['checks']['config.load']['details']['cwd']==expected
assert d['checks']['git.environment']['details']['repo root']==expected and d['checks']['git.environment']['details']['repo detected']=='true'
assert (runtime/'orders-next.json').exists()
# An existing Noodle control changes the run mode; no checkpoint edits or scheduler replacement.
request={'id':'issue39-capability-'+uuid.uuid4().hex,'action':'mode','value':'supervised'}
(out/'mode-request.json').write_text(json.dumps(request,indent=2)+'\n')
with (runtime/'control.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 with (runtime/'control.ndjson').open('a') as f:f.write(json.dumps(request)+'\n');f.flush();os.fsync(f.fileno())
 fcntl.flock(lock,fcntl.LOCK_UN)
start=time.monotonic();status='deadline';observed=None
with (out/'stdout.log').open('w') as stdout,(out/'stderr.log').open('w') as stderr:
 p=subprocess.Popen(['/Users/neon/.codex/experiments/noodle82-20260916/noodle','start'],cwd=root,env={**os.environ,'SOODLES_ADMISSION_LAUNCHER':str(r/'admission'),'PYTHONDONTWRITEBYTECODE':'1'},stdout=stdout,stderr=stderr,start_new_session=True)
 (out/'launch.json').write_text(json.dumps({'argv':p.args,'pid':p.pid,'cwd':str(root),'deadline_seconds':180,'parent_emits_outcome':False},indent=2)+'\n')
 while time.monotonic()-start<180:
  if p.poll() is not None:status='loop_exited';break
  state=json.loads((runtime/'state.snapshot.json').read_text());order=state.get('state',{}).get('orders',{}).get('soodles-39')
  if order and order.get('stages') and order['stages'][0].get('status') in ['review','completed','failed']:
   status='worker_'+order['stages'][0]['status'];observed=state;break
  time.sleep(.15)
 if p.poll() is None:
  p.send_signal(signal.SIGTERM)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
 report={'status':status,'loop_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'snapshot_at_stop':observed,'authorizes_landing':False}
 (out/'observation.json').write_text(json.dumps(report,indent=2)+'\n');shutil.copytree(runtime,out/'runtime',ignore=shutil.ignore_patterns('*.lock'))
 print(json.dumps({k:v for k,v in report.items() if k!='snapshot_at_stop'}))
