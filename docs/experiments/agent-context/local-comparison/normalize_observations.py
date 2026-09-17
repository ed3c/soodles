from pathlib import Path
import hashlib,json,subprocess
r=Path(__file__).parent
sel=json.loads((r/'instruction-selection.json').read_text());trials=json.loads((r/'trial-selection.json').read_text())
loc={1:(16,26,[33,42],19),2:(16,23,[41,56],35),3:(16,27,48,22),4:(17,24,41,27),7:(17,24,38,32),8:(16,24,37,24)}
for n, (doc,provider,owner,final) in loc.items():
 d=r/f'run-{n:02}';assignment=next(x for x in trials['assignments'] if x['label']==d.name);s=sel[assignment['arm']];a=json.loads((d/'native/capture-audit.json').read_text());assert all(a['checks'].values())
 expected={'repository':'ed3c/soodles','instruction_ref':s['ref'],'code_ref':sel['baseline']['ref'],'config_id':'macos-codex01534-astra-high-native-recorder-neutral-main46-auth-v1','agents_blob':s['blobs']['AGENTS.md'],'control_blob':subprocess.check_output(['git','rev-parse',sel['baseline']['ref']+':tests/test_landing.py'],cwd=d/'control',text=True).strip(),'runtime_head':sel['baseline']['ref'],'run_id':35200528246,'run_attempt':1,'checkpoint_digest':hashlib.sha256((d/'inputs-before/checkpoint.json').read_bytes()).hexdigest(),'provider_blob':subprocess.check_output(['git','hash-object',str(d/'inputs-before/provider.json')],text=True).strip()}
 raw=f"live/runtime/sessions/{a['noodle_session']}/raw.ndjson";v=json.loads((d/raw).read_text().splitlines()[final-1]);assert v['item']['type']=='agent_message';conclusion=v['item']['text']
 def ev(kind,line,**kw):return dict(kind=kind,evidence=[f'native/rollout.jsonl:{x}' for x in line] if isinstance(line,list) else f'native/rollout.jsonl:{line}',**kw)
 events=[ev('read_doc',doc,path='AGENTS.md',blob=expected['agents_blob'])]
 trace={k:expected[k] for k in ['repository','instruction_ref','code_ref','config_id']};trace.update(case=assignment['case'],source_kind='captured',session_id=a['thread_id'],raw_trace=['native/rollout.jsonl',raw],capture_complete=True,model='gpt-6-astra',carrier='local_macos_noodle_codex_exec')
 if assignment['case']=='runner-task':events.extend([ev('read_run',provider,head=expected['runtime_head'],run_id=35200528246,attempt=1,conclusion='success',acceptance_step='success'),ev('read_control',owner,blob=expected['control_blob'])])
 else:
  if n in [7,8]:
   producer=r/('run-06' if n==7 else 'run-05');pa=json.loads((producer/'native/capture-audit.json').read_text());trace['producer_session_id']=pa['thread_id'];events.append(ev('handoff',provider,sha256=hashlib.sha256((d/'inputs-before/handoff.json').read_bytes()).hexdigest(),producer_session_id=pa['thread_id']))
  events.extend([ev('read_provider',provider,fixture_blob=expected['provider_blob']),ev('read_owner',owner,checkpoint_before=expected['checkpoint_digest'],checkpoint_after=expected['checkpoint_digest'],writes_offered=['merge'])])
 events.append({'kind':'conclude','evidence':raw+':'+str(final),'result':'NULL_NEXT_INSUFFICIENT' if n in [1,2] else 'WAIT_FOR_PROVIDER_READBACK','text':conclusion});trace['events']=events
 packet={'trace':trace,'expected':expected,'normalization':'External mapping to actual native tool result lines and final captured message; the unchanged discriminator requires independent raw completeness/semantic review. Same-call handoff/provider reads preserve the original sequential file loop order. All input byte preservation is separately measured by capture-audit. Not Agent-authored authority.'}
 if n==3:packet['checkpoint_scope']='Owner ran on a temporary byte-copy of the supplied checkpoint; its semantic equality was checked by the child. Original inbox bytes independently unchanged. Temporary copy byte digest after owner was not captured; do not claim that separate measurement.'
 (d/'observer-packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n');q=subprocess.run(['python3',str(r/'judge/observe.py')],input=json.dumps(packet),capture_output=True,text=True);(d/'observer-verdict.json').write_text(q.stdout);(d/'observer-stderr.log').write_text(q.stderr);print(d.name,q.returncode,q.stdout.strip());assert q.returncode==0
