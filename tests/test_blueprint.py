import copy, json, unittest, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from validate_blueprint import check
BASE=json.loads((ROOT/"examples/order-processing/integration-blueprint.json").read_text())
class TestBlueprint(unittest.TestCase):
    def test_valid(self):self.assertEqual(check(BASE),[])
    def test_duplicate(self):
        d=copy.deepcopy(BASE);d["components"].append(dict(d["components"][0]));self.assertTrue(check(d))
    def test_reference(self):
        d=copy.deepcopy(BASE);d["components"][0]["requirementIds"]=["REQ-999"];self.assertTrue(check(d))
    def test_approval(self):
        d=copy.deepcopy(BASE);d["status"]="approved";self.assertTrue(check(d))
    def test_fake_pass(self):
        d=copy.deepcopy(BASE);d["testCases"][0]["status"]="passed";self.assertTrue(check(d))
    def test_secret(self):
        d=copy.deepcopy(BASE);d["project"]="SharedAccessKey=TEST";self.assertTrue(check(d))
if __name__=="__main__":unittest.main()
