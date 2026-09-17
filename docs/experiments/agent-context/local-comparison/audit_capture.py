from pathlib import Path
import json,subprocess,collections,hashlib
import sys
r=Path(sys.argv[1]).resolve()
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
 'recorder_fixed':hashlib.sha256((r/'installed/docs/experiments/agent-context/local/record_process.py').read_bytes()).hexdigest()==read(r.parent/'judge-selection.json')['files']['record_process.py'],
 'codex_measured':hashlib.sha256(Path(execution['carrier']['codex']['path']).read_bytes()).hexdigest()==execution['carrier']['codex']['sha256'],
}
raw=lines(s/'raw.ndjson');rollout=lines(r/'native/rollout.jsonl');history=read(r/'native/history.json')
captured=r/'process-exits'/session/'stdout.log'
checks['captured_stdout_digest']=hashlib.sha256(captured.read_bytes()).hexdigest()==exit_record['stdout_sha256']
checks['captured_stdout_bytes']=len(captured.read_bytes())==exit_record['stdout_bytes']
checks['native_bytes_forwarded_without_event_changes']=lines(captured)==[{k:v for k,v in e.items() if k!='_ts'} for e in raw]
checks['terminal_delivery_deferred']=exit_record['terminal_tail_lines_deferred']>=1
outcomes=[e for e in lines(s/'events.ndjson') if e.get('type')=='stage_message']
checks['typed_outcome_matches']=len(outcomes)==1 and outcomes[0]['session_id']==session and outcomes[0]['payload']['order_id']=='soodles-39' and outcomes[0]['payload']['stage_index']==0 and outcomes[0]['payload']['outcome']=='blocked'

# Audit native capture independently of the normalized case representation.
starts=[e['item']['id'] for e in raw if e.get('type')=='item.started']
ends=[e['item']['id'] for e in raw if e.get('type')=='item.completed']
checks['every_started_item_has_result']=len(starts)==len(set(starts)) and all(ends.count(i)==1 for i in starts)
thread=history['result']['thread'];turns=thread['turns']
checks['one_completed_history_turn']=len(turns)==1 and turns[0]['status']=='completed'
native_starts=[e for e in raw if e.get('type')=='thread.started']
checks['thread_join']=len(native_starts)==1 and native_starts[0]['thread_id']==thread['id']
checks['complete_native_turn']=sum(e.get('type')=='turn.started' for e in raw)==1 and sum(e.get('type')=='turn.completed' for e in raw)==1 and not any(e.get('type') in ['turn.failed','error'] for e in raw)
contexts=[dict(line=i+1,**e['payload']) for i,e in enumerate(rollout) if e.get('type')=='turn_context']
checks['native_turn_model']=bool(contexts) and all(e.get('turn_id')==turns[0]['id'] and e.get('model')=='gpt-6-astra' and e.get('effort')=='high' for e in contexts)
checks['native_session_meta']=any(e.get('type')=='session_meta' and e['payload'].get('id')==thread['id'] for e in rollout)
calls=[];outputs=[]
for i,e in enumerate(rollout,1):
 v=e.get('payload',{});t=v.get('type','')
 if e.get('type')=='response_item' and t in ['custom_tool_call','function_call']: calls.append(dict(line=i,call_id=v['call_id'],name=v.get('name'),input=v.get('input',v.get('arguments'))))
 if e.get('type')=='response_item' and t in ['custom_tool_call_output','function_call_output']:outputs.append(dict(line=i,call_id=v['call_id']))
checks['native_tool_call_result_pairs']=len(calls)==len(outputs) and len({v['call_id'] for v in calls})==len(calls) and sorted(v['call_id'] for v in calls)==sorted(v['call_id'] for v in outputs)
checks['child_exit_zero']=exit_record['returncode']==0
after=r/'inputs-after';after.mkdir(exist_ok=True)
import shutil
for f in (r/'inbox').iterdir():
 if f.is_file():shutil.copy2(f,after/f.name)
checks['checkpoint_bytes_preserved']=(r/'inputs-before/checkpoint.json').read_bytes()==(after/'checkpoint.json').read_bytes()
checks['provider_bytes_preserved']=(r/'inputs-before/provider.json').read_bytes()==(after/'provider.json').read_bytes()
commands=[dict(line=i+1,**e['item']) for i,e in enumerate(raw) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
audit=dict(checks=checks,thread_id=thread['id'],turn_id=turns[0]['id'],noodle_session=session,native_contexts=contexts,native_calls=calls,native_results=outputs,native_command_count=len(commands),native_item_errors=[e['item'] for e in raw if e.get('item',{}).get('type')=='error'],typed_outcomes=outcomes,child_returncode=exit_record['returncode'],noodle_attempt_exit_code=attempt['exit_code'],capture_scope='All emitted bounded-task CLI JSONL plus same-thread native rollout custom tool requests and exposed outputs. Hidden service internals unknown; tool truncation retained as emitted.',authorizes_landing=False)
(r/'native/capture-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
(r/'native/commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'run':r.name,'checks':checks,'thread':thread['id'],'native_calls':len(calls),'commands':len(commands)}))
assert all(checks.values()),checks
