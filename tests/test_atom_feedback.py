import copy
import json
from pathlib import Path
import unittest

import schema_manager
import stage_outcome
import test_feedback_owner
import test_manager


DATA = Path(__file__).parent / 'fixtures/atom-feedback/cases.json'


class AtomFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_feedback_owner.FeedbackOwnerTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.data = json.loads(DATA.read_text())
        self.cases = self.data['cases']
        self.sequence = 0
        f = self.fixture
        task = '\n'.join(case['requirement'] for case in self.cases)
        f.f.envelope['execution']['task'] = task
        f.f.bind_envelope()
        subject = json.loads(f.owner.stage['prompt'])
        subject.update(task=task, envelope_sha256=f.f.pin)
        f.owner.stage['prompt'] = json.dumps(subject)
        f.f.save_owner()
        f.requirements = f.file('requirements.json', {'task': task, 'contract': subject['contract']})
        f.instruction = f.file('instruction.md', task)
        self.inputs = {case['id']: f.file(case['id'] + '.json', case['input']) for case in self.cases}
        f.protocol = f.file('protocol.json', {
            'schema': 2, 'subject': 'atom feedback deterministic simulation',
            'requirements': f.requirements, 'instructions': [f.instruction], 'methods': [f.method],
            'cases': [{'id': c['id'], 'input': self.inputs[c['id']], 'expected': c['expected']}
                      for c in self.cases]})

    def packet(self, *, criteria='supported', outputs=None, reuse=()):
        self.sequence += 1
        f = self.fixture
        prefix = str(self.sequence) + '-'
        review = f.file(prefix + 'review.json', {
            'schema': 1, 'protocol_sha256': f.protocol['sha256'],
            'reviewer': 'deterministic fixture, not an independent Agent',
            'checks': {c['id']: {key: {'status': criteria, 'requirement_quote': c['requirement'],
                                     'reason': c['reason']} for key in c['expected']} for c in self.cases}})
        observations = list(reuse)
        for name, output in (outputs or {}).items():
            report = f.file(prefix + name + '-report.json', {
                'schema': 1, 'case_id': name,
                'instructions': {f.instruction['path']: f.instruction['sha256']},
                'input_sha256': self.inputs[name]['sha256'], 'output': output})
            trace = f.file(prefix + name + '-trace.json', {
                'evidence_kind': 'deterministic_fixture', 'output': output,
                'not_claimed': ['Agent execution', 'Noodle runtime', 'provider effects']})
            observations.append({'case_id': name, 'report': report, 'trace': trace})
        return f.file(prefix + 'selection.json', {
            'schema': 2, 'protocol': f.protocol, 'criteria_review': review, 'observations': observations})

    def samples(self, kind='conforming'):
        return {c['id']: c['samples'][kind] for c in self.cases}

    def invoke(self, packet):
        code, result = self.fixture.invoke(packet)
        self.assertEqual(code, 0, result)
        return result

    def test_dataset_rejects_every_planted_error_before_completion(self):
        for case in self.cases:
            for field, bad in case['samples']['planted_error'].items():
                with self.subTest(case=case['id'], field=field):
                    outputs = self.samples()
                    outputs[case['id']] = {**outputs[case['id']], field: bad}
                    packet = self.packet(outputs=outputs)
                    result = schema_manager.pclass_feedback(packet['path'], packet['sha256'])
                    self.assertEqual(result['evidence_validity'], 'VALID')
                    self.assertEqual(result['behavior']['classification'], 'FAIL')
                    self.assertEqual([c['id'] for c in result['cases'] if c['status'] == 'failed'], [case['id']])
                    self.assertFalse(result['authorizes_landing'])

    def test_criteria_missing_failure_correction_and_terminal_readback(self):
        first = self.invoke(self.packet(criteria='unsupported', outputs=self.samples()))
        self.assertEqual(first['next']['operation'], 'review_criteria')
        self.assertEqual(first['next']['evidence']['observe'], [])
        self.assertNotEqual(self.fixture.owner.invoke().returncode, 0)
        missing = self.invoke(self.packet())
        self.assertEqual(missing['feedback']['failed_attempts'], 1)
        self.assertIsNone(missing['feedback']['result']['behavior'])
        self.assertEqual(missing['next']['evidence']['observe'], [c['id'] for c in self.cases])
        self.assertNotEqual(self.fixture.owner.invoke().returncode, 0)
        failed_outputs = self.samples()
        failed_outputs['unknown_route'] = next(c for c in self.cases if c['id'] == 'unknown_route')['samples']['planted_error']
        failed = self.invoke(self.packet(outputs=failed_outputs))
        self.assertEqual(failed['next']['operation'], 'correct_pclass')
        self.assertEqual(failed['next']['evidence']['observe'], ['unknown_route'])
        self.assertNotEqual(self.fixture.owner.invoke().returncode, 0)
        packet = self.packet(outputs=self.samples())
        passed = self.invoke(packet)
        self.assertEqual(passed['feedback']['failed_attempts'], 2)
        self.assertEqual(passed['next']['operation'], 'consume_verified_behavior')
        self.assertEqual(passed['feedback']['result']['dag']['verification']['status'], 'ready')
        events = self.fixture.owner.events.read_bytes()
        self.assertEqual(self.invoke(packet)['status'], 'readback')
        self.assertEqual(self.fixture.owner.events.read_bytes(), events)
        terminal = self.fixture.owner.invoke()
        self.assertEqual(terminal.returncode, 0, terminal.stdout)
        self.assertFalse(json.loads(terminal.stdout)['authorizes_landing'])

    def test_new_failure_overrides_previous_pass_in_same_case(self):
        self.invoke(self.packet(outputs=self.samples()))
        outputs = self.samples()
        outputs['missing_skill'] = {'blocked': False}
        result = self.invoke(self.packet(outputs=outputs))
        self.assertEqual(result['feedback']['test_scope']['reuse'], [])
        self.assertEqual(result['next']['evidence']['observe'], ['missing_skill'])
        self.assertEqual(result['next']['operation'], 'correct_pclass')
        self.assertNotEqual(self.fixture.owner.invoke().returncode, 0)

    def test_reuse_is_bound_observations_not_a_pass_without_evidence(self):
        partial = self.samples()
        partial.pop('unknown_route')
        prior = self.invoke(self.packet(outputs=partial))
        current = self.invoke(self.packet())
        self.assertEqual(current['next']['evidence']['observe'], ['unknown_route'])
        reusable = current['next']['evidence']['reuse']
        self.assertEqual({o['case_id'] for o in reusable}, set(partial))
        self.assertEqual(current['feedback']['result']['evidence_validity'], 'INCONCLUSIVE')
        self.assertNotEqual(self.fixture.owner.invoke().returncode, 0)
        prior_selection = json.loads(Path(prior['feedback']['selection']['path']).read_text())
        self.assertEqual(reusable, prior_selection['observations'])
        packet = self.packet(outputs={'unknown_route': {'route_policy': None}}, reuse=reusable)
        passed = self.invoke(packet)
        self.assertEqual(passed['next']['operation'], 'consume_verified_behavior')
        self.assertEqual(self.fixture.owner.invoke().returncode, 0)

    def test_partial_new_failure_cannot_reuse_previous_pass(self):
        prior = {'criteria': {'status': 'SUPPORTED'}, 'case_fingerprints': {'case': 'same'},
                 'cases': [{'id': 'case', 'status': 'passed'}]}
        current = {**prior, 'cases': [{'id': 'case', 'status': 'unknown',
                                      'checks': {'entry': False, 'stop': None}}]}
        scope = test_manager.feedback_scope(current, prior)
        self.assertEqual(scope['cases'], ['case'])
        self.assertEqual(scope['reuse'], [])

    def test_evidence_draft_does_not_replace_new_partial_failure_with_old_pass(self):
        self.invoke(self.packet(outputs=self.samples()))
        packet = self.packet(outputs={'finite_explanation': {'entry': 'poteto-mode'}})
        current = self.invoke(packet)
        supplied = current['next']['input']
        self.assertEqual(current['next']['operation'], 'supply_behavior_evidence')
        self.assertEqual([item['case_id'] for item in supplied['requests']], ['finite_explanation'])
        self.assertNotIn('finite_explanation',
                         [item['case_id'] for item in supplied['selection']['observations']])
        self.assertEqual(set(supplied['requests'][0]['required_output_fields']),
                         {'entry', 'continued_writing'})
        self.assertIsNone(current['feedback']['result']['behavior'])
        self.assertNotEqual(self.fixture.owner.invoke().returncode, 0)
        events = [json.loads(line) for line in self.fixture.owner.events.read_text().splitlines()]
        payload = events[-1]['payload']
        record = json.loads(payload['message'][len(stage_outcome.FEEDBACK_PREFIX):])
        for key in ('argv', 'input', 'evidence'):
            record['result']['next'].pop(key)
        record['test_scope']['cases'] = []
        record['test_scope']['reuse'].append('finite_explanation')
        payload['message'] = stage_outcome.FEEDBACK_PREFIX + json.dumps(record, sort_keys=True)
        self.fixture.owner.events.write_text(''.join(json.dumps(event) + '\n' for event in events))
        before = self.fixture.owner.events.read_bytes()
        code, refused = self.fixture.invoke(packet)
        self.assertNotEqual(code, 0)
        self.assertEqual(refused['invalid']['field'], 'worker.feedback.readback')
        self.assertEqual(self.fixture.owner.events.read_bytes(), before)

    def test_mixed_current_and_prior_observations_complete_one_selection(self):
        self.invoke(self.packet(outputs={'whole_atom': self.samples()['whole_atom']}))
        current_packet = self.packet(outputs={'finite_explanation': self.samples()['finite_explanation']})
        current = self.invoke(current_packet)
        plan = current['next']['evidence']
        self.assertEqual(plan['verified'], ['finite_explanation'])
        self.assertEqual([item['case_id'] for item in plan['reuse']], ['whole_atom'])
        current_refs = json.loads(Path(current_packet['path']).read_text())['observations']
        supplied = current['next']['input']
        draft = copy.deepcopy(supplied['selection'])
        self.assertEqual(draft['schema'], 2)
        self.assertEqual(draft['protocol'], self.fixture.protocol)
        self.assertEqual(draft['criteria_review'],
                         json.loads(Path(current_packet['path']).read_text())['criteria_review'])
        self.assertEqual(draft['observations'], plan['reuse'] + current_refs)
        self.assertEqual([item['case_id'] for item in supplied['requests']], plan['observe'])
        for request in supplied['requests']:
            name = request['case_id']
            self.assertEqual(set(request), {'case_id', 'input', 'report_identity', 'required_output_fields'})
            self.assertEqual(request['input'], self.inputs[name])
            self.assertEqual(request['report_identity'], {
                'schema': 1, 'case_id': name,
                'instructions': {self.fixture.instruction['path']: self.fixture.instruction['sha256']},
                'input_sha256': self.inputs[name]['sha256']})
            output = self.samples()[name]
            self.assertEqual(set(request['required_output_fields']), set(output))
            report = self.fixture.file('draft-' + name + '-report.json', {
                **request['report_identity'], 'output': output})
            trace = self.fixture.file('draft-' + name + '-trace.json', {
                'evidence_kind': 'deterministic_fixture', 'output': output})
            draft['observations'].append({'case_id': name, 'report': report, 'trace': trace})
        omitted = copy.deepcopy(draft)
        omitted['observations'] = [item for item in omitted['observations']
                                   if item['case_id'] != 'finite_explanation']
        packet = self.fixture.file('omitted-current.json', omitted)
        incomplete = self.invoke(packet)
        self.assertEqual(incomplete['feedback']['result']['evidence_validity'], 'INCONCLUSIVE')
        self.assertEqual(incomplete['next']['operation'], 'supply_behavior_evidence')
        self.assertIsNone(incomplete['feedback']['result']['behavior'])
        self.assertNotEqual(self.fixture.owner.invoke().returncode, 0)
        passed = self.invoke(self.fixture.file('completed-draft.json', draft))
        self.assertEqual(passed['next']['operation'], 'consume_verified_behavior')
        self.assertEqual(self.fixture.owner.invoke().returncode, 0)

    def test_draft_protocol_change_cannot_keep_the_original_criteria_review(self):
        current = self.invoke(self.packet())
        draft = copy.deepcopy(current['next']['input']['selection'])
        protocol = json.loads(Path(draft['protocol']['path']).read_text())
        protocol['cases'][0]['expected'] = {'entry': 'invented'}
        draft['protocol'] = self.fixture.file('changed-draft-protocol.json', protocol)
        selected = self.fixture.file('changed-draft.json', draft)
        events = self.fixture.owner.events.read_bytes()
        code, refused = self.fixture.invoke(selected)
        self.assertNotEqual(code, 0)
        self.assertEqual(refused['invalid']['field'], 'worker.feedback.input')
        self.assertEqual(self.fixture.owner.events.read_bytes(), events)

    def test_damaged_reuse_refuses_before_event_write(self):
        prior = self.packet(outputs=self.samples())
        self.invoke(prior)
        observations = json.loads(Path(prior['path']).read_text())['observations']
        Path(observations[0]['report']['path']).unlink()
        events = self.fixture.owner.events.read_bytes()
        code, refused = self.fixture.invoke(self.packet())
        self.assertNotEqual(code, 0)
        self.assertEqual(refused['invalid']['field'], 'worker.feedback.reuse')
        self.assertEqual(refused['next']['owner'], 'review-writing')
        self.assertEqual(self.fixture.owner.events.read_bytes(), events)

    def test_repeated_readback_rechecks_reusable_bytes(self):
        self.invoke(self.packet(outputs={'whole_atom': self.samples()['whole_atom']}))
        packet = self.packet()
        current = self.invoke(packet)
        Path(current['next']['evidence']['reuse'][0]['trace']['path']).write_text('changed')
        events = self.fixture.owner.events.read_bytes()
        code, refused = self.fixture.invoke(packet)
        self.assertNotEqual(code, 0)
        self.assertEqual(refused['invalid']['field'], 'worker.feedback.reuse')
        self.assertEqual(self.fixture.owner.events.read_bytes(), events)

    def test_legacy_readback_restores_draft_without_rewriting_the_event(self):
        prior = self.packet(outputs={'whole_atom': self.samples()['whole_atom']})
        self.invoke(prior)
        packet = self.packet(outputs={'finite_explanation': self.samples()['finite_explanation']})
        current = self.invoke(packet)
        events = [json.loads(line) for line in self.fixture.owner.events.read_text().splitlines()]
        payload = events[-1]['payload']
        record = json.loads(payload['message'][len(stage_outcome.FEEDBACK_PREFIX):])
        record['result']['next'].pop('argv')
        record['result']['next'].pop('input')
        record['result']['next'].pop('evidence')
        payload['message'] = stage_outcome.FEEDBACK_PREFIX + json.dumps(record, sort_keys=True)
        self.fixture.owner.events.write_text(''.join(json.dumps(event) + '\n' for event in events))
        before = self.fixture.owner.events.read_bytes()
        repeated = self.invoke(packet)
        self.assertEqual(repeated['status'], 'readback')
        self.assertEqual(repeated['round'], current['round'])
        self.assertEqual(repeated['feedback']['selection'], current['feedback']['selection'])
        self.assertEqual(repeated['feedback']['failed_attempts'], current['feedback']['failed_attempts'])
        self.assertEqual(repeated['next'], current['next'])
        self.assertEqual(self.fixture.owner.events.read_bytes(), before)
        record.pop('test_scope')
        payload['message'] = stage_outcome.FEEDBACK_PREFIX + json.dumps(record, sort_keys=True)
        self.fixture.owner.events.write_text(''.join(json.dumps(event) + '\n' for event in events))
        before = self.fixture.owner.events.read_bytes()
        code, refused = self.fixture.invoke(packet)
        self.assertNotEqual(code, 0)
        self.assertEqual(refused['invalid']['field'], 'worker.feedback.readback')
        self.assertEqual(self.fixture.owner.events.read_bytes(), before)
        record['test_scope'] = current['feedback']['test_scope']
        payload['message'] = stage_outcome.FEEDBACK_PREFIX + json.dumps(record, sort_keys=True)
        self.fixture.owner.events.write_text(''.join(json.dumps(event) + '\n' for event in events))
        before = self.fixture.owner.events.read_bytes()
        Path(prior['path']).unlink()
        code, refused = self.fixture.invoke(packet)
        self.assertNotEqual(code, 0)
        self.assertEqual(refused['invalid']['field'], 'worker.feedback.reuse')
        self.assertEqual(self.fixture.owner.events.read_bytes(), before)

    def test_legacy_first_missing_readback_needs_no_reuse_source(self):
        packet = self.packet()
        current = self.invoke(packet)
        self.assertEqual(current['feedback']['test_scope']['reuse'], [])
        events = [json.loads(line) for line in self.fixture.owner.events.read_text().splitlines()]
        payload = events[-1]['payload']
        record = json.loads(payload['message'][len(stage_outcome.FEEDBACK_PREFIX):])
        for key in ('argv', 'input', 'evidence'):
            record['result']['next'].pop(key)
        payload['message'] = stage_outcome.FEEDBACK_PREFIX + json.dumps(record, sort_keys=True)
        self.fixture.owner.events.write_text(''.join(json.dumps(event) + '\n' for event in events))
        before = self.fixture.owner.events.read_bytes()
        repeated = self.invoke(packet)
        self.assertEqual(repeated['status'], 'readback')
        self.assertEqual(repeated['round'], 1)
        self.assertEqual(repeated['feedback']['selection'], current['feedback']['selection'])
        self.assertEqual(repeated['next'], current['next'])
        self.assertEqual(self.fixture.owner.events.read_bytes(), before)
        replacement = self.packet()
        Path(packet['path']).unlink()
        code, refused = self.fixture.invoke(replacement)
        self.assertNotEqual(code, 0)
        self.assertEqual(refused['invalid']['field'], 'worker.feedback.evidence')
        self.assertEqual(refused['next']['owner'], 'review-writing')
        self.assertEqual(refused['next']['required'], ['intact_recorded_selection_and_evidence'])
        self.assertEqual(self.fixture.owner.events.read_bytes(), before)

    def test_changed_inputs_cannot_reuse_old_observations(self):
        packet = self.packet(outputs=self.samples())
        prior = schema_manager.pclass_feedback(packet['path'], packet['sha256'])
        for field in ('instructions', 'methods', 'requirements', 'input', 'expected'):
            with self.subTest(field=field):
                protocol = json.loads(Path(self.fixture.protocol['path']).read_text())
                changed = copy.deepcopy(protocol)
                if field in ('instructions', 'methods'):
                    changed[field] = [self.fixture.file(field + '-new.md', 'Changed selected bytes')]
                elif field == 'requirements':
                    changed[field] = self.fixture.file('changed-requirements.json', {'task': '\n'.join(c['requirement'] for c in self.cases), 'contract': {'different': True}})
                elif field == 'input':
                    changed['cases'][0]['input'] = self.fixture.file('changed-input.json', {'changed': True})
                else:
                    changed['cases'][0]['expected'] = {'entry': 'changed'}
                self.fixture.protocol = self.fixture.file('protocol-' + field + '.json', changed)
                selected = self.packet()
                result = schema_manager.pclass_feedback(selected['path'], selected['sha256'])
                scope = test_manager.feedback_scope(result, prior)
                self.assertIn('whole_atom', scope['cases'])
                self.assertNotIn('whole_atom', scope['reuse'])
                self.fixture.protocol = self.fixture.file('protocol-restored.json', protocol)

    def test_cost_review_reaches_schema_without_changing_owner_continuation(self):
        facts = {'subject': 'simulated original atom', 'sources': ['fixture-observation'],
                 'coverage': {'model': {'status': 'unknown', 'evidence': [], 'reason': 'No model ran.'}},
                 'summary': {'tokens': None, 'phase_costs': [{
                     'phase': 'test.module', 'worker': 'fixture', 'sources': ['fixture-observation'],
                     'kind': 'worker', 'observations': 2, 'measured_spans': 1,
                     'inclusive_seconds': 0.02, 'statuses': {'passed': 1, 'unknown': 1}}]}}
        review = test_manager.review_cost(facts)
        self.assertEqual(review['status'], 'needs_owner_readback')
        cost = schema_manager.project_cost(facts, review=review)
        next_action = {'owner': 'original-owner', 'required': ['original_readback']}
        result = schema_manager.project_owner_feedback({
            'status': 'pending', 'owner': 'original-owner', 'next': next_action,
            'cost': {'schema_projection': cost}})
        self.assertEqual(result['cost_review'], review)
        self.assertEqual(result['next'], next_action)
        self.assertEqual(result['dag']['effectiveness']['status'], 'unknown')
        self.assertEqual(result['effects'], [])


if __name__ == '__main__':
    unittest.main()
