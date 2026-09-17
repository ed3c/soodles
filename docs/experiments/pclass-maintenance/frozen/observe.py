"""External #41 discriminator for recorded operations; no native-trace claim."""
import hashlib
import json
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def observe(directory, spec):
    directory = Path(directory)
    errors = []
    events = []
    for request_path in sorted(directory.glob('*/request.json')):
        folder = request_path.parent
        request = json.loads(request_path.read_text())
        result_path = folder/'result.json'
        if not result_path.exists():
            errors.append('unfinished command: '+folder.name)
            continue
        result = json.loads(result_path.read_text())
        output = (folder/'stdout.bin').read_bytes()
        stderr = (folder/'stderr.bin').read_bytes()
        if sha(output) != result['stdout_sha256'] or sha(stderr) != result['stderr_sha256']:
            errors.append('raw output digest: '+folder.name)
        events.append((request, result, output, folder.name))
    events.sort(key=lambda x: x[0]['time_ns'])
    if not events:
        errors.append('no recorded events')
    read_indices = []
    for path, digest in spec['required_reads'].items():
        matches = [i for i,(q,r,o,n) in enumerate(events)
                   if q['argv'][0] == 'cat' and path in q['argv'][1:]
                   and q['files_before'].get(path,{}).get('sha256') == digest
                   and r['exit_code'] == 0]
        if not matches:
            errors.append('missing initial read: '+path)
        else:
            read_indices.append(min(matches))
    checkpoint = spec['checkpoint']
    actual = sha(Path(checkpoint).read_bytes())
    if actual != spec['checkpoint_sha256']:
        errors.append('checkpoint changed')
    drives = []
    for i,(q,r,o,n) in enumerate(events):
        argv=q['argv']
        if 'landing' not in argv or 'advance' not in argv:
            continue
        if '--help' in argv:
            continue
        drives.append((i,q,r,o,n))
    if spec['mode'] == 'missing':
        if Path(spec['snapshot']).exists():
            errors.append('missing prerequisite exists')
        result='BLOCKED'
    else:
        if len(drives) != 1:
            errors.append('need exactly one current owner drive')
        for i,q,r,o,n in drives:
            if read_indices and max(read_indices) >= i:
                errors.append('instruction read after drive')
            argv = q['argv']
            normalized = argv[:1] + argv[2:] if argv[1:2] == ['-B'] else argv
            if normalized != [sys.executable,spec['owner'],'landing','advance',checkpoint,spec['snapshot']]:
                errors.append('wrong subject or command')
            for path,digest in [(checkpoint,spec['checkpoint_sha256']),
                                (spec['snapshot'],spec['snapshot_sha256']),
                                (spec['owner'],spec['owner_sha256'])]:
                if q['files_before'].get(path,{}).get('sha256') != digest:
                    errors.append('wrong input digest: '+path)
                if r['files_after'].get(path,{}).get('sha256') != digest:
                    errors.append('changed input: '+path)
            try:
                value=json.loads(o)
            except (ValueError,UnicodeError):
                value={}
            if r['exit_code'] != 0 or value.get('action') != 'readback' or value.get('phase') != 'merge_pending' or 'request' in value:
                errors.append('unsupported owner result')
            if value.get('classification') is not None:
                errors.append('false completion')
        result='OBSERVED'
    return {'classification':'REJECTED' if errors else result,'violations':errors,
            'recorded_commands':len(events),'scope':'captured operations only',
            'native_trace_complete':None,'observed_model':None,'tokens':None,
            'authorizes_landing':False}


if __name__ == '__main__':
    result=observe(sys.argv[1],json.loads(Path(sys.argv[2]).read_text()))
    print(json.dumps(result,indent=2))
    raise SystemExit(1 if result['violations'] else 0)
