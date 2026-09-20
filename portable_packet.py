"""Portable admission-recovery evidence. Never executes a packet continuation."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import sys
import tarfile

INPUT_SELECTION_SHA256 = '9b5c6505bcd023fb1a872d44d8a33880e862046883349bd032c4b830ccf18e14'
SOURCE = 'ca81f942f478e8e4afcbbce6ca69640867efe753'
OBSERVERS = {
    'recovery': '1f22ebd63786e032f92d51c455cfd35dff9f0660acd969db70d2f3e5deda5b6f',
    'refusal': 'b0029229f2794b283d8ab30faba8a621e0cd7035d83edcc6001a1a994229662b',
}
FIXTURES = Path(__file__).resolve().parent / 'tests/fixtures/admission-recovery-portable'
CONTINUATION = {'portable': False, 'owner': 'Noodle', 'entry': 'admission inspect'}
CARRIERS = {'linux_amd64': ('linux', 'amd64'), 'darwin_arm64': ('darwin', 'arm64')}


def require(ok, field):
    if not ok:
        raise ValueError(f'packet: invalid or missing {field}; continuation owner=Noodle entry=admission inspect')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rendered(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def write(root, name, value):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else rendered(value))


def credential_free_environment(*optional):
    names = ('PATH', 'LANG', 'LC_ALL') + optional
    return {name: os.environ[name] for name in names if name in os.environ}


def read_file(root, name):
    require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_.\-/]+', name)
            and name == str(PurePosixPath(name)) and not name.startswith('/')
            and not any(p in ('.', '..') for p in name.split('/')), 'files.path')
    path = Path(root)
    for part in name.split('/'):
        path = path / part
        require(not path.is_symlink(), 'files.path.symlink')
    require(path.is_file(), f'files.path:{name}')
    return path.read_bytes()


def selected_files():
    raw = (FIXTURES / 'preserved-input-selection.json').read_bytes()
    require(digest(raw) == INPUT_SELECTION_SHA256, 'input_selection.sha256')
    selection = json.loads(raw)
    return selection['files']


def layout():
    files = {'subject.json': 'subject', 'build.txt': 'subject',
             'preserved-input-selection.json': 'input_selection'}
    for name in selected_files():
        files['preserved-soodles-input/' + name] = 'input'
    for label in OBSERVERS:
        files[label + '-observer.py'] = 'observer'
        for name, role in [('process.json', 'process_exit'), ('stdout.bin', 'stdout'),
                           ('stderr.bin', 'stderr'), ('receipt.json', 'receipt'),
                           ('cleanup.json', 'cleanup')]:
            files[label + '/' + name] = role
    return files


def validate(packet, blobs, expected_carrier=None, expected_source=SOURCE):
    require(isinstance(packet, dict) and set(packet) == {
        'schema', 'subject', 'carrier', 'continuation', 'cleanup', 'files', 'authorizes_landing'}, 'packet.fields')
    require(type(packet['schema']) is int and packet['schema'] == 1, 'schema')
    require(packet['authorizes_landing'] is False, 'authorizes_landing')
    require(packet['continuation'] == CONTINUATION and packet['continuation']['portable'] is False, 'continuation')
    subject = packet['subject']
    require(isinstance(subject, dict) and set(subject) == {'repository', 'source_revision', 'binary_sha256'}, 'subject')
    require(subject['repository'] == 'ed3c/noodle' and subject['source_revision'] == expected_source, 'subject.source_revision')
    require(isinstance(subject['binary_sha256'], str) and re.fullmatch('[0-9a-f]{64}', subject['binary_sha256']), 'subject.binary_sha256')
    carrier = packet['carrier']
    require(isinstance(carrier, dict) and set(carrier) == {'id', 'os', 'arch'}, 'carrier')
    require(isinstance(carrier['id'], str) and carrier['id'] in CARRIERS
            and (carrier['os'], carrier['arch']) == CARRIERS[carrier['id']], 'carrier.os/arch')
    require(expected_carrier is None or carrier['id'] == expected_carrier, 'carrier.id')
    require(packet['cleanup'] == {'owned_residue_absent': True} and packet['cleanup']['owned_residue_absent'] is True, 'cleanup.owned_residue_absent')
    entries = packet['files']
    require(isinstance(entries, list), 'files')
    expected = layout()
    seen = set()
    for item in entries:
        require(isinstance(item, dict) and set(item) == {'path', 'role', 'sha256', 'bytes'}, 'files.fields')
        name = item['path']
        require(isinstance(name, str) and name in expected and name not in seen, 'files.path.allowlist')
        seen.add(name)
        require(item['role'] == expected[name], f'{name}.role')
        require(name in blobs, f'{name}.missing')
        require(type(item['bytes']) is int and item['bytes'] == len(blobs[name]), f'{name}.bytes')
        require(item['sha256'] == digest(blobs[name]), f'{name}.sha256')
    require(seen == set(expected) and set(blobs) == seen, 'files.roles/missing/extra')
    require(json.loads(blobs['subject.json']) == subject, 'subject.binding')
    build = blobs['build.txt'].decode()
    for field in [f'vcs.revision={subject["source_revision"]}', 'vcs.modified=false',
                  f'GOOS={carrier["os"]}', f'GOARCH={carrier["arch"]}']:
        require(field in build.split(), 'build.' + field)
    require(blobs['preserved-input-selection.json'] == (FIXTURES / 'preserved-input-selection.json').read_bytes(), 'input_selection.sha256')
    for name, sha in selected_files().items():
        require(digest(blobs['preserved-soodles-input/' + name]) == sha, 'input.sha256:' + name)
    for label, sha in OBSERVERS.items():
        require(digest(blobs[label + '-observer.py']) == sha, label + '.observer.sha256')
        process = json.loads(blobs[label + '/process.json'])
        require(isinstance(process, dict) and set(process) == {
            'exit_code', 'waited', 'timed_out', 'stdout_sha256', 'stderr_sha256'}, label + '.process.fields')
        require(type(process['exit_code']) is int, label + '.process.exit_code')
        require(process['waited'] is True and type(process['timed_out']) is bool, label + '.process.waited')
        for stream in ('stdout', 'stderr'):
            require(process[stream + '_sha256'] == digest(blobs[label + '/' + stream + '.bin']), label + '.process.' + stream)
        cleanup = json.loads(blobs[label + '/cleanup.json'])
        require(isinstance(cleanup, dict) and cleanup.get('owned_residue_absent') is True, label + '.cleanup')
        receipt = json.loads(blobs[label + '/receipt.json'])
        require(isinstance(receipt, dict), label + '.receipt')
        if label == 'recovery':
            require(receipt.get('scratch_removed') is True, label + '.receipt.cleanup')
            require(receipt.get('input_selection_sha256') == INPUT_SELECTION_SHA256, label + '.receipt.input_selection')
        require(receipt.get('authorizes_landing') is False, label + '.receipt.authorizes_landing')
        require(receipt.get('observer_sha256') == sha and receipt.get('binary_sha256') == subject['binary_sha256'], label + '.receipt.binding')
    return {'classification': 'GREEN', 'carrier': carrier, 'source_revision': subject['source_revision'],
            'authorizes_landing': False, 'continuation': CONTINUATION,
            'scope': 'evidence integrity; process nonzero/refusal is preserved, not reclassified as success'}


def verify(root, expected_carrier=None, expected_source=SOURCE):
    root = Path(root)
    if root.is_file():
        blobs = {}
        try:
            archive = tarfile.open(root, 'r:')
        except tarfile.TarError as exc:
            raise ValueError('packet: invalid tar; owner=Noodle entry=admission inspect') from exc
        with archive:
            for item in archive:
                require(item.isfile() and item.name in set(layout()) | {'packet.json'}
                        and item.name not in blobs, 'tar.member')
                blobs[item.name] = archive.extractfile(item).read()
        require('packet.json' in blobs, 'packet.json')
        packet = json.loads(blobs.pop('packet.json'))
    else:
        packet = json.loads(read_file(root, 'packet.json'))
        # Read fixed names only, never a path supplied by an untrusted manifest.
        blobs = {name: read_file(root, name) for name in layout()}
    return validate(packet, blobs, expected_carrier, expected_source)


def create(root, carrier_id, archive):
    root, archive = Path(root), Path(archive)
    require(carrier_id in CARRIERS, 'carrier.id')
    require(archive.resolve() != (root / 'packet.json').resolve(), 'archive.path')
    require(not (root / 'packet.json').exists() and not archive.exists(), 'output.exists')
    allowed = layout()
    blobs = {name: read_file(root, name) for name in allowed}
    system, arch = CARRIERS[carrier_id]
    packet = {'schema': 1, 'subject': json.loads(blobs['subject.json']),
              'carrier': {'id': carrier_id, 'os': system, 'arch': arch},
              'continuation': CONTINUATION, 'cleanup': {'owned_residue_absent': True},
              'authorizes_landing': False,
              'files': [{'path': n, 'role': allowed[n], 'bytes': len(b), 'sha256': digest(b)}
                        for n, b in sorted(blobs.items())]}
    result = validate(packet, blobs, carrier_id)
    blobs['packet.json'] = rendered(packet)
    # Tar has no host metadata, symlinks, directories, timestamps or ambient files.
    with archive.open('xb') as target:
        with tarfile.open(fileobj=target, mode='w', format=tarfile.USTAR_FORMAT) as tar:
            for name, data in sorted(blobs.items()):
                item = tarfile.TarInfo(name)
                item.size, item.mode, item.mtime = len(data), 0o644, 0
                tar.addfile(item, io.BytesIO(data))
    write(root, 'packet.json', packet)
    return result


def record(argv, cwd, output, scratch, timeout=120):
    """One fresh observer, isolated environment, actual communicate/wait readback."""
    output, scratch = Path(output), Path(scratch)
    require(not output.exists() and not scratch.exists(), 'record.output.exists')
    scratch.mkdir(parents=True)
    env = credential_free_environment()
    env.update(TMPDIR=str(scratch.resolve()), PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    result = {'exit_code': proc.returncode, 'waited': True, 'timed_out': timed_out,
              'stdout_sha256': digest(stdout), 'stderr_sha256': digest(stderr)}
    write(output, 'process.json', result)
    write(output, 'stdout.bin', stdout)
    write(output, 'stderr.bin', stderr)
    absent = not any(scratch.iterdir())
    write(output, 'cleanup.json', {'owned_residue_absent': absent,
          'scope': 'observer-owned scratch filesystem after actual subprocess wait'})
    if absent:
        scratch.rmdir()
    return result


def run_observers(binary, source, output, build_info=None):
    """Selected disposable controls only; build/source is checked before effects."""
    binary, source, output = Path(binary).resolve(), Path(source).resolve(), Path(output).resolve()
    require(not output.exists(), 'output.exists')
    # A runner may select a newer toolchain than its ambient `go`. Preserve that
    # non-secret selector so `go version -m` can inspect the binary it just built.
    env = credential_free_environment('GOTOOLCHAIN')
    def checked(argv):
        p = subprocess.run(argv, cwd=source, env=env, capture_output=True, timeout=30)
        require(p.returncode == 0, f'source.measurement:{argv[0]}:exit={p.returncode}')
        return p.stdout
    require(checked(['git', 'rev-parse', 'HEAD']).decode().strip() == SOURCE, 'source_revision')
    require(not checked(['git', 'status', '--porcelain']).strip(), 'source.clean')
    if build_info is None:
        build = checked(['go', 'version', '-m', str(binary)])
    else:
        build_path = Path(build_info)
        require(build_path.is_file() and not build_path.is_symlink(), 'build_info.path')
        build_path = build_path.resolve()
        build = build_path.read_bytes()
    require(('vcs.revision=' + SOURCE).encode() in build and b'vcs.modified=false' in build, 'build.source')
    output.mkdir(parents=True)
    write(output, 'subject.json', {'repository': 'ed3c/noodle', 'source_revision': SOURCE,
                                 'binary_sha256': digest(binary.read_bytes())})
    write(output, 'build.txt', build)
    for name, role in layout().items():
        if role in ('observer', 'input_selection', 'input'):
            write(output, name, read_file(FIXTURES, name))
    # Validate pinned inputs before either observer executes.
    for label, sha in OBSERVERS.items():
        require(digest(read_file(output, label + '-observer.py')) == sha, label + '.observer.sha256')
    for name, sha in selected_files().items():
        require(digest(read_file(output, 'preserved-soodles-input/' + name)) == sha, 'input.sha256')
    results = []
    for label in OBSERVERS:
        results.append(record([sys.executable, '-B', str(output / (label + '-observer.py')),
                               str(binary), str(output / label)], output, output / label,
                              output / (label + '-scratch')))
    return {'processes': results, 'authorizes_landing': False}
