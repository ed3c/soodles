"""External fixed code predicates; driver uses disposable process/provider fixtures."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
SOURCE=Path(sys.argv[1]).resolve();OUTPUT=Path(sys.argv[2]).resolve();ROOT=Path(__file__).resolve().parent
CASES=['own_pending', 'own_running', 'foreign_order', 'foreign_config', 'foreign_loop', 'unknown_start', 'missing_pid', 'wrong_scheduler_model', 'malformed_scheduler_attempt', 'wrong_order_projection', 'unlocked_runtime', 'missing_scheduler_process', 'wrong_scheduler_session', 'multiple_scheduler_attempts', 'unknown_execute_status', 'missing_admitted_order', 'stopped_loop', 'foreign_spawn']
results=[]
with tempfile.TemporaryDirectory(prefix='owner-wait-oracle-') as temp:
 for name in CASES:
  target=Path(temp)/(name+'.json');argv=[sys.executable,'-B',str(ROOT/'driver.py'),str(SOURCE),name,str(target)]
  run=subprocess.run(argv,capture_output=True,text=True,timeout=30)
  raw=json.loads(target.read_text()) if target.exists() else {'result':{},'calls':[],'canonical_state_config_unchanged':False}
  result=raw['result'];pending=name in ('own_pending','own_running')
  passed=(result.get('status')==('pending' if pending else 'refused') and run.returncode==(0 if pending else 1) and not any('forbidden_effect' in c for c in raw['calls']) and raw['canonical_state_config_unchanged'] and result.get('authorizes_landing') is False)
  if pending:passed=passed and result.get('next',{}).get('kind')=='executable' and result.get('next',{}).get('argv',[None])[0]==str(SOURCE/'issue-atom') and result.get('wait_exhausted') is True and bool(result.get('waiting_on'))
  results.append({'case':name,'passed':passed,'expected':'bounded_pending' if pending else 'refused','raw':raw,'argv':argv,'exit':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
receipt={'schema':1,'classification':'PASS' if all(x['passed'] for x in results) else 'FAIL','source':str(SOURCE),'pins':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['oracle.py','fixture.py','driver.py']},'cases':results,'scope':'Existing drive/run entry with external frozen disposable fixtures; process reads are mocked, no live provider or Noodle claim.','authorizes_landing':False}
OUTPUT.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'classification':receipt['classification'],'passed':sum(x['passed'] for x in results),'total':len(results)}));sys.exit(0 if receipt['classification']=='PASS' else 1)
