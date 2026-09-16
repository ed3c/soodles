from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tarfile,io,time
root=Path('/Users/neon/soodles/.worktrees/soodles-18-0-execute');archive=Path('/Users/neon/.codex/experiments/soodles18-continuation-20260917/controls');archive.mkdir()
judge=archive/'judge';judge.mkdir()
for name in ['test_issue_admission.py','test_issue_execution.py','test_landing.py']:
 shutil.copy2(root/'tests'/name,judge/name)
selection={'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'judge_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in judge.iterdir()},'scope':'local real consumer functions and executable sentinels over provider/owner fixtures','authorizes_landing':False}
(archive/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
source=archive/'subject';source.mkdir()
blob=subprocess.check_output(['git','archive','HEAD'],cwd=root)
with tarfile.open(fileobj=io.BytesIO(blob)) as tar:tar.extractall(source,filter='data')
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(judge)+os.pathsep+str(source),'TMPDIR':'/private/tmp'}
records=[]
def run(name,tests):
 start=time.monotonic();p=subprocess.run([sys.executable,'-B','-m','unittest',*tests,'-v'],cwd=archive,env=env,text=True,capture_output=True,timeout=50)
 (archive/(name+'.log')).write_text(p.stdout+p.stderr)
 record={'name':name,'control':tests,'exit':p.returncode,'elapsed_seconds':time.monotonic()-start};records.append(record);return record
assert run('cure-and-non-cases',['test_issue_admission','test_issue_execution','test_landing'])['exit']==0
mutations=[
 ('body-binding','issue_admission.py','require(body_digest(body) == envelope["body_sha256"]','require(True', ['test_issue_admission.IssueAdmissionTests.test_whole_body_and_revision_changes_require_fresh_envelope']),
 ('worker-entry','issue_execution.py','    binding = context(envelope_path, envelope_digest, root, reader)\n    execution = binding["execution"]\n    session = environ.get("NOODLE_SESSION_ID")','    binding = load_external_envelope(envelope_path, envelope_digest, root)\n    execution = binding["execution"]\n    session = environ.get("NOODLE_SESSION_ID")',['test_issue_execution.IssueExecutionTests.test_worker_revalidates_live_body_before_executable_effect']),
 ('takeover-process','issue_execution.py','            quiescent_order(binding, state)','            pass  # planted removal of process readback',['test_issue_execution.IssueExecutionTests.test_completed_label_cannot_hide_a_live_process_group']),
 ('delivery-consumer','landing.py','    execution_binding(claim, issue, operation=operation, checkpoint=checkpoint)\n','    pass  # planted removal of delivery binding\n',['test_landing.BoundLandingTests.test_body_amendment_refuses_prepared_dispatch_without_offer']),
 ('delivery-paths','issue_admission.py','require(not outside, "candidate.outside_write_paths", outside)','require(True, "candidate.outside_write_paths", outside)',['test_landing.BoundLandingTests.test_outside_delivery_paths_refuse_and_current_paths_pass']),
]
mutations.extend([
 ('worker-head','issue_execution.py','require(head == execution["source_head"], "worker.git.head", head,','require(True, "worker.git.head", head,',['test_issue_execution.IssueExecutionTests.test_clean_descendant_is_not_the_selected_starting_head']),
 ('order-history','issue_execution.py','if effect.get("type") == "initial_admission" and effect.get("payload", {}).get("order_id") == order_id:','if False:',['test_issue_execution.IssueExecutionTests.test_repeated_publication_preserves_one_mailbox_and_prior_admission']),
])
mutations.extend([
 ('continuation-operation','issue_execution.py','return {**next_action, "operation": operation,','return {**next_action, "operation": "automatic",',['test_issue_execution.IssueExecutionTests.test_stale_body_continuation_preserves_entry_and_requires_supervisor_rebinding']),
 ('continuation-owner','issue_admission.py','amendment = {"owner": "supervisor", "required": "fresh_execution_envelope"}','amendment = source',['test_issue_execution.IssueExecutionTests.test_stale_body_continuation_preserves_entry_and_requires_supervisor_rebinding']),
])
terminal=(source/'landing.py').read_text()
start=terminal.index('        if envelope is not None:\n')
end=terminal.index('        if worktree.exists() or branch:',start)
mutations.append(('terminal-order','landing.py',terminal[start:end],'',['test_landing.BoundLandingTests.test_provider_closure_cannot_resolve_before_original_noodle_order']))
for name,file,needle,replacement,tests in mutations:
 p=source/file;original=p.read_text();assert original.count(needle)==1,(name,original.count(needle));p.write_text(original.replace(needle,replacement));record=run('defect-'+name,tests);p.write_text(original);record['defect_detected']=record['exit']!=0;assert record['defect_detected'],name
 assert run('cure-'+name,tests)['exit']==0
(archive/'receipt.json').write_text(json.dumps({'selection':selection,'records':records,'classification':'VERIFIED_LOCAL_CONTROLS','authorizes_landing':False},indent=2)+'\n')
print(json.dumps({'controls':len(records),'defects_detected':len(mutations),'scope':selection['scope']}))
