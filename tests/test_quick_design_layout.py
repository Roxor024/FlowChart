"""Beginner-friendly Quick Design: template, worked example and HTML page stay consistent."""
import re
import unittest
from html.parser import HTMLParser

from _helpers import ROOT, SKILL

TEMPLATE = SKILL / "references" / "quick-design-template.md"
EXAMPLE_MD = ROOT / "examples" / "quick-design-dataverse-sap.md"
PAGE = SKILL / "assets" / "quick-design-page.html"

# Section headings in the order a Quick Design reply must use them.
ORDER = [
    "nothing has been built yet",
    "What you asked for, and what you'll get",
    "How it will work",
    "Architecture: which systems talk to each other",
    "Mistakes it protects you from",
    "quick questions before we build",
    "What happens next",
    "Technical details for engineers",
    "Where things stand",
]


def positions(text, needles):
    return [text.find(n) for n in needles]


def question_blocks(text):
    section = text[text.index("quick questions before we build"):text.index("## What happens next")]
    return re.split(r"\n\*\*\d+\. ", section)[1:]


class QuickDesignTemplate(unittest.TestCase):
    def test_skill_points_to_template(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/quick-design-template.md", skill)
        self.assertIn("make a practice version", skill)
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
                self.assertIn("Not sure", block)
                self.assertIn("For your tech team:", block)

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
    html = PAGE.read_text(encoding="utf-8")

    def setUp(self):
        self.c = _Collector()
        self.c.feed(self.html)

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
                       "quick questions before we build", "Technical details for engineers", "Where things stand"):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.html)
        self.assertTrue(1 <= len(self.c.radios) <= 5)
        for name, values in self.c.radios.items():
            with self.subTest(question=name):
                self.assertTrue(any(v.startswith("Not sure") for v in values), values)
        self.assertEqual(self.html.count("Why we ask:"), len(self.c.radios))
        self.assertEqual(self.html.count("For your tech team:"), len(self.c.radios))

    def test_accessible_basics(self):
        self.assertIn('<html lang="en">', self.html)
        for tag, a in self.c.tags:
            if tag == "svg" and a.get("role") != "img":
                self.assertEqual(a.get("aria-hidden"), "true", "decorative svg must be aria-hidden")
            if tag == "textarea":
                self.assertIn(f'for="{a.get("id")}"', self.html, "textarea needs a label")


if __name__ == "__main__":
    unittest.main()
