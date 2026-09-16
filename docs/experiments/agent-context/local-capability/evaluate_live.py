from pathlib import Path
import json, subprocess, collections
r=Path(__file__).resolve().parent
session='soodles-39-0-execute-20260916-192945-2432f9'
s=r/'live/runtime/sessions'/session
read=lambda p: json.loads(p.read_text())
lines=lambda p: [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
raw=lines(s/'raw.ndjson'); rollout=lines(r/'native/rollout.jsonl')
packet=dict(raw_events=raw,history=read(r/'native/history.json'),rollout=rollout,expected=dict(carrier='local_macos_noodle_codex_exec',model='gpt-6-astra',marker='SOODLES39_NATIVE_CAPTURE_V1',exit_code=None))
(r/'native/capability-packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
result=subprocess.run(['python3',str(r/'controls-v2/judge/capability.py')],input=json.dumps(packet),text=True,capture_output=True)
(r/'native/capability-verdict.json').write_text(result.stdout)
(r/'native/capability-stderr.log').write_text(result.stderr)
ends=[e['item'] for e in raw if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
events=lines(s/'events.ndjson'); outcomes=[e for e in events if e.get('type')=='stage_message']
snap=read(r/'live/runtime/state.snapshot.json'); stage=snap['state']['orders']['soodles-39']['stages'][0]
audit=dict(judge_exit=result.returncode,raw_event_counts=dict(collections.Counter(e.get('type') for e in raw)),commands=[dict(id=e['id'],command=e['command'],exit_code=e.get('exit_code')) for e in ends],native_item_errors=[e['item'] for e in raw if e.get('item',{}).get('type')=='error'],typed_outcomes=outcomes,typed_outcome_matches=len(outcomes)==1 and outcomes[0]['session_id']==session and outcomes[0]['payload']['order_id']=='soodles-39' and outcomes[0]['payload']['stage_index']==0,stage_status=stage['status'],actual_codex_exit_code=stage['attempts'][0]['exit_code'],exit_code_reason='Noodle attempt exit_code is null; exited metadata and turn.completed cannot reconstruct OS exit status. Outer loop/read-only app-server exit 0 is a different process.',authorizes_landing=False)
(r/'native/raw-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(result.stdout)
print(json.dumps({k:v for k,v in audit.items() if k!='commands'},ensure_ascii=False,indent=2))
