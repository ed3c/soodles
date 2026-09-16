import json
from pathlib import Path
import subprocess
import sys

subject = Path('/Users/neon/soodles/.worktrees/soodles-18-0-execute')
sys.path[:0] = [str(subject / 'tests'), str(subject)]
from test_issue_execution import IssueExecutionTests
from issue_admission import AdmissionRefusal
from issue_execution import refusal_output

receipt = {
    'subject_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=subject, text=True).strip(),
    'scope': 'Actual admission functions over provider/owner fixtures; no live Agent or provider effect',
    'authorizes_landing': False,
    'cases': [],
}
for route in ('automatic', 'supervised'):
    fixture = IssueExecutionTests()
    fixture.setUp()
    try:
        original = fixture.issue['body']
        fixture.issue['body'] += '\nchanged after envelope binding'
        try:
            fixture.admit(route)
            raise AssertionError('stale Issue unexpectedly admitted')
        except AdmissionRefusal as error:
            result = refusal_output(error, route)
        before_effects = not (fixture.runtime / 'orders-next.json').exists() and not fixture.effect.exists()
        explicit_reentry = bool(result['next'].get('operation')) and bool(result['next'].get('help_argv'))
        fixture.issue['body'] = original
        valid = fixture.admit(route)
        receipt['cases'].append({
            'route': route,
            'stale_refusal': result,
            'forbidden_effects_absent': before_effects,
            'correct_rejection_control': 'GREEN' if before_effects and result['invalid']['field'] == 'issue.body_sha256' else 'RED',
            'continuation_guidance_control': 'GREEN' if explicit_reentry else 'RED',
            'continuation_guidance_assertion': 'Named existing operation and supported entry help are present; neither authorizes a retry',
            'legal_current_body_control': 'GREEN' if valid['action'] == 'proposal_pending' and valid['published'] else 'RED',
            'cure': 'NOT_IMPLEMENTED_OR_TESTED',
        })
    finally:
        fixture.doCleanups()
    receipt['cases'][-1]['fixture_cleanup'] = not fixture.directory.exists()
receipt['classification'] = 'LOCAL_CONTINUATION_GUIDANCE_GAP_OBSERVED'
print(json.dumps(receipt, indent=2))
