"""Regression cases carried over from the flowpilot-v0.3.1 branch (tests/test_blueprint.py there),
adapted to schema 0.4.0 and the v0.4 example. Every mutation must still be rejected."""
import copy
import unittest

from _helpers import fresh, run

OK, INVALID = 0, 1


def mutated(n):
    d = fresh()
    if n == 1: del d["risks"]
    elif n == 2: del d["requirements"][0]["title"]
    elif n == 3: d["requirements"] = "bad"
    elif n == 4: d["components"][0]["requirementIds"] = None
    elif n == 5: d["openQuestions"][0]["blocking"] = "no"
    elif n == 6: d["testCases"][0]["status"] = "done"
    elif n == 7: d["requirements"][0]["status"] = "bad"
    elif n == 8: d["components"].append(copy.deepcopy(d["components"][0]))
    elif n == 9: d["components"][0]["id"] = "REQ-001"
    elif n == 10: d["openQuestions"].append(copy.deepcopy(d["openQuestions"][0]))
    elif n == 11: d["components"][0]["requirementIds"] = ["REQ-999"]
    elif n == 12: d["components"][0]["requirementIds"] = []
    elif n == 13: d["requirements"][0]["id"] = "REQ-01"
    elif n == 14: d["requirements"][0] = "bad"
    elif n == 15: d["testCases"][0] = "bad"
    elif n == 16: d["openQuestions"][0] = "bad"
    elif n == 17: d.update(status="approved", reviewStatus="approved",
                           reviewEvidence={"reviewer": " ", "reviewedAt": "not a date", "evidenceRef": " "})
    elif n == 18: d.update(status="approved", reviewStatus="approved",
                           reviewEvidence={"reviewer": "Claude", "reviewedAt": "2026-11-01T10:00:00Z", "evidenceRef": "fake"})
    elif n == 19: d.update(status="approved", reviewStatus="unreviewed")
    elif n == 20: d.update(status="approved", reviewStatus="approved",  # blocking questions remain in the example
                           reviewEvidence={"reviewer": "Alice Smith", "reviewedAt": "2026-11-01T10:00:00Z", "evidenceRef": "approval-001"})
    elif n == 21: d["testCases"][0]["status"] = "passed"
    elif n == 22: d["testCases"][0].update(status="passed", evidenceRef="x", executedAt="yesterday", environment="x")
    elif n == 23: d["project"] = "SharedAccessKey=TESTSECRET123"
    elif n == 24: d["project"] = "sig=REALISTIC_SECRET_VALUE_123456"
    elif n == 25: d["project"] = "client_secret=TESTSECRET123456"
    elif n == 26: d["components"][0]["requirmentIds"] = ["REQ-001"]
    elif n == 27: d["status"] = "draft"; d["decisions"] = []; d["implementationTasks"] = []; d["risks"] = []
    elif n == 28: d["status"] = "draft"; d["requirements"][0]["acceptanceCriteria"] = "  "
    elif n == 29: d["schemaVersion"] = "0.1.0"
    elif n == 30: d["status"] = "draft"; d["testCases"] = [x for x in d["testCases"] if "REQ-004" not in x["requirementIds"]]
    elif n == 31: d["conflicts"] = [{"id": "CON-001", "title": "Resolved conflict", "status": "resolved",
                                      "requirementIds": ["REQ-001", "REQ-003"]}]
    return d


class V031Regression(unittest.TestCase):
    def test_reference_passes(self):
        code, errors, _ = run(fresh())
        self.assertEqual(code, OK, errors)

    def test_negative_cases(self):
        for n in range(1, 32):
            with self.subTest(case=n):
                code, errors, _ = run(mutated(n))
                self.assertEqual(code, INVALID, f"v0.3.1 negative case {n} was accepted")

    def test_provisional_empty_design_accepted(self):
        d = fresh()
        d.update(status="provisional", requirements=[{"id": "REQ-001", "title": "Connect CRM to SAP", "status": "unknown"}],
                 components=[], testCases=[], decisions=[], implementationTasks=[], risks=[],
                 openQuestions=[{"id": "QUE-001", "title": "Which SAP interface?", "blocking": True, "requirementIds": ["REQ-001"]}],
                 conflicts=[])
        code, errors, _ = run(d)
        self.assertEqual(code, OK, errors)

    def test_substring_reviewer_names_are_not_false_positives(self):
        """v0.3.1 matched substrings ('bot', 'model'), rejecting real people. v0.4 uses word boundaries."""
        for name in ("Jane Abbott", "Ms Modelski", "Tom Bottomley", "Ai Tanaka"):
            d = fresh()
            d.update(status="approved", reviewStatus="approved",
                     reviewEvidence={"reviewer": name, "reviewedAt": "2026-11-01T10:00:00Z", "evidenceRef": "CAB-1234"})
            for q in d["openQuestions"]:
                q["blocking"] = False
            for r in d["requirements"]:
                if r["status"] == "unknown":
                    r["status"] = "assumed"
            with self.subTest(name):
                code, errors, _ = run(d)
                self.assertEqual(code, OK, errors)


if __name__ == "__main__":
    unittest.main()
