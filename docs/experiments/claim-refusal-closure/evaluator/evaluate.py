#!/usr/bin/env python3
"""Fixed external oracle. No candidate test imports or model-based verdicts."""
import argparse, copy, hashlib, json, pathlib, subprocess, sys, time
P=pathlib.Path; HERE=P(__file__).resolve().parent
def save(p,v): p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def assess(r,kind):
    z=r['result']; checks={'non_authorizing':z.get('authorizes_landing') is False,'same_entry':z.get('next',{}).get('argv')==r['same_command'],'no_provider_writes':r['provider']=={'create_calls':0,'merge_calls':0,'issue_state':'open'}}
    if kind.startswith('refusal'):
        checks.update(named_owner=z.get('next',{}).get('owner')=='Noodle',named_prerequisite=z.get('next',{}).get('required')==['fresh_noodle_claim'],known_identity=z.get('next',{}).get('known')=={'control_root':r['after']['envelope']['execution']['control_root'],'order_id':r['after']['envelope']['execution']['order_id'],'subject':'ed3c/soodles#131'})
        checks.update(structured_refusal=z.get('status')=='refused' and z.get('next',{}).get('kind')=='input',single_claim=len(r['claim_processes'])==1,no_sleep=r['sleeps']==[],no_accept=r['counts']['accept']==0,no_publish=r['counts']['publish']==0,no_claim_artifact='claim' not in r['after'],no_acceptance_artifact='acceptance' not in r['after'],execution_preserved=r['after']['state']['phase']=='execution',nonzero_observed=all(x['exit']!=0 for x in r['claim_processes']))
    elif kind=='running':
        checks.update(legal_pending=z.get('status')=='pending' and z.get('waiting_on')=='Noodle',no_claim=r['claim_processes']==[],no_accept=r['counts']['accept']==0,no_publish=r['counts']['publish']==0,execution_preserved=r['after']['state']['phase']=='execution')
    else:
        checks.update(ci_boundary=z.get('status')=='pending' and z.get('waiting_on')=='GitHub Actions',single_claim=len(r['claim_processes'])==1,zero_exit=all(x['exit']==0 for x in r['claim_processes']),accepted_once=r['counts']['accept']==1,published_once=r['counts']['publish']==1,ci_state=r['after']['state']['phase']=='ci',claim_identity=r['after']['claim']['head']=='b'*40 and r['after']['claim']['tree']=='c'*40)
    return {'pass':all(checks.values()),'checks':checks}
def main():
    p=argparse.ArgumentParser(); p.add_argument('source'); p.add_argument('output'); a=p.parse_args(); source=P(a.source).resolve(); out=P(a.output).resolve(); out.mkdir(parents=True,exist_ok=False)
    reports={}; verdicts={}; processes=[]
    def run(label,mode,session,timeout):
        cmd=[sys.executable,str(HERE/'worker.py'),str(source),str(out/session),mode,'--timeout',str(timeout)]
        started=time.monotonic(); result=subprocess.run(cmd,capture_output=True,text=True,timeout=60,env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'})
        (out/(label+'.stdout')).write_text(result.stdout); (out/(label+'.stderr')).write_text(result.stderr)
        processes.append({'label':label,'argv':cmd,'exit':result.returncode,'elapsed_seconds':time.monotonic()-started})
        if result.returncode: raise RuntimeError(label+': '+result.stderr)
        r=json.loads(result.stdout); reports[label]=r; verdicts[label]=assess(r,mode); save(out/(label+'.json'),r); return r
    run('refusal','refusal','refusal-state',3)
    run('refusal75','refusal75','refusal75-state',3)
    run('running','running','running-state',3)
    run('success','success','success-state',0)
    first=run('resume_initial','refusal','resume-state',3)
    second=run('resume_running','running','resume-state',0)
    third=run('resume_success','success','resume-state',0)
    stable=lambda field:len({json.dumps(r[field],sort_keys=True) for r in (first,second,third)})==1
    resume={'same_authorization':stable('authorization_sha256') and stable('authorization_path'),'same_reentry':stable('same_command'),'state_readback':second['before']['state']==first['after']['state'] and third['before']['state']==second['after']['state'],'envelope_identity':second['after']['state']['envelope_sha256']==first['after']['state']['envelope_sha256']==third['after']['state']['envelope_sha256']}
    verdicts['resume_identity']={'pass':all(resume.values()),'checks':resume}
    # Planted controls test evaluator sensitivity; never relabel as historical defects.
    planted=copy.deepcopy(reports['success']); planted['counts']['publish']=2
    planted2=copy.deepcopy(reports['running']); planted2['claim_processes']=[{'exit':2}]
    sensitivity={'duplicate_publish_rejected':not assess(planted,'success')['pass'],'claim_while_running_rejected':not assess(planted2,'running')['pass']}
    summary={'source':str(source),'source_issue_atom_sha256':hashlib.sha256((source/'issue_atom.py').read_bytes()).hexdigest(),'decision':'PASS' if all(x['pass'] for x in verdicts.values()) and all(sensitivity.values()) else 'FAIL','verdicts':verdicts,'sensitivity':sensitivity,'processes':processes,'authorizes_landing':False,'scope':'external local deterministic discriminator; fixture provider; not Linux acceptance or production runtime'}
    save(out/'summary.json',summary); print(json.dumps(summary,sort_keys=True)); return 0 if summary['decision']=='PASS' else 1
if __name__=='__main__': sys.exit(main())
