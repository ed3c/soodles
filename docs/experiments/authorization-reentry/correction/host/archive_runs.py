import gzip,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
B=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for label in sys.argv[1:]:
 p=B/'host/runs'/label;a=B/'archives'/label
 subprocess.run([sys.executable,str(B/'tools/archive_case.py'),str(p),str(a)],check=True,capture_output=True)
 subprocess.run([sys.executable,str(B/'tools/replay_archive.py'),str(a),sha(a/'inventory.json'),str(B/'evaluator/check.py'),str(B/'archives'/(label+'-replay'))],check=True,capture_output=True)
 dest=B/'archives'/(label+'.tar.gz')
 with dest.open('xb') as out,gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as tar:
  for f in sorted(a.rglob('*')):
   info=tar.gettarinfo(str(f),arcname=str(f.relative_to(a)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   if f.is_file():
    with f.open('rb') as stream:tar.addfile(info,stream)
   else:tar.addfile(info)
 entry={'id':label,'archive':dest.name,'archive_sha256':sha(dest),'inventory_sha256':sha(a/'inventory.json'),'result_sha256':sha(a/'result.json'),'replay_pass':True}
 (B/'archives'/(label+'-index.json')).write_text(json.dumps(entry,indent=2)+'\n')
 print(label,'archived and replayed')
