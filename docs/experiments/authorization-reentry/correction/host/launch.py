#!/usr/bin/env python3
"""One invocation, one existing Noodle capture. No retries or score-driven selection."""
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
TEMPLATE=Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/host/smoke-preparation/case-r04.json')
CARRIER=Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/host/carrier/run_case.py')
DRIVER=Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/fixture-public/drive.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def absent(pid):
 try:os.kill(pid,0)
 except ProcessLookupError:return True
 return False

def main():
 label,arm,case_id=sys.argv[1:]
 if arm not in ('baseline','r01','r02') or not label.replace('-','').isalnum():raise ValueError('invalid selected run')
 freeze=json.loads((BASE/'freeze.json').read_text())
 for p,digest in freeze['pins'].items():
  if sha(p)!=digest:raise RuntimeError('frozen input changed: '+p)
 packet=BASE/'host/runs'/label;packet.mkdir()
 public=packet/'public';public.mkdir();shutil.copytree(BASE/'snapshots'/arm,public/'subject')
 shutil.copy2(DRIVER,public/'drive.py')
 save(public/'input.json',{'source_dir':'subject','work_id':case_id});save(public/'context.json',{})
 spec=json.loads(TEMPLATE.read_text())
 for key in ('pins','source_head','public_files'):spec.pop(key,None)
 parent=Path(tempfile.mkdtemp(prefix='soodles-activation-',dir='/private/tmp'))
 runtime=Path(tempfile.mkdtemp(prefix='soodles-activation-runtime-',dir='/private/tmp'));runtime.chmod(0o700)
 shutil.copyfile('/Users/neon/.codex/auth.json',runtime/'auth.json');(runtime/'auth.json').chmod(0o600)
 (runtime/'public-probe.txt').write_text('public runtime probe\n')
 spec.update(run_root=str(parent/'run'),public_dir=str(public),task_file=str(BASE/'host/task.md'),workspace_factory=str(BASE/'private/workspace.py'),codex_home=str(runtime),probe_public_path=str(runtime/'public-probe.txt'),probe_denied_paths=[str(BASE/'evaluator/check.py'),str(BASE/'private/cases.json'),str(BASE/'evaluator/controls.json')],path=str(Path(spec['python']).parent)+':/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin',timeout_seconds=360)
 save(packet/'draft.json',spec)
 argv=[spec['python'],'-B',str(CARRIER),'--prepare',str(packet/'draft.json'),str(packet/'case.json')]
 prepared=subprocess.run(argv,capture_output=True,text=True)
 save(packet/'prepare.json',{'argv':argv,'exit':prepared.returncode,'stdout':prepared.stdout,'stderr':prepared.stderr})
 if prepared.returncode:shutil.rmtree(runtime);return prepared.returncode
 launched=[spec['python'],'-B',str(CARRIER),str(packet/'case.json'),sha(packet/'case.json')]
 try:
  result=subprocess.run(launched,capture_output=True,text=True)
  save(packet/'launch-result.json',{'argv':launched,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
  return result.returncode
 finally:
  run=Path(spec['run_root']);pids=[json.loads(p.read_text()).get('pid') for p in (run/'control/.noodle/sessions').glob('*/process.json')]
  if (run/'raw/exit.json').is_file():pids.append(json.loads((run/'raw/exit.json').read_text()).get('pid'))
  safe=all(type(p) is int and p>0 and absent(p) and absent(-p) for p in pids)
  if safe:shutil.rmtree(runtime)
  save(packet/'runtime-cleanup.json',{'temporary_runtime_removed':safe,'credential_bytes_archived':False})
  print(json.dumps({'packet':str(packet),'run_root':str(run),'runtime_removed':safe}),flush=True)
if __name__=='__main__':raise SystemExit(main())
