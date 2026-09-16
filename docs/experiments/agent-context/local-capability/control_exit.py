from pathlib import Path
import shutil,subprocess,json
r=Path(__file__).resolve().parent;source=Path('/Users/neon/soodles/.worktrees/issue-39-agent-context-patterns/docs/experiments/agent-context/local');out=r/'exit-control';out.mkdir()
for p in source.glob('*.py'):shutil.copy2(p,out/p.name)
p=out/'capability.py';original=p.read_text();needle="    need(expected.get('exit_code') == 0, 'successful_process_exit')";assert needle in original
results=[]
for label,content in [('planted-defect',original.replace(needle,'    # planted omission: absent child exit accepted')),('restored',original)]:
 p.write_text(content)
 run=subprocess.run(['python3','-B','-m','unittest','test_capability.CapabilityControls.test_unknown_or_failed_process_exit_cannot_pass','test_capability.CapabilityControls.test_native_turn_and_paired_tool_pass','test_capability.CapabilityControls.test_declared_local_scope_preserves_cloud_and_behavior_gates','-v'],cwd=out,text=True,capture_output=True)
 (out/(label+'.stdout.log')).write_text(run.stdout);(out/(label+'.stderr.log')).write_text(run.stderr);results.append(dict(label=label,exit=run.returncode))
assert [x['exit'] for x in results]==[1,0],results
(out/'receipt.json').write_text(json.dumps(dict(records=results,scope='post-run test sensitivity; active live discriminator bytes unchanged',authorizes_landing=False),indent=2)+'\n');print(results)
