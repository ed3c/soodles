from pathlib import Path
import json,subprocess,sys
r=Path(__file__).parent
for label in sys.argv[1:]:
 d=r/label;assert not (d/'postprocess.json').exists();records=[]
 observation=json.loads((d/'live/observation.json').read_text());assert observation['status'] in ['worker_review','worker_completed'],observation['status']
 for name,args in [('native',['python3',str(d/'read_native.py')]),('capture',['python3',str(r/'audit_capture.py'),str(d)]),('cleanup',['python3',str(d/'cleanup_probe.py')])]:
  q=subprocess.run(args,cwd=d,capture_output=True,text=True,timeout=50);records.append({'phase':name,'argv':args,'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr})
  # Capture/cleanup errors remain inspectable; do not manufacture a successful case.
  if name=='native' and q.returncode:break
 (d/'postprocess.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({'run':label,'phases':[{k:v for k,v in x.items() if k in ['phase','exit']} for x in records]}))
 assert len(records)==3 and all(x['exit']==0 for x in records),label
