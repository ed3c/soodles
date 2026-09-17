from pathlib import Path
import concurrent.futures,subprocess,hashlib,json,shutil,os
r=Path(__file__).resolve().parent
base='1ff2882891792b50d97529c9ee1a3e76eac1a6e7'
noodle='/Users/neon/.codex/experiments/noodle84-20260917/noodle-merged-ca81'
codex='/Users/neon/.codex/packages/standalone/releases/0.153.4-aarch64-apple-darwin/bin/codex'
neutral='''---
name: execute
description: Perform the supervisor-admitted bounded independent review using supplied inputs.
schedule: Only the admitted experimental order.
---

# Bounded independent review

The installed entry already validates the real current Issue and execution
identity before this Agent starts. Follow the bounded task in the stage prompt.
Read the assigned local AGENTS.md, then the provided task/input packet and nearest
needed source/control. For this experiment do not read Issue 39, experiment
reports/judges, other sessions or the operator's conversation. Do not modify
source or live provider state or launch another model. Simulated provider inputs
are local fixtures; their historical requests must never be sent to GitHub.

Use the existing owner and its current output to decide the supported conclusion.
If a producer task explicitly requests a handoff artifact, write it only to the
supplied inbox path. Otherwise report the scoped result in the final response.
At the end emit your own typed stage_message through the supplied Noodle binary
using actual NOODLE_SESSION_ID, NOODLE_ORDER_ID and integer NOODLE_STAGE_INDEX.
Read event emit --help first; fields are message, blocking, outcome, order_id,
stage_index. The experiment does not deliver the production Issue: use blocked
with blocking=true for that handoff, accurately describing your observed result.
No parent fills the event and a stage outcome is not Issue resolution.
'''
assert (r/'neutral-execute-SKILL.md').read_text()==neutral
cases=json.loads((r/'fixtures/cases.json').read_text());pending=json.loads((r/'fixtures/pending-input.json').read_text())
assert pending['checkpoint']['writes_offered']==['merge']
assignments=[('run-09','baseline','unknown-write'),('run-10','treatment','unknown-write')]
common_prefix='''This is a bounded independent read-only review. The launcher has already validated the real Issue contract. Use the installed execute skill and read local AGENTS.md. Do not fetch Issue 39, experiment reports, the judge, other sessions or the operator archive. The task inputs are in the inbox directory alongside NOODLE_PROJECT_DIR (Path(os.environ['NOODLE_PROJECT_DIR']).parent / 'inbox'). Read task-input.json there. Read-only command execution is authorized. For mutable fixtures, inspect the actual supplied checkpoint/provider files and invoke the current local owner entry, not merely the historical owner output. The local owner entry is python3 -B ./soodles.py landing; use its help for arguments. All provider subjects in fixture files are simulated, except the explicitly supplied common runtime readback. Do not send fixture requests to GitHub.\n\n'''
footer='''\n\nFinish with the scoped conclusion and your own typed blocked stage handoff as the execute skill describes. The admitted Noodle binary is /Users/neon/.codex/experiments/noodle84-20260917/noodle-merged-ca81. Event schema locator: https://github.com/ed3c/noodle/blob/ca81f942f478e8e4afcbbce6ca69640867efe753/event/types.go . Do not edit repository source or create extra worktrees/sessions.'''
old=Path('/Users/neon/.codex/experiments/soodles39-exit-recorder-v2-20260917')
prep=(old/'prepare_live.py').read_text().replace("'issue_execution.py',", "'issue_execution.py','github_reader.py',").replace('/Users/neon/.codex/experiments/noodle82-20260916/noodle','/Users/neon/.codex/experiments/noodle84-20260917/noodle-merged-ca81');prep=prep.replace("shutil.copy2(root/name,p);manifest[name]", "shutil.copy2((Path("+repr(str(r/'judge/record_process.py'))+") if name.endswith('record_process.py') else root/name),p);manifest[name]")
start=prep.index("task='");end=prep.index('\nhead=',start);prep=prep[:start]+"task=(r/'task.txt').read_text()"+prep[end:]
prep=prep.replace("'--add-dir',str(root/'.noodle')]","'--add-dir',str(root/'.noodle'),'--add-dir',str(r/'inbox')]")
prep=prep.replace("'deadline_seconds':180","'deadline_seconds':300").replace('e4b4a8487855b75ef2d47087019bb52c4d5ffd6c',base)
manifest=[]
for label,arm,case in assignments:
 out=r/label;out.mkdir();root=out/'control'
 subprocess.run(['git','clone','--quiet','--no-hardlinks','--single-branch','--branch','main','/Users/neon/soodles',str(root)],check=True)
 subprocess.run(['git','checkout','--quiet','--detach',base],cwd=root,check=True)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==base
 subprocess.run(['git','remote','set-url','origin','git@github.com:ed3c/soodles.git'],cwd=root,check=True)
 if arm=='treatment':
  for p in (r/'instructions/treatment').rglob('*'):
   if p.is_file():q=root/p.relative_to(r/'instructions/treatment');q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
 (root/'.agents/skills/execute/SKILL.md').write_text(neutral)
 subprocess.run(['git','add','AGENTS.md','README.md','contracts','.agents/skills'],cwd=root,check=True)
 subprocess.run(['git','-c','user.name=ed3c','-c','user.email=30064024+ed3c@users.noreply.github.com','commit','-q','-m','Bind isolated instruction and neutral task inputs for a bounded experiment'],cwd=root,check=True)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
 inbox=out/'inbox';inbox.mkdir()
 for name in ['identity-input.json','runtime-readback.json'] :shutil.copy2(r/'fixtures'/name,inbox/name)
 (inbox/'checkpoint.json').write_text(json.dumps(pending['checkpoint'],sort_keys=True,indent=2)+'\n')
 (inbox/'provider.json').write_text(json.dumps(pending['provider_snapshot'],sort_keys=True,indent=2)+'\n')
 shutil.copy2(r/'fixtures/handoff-seed.json',inbox/'historical-seed.json')
 inputs={'repository':'ed3c/soodles','assigned_instruction_ref':json.loads((r/'instruction-selection.json').read_text())[arm]['ref'],'common_code_ref':base,'owner_entry':['python3','-B','./soodles.py','landing'],'identity_output':'identity-input.json','runtime_readback':'runtime-readback.json','checkpoint':'checkpoint.json','provider':'provider.json','historical_material':'historical-seed.json'}
 if case=='fresh-transfer':inputs['handoff']='handoff.json'
 if case=='producer':
  prompt='Prepare a concise handoff for a different fresh reviewer continuing this fixture review. Inspect the current checkpoint/provider through the existing owner. Persist your handoff as inbox/handoff.json (in the supplied inbox, not the repository), including the actual source/checkpoint identity, observations and supported continuation. Keep any historical request clearly distinguished from current owner output. Do not claim the later consumer has run.'
 else:prompt=next(x['prompt'] for x in cases['cases'] if x['id']==case)
 (inbox/'task-input.json').write_text(json.dumps(inputs,indent=2)+'\n');(out/'task.txt').write_text(common_prefix+prompt+'\n\n'+'Invoke the local owner using the actual supplied inbox/checkpoint.json path (not a copied checkpoint); preserve and report its SHA-256 before and after invocation. The offered-state owner is authorized only to inspect this supplied fixture.'+footer+'\n')
 shutil.copy2(r/'live-issue.json',out/'live-issue.json');(out/'prepare_live.py').write_text(prep)
 subprocess.run(['python3',str(out/'prepare_live.py')],cwd=out,check=True,stdout=(out/'prepare.stdout.log').open('w'),stderr=(out/'prepare.stderr.log').open('w'))
 subprocess.run([noodle,'start','--once'],cwd=root,check=True,stdout=(out/'initialize.stdout.log').open('w'),stderr=(out/'initialize.stderr.log').open('w'))
 subprocess.run([str(out/'admission'),'supervised'],cwd=root,check=True,stdout=(out/'admission.stdout.json').open('w'),stderr=(out/'admission.stderr.log').open('w'))
 subprocess.run([noodle,'worktree','create','soodles-39-0-execute'],cwd=root,check=True,stdout=(out/'worktree-create.stdout.log').open('w'),stderr=(out/'worktree-create.stderr.log').open('w'))
 work=root/'.worktrees/soodles-39-0-execute'
 git=subprocess.run(['git','-C',str(work),'rev-parse','--show-toplevel','--is-inside-work-tree','HEAD'],capture_output=True,text=True,check=True);(out/'worker-git-preflight.txt').write_text(git.stdout)
 # Preserve exact fixture bytes outside consumer-visible inbox before any Agent.
 shutil.copytree(inbox,out/'inputs-before')
 run=(old/'run_live.py').read_text().replace('/Users/neon/.codex/experiments/noodle82-20260916/noodle','/Users/neon/.codex/experiments/noodle84-20260917/noodle-merged-ca81').replace("r/'judge-selection.json'",repr(str(r/'judge-selection.json'))).replace("(r/'judge'/name)","(Path("+repr(str(r/'judge'))+")/name)")
 run=run.replace("selection=json.loads(("+repr(str(r/'judge-selection.json'))+").read_text())","selection=json.loads(Path("+repr(str(r/'judge-selection.json'))+").read_text())")
 run=run.replace('180','300').replace("'PYTHONDONTWRITEBYTECODE':'1'","'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':'/private/tmp'");(out/'run_live.py').write_text(run)
 for name in ['read_native.py','cleanup_probe.py']:(out/name).write_text((old/name).read_text().replace('/Users/neon/.codex/experiments/noodle82-20260916/noodle','/Users/neon/.codex/experiments/noodle84-20260917/noodle-merged-ca81'))
 manifest.append({'label':label,'arm':arm,'case':case,'source_head':head,'task_sha256':hashlib.sha256((out/'task.txt').read_bytes()).hexdigest(),'checkpoint_sha256':hashlib.sha256((inbox/'checkpoint.json').read_bytes()).hexdigest(),'provider_sha256':hashlib.sha256((inbox/'provider.json').read_bytes()).hexdigest()})
(r/'additional-trial-selection.json').write_text(json.dumps({'assignments':manifest,'config_id':'macos-codex01534-astra-high-native-recorder-neutral-main46-auth-v1','deadline_seconds':300,'authorizes_landing':False},indent=2)+'\n')

def doctor(item):
 out=r/item['label'];work=out/'control/.worktrees/soodles-39-0-execute'
 with (out/'worker-doctor.json').open('w') as stdout,(out/'worker-doctor.stderr.log').open('w') as stderr:
  p=subprocess.run([codex,'-C',str(work),'doctor','--json'],stdout=stdout,stderr=stderr,timeout=80)
 d=json.loads((out/'worker-doctor.json').read_text());assert d['checks']['config.load']['details']['cwd']==str(work);assert d['checks']['git.environment']['details']['repo root']==str(work) and d['checks']['git.environment']['details']['repo detected']=='true'
 failed={k for k,v in d['checks'].items() if v['status']=='fail'};assert failed<={'terminal.env'},failed
 return {'label':item['label'],'doctor_exit':p.returncode,'failed_checks':sorted(failed)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(doctor,manifest))
(r/'additional-preflight.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps({'prepared':len(manifest),'checks':checks}))
