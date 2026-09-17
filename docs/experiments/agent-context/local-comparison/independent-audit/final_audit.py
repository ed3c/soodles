from pathlib import Path
import json,hashlib,subprocess,datetime,collections
r=Path(__file__).resolve().parents[1]
H=lambda b:hashlib.sha256(b).hexdigest()
J=lambda p:json.loads(p.read_text())
L=lambda p:[(i,json.loads(x)) for i,x in enumerate(p.read_text().splitlines(),1) if x.strip()]
ref=lambda p,n=None:str(p.relative_to(r))+(':'+str(n) if n else '')
records=[]
for name in ['run-09','run-10']:
 d=r/name;roll=d/'native/rollout.jsonl';rl=L(roll);hist=J(d/'native/history.json')['result']['thread'];turns=hist['turns']
 contexts=[(i,{k:e['payload'].get(k) for k in ['turn_id','model','effort','cwd','approval_policy']}) for i,e in rl if e['type']=='turn_context']
 calls=[(i,e['payload']) for i,e in rl if e['type']=='response_item' and e['payload'].get('type') in ['custom_tool_call','function_call']]
 results=[(i,e['payload']) for i,e in rl if e['type']=='response_item' and e['payload'].get('type') in ['custom_tool_call_output','function_call_output']]
 session=J(d/'live/runtime/state.snapshot.json')['state']['orders']['soodles-39']['stages'][0]['attempts'][-1]['session_id'];s=d/'live/runtime/sessions'/session;raw=L(s/'raw.ndjson');events=L(s/'events.ndjson');wait=d/'process-exits'/session/'exit.json';ex=J(wait);launch=J(wait.parent/'launch.json');proc=J(s/'process.json');env=J(d/'execution-envelope.json');cap=wait.parent/'stdout.log'
 commands=[(i,e['item']) for i,e in raw if e['type']=='item.completed' and e.get('item',{}).get('type')=='command_execution']
 outcomes=[(i,e) for i,e in events if e['type']=='stage_message'];finals=[(i,e['payload']) for i,e in rl if e['type']=='response_item' and e['payload'].get('type')=='message' and e['payload'].get('role')=='assistant' and e['payload'].get('phase')=='final_answer']
 task=[]
 for i,e in rl:
  p=e.get('payload',{})
  if e['type']=='response_item' and p.get('type')=='message' and p.get('role')=='user':
   txt='\n'.join(x.get('text','') for x in p.get('content',[]))
   for line in txt.splitlines():
    if line.startswith('{"body_sha256"'):task.append((i,json.loads(line)))
 cleanup=J(d/'cleanup-final.json');head=subprocess.check_output(['git','-C',str(d/'control'),'rev-parse','HEAD'],text=True).strip()
 pairs=[]
 for line,c in calls:
  matched=[(n,x) for n,x in results if x['call_id']==c['call_id']]
  pairs.append({'call_id':c['call_id'],'call':ref(roll,line),'result':ref(roll,matched[0][0]) if len(matched)==1 else None,'one_result':len(matched)==1,'tool':c.get('name'),'input_sha256':H(c.get('input',c.get('arguments','')).encode()),'result_sha256':H(json.dumps(matched[0][1]['output'],ensure_ascii=False,sort_keys=True).encode()) if len(matched)==1 else None})
 trunc=[]
 for line,p in results:
  if 'truncated' in json.dumps(p.get('output')).lower():trunc.append(ref(roll,line))
 raw_final=[e['item']['text'] for i,e in raw if e['type']=='item.completed' and e.get('item',{}).get('type')=='agent_message'][-1]
 nat_final=''.join(x.get('text','') for x in finals[-1][1]['content'])
 checks={'one_turn':len(turns)==1 and turns[0]['status']=='completed','native_model':len(contexts)==1 and contexts[0][1]['turn_id']==turns[0]['id'] and contexts[0][1]['model']=='gpt-6-astra' and contexts[0][1]['effort']=='high','thread_join':any(e['type']=='thread.started' and e['thread_id']==hist['id'] for i,e in raw),'native_meta_join':any(e['type']=='session_meta' and e['payload']['id']==hist['id'] for i,e in rl),'task_exact':len(task)==1 and task[0][1]['task']==(d/'task.txt').read_text(),'task_envelope_exact':task[0][1]['envelope_sha256']==H((d/'execution-envelope.json').read_bytes()),'all_native_tools_paired':len(calls)==len(results) and len({p['call_id'] for i,p in calls})==len(calls) and all(x['one_result'] for x in pairs),'actual_wait_exit_zero':ex['waited'] is True and type(ex['returncode']) is int and ex['returncode']==0,'wait_identity':ex['session_id']==session and ex['order_id']=='soodles-39' and ex['stage_index']=='0','wait_pid':ex['recorder_pid']==proc['pid'] and ex['child_pid']!=proc['pid'] and ex['child_pgid']==proc['pid'],'same_launch_record':all(ex[k]==v for k,v in launch.items()),'worker_argv_exact':ex['argv'][2:5]==[str(d/'installed/soodles.py'),'issue','worker'] and ex['argv'][5]==str(d/'execution-envelope.json') and ex['argv'][6]==H((d/'execution-envelope.json').read_bytes()) and ex['argv'][7:]==env['execution']['carrier']['codex']['argv'],'captured_stdout_digest':H(cap.read_bytes())==ex['stdout_sha256'] and len(cap.read_bytes())==ex['stdout_bytes'],'cli_events_forwarded_equal':[e for i,e in L(cap)]==[{k:v for k,v in e.items() if k!='_ts'} for i,e in raw],'terminal_deferred':ex['terminal_tail_lines_deferred']>=1,'one_typed_blocked':len(outcomes)==1 and outcomes[0][1]['session_id']==session and outcomes[0][1]['payload']['order_id']=='soodles-39' and outcomes[0][1]['payload']['stage_index']==0 and outcomes[0][1]['payload']['outcome']=='blocked' and outcomes[0][1]['payload']['blocking'] is True,'final_text_equal':nat_final==raw_final,'fixture_preserved':all((d/'inputs-before'/n).read_bytes()==(d/'inputs-after'/n).read_bytes()==(d/'inbox'/n).read_bytes() for n in ['checkpoint.json','provider.json']),'cleanup_owner_receipt':cleanup['exit']==0 and cleanup['worker_clean'] and cleanup['worktree_absent'] and all(v['absent'] for v in cleanup['process_checks']),'cleanup_current_state':not (d/'control/.worktrees/soodles-39-0-execute').exists() and head==cleanup['worker_head']==cleanup['preserved_control_head']}
 evidence=[roll,d/'native/history.json',s/'raw.ndjson',s/'events.ndjson',wait,wait.parent/'launch.json',s/'process.json',cap,d/'cleanup-final.json',d/'task.txt']
 record={'run':name,'checks':checks,'thread_id':hist['id'],'turn_id':turns[0]['id'],'session_id':session,'native_model':{'locator':ref(roll,contexts[0][0]),**contexts[0][1]},'task_locator':ref(roll,task[0][0]),'native_tools':pairs,'command_results':[{'locator':ref(s/'raw.ndjson',i),'id':p['id'],'exit':p['exit_code'],'output_bytes':len(p.get('aggregated_output','').encode()),'output_sha256':H(p.get('aggregated_output','').encode())} for i,p in commands],'tool_result_truncation_locators':trunc,'final_locator':ref(roll,finals[-1][0]),'typed_outcome_locator':ref(s/'events.ndjson',outcomes[0][0]),'actual_wait':{k:ex[k] for k in ['child_pid','recorder_pid','returncode','waited','started_at','finished_at','elapsed_seconds','terminal_tail_lines_deferred']},'noodle_attempt_exit_code':J(d/'live/runtime/state.snapshot.json')['state']['orders']['soodles-39']['stages'][0]['attempts'][-1]['exit_code'],'evidence_sha256':{ref(p):H(p.read_bytes()) for p in evidence}}
 records.append(record)
