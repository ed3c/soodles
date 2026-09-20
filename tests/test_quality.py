"""Admission and cost controls run without installing the optional analyzer."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from quality import measure, provider

ROOT = Path(__file__).resolve().parent.parent


class QualityTests(unittest.TestCase):
    def test_invalid_subject_refused_before_output_or_dependency_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'report'
            run = subprocess.run(['python3', '-B', str(ROOT/'quality/measure.py'),
                                  '--base', '--HEAD', '--head', 'a'*40, '--output', str(output)],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse(output.exists())
            with self.assertRaisesRegex(ValueError, 'invalid base='):
                measure.preflight(ROOT, 'main', 'a'*40, output)
            self.assertFalse(output.exists())

    def test_exact_same_head_allowed_but_output_inside_subject_refused(self):
        head = measure.git(ROOT, 'rev-parse', 'HEAD').decode().strip()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'report'
            self.assertEqual(measure.preflight(ROOT, head, head, out), out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError, 'outside the subject'):
            measure.preflight(ROOT, head, head, ROOT/'report')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'already exists'):
                measure.preflight(ROOT, head, head, tmp)

    def test_new_source_is_visible_in_unclassified_scope(self):
        paths = {'landing.py':'production', 'tests/test_landing.py':'tests',
                 'delivery_oracle.py':'oracles', 'quality/measure.py':'tooling',
                 'handoff_oracle.py':'oracles',
                 'new_owner/new.py':'unclassified'}
        self.assertEqual({p:measure.scope(p) for p in paths}, paths)

    def test_pending_time_is_not_zero_and_steps_are_not_summed_into_job_time(self):
        job = {'id':1,'name':'runtime-evidence','status':'in_progress',
               'started_at':'2026-09-16T00:00:00Z', 'completed_at':None,
               'steps':[{'name':'acceptance','started_at':'2026-09-16T00:00:01Z',
                         'completed_at':'2026-09-16T00:00:04Z'}]}
        result = provider.summarize_job(job)
        self.assertIsNone(result['seconds'])
        self.assertEqual(result['steps'][0]['seconds'], 3)
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(provider.collect('a'*40)['status'], 'unavailable')

    def test_analyzer_failure_cannot_be_interpreted_as_no_findings(self):
        with patch.object(measure, 'SG', '/pinned/analyzer', create=True), patch.object(
                measure.subprocess, 'run', return_value=subprocess.CompletedProcess([], 2, '', 'bad rules')):
            with self.assertRaisesRegex(RuntimeError, 'no score is valid'):
                measure.strict_sg([Path('subject.py')], Path('rules.yml'))
