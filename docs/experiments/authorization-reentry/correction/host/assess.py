#!/usr/bin/env python3
"""Seal the selected run's observations and invoke the fixed external oracle."""
import hashlib,json,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return {'path':str(p),'sha256':sha(p)}
def main():
    label=sys.argv[1];packet=BASE/'host/runs'/label
    spec=json.loads((packet/'case.json').read_text());run=Path(spec['run_root']);raw=run/'raw'
    facts=run/'output/workspace/workspace.json';case=json.loads(facts.read_text())['work_id']
    cases=json.loads((BASE/'private/cases.json').read_text())
    capture={'binding':run/'binding.json',**{k:raw/n for k,n in {'launch':'launch.json','exit':'exit.json','stdout':'stdout.bin','stderr':'stderr.bin','task_boundary':'task-boundary.json','isolation':'isolation-probe.json','profile':'consumer.sb'}.items()}}
    descriptor={'case_id':case,'stratum':cases[case]['stratum'],'group':cases[case]['group'],'workspace':pin(facts),'before':pin(raw/'workspace-before.json'),'drive':pin(packet/'public/drive.py'),'capture':{k:pin(p) for k,p in capture.items()}}
    path=packet/'descriptor.json'
    if path.exists():raise RuntimeError('refuse overwrite of sealed observations')
    path.write_text(json.dumps(descriptor,indent=2)+'\n')
    freeze=json.loads((BASE/'freeze.json').read_text())
    for p,digest in freeze['pins'].items():
        if sha(p)!=digest:raise RuntimeError('frozen input changed: '+p)
    argv=[spec['python'],'-B',str(BASE/'evaluator/check.py'),str(path),sha(path)]
    result=subprocess.run(argv,capture_output=True,text=True)
    (packet/'result.json').write_text(result.stdout);(packet/'result.stderr').write_text(result.stderr)
    (packet/'assessment.json').write_text(json.dumps({'argv':argv,'exit':result.returncode},indent=2)+'\n')
    v=json.loads(result.stdout)
    print(json.dumps({'label':label,'result':v.get('evidence_validity'),'behavior':v.get('behavior'),'commands':(v.get('cost') or {}).get('completed_commands')},indent=2))
    return result.returncode
if __name__=='__main__':raise SystemExit(main())
