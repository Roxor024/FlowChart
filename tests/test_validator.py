"""Regression tests for scripts/validate_blueprint.py.

Case IDs (V01-V46, X01-X06) match the independent evaluation harnesses so results stay comparable.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from _helpers import ROOT, SKILL, approve, fresh, run, validator

OK, INVALID, UNREADABLE, NOT_EXECUTED = 0, 1, 2, 3
VALIDATOR = SKILL / "scripts" / "validate_blueprint.py"


def joined(errors):
    return "\n".join(errors)


class Accepts(unittest.TestCase):
    def assertAccepted(self, doc, max_warnings=None):
        code, errors, warnings = run(doc)
        self.assertEqual(code, OK, joined(errors))
        if max_warnings is not None:
            self.assertLessEqual(len(warnings), max_warnings, joined(warnings))
        return warnings

    def test_V01_example(self):
        self.assertAccepted(fresh(), max_warnings=1)  # baseline draft has blocking questions; new status warning is expected

    def test_V24_approved_with_human_evidence(self):
        self.assertAccepted(approve(fresh()))

    def test_X02_resolved_conflict_does_not_block_approval(self):
        d = approve(fresh())
        d["conflicts"].append({"id": "CON-001", "title": "Sync vs outage", "status": "resolved",
                               "requirementIds": ["REQ-001", "REQ-003"],
                               "resolution": "Business accepted 202 = accepted, not completed"})
        self.assertAccepted(d)

    def test_human_name_containing_ai_is_not_flagged(self):
        self.assertAccepted(approve(fresh(), reviewer="Ai Tanaka"))

    def test_V42_redacted_placeholder(self):
        d = fresh(); d["summary"] = "password=[REDACTED]"
        self.assertAccepted(d)

    def test_placeholders_are_not_flagged(self):
        d = fresh(); d["summary"] = "api_key=<from-key-vault> client_secret=${CLIENT_SECRET} apiKey: your-api-key-here"
        self.assertAccepted(d)

    def test_prose_about_secrets_is_not_flagged(self):
        d = fresh(); d["summary"] = "ERP secret: rotated quarterly via Key Vault; token: issued by Entra ID"
        self.assertAccepted(d)

    def test_fractional_seconds_and_offsets(self):
        self.assertAccepted(approve(fresh(), when="2026-10-30T10:00:00.5+01:00"))

    def test_provisional_examples(self):
        for name in ("vague-sap-crm", "conflicting-erp-sla"):
            doc = json.loads((ROOT / "examples" / name / "integration-blueprint.json").read_text(encoding="utf-8"))
            with self.subTest(name):
                self.assertAccepted(doc)

    def test_V34_well_formed_fabricated_evidence_is_undetectable(self):
        """Documented limit: offline checks cannot prove evidence is real. Guarded by instructions and CI."""
        d = fresh()
        d["testCases"][0].update(status="passed", evidenceRef="ci-run-42", environment="test",
                                 executedAt="2026-10-01T00:00:00Z", artifactHash="a" * 64)
        self.assertAccepted(d)


class Rejects(unittest.TestCase):
    def assertRejected(self, doc, fragment):
        code, errors, _ = run(doc)
        self.assertEqual(code, INVALID, "expected rejection, got PASS")
        self.assertIn(fragment, joined(errors))

    def mutate(self, fn):
        d = fresh(); fn(d); return d

    # structural
    def test_V02_missing_operations(self):
        self.assertRejected(self.mutate(lambda d: d.pop("operations")), "'operations' is a required property")

    def test_V03_wrong_type(self):
        self.assertRejected(self.mutate(lambda d: d["openQuestions"][0].update(blocking="yes")), "not of type 'boolean'")

    def test_V04_bad_status_enum(self):
        self.assertRejected(self.mutate(lambda d: d.update(status="production-ready")), "is not one of")

    def test_V05_bad_test_status(self):
        self.assertRejected(self.mutate(lambda d: d["testCases"][0].update(status="pass")), "is not one of")

    def test_V06_wrong_prefix(self):
        self.assertRejected(self.mutate(lambda d: d["components"][0].update(id="ABC-001")), "does not match")

    def test_X06_test_with_requirement_prefix(self):
        self.assertRejected(self.mutate(lambda d: d["testCases"][0].update(id="REQ-005")), "does not match")

    def test_V07_unknown_top_level_property(self):
        self.assertRejected(self.mutate(lambda d: d.update(deployNow=True)), "Additional properties")

    def test_X01_unknown_nested_property(self):
        self.assertRejected(self.mutate(lambda d: d["requirements"][0].update(approved=True)), "Additional properties")

    def test_V08_wrong_version(self):
        self.assertRejected(self.mutate(lambda d: d.update(schemaVersion="0.2.0")), "'0.4.0' was expected")

    def test_V09_empty_requirements(self):
        self.assertRejected(self.mutate(lambda d: d.update(requirements=[])), "should be non-empty")

    def test_X03_reviewer_wrong_type(self):
        self.assertRejected(approve(fresh(), reviewer=123), "is not of type 'string'")

    def test_X04_requirements_not_array(self):
        self.assertRejected(self.mutate(lambda d: d.update(requirements="abc")), "is not of type 'array'")

    def test_X05_question_not_object(self):
        self.assertRejected(self.mutate(lambda d: d.update(openQuestions=["x"])), "is not of type 'object'")

    # identifiers and references
    def test_V11_duplicate_id(self):
        self.assertRejected(self.mutate(lambda d: d["requirements"].append(dict(d["requirements"][0], title="dup"))),
                            "duplicate ID REQ-001")

    def test_V12_missing_requirement_in_component(self):
        self.assertRejected(self.mutate(lambda d: d["components"][0]["requirementIds"].append("REQ-999")),
                            "references missing requirement REQ-999")

    def test_V13_missing_requirement_in_question(self):
        self.assertRejected(self.mutate(lambda d: d["openQuestions"][0].update(requirementIds=["REQ-999"])),
                            "references missing requirement REQ-999")

    def test_V14_missing_component_in_task(self):
        self.assertRejected(self.mutate(lambda d: d["implementationTasks"][0]["componentIds"].append("CMP-999")),
                            "references missing component CMP-999")

    def test_V15_missing_task_dependency(self):
        self.assertRejected(self.mutate(lambda d: d["implementationTasks"][1]["dependsOn"].append("IMP-999")),
                            "depends on missing task IMP-999")

    def test_V16_self_dependency(self):
        self.assertRejected(self.mutate(lambda d: d["implementationTasks"][1]["dependsOn"].append("IMP-002")),
                            "depends on itself")

    def test_V17_dependency_cycle(self):
        self.assertRejected(self.mutate(lambda d: d["implementationTasks"][0].update(dependsOn=["IMP-003"])),
                            "dependency cycle")

    def test_V18_conflict_same_requirement_twice(self):
        self.assertRejected(self.mutate(lambda d: d["conflicts"].append(
            {"id": "CON-001", "title": "x", "status": "open", "requirementIds": ["REQ-001", "REQ-001"]})),
            "non-unique")

    def test_V19_conflicting_without_conflict_record(self):
        self.assertRejected(self.mutate(lambda d: d["requirements"][7].update(status="conflicting")),
                            "no open CON record")

    def test_resolved_conflict_needs_resolution(self):
        self.assertRejected(self.mutate(lambda d: d["conflicts"].append(
            {"id": "CON-001", "title": "x", "status": "resolved", "requirementIds": ["REQ-001", "REQ-003"]})),
            "'resolution' is a required property")

    # requirement quality
    def test_V20_confirmed_requirement_without_test(self):
        self.assertRejected(self.mutate(lambda d: d["testCases"].__setitem__(
            slice(None), [t for t in d["testCases"] if "REQ-002" not in t["requirementIds"]])),
            "REQ-002 confirmed but has no test case")

    def test_V22_placeholder_criteria(self):
        self.assertRejected(self.mutate(lambda d: d["requirements"][1].update(acceptanceCriteria="TBD")),
                            "lacks acceptance criteria")

    def test_V43_draft_without_decisions(self):
        self.assertRejected(self.mutate(lambda d: d.update(decisions=[])), "requires a non-empty 'decisions'")

    # approval integrity
    def test_V23_approved_without_evidence(self):
        self.assertRejected(self.mutate(lambda d: d.update(status="approved", reviewStatus="approved")),
                            "'reviewEvidence' is a required property")

    def test_V25_V27_ai_reviewers(self):
        for name in ("Claude", "Claude Opus 5.5", "FlowPilot AI", "ChatGPT", "automated reviewer", "GPT-4o", "Review Bot"):
            with self.subTest(name):
                self.assertRejected(approve(fresh(), reviewer=name), "looks like an AI")

    def test_V28_review_time_not_a_date(self):
        for when in ("yesterday", "2026-10-30", "30/10/2026 10:00"):
            with self.subTest(when):
                self.assertRejected(approve(fresh(), when=when), "is not a 'date-time'")

    def test_placeholder_evidence_reference(self):
        self.assertRejected(approve(fresh(), ref="TBD"), "external review record")

    def test_V29_blocking_question(self):
        d = approve(fresh()); d["openQuestions"][0]["blocking"] = True
        self.assertRejected(d, "blocking open questions")

    def test_V30_unknown_requirement(self):
        d = approve(fresh()); d["requirements"][7]["status"] = "unknown"
        self.assertRejected(d, "still unknown/conflicting")

    def test_V31_conflicting_requirement(self):
        d = approve(fresh()); d["requirements"][7]["status"] = "conflicting"
        d["requirements"][8]["status"] = "conflicting"
        d["conflicts"].append({"id": "CON-001", "title": "x", "status": "open", "requirementIds": ["REQ-008", "REQ-009"]})
        self.assertRejected(d, "open conflicts remain")

    def test_V32_review_approved_but_status_not(self):
        d = fresh(); d["reviewStatus"] = "approved"
        d["reviewEvidence"] = {"reviewer": "Jane Doe", "reviewedAt": "2026-10-30T10:00:00Z", "evidenceRef": "CAB-1"}
        self.assertRejected(d, "'approved' was expected")

    # test evidence integrity
    def test_V33_passed_without_evidence(self):
        self.assertRejected(self.mutate(lambda d: d["testCases"][0].update(status="passed")), "without execution evidence")

    def test_V35_not_run_with_evidence(self):
        self.assertRejected(self.mutate(lambda d: d["testCases"][0].update(evidenceRef="run-1")), "carries execution evidence")

    def test_V36_executed_at_not_a_date(self):
        self.assertRejected(self.mutate(lambda d: d["testCases"][0].update(
            status="passed", evidenceRef="run-42", environment="test", executedAt="last week", artifactHash="b" * 64)),
            "is not a 'date-time'")

    def test_hash_must_be_sha256(self):
        self.assertRejected(self.mutate(lambda d: d["testCases"][0].update(
            status="passed", evidenceRef="run-42", environment="test", executedAt="2026-10-01T00:00:00Z", artifactHash="abc")),
            "does not match")

    # secrets
    def test_V37_V41_secrets(self):
        samples = {
            "service bus": "Endpoint=sb://x.servicebus.windows.net/;SharedAccessKeyName=Root;SharedAccessKey=abcDEF123456ghiJKL=",
            "apim key": "Ocp-Apim-Subscription-Key: 0123456789abcdef0123456789abcdef",
            "api_key": "api_key=sk_live_0123456789abcdefABCDEF",
            "storage": "DefaultEndpointsProtocol=https;AccountName=a;AccountKey=Zm9vYmFyYmF6cXV4MTIzNDU2Nzg5MA==",
            "private key": "-----BEGIN PRIVATE KEY-----\nMIIE",
            "bearer": "Authorization: Bearer abcdefghijklmnopqrstuvwxyz0123456789",
            "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
            "client secret": "client_secret=Q8f~2xY9pLm4Vt7Rk1Zs",
            "sas": "https://a.blob.core.windows.net/c?sv=2022-11-02&sig=AbC123dEf456GhI789%3D",
            "letters-only api key (audit finding)": "api_key=AbCdEfGhIjKlMnOpQrStUvWx",
            "letters-only client secret": "client_secret: QwErTyUiOpAsDfGhJk",
            "quoted key": 'apiKey: "ZyXwVuTsRqPoNmLkJiHg"',
            "github token": "ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        }
        for label, secret in samples.items():
            with self.subTest(label):
                d = fresh(); d["risks"][0]["evidence"] = secret
                self.assertRejected(d, "possible credential")


class Warns(unittest.TestCase):
    def warnings_for(self, doc):
        code, errors, warnings = run(doc)
        self.assertEqual(code, OK, joined(errors))
        return joined(warnings)

    def test_V21_vague_criteria(self):
        d = fresh(); d["requirements"][1]["acceptanceCriteria"] = "fast"
        self.assertIn("may not be measurable", self.warnings_for(d))

    def test_V44_orphan_component(self):
        d = fresh(); d["components"].append({"id": "CMP-099", "title": "Unused", "requirementIds": ["REQ-001"]})
        self.assertIn("CMP-099 is not implemented by any task", self.warnings_for(d))

    def test_V45_high_risk_without_owner(self):
        d = fresh(); d["risks"][0]["owner"] = "TBD"
        self.assertIn("without a named owner", self.warnings_for(d))

    def test_exactly_once_claim_is_warned(self):
        d = fresh(); d["requirements"][4]["acceptanceCriteria"] = "Every valid row is processed exactly once into the target system"
        self.assertIn("claims an exactly-once", self.warnings_for(d))

    def test_negated_exactly_once_is_fine(self):
        d = fresh(); d["decisions"][4]["rationale"] = "Duplicate detection is not exactly-once processing"
        self.assertNotIn("claims an exactly-once", self.warnings_for(d))

    def test_provisional_gaps_are_warnings(self):
        doc = json.loads((ROOT / "examples/vague-sap-crm/integration-blueprint.json").read_text(encoding="utf-8"))
        self.assertIn("REQ-001 confirmed but has no test case", self.warnings_for(doc))


class EvidenceVerification(unittest.TestCase):
    def passed_doc(self, ref, digest):
        d = fresh()
        d["testCases"][0].update(status="passed", evidenceRef=ref, environment="test",
                                 executedAt="2026-10-01T00:00:00Z", artifactHash=digest)
        return d

    def test_unverified_evidence_is_warned(self):
        code, errors, warnings = run(self.passed_doc("results/tst-001.xml", "a" * 64))
        self.assertEqual(code, OK, errors)
        self.assertIn("evidence NOT VERIFIED", joined(warnings))

    def test_matching_artifact_passes(self):
        import hashlib
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "results").mkdir()
            artifact = Path(tmp) / "results" / "tst-001.xml"; artifact.write_bytes(b"<testsuite passed='1'/>")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            code, errors, warnings = validator.validate(self.passed_doc("results/tst-001.xml", digest), None, Path(tmp))
        self.assertEqual(code, OK, errors)
        self.assertNotIn("NOT VERIFIED", joined(warnings))

    def test_fabricated_hash_is_rejected_when_verified(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "r.xml").write_bytes(b"real result")
            code, errors, _ = validator.validate(self.passed_doc("r.xml", "a" * 64), None, Path(tmp))
        self.assertEqual(code, INVALID)
        self.assertIn("SHA-256 is", joined(errors))

    def test_missing_artifact_and_path_escape_rejected(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            for ref, msg in (("nope.xml", "not found"), ("../../etc/passwd", "outside the evidence directory")):
                with self.subTest(ref):
                    code, errors, _ = validator.validate(self.passed_doc(ref, "b" * 64), None, Path(tmp))
                    self.assertEqual(code, INVALID)
                    self.assertIn(msg, joined(errors))

    def test_approval_is_reported_as_claim(self):
        code, errors, warnings = run(approve(fresh()))
        self.assertEqual(code, OK, errors)
        self.assertIn("approval is a CLAIM", joined(warnings))


class CommandLine(unittest.TestCase):
    def cli(self, content, extra_code=None):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(content); path = f.name
        try:
            if extra_code:
                cmd = [sys.executable, "-I", "-c", extra_code, str(VALIDATOR), path]
            else:
                cmd = [sys.executable, "-I", str(VALIDATOR), path]
            return subprocess.run(cmd, capture_output=True, text=True)
        finally:
            os.unlink(path)

    def test_valid_exit_0(self):
        p = self.cli(json.dumps(fresh()))
        self.assertEqual(p.returncode, OK, p.stdout + p.stderr)
        self.assertIn("NOT a human approval", p.stdout)

    def test_invalid_exit_1(self):
        d = fresh(); d["status"] = "bogus"
        self.assertEqual(self.cli(json.dumps(d)).returncode, INVALID)

    def test_V10_malformed_json_exit_2_without_traceback(self):
        p = self.cli('{"schemaVersion": "0.4.0",')
        self.assertEqual(p.returncode, UNREADABLE)
        self.assertNotIn("Traceback", p.stderr)

    def test_V46_jsonschema_missing_exit_3(self):
        code = ("import sys,runpy;sys.modules['jsonschema']=None;p=sys.argv[1];sys.argv=['v',sys.argv[2]];"
                "runpy.run_path(p, run_name='__main__')")
        p = self.cli(json.dumps(fresh()), extra_code=code)
        self.assertEqual(p.returncode, NOT_EXECUTED)
        self.assertIn("NOT EXECUTED", p.stdout)
        self.assertNotIn("PASS", p.stdout)

    def test_tools_wrapper_matches(self):
        p = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "validate_blueprint.py"),
                            str(ROOT / "examples/order-processing/integration-blueprint.json")],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, OK, p.stdout + p.stderr)


class DateTime(unittest.TestCase):
    def test_rfc3339(self):
        good = ["2026-10-30T10:00:00Z", "2026-10-30T10:00:00+01:00", "2026-10-30T10:00:00.123456Z", "2026-10-30t10:00:00z"]
        bad = ["2026-10-30", "2026-10-30T10:00:00", "2026-13-01T00:00:00Z", "yesterday", "", 5]
        for v in good:
            self.assertTrue(validator.is_rfc3339(v), v)
        for v in bad:
            self.assertFalse(validator.is_rfc3339(v), v)


if __name__ == "__main__":
    unittest.main()
