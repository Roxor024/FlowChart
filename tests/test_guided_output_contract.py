import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/".claude/skills/flowpilot-architect"
class GuidedOutputContract(unittest.TestCase):
 def test_references(self):
  s=(SKILL/"SKILL.md").read_text();self.assertIn("references/implementation-playbook.md",s)
  self.assertTrue((SKILL/"references/implementation-playbook.md").is_file())
 def test_expected_sections(self):
  s=(SKILL/"references/outputs.md").read_text()
  for text in ("Visible architecture diagram","EVERY implementationTask","NOT RUN","Technical appendix","new renderer"):
   with self.subTest(text=text):self.assertIn(text,s)
if __name__=="__main__":unittest.main()
