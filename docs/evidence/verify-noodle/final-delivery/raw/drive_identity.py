from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
r=Path(__file__).parent;w=Path('/Users/neon/soodles/.worktrees/soodles-46-0-execute');source=Path('/Users/neon/.codex/experiments/noodle78-delivery-20260916/control');binary=Path('/Users/neon/.codex/experiments/noodle84-20260917/noodle-merged-ca81');out=r/sys.argv[1]
recorder=w/'.agents/skills/verify-soodles/scripts/record_context.py';spec=importlib.util.spec_from_file_location('record_existing',recorder);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
records=[]
def run(label,argv):
 result,stdout,stderr=module.record(out,label,argv);records.append({'label':label,**result});assert result['exit_code']==0,(label,stderr.decode());return stdout.decode()
before=subprocess.check_output(['git','status','--porcelain'],cwd=w,text=True)
run('launch',[str(binary),'--help'])
version=run('doctor-version',[str(binary),'--project-dir',str(w),'version'])
build=run('doctor-build',['go','version','-m',str(binary)])
digest=run('doctor-digest',['python3','-c','import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())',str(binary)]).strip()
head=run('doctor-source-head',['git','-C',str(source),'rev-parse','HEAD']).strip();clean=run('doctor-source-clean',['git','-C',str(source),'status','--porcelain'])
selection=json.loads((r/'observer-selection.json').read_text());assert head==selection['source_commit'] and clean=='' and digest==selection['noodle']['sha256'];assert 'vcs.revision='+head in build and 'vcs.modified=false' in build
rows=run('skills-list',[str(binary),'--project-dir',str(w),'skills','list']);matches=[line.split('\t') for line in rows.splitlines() if line.startswith('verify-noodle\t')];assert len(matches)==1 and matches[0][2]=='true' and Path(matches[0][3]).resolve()==w/'.agents/skills/verify-noodle'
files={str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'.agents/skills/verify-noodle').rglob('*') if p.is_file()};assert len(files)==5
assert subprocess.check_output(['git','status','--porcelain'],cwd=w,text=True)==before
receipt={'feature':'identity-skills','classification':'VERIFIED','candidate_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=w,text=True).strip(),'candidate_status_before_and_after':before,'binary_sha256':digest,'source_head':head,'version':version.strip(),'resolved_skill':matches[0],'file_digests':files,'skill_loading_claim':False,'observations':records,'owned_processes_waited':True,'scratch_directories_created':0,'evidence_survives_cleanup':all((out/x['label']/'result.json').exists() for x in records),'authorizes_landing':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['feature','classification','candidate_head','resolved_skill','evidence_survives_cleanup']}))
