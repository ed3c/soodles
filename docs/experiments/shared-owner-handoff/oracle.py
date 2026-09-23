"""External fixed shared-owner boundary predicates; no model judgment."""
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
CASES=['foreign_live','foreign_stopped','foreign_checkpoint','malformed_owner','entry_busy','idle','same_owner']
def main():
 source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(exist_ok=False);records=[]
 for case in CASES:
  r=subprocess.run([sys.executable,'-B',str(P/'consumer-drive.py'),str(source),case,str(out/case)],capture_output=True,text=True,timeout=60,start_new_session=True)
  raw={'argv':r.args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};(out/(case+'-runner.json')).write_text(json.dumps(raw,indent=2)+'\n')
  try:
   v=json.loads(r.stdout);owner=json.loads(v['stdout']) if v['stdout'].strip() else None
   invariant=v['config_unchanged'] and v['existing_owner_unchanged'] and v['disposable_removed']
   if case=='idle':ok=invariant and v['boundary']=='existing_start' and v['calls']['provider_writes']==1 and v['calls']['start']==1
   elif case=='same_owner':ok=invariant and v['exit']==0 and owner['status']=='pending' and owner['execution']['action']=='running' and v['calls']['provider_writes']==0
   else:
    nxt=owner['next'];ok=invariant and v['exit']==1 and owner['status']=='refused' and nxt['kind']=='input' and nxt['owner']==('soodles.issue-atom' if case=='entry_busy' else 'Noodle') and bool(nxt['required']) and nxt['argv'][-2]=='run' and owner['authorizes_landing'] is False and v['calls']=={'supplier':0,'provider_reads':0,'provider_writes':0,'start':0} and v['checkpoint_before']==v['checkpoint_after'] and not v['proposal_created']
   records.append({'case':case,'pass':bool(ok),'observation':v})
  except (ValueError,KeyError,TypeError) as error:records.append({'case':case,'pass':False,'error':str(error),'process':raw})
 r=subprocess.run([sys.executable,'-B',str(P/'race-drive.py'),str(source),str(out/'race')],capture_output=True,text=True,timeout=60,start_new_session=True)
 raw={'argv':r.args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};(out/'race-runner.json').write_text(json.dumps(raw,indent=2)+'\n')
 try:
  v=json.loads(r.stdout);b=v['outcomes']['B'];ok=r.returncode==0 and v['effects']==['A'] and v['second_returned_before_first_released'] and not v['B_checkpoint_created'] and v['disposable_removed'] and b['status']=='refused' and b['next']['kind']=='input' and b['next']['owner']=='soodles.issue-atom' and b['authorizes_landing'] is False
  records.append({'case':'race','pass':ok,'observation':v})
 except (ValueError,KeyError,TypeError) as e:records.append({'case':'race','pass':False,'error':str(e),'process':raw})
 result={'classification':'GREEN' if all(r['pass'] for r in records) else 'RED','records':records,'oracle_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'authorizes_landing':False};(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'classification':result['classification'],'cases':[{'case':r['case'],'pass':r['pass']} for r in records]},indent=2))
if __name__=='__main__':main()
