"""Archive actual trial inputs/outputs; never derives a verdict or grants landing."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess
r=Path(__file__).resolve().parent;pub=r/'evidence-publication';dest=pub/'docs/experiments/agent-context/local-comparison'
assert not dest.exists(), 'publication is append-only; use a new archive for changed evidence'
# Staged export is independently audited before publication.
for n in [1,2,4,7,8,9,10]:
 d=r/f'run-{n:02d}'
 assert json.loads((d/'observer-verdict.json').read_text())['verdict']=='TRACE_CONSISTENT'
 assert all(json.loads((d/'native/capture-audit.json').read_text())['checks'].values())
for n in [5,6]:assert all(json.loads((r/f'run-{n:02d}/native/capture-audit.json').read_text())['checks'].values())
dest.mkdir(parents=True)
for p in sorted(r.iterdir()):
 if p.is_file() and p.suffix in ['.json','.py','.log','.md']:
  shutil.copy2(p,dest/p.name)
for name in ['judge','instructions','fixtures','independent-audit']:
 shutil.copytree(r/name,dest/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.lock'))
files=['task.txt','live-issue.json','selection.json','execution-envelope.json','prepare_live.py','run_live.py','read_native.py','cleanup_probe.py','worker-doctor.json','worker-doctor.stderr.log','worker-git-preflight.txt','admission.stdout.json','admission.stderr.log','admission','backlog','transfer-input-receipt.json','failure-and-cleanup.json','cleanup.json','cleanup.stdout.log','cleanup.stderr.log','observer-packet.json','observer-packet-original-locator.json','observer-verdict-original-locator.json','observer-verdict.json','observer-stderr.log','cleanup-final.json','cleanup-retry.json','cleanup-changed-readback.json','postprocess.json','observer-packet-initial.json','observer-verdict-initial.json','observer-packet-initial-locator.json','observer-verdict-initial-locator.json']
for n in range(1,11):
 source=r/f'run-{n:02d}';target=dest/source.name;target.mkdir()
 for name in files:
  p=source/name
  if p.exists():shutil.copy2(p,target/name)
 for name in ['live','native','process-exits','installed','provider','inputs-before','inputs-after','inbox']:
  if (source/name).exists():shutil.copytree(source/name,target/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.lock'))
 for p in source.glob('*.log'):shutil.copy2(p,target/p.name)
 shutil.copy2(source/'control/.noodle.toml',target/'noodle.toml')
 # Preserve exact tested source bytes and identities without the mutable clone's .git.
 subject=target/'source-subject';subject.mkdir()
 tracked=['AGENTS.md','README.md','contracts/system-v1.md','contracts/agent-context-design.md','.agents/skills/execute/SKILL.md','.agents/skills/verify-soodles/SKILL.md','tests/test_landing.py','landing.py','soodles.py','issue_admission.py','issue_execution.py','policy/runtime.lock.json']
 for name in tracked:
  p=source/'control'/name
  if p.exists():q=subject/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source/'control',text=True).strip()
 tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=source/'control',text=True).strip()
 (subject/'identity.json').write_text(json.dumps({'head':head,'tree':tree,'common_code_ref':'1ff2882891792b50d97529c9ee1a3e76eac1a6e7'},indent=2)+'\n')
# Public export keeps original line numbers and every task/tool/result/model/exit
# record. Platform instructions and encrypted internal reasoning are not published.
redactions=[]
for p in sorted(dest.glob('run-*/native/rollout.jsonl')):
 original=p.read_bytes();out=[];changes=[]
 for lineno,line in enumerate(original.splitlines(keepends=True),1):
  event=json.loads(line);payload=event.get('payload',{});changed=[]
  if event.get('type')=='session_meta' and 'base_instructions' in payload:
   payload['base_instructions']={'redacted':'platform instructions'};changed.append('base_instructions')
  if event.get('type')=='world_state':
   event['payload']={'redacted':'platform context assembly'};changed.append('world_state')
  if event.get('type')=='response_item' and payload.get('type')=='message' and payload.get('role') in ['developer','system']:
   payload['content']=[{'type':'input_text','text':'[Platform instructions omitted from public export]'}];changed.append('platform_message')
  if payload.get('type')=='reasoning':
   for key in ['encrypted_content','content','summary']:
    if key in payload:payload[key]=None if key=='encrypted_content' else []
   changed.append('internal_reasoning')
  if changed:
   exported=(json.dumps(event,ensure_ascii=False,separators=(',',':'))+'\n').encode();changes.append({'line':lineno,'fields':changed,'original_line_sha256':hashlib.sha256(line).hexdigest(),'export_line_sha256':hashlib.sha256(exported).hexdigest()});out.append(exported)
  else:out.append(line)
 data=b''.join(out);p.write_bytes(data)
 redactions.append({'path':str(p.relative_to(dest)),'original_sha256':hashlib.sha256(original).hexdigest(),'export_sha256':hashlib.sha256(data).hexdigest(),'unchanged_tool_and_task_lines':True,'line_count_preserved':len(out)==len(original.splitlines()),'changes':changes})
(dest/'public-export-redactions.json').write_text(json.dumps({'scope':'Public native rollouts are explicitly redacted exports. Original local raw files remain unchanged. No tool request/result, task user prompt, final answer, native turn/model, typed outcome, or actual child exit was removed or altered.','files':redactions},indent=2)+'\n')
patterns=[r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{30,}',r'sk-(?:proj-)?[A-Za-z0-9_-]{30,}',r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'];manifest={}
for p in sorted(dest.rglob('*')):
 if not p.is_file():continue
 data=p.read_bytes();s=data.decode()
 if any(re.search(pattern,s) for pattern in patterns):raise RuntimeError('credential-shaped material in '+str(p.relative_to(dest)))
 manifest[str(p.relative_to(dest))]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'files':len(manifest)+1,'bytes':sum(x['bytes'] for x in manifest.values())}))
