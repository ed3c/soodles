"""Externally frozen public-CLI discriminator; no candidate judge imports."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

OWNER = json.loads((Path(__file__).resolve().parent/'owner-input.json').read_text())
PROJECTION, EVENT = OWNER['projection'], OWNER['event']

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def main():
    subject = Path(sys.argv[1]).resolve()
    scripts = subject/'.agents/skills/verify-soodles/scripts'
    env = {k:v for k,v in os.environ.items() if k not in ('GH_TOKEN','GITHUB_TOKEN','PYTHONPATH')
           and not k.startswith(('NOODLE','SOODLES_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    records, checks = [], {}
    with tempfile.TemporaryDirectory(prefix='snapshot-oracle-') as tmp:
        root=Path(tmp).resolve()
        instruction=root/'AGENTS.md'
        instruction.write_text('Use current owner next.\n')

        def call(argv):
            process=subprocess.run(argv,cwd=subject,env=env,capture_output=True,text=True,timeout=30)
            row=dict(argv=argv,exit_status=process.returncode,stdout=process.stdout,stderr=process.stderr)
            records.append(row)
            return row

        def observe(label, observations):
            packet=dict(case='pending',requests=[{'files_before':observations}],owner_events=[EVENT],transport_events=[],
                initial_owner_projection=PROJECTION,expected_owner_projection_sha256=fingerprint(PROJECTION))
            path=root/(label+'.json')
            path.write_text(json.dumps(packet))
            row=call([sys.executable,str(scripts/'observe_pclass.py'),str(path)])
            row['input_packet']=packet
            return row,json.loads(row['stdout'])

        try:
            for label, shell, denied in [('readable',False,False),('direct_denied',False,True),('shell_denied',True,True)]:
                instruction.chmod(0 if denied else 0o600)
                command=['/bin/sh','-c','cat '+shlex.quote(str(instruction))] if shell else ['/bin/cat',str(instruction)]
                row=call([sys.executable,str(scripts/'record_context.py'),str(root/'evidence'),label,*command])
                request=json.loads((root/'evidence'/label/'request.json').read_text())
                recorded=json.loads((root/'evidence'/label/'result.json').read_text())
                row.update(request=request,result=recorded)
                observed,receipt=observe(label,request['files_before'])
                bound=request['files_before'].get(str(instruction))
                if denied:
                    checks[label+'_capability']=row['exit_status']!=0
                    checks[label+'_error_preserved']=bool(bound and bound.get('snapshot_error')=='PermissionError')
                    checks[label+'_not_valid_read']=observed['exit_status']==1 and receipt['classification']=='FAIL' and not receipt['instruction_documents']
                else:
                    checks['readable']=row['exit_status']==0 and observed['exit_status']==0 and receipt['classification']=='PASS'
            good={'bytes':0,'sha256':hashlib.sha256(b'').hexdigest(),'observed_from':['argv']}
            cases={'error_only':{'snapshot_error':'PermissionError','observed_from':['argv']},
                   'empty':{},'invalid_digest':dict(good,sha256='z'*64),
                   'invalid_size':dict(good,bytes=-1),'valid_empty':good}
            for label,value in cases.items():
                row,receipt=observe(label,{str(instruction):value})
                expected=label=='valid_empty'
                checks[label]=(row['exit_status']==(0 if expected else 1)
                    and receipt['classification']==('PASS' if expected else 'FAIL'))
            row,receipt=observe('mixed',{str(instruction):good,str(root/'.agents/skills/example/SKILL.md'):cases['error_only']})
            checks['mixed_preserves_valid_only']=row['exit_status']==0 and list(receipt['instruction_documents'])==[str(instruction)]
        finally:
            instruction.chmod(0o600)
    checks['cleanup']=not root.exists()
    print(json.dumps(dict(checks=checks,passed=all(checks.values()),records=records,
        subject=str(subject),scripts={p:hashlib.sha256((scripts/p).read_bytes()).hexdigest() for p in ('record_context.py','observe_pclass.py')},
        fixture_scope='planted recording/observer controls only; no model behavior or live provider',authorizes_landing=False),indent=2))
    return 0 if all(checks.values()) else 1

if __name__=='__main__':
    raise SystemExit(main())
