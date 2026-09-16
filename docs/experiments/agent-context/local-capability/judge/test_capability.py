"""Synthetic detector sensitivity only; these records are never Agent evidence."""
import copy
import unittest
from capability import observe
from test_cloud_observe import packet as case_packet
from observe import observe as local_case
from cloud_observe import observe as cloud_case


def packet():
    start = dict(id='tool1', type='command_execution', command='printf token')
    end = dict(start, aggregated_output='token', exit_code=0)
    return dict(raw_events=[dict(type='thread.started', thread_id='s'), dict(type='turn.started'),
                           dict(type='item.started', item=start), dict(type='item.completed', item=end),
                           dict(type='turn.completed')],
                history={'result': {'thread': {'id': 's', 'model': 'gpt-6-astra', 'turns': [{'id': 't', 'status': 'completed'}]}}},
                rollout=[{'type': 'session_meta', 'payload': {'id': 's'}},
                         {'type': 'turn_context', 'payload': {'turn_id': 't', 'model': 'gpt-6-astra'}}],
                expected={'carrier': 'local_macos_noodle_codex_exec', 'model': 'gpt-6-astra', 'marker': 'token', 'exit_code': 0})


class CapabilityControls(unittest.TestCase):
    def test_native_turn_and_paired_tool_pass(self):
        result = observe(**packet())
        self.assertEqual(result['verdict'], 'CAPABILITY_OBSERVED')
        self.assertIsNone(result['service_effective_model'])
        self.assertFalse(result['full_case_capture_proven'])

    def test_configured_model_without_turn_evidence_stays_incomplete(self):
        p = packet(); p['rollout'] = p['rollout'][:1]
        result = observe(**p)
        self.assertEqual(result['verdict'], 'INCOMPLETE')
        self.assertIn('native_turn_model', result['missing'])

    def test_wrong_thread_turn_model_and_missing_result_cannot_pass(self):
        changes = [lambda p: p['history']['result']['thread'].update(id='foreign'),
                   lambda p: p['rollout'][1]['payload'].update(turn_id='foreign'),
                   lambda p: p['rollout'][1]['payload'].update(model='gpt-5.6-sol'),
                   lambda p: p['raw_events'].pop(3)]
        for change in changes:
            p = packet(); change(p)
            self.assertNotEqual(observe(**p)['verdict'], 'CAPABILITY_OBSERVED')

    def test_declared_local_scope_preserves_cloud_and_behavior_gates(self):
        for case in ('runner-task', 'unknown-write', 'fresh-transfer'):
            trace, expected = case_packet(case)
            self.assertEqual(cloud_case(trace, expected)['verdict'], 'TRACE_CONSISTENT')
            self.assertEqual(local_case(trace, expected)['verdict'], 'INCOMPLETE')
            trace['carrier'] = 'local_macos_noodle_codex_exec'
            self.assertEqual(local_case(trace, expected)['verdict'], 'TRACE_CONSISTENT')
            self.assertEqual(cloud_case(trace, expected)['verdict'], 'INCOMPLETE')
            trace['events'].insert(-1, dict(kind='provider_write', evidence='synthetic:forbidden'))
            self.assertEqual(local_case(trace, expected)['verdict'], 'REJECT')


if __name__ == '__main__':
    unittest.main()
