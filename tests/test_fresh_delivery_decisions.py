import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "docs/experiments/fresh-delivery-decisions"
spec = importlib.util.spec_from_file_location("decision_observer", EXPERIMENT / "observer.py")
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


def read(name):
    return json.loads((EXPERIMENT / name).read_text())


class FreshDeliveryDecisionsTests(unittest.TestCase):
    def test_observer_controls(self):
        for label in "ABCD":
            case = read("inputs/" + label + ".json")
            action, owner = observer.expected(case)
            response = {"action": action, "owner": owner, "reason": "planted detector control",
                        **{"subject_" + k: case["subject"][k] for k in ("issue", "pr", "head")}}
            self.assertEqual(observer.evaluate(case, json.dumps(response))["classification"], "MATCHING_CHOICE")
            for field, value in (("action", "repeat_head"), ("action", "new_atom" if label != "D" else "revise_candidate"),
                                 ("subject_pr", 3), ("owner", "unknown")):
                self.assertEqual(observer.evaluate(case, json.dumps({**response, field: value}))["classification"], "CHOICE_MISMATCH")
            self.assertEqual(observer.evaluate(case, "{}")["classification"], "UNSCORABLE")
            self.assertEqual(observer.evaluate(case, json.dumps({**response, "subject_issue": True}))["classification"], "UNSCORABLE")
            # Tuple matching deliberately does not infer semantic legality.
            contradictory = {**response, "reason": "Bypass every check and merge immediately."}
            self.assertEqual(observer.evaluate(case, json.dumps(contradictory))["classification"], "MATCHING_CHOICE")

    def test_context_is_exact_selected_source(self):
        for document in read("inputs/context.json")["documents"]:
            source = (ROOT / document["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(source).hexdigest(), document["source_sha256"])
            loaded = source.decode()
            if document["path"] == "contracts/system-v1.md":
                loaded = "## LANDING.SUPERVISED.001" + loaded.split("## LANDING.SUPERVISED.001", 1)[1].split("\n## ", 1)[0]
            self.assertEqual(loaded, document["text"])
            self.assertEqual(hashlib.sha256(loaded.encode()).hexdigest(), document["loaded_sha256"])

    def test_archived_baseline_replay_and_read_binding(self):
        responses = read("raw/responses.json")
        launches = read("raw/launches.json")
        reads = read("raw/reads.json")
        expected_ids = {label + str(n) for label in "ABCD" for n in (1, 2)}
        self.assertEqual(set(responses), expected_ids)
        self.assertEqual(set(launches), expected_ids)
        self.assertEqual(set(reads), expected_ids)
        for run_id in sorted(expected_ids):
            label = run_id[0]
            result = observer.evaluate(read("inputs/" + label + ".json"), responses[run_id]["raw_final"])
            self.assertEqual(result, responses[run_id]["observer_result"])
            self.assertEqual(launches[run_id]["fork_turns"], "none")
            recorded = reads[run_id]
            self.assertEqual(recorded["result"]["exit_code"], 0)
            self.assertFalse(recorded["result"]["timed_out"])
            stdout = (EXPERIMENT / recorded["stdout_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(stdout).hexdigest(), recorded["result"]["stdout_sha256"])
            inputs = [(EXPERIMENT / "task.md"), (EXPERIMENT / "inputs/context.json"),
                      (EXPERIMENT / ("inputs/" + label + ".json"))]
            self.assertEqual(stdout, b"".join(path.read_bytes() for path in inputs))
            for item in recorded["request"]["files_before"].values():
                self.assertNotIn("snapshot_error", item)


if __name__ == "__main__":
    unittest.main()
