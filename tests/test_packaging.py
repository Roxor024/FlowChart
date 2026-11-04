"""Packaging, consistency and renderer tests."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from _helpers import EXAMPLE, ROOT, SKILL, fresh, renderer

VERSION = "0.4.0"


class SkillPackage(unittest.TestCase):
    def test_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", text, re.S)
        self.assertIsNotNone(match, "SKILL.md must start with name/description frontmatter")
        self.assertEqual(match.group(1), "flowpilot-architect")
        self.assertLessEqual(len(match.group(2)), 1024)

    def test_every_path_named_in_skill_md_exists_inside_skill(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        paths = set(re.findall(r"`((?:references|assets|scripts)/[\w./-]+)`", text))
        self.assertTrue(paths)
        for rel in paths:
            self.assertTrue((SKILL / rel).is_file(), f"SKILL.md references missing {rel}")
        self.assertNotRegex(text, r"`tools/|`schemas/|`examples/", "SKILL.md must not reference files outside the skill")

    def test_zip_is_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "skill.zip"
            p = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "package_skill.py"), str(out)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            names = set(zipfile.ZipFile(out).namelist())
        for rel in ("SKILL.md", "assets/integration-blueprint.schema.json", "assets/example-blueprint.json",
                    "scripts/validate_blueprint.py", "scripts/render_report.py", "references/azure-patterns.md"):
            self.assertIn("flowpilot-architect/" + rel, names)
        self.assertFalse(any("__pycache__" in n for n in names))

    def test_versions_consistent(self):
        schema = json.loads((SKILL / "assets/integration-blueprint.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schemaVersion"]["const"], VERSION)
        self.assertEqual(EXAMPLE["schemaVersion"], VERSION)
        for path, needle in ((SKILL / "SKILL.md", "v0.4"), (ROOT / "README.md", "v0.4"),
                             (ROOT / "CHANGELOG.md", "## 0.4.0"), (SKILL / "scripts/validate_blueprint.py", f'VERSION = "{VERSION}"'),
                             (SKILL / "scripts/render_report.py", f'VERSION = "{VERSION}"')):
            self.assertIn(needle, path.read_text(encoding="utf-8"), str(path))

    def test_example_copies_identical(self):
        repo_copy = json.loads((ROOT / "examples/order-processing/integration-blueprint.json").read_text(encoding="utf-8"))
        self.assertEqual(repo_copy, EXAMPLE, "examples/order-processing must mirror assets/example-blueprint.json")

    def test_all_example_blueprints_use_current_schema(self):
        for path in ROOT.glob("examples/*/integration-blueprint.json"):
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schemaVersion"], VERSION, str(path))


class RetryGuidance(unittest.TestCase):
    """Guards the P0 fix: retries/replays must never reuse the original MessageId."""
    FILES = [SKILL / "references/azure-patterns.md", SKILL / "SKILL.md", SKILL / "assets/example-blueprint.json",
             ROOT / "examples/order-processing/architecture.md"]

    def test_no_file_recommends_reusing_message_id(self):
        bad = re.compile(r"(keep|reuse|with) the same `?MessageId`?(?! for)|complete-and-reschedule|"
                         r"complete the message and schedule|resubmit[^.]*same MessageId", re.I)
        for path in self.FILES:
            with self.subTest(path.name):
                self.assertIsNone(bad.search(path.read_text(encoding="utf-8")), f"flawed retry advice in {path}")

    def test_identity_rule_present(self):
        text = (SKILL / "references/azure-patterns.md").read_text(encoding="utf-8")
        for needle in ("Scheduled messages take part in duplicate detection", "Never reuse the original `MessageId`",
                       "Never complete before the retry is durably scheduled", "Backstop — reconciliation"):
            self.assertIn(needle, text)


class Renderer(unittest.TestCase):
    def test_escapes_user_content(self):
        d = fresh()
        d["project"] = '<script>alert(1)</script><img src=x onerror=alert(2)>'
        d["requirements"][0]["acceptanceCriteria"] = '"><svg onload=alert(3)>'
        html = renderer.render(d)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<svg onload", html)
        self.assertNotIn("<img src=x", html)

    def test_shows_conflicts_criteria_evidence_and_operations(self):
        d = fresh()
        d["conflicts"].append({"id": "CON-001", "title": "VISIBLE-CONFLICT", "status": "open",
                               "requirementIds": ["REQ-001", "REQ-003"], "options": ["OPTION-A"]})
        d["testCases"][0].update(status="passed", evidenceRef="EVIDENCE-MARK", environment="test",
                                 executedAt="2026-10-01T00:00:00Z", artifactHash="c" * 64)
        html = renderer.render(d)
        for marker in ("VISIBLE-CONFLICT", "OPTION-A", "EVIDENCE-MARK", d["requirements"][0]["acceptanceCriteria"][:30],
                       "Operations", "traceparent"):
            self.assertIn(renderer.h(marker) if "<" in marker else marker, html)

    def approved_doc(self):
        d = fresh()
        d.update(status="approved", reviewStatus="approved",
                 reviewEvidence={"reviewer": "Jane Doe", "reviewedAt": "2026-10-30T10:00:00Z", "evidenceRef": "CAB-9"})
        for q in d["openQuestions"]:
            q["blocking"] = False
        for r in d["requirements"]:
            if r["status"] == "unknown":
                r["status"] = "assumed"
        return d

    def test_review_state_is_truthful(self):
        self.assertIn("No human approval is recorded", renderer.render(fresh(), {"code": 0, "errors": [], "warnings": []}))
        html = renderer.render(self.approved_doc(), {"code": 0, "errors": [], "warnings": []})
        self.assertIn("Claimed: approved by Jane Doe", html)
        self.assertIn("not an authenticated approval", html)
        self.assertNotIn('class="pill ok">Approval', html, "an approval must never be shown as a trusted green status")

    def test_unvalidated_render_hides_approval_and_shows_banner(self):
        html = renderer.render(self.approved_doc())   # no validation result supplied
        self.assertIn("PREVIEW — NOT VALIDATED", html)
        self.assertIn("Approval claim hidden", html)
        self.assertNotIn("Claimed: approved by Jane Doe", html)

    def cli(self, doc, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "bp.json"; src.write_text(json.dumps(doc), encoding="utf-8")
            out = Path(tmp) / "r.html"
            p = subprocess.run([sys.executable, "-I", str(ROOT / "tools/render_report.py"), *extra, str(src), str(out)],
                               capture_output=True, text=True)
            return p, (out.read_text(encoding="utf-8") if out.exists() else None)

    def test_cli_refuses_invalid_blueprint(self):
        d = self.approved_doc(); d["reviewEvidence"]["reviewer"] = "FlowPilot AI"
        p, html = self.cli(d)
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertIsNone(html, "no report may be written for an invalid blueprint")
        self.assertIn("REFUSED", p.stderr)

    def test_cli_preview_marks_invalid_report(self):
        d = self.approved_doc(); d["reviewEvidence"]["reviewer"] = "FlowPilot AI"
        p, html = self.cli(d, "--preview")
        self.assertEqual(p.returncode, 4, p.stderr)
        self.assertIn("PREVIEW — NOT VALIDATED", html)
        self.assertNotIn("FlowPilot AI on", html)

    def test_cli_valid_blueprint_renders_with_traceability(self):
        p, html = self.cli(fresh())
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Automated checks: passed", html)
        self.assertIn("<h2>Traceability</h2>", html)
        self.assertNotIn("NOT VALIDATED", html)

    def test_traceability_flags_untested_confirmed_requirement(self):
        d = fresh(); d["testCases"] = [t for t in d["testCases"] if "REQ-006" not in t["requirementIds"]]
        self.assertIn('class="gap">no test', renderer.traceability(d))

    def test_secrets_are_masked_in_report(self):
        d = fresh()
        d["summary"] = "Endpoint=sb://x.servicebus.windows.net/;SharedAccessKeyName=Root;SharedAccessKey=Zx9Q2mP7tL4vB8nK1rS6wY3="
        d["risks"][0]["evidence"] = "api_key=sk_live_0123456789abcdefABCDEF"
        html = renderer.render(d)
        self.assertNotIn("Zx9Q2mP7", html)
        self.assertNotIn("sk_live_0123", html)
        self.assertIn("[REDACTED]", html)

    def test_cli_handles_bad_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"; bad.write_text("[1,2", encoding="utf-8")
            p = subprocess.run([sys.executable, "-I", str(ROOT / "tools/render_report.py"), str(bad), str(Path(tmp) / "o.html")],
                               capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
