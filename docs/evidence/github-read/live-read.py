"""External one-shot recorder. No token/key bytes are persisted or printed."""
from pathlib import Path
import base64,hashlib,json,os,subprocess,sys,time,urllib.error,urllib.request,tempfile
ROOT=Path(__file__).resolve().parent
SOURCE=Path('/Users/neon/soodles/.worktrees/issue44-github-read')
KEY='/Users/neon/.noodles-app-key.pem'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**kw): return None
opener=urllib.request.build_opener(NoRedirect())
def enc(value): return base64.urlsafe_b64encode(value).rstrip(b'=')
now=int(time.time()); unsigned=enc(b'{"alg":"RS256","typ":"JWT"}')+b'.'+enc(json.dumps({'iat':now-60,'exp':now+480,'iss':'4753873'}).encode())
signature=subprocess.run(['openssl','dgst','-sha256','-sign',KEY],input=unsigned,capture_output=True,check=True).stdout
jwt=(unsigned+b'.'+enc(signature)).decode()
body={'repositories':['soodles'],'permissions':{'issues':'read'}}
request=urllib.request.Request('https://api.github.com/app/installations/157336758/access_tokens',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+jwt,'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'soodles-supervised-minimum-use'})
with opener.open(request,timeout=30) as response:
    mint=json.load(response)
token=mint.pop('token')
assert mint['permissions']=={'issues':'read','metadata':'read'}, 'unexpected token permissions'
assert [r['full_name'] for r in mint['repositories']]==['ed3c/soodles'], 'unexpected repository scope'
receipt={'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip(),'source_files':{name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in ['github_reader.py','issue_execution.py','soodles.py']},'carrier':'native macOS supervisor with child Python CLI; not #39 comparison','app_id':4753873,'installation_id':157336758,'mint_request':body,'mint_response':{'permissions':mint['permissions'],'repositories':[r['full_name'] for r in mint['repositories']],'expires_at':mint['expires_at']},'requests':[],'authorizes_landing':False}
try:
    with tempfile.TemporaryDirectory(prefix='soodles44-live-cache-') as cache:
        env={**os.environ,'GH_TOKEN':token,'XDG_CACHE_HOME':cache,'TMPDIR':'/private/tmp'}
        for index in (1,2):
            argv=[str(SOURCE/'soodles'),'github','issue','44']
            result=subprocess.run(argv,cwd=SOURCE,env=env,text=True,capture_output=True,timeout=40)
            assert token not in result.stdout+result.stderr, 'credential appeared in CLI output'
            data=json.loads(result.stdout)
            record={'argv':argv,'exit':result.returncode,'stdout':data,'stderr':result.stderr}
            (ROOT/f'live-cli-{index}.json').write_text(json.dumps(record,indent=2)+'\n')
            result.check_returncode(); receipt['requests'].append(data['observation'])
            if index==1: live_issue=data['issue']
            else: assert data['issue']==live_issue and data['observation']['status']==304
        sys.path[:0]=[str(SOURCE),str(SOURCE/'tests')]
        import issue_execution,issue_admission
        from test_issue_execution import IssueExecutionTests
        from unittest.mock import patch
        fixture=IssueExecutionTests('test_both_real_entry_functions_consume_same_normalized_binding')
        fixture.setUp()
        try:
            contract=issue_admission.parse_contract(live_issue['body'])
            fixture.envelope.update(issue=44,body_sha256=issue_admission.body_digest(live_issue['body']),body_updated_at=live_issue['updated_at'],owner=contract['owner'],write_paths=contract['write_paths'])
            fixture.envelope['execution']['order_id']='soodles-44'; fixture.bind_envelope()
            with patch.dict(os.environ,env):
                first=issue_execution.automatic(fixture.path,fixture.pin,fixture.root)
                before=(fixture.runtime/'orders-next.json').read_bytes()
                second=issue_execution.automatic(fixture.path,fixture.pin,fixture.root)
                assert (fixture.runtime/'orders-next.json').read_bytes()==before
            receipt['consumer']={'route':'real automatic function, default authenticated reader, live GitHub #44, local owner fixture','first':first,'second':second,'same_mailbox_bytes':True,'worker_effect':fixture.effect.exists(),'envelope':fixture.envelope,'mailbox_sha256':hashlib.sha256(before).hexdigest()}
        finally: fixture.doCleanups()
        receipt['cache_removed_after_run']=True
finally:
    request=urllib.request.Request('https://api.github.com/installation/token',method='DELETE',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'soodles-supervised-minimum-use'})
    with opener.open(request,timeout=30) as response: receipt['token_revocation_status']=response.status
    receipt['credential_persisted']=False
    (ROOT/'live-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'mint':receipt['mint_response'],'cli_reads':receipt['requests'],'consumer':{key:receipt.get('consumer',{}).get(key) for key in ['route','same_mailbox_bytes','worker_effect']},'revocation':receipt['token_revocation_status']},indent=2))
