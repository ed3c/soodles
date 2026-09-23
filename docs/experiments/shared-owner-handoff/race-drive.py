"""Two independently authorized atom calls, one disposable control root."""
import json,sys,threading
from pathlib import Path
P=Path(__file__).resolve().parent
source=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
sys.path[:0]=[str(source),str(P)]
import issue_atom as atom
from fixture import Fixture,Provider
f=Fixture();f.setUp();first=threading.Event();release=threading.Event();results={};effects=[]
class Stop(Exception):pass
class Synthetic(Provider):
 def __init__(self,label):super().__init__();self.label=label
 def create_issue(self,*args):
  effects.append(self.label)
  if self.label=='A':first.set();assert release.wait(10)
  raise Stop('bounded synthetic transport observed; no admission or real provider')
try:
 other=f.outer/'authorization-B.json';b={**f.authorization,'issue':{**f.authorization['issue'],'title':'Independent B'}};other.write_text(json.dumps(b))
 def invoke(label,path,env):
  try:atom.run(path,environ=env,provider=Synthetic(label));results[label]={'outcome':'returned'}
  except atom.AtomRefusal as e:results[label]=atom.refusal_output(e,path)
  except Stop as e:results[label]={'outcome':'synthetic_effect_then_stop','reason':str(e)}
 a=threading.Thread(target=invoke,args=('A',f.path,f.env));a.start();assert first.wait(10)
 t=threading.Thread(target=invoke,args=('B',other,{**f.env,'SOODLES_AUTHORIZATION_SHA256':atom.digest_file(other)}));t.start();t.join(5)
 second_returned=not t.is_alive();release.set();a.join(10);t.join(10);assert not a.is_alive() and not t.is_alive()
 result={'scope':'Actual atom.run calls, independently valid authorizations, same disposable root, synthetic provider transports; first call held inside Issue-create while second enters','effects':effects,'second_returned_before_first_released':second_returned,'outcomes':results,'B_checkpoint_created':atom.artifact_paths(other)['state'].exists(),'authorizes_landing':False}
finally:release.set();f.doCleanups()
result['disposable_removed']=not f.outer.exists();(out/'process.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