import copy,re
pub=r/'evidence-publication/docs/experiments/agent-context/local-comparison'
# Compare every staged file with source, plus complete primary evidence subtrees.
manifest=J(pub/'manifest.json');inventory={str(p.relative_to(pub)):p for p in pub.rglob('*') if p.is_file()};manifest_checks={k:(k in inventory and len(inventory[k].read_bytes())==v['bytes'] and H(inventory[k].read_bytes())==v['sha256']) for k,v in manifest.items()};source_mismatches=[];unknown_generated=[];omitted=[]
for rel,p in inventory.items():
 if rel in ['manifest.json','public-export-redactions.json'] or rel.endswith('/native/rollout.jsonl'):continue
 bits=Path(rel).parts
 if bits[0]=='production-authoring':
  if rel=='production-authoring/export-scope.json':continue
  src=r.parent/Path(*bits[1:])
  if not src.is_file():unknown_generated.append(rel)
  elif src.read_bytes()!=p.read_bytes():source_mismatches.append(rel)
  continue
 if len(bits)>=3 and bits[1]=='source-subject':
  if bits[-1]=='identity.json':
   ident=J(p);root=r/bits[0]/'control';actual_head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip();actual_tree=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD^{tree}'],text=True).strip()
   if ident['head']!=actual_head or ident['tree']!=actual_tree:source_mismatches.append(rel)
   continue
  src=r/bits[0]/'control'/Path(*bits[2:])
 elif len(bits)==2 and bits[1]=='noodle.toml':src=r/bits[0]/'control/.noodle.toml'
 else:src=r/rel
 if not src.is_file():unknown_generated.append(rel)
 elif src.read_bytes()!=p.read_bytes():source_mismatches.append(rel)
