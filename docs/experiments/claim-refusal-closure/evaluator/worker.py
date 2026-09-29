#!/usr/bin/env python3
"""External bounded process observer. Candidate supplies implementation, never judge."""
import argparse, contextlib, hashlib, importlib.util, json, os, pathlib, socket, subprocess, sys, tempfile, time
from unittest.mock import patch
P = pathlib.Path
HERE = P(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('source'); p.add_argument('session'); p.add_argument('mode', choices=['refusal','refusal75','running','success']); p.add_argument('--timeout',type=int,default=3); a=p.parse_args()
source=P(a.source).resolve(); session=P(a.session).resolve(); session.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(source)); import issue_atom as atom
spec=importlib.util.spec_from_file_location('frozen_fixture',HERE/'frozen/test_issue_atom.py'); fixture=importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
def save(path,value): path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
telemetry=[]; original_run=subprocess.run
allowed_git={'init','config','add','commit','remote','rev-parse','status','diff','show','ls-files','check-ignore','cat-file','log','merge-base'}
def guarded_run(argv,*args,**kw):
    argv=[str(x) for x in argv]
    if argv[0]=='git':
        git_args=[x for x in argv[1:] if x!='--no-pager']
        if not git_args or git_args[0] not in allowed_git: raise RuntimeError('forbidden git operation: '+repr(argv))
        if argv[1]=='remote' and argv[2:3]!=['add'] and argv[2:3]!=['get-url']: raise RuntimeError('forbidden remote operation')
    elif argv[0] != str(case.binary): raise RuntimeError('forbidden subprocess: '+repr(argv))
    start=time.monotonic(); result=original_run(argv,*args,**kw)
    telemetry.append({'argv':argv,'cwd':str(kw.get('cwd','')),'exit':result.returncode,'stdout':result.stdout.decode(errors='replace') if isinstance(result.stdout,bytes) else result.stdout,'stderr':result.stderr.decode(errors='replace') if isinstance(result.stderr,bytes) else result.stderr,'elapsed_seconds':time.monotonic()-start})
    return result
case=fixture.IssueAtomTests()
meta=session/'fixture.json'
if not meta.exists():
    tempfile.tempdir=str(session)
    case.setUp(); case.temp._finalizer.detach()
    carrier='''#!'''+sys.executable+'''\nimport json,pathlib,sys\np=pathlib.Path(__file__).parent\nm=json.loads((p/'mode.json').read_text())\nif m['mode']=='success':\n print(json.dumps(m['claim']))\nelse:\n print('fixture claim refuses canonical readiness',file=sys.stderr)\n sys.exit(75 if m['mode']=='refusal75' else 2)\n'''
    case.binary.write_text(carrier); case.binary.chmod(0o755)
    new_digest=digest(case.binary); case.authorization['noodle']['sha256']=new_digest; case.authorization['carrier']['codex']['sha256']=new_digest
    save(case.path,case.authorization); case.digest=digest(case.path); case.env['SOODLES_AUTHORIZATION_SHA256']=case.digest
    save(meta,{'outer':str(case.outer),'authorization_path':str(case.path),'env':case.env})
else:
    m=json.loads(meta.read_text()); case.outer=P(m['outer']); case.root=case.outer/'project'; case.binary=case.outer/'carrier'; case.path=P(m['authorization_path']); case.env=m['env']; case.authorization=json.loads(case.path.read_text()); case.digest=digest(case.path); case.base=case.authorization['base_head']
claim={'worktree_path':str(case.root),'worktree_name':atom.issue_admission.scoped_order_id(131,case.root)+'-0-execute','head':'b'*40,'tree':'c'*40,'base_head':case.base}
save(case.outer/'mode.json',{'mode':a.mode,'claim':claim})
provider=fixture.Provider(); case.ready_issue(provider)
paths=atom.artifact_paths(case.path)
before={k:json.loads(v.read_text()) for k,v in paths.items() if v.is_file() and v.suffix=='.json'}
counts={'accept':0,'publish':0,'supervised':0}; sleeps=[]; now=[0]
def supervised(*args,**kwargs):
    counts['supervised']+=1
    return {'action':'running'} if a.mode=='running' else {'published':True}
def accepted(auth,cl,out):
    counts['accept']+=1
    value={'repository':'ed3c/soodles','scope':'candidate runtime acceptance','candidate':{'head':cl['head'],'tree':cl['tree']},'authorizes_landing':False}
    atom.save_json(out,value,fresh=True); return value
def publish(*args,**kwargs):
    counts['publish']+=1
    return {'pr':{'number':132,'url':'https://github.com/ed3c/soodles/pull/132'},'branch':'soodles/issue-131-'+('b'*12),'head':'b'*40,'tree':'c'*40,'authorizes_landing':False}
def sleep(n): sleeps.append(n); now[0]+=n
def deny(*args,**kwargs): raise RuntimeError('live side effect forbidden by external fixture')
with contextlib.ExitStack() as s:
    for obj,name,replacement in [(atom.subprocess,'run',guarded_run),(atom.issue_execution,'supervised',supervised),(atom,'_accept',accepted),(atom.candidate_publication,'publish',publish),(atom,'select_run',lambda *x:(None,None)),(socket,'create_connection',deny),(socket.socket,'connect',deny),(atom,'ensure_noodle',deny),(atom,'bootstrap_noodle',deny),(atom,'GitHubProvider',deny),(atom.LandingOwner,'start',deny),(atom.LandingOwner,'dispatch',deny)]: s.enter_context(patch.object(obj,name,replacement))
    try: result=atom.drive(case.path,timeout=a.timeout,interval=1,sleep=sleep,clock=lambda:now[0],environ=case.env,provider=provider)
    except atom.AtomRefusal as e: result=atom.refusal_output(e,case.path)
claims=[x for x in telemetry if x['argv'][0]==str(case.binary)]
after={k:json.loads(v.read_text()) for k,v in paths.items() if v.is_file() and v.suffix=='.json'}
report={'mode':a.mode,'result':result,'counts':counts,'sleeps':sleeps,'claim_processes':claims,'subprocesses':telemetry,'before':before,'after':after,'authorization_path':str(case.path),'authorization_sha256':digest(case.path),'same_command':atom.same_command(case.path),'provider':{'create_calls':provider.create_calls,'merge_calls':provider.merge_calls,'issue_state':provider.value['state']},'observation_scope':'independent_drive_subprocess_telemetry_setup_excluded','authorizes_landing':False}
print(json.dumps(report,sort_keys=True))
