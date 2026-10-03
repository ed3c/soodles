"""Execute emitted CLI continuations with synthetic provider readbacks."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import soodles
import test_landing

ROOT = Path(__file__).resolve().parents[1]


class LandingContinuationTests(unittest.TestCase):
    def test_emitted_argv_requires_fresh_readback_and_never_repeats_unknown_writes(self):
        fixture = test_landing.LandingTests()
        fixture.setUp()
        fixture.snapshot['pr']['base']['sha'] = '9' * 40
        self.addCleanup(fixture.doCleanups)
        lane = Path(fixture.temp.name).resolve()
        checkpoint = lane / 'checkpoint with spaces.json'
        readback = lane / 'readback with spaces.json'
        claim_path = lane / 'claim with spaces.json'
        claim = dict(fixture.claim)
        claim.pop('control_root')
        claim_path.write_text(json.dumps(claim))

        def invoke(argv, snapshot, code=0):
            readback.write_text(json.dumps(snapshot))
            process = subprocess.run(argv, cwd=lane, env=soodles.clean_env(),
                                     capture_output=True, text=True, timeout=20)
            self.assertEqual(process.returncode, code, process.stderr + process.stdout)
            return json.loads(process.stdout)

        def continuation(result, operation):
            next_action = result['next']
            self.assertEqual(next_action['operation'], operation)
            self.assertEqual(next_action['required'], ['readback'])
            self.assertEqual(next_action['known']['checkpoint'], str(checkpoint))
            self.assertEqual(next_action['known']['readback'], str(readback))
            self.assertIn('pr', next_action['requests'])
            self.assertEqual(next_action['argv'], [sys.executable, '-B', str(ROOT / 'soodles.py'),
                                                   'landing', operation, str(checkpoint), str(readback)])
            return next_action['argv']

        result = invoke([sys.executable, '-B', str(ROOT / 'soodles.py'), 'landing', 'start',
                         str(claim_path), str(readback), str(checkpoint)], fixture.snapshot)
        advance = continuation(result, 'advance')
        prepared = invoke(advance, fixture.snapshot)
        dispatch = continuation(prepared, 'dispatch')
        offered = invoke(dispatch, fixture.snapshot)
        self.assertEqual(offered['request']['expected_head_sha'], claim['head'])
        advance = continuation(offered, 'advance')
        pending = invoke(advance, fixture.snapshot)
        self.assertNotIn('request', pending)
        self.assertNotEqual(pending.get('classification'), 'RESOLVED')

        before = checkpoint.read_bytes()
        self.assertNotIn('request', invoke(dispatch, fixture.snapshot, code=1))
        wrong = copy.deepcopy(fixture.snapshot)
        wrong['pr']['head']['sha'] = 'f' * 40
        self.assertNotIn('request', invoke(advance, wrong, code=1))
        self.assertEqual(checkpoint.read_bytes(), before)

        fixture.merged()
        merged = fixture.snapshot.pop('merge_commit')
        missing = invoke(advance, fixture.snapshot, code=1)
        self.assertNotIn('request', missing)
        self.assertIn('merge_commit', missing['next']['requests'])
        self.assertEqual(checkpoint.read_bytes(), before)
        advance = continuation(missing, 'advance')
        fixture.snapshot['merge_commit'] = merged
        prepared = invoke(advance, fixture.snapshot)
        offered = invoke(continuation(prepared, 'dispatch'), fixture.snapshot)
        self.assertIn('request', offered)
        advance = continuation(offered, 'advance')
        self.assertNotIn('request', invoke(advance, fixture.snapshot))
        fixture.snapshot['issue'].update(state='closed', state_reason='completed', closed_at='fixture')
        fixture.snapshot['branch']['commit']['sha'] = 'd' * 40
        result = invoke(advance, fixture.snapshot)
        self.assertEqual(result['classification'], 'RESOLVED')
        before = checkpoint.read_bytes()
        self.assertNotIn('request', invoke(advance, fixture.snapshot))
        self.assertEqual(checkpoint.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
