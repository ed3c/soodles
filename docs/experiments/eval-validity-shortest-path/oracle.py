#!/usr/bin/env python3
"""Fixed external controls for a single feature-map report family; no provider IO."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

CASES = {
    'normal': ('VALID', 'PASS'),
    'wrong_route': ('VALID', 'FAIL'),
    'missing_operations': ('INCONCLUSIVE', None),
    'null_operations': ('INCONCLUSIVE', None),
    'wrong_source': ('INVALID', None),
    'wrong_instruction': ('INVALID', None),
}
ENV = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, env=ENV,
                                   stderr=subprocess.PIPE, text=True).strip()

def fixture(root):
    git(root, 'init', '-b', 'main')
    files = {
        '.agents/skills/verify-soodles/features/README.md': 'Cross-repository delivery maps dependency satisfaction.\n',
        '.agents/skills/verify-soodles/features/cross-repository-delivery.md': 'Follow landing.next.requests dependency_N_* and current next.argv.\n',
        'task-input.json': '{"need":"locate the existing dependency validation owner"}\n',
    }
    for name, text in files.items():
        path=root/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Evaluator fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-m', 'Freeze synthetic subject before evaluating its report')
    head=git(root, 'rev-parse', 'HEAD')
    instruction='.agents/skills/verify-soodles/features/README.md'
    report={
        'source_head':head,
        'actual_files_read':[{'path':str(root/name),'sha256':sha(text.encode()),'bytes':len(text.encode())} for name,text in files.items()],
        'actual_commands':[], 'classification':'mapped',
        'selected_feature':'Cross-repository delivery',
        'recipe_path':'.agents/skills/verify-soodles/features/cross-repository-delivery.md',
        'owner_boundary':'landing.next.requests dependency_N_*; continue with the current owner',
        'new_feature_required':False,'new_cli_required':False,'new_registry_required':False,
        'delivery_complete':False,'external_operations_performed':[],
    }
    return head, instruction, report

def selection(subject, head, instruction, report_path, evaluator):
    return {'schema':1,'kind':'feature_map_routing_report_v2',
        'experiment_id':'eval-validity-shortest-path-v1',
        'source':{'root':str(subject),'head':head},
        'instruction':{'path':instruction,'sha256':sha((subject/instruction).read_bytes())},
        'report':{'path':str(report_path),'sha256':sha(report_path.read_bytes())},
        'evaluator_sha256':sha(evaluator.read_bytes())}

def observe(source, mode, output):
    source=Path(source).resolve();output=Path(output).resolve();output.mkdir(exist_ok=False)
    records=[]
    with tempfile.TemporaryDirectory(prefix='eval-validity-control-') as directory:
        subject=Path(directory).resolve();head,instruction,normal=fixture(subject)
        for case, expected in CASES.items():
            target=output/case;target.mkdir()
            report=copy.deepcopy(normal)
            if case=='wrong_route':report['selected_feature']='Unrelated feature'
            elif case=='missing_operations':report.pop('external_operations_performed')
            elif case=='null_operations':report['external_operations_performed']=None
            elif case=='wrong_source':report['source_head']='f'*40
            elif case=='wrong_instruction':report['actual_files_read'][0]['sha256']='0'*64
            report_path=target/'report.json';put(report_path,report)
            if mode=='legacy':
                evaluator=source/'docs/experiments/feature-map-dependency-routing/evaluator.py'
                argv=[sys.executable,'-B',str(evaluator),str(report_path),str(subject),head,str(target/'receipt.json')]
            else:
                evaluator=source/'report_evaluation.py'
                spec=selection(subject,head,instruction,report_path,evaluator)
                selected=target/'selection.json';put(selected,spec)
                argv=[sys.executable,'-B',str(source/'soodles.py'),'eval','report',str(selected),sha(selected.read_bytes())]
            started=time.monotonic()
            process=subprocess.run(argv,cwd=source,env=ENV,stdin=subprocess.DEVNULL,
                capture_output=True,text=True,timeout=60)
            put(target/'process.json',{'argv':argv,'cwd':str(source),'exit':process.returncode,
                'stdout':process.stdout,'stderr':process.stderr,'elapsed_seconds':time.monotonic()-started})
            if mode=='legacy':
                result=json.loads((target/'receipt.json').read_text())
                # Legacy has no validity field: preserve that absence, never fabricate VALID.
                actual=(None,'PASS' if result['classification']=='NO_OBSERVED_BARRIER' else 'FAIL')
                passed=(case in ('normal','wrong_route') and actual[1]==expected[1])
            else:
                result=json.loads(process.stdout);put(target/'receipt.json',result)
                behavior=result.get('behavior')
                actual=(result.get('evidence_validity'),behavior.get('classification') if isinstance(behavior,dict) else None)
                passed=actual==expected and result.get('owner')=='eval.report' and result.get('authorizes_landing') is False
                passed=passed and result.get('observation_scope')=='consumer_report'
                if expected[0]!='VALID':
                    passed=passed and behavior is None and process.returncode!=0 and result.get('next',{}).get('owner')=='supervisor'
                else:
                    passed=passed and process.returncode==(0 if expected[1]=='PASS' else 1)
            records.append({'case':case,'expected':list(expected),'observed':list(actual),'predicate':'PASS' if passed else 'FAIL'})
        source_clean=git(subject,'status','--porcelain')==''
    result={'mode':mode,'classification':'GREEN' if all(x['predicate']=='PASS' for x in records) and source_clean else 'RED',
        'records':records,'source_clean':source_clean,'disposable_removed':not subject.exists(),
        'provider_operations':0,'oracle_sha256':sha(Path(__file__).read_bytes()),'authorizes_landing':False}
    put(output/'result.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('mode',choices=['legacy','candidate']);p.add_argument('output')
    args=p.parse_args();print(json.dumps(observe(args.source,args.mode,args.output),indent=2))
