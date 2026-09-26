import sys,json,hashlib,subprocess,os,shutil
from pathlib import Path
source=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); arm=sys.argv[3]; frozen=Path(__file__).resolve().parent
sys.path[:0]=[str(source),str(frozen/'fixtures')]
import test_supervisor_admission
test_supervisor_admission.ROOT=source
from test_supervisor_admission import SupervisorFixture
import issue_execution as ix
f=SupervisorFixture()
try:
 p='.agents/skills/verify-soodles/features/pclass-context.md';b=(frozen/'selected-recipe.md').read_bytes();path=f.root/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
 f._git('add',p);f._git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Fixed selected recipe fixture')
 f.head=f._git('rev-parse','HEAD'); f.contract['base_head']=f.head
 f.issue['body']='<!-- soodles:execution-v1 -->\n```json\n'+json.dumps(f.contract)+'\n```\n<!-- /soodles:execution-v1 -->\n'; f.issue_path.write_text(json.dumps(f.issue))
 task='Use the selected recipe '+p+' to handle the current supplied evaluation-owner result. Return only owner, required, behavior, authorizes_landing in result.json. Recipe bytes are available through the supplied reader. This is a read-only fixture with no provider or lifecycle action authorization.'
 kw={'task':task}
 if arm=='treatment':kw['instruction_pins']=[{'path':p,'sha256':hashlib.sha256(b).hexdigest()}]
 bundle,prepared=f.prepare(**kw)
 route=ix.inspect_schedule(f.root,{**f.schedule_env,'SOODLES_ADMISSION_LAUNCHER':prepared['launcher']})['next']['argv']
 env={k:v for k,v in os.environ.items() if not k.startswith('NOODLE_')};env['FIXTURE_ISSUE_READBACK']=str(f.issue_path)
 run=subprocess.run(route,cwd=f.root,env=env,capture_output=True,text=True,timeout=30);assert run.returncode==0,run.stderr+run.stdout
 prompt=json.loads(json.loads((f.root/'.noodle/orders-next.json').read_text())['orders'][0]['stages'][0]['prompt'])
 output.mkdir(parents=True,exist_ok=True);(output.parent/'observations').mkdir(exist_ok=True)
 (output/'input.json').write_text(json.dumps({'selected_execute_skill':(frozen/arm/'.agents/skills/execute/SKILL.md').read_text(),'stage_prompt':prompt,'current_owner_result':{'owner':'soodles.eval.report','evidence_validity':'INCONCLUSIVE','behavior':None,'next':{'owner':'external-supervisor','missing_input':['raw_results']},'authorizes_landing':False}},indent=2)+'\n')
 (output/'recipe.md').write_bytes(b);shutil.copyfile(frozen/'read.py',output/'read.py')
 (output.parent/'observations'/f'{output.name}-producer.json').write_text(json.dumps({'argv':route,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'source_head':f.head,'implementation_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'fixture':True},indent=2)+'\n')
finally:f.close()
