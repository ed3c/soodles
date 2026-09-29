#!/usr/bin/env python3
"""Crash/readback qualification using the actual owner, disposable provider-free fixtures."""
import hashlib, importlib.util, json, os
from pathlib import Path
import signal, subprocess, sys, time

ROOT=Path(__file__).resolve().parent.parent
SOURCE=Path('/Users/neon/.codex/experiments/claim-refusal-closure-39lph64z/control-r02')
FACTORY=Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/fixture-public/workspace.py')
PYTHON=str(Path(sys.executable).resolve())

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def snap(path):
    return {str(p.relative_to(path)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(path.rglob('*')) if p.is_file()} if path.exists() else {}

def child():
    control,selection,selected_sha,out,point=sys.argv[2:]
    sys.path.insert(0,control)
    import supervisor_admission as owner
    target=Path(out)
    write=Path.write_bytes
    replace=owner.os.replace
    def killed(): os.kill(os.getpid(),signal.SIGKILL)
    def fault_write(path,data):
        result=write(path,data)
        if point=='authorization_written' and path==target/'authorization.json': killed()
        return result
    def fault_replace(source,destination):
        if Path(destination)==target/'prepared.json' and point=='prepared_temp_written': killed()
        result=replace(source,destination)
        if Path(destination)==target/'prepared.json' and point=='receipt_published': killed()
        return result
    Path.write_bytes=fault_write
    owner.os.replace=fault_replace
    sys.argv=[str(Path(control)/'supervisor-admission'),'authorize',selection,selected_sha,out]
    raise SystemExit(owner.main())

def main():
    spec=importlib.util.spec_from_file_location('fixture_factory',FACTORY)
    factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
    report={'source':{'path':str(SOURCE),'head':factory.git(SOURCE,'rev-parse','HEAD'),
                      'owner_sha256':digest(SOURCE/'supervisor_admission.py')},
            'instrumentation':{'path':str(Path(__file__)),'sha256':digest(Path(__file__)),
                'scope':'SIGKILL after successful actual filesystem operation, before CLI stdout; owner source unchanged'},
            'factory':{'path':str(FACTORY),'sha256':digest(FACTORY)},'cases':[]}
    cases=ROOT/'discovery'/'faults';cases.mkdir()
    for point in ('clean','authorization_written','prepared_temp_written','receipt_published'):
        case=cases/point;case.mkdir();workspace=case/'workspace'
        factory.create(SOURCE,'soodles-work-1',workspace)
        facts=json.loads((workspace/'workspace.json').read_text())
        selection=facts['selection'];control=Path(facts['control_root']);out=Path(selection['external_output'])
        env=dict(os.environ)
        for name in tuple(env):
            if name.startswith(('NOODLE_','NOODLES_','SOODLES_')) or name in factory.SENSITIVE_ENV: env.pop(name,None)
        env.update(facts['host']['environment'])
        invoke=[PYTHON,'-B',str(control/'supervisor-admission'),'authorize',selection['path'],selection['sha256'],str(out)]
        instrumented=[PYTHON,'-B',str(Path(__file__)),'--child',str(control),selection['path'],selection['sha256'],str(out),point]
        def run(argv,label):
            start=time.monotonic();result=subprocess.run(argv,cwd=control,env=env,capture_output=True,timeout=45)
            (case/(label+'.stdout')).write_bytes(result.stdout);(case/(label+'.stderr')).write_bytes(result.stderr)
            value={'argv':argv,'returncode':result.returncode,'elapsed_seconds':time.monotonic()-start,
                   'stdout':{'path':str(case/(label+'.stdout')),'sha256':digest(case/(label+'.stdout'))},
                   'stderr':{'path':str(case/(label+'.stderr')),'sha256':digest(case/(label+'.stderr'))}}
            save(case/(label+'.json'),value);return value
        before=snap(out);first=run(invoke if point=='clean' else instrumented,'first');after=snap(out)
        retry=run(invoke,'readback-attempt');end=snap(out)
        refused=json.loads((case/'readback-attempt.stdout').read_text())
        value={'point':point,'first':first,'readback_attempt':retry,'before':before,'after_crash':after,'after_readback':end,
               'refusal':refused,'identity_unchanged_by_readback':after==end,
               'no_lifecycle_checkpoint':not list(out.glob('*.state.json')),
               'no_noodle_state':not (control/'.noodle').exists(),
               'git_clean':not factory.git(control,'status','--porcelain','--untracked-files=all'),
               'provider_scope':'No lifecycle invocation; no provider capability in fixture; preparation has no transport'}
        save(case/'observation.json',value);report['cases'].append(value)
    save(ROOT/'discovery'/'reproduction.json',report)
    print(json.dumps({'report':str(ROOT/'discovery'/'reproduction.json'),'cases':[
        {'point':c['point'],'first_exit':c['first']['returncode'],'remaining':list(c['after_crash']),
         'readback_field':c['refusal']['invalid']['field'],'next':c['refusal']['next']} for c in report['cases']]},indent=2))

if __name__=='__main__':
    child() if len(sys.argv)>1 and sys.argv[1]=='--child' else main()
