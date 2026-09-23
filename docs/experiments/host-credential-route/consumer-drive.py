"""Run the supplied source's actual atom CLI against a disposable host/provider fixture."""
import contextlib,hashlib,io,json,os,subprocess,sys,time
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent

def main():
 source=Path(sys.argv[1]).resolve();case=sys.argv[2];out=Path(sys.argv[3]);out.mkdir(exist_ok=False)
 sys.path.insert(0,str(source));sys.path.insert(1,str(P))
 import issue_atom as atom,soodles,provider_credential as credential
 from fixture import Fixture
 f=Fixture();f.setUp();outer=f.outer
 calls={'supplier':0,'provider_reads':0,'provider_writes':0,'scope_matches':None,'child_credentials_removed':None}
 marker=outer/'supplier-count';key=outer/'synthetic-key';key.write_text('fixture only, not a private key');key.chmod(0o600)
 supplier=outer/'supplier';supplier.write_text('''#!/bin/sh
printf x >> "$FIXTURE_SUPPLIER_COUNT"
test "$NOODLES_APP_REPOSITORIES_JSON" = '["soodles"]' || exit 9
test "$NOODLES_APP_PERMISSIONS_JSON" = '{"actions": "read", "contents": "write", "issues": "write", "pull_requests": "write"}' || exit 10
if test "$FIXTURE_FAILURE" = 1; then printf fixture-secret >&2; exit 7; fi
printf fixture-installation-token
''');supplier.chmod(0o755)
 config=outer/'config';profile=config/'soodles/provider.json';profile.parent.mkdir(parents=True)
 spec={'schema':1,'kind':'github_app_supplier','supplier':{'path':str(supplier),'sha256':hashlib.sha256(supplier.read_bytes()).hexdigest()},'app':{'client_id':'fixture-client','installation_id':'123','private_key_path':str(key)}}
 env={'PATH':os.environ['PATH'],'HOME':str(outer/'home'),'XDG_CONFIG_HOME':str(config),'SOODLES_AUTHORIZATION_SHA256':f.digest,'FIXTURE_SUPPLIER_COUNT':str(marker),'GH_TOKEN':'stale-parent','NOODLES_APP_REPOSITORIES_JSON':'["wrong"]','NOODLES_APP_PERMISSIONS_JSON':'{"administration":"write"}'}
 if case.startswith('missing_'):
  group,name=case.removeprefix('missing_').split('.',1);del spec[group][name]
 elif case=='digest':spec['supplier']['sha256']='0'*64
 elif case=='key_missing':key.unlink()
 elif case=='failure':env['FIXTURE_FAILURE']='1'
 elif case=='child_context':env['NOODLE_SESSION_ID']='fixture-child'
 elif case=='internal':
  config=f.root/'config';profile=config/'soodles/provider.json';profile.parent.mkdir(parents=True);env['XDG_CONFIG_HOME']=str(config)
 if case!='absent':profile.write_text(json.dumps(spec));profile.chmod(0o600)
 if case=='legacy':env['NOODLES_TOKEN_COMMAND']=str(supplier);profile.write_text('{invalid profile is not selected')
 class Provider:
  def __init__(self,repository,*,token):
   assert repository=='ed3c/soodles' and token=='fixture-installation-token';self.value=None;f.ready_issue(self)
  def issues(self):calls['provider_reads']+=1;return [self.value]
  def issue(self,number):calls['provider_reads']+=1;return self.value
  def create_issue(self,*a):calls['provider_writes']+=1;raise AssertionError('fixture must never write')
 class Reached(Exception):pass
 def admission(*args,**kwargs):
  resolved=kwargs['environ'];clean=credential.clean_child_env(resolved)
  calls['scope_matches']=True
  calls['child_credentials_removed']=all(k not in clean for k in ['NOODLES_TOKEN_COMMAND','GH_TOKEN','NOODLES_APP_CLIENT_ID','NOODLES_APP_INSTALLATION_ID','NOODLES_APP_PRIVATE_KEY_PATH'])
  raise Reached()
 stdout=io.StringIO();stderr=io.StringIO();started=time.monotonic();exit_code=None;boundary=None
 try:
  with patch.dict(os.environ,env,clear=True),patch.object(sys,'argv',['soodles','atom','run',str(f.path)]),patch.object(atom,'GitHubProvider',Provider),patch.object(atom,'create_envelope',admission),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
   try:exit_code=soodles.main()
   except Reached:boundary='admission';exit_code=0
  calls['supplier']=len(marker.read_bytes()) if marker.exists() else 0
  result={'case':case,'exit':exit_code,'boundary':boundary,'stdout':stdout.getvalue(),'stderr':stderr.getvalue(),'calls':calls,'checkpoint_created':atom.artifact_paths(f.path)['state'].exists(),'elapsed_seconds':time.monotonic()-started,'fixture_scope':'real atom CLI, synthetic provider and supplier, stopped at existing admission handoff','authorizes_landing':False}
 finally:f.doCleanups()
 result['disposable_removed']=not outer.exists();(out/'process.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
