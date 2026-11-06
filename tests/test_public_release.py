"""Public-release readiness: licence, public docs, and the fixes found in the timed order-status run."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from _helpers import ROOT, SKILL, load

PROCEDURE = (SKILL / "references" / "full-build-pack.md").read_text(encoding="utf-8")
DOCS = (SKILL / "references" / "azure-docs-example.md").read_text(encoding="utf-8")


class Licence(unittest.TestCase):
    def test_licence_in_repo_and_skill_zip(self):
        root = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", root)
        self.assertEqual((SKILL / "LICENSE.txt").read_text(encoding="utf-8"), root, "skill copy must match")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "skill.zip"
            subprocess.run([sys.executable, str(ROOT / "tools" / "package_skill.py"), str(out)], check=True,
                           capture_output=True)
            self.assertIn("flowpilot-architect/LICENSE.txt", zipfile.ZipFile(out).namelist())


class PublicDocs(unittest.TestCase):
    def test_no_internal_pilot_wording_or_planning_docs(self):
        for name in ("README.md", "docs/SECURITY.md"):
            text = (ROOT / name).read_text(encoding="utf-8").lower()
            with self.subTest(file=name):
                for phrase in ("internal-pilot", "internal pilot", "organizational pilot"):
                    self.assertNotIn(phrase, text)
        self.assertFalse((ROOT / "docs" / "PRODUCT-SPEC.md").exists())
        self.assertFalse((ROOT / "docs" / "GUIDED-BUILDER-v0.5.md").exists())

    def test_readme_has_install_disclaimer_and_licence(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for needle in ("## Install", "Customize > Skills", "## Disclaimer", "never deploys", "MIT License", "LICENSE"):
            with self.subTest(needle=needle):
                self.assertIn(needle, readme)

    def test_security_claims_match_ci(self):
        security = (ROOT / "docs" / "SECURITY.md").read_text(encoding="utf-8")
        ci = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / ".github" / "workflows").glob("*.yml"))
        if "gitleaks" not in ci:
            self.assertNotRegex(security, r"CI runs a gitleaks", "SECURITY.md must not claim a CI scan that doesn't exist")


class RunFixes(unittest.TestCase):
    def test_allowed_values_are_listed_and_match_the_schema(self):
        schema = json.loads((SKILL / "assets" / "integration-blueprint.schema.json").read_text(encoding="utf-8"))
        enums = set()

        def walk(node):
            if isinstance(node, dict):
                enums.update(node.get("enum", []))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        walk(schema)
        listed = set(re.findall(r"`([a-z_]+)`", PROCEDURE[:PROCEDURE.index("4. **Write the code")]))
        missing = sorted(e for e in enums if isinstance(e, str) and e not in listed)
        self.assertEqual(missing, [], "full-build-pack.md step 3 must list every allowed value")

    def test_guide_is_rendered_before_the_final_check(self):
        render = PROCEDURE.index("render_build_guide.py integration-blueprint.json")
        check = PROCEDURE.index("check_pack.py <pack dir>")
        self.assertLess(render, check, "render the guide first so check_pack also checks it")
        self.assertIn("not `build-guide.html` or `evidence/`", PROCEDURE)

    def test_xml_quoting_tip_example_is_well_formed(self):
        match = re.search(r"`(condition='[^`]+')`", PROCEDURE)
        self.assertIsNotNone(match, "XML quoting tip missing")
        ET.fromstring(f"<when {match.group(1)}/>")

    def test_docs_list_covers_common_services(self):
        urls = re.findall(r"https://\S+", DOCS)
        self.assertGreaterEqual(len(urls), 10)
        self.assertTrue(all(u.startswith("https://learn.microsoft.com/en-us/") for u in urls), urls)
        for service in ("api-management", "storage/tables", "key-vault", "event-grid", "secure-file-transfer-protocol",
                        "azure-functions", "logic-apps", "service-bus"):
            with self.subTest(service=service):
                self.assertTrue(any(service in u for u in urls))
        self.assertIn("at least one `docs` link", PROCEDURE)

    def test_answering_gives_an_updated_quick_design(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("When the user answers", skill)
        self.assertIn("Answering is not a request for the Full Build Pack", skill)
        for path in (SKILL / "references" / "quick-design-template.md", ROOT / "examples" / "quick-design-dataverse-sap.md"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertIn("updated page with the settled design", text)
                self.assertIn('"build it"', text)
                self.assertNotIn("You'll get the real plan", text)
        rqd = load("render_quick_design")
        page = rqd.render(json.loads((SKILL / "assets" / "quick-design.example.json").read_text(encoding="utf-8")))
        self.assertIn("updated page with the settled design", page)
        self.assertIn('<span class="mono">build it</span>', page)
        self.assertNotIn("get the real plan", page)


if __name__ == "__main__":
    unittest.main()
