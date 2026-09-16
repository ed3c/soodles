from pathlib import Path
import json,os,signal,subprocess,time
archive=Path(__file__).parent;root=Path('/Users/neon/soodles');out=archive/'live-attempt-2';out.mkdir()
env=os.environ.copy();env['SOODLES_ADMISSION_LAUNCHER']=str(archive/'admission-b3850ee');env['PYTHONDONTWRITEBYTECODE']='1'
prior_sessions={p.name for p in (root/'.noodle/sessions').iterdir()}
start=time.monotonic();status='deadline';observed=None
with (out/'stdout.log').open('w') as stdout,(out/'stderr.log').open('w') as stderr:
    p=subprocess.Popen(['/Users/neon/.codex/experiments/noodle82-20260916/noodle','start'],cwd=root,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
    (out/'launch.json').write_text(json.dumps({'pid':p.pid,'deadline_seconds':180,'argv':p.args,'cwd':str(root),'parent_emits_outcome':False},indent=2)+'\n')
    while time.monotonic()-start<180:
        if p.poll() is not None: status='loop_exited';break
        path=root/'.noodle/state.snapshot.json'
        if path.exists():
            data=json.loads(path.read_text());order=data.get('state',{}).get('orders',{}).get('soodles-18')
            if order:
                stages=order.get('stages',[])
                if stages and stages[0].get('status') in ('review','failed','completed'):
                    status='owner_stage_'+stages[0]['status'];observed=data;break
        refusal = False
        for directory in (root/'.noodle/sessions').iterdir():
            if directory.name in prior_sessions: continue
            raw=directory/'raw.ndjson'
            if raw.exists():
                events=[json.loads(line) for line in raw.read_text().splitlines() if line]
                for event in events:
                    item=event.get('item',{})
                    if item.get('type')=='command_execution' and '"status": "refused"' in item.get('aggregated_output',''):
                        refusal=True
        if refusal: status='first_new_refusal_stop';break
        time.sleep(.25)
    if p.poll() is None:
        p.send_signal(signal.SIGTERM)
        try:p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            status+='; shutdown_timeout';os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    report={'observation':status,'loop_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'snapshot_at_stop':observed,'authorizes_landing':False}
    (out/'observation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='snapshot_at_stop'}))
