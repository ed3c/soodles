"""Independent disposable report fixture; never imports candidate code."""
import hashlib, json, os, subprocess
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def make(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    subject = destination / 'subject'
    subject.mkdir()
    env = {k:v for k,v in os.environ.items() if not k.startswith(('GIT_', 'NOODLE', 'GH_', 'GITHUB_'))}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=subject, env=env, stderr=subprocess.PIPE, text=True).strip()
    git('init', '-b', 'main')
    files = {'.agents/skills/verify-soodles/features/README.md': b'dependency map\n',
             '.agents/skills/verify-soodles/features/cross-repository-delivery.md': b'current landing owner\n',
             'task-input.json': b'{}\n'}
    for name,data in files.items():
        p=subject/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    git('add','.')
    git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Pin disposable subject')
    head=git('rev-parse','HEAD')
    report={'source_head':head,'actual_files_read':[{'path':p,'sha256':sha(b),'bytes':len(b)} for p,b in files.items()],
            'actual_commands':[], 'classification':'mapped','selected_feature':'Cross-repository delivery',
            'recipe_path':'.agents/skills/verify-soodles/features/cross-repository-delivery.md',
            'owner_boundary':'landing.next.requests dependency_N_*','new_feature_required':False,
            'new_cli_required':False,'new_registry_required':False,'delivery_complete':False,'external_operations_performed':[]}
    cases={}
    for name in ('family','missing','normal','route'):
        r=dict(report)
        if name=='missing': r.pop('external_operations_performed')
        if name=='route': r['selected_feature']='Unrelated feature'
        rp=destination/(name+'-report.json');rp.write_text(json.dumps(r)+'\n')
        selection={'schema':1,'kind':'other' if name=='family' else 'feature_map_routing_report_v2',
                   'experiment_id':'eval-validity-shortest-path-v1','source':{'root':str(subject),'head':head},
                   'instruction':{'path':next(iter(files)),'sha256':sha(next(iter(files.values())))},
                   'report':{'path':str(rp),'sha256':sha(rp.read_bytes())},
                   'evaluator_sha256':sha((source/'report_evaluation.py').read_bytes())}
        sp=destination/(name+'-selection.json');sp.write_text(json.dumps(selection)+'\n')
        cases[name]=['./soodles','eval','report',str(sp),sha(sp.read_bytes())]
    cases['arguments']=['./soodles','eval','report','--unsupported-option']
    (destination/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    return cases
