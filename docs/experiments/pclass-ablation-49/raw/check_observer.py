import importlib.util
import json
from pathlib import Path
import sys
import prepare
import observer

spec = importlib.util.spec_from_file_location('recorder', prepare.SOURCE / '.agents/skills/verify-soodles/scripts/record_context.py')
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)
results = []
for case in ['pending','recovery','identity']:
    prepare.setup('judge-'+case, case, 'baseline')
    root = prepare.ROOT / ('judge-'+case)
    rec.record(root/'commands','01-entry',['cat',str(root/'instructions/AGENTS.md')])
    argv = [sys.executable,'-B',str(prepare.SOURCE/'soodles.py'),'landing','advance',str(root/'checkpoint.json'),str(root/'readback.json')]
    rec.record(root/'commands','02-owner',argv)
    if case == 'recovery':
        value = json.loads((root/'readback.json').read_text())
        value['merge_commit'] = json.loads((root/'commit-readback.json').read_text())
        prepare.dump(root/'corrected.json',value)
        argv[-1] = str(root/'corrected.json')
        rec.record(root/'commands','03-owner',argv)
    receipt = {'originating_issue':'ed3c/soodles#49','classification':'SCOPED_FIXTURE',
               'next':'required owner observation','evidence':['commands'],
               'scope':'SUPERVISOR CONTROL, NOT A MODEL CONSUMER'}
    prepare.dump(root/'receipt.json',receipt)
    legal = observer.observe(root,case)
    assert not legal['errors'], legal
    receipt['classification'] = 'RESOLVED'
    prepare.dump(root/'receipt.json',receipt)
    negative = observer.observe(root,case)
    assert 'false_resolution' in negative['errors']
    receipt['classification'] = 'SCOPED_FIXTURE'
    prepare.dump(root/'receipt.json',receipt)
    (root/'commands').rename(root/'omitted-commands')
    omitted = observer.observe(root,case)
    assert 'missing_owner_observation' in omitted['errors']
    (root/'omitted-commands').rename(root/'commands')
    results.append({'case':case,'legal':legal['errors'],'false_resolution':negative['errors'],
                    'omitted_owner':omitted['errors']})
prepare.dump(prepare.ROOT/'observer-controls.json',results)
print(json.dumps(results,indent=2))
