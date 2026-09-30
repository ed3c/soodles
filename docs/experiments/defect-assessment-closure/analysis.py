"""Portable integrity and reported shell-call replay; not a semantic judge."""
import hashlib
import json
from pathlib import Path
import statistics
import tarfile

ROOT = Path(__file__).resolve().parent

def analyze(root=ROOT):
    records = []
    cost = {}
    index_paths = sorted((root / 'archives').glob('*index.json'))
    if not index_paths:
        raise ValueError('no evidence indexes')
    for index_path in index_paths:
        index = json.loads(index_path.read_text())
        archive = root / 'archives' / Path(index['archive']).name
        if hashlib.sha256(archive.read_bytes()).hexdigest() != index['sha256']:
            raise ValueError('archive digest mismatch: ' + archive.name)
        expected = {entry.get('path', entry.get('member')): entry for entry in index['members']}
        if len(expected) != len(index['members']):
            raise ValueError('duplicate indexed member')
        with tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
            if len({m.name for m in members}) != len(members) or set(expected) != {m.name for m in members}:
                raise ValueError('archive member set mismatch')
            for member in members:
                name = Path(member.name)
                if not member.isfile() or name.is_absolute() or '..' in name.parts:
                    raise ValueError('unsafe archive member')
                if name.name == 'auth.json' or name.suffix == '.pem':
                    raise ValueError('credential file must not be archived')
                data = tar.extractfile(member).read()
                pin = expected[member.name]
                if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
                    raise ValueError('member digest mismatch: ' + member.name)
                if archive.name == 'create-confirmation.tar.gz' and member.name.endswith('/raw/stdout.bin'):
                    events = [json.loads(line) for line in data.splitlines() if line.startswith(b'{')]
                    count = sum(e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'command_execution' for e in events)
                    label = member.name.split('/')[1]
                    arm = 'baseline' if label.startswith('confirm-baseline-') else 'r03'
                    cost.setdefault(arm, []).append(count)
        records.append({'archive': archive.name, 'members': len(members), 'runs': len(index.get('runs', []))})
    if set(cost) != {'baseline', 'r03'} or any(len(v) != 3 for v in cost.values()):
        raise ValueError('confirmation membership mismatch')
    medians = {arm: statistics.median(values) for arm, values in cost.items()}
    saved = json.loads((root / 'create/confirmation/summary.json').read_text())
    if medians != saved['median_shell_calls_including_carrier']:
        raise ValueError('reported confirmation costs do not match raw events')
    return {'archives': records, 'confirmation_shell_call_medians': medians,
            'efficiency_target_met': medians['r03'] <= medians['baseline'] * 0.8,
            'scope': 'byte integrity and reported shell calls only; no semantic or landing authority',
            'authorizes_landing': False}

if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2))
