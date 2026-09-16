from pathlib import Path
import json,subprocess,collections,hashlib
r=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
lines=lambda p:[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
snap=read(r/'live/runtime/state.snapshot.json');stage=snap['state']['orders']['soodles-39']['stages'][0];attempt=stage['attempts'][-1];session=attempt['session_id'];s=r/'live/runtime/sessions'/session
exit_record=read(r/'process-exits'/session/'exit.json');launch=read(r/'process-exits'/session/'launch.json');owner_process=read(s/'process.json');spawn=read(s/'spawn.json');envelope=read(r/'execution-envelope.json');execution=envelope['execution']
checks={
 'recorder_pid_matches_noodle_process':exit_record['recorder_pid']==owner_process['pid'],
 'record_identity_matches':exit_record['session_id']==session and exit_record['order_id']=='soodles-39' and exit_record['stage_index']=='0',
 'record_worktree_matches':exit_record['cwd']==spawn['worktree_path']==str(r/'control/.worktrees/soodles-39-0-execute'),
 'same_launch_and_exit':all(exit_record[k]==v for k,v in launch.items()),
 'child_is_separate':exit_record['child_pid']!=exit_record['recorder_pid'],
 'group_retained':exit_record['child_pgid']==owner_process['pid'],
 'actual_wait':exit_record['waited'] is True and type(exit_record['returncode']) is int,
 'exact_worker_chain':exit_record['argv'][2:5]==[str(r/'installed/soodles.py'),'issue','worker'] and exit_record['argv'][5]==str(r/'execution-envelope.json') and exit_record['argv'][6]==hashlib.sha256((r/'execution-envelope.json').read_bytes()).hexdigest() and exit_record['argv'][7:]==execution['carrier']['codex']['argv'],
 'recorder_fixed':hashlib.sha256((r/'installed/docs/experiments/agent-context/local/record_process.py').read_bytes()).hexdigest()==read(r/'judge-selection.json')['files']['record_process.py'],
 'codex_measured':hashlib.sha256(Path(execution['carrier']['codex']['path']).read_bytes()).hexdigest()==execution['carrier']['codex']['sha256'],
}
raw=lines(s/'raw.ndjson');rollout=lines(r/'native/rollout.jsonl');history=read(r/'native/history.json')
outcomes=[e for e in lines(s/'events.ndjson') if e.get('type')=='stage_message']
checks['typed_outcome_matches']=len(outcomes)==1 and outcomes[0]['session_id']==session and outcomes[0]['payload']['order_id']=='soodles-39' and outcomes[0]['payload']['stage_index']==0 and outcomes[0]['payload']['outcome']=='blocked'
# This is an external raw identity audit, not a replacement or weakening of the frozen judge.
(r/'native/exit-binding-audit.json').write_text(json.dumps({'checks':checks,'exit_record_path':str((r/'process-exits'/session/'exit.json').relative_to(r)),'authorizes_landing':False},indent=2)+'\n')
assert all(checks.values()),checks
packet=dict(raw_events=raw,history=history,rollout=rollout,expected=dict(carrier='local_macos_noodle_codex_exec',model='gpt-6-astra',marker='SOODLES39_NATIVE_CAPTURE_V2',exit_code=exit_record['returncode']))
(r/'native/capability-packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
p=subprocess.run(['python3','-B',str(r/'judge/capability.py')],input=json.dumps(packet),text=True,capture_output=True)
(r/'native/capability-verdict.json').write_text(p.stdout);(r/'native/capability-stderr.log').write_text(p.stderr)
commands=[e['item'] for e in raw if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
all_starts=[e['item']['id'] for e in raw if e.get('type')=='item.started'];all_ends=[e['item']['id'] for e in raw if e.get('type')=='item.completed']
audit=dict(judge_exit=p.returncode,event_counts=dict(collections.Counter(e.get('type') for e in raw)),all_started_items_have_one_result=all(all_ends.count(i)==1 for i in all_starts),commands=[dict(id=e['id'],command=e['command'],exit_code=e.get('exit_code')) for e in commands],native_item_errors=[e['item'] for e in raw if e.get('item',{}).get('type')=='error'],typed_outcomes=outcomes,child_returncode=exit_record['returncode'],noodle_attempt_exit_code=attempt['exit_code'],exit_binding_checks=checks,full_matched_cases='NOT_RUN',authorizes_landing=False)
(r/'native/raw-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(p.stdout);print(json.dumps({'raw_event_counts':audit['event_counts'],'exit_binding_checks':checks,'typed_outcomes':outcomes},ensure_ascii=False))
