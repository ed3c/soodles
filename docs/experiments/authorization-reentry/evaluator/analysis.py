#!/usr/bin/env python3
"""Aggregate only this fixed protocol; never invokes a product or grants landing."""
import hashlib,json,statistics,sys
from pathlib import Path

class Invalid(ValueError):pass

def validate(values,shape):
    if len(values)!=len(shape):raise Invalid('wrong run membership')
    for v,stratum in zip(values,shape):
        if v.get('evidence_validity')!='VALID':raise Invalid('invalid or inconclusive evidence')
        if v.get('stratum')!=stratum:raise Invalid('wrong stratum membership')
        if v.get('behavior',{}).get('classification') not in ('PASS','FAIL'):raise Invalid('missing behavior')
    identities=[run_identity(v) for v in values]
    if len(set(identities))!=len(identities):raise Invalid('duplicate actual consumer run')

def run_identity(value):
    identities={v['key'][0] for v in value.get('cost',{}).get('command_event_locators',[]) if isinstance(v.get('key'),list) and len(v['key'])==3}
    if len(identities)!=1 or not all(isinstance(i,str) and i for i in identities):raise Invalid('missing actual run identity')
    return next(iter(identities))

def passed(values):return all(v['behavior']['classification']=='PASS' for v in values)

def command_cost(values):
    if not passed(values) or not all(v.get('cost_comparison_eligible') is True for v in values):raise Invalid('incomplete tasks have no qualified cost')
    result=[v.get('cost',{}).get('completed_commands') for v in values]
    if any(type(x) is not int or x<1 for x in result):raise Invalid('missing command count')
    return result

def decide(baseline,candidate,comparator=None):
    shape=['A','A','A','B','C'];validate(baseline,shape);validate(candidate,shape)
    if {run_identity(v) for v in baseline}&{run_identity(v) for v in candidate}:raise Invalid('shared baseline/candidate consumer')
    reproduced=sum(v['behavior']['classification']=='FAIL' for v in baseline[:3])
    value={'authorizes_landing':False,'baseline_target_failures':reproduced,'candidate_all_gates':passed(candidate),'cost_improvement':None,'adopt':False,'verdict':'revert'}
    if not passed(candidate):return {**value,'reason':'candidate behavior gate failed; cost not used'}
    if not reproduced:return {**value,'verdict':'inconclusive','reason':'target failure not reproduced in this baseline'}
    if comparator is None:
        return {**value,'adopt':True,'verdict':'keep_correctness','reason':'recovery completion improved; cost remains unproved','efficiency_target_achieved':False}
    validate(comparator,['A','A','A'])
    if {run_identity(v) for v in comparator}&{run_identity(v) for v in baseline+candidate}:raise Invalid('shared comparator consumer')
    before=command_cost(comparator);after=command_cost(candidate[:3])
    b,a=statistics.median(before),statistics.median(after);delta=(b-a)/b;below=sum(x<b for x in after)
    value.update(cost_improvement={'before':before,'after':after,'before_median':b,'after_median':a,'relative_reduction':delta,'below_before_median':below})
    if delta>=0.2 and below>=2:return {**value,'adopt':True,'verdict':'keep_efficiency','reason':'all gates pass and fixed qualified cost target met','efficiency_target_achieved':True}
    return {**value,'reason':'qualified command reduction did not meet unchanged threshold','efficiency_target_achieved':False}

def main():
    try:
        def pinned(pin):
            data=Path(pin['path']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=pin['sha256']:raise Invalid('artifact digest mismatch')
            return json.loads(data)
        if len(sys.argv)!=3:raise Invalid('usage: analysis.py MANIFEST EXPECTED_SHA256')
        manifest=pinned({'path':sys.argv[1],'sha256':sys.argv[2]})
        def read(name):return [pinned(p) for p in manifest[name]]
        result=decide(read('baseline'),read('candidate'),read('comparator') if 'comparator' in manifest else None)
    except (Invalid,OSError,ValueError,KeyError,TypeError,IndexError) as error:result={'verdict':'INVALID','adopt':False,'reason':str(error),'authorizes_landing':False}
    print(json.dumps(result,indent=2));return 0 if result['adopt'] else 1
if __name__=='__main__':raise SystemExit(main())
