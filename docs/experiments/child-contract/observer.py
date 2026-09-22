"""Externally frozen #135 discriminator; production imports are subjects only."""
import hashlib
import json
from pathlib import Path
import sys

SOURCE = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(SOURCE), str(Path(__file__).resolve().parent/'frozen')]
import issue_admission as admission
from test_issue_execution import IssueExecutionTests

rows=[]
for route in ('automatic','supervised'):
    case=IssueExecutionTests()
    case.setUp()
    try:
        case.admit(route)
        proposal=json.loads((case.runtime/'orders-next.json').read_text())
        prompt=json.loads(proposal['orders'][0]['stages'][0]['prompt'])
        expected=admission.parse_contract(case.issue['body'])
        rows.append(dict(case=route+'_complete_contract',passed=prompt.get('contract')==expected,
                         actual_prompt=prompt,expected_contract=expected))
    finally:
        case.doCleanups()

for mutation in ('missing','altered','stale_provider','legal'):
    case=IssueExecutionTests()
    case.setUp()
    try:
        case.admit('supervised')
        case.promote_fixture()
        stage=case.snapshot['state']['orders']['soodles-18']['stages'][0]
        prompt=json.loads(stage['prompt'])
        if mutation=='missing':
            prompt.pop('contract',None)
        elif mutation=='altered':
            prompt['contract']={'write_paths':['foreign.py']}
        elif mutation=='stale_provider':
            case.issue['body']+='\nprovider amendment'
        stage['prompt']=json.dumps(prompt)
        case.save_owner()
        refusal=None
        try:
            result=case.launch()
        except admission.AdmissionRefusal as error:
            refusal=error.invalid
        expected_field='issue.body_sha256' if mutation=='stale_provider' else 'worker.stage.binding'
        passed=(refusal is None and case.effect.exists()) if mutation=='legal' else (
            refusal is not None and refusal['field']==expected_field and not case.effect.exists())
        rows.append(dict(case=mutation,passed=passed,refusal=refusal,worker_effect=case.effect.exists()))
    finally:
        case.doCleanups()
report=dict(observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            source=str(SOURCE),cases=rows,passed=all(r['passed'] for r in rows),
            scope='deterministic fixture, not fresh consumer or live provider',authorizes_landing=False)
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['passed'] else 1)
