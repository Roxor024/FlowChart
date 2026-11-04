#!/usr/bin/env python3
"""FlowPilot v0.4 offline blueprint validator (read-only).

Order of checks:
  1. JSON parsing                         -> exit 2 on failure
  2. JSON Schema 2020-12 (jsonschema)     -> exit 3 if jsonschema is not installed (validation NOT executed)
     date-time is enforced by a built-in checker, so no optional format packages are needed.
  3. Semantic checks (references, cycles, traceability, approval and evidence integrity, secrets)
                                          -> exit 1 on any error
Warnings never change the exit code. Exit 0 means "passed automated checks", never "approved".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

VERSION = "0.4.0"
SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "assets" / "integration-blueprint.schema.json"

EXIT_OK, EXIT_INVALID, EXIT_UNREADABLE, EXIT_NOT_EXECUTED = 0, 1, 2, 3

ID_SECTIONS = ("requirements", "components", "decisions", "implementationTasks",
               "testCases", "risks", "openQuestions", "conflicts")
PLACEHOLDERS = {"", "tbd", "tba", "todo", "unknown", "none", "n/a", "na", "x", "-", "?", "pending",
                "yesterday", "today", "later", "ok", "yes", "done"}
# Reviewer names that identify an AI, a tool or an automated process rather than a person.
AI_REVIEWER_RE = re.compile(
    r"\b(claude|anthropic|chatgpt|gpt[-\s]?\w*|openai|copilot|gemini|bard|llama|mistral|llm|"
    r"ai[-\s]+(?:assistant|reviewer|agent|bot|model)|assistant|bot|robot|flowpilot|automated|"
    r"automation|agent|validator|script)\b",
    re.IGNORECASE)
_NOT_PLACEHOLDER = r"(?!\[REDACTED\]|<|\$\{|\{\{|%|xxx|\*\*\*|example|placeholder|changeme|your[-_])"
SECRET_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in (
        # names that only ever hold credentials: any 12+ character value counts, letters only included
        r"(?<![\w-])(?:sharedaccesskey|accountkey|client[_-]?secret|api[_-]?key|apikey|access[_-]?key|"
        r"subscription[_-]?key|primary[_-]?key|secondary[_-]?key|sig)\s*[=:]\s*[\"']?" + _NOT_PLACEHOLDER +
        r"[^\s\"',;}&]{12,}",
        # generic words that also appear in prose: require a digit so "secret: rotated quarterly" is not flagged
        r"(?<![\w-])(?:password|passwd|pwd|secret|token)\s*[=:]\s*[\"']?" + _NOT_PLACEHOLDER +
        r"(?=[^\s\"',;}]*\d)[^\s\"',;}]{8,}",
        r"ocp-apim-subscription-key\s*[=:]\s*" + _NOT_PLACEHOLDER + r"[0-9a-z]{16,}",
        r"\bbearer\s+" + _NOT_PLACEHOLDER + r"[A-Za-z0-9._~+/=-]{20,}",
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----",
        r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"\b(?:sk|rk)_live_[0-9A-Za-z]{10,}",
        r"\bgh[pousr]_[A-Za-z0-9]{30,}",
        r"\bxox[abpr]-[A-Za-z0-9-]{10,}",
    )
]
# Delivery-guarantee wording that messaging systems cannot honour end to end (negations are allowed).
EXACTLY_ONCE_RE = re.compile(r"(?<!not )(?<!no )(?<!never )(?<!isn't )\b(?:exactly[- ]once|guaranteed (?:once|delivery)|"
                             r"never (?:lost|duplicated)|zero duplicates guaranteed)\b", re.IGNORECASE)
MEASURABLE_HINT = re.compile(
    r"\d|\b(every|each|all|no|zero|exactly|at most|at least|only|never|within|before|after|"
    r"returns?|rejects?|receives?|creates?|cannot|must|equals?|matches?)\b", re.IGNORECASE)


# ---------------------------------------------------------------- helpers
def meaningful(value: object) -> bool:
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDERS


def is_rfc3339(value: object) -> bool:
    """RFC 3339 date-time: date, 'T', time and an explicit offset or Z."""
    if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})", value):
        return False
    try:
        normalised = re.sub(r"\.\d+", "", value).replace("t", "T").replace("z", "Z").replace("Z", "+00:00")
        return datetime.fromisoformat(normalised).tzinfo is not None  # fractions stripped for Python 3.10
    except ValueError:
        return False


def strings_in(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings_in(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings_in(item)


def find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {node: WHITE for node in graph}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        colour[node] = GREY
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in colour:
                continue
            if colour[nxt] == GREY:
                return stack[stack.index(nxt):] + [nxt]
            if colour[nxt] == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        colour[node] = BLACK
        return None

    for node in graph:
        if colour[node] == WHITE:
            found = visit(node)
            if found:
                return found
    return None


# ---------------------------------------------------------------- schema
def schema_errors(doc: object, schema: dict) -> list[str]:
    import jsonschema  # ImportError handled by caller

    checker = jsonschema.FormatChecker()
    checker.checks("date-time")(is_rfc3339)  # enforce regardless of optional packages
    validator = jsonschema.Draft202012Validator(schema, format_checker=checker)
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    return [f"schema {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors]


def verify_artifact(evidence_dir: Path, ref: str, expected_hash: str) -> str | None:
    """Return None if evidence_dir/ref exists and its SHA-256 equals expected_hash, else a reason."""
    base = evidence_dir.resolve()
    target = (base / ref).resolve()
    if base != target and base not in target.parents:
        return f"evidenceRef {ref!r} points outside the evidence directory"
    if not target.is_file():
        return f"artifact {ref!r} not found in {evidence_dir}"
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    if actual.lower() != expected_hash.lower():
        return f"artifact {ref!r} SHA-256 is {actual}, blueprint claims {expected_hash}"
    return None


# ---------------------------------------------------------------- semantics
def semantic_checks(doc: dict, evidence_dir: Path | None = None) -> tuple[list[str], list[str]]:
    """Run after schema validation passed, so types and shapes can be trusted."""
    errors: list[str] = []
    warnings: list[str] = []
    status = doc["status"]
    provisional = status == "provisional"

    # unique IDs across the whole document
    seen: dict[str, str] = {}
    for section in ID_SECTIONS:
        for item in doc[section]:
            if item["id"] in seen:
                errors.append(f"duplicate ID {item['id']} ({seen[item['id']]} and {section})")
            seen[item["id"]] = section

    reqs = {r["id"]: r for r in doc["requirements"]}
    comps = {c["id"] for c in doc["components"]}
    tasks = {t["id"]: t for t in doc["implementationTasks"]}

    # requirement references everywhere
    referenced_by: dict[str, set[str]] = {rid: set() for rid in reqs}
    for section in ID_SECTIONS:
        for item in doc[section]:
            for ref in item.get("requirementIds", []):
                if ref not in reqs:
                    errors.append(f"{item['id']} references missing requirement {ref}")
                else:
                    referenced_by[ref].add(section)

    # task -> component and task -> task references, cycles
    used_components: set[str] = set()
    for task in tasks.values():
        for cid in task.get("componentIds", []):
            if cid not in comps:
                errors.append(f"{task['id']} references missing component {cid}")
            used_components.add(cid)
        for dep in task.get("dependsOn", []):
            if dep == task["id"]:
                errors.append(f"{task['id']} depends on itself")
            elif dep not in tasks:
                errors.append(f"{task['id']} depends on missing task {dep}")
    cycle = find_cycle({tid: [d for d in t.get("dependsOn", []) if d != tid] for tid, t in tasks.items()})
    if cycle:
        errors.append("implementation task dependency cycle: " + " -> ".join(cycle))
    if tasks:
        for cid in sorted(comps - used_components):
            warnings.append(f"{cid} is not implemented by any task (componentIds)")

    # requirement quality and traceability
    for rid, req in reqs.items():
        if req["status"] == "confirmed":
            criteria = req.get("acceptanceCriteria")
            if not meaningful(criteria):
                (warnings if provisional else errors).append(f"{rid} confirmed but lacks acceptance criteria")
            elif len(criteria.split()) < 4 or not MEASURABLE_HINT.search(criteria):
                warnings.append(f"{rid} acceptance criteria may not be measurable: {criteria!r}")
            if "testCases" not in referenced_by[rid]:
                (warnings if provisional else errors).append(f"{rid} confirmed but has no test case")

    # conflicts
    open_conflict_reqs: set[str] = set()
    for con in doc["conflicts"]:
        if len(set(con["requirementIds"])) < 2:
            errors.append(f"{con['id']} must reference at least two different requirements")
        if con["status"] == "open":
            open_conflict_reqs.update(con["requirementIds"])
        elif not meaningful(con.get("resolution")):
            errors.append(f"{con['id']} resolved without a resolution explanation")
    for rid, req in reqs.items():
        if req["status"] == "conflicting" and rid not in open_conflict_reqs:
            errors.append(f"{rid} is 'conflicting' but no open CON record references it")

    # design completeness for draft (provisional may be partial)
    if status in ("draft", "approved"):
        for section in ("components", "decisions", "implementationTasks", "testCases", "risks"):
            if not doc[section]:
                errors.append(f"status '{status}' requires a non-empty '{section}' "
                              f"(use status 'provisional' when requirements are insufficient)")
    if status == "draft" and any(q["blocking"] for q in doc["openQuestions"]):
        warnings.append("draft blueprint has blocking open questions; use provisional until blockers are resolved")
    if status == "draft" and (doc["conflicts"] and any(c["status"] == "open" for c in doc["conflicts"])):
        warnings.append("open conflicts present: consider status 'provisional' until resolved")

    # approval integrity
    if status == "approved":
        ev = doc["reviewEvidence"]
        reviewer = ev["reviewer"].strip()
        if not meaningful(reviewer) or len(reviewer) < 3 or not re.search(r"[A-Za-z]", reviewer):
            errors.append("approval requires an identifiable human reviewer")
        elif AI_REVIEWER_RE.search(reviewer):
            errors.append(f"approval reviewer {reviewer!r} looks like an AI, tool or automated process")
        if not meaningful(ev["evidenceRef"]) or len(ev["evidenceRef"].strip()) < 4:
            errors.append("approval requires a reference to an external review record")
        if any(q["blocking"] for q in doc["openQuestions"]):
            errors.append("approval blocked: blocking open questions remain")
        if any(c["status"] == "open" for c in doc["conflicts"]):
            errors.append("approval blocked: open conflicts remain")
        unresolved = [rid for rid, r in reqs.items() if r["status"] in ("unknown", "conflicting")]
        if unresolved:
            errors.append("approval blocked: requirements still unknown/conflicting: " + ", ".join(unresolved))
        if any(t["status"] == "failed" for t in doc["testCases"]):
            warnings.append("approved blueprint contains failed tests")
        warnings.append("approval is a CLAIM recorded in the blueprint; confirm "
                        f"{ev['evidenceRef']!r} in the review system before relying on it")
    elif "reviewEvidence" in doc and doc["reviewStatus"] == "unreviewed":
        warnings.append("reviewEvidence present but reviewStatus is 'unreviewed'")

    # test evidence integrity
    for test in doc["testCases"]:
        executed_fields = [k for k in ("executedAt", "evidenceRef", "artifactHash") if k in test]
        if test["status"] in ("passed", "failed"):
            missing = [k for k in ("evidenceRef", "executedAt", "environment", "artifactHash")
                       if not meaningful(test.get(k))]
            if missing:
                errors.append(f"{test['id']} is '{test['status']}' without execution evidence: missing {', '.join(missing)}")
            elif evidence_dir is None:
                warnings.append(f"{test['id']} '{test['status']}' evidence NOT VERIFIED (run with --evidence-dir to check the artifact hash)")
            else:
                problem = verify_artifact(evidence_dir, test["evidenceRef"], test["artifactHash"])
                if problem:
                    errors.append(f"{test['id']} evidence check failed: {problem}")
        elif executed_fields:
            errors.append(f"{test['id']} is '{test['status']}' but carries execution evidence ({', '.join(executed_fields)})")

    # unsupported delivery guarantees
    for section in ("requirements", "components", "decisions", "testCases"):
        for item in doc[section]:
            for key in ("acceptanceCriteria", "responsibility", "rationale", "expectedResult"):
                if isinstance(item.get(key), str) and EXACTLY_ONCE_RE.search(item[key]):
                    warnings.append(f"{item['id']} {key} claims an exactly-once/guaranteed delivery; state the "
                                    "idempotent business outcome instead (e.g. 'at most one target record per key')")

    # risk ownership
    for risk in doc["risks"]:
        if risk.get("severity") in ("critical", "high") and not meaningful(risk.get("owner")):
            warnings.append(f"{risk['id']} is {risk['severity']} severity without a named owner role")

    # secrets anywhere in the document
    for text in strings_in(doc):
        if any(p.search(text) for p in SECRET_PATTERNS):
            errors.append("possible credential in blueprint: redact it as [REDACTED] and rotate the exposed secret")
            break

    return errors, warnings


# ---------------------------------------------------------------- API
def validate(doc: object, schema: dict | None = None,
             evidence_dir: Path | None = None) -> tuple[int, list[str], list[str]]:
    """Return (exit_code, errors, warnings). Usable from tests without a subprocess."""
    if schema is None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        structural = schema_errors(doc, schema)
    except ImportError:
        return EXIT_NOT_EXECUTED, ["validation NOT EXECUTED: the 'jsonschema' package is not installed "
                                   "(pip install -r requirements-dev.txt)"], []
    if structural:
        return EXIT_INVALID, structural, []
    errors, warnings = semantic_checks(doc, evidence_dir)  # type: ignore[arg-type]
    return (EXIT_INVALID if errors else EXIT_OK), errors, warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="validate_blueprint.py", description=__doc__.splitlines()[0])
    parser.add_argument("blueprint")
    parser.add_argument("--evidence-dir", type=Path,
                        help="directory holding test result artifacts; passed/failed tests must match their SHA-256")
    args = parser.parse_args(argv[1:])  # usage errors exit 2
    try:
        doc = json.loads(Path(args.blueprint).read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"UNREADABLE: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE
    code, errors, warnings = validate(doc, schema, args.evidence_dir)
    for error in errors:
        print("ERROR:", error)
    for warning in warnings:
        print("WARNING:", warning)
    if code == EXIT_OK:
        print(f"PASS: schema {VERSION} + semantic checks ({len(warnings)} warnings). "
              "This is NOT a human approval or a production-readiness statement.")
    elif code == EXIT_NOT_EXECUTED:
        print("Validation: NOT EXECUTED")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
