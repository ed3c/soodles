#!/usr/bin/env python3
import importlib.util,json,os,subprocess,sys,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'evaluator'));import check,capture_decoder as c
PYTHON=str(Path(sys.executable).resolve())
def main():
 reports=[]
 for arm,label in [('baseline','selection-a1'),('r01','selection-a1'),('r01','selection-b1'),('r01','selection-c1')]:
  case=Path(tempfile.mkdtemp(prefix='activation-control-',dir='/private/tmp'))
  source=case/'source'
  __import__('shutil').copytree(BASE/'snapshots'/arm,source)
  def cmd(argv,cwd=source):
   return subprocess.run(argv,cwd=cwd,capture_output=True,text=True,check=True)
  cmd(['git','init','-b','main']);cmd(['git','add','.']);cmd(['git','-c','user.name=Control','-c','user.email=control@example.invalid','commit','-m','Pin control source'])
  output=case/'workspace'
  setup=cmd([PYTHON,'-B',str(BASE/'private/workspace.py'),str(source),label,str(output),'unused'])
  facts=json.loads((output/'workspace.json').read_text())
  before={str(p):c.sha(p.read_bytes()) for p in output.rglob('*') if p.is_file() and '.git' not in p.parts}
  selected=facts['selection'];argv=[PYTHON,'-B',facts['entries']['supervisor_admission'],'authorize',selected['path'],selected['sha256'],selected['external_output']]
  env=dict(os.environ);env.update(facts['host']['environment'])
  result=subprocess.run(argv,cwd=facts['control_root'],env=env,capture_output=True,text=True)
  Path(facts['task']['raw_cli_receipt']).write_text(result.stdout)
  receipt=json.loads(result.stdout)
  Path(facts['task']['handoff']).write_text(json.dumps({'receipt':{'path':facts['task']['raw_cli_receipt']},'next':receipt.get('next')}))
  drives=[{'record':{'argv':argv,'stdout':result.stdout,'result':{'exit_code':result.returncode,'timed_out':False,'error':None}}}]
  stratum=json.loads((BASE/'private/cases.json').read_text())[label]['stratum']
  verdict=check.classify(facts,drives,before,stratum)
  expected='FAIL' if arm=='baseline' else 'PASS'
  if verdict['classification']!=expected:raise RuntimeError(json.dumps(verdict))
  # Planted handoff corruption must be discriminated in every legal scenario.
  Path(facts['task']['handoff']).write_text('{}')
  negative=check.classify(facts,drives,before,stratum)
  if negative['classification']!='FAIL':raise RuntimeError('undiscriminated wrong handoff')
  reports.append({'arm':arm,'case':label,'argv':argv,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'verdict':verdict,'planted_wrong_handoff':negative,'workspace':str(output)})
 (BASE/'evaluator/controls.json').write_text(json.dumps({'scope':'real CLI controls, not Agent behavior','cases':reports},indent=2)+'\n')
 print(json.dumps({'controls':len(reports),'pass':True}))
if __name__=='__main__':main()
