#!/usr/bin/env python3
"""External actual-process controls for preparation publication. No candidate imports."""
import hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
FACTORY=Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/fixture-public/workspace.py')
spec=importlib.util.spec_from_file_location('factory',FACTORY);factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(root):return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def main():
    source=Path(sys.argv[1]).resolve();destination=Path(sys.argv[2]).resolve();destination.mkdir()
    results=[];begun=time.monotonic()
    for case in ('normal','before_receipt_write','after_receipt_write','after_publication','foreign_empty','foreign_symlink','changed_selection','missing_authorization','changed_receipt','changed_binding','legacy_without_binding','stale_head_downstream','missing_capability_downstream'):
        root=destination/case;root.mkdir();work=root/'workspace';factory.create(source,'soodles-work-1',work)
        facts=json.loads((work/'workspace.json').read_text());sel=facts['selection'];control=Path(facts['control_root']);out=Path(sel['external_output'])
        env=dict(os.environ)
        for key in tuple(env):
            if key.startswith(('NOODLE_','NOODLES_','SOODLES_','GH_','GITHUB_')):env.pop(key,None)
        env.update(facts['host']['environment'])
        argv=[str(Path(sys.executable).resolve()),'-B',str(control/'supervisor-admission'),'authorize',sel['path'],sel['sha256'],str(out)]
        observations=[]
        def run(cmd,label,environment=env):
            start=time.monotonic();p=subprocess.run(cmd,cwd=control,env=environment,capture_output=True,timeout=45)
            (root/(label+'.stdout')).write_bytes(p.stdout);(root/(label+'.stderr')).write_bytes(p.stderr)
            observation={'argv':cmd,'exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':sha(root/(label+'.stdout')),'stderr_sha256':sha(root/(label+'.stderr'))}
            observations.append(observation)
            try:value=json.loads(p.stdout)
            except (ValueError,UnicodeError):value={}
            return p,value
        checks={}
        if case in ('foreign_empty','foreign_symlink'):
            if case=='foreign_empty':out.mkdir()
            else:
                foreign=root/'foreign';foreign.mkdir();(foreign/'marker').write_text('preserve\n');out.symlink_to(foreign,target_is_directory=True)
            prior=out.lstat().st_ino;before=inventory(work);p,value=run(argv,'refusal')
            checks.update(refused=p.returncode==1 and value.get('status')=='refused',foreign_preserved=inventory(work)==before and out.lstat().st_ino==prior)
        else:
            fault=case if case in ('before_receipt_write','after_receipt_write','after_publication') else None
            if fault:
                event=root/'fault.json';cmd=[argv[0],'-B',str(BASE/'private/fault.py'),str(control),sel['path'],sel['sha256'],str(out),fault,str(event)]
                p,value=run(cmd,'fault');checks['actual_process_kill']=p.returncode==-9 and event.is_file()
                checks['atomic_visible_state']=((out/'authorization.json').is_file() and (out/'prepared.json').is_file() and (out/'selection-binding.json').is_file()) if fault=='after_publication' else not out.exists()
                before=inventory(out) if out.exists() else {};p,value=run(argv,'continuation')
                checks['recovered_prepared']=p.returncode==0 and value.get('status')=='prepared'
                checks['published_identity_preserved']=not before or inventory(out)==before
            else:p,value=run(argv,'first');checks['initial_prepared']=p.returncode==0 and value.get('status')=='prepared'
            auth=out/'authorization.json';receipt=out/'prepared.json';binding=out/'selection-binding.json'
            if case in ('changed_selection','missing_authorization','changed_receipt','changed_binding','legacy_without_binding'):
                if case=='changed_selection':
                    f=Path(sel['path']);v=json.loads(f.read_text());v['task']+=' Different selected work.';save(f,v);argv[-2]=sha(f)
                elif case=='missing_authorization':auth.unlink()
                elif case=='changed_receipt':
                    v=json.loads(receipt.read_text());v['next']['argv'][-1]+='.foreign';save(receipt,v)
                elif case=='changed_binding':
                    if binding.exists():
                        v=json.loads(binding.read_text());v['selection_sha256']='0'*64;save(binding,v)
                    else:checks['binding_present']=False
                else:
                    if binding.exists():binding.unlink()
                before=inventory(work);p,v=run(argv,'refusal');checks.update(refused=p.returncode==1 and v.get('status')=='refused',refusal_preserved=inventory(work)==before)
            elif value.get('status')=='prepared' and auth.is_file():
                initial_hash=sha(auth);before=inventory(out);p,again=run(argv,'readback')
                checks.update(readback_exact=p.returncode==0 and again==value,readback_no_mutation=inventory(out)==before)
                if case in ('stale_head_downstream','missing_capability_downstream'):
                    if case=='stale_head_downstream':
                        (control/'work-item.txt').write_text('new head after preparation\n');factory.git(control,'add','work-item.txt');factory.git(control,'commit','-m','Move fixture head after preparation')
                        p,current=run(argv,'advanced-readback');checks['readback_does_not_reauthorize']=p.returncode==0 and current==value and sha(auth)==initial_hash
                    next_action=value['next'];runtime_env={**env,**next_action['environment']};p,current=run(next_action['argv'],'downstream',runtime_env)
                    field='git.head' if case=='stale_head_downstream' else 'provider_credential_profile.path'
                    checks['current_downstream_refusal']=p.returncode==1 and current.get('status')=='refused' and current.get('invalid',{}).get('field')==field
                    checks['identity_unchanged_downstream']=sha(auth)==initial_hash
            checks['no_lifecycle_checkpoint']=not (out/'authorization.json.state.json').exists() and not (out/'authorization.json.d').exists()
        value={'case':case,'checks':checks,'pass':all(checks.values()),'processes':observations,'post_inventory':inventory(work)}
        save(root/'observation.json',value);results.append(value)
    summary={'scope':'actual process/file/local-owner controls; no provider transport','source':{'path':str(source),'head':factory.git(source,'rev-parse','HEAD')},'elapsed_seconds':time.monotonic()-begun,'cases':results,'pass':all(c['pass'] for c in results)}
    save(destination/'results.json',summary)
    print(json.dumps({'output':str(destination),'pass':summary['pass'],'failures':{c['case']:[k for k,v in c['checks'].items() if not v] for c in results if not c['pass']}},indent=2))
    return int(not summary['pass'])
if __name__=='__main__':raise SystemExit(main())
