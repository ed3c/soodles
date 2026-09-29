#!/usr/bin/env python3
"""Read-only prelaunch binding verification; no model or product mutation."""
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]).resolve()
def sha(q): return hashlib.sha256(q.read_bytes()).hexdigest()
def snapshot(root):
 return {str(q.relative_to(root)):{'sha256':sha(q),'mode':q.stat().st_mode&0o777} for q in sorted(root.rglob('*')) if q.is_file() and not q.is_symlink()}
b=json.loads((p/'validation-bindings.json').read_text()); errors=[]
for source in b['sources']:
 root=Path(source['path']); pin=json.loads((root/'projection.json').read_text())
 if sha(root/'projection.json')!=source['manifest_sha256']:errors.append(str(root)+': manifest digest')
 if (root/'.git').exists():errors.append(str(root)+': unexpected .git')
 if set(pin['allowlist'])!=set(pin['files']):errors.append(str(root)+': allowlist')
 actual={str(q.relative_to(root)) for q in root.rglob('*') if q.is_file()}
 if actual!=set(pin['files'])|{'projection.json'}:errors.append(str(root)+': unexpected file set')
 for name,v in pin['files'].items():
  q=root/name; data=q.read_bytes()
  checks={'sha256':hashlib.sha256(data).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),'bytes':len(data),'projected_mode':oct(q.stat().st_mode&0o777),'source_ref':pin['selected_ref']}
  for k,value in checks.items():
   if value!=v[k]:errors.append(str(q)+': '+k)
  if q.is_symlink():errors.append(str(q)+': symlink')
 if snapshot(root)!=json.loads((p/'source-inventory.json').read_text())[str(root)]:errors.append(str(root)+': source inventory')
for fixture in b['fixtures']:
 root=Path(fixture['path']);current={k:v for k,v in snapshot(root).items() if not k.startswith(('work/','evidence/'))}
 if current!=json.loads((p/fixture['inventory']).read_text()):errors.append(str(root)+': immutable fixture inventory')
manifest=p/'manifest.json'
if manifest.exists():
 for name,digest in json.loads(manifest.read_text())['fixed_files'].items():
  if sha(p/name)!=digest:errors.append(name+': fixed metadata digest')
print(json.dumps({'status':'PASS' if not errors else 'FAIL','sources':len(b['sources']),'fixtures':len(b['fixtures']),'errors':errors,'manifest_present':manifest.exists(),'authorizes_landing':False},indent=2))
sys.exit(bool(errors))
