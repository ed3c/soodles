import base64
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/skills/verify-soodles/scripts'
DATA = ROOT / 'docs/experiments/pclass-admission-recovery-81/raw'
SCRIPT = SCRIPTS / 'replay_pclass.py'
OBSERVER = SCRIPTS / 'observe_admission_recovery_pclass.py'
DECIDER = SCRIPTS / 'decide_admission_recovery_pclass.py'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


replay = module('replay', SCRIPT)
observer = module('observer', OBSERVER)


def bind(raw, manifest):
    """Test-fixture supervisor, not a production manifest authorizer."""
    manifest['raw_bundle_sha256'] = replay.fingerprint(raw)
    for run, declaration in zip(raw['runs'], manifest['runs']):
        declaration['evidence_sha256'] = replay.fingerprint(run)
    return manifest


def replace_record(run, label, file, fn):
    record = next(r for r in run['records'] if r['label'] == label)
    value = observer.parsed(record, file)
    fn(value)
    record[file] = observer.pack((json.dumps(value) + '\n').encode())
    if file == 'stdout.bin':
        result = observer.parsed(record, 'result.json')
        result['stdout_sha256'] = record[file]['sha256']
        record['result.json'] = observer.pack(json.dumps(result).encode())


def complete_fixture(raw, manifest):
    """Three synthetic GREEN controls derived from the actual clean e_b5.

    These are unit fixtures, never fresh consumers or experiment evidence.
    """
    raw, manifest = copy.deepcopy(raw), copy.deepcopy(manifest)
    raw.pop('cleanup_supplement', None)
    manifest.pop('cleanup_supplement', None)
    manifest['required_controls'] = observer.CONTROLS
    source = raw['runs'][1]
    declared = manifest['runs'][1]
    runs, declarations = [], []
    for rid in manifest['selection']['run_ids']:
        run = copy.deepcopy(source)
        run['run_id'] = rid
        for record in run['records']:
            for name in ('request.json', 'result.json', 'stdout.bin', 'stderr.bin'):
                record[name] = observer.pack(observer.unpack(record[name]).replace(b'e_b5', rid.encode()))
            result = observer.parsed(record, 'result.json')
            for stream in ('stdout', 'stderr'):
                result[stream + '_sha256'] = record[stream + '.bin']['sha256']
            record['result.json'] = observer.pack(json.dumps(result).encode())
        run['consumer'] = observer.pack(observer.unpack(run['consumer']).replace(b'e_b5', rid.encode()))
        declaration = json.loads(json.dumps(declared).replace('e_b5', rid))
        declaration['run_id'] = rid
        b = declaration['bindings']
        by_label = {r['label']: r for r in run['records']}
        b['commands'] = {r['label']: replay.fingerprint(observer.parsed(r, 'request.json')['argv'])
                         for r in run['records']}
        b['projection_sha256'] = by_label[b['roles']['initial']]['stdout.bin']['sha256']
        b['completion_sha256'] = by_label[b['roles']['completion']]['stdout.bin']['sha256']
        runs.append(run)
        declarations.append(declaration)
    raw['runs'], manifest['runs'] = runs, declarations
    return raw, bind(raw, manifest)


class AdmissionRecoveryReplayTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((DATA / 'raw-runs.json').read_text())
        self.manifest = json.loads((DATA / 'manifest.json').read_text())
        self.gates = json.loads((DATA / 'gates.json').read_text())

    def evaluate(self, raw=None, manifest=None, gates=None):
        manifest = manifest if manifest is not None else self.manifest
        return replay.replay(self.raw if raw is None else raw,
                             self.gates if gates is None else gates,
                             manifest, replay.fingerprint(manifest), OBSERVER, DECIDER)

    def test_raw_exploration_preserves_cleanup_disagreement(self):
        raw, manifest = copy.deepcopy(self.raw), copy.deepcopy(self.manifest)
        raw.pop('cleanup_supplement')
        manifest.pop('cleanup_supplement')
        manifest['required_controls'] = observer.CONTROLS
        bind(raw, manifest)
        result = self.evaluate(raw, manifest)
        self.assertEqual(result['classification'], 'FAIL')
        self.assertEqual(result['decision']['disposition'], 'INCONCLUSIVE')
        self.assertIn('e_b4:retained_runtime_lock', result['errors'])
        self.assertIn('e_b6:recovery_residue', result['errors'])
        self.assertEqual([r['hard_gate'] for r in result['baseline']], ['FAIL', 'PASS', 'FAIL'])
        self.assertIsNone(result['decision']['barrier_totals'])
        self.assertTrue(all(c['predicate'] == 'PASS' for c in result['controls']), result['controls'])
        self.assertFalse(result['authorizes_landing'])

    def test_fixed_append_only_supplement_completes_same_packet(self):
        result = self.evaluate()
        self.assertEqual(result['classification'], 'PASS', result['errors'])
        self.assertEqual(result['decision']['disposition'], 'NO_QUALIFIED_BARRIER')
        self.assertEqual(result['decision']['barrier_totals'], dict.fromkeys(observer.BARRIERS, 0))
        self.assertEqual([r['initial_cleanup_errors'] for r in result['baseline']],
                         [['retained_runtime_lock'], [], ['recovery_residue']])
        self.assertEqual([r['cleanup_supplement_verified'] for r in result['baseline']],
                         [True, False, True])
        initial = json.loads(observer.unpack(self.raw['initial_replay']))
        self.assertEqual(initial['decision']['disposition'], 'INCONCLUSIVE')
        original = json.loads(observer.unpack(self.raw['initial_manifest']))
        self.assertEqual([replay.fingerprint(r) for r in self.raw['runs']],
                         [r['evidence_sha256'] for r in original['runs']])
        self.assertTrue(all(c['predicate'] == 'PASS' for c in result['controls']))

    def test_supplement_omission_and_rebinding_are_red(self):
        for mutation in ('omit', 'observer', 'selection', 'receipt', 'run', 'project', 'lock', 'original'):
            with self.subTest(mutation=mutation):
                raw, manifest = copy.deepcopy(self.raw), copy.deepcopy(self.manifest)
                s = raw['cleanup_supplement']
                b = manifest['cleanup_supplement']['runs']['e_b4']
                if mutation == 'omit':
                    raw.pop('cleanup_supplement')
                elif mutation in ('observer', 'selection'):
                    s[mutation] = observer.pack(b'changed')
                elif mutation == 'receipt':
                    s['receipts']['e_b4'] = s['receipts']['e_b6']
                elif mutation in ('run', 'project'):
                    receipt = json.loads(observer.unpack(s['receipts']['e_b4']))
                    receipt['run_id' if mutation == 'run' else 'project'] = 'another'
                    s['receipts']['e_b4'] = observer.pack(json.dumps(receipt).encode())
                    b['receipt_sha256'] = s['receipts']['e_b4']['sha256']
                elif mutation == 'lock':
                    b['lock']['lock_sha256'] = '0' * 64
                else:
                    b['original_run_sha256'] = '0' * 64
                bind(raw, manifest)
                result = self.evaluate(raw, manifest)
                self.assertEqual(result['classification'], 'FAIL', result)
                self.assertIsNone(result['decision']['barrier_totals'])

    def test_supplement_cannot_hide_scope_or_process_failures(self):
        for field in ('scope', 'process', 'sessions', 'residue', 'archive', 'time'):
            with self.subTest(field=field):
                raw, manifest = copy.deepcopy(self.raw), copy.deepcopy(self.manifest)
                s = raw['cleanup_supplement']
                receipt = json.loads(observer.unpack(s['receipts']['e_b4']))
                if field == 'scope':
                    receipt['scope']['owned_path'] = '.noodle/orders.json'
                elif field == 'process':
                    receipt['process_readback'][0]['absent'] = False
                elif field == 'sessions':
                    receipt['session_readback'].pop()
                elif field == 'residue':
                    receipt['before']['temporary_paths'] = ['residue.tmp']
                elif field == 'archive':
                    receipt['after']['archives'] = []
                else:
                    receipt['observed_at_ns'] = 1
                s['receipts']['e_b4'] = observer.pack(json.dumps(receipt).encode())
                manifest['cleanup_supplement']['runs']['e_b4']['receipt_sha256'] = s['receipts']['e_b4']['sha256']
                bind(raw, manifest)
                result = self.evaluate(raw, manifest)
                self.assertIn('e_b4:cleanup_supplement_incomplete_readback', result['errors'])
                self.assertIsNone(result['baseline'][0]['barriers'])

    def test_complete_zero_is_no_qualified_barrier(self):
        raw, manifest = complete_fixture(self.raw, self.manifest)
        result = self.evaluate(raw, manifest)
        self.assertEqual(result['classification'], 'PASS', result['errors'])
        self.assertEqual(result['decision']['disposition'], 'NO_QUALIFIED_BARRIER')
        self.assertEqual(result['decision']['barrier_totals'], dict.fromkeys(observer.BARRIERS, 0))
        self.assertFalse(result['decision']['confirmation_authorized'])
        self.assertFalse(result['decision']['treatment_retained'])
        self.assertNotIn('treatment', result)

    def test_all_planted_controls_discriminate_from_green_fixture(self):
        raw, manifest = complete_fixture(self.raw, self.manifest)
        result = self.evaluate(raw, manifest)
        self.assertEqual([c['name'] for c in result['controls']], observer.CONTROLS)
        for control in result['controls']:
            with self.subTest(control=control['name']):
                self.assertEqual(control['predicate'], 'PASS', control)
                self.assertEqual(control['observed'], control['expected'])
                if control['expected'] == 'PASS':
                    self.assertEqual(control['errors'], [])

    def test_membership_cannot_be_redeclared_as_two_or_treatment(self):
        raw, manifest = complete_fixture(self.raw, self.manifest)
        raw['runs'].pop()
        manifest['runs'].pop()
        bind(raw, manifest)
        self.assertEqual(self.evaluate(raw, manifest)['classification'], 'FAIL')
        raw, manifest = complete_fixture(self.raw, self.manifest)
        raw['runs'][0]['arm'] = manifest['runs'][0]['arm'] = 'treatment'
        bind(raw, manifest)
        self.assertEqual(self.evaluate(raw, manifest)['classification'], 'FAIL')

    def test_missing_confirmation_is_unknown_not_zero(self):
        raw, manifest = complete_fixture(self.raw, self.manifest)
        consumer = json.loads(observer.unpack(raw['runs'][0]['consumer']))
        consumer.pop('confirmation')
        raw['runs'][0]['consumer'] = observer.pack(json.dumps(consumer).encode())
        bind(raw, manifest)
        result = self.evaluate(raw, manifest)
        self.assertEqual(result['classification'], 'FAIL')
        self.assertIsNone(result['decision']['barrier_totals'])

    def test_binding_mutations_fail_at_public_entry(self):
        for key, replacement, error in (
                ('observer_sha256', '0' * 64, 'run_observer_identity_mismatch'),
                ('carrier', {'platform': 'linux_amd64'}, 'run_carrier_mismatch'),
                ('completion_sha256', '0' * 64, 'completion_projection_digest_mismatch')):
            with self.subTest(key=key):
                raw, manifest = complete_fixture(self.raw, self.manifest)
                manifest['runs'][0]['bindings'][key] = replacement
                result = self.evaluate(raw, manifest)
                self.assertEqual(result['classification'], 'FAIL')
                self.assertTrue(any(error in e for e in result['errors']), result)

    def test_missing_and_changed_streams_fail_closed(self):
        for mutation in ('missing', 'changed'):
            with self.subTest(mutation=mutation):
                raw, manifest = complete_fixture(self.raw, self.manifest)
                if mutation == 'missing':
                    raw['runs'][0]['records'][0].pop('stdout.bin')
                else:
                    raw['runs'][0]['records'][0]['stdout.bin']['base64'] = base64.b64encode(b'changed').decode()
                bind(raw, manifest)
                self.assertEqual(self.evaluate(raw, manifest)['classification'], 'FAIL')

    def test_failed_process_and_failed_cleanup_are_not_success(self):
        for role, field, change in (
                ('retire', 'result.json', {'timed_out': True}),
                ('cleanup', 'result.json', {'exit_code': 1}),
                ('process', 'stdout.bin', {'pid_or_group_matches': [{'pid': 123}]}),
                ('lock_process', 'stdout.bin', {'pid_or_group_matches': [{'pid': 456}]})):
            with self.subTest(role=role, field=field):
                raw, manifest = complete_fixture(self.raw, self.manifest)
                label = manifest['runs'][0]['bindings']['roles'][role]
                replace_record(raw['runs'][0], label, field, lambda x: x.update(change))
                bind(raw, manifest)
                result = self.evaluate(raw, manifest)
                self.assertEqual(result['classification'], 'FAIL', result)
                self.assertIsNone(result['decision']['barrier_totals'])

    def test_analyzer_and_manifest_preflight_precedes_import(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'imported'
            analyzer = Path(directory) / 'observer.py'
            analyzer.write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
            for target in ('observer', 'decider'):
                result = replay.replay(self.raw, self.gates, self.manifest,
                                       replay.fingerprint(self.manifest),
                                       analyzer if target == 'observer' else OBSERVER,
                                       analyzer if target == 'decider' else DECIDER)
                self.assertIn(target + '_digest_mismatch', result['errors'])
                self.assertFalse(marker.exists())
            result = replay.replay(self.raw, self.gates, self.manifest, '0' * 64,
                                   OBSERVER, DECIDER)
            self.assertIn('manifest_digest_mismatch', result['errors'])

    def test_caller_gates_cannot_supply_pass_or_counts(self):
        gates = copy.deepcopy(self.gates)
        gates['controls'] = [{'predicate': 'PASS'}]
        self.manifest['gates_sha256'] = replay.fingerprint(gates)
        self.assertIn('invalid_exploration_gates', self.evaluate(gates=gates)['errors'])

    def test_positive_legal_barrier_selects_first_without_confirmation(self):
        raw, manifest = complete_fixture(self.raw, self.manifest)
        run, declaration = raw['runs'][0], manifest['runs'][0]
        b = declaration['bindings']
        source_index = next(i for i, r in enumerate(run['records']) if r['label'] == b['roles']['initial'])
        repeated = copy.deepcopy(run['records'][source_index])
        repeated['label'] = 'planted_repeated_inspect'
        request = observer.parsed(repeated, 'request.json')
        request['time_ns'] += 1
        repeated['request.json'] = observer.pack(json.dumps(request).encode())
        run['records'].insert(source_index + 1, repeated)
        b['record_labels'].insert(source_index + 1, repeated['label'])
        b['commands'][repeated['label']] = replay.fingerprint(request['argv'])
        bind(raw, manifest)
        result = self.evaluate(raw, manifest)
        self.assertEqual(result['classification'], 'PASS', result['errors'])
        self.assertEqual(result['decision']['selected_barrier'], observer.BARRIERS[0])
        self.assertEqual(result['decision']['barrier_totals'][observer.BARRIERS[0]], 1)
        self.assertEqual(result['decision']['disposition'], 'INCONCLUSIVE')
        self.assertFalse(result['decision']['confirmation_authorized'])

    def test_unchanged_reinspection_after_completion_is_a_legal_barrier(self):
        raw, manifest = complete_fixture(self.raw, self.manifest)
        run, declaration = raw['runs'][0], manifest['runs'][0]
        b = declaration['bindings']
        index = next(i for i, r in enumerate(run['records']) if r['label'] == b['roles']['completion'])
        record = copy.deepcopy(run['records'][index])
        record['label'] = 'post_completion_inspect'
        request = observer.parsed(record, 'request.json')
        request['time_ns'] += 1
        record['request.json'] = observer.pack(json.dumps(request).encode())
        run['records'].insert(index + 1, record)
        b['record_labels'].insert(index + 1, record['label'])
        b['commands'][record['label']] = replay.fingerprint(request['argv'])
        bind(raw, manifest)
        result = self.evaluate(raw, manifest)
        self.assertEqual(result['classification'], 'PASS', result['errors'])
        self.assertEqual(result['baseline'][0]['barriers'][observer.BARRIERS[0]], 1)

    def test_all_barriers_are_ordered_and_separate_from_hard_gates(self):
        raw, manifest = complete_fixture(self.raw, self.manifest)
        run, declaration = raw['runs'][0], manifest['runs'][0]
        b = declaration['bindings']
        index = next(i for i, r in enumerate(run['records']) if r['label'] == b['roles']['initial'])
        time_ns = observer.parsed(run['records'][index], 'request.json')['time_ns']
        for offset, label in enumerate(('help', 'read_verify_noodle_skill'), 1):
            record = copy.deepcopy(next(r for r in run['records'] if r['label'] == label))
            record['label'] = 'repeated_' + label
            request = observer.parsed(record, 'request.json')
            request['time_ns'] = time_ns + offset
            record['request.json'] = observer.pack(json.dumps(request).encode())
            run['records'].insert(index + offset, record)
            b['record_labels'].insert(index + offset, record['label'])
            b['commands'][record['label']] = replay.fingerprint(request['argv'])
        consumer = json.loads(observer.unpack(run['consumer']))
        consumer['confirmation'] = {'requested': True, 'count': 1}
        run['consumer'] = observer.pack(json.dumps(consumer).encode())
        bind(raw, manifest)
        result = self.evaluate(raw, manifest)
        self.assertEqual(result['classification'], 'PASS', result['errors'])
        self.assertEqual(list(result['decision']['barrier_totals'].values()), [0, 1, 1, 1])
        self.assertEqual(result['decision']['selected_barrier'], observer.BARRIERS[1])
        self.assertFalse(result['decision']['confirmation_authorized'])

    def test_required_control_and_carrier_cannot_be_redefined(self):
        for key, value in (('required_controls', []),
                           ('carrier', {'platform': 'linux_amd64'})):
            raw, manifest = complete_fixture(self.raw, self.manifest)
            manifest[key] = value
            self.assertEqual(self.evaluate(raw, manifest)['classification'], 'FAIL')

    def test_normalizer_identity_is_the_actual_entry(self):
        result = replay.replay(self.raw, self.gates, self.manifest,
                               replay.fingerprint(self.manifest), OBSERVER, DECIDER,
                               normalizer_path=OBSERVER)
        self.assertIn('normalizer_path_mismatch', result['errors'])

    def test_duplicate_mutation_cannot_be_an_optimization_barrier(self):
        raw, manifest = complete_fixture(self.raw, self.manifest)
        run, declaration = raw['runs'][0], manifest['runs'][0]
        b = declaration['bindings']
        index = next(i for i, r in enumerate(run['records']) if r['label'] == b['roles']['completion'])
        record = copy.deepcopy(next(r for r in run['records'] if r['label'] == b['roles']['retire']))
        record['label'] = 'duplicate_retire'
        request = observer.parsed(record, 'request.json')
        request['time_ns'] = observer.parsed(run['records'][index], 'request.json')['time_ns'] + 1
        record['request.json'] = observer.pack(json.dumps(request).encode())
        run['records'].insert(index + 1, record)
        b['record_labels'].insert(index + 1, record['label'])
        b['commands'][record['label']] = replay.fingerprint(request['argv'])
        bind(raw, manifest)
        result = self.evaluate(raw, manifest)
        self.assertEqual(result['classification'], 'FAIL')
        self.assertIn('e_b4:mutating_continuation_count', result['errors'])
        self.assertIsNone(result['baseline'][0]['barriers'])

    def test_preflight_aborts_have_no_score(self):
        aborts = json.loads((DATA / 'preflight-aborts.json').read_text())
        self.assertEqual(aborts['run_ids'], ['e_b1', 'e_b2', 'e_b3'])
        self.assertFalse(aborts['scored'])
        self.assertIsNone(aborts['barriers'])
        self.assertNotEqual(aborts['run_ids'], self.manifest['selection']['run_ids'])


if __name__ == '__main__':
    unittest.main()
