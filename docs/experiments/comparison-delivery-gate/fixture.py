"""Synthetic comparison fixtures; historical event shapes are not new model evidence."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

PREFIX = '.agents/skills/verify-soodles/scripts/'
ANALYZERS = {'replayer': PREFIX+'replay_pclass.py', 'observer': PREFIX+'observe_pclass.py', 'decider': PREFIX+'decide_pclass.py'}
POLICY = 'AGENTS.md'
RAW = 'evidence/raw.json'
GATES = 'evidence/gates.json'
MANIFEST = 'evidence/comparison.json'
EVIDENCE = 'evidence/manifest.json'
BASELINE = b'---\nname: comparison-fixture\ndescription: Fixture baseline.\n---\nFollow the current owner.\n'
TREATMENT = BASELINE + b'Stop at the selected completion projection.\n'
EXPERIMENT = 'comparison-delivery-gate-fixture-v1'

def sha(data): return hashlib.sha256(data).hexdigest()
def encoded(value): return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def fingerprint(value): return sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
def git(root,*args): return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.PIPE).strip()
def write(root,path,data):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
def commit(root,message):
    git(root,'add','.');git(root,'-c','user.name=Comparison Fixture','-c','user.email=fixture@example.invalid','commit','-m',message)
    return git(root,'rev-parse','HEAD')

def build(source,destination,case='admitted'):
    source=Path(source).resolve();root=Path(destination).resolve();root.mkdir(parents=True)
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=source).decode().split('\0')
    for name in sorted(set(names)-{''}):
        path=source/name
        if path.is_file():write(root,name,path.read_bytes())
    git(root,'init','-b','main')
    write(root,POLICY,BASELINE)
    analyzer_pins={key:{'path':path,'revision':'base','sha256':sha((root/path).read_bytes())} for key,path in ANALYZERS.items()}
    sentinel=root.parent/(root.name+'-observer-imported')
    if case=='analyzer_mismatch':
        write(root,ANALYZERS['observer'],('from pathlib import Path\nPath('+repr(str(sentinel))+').touch()\n').encode())
    base=commit(root,'Freeze synthetic comparison base')
    raw=json.loads((source/'docs/experiments/pclass-recovery-stop-73/raw/raw-runs.json').read_text())
    manifest=json.loads((source/'docs/experiments/pclass-derived-admission-77/manifest.json').read_text())
    gates=json.loads((source/'docs/experiments/pclass-derived-admission-77/gates.json').read_text())
    gates['experiment_id']=manifest['experiment_id']=EXPERIMENT
    for run in raw['runs']:
        data=BASELINE if run['arm']=='baseline' else TREATMENT
        run['packet']['instruction']={'path':POLICY,'sha256':sha(data)}
        for observation in run['instruction_observations']:
            observation.update(path=POLICY,sha256=sha(data),bytes=len(data))
    if case=='rejected': gates['independent_audit']['classification']='FAIL'
    if case=='weak_target': manifest['admission_target']='nonregression'
    manifest['observer_sha256']=analyzer_pins['observer']['sha256']
    manifest['normalizer_sha256']=analyzer_pins['replayer']['sha256']
    manifest['decider_sha256']=analyzer_pins['decider']['sha256']
    manifest['gates_sha256']=fingerprint(gates)
    manifest['runs']=[{'run_id':r['run_id'],'arm':r['arm'],'case':r['packet']['case'],'evidence_sha256':fingerprint(r)} for r in raw['runs']]
    inputs={RAW:encoded(raw),GATES:encoded(gates),MANIFEST:encoded(manifest)}
    comparison={'kind':'pclass_replay_v2','experiment_id':EXPERIMENT,'admission_target':'improvement',
                'subject':{'repository':'ed3c/soodles','issue':1,'base_head':base},
                'instructions':[{'path':POLICY,'baseline_sha256':sha(BASELINE),'treatment_sha256':sha(TREATMENT)}],
                'raw':{'path':RAW,'sha256':sha(inputs[RAW])},
                'gates':{'path':GATES,'sha256':sha(inputs[GATES])},
                'manifest':{'path':MANIFEST,'sha256':sha(inputs[MANIFEST])},'analyzers':analyzer_pins}
    if case=='foreign_subject': comparison['subject']['issue']=2
    actual_treatment=TREATMENT+b'Foreign instruction.\n' if case=='foreign_instruction' else TREATMENT
    if case=='raw_tamper':
        altered=copy.deepcopy(raw);altered['runs'][0]['owner_events'].append({'owner':'landing.dispatch'})
        inputs[RAW]=encoded(altered)
    write(root,POLICY,actual_treatment)
    for path,data in inputs.items(): write(root,path,data)
    required=[POLICY,EVIDENCE,RAW,GATES,MANIFEST]
    evidence={'schema':1,'issue':{'repository':'ed3c/soodles','number':1},
              'instructions':[{'path':POLICY,'baseline_sha256':sha(BASELINE),'treatment_sha256':sha(actual_treatment)}],
              'artifacts':[{'path':p,'role':'comparison_fixture','sha256':sha(data)} for p,data in inputs.items()],
              'owner':{'name':'Soodles Issue admission','tool':'issue_admission.validate_delivery_paths','authorization':'ed3c/soodles#1'},'authorizes_landing':False}
    write(root,EVIDENCE,encoded(evidence))
    if case=='missing': (root/RAW).unlink()
    head=commit(root,'Materialize synthetic comparison evidence')
    contract={'schema':3 if case=='ordinary' else 4,'trigger':'An externally required comparison gates this synthetic candidate.',
              'source':'Fixed external synthetic comparison fixture.','owner':'Soodles candidate verification',
              'changes':['Consume externally pinned comparison before delivery.'],'write_paths':required,'required_paths':required,
              'evidence_manifest':EVIDENCE,'base_head':base,
              'frozen_paths':[{'path':MANIFEST,'revision':'head','sha256':sha(inputs[MANIFEST])}],
              'behavior':['Comparison gate precedes candidate delivery.'],'defect_controls':['Rejected and foreign comparisons refuse.'],
              'non_cases':['Ordinary schema-3 atom.'],'dependencies':[],'acceptance':'Fixed external comparison requirement.',
              'delivery':'Existing owner only.','reconciliation':'Existing owner only.','feature_scope':'Synthetic comparison delivery gate.'}
    if case!='ordinary': contract['comparison']=comparison
    body='<!-- soodles:execution-v1 -->\n```json\n'+json.dumps(contract,indent=2)+'\n```\n<!-- /soodles:execution-v1 -->\n'
    issue={'url':'https://api.github.com/repos/ed3c/soodles/issues/1','html_url':'https://github.com/ed3c/soodles/issues/1',
           'number':1,'body':body,'state':'open','updated_at':'2026-09-23T00:00:00Z'}
    readback=root.parent/(root.name+'-issue.json');readback.write_bytes(encoded(issue))
    return {'root':str(root),'base':base,'head':head,'issue':str(readback),'sentinel':str(sentinel),'case':case,
            'comparison':comparison,'provider_transport_authorized':False}
