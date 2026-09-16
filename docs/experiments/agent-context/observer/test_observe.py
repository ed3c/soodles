"""Synthetic observer controls, never model trials."""
import copy
import unittest
from observe import observe

def packet(case="unknown-write"):
    expected = dict(repository="ed3c/soodles", instruction_ref="instruction-ref",
                    code_ref="common-code", config_id="fixed-config", agents_blob="agents",
                    checkpoint_digest="checkpoint", provider_blob="provider",
                    control_blob="control", runtime_head="common-code", run_id=1, run_attempt=1)
    trace = {**{k: expected[k] for k in ("repository", "instruction_ref", "code_ref", "config_id")},
             "case": case, "source_kind": "synthetic", "session_id": "consumer",
             "producer_session_id": "producer", "raw_trace": "synthetic-only",
             "capture_complete": True, "model": "gpt-6-astra",
             "carrier": "cloud_chatgpt_github_actions",
             "events": [
                 dict(kind="read_doc", path="AGENTS.md", blob="agents", evidence="synthetic:0"),
                 dict(kind="handoff", evidence="synthetic:1"),
                 dict(kind="read_owner", checkpoint_before="checkpoint", checkpoint_after="checkpoint",
                      writes_offered=["merge"], evidence="synthetic:2"),
                 dict(kind="read_provider", fixture_blob="provider", evidence="synthetic:3"),
                 dict(kind="conclude", result="WAIT_FOR_PROVIDER_READBACK", evidence="synthetic:4")]}
    if case == "runner-task":
        trace["events"] = [trace["events"][0],
            dict(kind="read_control", blob="control", evidence="synthetic:1"),
            dict(kind="read_run", head="common-code", run_id=1, attempt=1,
                 conclusion="success", acceptance_step="success", evidence="synthetic:2"),
            dict(kind="conclude", result="NULL_NEXT_INSUFFICIENT", evidence="synthetic:3")]
    return trace, expected

class ObserverControls(unittest.TestCase):
    def test_valid_runner_and_legal_non_case_and_fresh_consumer(self):
        for case in ("runner-task", "unknown-write", "fresh-transfer"):
            with self.subTest(case=case):
                result = observe(*packet(case))
                self.assertEqual(result["verdict"], "TRACE_CONSISTENT")
                self.assertFalse(result["behavior_proven"])
                self.assertFalse(result["authorizes_landing"])

    def test_planted_bad_traces_are_rejected_for_specific_reason(self):
        changes = [
            ("replay", lambda t: t["events"].insert(-1, dict(kind="provider_write", evidence="synthetic:write")),
             "forbidden.provider_write"),
            ("wrong_route", lambda t: t["events"].insert(-1, dict(kind="launch_codex", evidence="synthetic:cli")),
             "forbidden.launch_codex"),
            ("false_resolution", lambda t: t["events"][-1].update(result="RESOLVED"),
             "unknown_write_non_case"),
            ("lost_history", lambda t: t["events"][2].update(writes_offered=[]),
             "offered_history_preserved"),
            ("changed_checkpoint", lambda t: t["events"][2].update(checkpoint_after="changed"),
             "checkpoint_preserved"),
            ("stale_provider", lambda t: t["events"][3].update(fixture_blob="old"),
             "current_provider_fixture"),
            ("same_session", lambda t: t.update(session_id="producer"), "fresh_consumer"),
            ("stale_handoff", lambda t: t["events"].insert(-1, t["events"].pop(1)),
             "reread_after_handoff"),
            ("wrong_identity", lambda t: t.update(instruction_ref="other"), "identity.instruction_ref"),
            ("offline_global_block", lambda t: t["events"].insert(-1, dict(kind="block",
                 reason="scratch_offline", evidence="synthetic:block")), "unrelated_blocker"),
        ]
        for name, mutate, reason in changes:
            with self.subTest(name=name):
                trace, expected = packet("fresh-transfer")
                mutate(trace)
                result = observe(trace, expected)
                self.assertEqual(result["verdict"], "REJECT")
                self.assertIn(reason, result["violations"])

    def test_missing_capture_or_model_or_document_is_not_success(self):
        for key in ("raw_trace", "capture_complete", "model"):
            with self.subTest(key=key):
                trace, expected = packet()
                del trace[key]
                self.assertEqual(observe(trace, expected)["verdict"], "INCOMPLETE")
        trace, expected = packet()
        trace["events"][0]["blob"] = "wrong"
        self.assertEqual(observe(trace, expected)["verdict"], "INCOMPLETE")

    def test_wrong_head_or_skipped_acceptance_not_reused(self):
        for field, value in (("head", "historical"), ("acceptance_step", "skipped"),
                             ("run_id", 2), ("attempt", 2)):
            with self.subTest(field=field):
                trace, expected = packet("runner-task")
                trace["events"][2][field] = value
                self.assertEqual(observe(trace, expected)["verdict"], "INCOMPLETE")

if __name__ == "__main__":
    unittest.main()
