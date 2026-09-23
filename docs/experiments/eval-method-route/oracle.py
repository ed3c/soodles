"""Frozen external CLI observer, real subprocess output and bounded predicates."""
import copy, hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path
from fixture import make

HELP=['./soodles','eval','report','--help']
def judge(records):
    expected={'arguments':('INVALID',None,2,'arguments'), 'family':('INVALID',None,2,'selection.kind'),
              'missing':('INCONCLUSIVE',None,2,'report.external_operations_performed'),
              'normal':('VALID','PASS',0,None),'route':('VALID','FAIL',1,None)}
    checks={}
    for name,(valid,behavior,code,field) in expected.items():
        r=records[name];v=json.loads(r['stdout']);n=v.get('next',{})
        checks[name+'.semantics']=(v['evidence_validity']==valid and (v['behavior'] or {}).get('classification')==behavior
            and r['exit']==code and v['authorizes_landing'] is False)
        if field:
            checks[name+'.problem']=(v.get('problem',{}).get('field')==field and n.get('owner')=='supervisor'
                and n.get('operation')=='supply_report_evidence' and n.get('missing_input')==v['problem'])
            checks[name+'.help']=(n.get('help_argv')==HELP and r.get('help',{}).get('exit')==0)
    return checks

def drive(source, destination):
    source, destination=Path(source).resolve(),Path(destination).resolve()
    destination.mkdir(parents=True,exist_ok=False)
    records={}
    env={k:v for k,v in os.environ.items() if not k.startswith(('NOODLE','GH_','GITHUB_'))}
    env['PYTHONDONTWRITEBYTECODE']='1'
    def run(argv):
        started=time.monotonic()
        p=subprocess.run(argv,cwd=source,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=60)
        return {'argv':argv,'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode,'elapsed_seconds':time.monotonic()-started}
    with tempfile.TemporaryDirectory(prefix='eval-route-fixture-') as tmp:
        cases=make(source,Path(tmp)/'inputs')
        for name,argv in cases.items():
            r=run(argv);v=json.loads(r['stdout']);help_argv=v.get('next',{}).get('help_argv')
            if help_argv==HELP: r['help']=run(help_argv)
            records[name]=r
        snapshots={str(p.relative_to(Path(tmp))):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'content':p.read_text()}
                   for p in (Path(tmp)/'inputs').glob('*.json')}
    checks=judge(records)
    planted=copy.deepcopy(records)
    v=json.loads(planted['family']['stdout']);v['next'].pop('help_argv',None)
    planted['family']['stdout']=json.dumps(v)
    result={'schema':1,'source':str(source),'records':records,'input_snapshots':snapshots,'checks':checks,
            'classification':'GREEN' if all(checks.values()) else 'RED',
            'planted_missing_help_rejected':not judge(planted)['family.help'],
            'fixture_removed':not Path(tmp).exists(),'authorizes_landing':False,
            'source_digests':{p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in ('soodles.py','report_evaluation.py','.agents/skills/verify-soodles/features/pclass-context.md')}}
    (destination/'controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','input_snapshots')}))
    return result
if __name__=='__main__': drive(*sys.argv[1:])
