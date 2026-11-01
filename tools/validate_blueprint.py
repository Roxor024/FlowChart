#!/usr/bin/env python3
"""FlowPilot v0.2: local schema and semantic validator, read-only."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SECTIONS=("requirements","components","decisions","implementationTasks","testCases","risks","conflicts")
def check(doc):
    errors=[];seen=set();requirements=set();used=set()
    if not isinstance(doc,dict):return ["not an object"]
    for section in SECTIONS:
        items=doc.get(section,[])
        if not isinstance(items,list):errors.append(section+" not an array");continue
        for item in items:
            if not isinstance(item,dict):errors.append(section+" non-object");continue
            ident=item.get("id")
            if not isinstance(ident,str) or not re.fullmatch(r"[A-Z]+-[0-9]{3,}",ident):errors.append(section+" malformed id")
            elif ident in seen:errors.append("duplicate ID "+ident)
            else:seen.add(ident)
            if section=="requirements" and isinstance(ident,str):requirements.add(ident)
    for section in SECTIONS:
        for item in doc.get(section,[]):
            if not isinstance(item,dict):continue
            for ref in item.get("requirementIds",[]):
                if ref not in requirements:errors.append(item.get("id","?")+" unknown requirement "+str(ref))
                else:used.add(ref)
    for item in doc.get("requirements",[]):
        if item.get("status")!="unknown" and not item.get("acceptanceCriteria"):errors.append(item.get("id","?")+" missing acceptance criteria")
        if item.get("status")!="unknown" and item.get("id") not in used:errors.append(item.get("id","?")+" not traceable")
    if any(not doc.get(s) for s in ("requirements","components","testCases")):errors.append("core arrays empty")
    if doc.get("status")=="approved" or doc.get("reviewStatus")=="approved":
        proof=doc.get("reviewEvidence") or {}
        if not all(proof.get(k) for k in ("reviewer","reviewedAt","evidence")):errors.append("approval evidence missing")
        if doc.get("status")!="approved" or doc.get("reviewStatus")!="approved":errors.append("inconsistent approval")
        if doc.get("conflicts") or any(q.get("blocking") for q in doc.get("openQuestions",[])):errors.append("approval blocked")
    for t in doc.get("testCases",[]):
        if t.get("status") in ("passed","failed") and not all(t.get(k) for k in ("evidence","executedAt","environment")):errors.append("test evidence missing "+t.get("id","?"))
    serialized=json.dumps(doc)
    for p in (r"SharedAccessKey\s*=",r"AccountKey\s*=",r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"):
        if re.search(p,serialized,re.I):errors.append("possible secret in blueprint")
    return errors
def main():
    if len(sys.argv)!=2:raise SystemExit("usage: python tools/validate_blueprint.py <blueprint.json>")
    doc=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    errors=check(doc)
    try:
        import jsonschema
        schema=json.loads((ROOT/"schemas/integration-blueprint.schema.json").read_text())
        errors.extend("schema: "+e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(doc))
    except ImportError:errors.append("NOT VERIFIED: jsonschema missing")
    for error in errors:print("FAIL:",error)
    if not errors:print("PASS: schema and semantic checks")
    return 1 if errors else 0
if __name__=="__main__":sys.exit(main())
