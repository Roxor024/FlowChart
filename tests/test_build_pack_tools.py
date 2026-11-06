"""Full Build Pack tools: render_build_guide.py, check_pack.py and the compact example blueprint."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from _helpers import ROOT, SKILL, load

FIXTURE = ROOT / "tests" / "fixtures" / "sample-pack"
GUIDE = SKILL / "scripts" / "render_build_guide.py"
CHECK = SKILL / "scripts" / "check_pack.py"
COMPACT = SKILL / "assets" / "example-blueprint.compact.json"
VOID = {"meta", "input", "br", "link", "img", "path", "rect", "circle", "hr", "source"}


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, "-I", str(script), *map(str, args)], capture_output=True, text=True, cwd=cwd)


class _Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.bad, self.tags = [], [], []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.bad.append(tag)


class PackTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pack = Path(self.tmp.name) / "pack"
        shutil.copytree(FIXTURE, self.pack, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "evidence"))

    def tearDown(self):
        self.tmp.cleanup()

    def extras(self):
        return json.loads((self.pack / "guide-extras.json").read_text(encoding="utf-8"))

    def write_extras(self, data):
        (self.pack / "guide-extras.json").write_text(json.dumps(data), encoding="utf-8")

    def render(self):
        return run(GUIDE, "integration-blueprint.json", "guide-extras.json", "build-guide.html", cwd=self.pack)


class BuildGuide(PackTestCase):
    def test_renders_a_complete_honest_guide(self):
        res = self.render()
        self.assertEqual(res.returncode, 0, res.stderr)
        html = (self.pack / "build-guide.html").read_text(encoding="utf-8")
        p = _Balance()
        p.feed(html)
        self.assertEqual((p.bad, p.stack), ([], []), "unbalanced HTML")
        self.assertFalse(any(t == "script" for t, _ in p.tags), "no scripts")
        bp = json.loads((self.pack / "integration-blueprint.json").read_text(encoding="utf-8"))
        for task in bp["implementationTasks"]:
            self.assertIn(f'id="{task["id"]}"', html)
            self.assertIn(task["rollback"], html)
        for test in bp["testCases"]:
            self.assertIn(test["id"], html)
        self.assertGreaterEqual(html.count("NOT RUN"), len(bp["testCases"]))
        self.assertEqual(html.count("(NOT RUN)</span>"), len(bp["implementationTasks"]), "every task check is marked NOT RUN")
        self.assertIn("link not verified", html)
        for line in ("Validation: executed (validate_blueprint.py: PASS", "Deployment: not performed", "Human review: pending"):
            self.assertIn(line, html)
        self.assertNotIn("validated successfully", html.lower())

    def test_provisional_blueprint_shows_practice_banner(self):
        bp = json.loads((self.pack / "integration-blueprint.json").read_text(encoding="utf-8"))
        bp["status"] = "provisional"
        (self.pack / "integration-blueprint.json").write_text(json.dumps(bp), encoding="utf-8")
        res = self.render()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("PRACTICE VERSION. Not for real use.", (self.pack / "build-guide.html").read_text(encoding="utf-8"))

    def test_reuses_quick_design(self):
        data = self.extras()
        data.pop("architecture")
        data.pop("title")
        self.write_extras(data)
        shutil.copy(SKILL / "assets" / "quick-design.example.json", self.pack / "quick-design.json")
        res = run(GUIDE, "integration-blueprint.json", "guide-extras.json", "build-guide.html",
                  "--quick", "quick-design.json", cwd=self.pack)
        self.assertEqual(res.returncode, 0, res.stderr)
        html = (self.pack / "build-guide.html").read_text(encoding="utf-8")
        self.assertIn("Send new consignment orders from Dataverse to SAP", html)
        self.assertIn("Your company network", html)

    def test_refuses_bad_extras(self):
        cases = {
            "missing task": (lambda d: d["tasks"].pop("IMP-005"), "missing in extras.tasks"),
            "invented file": (lambda d: d["tasks"]["IMP-003"]["files"].append("nope.py"), "does not exist"),
            "unknown task": (lambda d: d["tasks"].__setitem__("IMP-999", d["tasks"]["IMP-003"]), "not a task"),
            "bad state": (lambda d: d["artifacts"][0].__setitem__("state", "DONE"), "state must be one of"),
            "http link": (lambda d: d["tasks"]["IMP-003"]["docs"][0].__setitem__("url", "http://x"), "https"),
            "no actions": (lambda d: d["tasks"]["IMP-003"].__setitem__("actions", []), "at least one action"),
            "claim": (lambda d: d.__setitem__("summary", "Validated successfully."), "claim"),
            "no architecture": (lambda d: d.pop("architecture"), "architecture"),
        }
        for name, (change, needle) in cases.items():
            with self.subTest(case=name):
                data = self.extras()
                change(data)
                self.write_extras(data)
                res = self.render()
                self.assertEqual(res.returncode, 1, f"{name}: {res.stdout}")
                self.assertIn(needle, res.stderr)
                self.assertFalse((self.pack / "build-guide.html").exists(), "no guide may be written")

    def test_refuses_dangling_test_reference(self):
        bp = json.loads((self.pack / "integration-blueprint.json").read_text(encoding="utf-8"))
        bp["implementationTasks"][0]["verification"] = "TST-001 and TST-777 in the test environment"
        (self.pack / "integration-blueprint.json").write_text(json.dumps(bp), encoding="utf-8")
        res = self.render()
        self.assertEqual(res.returncode, 1)
        self.assertIn("TST-777", res.stderr)

    def test_refuses_invalid_blueprint(self):
        bp = json.loads((self.pack / "integration-blueprint.json").read_text(encoding="utf-8"))
        bp["status"] = "finished"
        (self.pack / "integration-blueprint.json").write_text(json.dumps(bp), encoding="utf-8")
        res = self.render()
        self.assertEqual(res.returncode, 1)
        self.assertIn("REFUSED", res.stderr)

    def test_escapes_text(self):
        data = self.extras()
        data["tasks"]["IMP-003"]["actions"] = ["<script>alert(1)</script>"]
        self.write_extras(data)
        self.assertEqual(self.render().returncode, 0)
        html = (self.pack / "build-guide.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)


class CheckPack(PackTestCase):
    def test_clean_pack_passes_and_writes_evidence(self):
        res = run(CHECK, self.pack)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        for line in ("JSON parses", "XML well-formed", "Python compiles", "Local tests (synthetic data)",
                     "Blueprint validation", "No secrets in files", "Not a production sign-off"):
            self.assertIn(line, res.stdout)
        self.assertRegex(res.stdout, r"Local tests \(synthetic data\)\s+PASS")
        evidence = self.pack / "evidence" / "check-pack.txt"
        self.assertTrue(evidence.is_file())
        self.assertIn("sha256=", res.stdout)
        self.assertFalse(list(self.pack.rglob("__pycache__")), "pack is left clean")

    def test_detects_each_problem(self):
        problems = {
            "XML well-formed": ("apim/broken.xml", "<a><b></a>"),
            "Python compiles": ("function_app/broken.py", "x = (\n"),
            "JSON parses": ("broken.json", "{not json"),
            "No secrets in files": ("notes.txt", 'client_secret = "AbCdEfGhIjKlMnOp1234"'),
            "Local tests (synthetic data)": ("function_app/tests/test_fail.py",
                                             "import unittest\n\n\nclass F(unittest.TestCase):\n"
                                             "    def test_fails(self):\n        self.fail()\n"),
        }
        for check, (rel, content) in problems.items():
            with self.subTest(check=check):
                target = self.pack / rel
                target.write_text(content, encoding="utf-8")
                res = run(CHECK, self.pack)
                target.unlink()
                self.assertEqual(res.returncode, 1, res.stdout)
                self.assertRegex(res.stdout, rf"{check.replace('(', '[(]').replace(')', '[)]')}\s+FAIL")

    def test_unittest_runner_without_pytest(self):
        # CI installs only jsonschema, so the pack's tests must also run under plain unittest.
        res = run(CHECK, self.pack, "--runner", "unittest")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertRegex(res.stdout, r"Local tests \(synthetic data\)\s+PASS\s+unittest")

    def test_zero_tests_is_a_failure(self):
        (self.pack / "function_app" / "tests" / "test_intake.py").write_text("def test_plain():\n    pass\n", encoding="utf-8")
        res = run(CHECK, self.pack, "--runner", "unittest")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("no tests found", res.stdout)

    def test_bad_folder(self):
        self.assertEqual(run(CHECK, self.pack / "missing").returncode, 2)


class CompactExample(unittest.TestCase):
    def test_is_valid_without_warnings(self):
        validator = load("validate_blueprint")
        code, errors, warnings = validator.validate(json.loads(COMPACT.read_text(encoding="utf-8")))
        self.assertEqual((code, errors, warnings), (0, [], []))

    def test_small_and_referenced(self):
        self.assertLess(COMPACT.stat().st_size, 10_000)
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("assets/example-blueprint.compact.json", skill)
        procedure = (SKILL / "references" / "full-build-pack.md").read_text(encoding="utf-8")
        for value in ("check_pack.py", "render_build_guide.py", "--quick quick-design.json", "guide-extras.json",
                      "example-blueprint.compact.json", "Never write or edit `build-guide.html` by hand"):
            with self.subTest(value=value):
                self.assertIn(value, procedure)

    def test_skill_md_is_short(self):
        # Quick Design reads SKILL.md every time; full-pack rules live in references/full-build-pack.md.
        self.assertLess(len((SKILL / "SKILL.md").read_text(encoding="utf-8")), 10_500)


if __name__ == "__main__":
    unittest.main()
