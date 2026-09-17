from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile,time,urllib.request
r=Path(__file__).parent;label=sys.argv[1];out=r/(label+'-auth.json');assert not out.exists()
supplier=Path('/Users/neon/noodles/.noodle/staging/bin/mint-noodles-installation-token')
env={**os.environ,'NOODLES_APP_CLIENT_ID':'Iv23lichgyEbAAvpRk19','NOODLES_APP_PRIVATE_KEY_PATH':'/Users/neon/.noodles-app-key.pem','NOODLES_APP_INSTALLATION_ID':'157336758','NOODLES_APP_REPOSITORIES_JSON':'["soodles"]','NOODLES_APP_PERMISSIONS_JSON':'{"issues":"read"}'}
mint=subprocess.run([str(supplier)],capture_output=True,text=True,env=env,timeout=30)
assert mint.returncode==0,'managed App supplier failed; sensitive output suppressed'
token=mint.stdout.strip();assert token and '\n' not in token
receipt={'argv':sys.argv[2:],'requested_repositories':['soodles'],'requested_permissions':{'issues':'read'},'supplier_sha256':hashlib.sha256(supplier.read_bytes()).hexdigest(),'token_persisted':False,'anonymous_fallback':False,'authorizes_landing':False}
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):return None
start=time.monotonic();result=None
try:
 with tempfile.TemporaryDirectory(prefix='soodles39-app-cache-') as cache:
  result=subprocess.run(sys.argv[2:],cwd=r,env={**os.environ,'GH_TOKEN':token,'XDG_CACHE_HOME':cache,'TMPDIR':'/private/tmp','PYTHONDONTWRITEBYTECODE':'1','NOODLE_NO_BROWSER':'1'},capture_output=True,text=True,timeout=1000)
  assert token not in result.stdout+result.stderr,'credential reached output; withheld'
  (r/(label+'.stdout.log')).write_text(result.stdout);(r/(label+'.stderr.log')).write_text(result.stderr)
  receipt.update(exit=result.returncode,elapsed_seconds=time.monotonic()-start)
finally:
 req=urllib.request.Request('https://api.github.com/installation/token',method='DELETE',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'soodles39-bounded-comparison'})
 with urllib.request.build_opener(NoRedirect()).open(req,timeout=30) as response:receipt['revocation_status']=response.status
 out.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt));raise SystemExit(result.returncode if result else 1)
