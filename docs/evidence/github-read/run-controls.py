from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile,time
ROOT=Path(__file__).resolve().parent
SOURCE=Path('/Users/neon/soodles/.worktrees/issue44-github-read')
ORACLE=ROOT/'fixed-oracle'; ORACLE.mkdir(exist_ok=True)
for name in ['test_github_reader.py']:
    target=ORACLE/name
    if not target.exists(): target.write_bytes((SOURCE/'tests'/name).read_bytes());target.chmod(0o444)
selection={'selected_at':time.time(),'oracle_sha256':hashlib.sha256((ORACLE/'test_github_reader.py').read_bytes()).hexdigest(),'authorizes_landing':False,'scope':'Fixed external discriminators against copied production reader bytes; only redirects use loopback HTTP, other provider responses are fixtures.'}
if not (ROOT/'oracle-selection.json').exists(): (ROOT/'oracle-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
assert selection['oracle_sha256']==json.loads((ROOT/'oracle-selection.json').read_text())['oracle_sha256']
CONTROL='test_github_reader.GithubReaderTests.'
source=(SOURCE/'github_reader.py').read_text()
cases=[
 ('anonymous',None,None,'test_no_anonymous_request_without_credentials','test_authenticated_non_case'),
 ('opaque-credential','if not token or any(not 33 <= ord(character) <= 126 for character in token):','if not re.fullmatch(r"[A-Za-z0-9_]+", token):','test_opaque_provider_credential_is_a_legal_non_case','test_authenticated_non_case'),
 ('header-safety','if not token or any(not 33 <= ord(character) <= 126 for character in token):','if not token:','test_header_control_characters_refused_before_transport','test_opaque_provider_credential_is_a_legal_non_case'),
 ('identity','identity = _hash(token.encode())','identity = "shared"','test_changed_identity_never_reuses_cache','test_304_revalidates_same_identity_and_bytes'),
 ('cache-bytes','cached.get("sha256") == _hash(cached["body"].encode())','True','test_corrupt_cache_requires_fresh_bytes','test_304_revalidates_same_identity_and_bytes'),
 ('freshness','if status == 304:','if status in (304, 500):','test_provider_failure_never_returns_stale_cache','test_304_revalidates_same_identity_and_bytes'),
 ('redirect','urllib.request.build_opener(NoRedirect())','urllib.request.build_opener()','test_credential_not_forwarded_on_redirect','test_authenticated_non_case'),
 ('budget','if until > now:','if False:','test_quota_wait_has_no_retry_and_blocks_next_call','test_expired_wait_allows_authenticated_non_case'),
 ('no-retry','response = _request(request)','response = _request(request)\n                response.close()\n                response = _request(request)','test_quota_wait_has_no_retry_and_blocks_next_call','test_authenticated_non_case'),
 ('exact-subject','if not isinstance(value, dict) or value.get("url") != url or type(value.get("number")) is not int or value["number"] != number or "pull_request" in value:','if False:','test_wrong_issue_identity_refused','test_authenticated_non_case'),
 ('wait-exit',None,None,'test_cli_quota_wait_reports_exit_75_without_network','test_cli_missing_credential_names_owner_and_help'),
]
records=[]
with tempfile.TemporaryDirectory(prefix='soodles44-mutants-') as directory:
    for name,old,new,control,noncase in cases:
        candidate=Path(directory)/name;candidate.mkdir()
        for path in SOURCE.glob('*.py'): shutil.copy2(path,candidate/path.name)
        shutil.copy2(SOURCE/'soodles',candidate/'soodles')
        if name=='anonymous':
            old_source=subprocess.check_output(['git','show','f2bd849b9523134364ca598df72a4e15fc541ab9:issue_execution.py'],cwd=SOURCE)
            (candidate/'issue_execution.py').write_bytes(old_source)
        elif name=='wait-exit':
            p=candidate/'soodles.py';s=p.read_text();assert 'return getattr(error, "exit_code", 1)' in s;s=s.replace('return getattr(error, "exit_code", 1)','return 1');p.write_text(s)
        else:
            assert source.count(old)==1,(name,source.count(old))
            (candidate/'github_reader.py').write_text(source.replace(old,new))
        runs=[]
        for kind,root,test in [('RED',candidate,control),('GREEN',SOURCE,control),('NON_CASE_GREEN',SOURCE,noncase)]:
            argv=['python3','-B','-m','unittest',CONTROL+test,'-v']
            env={key:os.environ[key] for key in ('PATH','LANG','LC_ALL') if key in os.environ}
            env.update(PYTHONPATH=str(ORACLE)+os.pathsep+str(root),TMPDIR='/private/tmp')
            result=subprocess.run(argv,cwd=root,env=env,capture_output=True,text=True,timeout=15)
            runs.append({'classification':kind,'argv':argv,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        record={'gate':name,'mutation':{'old':old,'new':new} if old else {'kind':'old production reader' if name=='anonymous' else 'drop structured wait exit'},'control':control,'non_case':noncase,'runs':runs,'passed':runs[0]['exit']!=0 and all(x['exit']==0 for x in runs[1:])}
        records.append(record)
receipt={**selection,'source_files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'github_reader.py',SOURCE/'soodles.py',SOURCE/'issue_execution.py']},'cases':records,'passed':all(r['passed'] for r in records),'mutant_worktrees_removed':True}
(ROOT/'gate-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'passed':receipt['passed'],'cases':[{'gate':x['gate'],'exits':[y['exit'] for y in x['runs']],'passed':x['passed']} for x in records]},indent=2))
raise SystemExit(0 if receipt['passed'] else 1)
