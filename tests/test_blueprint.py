"""End-to-end schema + semantic regression: 31 invalid/edge mutations."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from validate_blueprint import validate
BASE=json.loads((ROOT/"examples/order-processing/integration-blueprint.json").read_text())
SCHEMA=json.loads((ROOT/"schemas/integration-blueprint.schema.json").read_text())
def bad_change(n):
 d=copy.deepcopy(BASE)
 if n==1:del d["risks"]
 elif n==2:del d["requirements"][0]["title"]
 elif n==3:d["requirements"]="bad"
 elif n==4:d["components"][0]["requirementIds"]=None
 elif n==5:d["openQuestions"][0]["blocking"]="no"
 elif n==6:d["testCases"][0]["status"]="done"
 elif n==7:d["requirements"][0]["status"]="bad"
 elif n==8:d["components"].append(copy.deepcopy(d["components"][0]))
 elif n==9:d["components"][0]["id"]="REQ-001"
 elif n==10:d["openQuestions"].append(copy.deepcopy(d["openQuestions"][0]))
 elif n==11:d["components"][0]["requirementIds"]=["REQ-999"]
 elif n==12:d["components"][0]["requirementIds"]=[]
 elif n==13:d["requirements"][0]["id"]="REQ-01"
 elif n==14:d["requirements"][0]="bad"
 elif n==15:d["testCases"][0]="bad"
 elif n==16:d["openQuestions"][0]="bad"
 elif n==17:d.update(status="approved",reviewStatus="approved",reviewEvidence={"reviewer":" ","reviewedAt":"not a date","evidenceRef":" "})
 elif n==18:d.update(status="approved",reviewStatus="approved",reviewEvidence={"reviewer":"Claude","reviewedAt":"2026-11-01T10:00:00Z","evidenceRef":"fake"})
 elif n==19:d.update(status="approved",reviewStatus="unreviewed")
 elif n==20:d.update(status="approved",reviewStatus="approved",reviewEvidence={"reviewer":"Alice Smith","reviewedAt":"2026-11-01T10:00:00Z","evidenceRef":"approval-001"})
 elif n==21:d["testCases"][0]["status"]="passed"
 elif n==22:d["testCases"][0].update(status="passed",evidenceRef="x",executedAt="yesterday",environment="x")
 elif n==23:d["project"]="SharedAccessKey=TESTSECRET123"
 elif n==24:d["project"]="sig=REALISTIC_SECRET_VALUE_123456"
 elif n==25:d["project"]="client_secret=TESTSECRET123456"
 elif n==26:d["components"][0]["requirmentIds"]=["REQ-001"]
 elif n==27:d["status"]="draft";d["decisions"]=[];d["implementationTasks"]=[];d["risks"]=[]
 elif n==28:d["status"]="draft";d["requirements"][0]["acceptanceCriteria"]="  "
 elif n==29:d["schemaVersion"]="0.1.0"
 elif n==30:d["status"]="draft";d["testCases"]=[x for x in d["testCases"] if "REQ-004" not in x["requirementIds"]]
 elif n==31:d["conflicts"]=[{"id":"CON-001","title":"Resolved conflict","status":"resolved","requirementIds":["REQ-001","REQ-003"]}]
 return d
class ValidationRegression(unittest.TestCase):
 def test_reference_passes(self):
  e,ran=validate(BASE,SCHEMA);self.assertTrue(ran);self.assertEqual(e,[])
 def test_negative_cases(self):
  for n in range(1,32):
   with self.subTest(case=n):
    e,ran=validate(bad_change(n),SCHEMA)
    self.assertTrue(ran,"jsonschema dependency missing")
    self.assertTrue(e,f"invalid case {n} was accepted")
 def test_missing_component_reference(self):
  d=copy.deepcopy(BASE);d["implementationTasks"][0]["componentIds"]=["CMP-999"]
  errors,_=validate(d,SCHEMA);self.assertTrue(any("missing component" in x for x in errors))
 def test_unknown_dependency(self):
  d=copy.deepcopy(BASE);d["implementationTasks"][0]["dependsOn"]=["IMP-999"]
  errors,_=validate(d,SCHEMA);self.assertTrue(any("missing task" in x for x in errors))
 def test_task_cycle(self):
  d=copy.deepcopy(BASE);d["implementationTasks"][0]["dependsOn"]=["IMP-002"]
  errors,_=validate(d,SCHEMA);self.assertTrue(any("cycle" in x for x in errors))
 def test_model_reviewer_rejected(self):
  d=copy.deepcopy(BASE);d.update(status="approved",reviewStatus="approved",reviewEvidence={"reviewer":"Claude Opus 5.5","reviewedAt":"2026-11-01T10:00:00Z","evidenceRef":"review-123"})
  errors,_=validate(d,SCHEMA);self.assertTrue(any("human reviewer" in x for x in errors))
 def test_invalid_review_date(self):
  d=copy.deepcopy(BASE);d.update(status="approved",reviewStatus="approved",reviewEvidence={"reviewer":"Alice Smith","reviewedAt":"yesterday","evidenceRef":"review-123"})
  errors,_=validate(d,SCHEMA);self.assertTrue(errors)
 def test_provisional_confirmed_without_test(self):
  d=copy.deepcopy(BASE);d["status"]="provisional";d["testCases"]=[];d["requirements"][0].pop("acceptanceCriteria")
  errors,_=validate(d,SCHEMA);self.assertFalse(any("lacks a test" in x for x in errors))
 def test_mutation_secret(self):
  d=copy.deepcopy(BASE);d["summary"]="api_key=sk_live_sample12345"
  errors,_=validate(d,SCHEMA);self.assertTrue(any("credential" in x for x in errors))
 def test_provisional_empty_design_accepted(self):
  d=copy.deepcopy(BASE)
  d["requirements"]=[{"id":"REQ-001","title":"Connect CRM to SAP","status":"unknown"}]
  d["components"]=[];d["testCases"]=[];d["decisions"]=[];d["implementationTasks"]=[];d["risks"]=[];d["openQuestions"]=[{"id":"QUE-001","title":"Which SAP interface?","blocking":True}]
  e,_=validate(d,SCHEMA);self.assertEqual(e,[])
 def test_redaction_allowed(self):
  d=copy.deepcopy(BASE);d["summary"]="SharedAccessKey=[REDACTED]"
  e,_=validate(d,SCHEMA);self.assertEqual(e,[])
if __name__=="__main__":unittest.main()
