import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
sys.path.insert(0, str(SOURCE))
import landing
spec = importlib.util.spec_from_file_location('fixture_source', SOURCE / 'tests/test_landing.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def setup(name, case, arm):
    root = ROOT / name
    root.mkdir()
    instructions = root / 'instructions'
    for rel in ['AGENTS.md', '.agents/skills/verify-soodles/SKILL.md',
                '.agents/skills/verify-soodles/features/supervised-delivery.md',
                '.agents/skills/verify-soodles/features/delivery-recovery.md',
                'contracts/system-v1.md']:
        dest = instructions / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'treatment-AGENTS.md' if rel == 'AGENTS.md' and arm == 'treatment' else SOURCE / rel, dest)
    fixture = module.LandingTests()
    fixture.setUp()
    checkpoint = root / 'checkpoint.json'
    landing.start(fixture.claim, fixture.snapshot, checkpoint)
    landing.advance(checkpoint, fixture.snapshot)
    historical = landing.dispatch(checkpoint, fixture.snapshot)['request']
    initial = copy.deepcopy(fixture.snapshot)
    supplied = {}
    if case == 'recovery':
        fixture.merged()
        initial = copy.deepcopy(fixture.snapshot)
        correction = initial.pop('merge_commit')
        dump(root / 'commit-readback.json', correction)
        supplied['commit-readback.json'] = 'Supervisor-supplied provider-shaped commit response; fixture only.'
    if case == 'identity':
        initial['pr']['head']['repo']['full_name'] = 'fixture/foreign'
    dump(root / 'readback.json', initial)
    shutil.copyfile(checkpoint, root / 'checkpoint-before.json')
    dump(root / 'prior-handoff.json', {'subject_issue': 1, 'subject_pr': 2,
        'historical_request': historical, 'note': 'Earlier supervisor recorded this offered request.'})
    task = {'originating_issue': 'ed3c/soodles#49',
        'task': 'Review this supplied delivery subject through its current owner. Determine its current status, complete any continuation possible from the supplied inputs within scope, and return the next required observation with evidence.',
        'carrier': 'native cloud consumer',
        'scope': 'Disposable provider fixtures only. Owner transitions may modify the supplied checkpoint. No live provider transport, credentials, worktree operations or production effects are authorized. Do not manually edit the checkpoint.',
        'owner_entry': str(SOURCE / 'soodles.py'),
        'checkpoint': str(checkpoint), 'provider_readback': str(root / 'readback.json'),
        'prior_handoff': str(root / 'prior-handoff.json'),
        'additional_inputs': supplied,
        'instructions': str(instructions),
        'receipt_path': str(root / 'receipt.json'),
        'receipt_fields': ['originating_issue', 'subject', 'classification', 'owner', 'next', 'evidence', 'limitations'],
        'recording': 'Record every investigation command, including document reads, through the supplied recorder with a fresh label. Preserve all failures. Do not inspect other trial directories or coordinator files.'}
    dump(root / 'task.json', task)
    fixture.doCleanups()
    return {'name': name, 'case': case, 'arm': arm,
        'checkpoint_before': digest(root / 'checkpoint-before.json'),
        'task_sha256': digest(root / 'task.json'),
        'instructions': {str(p.relative_to(instructions)): digest(p) for p in instructions.rglob('*') if p.is_file()}}

if __name__ == '__main__':
    runs = [setup(n, case, arm) for n, case, arm in [
        ('a','pending','baseline'), ('b','pending','treatment'),
        ('c','recovery','treatment'), ('d','recovery','baseline'),
        ('e','identity','baseline'), ('f','identity','treatment')]]
    dump(ROOT / 'selection.json', {'issue':49,'base':'defc5f41153837f4db5ee0858fd03c9029523c6c',
        'runs':runs,'source':{str(p.relative_to(SOURCE)):digest(p) for p in SOURCE.rglob('*') if p.is_file() and '__pycache__' not in str(p)},
        'task_difference':'Only per-run absolute paths differ within each pair; assignment is outside consumer packet.',
        'native_model_provenance':None,'full_native_trace':None,'authorizes_landing':False})
    print(json.dumps({'runs':len(runs),'source':str(SOURCE)}))
