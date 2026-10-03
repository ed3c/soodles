"""Feedback uses the original event writer and completion boundary."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest

import stage_outcome
import test_stage_outcome
import test_issue_execution
import issue_execution
from issue_admission import AdmissionRefusal
import handoff_oracle
import test_manager


class FeedbackOwnerTests(unittest.TestCase):
    def setUp(self):
        self.owner = test_stage_outcome.StageOutcomeTests('runTest')
        self.owner.setUp()
        self.addCleanup(self.owner.doCleanups)
        self.f = self.owner.fixture
        self.directory = self.f.directory
        self.instruction = self.file('instruction.md', 'Keep missing evidence incomplete.')
        self.f.envelope['execution']['task'] = 'Keep missing evidence incomplete.'
        self.f.bind_envelope()
        subject = json.loads(self.owner.stage['prompt'])
        subject.update(task=self.f.envelope['execution']['task'], envelope_sha256=self.f.pin)
        self.owner.stage['prompt'] = json.dumps(subject)
        self.f.save_owner()
        self.requirements = self.file('requirements.txt', {'task': subject['task'], 'contract': subject['contract']})
        self.method = self.file('method.md', 'Compare observed completion with the requirement.')
        self.task = self.file('input.json', {'evidence': None})
        self.protocol = self.file('protocol.json', {
            'schema': 2, 'subject': 'missing evidence completion',
            'requirements': self.requirements, 'instructions': [self.instruction], 'methods': [self.method],
            'cases': [{'id': 'missing', 'input': self.task, 'expected': {'complete': False}}]})

    def file(self, name, value):
        p = self.directory / name
        p.write_text(value if isinstance(value, str) else json.dumps(value))
        return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

    def packet(self, status='supported', complete=False, quote=None):
        review = self.file('review-' + str(status) + str(complete) + '.json', {
            'schema': 1, 'protocol_sha256': self.protocol['sha256'], 'reviewer': 'fixture observer',
            'checks': {'missing': {'complete': {'status': status,
                'requirement_quote': quote if quote is not None else 'Keep missing evidence incomplete.',
                'reason': 'The selected task has no evidence; completed would contradict the requirement.'}}}})
        report = self.file('report-' + str(complete) + '.json', {
            'schema': 1, 'case_id': 'missing',
            'instructions': {self.instruction['path']: self.instruction['sha256']},
            'input_sha256': self.task['sha256'], 'output': {'complete': complete}})
        trace = self.file('trace-' + str(complete) + '.txt', 'Fixture output: complete=' + str(complete))
        return self.file('selection-' + status + str(complete) + '.json', {
            'schema': 2, 'protocol': self.protocol, 'criteria_review': review,
            'observations': [{'case_id': 'missing', 'report': report, 'trace': trace}]})

    def invoke(self, packet):
        run = subprocess.run([str(Path(stage_outcome.__file__).with_name('stage-outcome')),
            'feedback', packet['path'], packet['sha256']], cwd=self.f.worktree,
            env={**os.environ, **self.f.env}, capture_output=True, text=True)
        value = json.loads(run.stdout)
        self.assertFalse(value['authorizes_landing'])
        return run.returncode, value

    def instruction_packet(self, source):
        target = self.f.worktree / 'contracts' / 'instruction.md'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('Keep missing evidence incomplete.')
        source.parent.mkdir(parents=True, exist_ok=True)
        self.instruction = self.file(str(source), target.read_text())
        protocol = json.loads(Path(self.protocol['path']).read_text())
        protocol['instructions'] = [self.instruction]
        self.protocol = self.file('protocol.json', protocol)
        return self.packet(), target

    def registered_source(self):
        source = self.directory / 'prior-worktree'
        self.f.git('worktree', 'add', '--detach', str(source))
        return source

    def record_pass(self, packet):
        code, receipt = self.invoke(packet)
        self.assertEqual(code, 0, receipt)
        self.assertEqual(receipt['feedback']['result']['criteria']['status'], 'SUPPORTED')
        self.assertEqual(receipt['feedback']['result']['evidence_validity'], 'VALID')
        self.assertEqual(receipt['feedback']['result']['behavior']['classification'], 'PASS')

    def assert_completion_refused(self, field):
        receipt = self.owner.refused(self.owner.invoke(), effects=1)
        self.assertEqual(receipt['invalid']['field'], field)
        return receipt

    def test_same_absolute_instruction_path_completes(self):
        packet, _ = self.instruction_packet(self.f.worktree / 'contracts' / 'instruction.md')
        self.record_pass(packet)
        result = self.owner.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['event']['payload']['outcome'], 'completed')

    def test_registered_worktree_reuses_same_relative_path_without_rewriting_evidence(self):
        source = self.registered_source() / 'contracts' / 'instruction.md'
        packet, _ = self.instruction_packet(source)
        selection = json.loads(Path(packet['path']).read_text())
        refs = [packet, self.protocol, self.instruction, self.requirements, self.method,
                self.task, selection['criteria_review'], selection['observations'][0]['report'],
                selection['observations'][0]['trace']]
        before = {ref['path']: Path(ref['path']).read_bytes() for ref in refs}
        self.record_pass(packet)
        result = self.owner.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['event']['payload']['outcome'], 'completed')
        self.assertEqual({path: Path(path).read_bytes() for path in before}, before)

    def test_same_basename_and_bytes_at_another_relative_path_do_not_cover_change(self):
        source = self.registered_source() / 'other' / 'instruction.md'
        packet, _ = self.instruction_packet(source)
        self.record_pass(packet)
        self.assert_completion_refused('worker.feedback.coverage')

    def test_unrelated_repository_with_same_path_and_bytes_does_not_cover_change(self):
        source = self.directory / 'unrelated'
        source.mkdir()
        subprocess.run(['git', 'init', '-b', 'main', str(source)],
                       check=True, capture_output=True, text=True)
        packet, _ = self.instruction_packet(source / 'contracts' / 'instruction.md')
        self.record_pass(packet)
        self.assert_completion_refused('worker.feedback.coverage')

    def test_copied_git_pointer_does_not_register_an_instruction_source(self):
        registered = self.registered_source()
        copied = self.directory / 'unregistered'
        copied.mkdir()
        (copied / '.git').write_bytes((registered / '.git').read_bytes())
        packet, _ = self.instruction_packet(copied / 'contracts' / 'instruction.md')
        self.record_pass(packet)
        self.assert_completion_refused('worker.feedback.coverage')

    def test_nested_foreign_repository_does_not_inherit_parent_worktree_identity(self):
        nested = self.registered_source() / 'contracts'
        nested.mkdir()
        subprocess.run(['git', 'init', '-b', 'main', str(nested)],
                       check=True, capture_output=True, text=True)
        packet, _ = self.instruction_packet(nested / 'instruction.md')
        self.record_pass(packet)
        self.assert_completion_refused('worker.feedback.coverage')

    def test_changed_target_bytes_do_not_reuse_registered_worktree_evidence(self):
        packet, target = self.instruction_packet(
            self.registered_source() / 'contracts' / 'instruction.md')
        self.record_pass(packet)
        target.write_text('Changed after observation.')
        self.assert_completion_refused('worker.feedback.coverage')

    def test_valid_relocation_does_not_cover_another_changed_instruction(self):
        packet, target = self.instruction_packet(
            self.registered_source() / 'contracts' / 'instruction.md')
        uncovered = target.with_name('uncovered.md')
        uncovered.write_bytes(target.read_bytes())
        self.record_pass(packet)
        receipt = self.assert_completion_refused('worker.feedback.coverage')
        self.assertEqual(receipt['invalid']['value'], [str(uncovered)])

    def test_missing_source_and_tampered_evidence_refuse_before_coverage(self):
        packet, _ = self.instruction_packet(
            self.registered_source() / 'contracts' / 'instruction.md')
        self.record_pass(packet)
        observation = json.loads(Path(packet['path']).read_text())['observations'][0]
        for ref in (self.instruction, observation['report'], observation['trace'], self.task):
            with self.subTest(path=ref['path']):
                path = Path(ref['path'])
                original = path.read_bytes()
                if ref is self.instruction:
                    path.unlink()
                else:
                    path.write_bytes(original + b' changed')
                try:
                    self.assert_completion_refused('worker.feedback.incomplete')
                finally:
                    path.write_bytes(original)

    def test_report_identity_mismatch_refuses_before_recording(self):
        packet, target = self.instruction_packet(
            self.registered_source() / 'contracts' / 'instruction.md')
        selection = json.loads(Path(packet['path']).read_text())
        observation = selection['observations'][0]
        report = json.loads(Path(observation['report']['path']).read_text())
        for field, value in (('instructions', {str(target): self.instruction['sha256']}),
                             ('input_sha256', 'f' * 64)):
            with self.subTest(field=field):
                observation['report'] = self.file(observation['report']['path'], {**report, field: value})
                packet = self.file(packet['path'], selection)
                code, receipt = self.invoke(packet)
                self.assertNotEqual(code, 0)
                self.assertEqual(receipt['invalid']['field'], 'worker.feedback.input')
                self.assertIn('report.identity', json.dumps(receipt['invalid']))
                self.assertEqual(self.owner.events.read_text(), '')
                self.assertFalse(self.owner.calls.exists())

    def test_relocated_instruction_keeps_original_task_and_contract_guard(self):
        self.instruction_packet(self.registered_source() / 'contracts' / 'instruction.md')
        original = json.loads(Path(self.requirements['path']).read_text())
        for field in ('task', 'contract'):
            with self.subTest(field=field):
                requirements = dict(original)
                requirements[field] = (original['task'] + ' Changed task.' if field == 'task'
                                       else {**original['contract'], 'behavior': ['changed behavior']})
                self.requirements = self.file('requirements.txt', requirements)
                protocol = json.loads(Path(self.protocol['path']).read_text())
                protocol['requirements'] = self.requirements
                self.protocol = self.file('protocol.json', protocol)
                code, receipt = self.invoke(self.packet())
                self.assertNotEqual(code, 0)
                self.assertEqual(receipt['invalid']['field'], 'worker.feedback.requirements')
                self.assertEqual(self.owner.events.read_text(), '')
                self.assertFalse(self.owner.calls.exists())

    def test_conditions_then_behavior_then_completion_and_reentry(self):
        code, first = self.invoke(self.packet('unsupported'))
        self.assertEqual(code, 0)
        self.assertEqual(first['next']['operation'], 'review_criteria')
        self.assertIsNone(first['next']['argv'])
        self.assertIsNone(first['next']['input'])
        self.assertEqual(first['feedback']['test_scope']['cases'], [])
        self.assertNotEqual(self.owner.invoke().returncode, 0)
        code, repeated = self.invoke(self.packet('unsupported'))
        self.assertEqual(repeated['status'], 'readback')
        self.assertEqual(len(self.owner.events.read_text().splitlines()), 1)
        code, second = self.invoke(self.packet(complete=True))
        self.assertEqual(second['round'], 2)
        self.assertEqual(second['next']['operation'], 'correct_pclass')
        self.assertIsNone(second['next']['argv'])
        self.assertIsNone(second['next']['input'])
        self.assertEqual(second['feedback']['test_scope']['cases'], ['missing'])
        self.assertNotEqual(self.owner.invoke().returncode, 0)
        code, third = self.invoke(self.packet())
        self.assertEqual(third['round'], 3)
        self.assertEqual(third['feedback']['test_scope']['cases'], [])
        self.assertEqual(third['next']['operation'], 'consume_verified_behavior')
        self.assertIsNone(third['next']['argv'])
        self.assertIsNone(third['next']['input'])
        self.assertEqual(self.owner.invoke().returncode, 0)
        self.assertEqual(len(stage_outcome.typed_events(json.loads(x) for x in self.owner.events.read_text().splitlines())), 1)

    def test_quote_drift_and_three_failures_require_reassessment(self):
        code, bad = self.invoke(self.packet(quote='invented requirement'))
        self.assertNotEqual(code, 0)
        self.assertFalse(self.owner.calls.exists())
        for value in (1, 2, 3):
            code, failed = self.invoke(self.packet(complete=value))
            self.assertEqual(code, 0)
        self.assertEqual(failed['next']['operation'], 'reassess_cause')
        self.assertIsNone(failed['next']['argv'])
        self.assertIsNone(failed['next']['input'])
        code, exhausted = self.invoke(self.packet(complete=4))
        self.assertNotEqual(code, 0)
        self.assertEqual(exhausted['invalid']['field'], 'worker.feedback.budget')
        self.assertEqual(len(self.owner.calls.read_text().splitlines()), 3)
        code, passed = self.invoke(self.packet())
        self.assertEqual(code, 0)
        self.assertEqual(passed['feedback']['failed_attempts'], 3)
        self.assertEqual(self.owner.invoke().returncode, 0)

    def test_changed_instruction_after_pass_and_unknown_event_write(self):
        packet = self.packet()
        self.assertEqual(self.invoke(packet)[0], 0)
        Path(self.instruction['path']).write_text('Changed after observation')
        self.assertNotEqual(self.owner.invoke().returncode, 0)
        self.owner.events.write_text('')
        self.owner.mode.write_text('write-failure')
        Path(self.instruction['path']).write_text('Keep missing evidence incomplete.')
        code, refused = self.invoke(packet)
        self.assertNotEqual(code, 0)
        self.assertEqual(refused['next']['owner'], 'Noodle')
        count = len(self.owner.calls.read_text().splitlines())
        self.owner.mode.write_text('ok')
        self.assertEqual(self.invoke(packet)[1]['status'], 'readback')
        self.assertEqual(len(self.owner.calls.read_text().splitlines()), count)

    def test_feedback_scope_reuses_only_same_passed_case(self):
        from schema_manager import pclass_feedback
        packet = self.packet()
        prior = pclass_feedback(packet['path'], packet['sha256'])
        missing = {**prior, 'cases': []}
        scope = test_manager.feedback_scope(missing, prior)
        self.assertEqual(scope['reuse'], ['missing'])
        changed = {**missing, 'case_fingerprints': {'missing': 'changed'}}
        self.assertEqual(test_manager.feedback_scope(changed, prior)['cases'], ['missing'])
        self.assertFalse(scope['full'])


class ArchivedFeedbackTests(unittest.TestCase):
    def test_nonterminal_feedback_does_not_replace_or_duplicate_outcome(self):
        f = test_issue_execution.IssueExecutionTests('runTest')
        f.setUp(); self.addCleanup(f.doCleanups)
        directory = f.archived_completion()
        path = directory / 'events.ndjson'
        terminal = path.read_text()
        note = json.dumps({'type': 'stage_message', 'session_id': f.session,
            'payload': {'message': 'feedback observation', 'blocking': False,
                        'order_id': f.env['NOODLE_ORDER_ID'], 'stage_index': 0}}) + '\n'
        path.write_text(note + terminal)
        self.assertEqual(issue_execution.completed_original_order(f.envelope, f.snapshot)['source'], 'archived_projection')
        self.assertEqual(handoff_oracle._session(f.root, f.env['NOODLE_ORDER_ID'])[0], directory)
        path.write_text(note + terminal + terminal)
        with self.assertRaises(AdmissionRefusal):
            issue_execution.completed_original_order(f.envelope, f.snapshot)
        with self.assertRaises(RuntimeError):
            handoff_oracle._session(f.root, f.env['NOODLE_ORDER_ID'])
        path.write_text(terminal + note)
        with self.assertRaises(AdmissionRefusal):
            issue_execution.completed_original_order(f.envelope, f.snapshot)
        with self.assertRaises(RuntimeError):
            handoff_oracle._session(f.root, f.env['NOODLE_ORDER_ID'])
