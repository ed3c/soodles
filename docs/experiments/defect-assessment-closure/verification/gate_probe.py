#!/usr/bin/env python3
"""Synthetic gate controls; fixed PASS bytes are not real Agent evidence."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
source=Path(sys.argv[1]).resolve();sys.path.insert(0,str(source))
import issue_admission as gate

def encoded(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def command(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.PIPE).strip()
def write(root,name,data):
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
def commit(root):
 command(root,'add','.');command(root,'-c','user.name=Gate Fixture','-c','user.email=fixture@example.invalid','commit','-m','Fixed fixture')
 return command(root,'rev-parse','HEAD')
records=[]
with tempfile.TemporaryDirectory(prefix='soodles-assessment-gate-') as temporary:
 root=Path(temporary);command(root,'init','-b','main')
 before=b'Follow existing owner.\n';after=before+b'Consume its current context.\n'
 write(root,'AGENTS.md',before);base=commit(root)
 artifacts={name:encoded({'scope':'synthetic control only','classification':'PASS','axis':name}) for name in ('product.json','behavior.json','confirmation.json')}
 required=['AGENTS.md','manifest.json',*artifacts]
 contract={'schema':3,'trigger':'Fixed assessment bytes must bind local completion.','source':'synthetic control','owner':'existing gate','changes':['Reject replacement of selected evidence.'],'write_paths':required,'required_paths':required,'base_head':base,'frozen_paths':[{'path':p,'revision':'head','sha256':sha(data)} for p,data in artifacts.items()],'evidence_manifest':'manifest.json','behavior':['Reject absent or substituted required evidence.'],'defect_controls':['Nearest complete candidate and substituted receipt.'],'non_cases':['No fresh Agent evidence in these fixtures.'],'dependencies':[],'acceptance':'Existing owner','delivery':'Existing owner','reconciliation':'Existing owner','feature_scope':'External assessment integrity'}
 for name,data in artifacts.items():write(root,name,data)
 write(root,'AGENTS.md',after)
 def manifest():
  return {'schema':1,'issue':{'repository':'ed3c/soodles','number':1},'instructions':[{'path':'AGENTS.md','baseline_sha256':sha(before),'treatment_sha256':sha(after)}],'artifacts':[{'path':p,'role':'synthetic control','sha256':sha((root/p).read_bytes())} for p in artifacts if (root/p).exists()],'owner':{'name':'Soodles Issue admission','tool':'issue_admission.validate_delivery_paths','authorization':'ed3c/soodles#1'},'authorizes_landing':False}
 write(root,'manifest.json',encoded(manifest()));clean=commit(root)
 body='<!-- soodles:execution-v1 -->\n```json\n'+json.dumps(contract)+'\n```\n<!-- /soodles:execution-v1 -->\n'
 issue={'number':1,'url':'https://api.github.com/repos/ed3c/soodles/issues/1','html_url':'https://github.com/ed3c/soodles/issues/1','state':'open','body':body}
 binding={'repository':'ed3c/soodles','issue':1,'base_head':base,'write_paths':required,'contract':gate.parse_contract(body)}
 for case in ('complete','missing_product','missing_behavior','missing_confirmation','substituted_behavior'):
  command(root,'reset','--hard',clean)
  if case.startswith('missing_'):(root/(case[8:]+'.json')).unlink()
  elif case=='substituted_behavior':write(root,'behavior.json',encoded({'scope':'synthetic','classification':'FAIL'}))
  if case!='complete':write(root,'manifest.json',encoded(manifest()));head=commit(root)
  else:head=clean
  before_tree=command(root,'status','--porcelain');observations={}
  for name,operation in [('shared',lambda:gate.validate_delivery_paths(root,base,head,binding)),('candidate',lambda:gate.verify_candidate(root,base,head,issue))]:
   try:receipt=operation();observations[name]={'status':'PASS','authorizes_landing':receipt['authorizes_landing']}
   except gate.AdmissionRefusal as e:observations[name]={'status':'REFUSED','invalid':e.invalid,'next':e.next}
  records.append({'case':case,'observations':observations,'workspace_unchanged':before_tree==command(root,'status','--porcelain')})
print(json.dumps({'scope':'synthetic gate controls; no fresh behavior or live provider effects','source':str(source),'source_sha256':sha((source/'issue_admission.py').read_bytes()),'records':records,'authorizes_landing':False},indent=2))
