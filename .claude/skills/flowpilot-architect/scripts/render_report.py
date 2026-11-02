#!/usr/bin/env python3
"""FlowPilot v0.4: render a readable, print-friendly HTML review report from a blueprint.

Fails closed: the blueprint is validated first, and an invalid (or unvalidated) blueprint is not rendered
unless --preview is given, in which case the report carries a prominent NOT VALIDATED banner and hides
any approval claim. Approvals are always shown as claims to verify, never as a trusted status.
Offline, no external assets. Every value is HTML-escaped and credential-like strings are masked.
Usage: render_report.py [--preview] [--evidence-dir DIR] <blueprint.json> <report.html>
Exit codes: 0 rendered from a valid blueprint · 1 refused (invalid) · 2 unreadable · 3 refused (validation not executed)
            · 4 preview rendered from an invalid or unvalidated blueprint
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import re
import json
import sys
from pathlib import Path

VERSION = "0.4.0"

CSS = """
:root{--ink:#18283b;--muted:#5a697b;--line:#e3e9f0;--bg:#f4f7fb;--warn:#8a4b00;--warnbg:#fff4e0;--ok:#1f6b3a;--okbg:#e7f5ec;--bad:#9b1c1c;--badbg:#fdecec}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:980px;margin:auto;padding:40px 20px}
header,section{background:#fff;padding:26px 28px;border:1px solid var(--line);border-radius:14px;margin-bottom:16px}
h1{font-size:30px;line-height:1.2;margin:.2em 0}h2{font-size:21px;margin:0 0 12px}h3{font-size:16px;margin:14px 0 6px}
.meta{color:var(--muted);font-size:14px}.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:13px;font-weight:600;margin-right:6px}
.warn{background:var(--warnbg);color:var(--warn)}.claim{background:#eef1f6;color:#33475b}.banner{padding:16px 20px;border-radius:12px;margin-bottom:16px;font-weight:600}.banner.bad{border:2px solid var(--bad)}.banner.warn{border:2px solid var(--warn)}table.trace{border-collapse:collapse;width:100%;font-size:13px}table.trace th,table.trace td{border:1px solid var(--line);padding:5px 7px;text-align:left;vertical-align:top}table.trace td.gap{background:var(--badbg);color:var(--bad);font-weight:600}.ok{background:var(--okbg);color:var(--ok)}.bad{background:var(--badbg);color:var(--bad)}
.item{border-top:1px solid var(--line);padding:10px 0}.item:first-of-type{border-top:0}.id{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:var(--muted)}
dl{display:grid;grid-template-columns:max-content 1fr;gap:2px 14px;margin:6px 0 0;font-size:14px}dt{color:var(--muted)}dd{margin:0}
ul{margin:4px 0 0 18px;padding:0}.empty{color:var(--muted);font-style:italic}
@media print{body{background:#fff}header,section{break-inside:avoid;border-color:#ccc}}
"""

FIELD_LABELS = {
    "status": "Status", "type": "Type", "priority": "Priority", "acceptanceCriteria": "Acceptance criteria",
    "source": "Source", "requirementIds": "Requirements", "azureService": "Azure service", "sku": "SKU / tier",
    "responsibility": "Responsibility", "description": "Description", "rationale": "Rationale",
    "alternative": "Alternative considered", "tradeoff": "Trade-off", "componentIds": "Components",
    "dependsOn": "Depends on", "prerequisites": "Prerequisites", "verification": "Verification",
    "rollback": "Rollback", "expectedResult": "Expected result", "evidenceRef": "Evidence",
    "executedAt": "Executed at", "environment": "Environment", "artifactHash": "Artifact SHA-256",
    "severity": "Severity", "owner": "Owner", "mitigation": "Mitigation", "evidence": "Evidence",
    "blocking": "Blocking", "explanation": "Why they conflict", "options": "Options", "resolution": "Resolution",
}
SECTIONS = [
    ("Requirements", "requirements"), ("Open conflicts and resolutions", "conflicts"),
    ("Questions to resolve", "openQuestions"), ("Architecture components", "components"),
    ("Architecture decisions", "decisions"), ("Implementation plan", "implementationTasks"),
    ("Test cases", "testCases"), ("Risk register", "risks"),
]


def _load_validator():
    spec = importlib.util.spec_from_file_location("_fp_validator", Path(__file__).with_name("validate_blueprint.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    VALIDATOR = _load_validator()
    SECRET_PATTERNS = VALIDATOR.SECRET_PATTERNS
except Exception:  # still mask secrets even if the validator file is missing
    VALIDATOR = None
    SECRET_PATTERNS = [re.compile(r"(?i)(sharedaccesskey|accountkey|password|secret|api[_-]?key|sig)\s*[=:]\s*\S{6,}")]


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def h(value: object) -> str:
    return html.escape(redact(str(value)), quote=True)


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return ", ".join(h(v) for v in value) if value else "—"
    return h(value)


def pill(text: str, kind: str) -> str:
    return f'<span class="pill {kind}">{h(text)}</span>'


def status_pill(doc: dict) -> str:
    return pill(f"Design: {doc.get('status', 'draft')}", "claim")


def validation_pill(validation: dict) -> str:
    code = validation.get("code")
    if code == 0:
        return pill("Automated checks: passed", "ok")
    if code == 3:
        return pill("Automated checks: NOT EXECUTED", "bad")
    if code is None:
        return pill("Automated checks: not run", "bad")
    return pill(f"Automated checks: FAILED ({len(validation.get('errors', []))} errors)", "bad")


def review_pill(doc: dict, trusted_blueprint: bool) -> str:
    ev = doc.get("reviewEvidence") if isinstance(doc.get("reviewEvidence"), dict) else None
    if doc.get("reviewStatus") == "approved" and ev:
        if not trusted_blueprint:
            return pill("Approval claim hidden: blueprint not validated", "bad")
        return pill(f"Approval CLAIMED — verify record {ev.get('evidenceRef', '?')}", "claim")
    return pill(f"Human review: {doc.get('reviewStatus', 'unreviewed')}", "warn")


def tests_pill(doc: dict) -> str:
    tests = doc.get("testCases", [])
    counts = {s: sum(1 for t in tests if t.get("status") == s) for s in ("passed", "failed", "blocked", "not_run")}
    kind = "bad" if counts["failed"] else ("ok" if tests and counts["passed"] == len(tests) else "warn")
    return pill(" · ".join(f"{v} {k.replace('_', ' ')}" for k, v in counts.items()) or "no tests", kind)


def render_item(item: dict) -> str:
    rows = "".join(f"<dt>{h(FIELD_LABELS.get(k, k))}</dt><dd>{fmt(v)}</dd>"
                   for k, v in item.items() if k not in ("id", "title"))
    return (f'<div class="item"><span class="id">{h(item.get("id", ""))}</span> '
            f'<strong>{h(item.get("title", ""))}</strong>{"<dl>" + rows + "</dl>" if rows else ""}</div>')


TRACE_COLUMNS = [("components", "Components"), ("decisions", "Decisions"), ("implementationTasks", "Tasks"),
                 ("testCases", "Tests"), ("risks", "Risks")]


def traceability(doc: dict) -> str:
    reqs = [r for r in doc.get("requirements", []) if isinstance(r, dict)] if isinstance(doc.get("requirements"), list) else []
    if not reqs:
        return '<p class="empty">No requirements recorded.</p>'
    links = {key: {} for key, _ in TRACE_COLUMNS}
    for key, _ in TRACE_COLUMNS:
        for item in doc.get(key, []) if isinstance(doc.get(key), list) else []:
            if isinstance(item, dict):
                for rid in item.get("requirementIds", []) if isinstance(item.get("requirementIds"), list) else []:
                    links[key].setdefault(rid, []).append(str(item.get("id", "?")))
    head = "<tr><th>Requirement</th><th>Status</th>" + "".join(f"<th>{h(t)}</th>" for _, t in TRACE_COLUMNS) + "</tr>"
    rows = []
    for r in reqs:
        cells = []
        for key, _ in TRACE_COLUMNS:
            ids = links[key].get(r.get("id"), [])
            gap = key == "testCases" and not ids and r.get("status") == "confirmed" and doc.get("status") != "provisional"
            cells.append(f'<td class="gap">no test</td>' if gap else f"<td>{fmt(ids) if ids else '—'}</td>")
        rows.append(f'<tr><td><span class="id">{h(r.get("id", ""))}</span> {h(r.get("title", ""))}</td>'
                    f'<td>{h(r.get("status", ""))}</td>{"".join(cells)}</tr>')
    return f'<table class="trace">{head}{"".join(rows)}</table>'


def render(doc: dict, validation: dict | None = None) -> str:
    """validation = {"code": int|None, "errors": [...], "warnings": [...]}; None means not validated."""
    validation = validation or {"code": None, "errors": [], "warnings": []}
    trusted = validation.get("code") == 0
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1">'
           f'<title>{h(doc.get("project", "FlowPilot review"))}</title><style>{CSS}</style></head><body><main>']
    out.append(f'<header><p class="meta">FLOWPILOT · INTEGRATION ENGINEERING REPORT · schema {h(doc.get("schemaVersion", "?"))}</p>'
               f'<h1>{h(doc.get("project", "Untitled integration"))}</h1>'
               f'<p>{status_pill(doc)}{validation_pill(validation)}{review_pill(doc, trusted)}{tests_pill(doc)}</p>'
               + (f'<p>{h(doc["summary"])}</p>' if doc.get("summary") else "")
               + f'<p class="meta">Data classification: {h(doc.get("dataClassification", "unknown"))}. '
                 'Proposed engineering blueprint; no deployment is implied.</p></header>')
    if not trusted:
        reason = ("validation was not executed" if validation.get("code") in (None, 3)
                  else f"{len(validation.get('errors', []))} validation errors")
        listing = "".join(f"<li>{h(e)}</li>" for e in validation.get("errors", [])[:20])
        out.insert(1, f'<div class="banner bad">PREVIEW — NOT VALIDATED ({h(reason)}). Do not use this report for '
                      f'decisions or approval.{"<ul>" + listing + "</ul>" if listing else ""}</div>')
    out.append(f"<section><h2>Traceability</h2>{traceability(doc)}</section>")
    for title, key in SECTIONS:
        items = [i for i in doc.get(key, []) if isinstance(i, dict)] if isinstance(doc.get(key), list) else []
        body = "".join(render_item(i) for i in items) if items else '<p class="empty">None recorded.</p>'
        out.append(f"<section><h2>{h(title)}</h2>{body}</section>")
    ops = doc.get("operations") if isinstance(doc.get("operations"), dict) else {}
    ops_html = "".join(f"<h3>{h(k.capitalize())}</h3><ul>{''.join('<li>' + h(v) + '</li>' for v in vals)}</ul>"
                       for k, vals in ops.items() if isinstance(vals, list) and vals) or '<p class="empty">None recorded.</p>'
    out.append(f"<section><h2>Operations</h2>{ops_html}</section>")
    ev = doc.get("reviewEvidence") if isinstance(doc.get("reviewEvidence"), dict) else None
    if doc.get("reviewStatus") == "approved" and ev and trusted:
        review = (f"Claimed: approved by {h(ev.get('reviewer'))} on {h(ev.get('reviewedAt'))}, record "
                  f"{h(ev.get('evidenceRef'))}. This is a claim in the blueprint, not an authenticated approval; "
                  "confirm it in the review system.")
    elif doc.get("reviewStatus") == "approved" and ev:
        review = "An approval is claimed, but it is not shown because the blueprint failed or skipped validation."
    else:
        review = "Pending. No human approval is recorded in this blueprint."
    if validation.get("code") == 0:
        checks = f"Passed schema and semantic checks ({len(validation.get('warnings', []))} warnings)."
    elif validation.get("code") in (None, 3):
        checks = "NOT EXECUTED."
    else:
        checks = f"FAILED with {len(validation.get('errors', []))} errors."
    warn_list = "".join(f"<li>{h(w)}</li>" for w in validation.get("warnings", []))
    out.append("<section><h2>Verification status</h2><dl>"
               f"<dt>Automated checks</dt><dd>{checks}{'<ul>' + warn_list + '</ul>' if warn_list else ''}</dd>"
               f"<dt>Human review</dt><dd>{review}</dd>"
               "<dt>Tests</dt><dd>Only results with recorded evidence count as executed; all others are proposals.</dd>"
               "<dt>Deployment</dt><dd>Not performed.</dd></dl></section></main></body></html>")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="render_report.py")
    parser.add_argument("blueprint")
    parser.add_argument("report")
    parser.add_argument("--preview", action="store_true",
                        help="render even if validation fails or cannot run, with a NOT VALIDATED banner")
    parser.add_argument("--evidence-dir", type=Path, help="passed to the validator to verify test artifacts")
    args = parser.parse_args(argv[1:])
    try:
        doc = json.loads(Path(args.blueprint).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"UNREADABLE: {exc}", file=sys.stderr)
        return 2
    if not isinstance(doc, dict):
        print("UNREADABLE: blueprint must be a JSON object", file=sys.stderr)
        return 2
    if VALIDATOR is None:
        code, errors, warnings = 3, ["validator script missing next to the renderer"], []
    else:
        code, errors, warnings = VALIDATOR.validate(doc, None, args.evidence_dir)
    if code != 0 and not args.preview:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        print("REFUSED: blueprint did not pass validation; no report written (use --preview for a marked draft).",
              file=sys.stderr)
        return 3 if code == 3 else 1
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(doc, {"code": code, "errors": errors, "warnings": warnings}), encoding="utf-8")
    print(out if code == 0 else f"{out} (PREVIEW — NOT VALIDATED)")
    return 0 if code == 0 else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv))
