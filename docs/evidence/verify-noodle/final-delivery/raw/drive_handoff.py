from pathlib import Path
import base64,hashlib,importlib.util,json,os,shutil,subprocess,tempfile,tomllib
r=Path(__file__).parent; old=r.parent/'noodle84-20260917'; w=Path('/Users/neon/soodles/.worktrees/soodles-46-0-execute'); project=w.parent.parent
b=old/'noodle-merged-ca81'; out=r/'maintenance-handoff';out.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('recorder',w/'.agents/skills/verify-soodles/scripts/record_context.py');rec=importlib.util.module_from_spec(spec);spec.loader.exec_module(rec)
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(label,argv):
 result,stdout,stderr=rec.record(out,label,list(map(str,argv)));assert result['exit_code']==0,(label,stderr.decode());return stdout
def doctor(label):
 run(label+'-launch',[b,'--help']);run(label+'-version',[b,'version'])
 build=run(label+'-build',['go','version','-m',b]).decode()
 sel=json.loads((r/'observer-selection.json').read_text());assert digest(b)==sel['noodle']['sha256']
 head=run(label+'-source',['git','-C',sel['source_root'],'rev-parse','HEAD']).decode().strip()
 assert head==sel['source_commit'] and 'vcs.revision='+head in build and 'vcs.modified=false' in build
 assert run(label+'-clean',['git','-C',sel['source_root'],'status','--porcelain'])==b''
doctor('handoff')
run('handoff-status',[b,'--project-dir',project,'status'])
sid='soodles-46-0-execute-20260917-081036-db7f05';session=project/'.noodle/sessions'/sid
shutil.copytree(session,out/'original-session');shutil.copy2(project/'.noodle/state.snapshot.json',out/'canonical.json');shutil.copy2(project/'.noodle/orders.json',out/'orders.json');shutil.copy2(project/'.noodle.toml',out/'noodle.toml')
state=json.loads((out/'canonical.json').read_text());order=state['state']['orders']['soodles-46'];assert order['status']=='completed'
config=tomllib.loads((out/'noodle.toml').read_text());assert config['agents']['codex']['require_typed_outcome'] is True
events=[json.loads(line) for line in (session/'events.ndjson').read_text().splitlines()];typed=[x for x in events if x['type']=='stage_message' and x.get('payload',{}).get('outcome')]
assert len(typed)==1 and typed[0]['payload']['order_id']=='soodles-46' and typed[0]['payload']['stage_index']==0 and typed[0]['payload']['outcome']=='completed'
exit_record=json.loads((r/'process-exits'/sid/'exit.json').read_text());assert exit_record['waited'] and exit_record['returncode']==0 and not exit_record['forwarded_signals']
absence=[]
for kind,pid in [('pid',exit_record['child_pid']),('pgid',exit_record['child_pgid']),('pid',exit_record['recorder_pid'])]:
 try:(os.killpg if kind=='pgid' else os.kill)(pid,0)
 except ProcessLookupError:absence.append({'kind':kind,'id':pid,'absent':True})
 else:raise AssertionError((kind,pid,'still present'))
assert any(e['effect']['type']=='initial_admission' and e['effect']['payload']['order_id']=='soodles-46' for e in state['effect_ledger'])
save(out/'handoff.json',{'classification':'GREEN','scope':'original admitted authoring handoff; provider delivery separate','order':order,'typed_event':typed[0],'external_exit':exit_record,'kernel_absence':absence,'checkout_recreated_after_owner_cleanup':True,'skill_loading_claim':False,'authorizes_landing':False})
manifest={str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()}
save(out/'receipt.json',{'outcome':'changed','features':{'admission-recovery':'VERIFIED','order-handoff':'VERIFIED'},'corrections':['index pending language','non-schedule typed enforcement scope','fixed observer coverage limits'],'file_digests':manifest,'evidence_survives_cleanup':True,'authorizes_landing':False})
print(json.dumps({'outcome':'changed','features':['admission-recovery','order-handoff'],'files':len(manifest)}))
