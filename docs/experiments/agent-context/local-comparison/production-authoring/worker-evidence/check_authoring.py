from pathlib import Path
import subprocess, hashlib, json, re, posixpath, difflib
ROOT=Path('/Users/neon/.codex/experiments/soodles39-resume-20260917')
REPO=Path('/Users/neon/soodles/.worktrees/soodles-39-0-execute')
BASE='1ff2882891792b50d97529c9ee1a3e76eac1a6e7'
OLD='2e9d51261c80b2c5c120ca6549c759704c615c61'
OLD_BASE='f2bd849b9523134364ca598df72a4e15fc541ab9'
PATHS=['AGENTS.md','README.md','contracts/system-v1.md','contracts/agent-context-design.md','.agents/skills/verify-soodles/SKILL.md']
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args])
def sha(data): return hashlib.sha256(data).hexdigest()
def exists(ref,p): return subprocess.run(['git','-C',str(REPO),'cat-file','-e',ref+':'+p],capture_output=True).returncode==0
def source(ref,p): return git('show',ref+':'+p)
def candidate(p): return (ROOT/'draft'/p).read_bytes() if p in PATHS else source(BASE,p)
def anchors(data):
 out=set()
 for title in re.findall(r'^#{1,6} (.+)$',data.decode(),re.M):
  title=re.sub(r'[^\w\- ]','',title.lower()).replace(' ','-'); out.add(title)
 return out
checks=[]
def check(name,result,details=None):
 checks.append({'name':name,'passed':bool(result),'details':details})
check('actual_head_is_admitted_base',git('rev-parse','HEAD').decode().strip()==BASE)
check('target_checkout_clean',git('status','--porcelain')==b'')
check('exact_five_draft_files',sorted(str(p.relative_to(ROOT/'draft')) for p in (ROOT/'draft').rglob('*') if p.is_file())==sorted(PATHS))
issue=json.loads((ROOT/'issue.json').read_text())
check('admitted_issue_body_hash',sha(issue['body'].encode())=='cf54e51c5af83fa75625abd68e12b68d1bcd90c7938bea4406467a95020b1887')
patch=''
files=[]
for p in PATHS:
 data=candidate(p); before=source(BASE,p) if exists(BASE,p) else b''
 files.append({'path':p,'bytes':len(data),'sha256':sha(data),'base_sha256':sha(before) if before else None,'old_integration_sha256':sha(source(OLD,p))})
 patch+=''.join(difflib.unified_diff(before.decode().splitlines(True),data.decode().splitlines(True),fromfile='a/'+p if before else '/dev/null',tofile='b/'+p))
check('system_executable_requirements_byte_identical',candidate('contracts/system-v1.md').split(b'## RUNTIME.ADMISSION.001',1)[1]==source(BASE,'contracts/system-v1.md').split(b'## RUNTIME.ADMISSION.001',1)[1])
agents=candidate('AGENTS.md').decode(); current=source(BASE,'AGENTS.md').decode()
for start in ['For verification of Noodle itself','For authenticated Issue reads,','Classes describe authority']:
 para=next(x for x in current.split('\n\n') if x.startswith(start))
 check('preserved_root_'+start,para in agents)
skill=candidate('.agents/skills/verify-soodles/SKILL.md').decode(); base_skill=source(BASE,'.agents/skills/verify-soodles/SKILL.md').decode()
for start in ['For P-class behavior/context work,','For landing, consume','Local feature receipts have','P-class comparisons are one mapped feature,','This existing skill was created']:
 para=next(x for x in base_skill.split('\n\n') if x.startswith(start))
 check('preserved_skill_'+start,para in skill)
check('authenticated_read_recipe_retained','[authenticated Issue readback](features/github-read.md)' in skill)
check('skill_frontmatter',skill.startswith('---\nname: verify-soodles\ndescription: ') and skill.splitlines()[3]=='---')
untouched=[]
for p in ['.agents/skills/verify-soodles/features/pclass-context.md','.agents/skills/verify-soodles/scripts/record_context.py','.agents/skills/verify-soodles/features/github-read.md','.agents/skills/verify-noodle/SKILL.md','landing.py','soodles.py','policy/runtime.lock.json']:
 unchanged=(REPO/p).read_bytes()==source(BASE,p)
 check('unchanged_base:'+p,unchanged)
 untouched.append({'path':p,'sha256':sha(source(BASE,p))})
links=[]; external=[]
for p in PATHS:
 for target in re.findall(r'\[[^\]\n]*\]\(([^)\s]+)\)',candidate(p).decode()):
  if '://' in target:
   external.append({'source':p,'target':target,'network_checked':False}); continue
  path,_,anchor=target.partition('#'); resolved=posixpath.normpath(posixpath.join(posixpath.dirname(p),path)) if path else p
  ok=resolved in PATHS or exists(BASE,resolved)
  if ok and anchor: ok=anchor in anchors(candidate(resolved))
  links.append({'source':p,'target':target,'resolved':resolved,'passed':ok})
check('combined_overlay_relative_links_and_anchors',all(x['passed'] for x in links),links)
# Check existing Markdown incoming links to changed files as well.
incoming=[]
for p in git('ls-tree','-r','--name-only',BASE).decode().splitlines():
 if not p.endswith('.md') or p in PATHS: continue
 for target in re.findall(r'\[[^\]\n]*\]\(([^)\s]+)\)',source(BASE,p).decode()):
  if '://' in target: continue
  path,_,anchor=target.partition('#'); resolved=posixpath.normpath(posixpath.join(posixpath.dirname(p),path)) if path else p
  if resolved in PATHS and anchor: incoming.append({'source':p,'target':target,'passed':anchor in anchors(candidate(resolved))})
check('existing_incoming_anchors',all(x['passed'] for x in incoming),incoming)
check('historical_protocol_pinned_object_exists',exists(OLD,'docs/experiments/agent-context/protocol.md'))
(ROOT/'worker-evidence/candidate.patch').write_text(patch)
for a,b,label in [(OLD_BASE,OLD,'old-integration-vs-f2bd849'),(OLD_BASE,BASE,'current-base-vs-f2bd849')]:
 (ROOT/'worker-evidence'/f'{label}.patch').write_bytes(git('diff',a,b,'--',*PATHS))
result=subprocess.run(['git','-C',str(REPO),'apply','--check',str(ROOT/'worker-evidence/candidate.patch')],capture_output=True,text=True)
check('patch_applies_to_current_base_without_writing',result.returncode==0,{'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
result=subprocess.run(['git','-C',str(REPO),'apply','--check','--whitespace=error',str(ROOT/'worker-evidence/candidate.patch')],capture_output=True,text=True)
check('patch_whitespace',result.returncode==0,{'exit_code':result.returncode,'stderr':result.stderr})
report={'scope':'Authoring checks only; no behavioral experiment, canonical acceptance or provider delivery','authorizes_landing':False,'checks':checks,'files':files,'unchanged_base_inputs':untouched,'external_links_not_network_checked':external,'source_issue_found_and_corrected':{'kind':'authoring_missing_link_target','original':'../docs/experiments/agent-context/protocol.md','reason':'Absent from current base plus five-file overlay','correction':'Pinned historical protocol at '+OLD},'passed':all(c['passed'] for c in checks)}
(ROOT/'worker-evidence/authoring-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'relative_links':len(links),'failures':[c for c in checks if not c['passed']]},indent=2))
raise SystemExit(0 if report['passed'] else 1)