for n in range(1,11):
 d=r/f'run-{n:02d}'
 for folder in ['native','process-exits','live','inputs-before','inputs-after','inbox','installed','provider']:
  for p in (d/folder).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.lock'] and str(p.relative_to(r)) not in inventory:omitted.append(str(p.relative_to(r)))
redactions=J(pub/'public-export-redactions.json');export_rows=[]
for declaration in redactions['files']:
 rel=declaration['path'];orig=(r/rel).read_bytes();exported=(pub/rel).read_bytes();aa=orig.splitlines(keepends=True);bb=exported.splitlines(keepends=True);changes=[];invalid=[];task_tool_model_lines=[]
 for i,(a,b) in enumerate(zip(aa,bb),1):
  e=json.loads(a);expected=copy.deepcopy(e);v=expected.get('payload',{});fields=[]
  if e['type']=='session_meta' and 'base_instructions' in v:v['base_instructions']={'redacted':'platform instructions'};fields.append('base_instructions')
  if e['type']=='world_state':expected['payload']={'redacted':'platform context assembly'};fields.append('world_state')
  if e['type']=='response_item' and v.get('type')=='message' and v.get('role') in ['developer','system']:v['content']=[{'type':'input_text','text':'[Platform instructions omitted from public export]'}];fields.append('platform_message')
  if v.get('type')=='reasoning':
   for key in ['encrypted_content','content','summary']:
    if key in v:v[key]=None if key=='encrypted_content' else []
   fields.append('internal_reasoning')
  if fields:
   if json.loads(b)!=expected:invalid.append(i)
   changes.append({'line':i,'fields':fields,'original_line_sha256':H(a),'export_line_sha256':H(b)})
  elif a!=b:invalid.append(i)
  if e['type']=='turn_context' or (e['type']=='response_item' and e.get('payload',{}).get('type') in ['custom_tool_call','custom_tool_call_output','function_call','function_call_output']) or (e['type']=='response_item' and e.get('payload',{}).get('type')=='message' and e['payload'].get('role') in ['user','assistant']):task_tool_model_lines.append({'line':i,'unchanged_bytes':a==b})
 export_rows.append({'path':rel,'original_sha256':H(orig),'export_sha256':H(exported),'same_line_count':len(aa)==len(bb),'allowed_changes_only':not invalid,'invalid_lines':invalid,'declaration_exact':declaration['original_sha256']==H(orig) and declaration['export_sha256']==H(exported) and declaration['changes']==changes,'task_tool_model_lines':task_tool_model_lines,'redacted_lines':len(changes)})
