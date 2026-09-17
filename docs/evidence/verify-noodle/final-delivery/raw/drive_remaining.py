from pathlib import Path
import base64,hashlib,importlib.util,json,os,shutil,subprocess,tempfile,tomllib
r=Path(__file__).parent; old=r.parent/'noodle84-20260917'; w=Path('/Users/neon/soodles/.worktrees/soodles-46-0-execute'); project=w.parent.parent
b=old/'noodle-merged-ca81'; out=r/'maintenance';out.mkdir(exist_ok=False)
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
doctor('recovery')
selection=json.loads((old/'preserved-input-selection.json').read_text());src=old/'preserved-soodles-input'
assert all(digest(src/name)==value for name,value in selection['files'].items())
with tempfile.TemporaryDirectory(prefix='noodle46-recovery-') as tmp:
 root=Path(tmp)/'control';shutil.copytree(src,root);(root/'.noodle.toml').write_text('mode="manual"\n[server]\nenabled=false\n');runtime=root/'.noodle'
 shutil.copytree(runtime,out/'recovery-before'); original=(runtime/'orders-next.json').read_bytes()
 before={name:(runtime/name).read_bytes() for name in ['state.snapshot.json','orders.json']}
 first=json.loads(run('recovery-inspect',[b,'--project-dir',root,'admission','inspect']));assert first['status']=='recoverable'
 def next_call(label,value):
  argv=value['next']['argv'];assert argv[0]==str(b) and argv[1:3]==['--project-dir',str(root)]
  return json.loads(run(label,argv))
 retired=next_call('recovery-retire',first);assert retired['status']=='retired'
 final=next_call('recovery-fresh-next',retired);assert final['status']=='no_proposal' and not final['next']['argv']
 archive=runtime/'admission-retirements';shutil.copytree(archive,out/'recovery-archive')
 def contains(v):
  if isinstance(v,dict):return any(contains(x) for x in v.values())
  if isinstance(v,list):return any(contains(x) for x in v)
  if isinstance(v,str):
   if v.encode()==original:return True
   try:return base64.b64decode(v,validate=True)==original
   except (ValueError,UnicodeError):pass
  return False
 assert any(p.read_bytes()==original or contains(json.loads(p.read_text())) for p in archive.rglob('*') if p.is_file())
 assert all((runtime/name).read_bytes()==raw for name,raw in before.items()) and not (runtime/'orders-next.json').exists()
 save(out/'recovery-normal.json',{'classification':'GREEN','final':final,'canonical_and_orders_unchanged':True,'archive_preserved':True,'scratch':str(root),'authorizes_landing':False})
assert not root.exists() and all(digest(src/name)==value for name,value in selection['files'].items())
for label,filename in [('fixed-recovery','recovery-observer.py'),('fixed-refusal','refusal-observer.py')]:
 doctor(label)
 expected=json.loads((r/'observer-selection.json').read_text())['recovery_observer'][str(old/filename)];assert digest(old/filename)==expected
 run(label,['python3',old/filename,b,out/(label+'-evidence')])
# Observe cleanup of fixed observers' temporary roots and their synthetic PIDs.
fixed=json.loads((out/'fixed-refusal-evidence/receipt.json').read_text());cleanup=[]
for c in fixed['cases']:
 assert not Path(c['argv'][2]).exists()
 value=json.loads(c['stdout'])
 cleanup.append({'case':c['case'],'scratch_absent':True,'continuation':value.get('next')})
save(out/'fixed-observer-limits.json',{'cases':cleanup,'unknown_ambiguous_live_coverage':False,'refusal_orders_byte_coverage':False,'synthetic_group_final_absence':'not emitted by fixed observer; independent system process inventory retained','authorizes_landing':False})
run('process-inventory',['ps','-axo','pid,ppid,pgid,command'])
doctor('handoff')
run('handoff-status',[b,'--project-dir',project,'status'])
sid='soodles-46-0-execute-20260917-081036-db7f05';session=project/'.noodle/sessions'/sid
shutil.copytree(session,out/'original-session');shutil.copy2(project/'.noodle/state.snapshot.json',out/'canonical.json');shutil.copy2(project/'.noodle/orders.json',out/'orders.json');shutil.copy2(project/'.noodle.toml',out/'noodle.toml')
state=json.loads((out/'canonical.json').read_text());order=state['state']['orders']['soodles-46'];assert order['status']=='completed'
config=tomllib.loads((out/'noodle.toml').read_text());assert 'require_typed_outcome = true' in (out/'noodle.toml').read_text()
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
