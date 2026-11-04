"""Regression tests for fast mode, SAP transaction safeguards and provisional status."""
import unittest
from pathlib import Path
from _helpers import SKILL, fresh, run

class FastModesContract(unittest.TestCase):
    def test_default_is_quick_and_build_pack_opt_in(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertIn("Quick Design is the default", text)
        self.assertIn("Full Build Pack", text)
        self.assertIn("fewest Azure services", text)
    def test_outputs_are_mode_specific(self):
        text = (SKILL / "references/outputs.md").read_text()
        self.assertIn("Default: Quick Design", text)
        self.assertIn("Full Build Pack: opt-in", text)
    def test_sap_safety_and_language_mapping_guidance(self):
        text = (SKILL / "references/azure-patterns.md").read_text()
        for value in ("Auto Commit", "does not commit", "read the SAP document back", "en-US and en-GB", "zero matches", "LCID", "Synced"):
            with self.subTest(value=value):
                self.assertIn(value, text)
    def test_draft_with_blocking_question_warns(self):
        doc=fresh()
        doc["status"]="draft"
        doc["openQuestions"][0]["blocking"]=True
        code, errors, warnings=run(doc)
        self.assertEqual(code,0, errors)
        self.assertTrue(any("draft blueprint has blocking open questions" in w for w in warnings), warnings)
    def test_provisional_with_blocking_question_is_allowed(self):
        doc=fresh()
        doc["status"]="provisional"
        doc["openQuestions"][0]["blocking"]=True
        code, errors, warnings=run(doc)
        self.assertEqual(code,0, errors)
        self.assertFalse(any("draft blueprint has blocking" in w for w in warnings))