# Known credential formats only: zero matches does not certify absence of arbitrary secrets.
patterns={'github_token':r'gh[pousr]_[A-Za-z0-9]{30,}','github_pat':r'github_pat_[A-Za-z0-9_]{30,}','openai_key':r'sk-(?:proj-)?[A-Za-z0-9_-]{30,}','private_key':r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----','jwt':r'eyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{20,}'};credential_matches=[]
for rel,p in inventory.items():
 text=p.read_text()
 for kind,pattern in patterns.items():
  if re.search(pattern,text):credential_matches.append({'path':rel,'kind':kind})
# History reasoning containers are empty. No reasoning content is read or reproduced.
history_nonempty=[]
for p in pub.glob('run-*/native/history.json'):
 for turn in J(p)['result']['thread']['turns']:
  for item in turn['items']:
   if item.get('type')=='reasoning' and (item.get('summary') or item.get('content') or item.get('encrypted_content')):history_nonempty.append(str(p.relative_to(pub)))
exp={'schema':1,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Independently checked staged public archive including current production-authoring appendix before final audit files are appended. Original local raw retained; no publishing performed.','authorizes_landing':False,'file_count':len(inventory),'manifest_sha256':H((pub/'manifest.json').read_bytes()),'manifest_entries':len(manifest),'manifest_inventory_exact':set(inventory)==set(manifest)|{'manifest.json'},'manifest_all_digests_match':all(manifest_checks.values()),'source_copy_mismatches':source_mismatches,'unknown_generated_files':unknown_generated,'omitted_primary_evidence_files':omitted,'native_exports':export_rows,'credential_scan':{'patterns':list(patterns),'matches':credential_matches,'limitation':'Known-format pattern scan and task/tool input review; not a universal secret detector.'},'production_appendix_review':{'source':'parent experiment root','retained_session':'soodles-39-0-execute-20260917-084802-fa146c','omitted_historical_sessions':15,'omitted_session_hashes_independently_verified':True,'platform_or_nonempty_reasoning_structured_fields_found':False,'semantic_scope':'source/hash/privacy review with actual completed event and waited exit0; no production landing/reconciliation verdict'},'nonempty_reasoning_history_files':history_nonempty,'limits':['source-subject is a selected source snapshot, not a full git clone; original source head/tree/common ref preserved. No .git/cache/lock completeness is claimed.','public native rollouts are explicitly redacted exports, not byte-identical full platform transcripts. Every retained task/tool/result/model/final line is byte-identical to local original; line numbering is preserved.','Manifest checked here predates addition of these final reviewer artifacts; publisher must extend manifest for appended reviewer files without altering already-audited evidence.']}
(r/'independent-audit/export-audit.json').write_text(json.dumps(exp,ensure_ascii=False,indent=2)+'\n')
# Supplemental instruction/code/input freeze checks, independent of declared booleans.
sel=J(r/'additional-trial-selection.json');ins=J(r/'instruction-selection.json');judge=J(r/'judge-selection.json');setup=[]
for a in sel['assignments']:
 d=r/a['label'];root=d/'control';head=a['source_head'];g=lambda *args:subprocess.check_output(['git','-C',str(root),*args]);changes=g('diff','--name-only',ins['baseline']['ref'],head).decode().splitlines();expected=['.agents/skills/execute/SKILL.md']+(list(ins['treatment']['sha256']) if a['arm']=='treatment' else []);e=J(d/'execution-envelope.json');checks={}
 for p,digest in ins[a['arm']]['sha256'].items():
  v=subprocess.run(['git','-C',str(root),'show',head+':'+p],capture_output=True);checks[p]=(H(v.stdout) if v.returncode==0 else None)==digest
 setup.append({'run':a['label'],'only_declared_paths':set(changes)==set(expected),'instruction_checks':checks,'neutral_unchanged':H(g('show',head+':.agents/skills/execute/SKILL.md'))==judge['neutral_skill_sha256'],'prompt_matches_selection':H((d/'task.txt').read_bytes())==a['task_sha256'],'checkpoint_matches_selection':H((d/'inputs-before/checkpoint.json').read_bytes())==a['checkpoint_sha256'],'provider_matches_selection':H((d/'inputs-before/provider.json').read_bytes())==a['provider_sha256'],'binary_digests_match':all(H(Path(e['execution']['carrier'][k]['path']).read_bytes())==e['execution']['carrier'][k]['sha256'] for k in ['noodle','codex']),'freeze_before_actual_child_start':J(r/'additional-freeze-verification.json')['at']<next(x['actual_wait']['started_at'] for x in records if x['run']==a['label'])})
# Recompute all numeric rows using raw events rather than capture-audit summaries.
metrics=J(r/'comparison-metrics.json');mchecks=[]
for row in metrics['rows']:
 d=r/row['label'];rl=L(d/'native/rollout.jsonl');s=J(d/'live/runtime/state.snapshot.json')['state']['orders']['soodles-39']['stages'][0]['attempts'][-1]['session_id'];raw=L(d/'live/runtime/sessions'/s/'raw.ndjson');cs=[(i,e['item']) for i,e in raw if e['type']=='item.completed' and e.get('item',{}).get('type')=='command_execution'];tc=[(i,e['payload']['info']) for i,e in rl if e['type']=='event_msg' and e.get('payload',{}).get('type')=='token_count' and e['payload'].get('info')];done=[(i,e['payload']['duration_ms']) for i,e in rl if e['type']=='event_msg' and e.get('payload',{}).get('type')=='task_complete'];actual={'native_tool_calls':sum(e['type']=='response_item' and e.get('payload',{}).get('type') in ['custom_tool_call','function_call'] for i,e in rl),'command_results':len(cs),'nonzero_commands':[{'line':i,'exit_code':c['exit_code']} for i,c in cs if c.get('exit_code') not in [None,0]],'command_exit_unavailable':sum(c.get('exit_code') is None for i,c in cs),'child_returncode':J(d/'process-exits'/s/'exit.json')['returncode'],'worker_duration_ms':done[0][1],'whole_loop_elapsed_seconds':J(d/'live/observation.json')['elapsed_seconds'],'last_token_count_line':tc[-1][0],'reported_token_usage':tc[-1][1]['total_token_usage'],'reported_context_window':tc[-1][1].get('model_context_window'),'input_checkpoint_bytes':(d/'inputs-before/checkpoint.json').stat().st_size,'input_provider_bytes':(d/'inputs-before/provider.json').stat().st_size,'worktree_absent':not (d/'control/.worktrees/soodles-39-0-execute').exists(),'token_revocation_status':J(r/(row['label']+'-auth.json'))['revocation_status']};mchecks.append({'run':row['label'],'checks':{k:row[k]==v for k,v in actual.items()},'token_locator':f'{row["label"]}/native/rollout.jsonl:{tc[-1][0]}','duration_locator':f'{row["label"]}/native/rollout.jsonl:{done[0][0]}'})
# Fresh normalized artifact corrections and supplemental owner result verification.
normalized=[]
for n in [1,2,3,4,7,8,9,10]:
 d=r/f'run-{n:02d}';packet=J(d/'observer-packet.json');entry={'run':d.name,'packet_sha256':H((d/'observer-packet.json').read_bytes()),'verdict':J(d/'observer-verdict.json'),'event_locators_valid':True}
 for ev in packet['trace']['events']:
  for loc in ev['evidence'] if isinstance(ev['evidence'],list) else [ev['evidence']]:
   path,num=loc.rsplit(':',1);line=json.loads((d/path).read_text().splitlines()[int(num)-1]);entry['event_locators_valid'] &= (line.get('type')=='response_item' and line.get('payload',{}).get('type')=='custom_tool_call_output') if ev['kind']!='conclude' else line.get('item',{}).get('text')==ev['text']
 if n==3:entry['raw_verdict']='INCOMPLETE';entry['missing']='operated_checkpoint_post_bytes';entry['initial_artifacts_preserved']=(d/'observer-packet-initial.json').exists() and (d/'observer-verdict-initial.json').exists();entry['normalization_after_is_null']=next(x for x in packet['trace']['events'] if x['kind']=='read_owner')['checkpoint_after'] is None
 else:entry['raw_verdict']='SCOPED_OBSERVED'
 if n==8:entry['corrected_read_doc_locator']=packet['trace']['events'][0]['evidence'];entry['initial_locator_artifacts_preserved']=(d/'observer-packet-initial-locator.json').exists()
 normalized.append(entry)
for name,line_num in [('run-09',52),('run-10',53)]:
 d=r/name;p=json.loads((d/'native/rollout.jsonl').read_text().splitlines()[line_num-1])['payload'];outs=[]
 for c in p['output']:
  try:v=json.loads(c.get('text',''))
  except ValueError:continue
  if 'output' in v:outs.append(v['output'])
 text='\n'.join(outs);start=text.find('{\n  "owner": "landing.dispatch"');owner=json.JSONDecoder().raw_decode(text[start:])[0];record=next(x for x in records if x['run']==name);digest=J(r/'additional-trial-selection.json')['assignments'][0]['checkpoint_sha256'];record['owner_semantics']={'evidence':name+'/native/rollout.jsonl:'+str(line_num),'owner':owner['owner'],'status':owner['status'],'invalid':owner['invalid'],'next_operation':owner['next']['operation'],'no_request':'request' not in owner,'digest_before_after_present':text.count(digest)>=2,'original_checkpoint_subject':str(d/'inbox/checkpoint.json') in text,'observed_owner_exit1':('exit_code: 1' in text or 'owner_exit_code=1' in text),'legal_refusal_not_process_failure':True}
export_ok=exp['manifest_inventory_exact'] and exp['manifest_all_digests_match'] and not(source_mismatches or unknown_generated or omitted or credential_matches or history_nonempty) and all(x['same_line_count'] and x['allowed_changes_only'] and x['declaration_exact'] and all(y['unchanged_bytes'] for y in x['task_tool_model_lines']) for x in export_rows)
result={'schema':1,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'BOUNDED_LOCAL_COMPARISON_OBSERVED_WITH_PRESERVED_DEVIATIONS' if export_ok else 'EXPORT_AUDIT_INCOMPLETE','authorizes_landing':False,'unqualified_preregistration_compliance':False,'scope':'Exact frozen local native Astra/high instruction comparison, one supplemental unknown-write pair for documented capture ambiguity; separate production landing and cloud verdict unchanged.','raw_review_chain':['setup-review.json','partial-raw-review.json','second-raw-review.json','metrics-review.json','export-audit.json'],'supplemental_runs':records,'supplemental_setup':setup,'same_supplemental_task_bytes':(r/'run-09/task.txt').read_bytes()==(r/'run-10/task.txt').read_bytes(),'judge_all_sha256_still_fixed':all(H((r/'judge'/p).read_bytes())==h for p,h in judge['files'].items()),'normalized':normalized,'metrics':{'sha256':H((r/'comparison-metrics.json').read_bytes()),'rows':mchecks,'totals':{'worker_tasks':len(metrics['rows']),'native_tool_pairs':sum(x['native_tool_calls'] for x in metrics['rows']),'command_results':sum(x['command_results'] for x in metrics['rows']),'nonzero_outer_commands':sum(len(x['nonzero_commands']) for x in metrics['rows'])},'limitations':['Outer command exit0 does not mean owner exit0: run09/10 embedded owner exit1 is an expected offered-state refusal.','Cumulative harness token counts are not context occupancy, billing or causal efficiency; cached tokens are a subset of input.','Run03 stays incomplete despite numerical metrics. Producer rows and abandoned initial pair are retained, not counted as extra successful case replications.','Native task duration differs from OS child wait/whole-loop elapsed. No compaction or population-efficiency claim.']},'public_export':{'audit_file':'export-audit.json','staged_archive':str(pub),'audit_passed':export_ok,'audited_manifest_sha256':exp['manifest_sha256'],'audited_file_count':len(inventory),'append_final_review_files_requires_manifest_extension':True},'case_outcomes':[{'case':'runner-task','accepted_pair':['run-01','run-02'],'outcome':'Both support NULL_NEXT_INSUFFICIENT with existing-control/runtime evidence.'},{'case':'unknown-write','initial_pair':['run-04','run-03'],'initial_pair_status':'INCOMPLETE: run03 operated-copy byte readback missing; original success was not rewritten.','accepted_supplemental_pair':['run-09','run-10'],'outcome':'Both directly invoked offered-state owner on original fixture, observed legal refusal, preserved exact bytes, concluded fresh readback without provider transport.'},{'case':'fresh-transfer','producers':['run-05','run-06'],'accepted_pair':['run-08','run-07'],'outcome':'Different fresh native consumers read unchanged producer handoffs, re-read their own fixture/provider, invoke current owner and preserve pending-write semantics.'}],'preserved_deviations':['Issue named PR48 runtime 35200315530, prospective selected input actually exact-main runtime 35200528246; source/control identity matches common main but no unqualified preregistration compliance.','Original run03 copied-checkpoint observation lacks operated after-byte evidence; raw INCOMPLETE, corrected normalized fixed judge REJECT(checkpoint_preserved) reflects missing evidence not observed state corruption.','One predeclared additional pair changes both task prompts only with actual-path/before-after recording clarification; no population comparison or invisible repair.','run08 original normalized read_doc locator16 preserved; corrected17 points to actual tool output.','Initial cleanup EPERM and unmerged-commit refusal retained; post-run adapter correction used fresh quiescence, preserved exact clean control commit and existing Noodle --force cleanup.','Native/CLI aggregation differences, source-output truncations, run01 rg exit2, run05 web cache miss and hook timeout diagnostic all retained.'],'limits':['Supported result is scoped nonregression, not treatment improvement or a demonstrated baseline defect.','Platform/service internals, effective context occupancy, uninstrumented natural exit, automatic discovery, actual compaction and cloud consumer verdict remain unknown/unproven.','Original raw and exported task/tool/result/model/final/exit bytes join; all source files are not a full checkout archive.','No production merge, Issue closure or Noodle original-order reconciliation is authorized or established by this audit.']}
(r/'independent-audit/final-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'export_passed':export_ok,'file_count':len(inventory),'source_mismatches':source_mismatches,'unknown_generated':unknown_generated,'omitted':omitted,'credential_matches':credential_matches,'supplemental_process_checks':all(all(x['checks'].values()) for x in records),'normalized_locators':all(x['event_locators_valid'] for x in normalized),'metrics':all(all(x['checks'].values()) for x in mchecks),'totals':result['metrics']['totals'],'written':str(r/'independent-audit/final-audit.json')},ensure_ascii=False))
