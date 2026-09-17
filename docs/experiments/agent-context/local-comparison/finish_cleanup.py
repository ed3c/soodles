from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
r=Path(__file__).parent;b='/Users/neon/.codex/experiments/noodle84-20260917/noodle-merged-ca81'
for label in sys.argv[1:]:
 d=r/label;root=d/'control';w=root/'.worktrees/soodles-39-0-execute';output=d/'cleanup-final.json';assert not output.exists()
 records=[d/'live/launch.json',d/'native/observation.json',*sorted((d/'live/runtime/sessions').glob('*/process.json')),*sorted((d/'process-exits').glob('*/exit.json'))];checks=[]
 for path in records:
  v=json.loads(path.read_text());pid=v.get('pid',v.get('child_pid'));pgid=v.get('child_pgid',pid)
  for kind,fn,n in [('pid',os.kill,pid),('pgid',os.killpg,pgid)]:
   try:fn(n,0)
   except ProcessLookupError:checks.append({'record':str(path.relative_to(d)),'kind':kind,'id':n,'absent':True})
   else:raise AssertionError((label,kind,n,'present'))
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=w,text=True).strip();root_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
 assert head==root_head and subprocess.check_output(['git','status','--porcelain'],cwd=w)==b''
 # The whole disposable subject remains in the independent control checkout;
 # force only removes its duplicate clean worker checkout through Noodle.
 q=subprocess.run([b,'--project-dir',str(root),'worktree','cleanup',w.name,'--force'],capture_output=True,text=True,timeout=30)
 receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'process_checks':checks,'worker_head':head,'preserved_control_head':root_head,'worker_clean':True,'owner_reason':'ordinary cleanup refuses detached-root experimental commit not merged to main; exact commit remains in source control checkout and frozen source evidence','argv':q.args,'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr,'worktree_absent':not w.exists(),'authorizes_landing':False}
 output.write_text(json.dumps(receipt,indent=2)+'\n');assert q.returncode==0 and not w.exists()
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==head
 print(json.dumps({'run':label,'worktree_absent':True,'preserved_head':head}))
