"""Fixed external predicates; consumers receive the separate driver only."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
CASES=['registered','absent','missing_app.client_id','missing_app.installation_id','missing_app.private_key_path','missing_supplier.path','missing_supplier.sha256','digest','key_missing','failure','child_context','internal','legacy']
def expected_field(case):
 if case=='absent':return 'provider_credential_profile.path'
 if case.startswith('missing_'):return 'provider_credential_profile.'+case[8:]
 return {'digest':'provider_credential_profile.supplier.sha256','key_missing':'provider_credential_profile.app.private_key_path','failure':'provider_credential_supplier_exit','child_context':'provider_credential_profile.context','internal':'provider_credential_profile.path'}[case]
def observe(source,out):
 out=Path(out);out.mkdir(exist_ok=False);records=[]
 for case in CASES:
  target=out/case
  process=subprocess.run([sys.executable,'-B',str(P/'consumer-drive.py'),str(source),case,str(target)],capture_output=True,text=True,timeout=60,env={k:v for k,v in os.environ.items() if not k.startswith('NOODLE_')})
  (out/(case+'-runner.json')).write_text(json.dumps({'exit':process.returncode,'stdout':process.stdout,'stderr':process.stderr},indent=2)+'\n')
  if process.returncode:raise RuntimeError(case+' driver failed: '+process.stderr)
  r=json.loads(process.stdout);c=r['calls'];passed=c['provider_writes']==0 and r['disposable_removed'] and 'fixture-secret' not in (r['stdout']+r['stderr'])
  if case in ['registered','legacy']:passed=passed and r['boundary']=='admission' and r['exit']==0 and c['supplier']==1 and c['provider_reads']==2 and c['child_credentials_removed'] is True
  else:
   receipt=json.loads(r['stdout']);passed=passed and receipt['status']=='refused' and receipt['invalid']['field']==expected_field(case) and c['provider_reads']==0 and not r['checkpoint_created'] and c['supplier']==(1 if case=='failure' else 0)
  records.append({'case':case,'predicate':'PASS' if passed else 'FAIL'})
 result={'classification':'GREEN' if all(x['predicate']=='PASS' for x in records) else 'RED','records':records,'oracle_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'authorizes_landing':False};(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':observe(Path(sys.argv[1]),Path(sys.argv[2]))
