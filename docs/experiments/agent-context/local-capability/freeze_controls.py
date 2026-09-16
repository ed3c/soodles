from pathlib import Path
import hashlib,json,shutil,subprocess,sys,os
r=Path(__file__).parent;source=Path('/Users/neon/soodles/.worktrees/issue-39-agent-context-patterns/docs/experiments/agent-context/local');judge=r/'judge';judge.mkdir();subject=r/'control-subject';subject.mkdir()
for p in source.glob('*.py'):
 shutil.copy2(p,judge/p.name);shutil.copy2(p,subject/p.name)
selection={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in judge.iterdir()}
(r/'judge-selection.json').write_text(json.dumps({'files':selection,'authority':'externally selected experimental discriminator only; not landing authority'},indent=2)+'\n')
records=[]
def run(name):
 p=subprocess.run([sys.executable,'-B','-m','unittest','test_capability','test_cloud_observe','-v'],cwd=subject,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
 (r/(name+'.log')).write_text(p.stdout+p.stderr);records.append({'name':name,'exit':p.returncode});return p.returncode
assert run('controls-cure-and-noncases')==0
p=subject/'capability.py';original=p.read_text()
for name,needle in [('native-model','need(bool(bound), \'native_turn_model\')'),('thread-identity',"need(thread.get('id') == session and bool(session), 'history_thread_identity')"),('tool-result',"need(sorted(start_ids) == sorted(end_ids), 'tool_results_complete')"),('turn-model-match',"require(all(e.get('model') == expected.get('model') for e in bound), 'turn_model_matches')")]:
 assert original.count(needle)==1;p.write_text(original.replace(needle,'pass  # planted omission'))
 assert run('defect-'+name)!=0;p.write_text(original);assert run('cure-'+name)==0
(r/'controls.json').write_text(json.dumps({'scope':'synthetic detector controls; defects in discriminator, not document baseline','records':records,'authorizes_landing':False},indent=2)+'\n');print(json.dumps(records))
