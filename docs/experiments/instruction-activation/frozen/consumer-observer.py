import json,sys
from pathlib import Path
root=Path(sys.argv[1]); results={}
for name in ('sample-a','sample-b'):
 d=root/name; result=json.loads((d/'result.json').read_text()); events=[json.loads(x) for x in (root/'observations'/f'{name}.jsonl').read_text().splitlines()]
 expected={'owner':'external-supervisor','required':['raw_results'],'behavior':None,'authorizes_landing':False}
 results[name]={'behavior_pass':result==expected,'reader_events':events,'recipe_reads':sum(x['selection']=='recipe' for x in events),'result':result}
assert not ({'owner':'external-supervisor','required':['raw_results'],'behavior':'PASS','authorizes_landing':False}==expected),'planted invalid result was accepted'
valid=all(x['behavior_pass'] for x in results.values())
delta=results['sample-b']['recipe_reads']-results['sample-a']['recipe_reads']
print(json.dumps({'results':results,'behavior':'PASS' if valid else 'FAIL','context_acquisition_delta':delta,'supported_claim':'scoped reduced recipe acquisition' if valid and delta<0 else 'scoped nonregression' if valid else 'NOT VERIFIED','planted_bad_result':'rejected','observation_scope':'independent reader process events plus consumer result; other platform operations unknown','authorizes_landing':False},indent=2))
