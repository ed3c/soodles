from pathlib import Path
import json,hashlib,shutil,subprocess,sys
r=Path(__file__).parent;root=r/'control';install=r/'installed';install.mkdir()
files=['soodles','soodles.py','issue_admission.py','issue_execution.py','landing.py','policy/runtime.lock.json','.agents/skills/schedule/SKILL.md','.agents/skills/execute/SKILL.md','docs/experiments/agent-context/local/record_process.py']
manifest={}
for name in files:
 p=install/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2((Path('/Users/neon/.codex/experiments/soodles39-completion-20260917/judge/record_process.py') if name.endswith('record_process.py') else root/name),p);manifest[name]=hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(install));from issue_admission import parse_contract,validate_issue
issue=json.loads((r/'live-issue.json').read_text());c=parse_contract(issue['body'])
noodle=Path('/Users/neon/.codex/experiments/noodle82-20260916/noodle');codex=Path('/Users/neon/.codex/packages/standalone/releases/0.153.4-aarch64-apple-darwin/bin/codex')
extra=['-c','default_permissions="agent-default"','-c','approval_policy="never"','-c','model_reasoning_effort="high"','--add-dir',str(root/'.noodle'),'--add-dir',str(r/'inbox')]
argv=['exec','--skip-git-repo-check','--json','--model','gpt-6-astra',*extra]
task=(r/'task.txt').read_text()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
envelope={'schema':1,'repository':'ed3c/soodles','issue':39,'body_sha256':hashlib.sha256(issue['body'].encode()).hexdigest(),'body_updated_at':issue['updated_at'],'owner':c['owner'],'write_paths':c['write_paths'],'base_head':'e4b4a8487855b75ef2d47087019bb52c4d5ffd6c','execution':{'control_root':str(root),'worktree':'soodles-39-0-execute','order_id':'soodles-39','stage_index':0,'task':task,'source_head':head,'carrier':{'platform':'darwin_arm64','noodle':{'path':str(noodle),'sha256':hashlib.sha256(noodle.read_bytes()).hexdigest()},'codex':{'path':str(codex),'sha256':hashlib.sha256(codex.read_bytes()).hexdigest(),'model':'gpt-6-astra','argv':argv}}}}
validate_issue(issue,envelope)
p=r/'execution-envelope.json';p.write_text(json.dumps(envelope,indent=2)+'\n');pin=hashlib.sha256(p.read_bytes()).hexdigest()
prelude='#!'+sys.executable+'\nimport hashlib,os,sys\nfrom pathlib import Path\nroot=Path('+repr(str(install))+')\nmanifest='+repr(manifest)+'\nfor name,digest in manifest.items():\n    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: raise SystemExit("changed installed bytes: "+name)\n'
launcher=r/'admission';launcher.write_text(prelude+'if sys.argv[1:] not in (["automatic"],["supervised"]): raise SystemExit("expected route")\nos.execv('+repr(sys.executable)+',['+repr(sys.executable)+',"-B",str(root/"soodles.py"),"issue",sys.argv[1],'+repr(str(p))+','+repr(pin)+'])\n');launcher.chmod(0o755)
provider=r/'provider';provider.mkdir();wrapper=provider/'codex';wrapper.write_text(prelude+'os.execv('+repr(sys.executable)+',['+repr(sys.executable)+',"-B",str(root/"docs/experiments/agent-context/local/record_process.py"),'+repr(str(r/'process-exits'))+'+"/"+os.environ["NOODLE_SESSION_ID"],"--",'+repr(sys.executable)+',"-B",str(root/"soodles.py"),"issue","worker",'+repr(str(p))+','+repr(pin)+',*sys.argv[1:]])\n');wrapper.chmod(0o755)
adapter=r/'backlog';adapter.write_text(prelude+'import json\nsys.path.insert(0,str(root))\nfrom issue_admission import load_external_envelope,validate_issue\nfrom issue_execution import fetch_issue\ne=load_external_envelope('+repr(str(p))+','+repr(pin)+','+repr(str(root))+')\ni=fetch_issue(39)\nif sys.argv[1:]==["sync"]:\n    validate_issue(i,e);print(json.dumps({"id":"soodles-39","title":i["title"],"status":"open","plan":e["execution"]["task"]}))\nelse: raise SystemExit("capability adapter cannot mark production Issue done")\n');adapter.chmod(0o755)
config='mode = "manual"\n[server]\nenabled=false\n[concurrency]\nmax_concurrency=1\n[routing.defaults]\nprovider="codex"\nmodel="gpt-6-astra"\n[skills]\npaths=['+json.dumps(str(install/'.agents/skills'))+']\n[agents.codex]\npath='+json.dumps(str(provider))+'\nargs='+json.dumps(extra)+'\nrequire_typed_outcome=true\n[adapters.backlog.scripts]\nsync='+json.dumps(str(adapter)+' sync')+'\n'
for name in ['add','edit','done']:config+=name+'='+json.dumps(str(adapter)+' '+name)+'\n'
(root/'.noodle.toml').write_text(config)
with (root/'.git/info/exclude').open('a') as f:f.write('\n/.noodle/\n/.noodle.toml\n')
(r/'selection.json').write_text(json.dumps({'head':head,'install':manifest,'envelope_sha256':pin,'new_carrier':'local_macos_noodle_codex_exec','full_cases_authorized_after_capability_only':True,'deadline_seconds':300,'source_editing_worktree_is_separate':True},indent=2)+'\n')
print(json.dumps({'head':head,'envelope_sha256':pin,'control_root':str(root)}))
