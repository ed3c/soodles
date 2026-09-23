"""Frozen process oracle; no candidate verdict implementation is imported."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

CASES=('ordinary','admitted','rejected','foreign_subject','foreign_instruction','raw_tamper','weak_target','missing','analyzer_mismatch')
def run(source,output):
    source=Path(source).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('external_fixture',Path(__file__).with_name('fixture.py'))
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    records=[]
    with tempfile.TemporaryDirectory(prefix='comparison-gate-oracle-') as folder:
        for case in CASES:
            value=fixture.build(source,Path(folder)/case,case)
            argv=[sys.executable,'-B',str(Path(value['root'])/'soodles.py'),'candidate','verify',value['issue'],value['base'],value['head']]
            before=time.monotonic();p=subprocess.run(argv,cwd=value['root'],capture_output=True,text=True,timeout=60)
            try: result=json.loads(p.stdout)
            except ValueError:result={}
            positive=case in ('ordinary','admitted')
            ok=(p.returncode==0 and result.get('classification')=='VERIFIED') if positive else (p.returncode!=0 and result.get('status')=='refused' and 'request' not in result)
            if case=='admitted':ok=ok and result.get('comparison',{}).get('decision')=='ADMIT_IMPROVEMENT'
            if case=='analyzer_mismatch':ok=ok and not Path(value['sentinel']).exists()
            records.append({'case':case,'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,
                            'elapsed_seconds':time.monotonic()-before,'predicate':'PASS' if ok else 'FAIL',
                            'sentinel_observed':Path(value['sentinel']).exists(),'provider_transport_count':0})
    receipt={'classification':'GREEN' if all(r['predicate']=='PASS' for r in records) else 'RED',
             'scope':'fixed synthetic candidate comparison gate; no provider transport','records':records,'authorizes_landing':False}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'classification':receipt['classification'],'predicates':{r['case']:r['predicate'] for r in records},'receipt':str(output/'receipt.json')}))
    return 0 if receipt['classification']=='GREEN' else 1
if __name__=='__main__':raise SystemExit(run(sys.argv[1],sys.argv[2]))
