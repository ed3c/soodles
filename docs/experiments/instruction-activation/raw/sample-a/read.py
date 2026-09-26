import sys,json,hashlib,os,time
from pathlib import Path
root=Path(__file__).resolve().parent
key=sys.argv[1] if len(sys.argv)==2 else ''
if key not in ('input','recipe'):raise SystemExit('use the supplied reader with input or recipe')
p=root/('input.json' if key=='input' else 'recipe.md');b=p.read_bytes()
with (root.parent/'observations'/f'{root.name}.jsonl').open('a') as f:
 f.write(json.dumps({'selection':key,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'pid':os.getpid(),'time_ns':time.time_ns(),'argv':sys.argv})+'\n')
sys.stdout.buffer.write(b)
