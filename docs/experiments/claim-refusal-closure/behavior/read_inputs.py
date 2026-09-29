#!/usr/bin/env python3
"""Read only the externally assigned packet, preserving exact observed bytes."""
import hashlib,json,pathlib,sys
p=pathlib.Path; manifest=p(sys.argv[1]); output=p(sys.argv[2]); assigned=json.loads(manifest.read_text()); reads=[]; chunks=[]
for item in assigned['inputs']:
 path=p(item['path']); data=path.read_bytes(); observed=hashlib.sha256(data).hexdigest()
 if observed!=item['sha256']: raise SystemExit('assigned input digest mismatch: '+str(path))
 reads.append({'path':str(path),'bytes':len(data),'sha256':observed}); chunks.append('FILE '+str(path)+'\n'+data.decode('utf-8'))
text='\n\n'.join(chunks)+'\n'
with output.open('x') as f: json.dump({'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'reads':reads,'stdout_sha256':hashlib.sha256(text.encode()).hexdigest(),'scope':'assigned_reader_subprocess_actual_file_reads'},f,sort_keys=True,indent=2)
print(text,end='')
