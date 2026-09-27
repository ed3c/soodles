"""External fixed oracle: bind the recovery replay metric before analyzer import.

Usage: python3 oracle.py SOURCE OUTPUT.json
Only disposable subprocesses are driven; no credentials or provider effects.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def drive(source):
    source = Path(source).resolve()
    fixture = json.loads(Path(__file__).with_name('fixture.json').read_text())
    script = source / '.agents/skills/verify-soodles/scripts/replay_pclass.py'
    cases = [('supported', 'post_completion_owner_request'), ('wrong_metric', 'wrong_route'),
             ('unknown_metric', 'unmeasured_barrier'), ('empty_metric', ''),
             ('null_metric', None), ('array_metric', []), ('missing_metric', None),
             ('before_import', 'wrong_route')]
    results = []
    with tempfile.TemporaryDirectory(prefix='pclass-metric-oracle-') as directory:
        work = Path(directory)
        for label, metric in cases:
            case = work / label
            case.mkdir()
            marker = case / 'imported'
            observer = case / 'observer.py'
            decider = case / 'decider.py'
            observer.write_text(fixture['observer'])
            decider.write_text(fixture['decider'])
            if label == 'before_import':
                observer.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n' + fixture['observer'])
            manifest = copy.deepcopy(fixture['manifest'])
            manifest['primary_barrier'] = metric
            if label == 'missing_metric':
                del manifest['primary_barrier']
            for name,path in [('observer',observer),('decider',decider),('normalizer',script)]:
                manifest[name+'_sha256'] = digest(path.read_bytes())
            for name,value in [('raw',fixture['raw']),('gates',fixture['gates']),('manifest',manifest)]:
                (case/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
            argv = [sys.executable,'-B',str(script),str(case/'raw.json'),str(case/'gates.json'),
                    str(case/'manifest.json'),fingerprint(manifest),str(observer),str(decider)]
            env={k:os.environ[k] for k in ('PATH','LANG','LC_ALL','TMPDIR') if k in os.environ}
            proc = subprocess.run(argv,env=env,capture_output=True,text=True,timeout=45)
            try:
                receipt=json.loads(proc.stdout)
            except ValueError:
                receipt=None
            if label=='supported':
                passed=(proc.returncode==0 and isinstance(receipt,dict)
                        and receipt.get('classification')=='PASS'
                        and receipt.get('authorizes_landing') is False
                        and receipt.get('decision',{}).get('decision')=='ADMIT_IMPROVEMENT'
                        and receipt['decision'].get('baseline_total')==3
                        and receipt['decision'].get('treatment_total')==0
                        and len(receipt.get('controls',[]))==6
                        and all(c.get('predicate')=='PASS' for c in receipt['controls']))
            else:
                passed=(proc.returncode!=0 and isinstance(receipt,dict)
                        and receipt.get('classification')=='FAIL'
                        and receipt.get('authorizes_landing') is False
                        and any('primary_barrier' in str(e) for e in receipt.get('errors',[]))
                        and not receipt.get('decision',{}).get('decision','').startswith('ADMIT_')
                        and 'Traceback' not in proc.stderr and not marker.exists())
            results.append({'case':label,'passed':passed,'argv':argv,'exit_code':proc.returncode,
                            'stdout':proc.stdout,'stderr':proc.stderr,'analyzer_imported':marker.exists()})
    return {'schema':1,'classification':'PASS' if all(r['passed'] for r in results) else 'FAIL',
            'source':str(source),'replayer_sha256':digest(script.read_bytes()),
            'oracle_sha256':digest(Path(__file__).read_bytes()),
            'fixture_sha256':digest(Path(__file__).with_name('fixture.json').read_bytes()),
            'cases':results,'authorizes_landing':False}


if __name__=='__main__':
    result=drive(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'classification':result['classification'],'passed':sum(r['passed'] for r in result['cases']),'total':len(result['cases']),'authorizes_landing':False}))
    raise SystemExit(0 if result['classification']=='PASS' else 1)
