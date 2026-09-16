"""Bounded baseline probe; provider snapshots are fixtures, no writes transported."""
import copy, hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile
ROOT=pathlib.Path('/workspace/scratch/8d9f1ebaaa91/soodles')
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('fixture',ROOT/'tests/test_landing.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
f=module.LandingTests();f.setUp();rows=[]
def invoke(args):
 argv=[sys.executable,'-B',str(ROOT/'soodles.py'),'landing',*map(str,args)]
 p=subprocess.run(argv,cwd=ROOT,env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','LC_ALL','TMPDIR')},text=True,capture_output=True,timeout=15)
 row={'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr};rows.append(row);return p
before=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT,text=True)
try:
 with tempfile.TemporaryDirectory(prefix='soodles-18-baseline-') as d:
  p=pathlib.Path(d);cp=p/'claim.json';rp=p/'readback.json';cp.write_text(json.dumps(f.claim));cases=[]
  for name,body in [('missing_body',None),('empty_body',''),('undeclared_body','Proposed feature; no executable Issue contract.')]:
   snap=copy.deepcopy(f.snapshot)
   if body is not None:snap['issue']['body']=body
   rp.write_text(json.dumps(snap));out=invoke(['start',cp,rp,p/(name+'.json')]);assert out.returncode==0,out.stderr
   state=json.loads(out.stdout);cases.append({'case':name,'phase':state['phase'],'classification':state['classification'],'writes_offered':json.loads((p/(name+'.json')).read_text())['writes_offered']})
  snap=copy.deepcopy(f.snapshot);snap['issue']['body']='Original authoring text';rp.write_text(json.dumps(snap));chk=p/'drift.json';assert invoke(['start',cp,rp,chk]).returncode==0
  assert invoke(['advance',chk,rp]).returncode==0
  snap['issue']['body']='Changed scope after admission';rp.write_text(json.dumps(snap));out=invoke(['dispatch',chk,rp]);assert out.returncode==0,out.stderr
  cases.append({'case':'body_changed_before_dispatch','request_emitted':json.loads(out.stdout)['request'],'transported':False})
  snap=copy.deepcopy(f.snapshot);snap['issue']['html_url']='https://github.com/other/repo/issues/1';rp.write_text(json.dumps(snap));foreign=p/'foreign.json';out=invoke(['start',cp,rp,foreign]);assert out.returncode!=0 and not foreign.exists()
  cases.append({'case':'foreign_provider_identity','refused':True,'checkpoint_absent':True})
 finally_cleanup='temporary fixture cleaned'
finally:f.doCleanups()
after=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT,text=True);assert before==after==''
report={'schema':1,'issue':18,'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'scope':'Real local CLI over labelled provider fixtures; existing landing owner does not claim Issue-body admission. This is capability-gap evidence, not a claim of regression or a production request.','provider_write_count':0,'production_orders_created':0,'Agent_launch_attempts':0,'classification':'BLOCKED','reason':'Shared execution admission and automatic consumer unimplemented; real Noodle-to-Codex capability remains unresolved in noodle#78/#80.','cases':cases,'commands':rows,'cleanup':{'temporary_fixture_removed':True,'source_unchanged':True},'non_claims':['No automatic admission, dispatch or takeover proof','No canonical acceptance or feature-map expansion','No invalid field schema introduced by this probe']}
out=pathlib.Path('/tmp/soodles-18-admission-preflight/baseline.json');out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':cases,'report_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'commands':len(rows),'cleanup':report['cleanup']}))
