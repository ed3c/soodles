import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import issue_atom as atom
c=Path(sys.argv[2]);p=c/'admission-v4/authorization.json';a=json.loads(p.read_text());state=json.loads(Path(str(p)+'.state.json').read_text())
a.update(prior_atom={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},prior_publication=state['publication'])
try:r={'status':'verified','readback':atom.verify_prior_atom(a)}
except atom.AtomRefusal as e:r={'status':'refused','invalid':e.invalid,'required':e.required}
print(json.dumps({'source_sha256':hashlib.sha256((Path(sys.argv[1])/'issue_atom.py').read_bytes()).hexdigest(),'authorizes_landing':False,**r},indent=2))
