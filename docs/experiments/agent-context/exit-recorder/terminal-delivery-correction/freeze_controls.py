from pathlib import Path
import shutil,subprocess,json,hashlib
r=Path(__file__).parent;source=Path('/Users/neon/soodles/.worktrees/issue-39-agent-context-patterns/docs/experiments/agent-context/local');judge=r/'judge';subject=r/'control-subject';judge.mkdir();subject.mkdir()
for p in source.glob('*.py'):
 shutil.copy2(p,judge/p.name);shutil.copy2(p,subject/p.name)
old=Path('/Users/neon/.codex/experiments/soodles39-local-capability-20260917/controls-v2/judge/capability.py')
assert (judge/'capability.py').read_bytes()==old.read_bytes()
(r/'judge-selection.json').write_text(json.dumps({'source_head':'7323aea7f5a7dc1da34c64fdb61f3145c8e2f3ff','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in judge.glob('*.py')},'capability_judge_unchanged':True,'authorizes_landing':False},indent=2)+'\n')
original=(subject/'record_process.py').read_text();records=[]
def run(name,method=None):
 args=['python3','-B','-m','unittest',method,'-v'] if method else ['python3','-B','-m','unittest','discover','-p','test_*.py','-v']
 p=subprocess.run(args,cwd=subject,text=True,capture_output=True,timeout=20)
 (r/(name+'.stdout.log')).write_text(p.stdout);(r/(name+'.stderr.log')).write_text(p.stderr);records.append({'name':name,'exit':p.returncode});return p.returncode
assert run('restored-all-controls')==0
mutations=[('missing-exit',"persist(directory, 'exit.json', dict(identity, returncode=returncode,","persist(directory, 'unobserved-exit.json', dict(identity, returncode=returncode,",'test_record_process.ProcessControls.test_success_and_nonzero_are_actual_child_exits'),('false-zero','returncode = child.wait()','returncode = child.wait(); returncode = 0','test_record_process.ProcessControls.test_success_and_nonzero_are_actual_child_exits'),('lost-signal','termination_signal=-returncode if returncode < 0 else None','termination_signal=None','test_record_process.ProcessControls.test_signal_exit_is_not_normalized_to_success'),('overwrite','exist_ok=False','exist_ok=True','test_record_process.ProcessControls.test_existing_record_is_preserved_without_launch')]
for name,before,after,method in mutations:
 assert before in original
 (subject/'record_process.py').write_text(original.replace(before,after))
 assert run('defect-'+name,method)!=0
 (subject/'record_process.py').write_text(original)
 assert run('cure-'+name,method)==0
prior=Path('/Users/neon/.codex/experiments/soodles39-exit-recorder-20260917/judge/record_process.py').read_text()
(subject/'record_process.py').write_text(prior)
assert run('prior-recorder-group-kill','test_record_process.ProcessControls.test_terminal_delivery_survives_owner_group_kill')!=0
(subject/'record_process.py').write_text(original)
assert run('corrected-recorder-group-kill','test_record_process.ProcessControls.test_terminal_delivery_survives_owner_group_kill')==0
assert run('legal-noncases-and-restored')==0
(r/'controls.json').write_text(json.dumps({'records':records,'scope':'real subprocess detector controls; no model calls','authorizes_landing':False},indent=2)+'\n');print(json.dumps(records))
