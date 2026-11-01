#!/usr/bin/env python3
"""FlowPilot v0.3 offline validator: schema first, then cross-document checks."""
import json, re, sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/"schemas"/"integration-blueprint.schema.json"
SECTIONS=("requirements","components","decisions","implementationTasks","testCases","risks","openQuestions","conflicts")
AI_RE=re.compile(r"(?:claude|chatgpt|gpt|copilot|flowpilot|llm|ai assistant|artificial intelligence|bot|model)",re.I)
SECRET_RE=[re.compile(p,re.I) for p in (r"(?<!\w)(?:sig|client_secret|password|accountkey|sharedaccesskey)\s*[=:]\s*(?!\[REDACTED\])[^\s\",;}]{5,}",r"(?<!\w)(?:api[_-]?key|ocp-apim-subscription-key)\s*[=:]\s*(?!\[REDACTED\])[^\s\",;}]{5,}",r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",r"\beyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]+")]
def valid_text(v):
    return isinstance(v,str) and bool(v.strip()) and v.strip().lower() not in ("tbd","unknown","none","x","n/a","yesterday")
def collect_strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,list):
        for item in value:yield from collect_strings(item)
    elif isinstance(value,dict):
        for item in value.values():yield from collect_strings(item)
def parse_timestamp(value):
    if not isinstance(value,str):return False
    try:
        if not re.search(r"(?:Z|[+-][0-9]{2}:[0-9]{2})$",value):return False
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
        return dt.tzinfo is not None and bool(dt.utcoffset() is not None)
    except (ValueError,TypeError):return False
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
    components={x["id"] for x in doc["components"]}
    tasks={x["id"] for x in doc["implementationTasks"]}
    graph={}
    for task in doc["implementationTasks"]:
        for cid in task.get("componentIds",[]):
            if cid not in components:problems.append(task["id"]+" missing component "+cid)
        dependencies=task.get("dependsOn",[])
        graph[task["id"]]=dependencies
        for dep in dependencies:
            if dep not in tasks:problems.append(task["id"]+" missing task "+dep)
            if dep==task["id"]:problems.append(task["id"]+" self dependency")
    visited=set(); stack=set()
    def dfs(v):
        if v in stack:problems.append("task dependency cycle at "+v);return
        if v in visited:return
        stack.add(v)
        for w in graph.get(v,[]):
            if w in graph:dfs(w)
        stack.remove(v);visited.add(v)
    for node in graph:dfs(node)
    for r in reqs.values():
        if r["status"]=="conflicting" and not any(r["id"] in c["requirementIds"] for c in doc["conflicts"]):problems.append(r["id"]+" conflicting without CON record")
        if r["status"]=="confirmed" and doc["status"]!="provisional":
            if not valid_text(r.get("acceptanceCriteria")):problems.append(r["id"]+" lacks measurable acceptance criteria")
            if r["id"] not in tested:problems.append(r["id"]+" lacks a test case")
    if doc["status"]=="approved" or doc["reviewStatus"]=="approved":
        p=doc.get("reviewEvidence",{})
        if not valid_text(p.get("reviewer")) or AI_RE.search(str(p.get("reviewer","")).strip()):problems.append("approval requires identifiable human reviewer")
        if not valid_text(p.get("evidenceRef")):problems.append("approval requires meaningful evidence reference")
        if not parse_timestamp(p.get("reviewedAt")):problems.append("approval timestamp must be RFC3339 date-time")
        if any(r["status"] in ("unknown","conflicting") for r in reqs.values()):problems.append("approval blocked by unconfirmed requirements")
        if any(q["blocking"] for q in doc["openQuestions"]) or any(c["status"]=="open" for c in doc["conflicts"]):problems.append("approval blocked by unresolved requirements")
    for item in doc["testCases"]:
        if item["status"]=="not_run" and any(item.get(k) for k in ("evidenceRef","executedAt","environment","artifactHash")):problems.append(item["id"]+" not_run cannot carry execution evidence")
        if item["status"] in ("passed","failed"):
            if not parse_timestamp(item.get("executedAt")):problems.append(item["id"]+" invalid execution timestamp")
            if not all(valid_text(item.get(k)) for k in ("evidenceRef","environment","artifactHash")):problems.append(item["id"]+" missing independently reviewable test evidence")
            if not re.fullmatch(r"[0-9a-fA-F]{64}",str(item.get("artifactHash",""))):problems.append(item["id"]+" evidence digest must be SHA-256")
    if doc["status"]=="draft" and any(r["status"]=="confirmed" for r in reqs.values()) and any(not doc[section] for section in ("decisions","implementationTasks","risks")):problems.append("draft with confirmed requirements needs decisions, tasks and risk assessment")
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
        if structural:return ["schema "+"/".join(map(str,e.absolute_path))+": "+e.message for e in structural],True
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
    if errors:return 1 if ran else 3
    print("PASS: JSON Schema 2020-12 + semantic checks; NOT a production approval")
    return 0
if __name__=="__main__":sys.exit(main(sys.argv))
