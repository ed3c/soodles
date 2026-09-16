from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
archive=Path(__file__).parent
source=Path('/Users/neon/soodles/.worktrees/soodles-18-0-execute')
root=Path('/Users/neon/soodles')
install=archive/'installed-847f3f8'
assert not install.exists()
install.mkdir()
files=['soodles','soodles.py','issue_admission.py','issue_execution.py','landing.py','policy/runtime.lock.json','.agents/skills/schedule/SKILL.md','.agents/skills/execute/SKILL.md']
manifest={}
for name in files:
    dest=install/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,dest)
    manifest[name]=hashlib.sha256(dest.read_bytes()).hexdigest()
(archive/'installed-source-selection.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'files':manifest,'authority':'external supervisor selection for bounded live seam observation; not candidate self-authorization for landing'},indent=2)+'\n')
issue=json.loads((archive/'selected-issue.json').read_text())
sys.path.insert(0,str(install));from issue_admission import parse_contract,validate_issue
contract=parse_contract(issue['body'])
noodle=Path('/Users/neon/.codex/experiments/noodle82-20260916/noodle')
codex=Path('/Users/neon/.codex/packages/standalone/releases/0.153.4-aarch64-apple-darwin/bin/codex')
extra=['-c','default_permissions="agent-default"','--ephemeral','-c','approval_policy="never"','--add-dir',str(root/'.noodle')]
argv=['exec','--skip-git-repo-check','--json','--model','gpt-5.6-sol',*extra]
task=('This is the admitted bounded physical integration task for Soodles #18. Do not edit source, create commits, or perform provider delivery. '
      'Run exactly the focused control suites from this worktree using Python unittest discovery for test_issue_*.py and test_landing.py, with TMPDIR=/private/tmp and -B. '
      'Read the current GitHub Issue 18 contract. Then inspect the actual admitted Noodle binary event emit --help. '
      'Use that binary yourself to emit exactly one stage_message to your actual NOODLE_SESSION_ID with order_id from NOODLE_ORDER_ID and integer stage_index from NOODLE_STAGE_INDEX. '
      'The supported payload fields are message, blocking, outcome, order_id, stage_index; this schema is read back from the selected Noodle source event/types.go. '
      'Use outcome="blocked", blocking=true, and a truthful message reporting the checks and that full delivery/final acceptance remains with the supervisor. '
      'This is not a completed Issue. Preserve the existing worktree and canonical identity. Exit after emitting; do not ask the parent to fill the outcome. '
      'Admitted Noodle executable: '+str(noodle))
envelope={'schema':1,'repository':'ed3c/soodles','issue':18,'body_sha256':hashlib.sha256(issue['body'].encode()).hexdigest(),'body_updated_at':issue['updated_at'],'owner':contract['owner'],'write_paths':contract['write_paths'],'base_head':'50f41919ead671d69eade1ae5cc66bd1d96e347c','execution':{'control_root':str(root),'worktree':'soodles-18-0-execute','order_id':'soodles-18','stage_index':0,'task':task,'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'carrier':{'platform':'darwin_arm64','noodle':{'path':str(noodle),'sha256':hashlib.sha256(noodle.read_bytes()).hexdigest()},'codex':{'path':str(codex),'sha256':hashlib.sha256(codex.read_bytes()).hexdigest(),'model':'gpt-5.6-sol','argv':argv}}}}
validate_issue(issue,envelope)
envpath=archive/'execution-envelope-847f3f8.json';envpath.write_text(json.dumps(envelope,indent=2)+'\n');pin=hashlib.sha256(envpath.read_bytes()).hexdigest()
(archive/'envelope-pin.txt').write_text(pin+'\n')
wrapperdir=archive/'provider-847f3f8';wrapperdir.mkdir()
prelude='#!'+sys.executable+'\nimport hashlib,os,sys\nfrom pathlib import Path\nroot=Path('+repr(str(install))+')\nmanifest='+repr(manifest)+'\nfor name,digest in manifest.items():\n    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: raise SystemExit("refused: changed installed implementation: "+name)\n'
launcher=archive/'admission-847f3f8'
launcher.write_text(prelude+'if len(sys.argv)!=2 or sys.argv[1] not in ("automatic","supervised"): raise SystemExit("expected automatic or supervised")\nos.execv('+repr(sys.executable)+', ['+repr(sys.executable)+',"-B",str(root/"soodles.py"),"issue",sys.argv[1],'+repr(str(envpath))+','+repr(pin)+'])\n');launcher.chmod(0o755)
wrapper=wrapperdir/'codex'
wrapper.write_text(prelude+'os.execv('+repr(sys.executable)+', ['+repr(sys.executable)+',"-B",str(root/"soodles.py"),"issue","worker",'+repr(str(envpath))+','+repr(pin)+',*sys.argv[1:]])\n');wrapper.chmod(0o755)
adapter=archive/'backlog-847f3f8'
adapter.write_text(prelude+'import json\nsys.path.insert(0,str(root))\nfrom issue_admission import load_external_envelope,validate_issue\nfrom issue_execution import fetch_issue\nenvelope=load_external_envelope('+repr(str(envpath))+','+repr(pin)+','+repr(str(source))+')\nissue=fetch_issue(envelope["issue"])\nif sys.argv[1]=="sync":\n    validate_issue(issue,envelope)\n    print(json.dumps({"id":"soodles-18","title":issue["title"],"status":"open","plan":envelope["execution"]["task"]}))\nelif sys.argv[1]=="done":\n    if len(sys.argv)>2 and sys.argv[2]=="schedule": print("{}")\n    else:\n        assert sys.argv[2:]==["soodles-18"],"unselected backlog item"\n        validate_issue(issue,envelope,completed=True)\n        print(json.dumps({"readback":"closed/completed","issue":18}))\nelse: raise SystemExit("unsupported adapter operation")\n');adapter.chmod(0o755)
config='mode = "supervised"\n[server]\nenabled = false\n[concurrency]\nmax_concurrency = 1\n[routing.defaults]\nprovider = "codex"\nmodel = "gpt-5.6-sol"\n[skills]\npaths = ['+json.dumps(str(install/'.agents/skills'))+']\n[agents.codex]\npath = '+json.dumps(str(wrapperdir))+'\nargs = '+json.dumps(extra)+'\nrequire_typed_outcome = true\n[adapters.backlog.scripts]\nsync = '+json.dumps(str(adapter)+' sync')+'\ndone = '+json.dumps(str(adapter)+' done')+'\n'
assert (root/'.noodle.toml').read_text().startswith('mode = "manual"')
(archive/'previous-noodle.toml').write_text((root/'.noodle.toml').read_text())
config += 'add = '+json.dumps(str(adapter)+' unsupported-add')+'\nedit = '+json.dumps(str(adapter)+' unsupported-edit')+'\n'
(root/'.noodle.toml').write_text(config);(archive/'installed-noodle.toml').write_text(config)
exclude=root/'.git/info/exclude';original=exclude.read_text();(archive/'git-info-exclude-before.txt').write_text(original)
assert '/.noodle/' in original and '/.noodle.toml' in original
(archive/'launcher-selection.json').write_text(json.dumps({'envelope':str(envpath),'sha256':pin,'launcher':str(launcher),'provider':str(wrapper),'wrapper_sha256':hashlib.sha256(wrapper.read_bytes()).hexdigest(),'task_deadline_seconds':180,'side_effect_boundary':'Noodle runtime state and existing admitted worktree; child task does not edit source'},indent=2)+'\n')
print(json.dumps({'install':str(install),'pin':pin,'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'launcher':str(launcher)}))
