"""Beginner-friendly Quick Design: template, worked example and HTML page stay consistent."""
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from _helpers import ROOT, SKILL, load

TEMPLATE = SKILL / "references" / "quick-design-template.md"
EXAMPLE_MD = ROOT / "examples" / "quick-design-dataverse-sap.md"
RENDERER = SKILL / "scripts" / "render_quick_design.py"
EXAMPLE_JSON = SKILL / "assets" / "quick-design.example.json"
SFTP_JSON = ROOT / "examples" / "quick-design-sftp.json"
rqd = load("render_quick_design")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

# Section headings in the order a Quick Design reply must use them.
ORDER = [
    "nothing has been built yet",
    "What you asked for, and what you'll get",
    "How it will work",
    "Architecture: which systems talk to each other",
    "Mistakes it protects you from",
    "Questions we need answered before we build",
    "What happens next",
    "Technical details for engineers",
    "Where things stand",
]


def positions(text, needles):
    return [text.find(n) for n in needles]


def question_blocks(text):
    section = text[text.index("Questions we need answered before we build"):text.index("## What happens next")]
    return re.split(r"\n\*\*\d+\. ", section)[1:]


class QuickDesignTemplate(unittest.TestCase):
    def test_skill_points_to_template(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/quick-design-template.md", skill)
        self.assertIn("make a practice version", skill)
        self.assertIn("No answer choices", skill)
        for gone in ("AskUserQuestion", "Reply like: 1A", "lettered"):
            with self.subTest(gone=gone):
                self.assertNotIn(gone, skill)
        for ref in ("references/outputs.md", "references/workflow.md"):
            self.assertIn("quick-design-template.md", (SKILL / ref).read_text(encoding="utf-8"), ref)

    def test_template_and_example_follow_section_order(self):
        for path in (TEMPLATE, EXAMPLE_MD):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                pos = positions(text, ORDER)
                self.assertNotIn(-1, pos, [n for n, p in zip(ORDER, pos) if p == -1])
                self.assertEqual(pos, sorted(pos), "sections out of order")

    def test_status_tags_and_honesty_lines(self):
        for path in (TEMPLATE, EXAMPLE_MD):
            text = path.read_text(encoding="utf-8")
            for value in ("Clear", "Needs detail", "Our guess", "Not yet", "Validation: not executed",
                          "Deployment: not performed", "Human review: pending"):
                with self.subTest(path=path.name, value=value):
                    self.assertIn(value, text)


class QuickDesignExample(unittest.TestCase):
    text = EXAMPLE_MD.read_text(encoding="utf-8")

    def test_at_most_five_questions_each_complete(self):
        blocks = question_blocks(self.text)
        self.assertTrue(1 <= len(blocks) <= 5, len(blocks))
        for i, block in enumerate(blocks, 1):
            with self.subTest(question=i):
                self.assertIn("Why we ask:", block)
                self.assertIn("For your tech team:", block)
                self.assertNotRegex(block, r"\*\*[A-D]\*\* ", "questions are open; no lettered choices")

    def test_questions_are_open(self):
        self.assertIn("Answer in your own words", self.text)
        self.assertNotRegex(self.text, r"`1[A-D] 2[A-D]", "no answer codes")

    def test_language_rule_outcome(self):
        rule = self.text[self.text.index("## The language rule"):self.text.index("## Mistakes")]
        self.assertRegex(rule, r"created: English, German, French")
        self.assertRegex(rule, r"skipped: Polish")
        self.assertRegex(rule, r"ignored: Dutch")
        self.assertIn("Needs checking", rule, "zero overlap must not be shown as Synced")

    def test_never_claims_validation_review_or_deployment(self):
        lowered = self.text.lower()
        for claim in ("validation: passed", "validated successfully", "approved by", "deployed to azure: yes",
                      "production-ready", "production ready"):
            with self.subTest(claim=claim):
                self.assertNotIn(claim, lowered)
        self.assertIn("0 of 5", self.text)


VOID = {"meta", "input", "br", "link", "img", "path", "rect", "circle", "hr", "source"}


class _Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.radios, self.stack, self.unbalanced = [], {}, [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag not in VOID:
            self.stack.append(tag)
        if tag == "input" and a.get("type") == "radio":
            self.radios.setdefault(a["name"], []).append(a.get("value", ""))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.unbalanced.append((tag, self.getpos()[0]))


class QuickDesignPage(unittest.TestCase):
    """Checks the page rendered from the packaged example; QuickDesignPageSftp reruns them on a second scenario."""
    source = EXAMPLE_JSON

    def setUp(self):
        doc = read_json(self.source)
        self.assertEqual(rqd.check(doc), [], self.source.name)
        self.html = rqd.render(doc)
        self.c = _Collector()
        self.c.feed(self.html)
        self.radios = sum(len(v) for v in self.c.radios.values())

    def test_self_contained(self):
        for tag, a in self.c.tags:
            with self.subTest(tag=tag):
                self.assertNotEqual(tag, "script", "no scripts")
                self.assertNotIn(tag, ("link", "iframe", "object", "embed"))
                for key in ("src", "href"):
                    value = a.get(key) or ""
                    self.assertFalse(value.startswith(("http:", "https:", "//")), f"remote {key}: {value}")
        self.assertNotIn("{{", self.html, "unfilled template holes")

    def test_tags_balanced(self):
        self.assertEqual(self.c.unbalanced, [], "mismatched closing tags")
        self.assertEqual(self.c.stack, [], "unclosed tags")

    def test_sections_and_questions(self):
        for needle in ("nothing has been built yet", "What you asked for, and what you’ll get", "How it will work",
                       "Architecture: which systems talk to each other", "Mistakes it protects you from",
                       "Questions we need answered before we build", "Technical details for engineers", "Where things stand"):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.html)
        n = len(read_json(self.source)["questions"])
        self.assertTrue(1 <= n <= 5)
        self.assertEqual(self.radios, 0, "questions are open: no radio buttons")
        self.assertIn("Answer in your own words", self.html)
        self.assertIn("<details open><summary>Technical details for engineers", self.html)

    def test_page_is_honest_about_sending(self):
        # A static page cannot send answers back: no fake submit buttons, and it says to reply in chat.
        self.assertFalse(any(tag in ("button", "form") for tag, _ in self.c.tags), "no buttons that do nothing")
        self.assertIn("this page can’t send anything", self.html.lower())
        self.assertIn("make a practice version", self.html)
        for line in ("Validation: not executed", "Deployment: not performed", "Human review: pending", "Not yet"):
            self.assertIn(line, self.html)
        for claim in ("validation: passed", "validated successfully", "production-ready", "production ready"):
            self.assertNotIn(claim, self.html.lower())
        n = len(read_json(self.source)["questions"])
        self.assertEqual(self.html.count("Why we ask:"), n)
        self.assertEqual(self.html.count("For your tech team:"), n)

    def test_accessible_basics(self):
        self.assertIn('<html lang="en">', self.html)
        for tag, a in self.c.tags:
            if tag == "svg" and a.get("role") != "img":
                self.assertEqual(a.get("aria-hidden"), "true", "decorative svg must be aria-hidden")
            if tag == "textarea":
                self.assertIn(f'for="{a.get("id")}"', self.html, "textarea needs a label")


class QuickDesignPageSftp(QuickDesignPage):
    source = SFTP_JSON


class RendererRules(unittest.TestCase):
    def broken(self, change):
        doc = copy.deepcopy(read_json(EXAMPLE_JSON))
        change(doc)
        return rqd.check(doc)

    def test_rejects_rule_breaks(self):
        cases = {
            "six questions": lambda d: d["questions"].append(copy.deepcopy(d["questions"][0])),
            "answer choices": lambda d: d["questions"][0].__setitem__("choices", ["Yes", "No"]),
            "missing why": lambda d: d["questions"][0].pop("why"),
            "no technical details": lambda d: d.pop("technical"),
            "skipping an area": lambda d: d["architecture"]["flow"].append({"from": 0, "to": 2, "text": "jump"}),
            "unknown status": lambda d: d["requirements"][0].__setitem__("status", "done"),
            "claims validation": lambda d: d.__setitem__("summary", "Validated successfully and ready."),
            "missing questions": lambda d: d.pop("questions"),
            "too many glossary terms": lambda d: d["glossary"].extend(d["glossary"] * 2),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                self.assertNotEqual(self.broken(change), [], f"{name} should be rejected")

    def test_escapes_user_text(self):
        doc = copy.deepcopy(read_json(EXAMPLE_JSON))
        doc["title"] = "<script>alert(1)</script> & co"
        page = rqd.render(doc)
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; co", page)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "page.html"
            ok = subprocess.run([sys.executable, "-I", str(RENDERER), str(EXAMPLE_JSON), str(out)],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertTrue(out.is_file())
            bad_doc = read_json(EXAMPLE_JSON)
            bad_doc["questions"][0]["choices"] = ["Yes", "No"]
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps(bad_doc), encoding="utf-8")
            out2 = Path(tmp) / "bad.html"
            res = subprocess.run([sys.executable, "-I", str(RENDERER), str(bad), str(out2)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("remove 'choices'", res.stderr)
            self.assertFalse(out2.exists(), "no page may be written for invalid content")
            res = subprocess.run([sys.executable, "-I", str(RENDERER), str(Path(tmp) / "missing.json"), str(out2)],
                                 capture_output=True, text=True)
            self.assertEqual(res.returncode, 2)

    def test_skill_points_to_renderer(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for value in ("scripts/render_quick_design.py", "assets/quick-design.example.json", "60 seconds",
                      "Never edit the HTML by hand", "reply in markdown using the template"):
            with self.subTest(value=value):
                self.assertIn(value, skill)
        self.assertFalse((SKILL / "assets" / "quick-design-page.html").exists(), "hand-written page was replaced")


if __name__ == "__main__":
    unittest.main()
