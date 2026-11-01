#!/usr/bin/env python3
"""FlowPilot v0.3 offline validator: schema first, then cross-document checks."""
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/"assets"/"integration-blueprint.schema.json"
SECTIONS=("requirements","components","decisions","implementationTasks","testCases","risks","openQuestions","conflicts")
AI_RE=re.compile(r"^(?:claude|chatgpt|gpt[- ]?\w*|ai assistant|flowpilot|automated reviewer|llm|bot)$",re.I)
SECRET_RE=[re.compile(p,re.I) for p in (r"(?<!\w)(?:sig|client_secret|password|accountkey|sharedaccesskey)\s*[=:]\s*(?!\[REDACTED\])[^\s\",;}]{5,}",r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",r"\beyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]+")]
def valid_text(v):
    return isinstance(v,str) and bool(v.strip()) and v.strip().lower() not in ("tbd","unknown","none","x","n/a","yesterday")
def collect_strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,list):
        for item in value:yield from collect_strings(item)
    elif isinstance(value,dict):
        for item in value.values():yield from collect_strings(item)
def semantic(doc):
    problems=[]; identities={}; reqs={}; tested=set()
    for section in SECTIONS:
        for item in doc.get(section,[]):
            ident=item["id"]
            if ident in identities:problems.append(f"duplicate ID {ident} ({identities[ident]} and {section})")
            identities[ident]=section
            if section=="requirements":reqs[ident]=item
    for section in SECTIONS:
        for item in doc.get(section,[]):
            for ref in item.get("requirementIds",[]):
                if ref not in reqs:problems.append(f"{item['id']} references missing {ref}")
                if section=="testCases":tested.add(ref)
    for r in reqs.values():
        if r["status"]=="confirmed":
            if not valid_text(r.get("acceptanceCriteria")):problems.append(r["id"]+" lacks measurable acceptance criteria")
            if r["id"] not in tested:problems.append(r["id"]+" lacks a test case")
    if doc["status"]=="approved" or doc["reviewStatus"]=="approved":
        p=doc.get("reviewEvidence",{})
        if not valid_text(p.get("reviewer")) or AI_RE.fullmatch(str(p.get("reviewer","")).strip()):problems.append("approval requires identifiable human reviewer")
        if not valid_text(p.get("evidenceRef")):problems.append("approval requires meaningful evidence reference")
        if any(q["blocking"] for q in doc["openQuestions"]) or any(c["status"]=="open" for c in doc["conflicts"]):problems.append("approval blocked by unresolved requirements")
    for item in doc["testCases"]:
        if item["status"] in ("passed","failed"):
            if not all(valid_text(item.get(k)) for k in ("evidenceRef","environment","artifactHash")):problems.append(item["id"]+" missing independently reviewable test evidence")
            if not re.fullmatch(r"[0-9a-fA-F]{64}",str(item.get("artifactHash",""))):problems.append(item["id"]+" evidence digest must be SHA-256")
    if doc["status"]=="provisional" and doc["reviewStatus"]=="approved":problems.append("provisional cannot be approved")
    for c in doc["conflicts"]:
        if c["status"]=="resolved" and not valid_text(c.get("resolution")):problems.append(c["id"]+" resolved without explanation")
    for val in collect_strings(doc):
        if "[REDACTED]" in val:val=val.replace("[REDACTED]","")
        if any(p.search(val) for p in SECRET_RE):problems.append("possible credential detected (redact input and rotate exposed keys)");break
    return problems
def validate(doc,schema):
    try:
        import jsonschema
        checker=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
        structural=sorted(checker.iter_errors(doc),key=lambda e:list(map(str,e.absolute_path)))
        if structural:return ["schema "+"/".join(map(str,e.absolute_path))+": "+e.message for e in structural],False
    except ImportError:return ["full validation NOT EXECUTED: jsonschema unavailable"],False
    except Exception as ex:return ["schema processing error: "+type(ex).__name__+": "+str(ex)],False
    try:return semantic(doc),True
    except Exception as ex:return ["semantic processing error: "+type(ex).__name__+": "+str(ex)],True
def main(argv):
    if len(argv)!=2:
        print("Usage: validate_blueprint.py blueprint.json",file=sys.stderr);return 2
    try:
        doc=json.loads(Path(argv[1]).read_text(encoding="utf8"))
        schema=json.loads(SCHEMA.read_text(encoding="utf8"))
    except (OSError,UnicodeError,json.JSONDecodeError) as ex:
        print("INVALID INPUT:",str(ex),file=sys.stderr);return 2
    errors,ran=validate(doc,schema)
    for error in errors:print("ERROR:",error)
    if errors:return 1
    print("PASS: JSON Schema 2020-12 + semantic checks; NOT a production approval")
    return 0
if __name__=="__main__":sys.exit(main(sys.argv))
