"""Archive bounded handoff observations; never claims a fresh replay."""
import hashlib,json,shutil,subprocess,sys,gzip,tarfile
from pathlib import Path
B=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(B/'tools'));from archive_case import walk,inventory
p=B/'host/runs/downstream-r03';spec=json.loads((p/'case.json').read_text());run=Path(spec['run_root']);context=json.loads((B/'host/downstream-context.json').read_text());parent=Path(context['prior_facts']).parent
dest=B/'archives/downstream-r03';dest.mkdir()
for src,relative in [(run/'raw','run/raw'),(run/'binding.json','run/binding.json'),(run/'output/workspace','run/output/workspace'),(parent,'parent'),(p/'downstream-result.json','result.json'),(p/'case.json','case.json'),(B/'host/downstream-context.json','parent-context.json'),(run/'control/drive.py','run/control/drive.py')]:
 files,dirs=walk(src,exclude_git=True)
 for f in files:
  target=dest/relative/(f.relative_to(src)) if src.is_dir() else dest/relative
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
(dest/'roots.json').write_text(json.dumps({'run':str(run),'parent':str(parent),'scope':'captured observations only; Git omitted'},indent=2)+'\n')
(dest/'inventory.json').write_text(json.dumps(inventory(dest),indent=2,sort_keys=True)+'\n')
out=B/'archives/downstream-r03.tar.gz'
with out.open('xb') as o,gzip.GzipFile(filename='',mode='wb',fileobj=o,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as tar:
 for f in sorted(dest.rglob('*')):
  info=tar.gettarinfo(str(f),arcname=str(f.relative_to(dest)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  if f.is_file():
   with f.open('rb') as stream:tar.addfile(info,stream)
  else:tar.addfile(info)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(B/'archives/downstream-index.json').write_text(json.dumps({'archive':out.name,'archive_sha256':sha(out),'inventory_sha256':sha(dest/'inventory.json'),'result_sha256':sha(dest/'result.json'),'scope':'actual previous consumer handoff; archive integrity, not model replay'},indent=2)+'\n')
print('downstream raw and exact parent handoff archived')
