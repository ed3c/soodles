"""One real harmless process at the existing oracle seam, no Noodle run."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import traceback
from unittest.mock import patch

P=Path(__file__).resolve().parent
subject=Path(sys.argv[1]).resolve()
output=Path(sys.argv[2]).resolve()
assert not output.exists()
spec=importlib.util.spec_from_file_location('subject_handoff_oracle',subject/'handoff_oracle.py')
oracle=importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
sys.path.insert(0,str(subject))
children=[]
roots=[]
argv=[sys.executable,'-u','-c',
    'import signal,sys; signal.signal(signal.SIGINT,lambda *_:sys.exit(0)); print("ready",flush=True); signal.pause()']
report=dict(source=str(subject),source_sha256=hashlib.sha256((subject/'handoff_oracle.py').read_bytes()).hexdigest(),
    protocol_sha256=hashlib.sha256((P/'protocol.md').read_bytes()).hexdigest(),
    scope='oracle cleanup unit seam with a real harmless Python child; no Noodle/model/provider execution',
    process_argv=argv,authorizes_landing=False)

def start(noodle,root):
    process=subprocess.Popen(argv,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    children.append(process)
    roots.append(Path(root))
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout,selectors.EVENT_READ)
        if not selector.select(timeout=5):
            raise RuntimeError('control child did not become ready')
    assert process.stdout.readline().strip()=='ready'
    return process

def wait(*args,**kwargs):
    raise RuntimeError('fixed first-projection failure')

try:
    with patch.object(oracle,'_run',return_value='a'*40), \
         patch.object(oracle.subprocess,'run',return_value=subprocess.CompletedProcess([],0)), \
         patch.object(oracle,'_start',side_effect=start), patch.object(oracle,'_wait',side_effect=wait):
        try:
            oracle.handoff_probe('/Users/neon/.codex/experiments/soodles133-bootstrap.QpepPK/noodle-source/bin/noodle',subject)
        except Exception as error:
            report['exception']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    assert len(children)==1
    child=children[0]
    report.update(pid=child.pid,returncode_before_external_cleanup=child.poll(),
        child_alive_after_owner_failure=child.poll() is None,fixture_removed_before_external_cleanup=not roots[0].exists(),
        original_failure_preserved=report.get('exception',{}).get('message')=='fixed first-projection failure')
finally:
    cleanup=[]
    for child in children:
        try:
            if child.poll() is None:
                stopped=oracle._stop(child)
                cleanup.append(dict(owner='external harness emergency cleanup via existing _stop',result=stopped))
            else:
                stdout,stderr=child.communicate(timeout=5)
                cleanup.append(dict(owner='subject already terminated child; harness confirms reap',returncode=child.returncode))
        except Exception as error:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL)
            child.communicate(timeout=5)
            cleanup.append(dict(owner='bounded emergency kill of known child only',error_type=type(error).__name__,returncode=child.returncode))
    report['cleanup']=cleanup
    report['processes_absent']=all(child.poll() is not None for child in children)
    report['passed']=bool(children) and report.get('child_alive_after_owner_failure') is False and report.get('original_failure_preserved') is True
    with output.open('x') as stream:
        json.dump(report,stream,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('exception','process_argv')}))
raise SystemExit(0 if report['passed'] else 1)
