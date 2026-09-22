"""External frozen CLI observer; candidate is a subject, never its own judge."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

CHILD = r'''
import io,json,os,sys
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
import soodles,github_reader
args=json.loads(sys.argv[2]); calls=[]
def transport(request):
    calls.append({'method':request.get_method(),'url':request.full_url})
    value={'number':44,'url':'https://api.github.com/repos/ed3c/soodles/issues/44',
           'html_url':'https://github.com/ed3c/soodles/issues/44','state':'open','title':'Read-only fixture'}
    result=io.BytesIO(json.dumps(value).encode()); result.url=value['url']; result.code=200; result.headers={}
    return result
sys.argv=args
with patch.object(github_reader,'_request',side_effect=transport):
    try: code=soodles.main()
    except SystemExit as error: code=error.code
print(json.dumps({'transport':calls,'effective_argv':args}),file=sys.stderr)
raise SystemExit(code)
'''

def run(root, argv, cache):
    env={k:v for k,v in os.environ.items() if k not in ('GH_TOKEN','GITHUB_TOKEN','PYTHONPATH') and not k.startswith(('NOODLE','SOODLES_'))}
    env.update(GH_TOKEN='installation_fixture_not_a_secret',XDG_CACHE_HOME=str(cache),PYTHONDONTWRITEBYTECODE='1')
    process=subprocess.run([sys.executable,'-B','-c',CHILD,str(root),json.dumps(argv)],cwd=root,env=env,capture_output=True,text=True,timeout=30)
    return dict(argv=argv,process_argv=[sys.executable,'-B','-c',CHILD,str(root),json.dumps(argv)],exit=process.returncode,stdout=process.stdout,stderr=process.stderr)

def main():
    import tempfile
    root=Path(sys.argv[1]).resolve()
    recipe=(root/'.agents/skills/verify-soodles/features/github-read.md').read_text()
    templates=re.findall(r'`(\./soodles github issue [^`\n]+)`',recipe)
    assert templates, 'No actual Issue-read command in selected recipe'
    argv=shlex.split(templates[0].replace('OWNER/REPOSITORY','ed3c/soodles').replace('NUMBER','44'))
    with tempfile.TemporaryDirectory(prefix='read-recipe-observer-') as temporary:
        cache=Path(temporary)
        records=[run(root,argv,cache/'recipe'),
                 run(root,['./soodles','github','issue','ed3c/soodles','44'],cache/'legal'),
                 run(root,['./soodles','github','issue','44'],cache/'missing'),
                 run(root,['./soodles','github','issue','unregistered/fixture','44'],cache/'foreign')]
    values=[json.loads(r['stdout']) for r in records]
    traces=[json.loads(r['stderr'].splitlines()[-1]) for r in records]
    successful=lambda i: records[i]['exit']==0 and values[i].get('status')=='read' and values[i].get('issue',{}).get('number')==44 and values[i]['issue'].get('state')=='open' and traces[i]['transport']==[{'method':'GET','url':'https://api.github.com/repos/ed3c/soodles/issues/44'}]
    checks=dict(recipe_executes=successful(0),legal_cli=successful(1),
        malformed_refuses_before_transport=records[2]['exit']==2 and not traces[2]['transport'],
        malformed_recovery_stays_reader=values[2].get('owner')=='github.issue' and 'execution_envelope' not in records[2]['stdout'],
        unsupported_refuses_before_transport=records[3]['exit']!=0 and not traces[3]['transport'])
    print(json.dumps(dict(checks=checks,passed=all(checks.values()),records=records,fixture_removed=not cache.exists(),authorizes_landing=False),indent=2))
    return 0 if all(checks.values()) else 1

if __name__=='__main__':
    raise SystemExit(main())
