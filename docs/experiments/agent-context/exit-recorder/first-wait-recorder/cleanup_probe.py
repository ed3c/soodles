from pathlib import Path
import json,os,subprocess
r=Path(__file__).resolve().parent;root=r/'control';work=root/'.worktrees/soodles-39-0-execute'
records=[r/'live/launch.json',r/'native/observation.json',*sorted((r/'live/runtime/sessions').glob('*/process.json'))]
checks=[]
for path in records:
 d=json.loads(path.read_text());pid=d['pid']
 try:os.kill(pid,0);alive=True
 except ProcessLookupError:alive=False
 try:os.killpg(pid,0);group_alive=True
 except ProcessLookupError:group_alive=False
 checks.append(dict(record=str(path.relative_to(r)),pid=pid,alive=alive,group_alive=group_alive))
for path in sorted((r/'process-exits').glob('*/exit.json')):
 d=json.loads(path.read_text());pid=d['child_pid']
 try:os.kill(pid,0);alive=True
 except ProcessLookupError:alive=False
 try:os.killpg(d['child_pgid'],0);group_alive=True
 except ProcessLookupError:group_alive=False
 checks.append(dict(record=str(path.relative_to(r)),pid=pid,pgid=d['child_pgid'],alive=alive,group_alive=group_alive))
assert all(not p['alive'] and not p['group_alive'] for p in checks),checks
status=subprocess.run(['git','status','--porcelain=v1'],cwd=work,capture_output=True,text=True,check=True)
assert not status.stdout,status.stdout
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=work,text=True).strip()
result=subprocess.run(['/Users/neon/.codex/experiments/noodle82-20260916/noodle','worktree','cleanup','soodles-39-0-execute'],cwd=root,capture_output=True,text=True)
(r/'cleanup.stdout.log').write_text(result.stdout);(r/'cleanup.stderr.log').write_text(result.stderr)
receipt=dict(process_checks=checks,worker_head=head,worker_clean=True,cleanup_exit=result.returncode,worktree_absent=not work.exists(),production_issue_resolved=False,authorizes_landing=False)
(r/'cleanup.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
assert result.returncode==0 and not work.exists()
