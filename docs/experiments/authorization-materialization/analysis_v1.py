#!/usr/bin/env python3
"""Aggregate preserved observations; never select an evaluator or authorize effects."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
baseline = {r['case']:r for r in json.loads((HERE/'behavior/r01-observed.json').read_text()) if r['arm']=='baseline'}
treatment = {r['case']:r for r in json.loads((HERE/'behavior/r03-observed.json').read_text())}
confirmation = json.loads((HERE/'behavior/confirmation-observed.json').read_text())
rows=[]
for case in ('schema2','schema3'):
    a,b=baseline[case],treatment[case]
    rows.append({'case':case,'baseline_operations':a['captured_operation_count'],
                 'treatment_operations':b['captured_operation_count'],
                 'baseline_observed_gates':a['gates'],'treatment_observed_gates':b['gates']})
rows.append({'case':'publisher_changed','baseline_operations':confirmation[0]['captured_operation_count'],
             'treatment_operations':confirmation[1]['captured_operation_count'],
             'baseline_observed_gates':confirmation[0]['gates'],'treatment_observed_gates':confirmation[1]['gates']})
print(json.dumps({'rows':rows,'v1_formal_adoption':'INCONCLUSIVE',
                  'reason':'Original all bounded gates wording includes the observed failed baseline refusal-residue gate; no retroactive waiver.',
                  'scope':'captured native consumer operations and independently read final bytes, not full model cost or universal nondegradation',
                  'authorizes_landing':False},indent=2))
