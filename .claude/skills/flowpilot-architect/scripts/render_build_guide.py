#!/usr/bin/env python3
"""Render the beginner-friendly build guide (Full Build Pack) from the blueprint plus a small extras file.

The blueprint already holds requirements, components, tasks (with verification and rollback), tests,
risks and open questions. guide-extras.json adds only what a beginner needs on top: where to click,
the exact actions, files, documentation links and what to do if a step fails. Title, summary, glossary
and architecture can be reused from the Quick Design (--quick quick-design.json).

Usage: python render_build_guide.py <blueprint.json> <guide-extras.json> <build-guide.html> [--quick quick-design.json]
Exit codes: 0 guide written from a validated blueprint · 1 refused (invalid blueprint or extras; nothing written)
            · 2 unreadable input · 4 guide written, but validation NOT EXECUTED (jsonschema missing; marked on the page)
Every file named in the extras must exist next to the guide, so the guide cannot point at invented files.
Format of guide-extras.json: references/full-build-pack.md.
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATES = ("WORKING LOCAL EXAMPLE", "UNVERIFIED STARTER", "TEMPLATE ONLY", "REQUIRES CONTRACT")


def _load(name):
    spec = importlib.util.spec_from_file_location(f"_fp_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QD = _load("render_quick_design")
esc = QD.esc

CSS_EXTRA = """
.banner{border:2px solid #B45309;background:#FFF7ED;border-radius:14px;padding:16px 20px}.banner b{color:#9A3F07}
.unknown{border-left:4px solid #B91C1C;background:#FEF2F2;border-radius:12px;padding:16px 20px}.unknown ol{margin:8px 0 0 20px;padding:0}
.glance{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:12px}.glance div{border:1px solid #E2E6EB;border-radius:12px;padding:16px}
.task{border:1px solid #E2E6EB;border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:10px}
.task h3 .id{font-family:ui-monospace,Menlo,Consolas,monospace;color:#5B6573;font-weight:600;margin-right:8px}
.kv{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:6px 14px;font-size:15px}.kv dt{font-weight:700;margin:0}.kv dd{margin:0;color:#3D4652;overflow-wrap:anywhere}
.task ol{margin:0;padding-left:20px}.files code{background:#F1F4F8;padding:1px 6px;border-radius:4px;font-size:13px}
.unv{font-size:12px;font-weight:700;color:#9A3F07;background:#FFF7ED;border-radius:999px;padding:1px 8px;margin-left:6px}
.state{font-size:12px;font-weight:700;border-radius:999px;padding:2px 8px;white-space:nowrap}
.st-WORKING{background:#EAF6EF;color:#115E39}.st-UNVERIFIED,.st-TEMPLATE{background:#EEF1F5;color:#3D4652}.st-REQUIRES{background:#FEF2F2;color:#9B1C1C}
.notrun{font-weight:700;color:#9A3F07}
.task,.glance div{min-width:0;overflow-wrap:anywhere}
@media (max-width:720px){.kv{grid-template-columns:minmax(0,1fr)}.kv dt{margin-top:6px}}
"""


def check(bp, extras, pack: Path, quick):
    errors = []
    tasks = {t["id"]: t for t in bp.get("implementationTasks", [])}
    ext = extras.get("tasks", {})
    if not isinstance(ext, dict):
        return ["extras.tasks must be an object keyed by task ID (IMP-001 ...)"]
    for tid in tasks:
        e = ext.get(tid)
        if not isinstance(e, dict):
            errors.append(f"{tid}: missing in extras.tasks (every blueprint task needs actions)")
            continue
        if not (isinstance(e.get("actions"), list) and e["actions"]):
            errors.append(f"{tid}: needs at least one action")
        if not e.get("if_it_fails"):
            errors.append(f"{tid}: needs 'if_it_fails'")
        docs = e.get("docs", [])
        if not docs:
            errors.append(f"{tid}: needs at least one documentation link (mark unchecked ones verified: false)")
        for d in docs:
            if not (isinstance(d, dict) and d.get("title") and str(d.get("url", "")).startswith("https://")):
                errors.append(f"{tid}: docs entries need 'title' and an https 'url'")
        for f in e.get("files", []):
            if not (pack / f).is_file():
                errors.append(f"{tid}: file '{f}' does not exist in the pack")
    test_ids = {t["id"] for t in bp.get("testCases", [])}
    for tid, t in tasks.items():
        for ref in sorted(set(re.findall(r"TST-\d{3,}", str(t.get("verification", "")))) - test_ids):
            errors.append(f"{tid}: verification names {ref}, which is not a test in the blueprint")
    for tid in ext:
        if tid not in tasks:
            errors.append(f"extras.tasks has {tid}, which is not a task in the blueprint")
    for a in extras.get("artifacts", []):
        if a.get("state") not in STATES:
            errors.append(f"artifact {a.get('path')}: state must be one of {', '.join(STATES)}")
        if not (pack / str(a.get("path", ""))).exists():
            errors.append(f"artifact '{a.get('path')}' does not exist in the pack")
    if not extras.get("artifacts"):
        errors.append("extras.artifacts: list every generated file with its state")
    for key in ("prerequisites", "walkthrough", "troubleshooting"):
        if not extras.get(key):
            errors.append(f"extras.{key}: at least one entry")
    arch = extras.get("architecture") or (quick or {}).get("architecture")
    if not arch:
        errors.append("architecture: give extras.architecture or --quick quick-design.json")
    else:
        QD.check_architecture(arch, errors)
    text = json.dumps(extras, ensure_ascii=False).lower()
    for claim in QD.FORBIDDEN_CLAIMS + ("deployed successfully", "tested in azure"):
        if claim in text:
            errors.append(f"extras claim '{claim}': nothing in a build pack is validated in Azure or production-ready")
    return errors


def render(bp, extras, quick, validation) -> str:
    e = esc
    q = quick or {}
    title = extras.get("title") or q.get("title") or bp.get("project", "Integration build guide")
    summary = extras.get("summary") or q.get("summary") or bp.get("summary", "")
    status = bp.get("status")
    out = []
    w = out.append
    w('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
      '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
      f'<title>Build guide — {e(title)}</title>\n'
      f'<meta name="generator" content="FlowPilot render_build_guide.py {QD.VERSION}">\n'
      f'<style>{QD.CSS}{CSS_EXTRA}</style>\n</head>\n<body>\n')
    w('<div class="top"><div class="bar"><div class="brand">FlowPilot <span>/ Build guide</span></div>'
      f'<div class="draft">Blueprint status: {e(status)} · nothing deployed</div></div></div>\n<main class="wrap">\n')
    if status == "provisional":
        w('<div class="banner"><b>PRACTICE VERSION. Not for real use.</b> Built with sample data because some details are '
          'still unknown. Everything marked <b>REQUIRES CONTRACT</b> or <code>TODO</code> must be replaced first. '
          'Nothing has been deployed, and no person has reviewed it.</div>\n')
    elif status == "approved":
        w('<div class="banner"><b>Approval claimed in the blueprint.</b> Confirm it in your review system before relying on it. '
          'Nothing has been deployed.</div>\n')
    else:
        w('<div class="banner"><b>Draft.</b> Awaiting human review. Nothing has been deployed.</div>\n')
    if validation["code"] != 0:
        w('<div class="unknown"><b>Validation NOT EXECUTED.</b> The blueprint checker could not run here '
          f'({e(validation["reason"])}). Run <code>validate_blueprint.py</code> before using this guide.</div>\n')
    w(f'<h1>{e(title)}</h1>\n<p class="lead">{e(summary)}</p>\n')
    glossary = extras.get("glossary") or q.get("glossary")
    if glossary:
        w('<div class="tip"><strong>Words used:</strong> ' + " · ".join(
            f'<strong>{e(g["term"])}</strong>: {e(g["meaning"])}' for g in glossary) + '</div>\n')
    unknowns = extras.get("unknowns") or [x["title"] for x in bp.get("openQuestions", []) if x.get("blocking")]
    if unknowns:
        w('<div class="unknown"><b>Still unknown (the guide uses samples instead):</b><ol>'
          + "".join(f'<li>{e(u)}</li>' for u in unknowns) + '</ol></div>\n')

    tasks = bp.get("implementationTasks", [])
    services = sorted({c.get("azureService") for c in bp.get("components", []) if c.get("azureService")})
    w('<section class="card"><h2>At a glance</h2><div class="glance">'
      f'<div><strong>Steps</strong><br>{len(tasks)} build tasks, then the tests.</div>'
      f'<div><strong>Azure services</strong><br>{e(", ".join(services) or "see components")}</div>'
      f'<div><strong>You will need</strong><br>{e("; ".join(extras["prerequisites"][:4]))}</div>'
      f'<div><strong>Cost drivers</strong><br>{e(extras.get("cost_drivers", "See the Azure pricing calculator; no prices are given here."))}</div>'
      '</div>')
    if extras.get("not_used"):
        w(f'<div class="tip"><strong>Not used, on purpose:</strong> {e(extras["not_used"])}</div>')
    w('</section>\n')
    w(QD.architecture_html(extras.get("architecture") or q["architecture"]))

    w('<section class="card"><h2>Prepare</h2><ul>' + "".join(f'<li>{e(p)}</li>' for p in extras["prerequisites"])
      + '</ul></section>\n')

    w('<section class="card"><h2>Build it step by step</h2>')
    for t in tasks:
        x = extras["tasks"][t["id"]]
        w(f'<div class="task" id="{e(t["id"])}"><h3><span class="id">{e(t["id"])}</span>{e(t["title"])}</h3><dl class="kv">')
        w(f'<dt>Requirements</dt><dd>{e(", ".join(t.get("requirementIds", [])))}</dd>')
        if x.get("where"):
            w(f'<dt>Where</dt><dd>{e(x["where"])}</dd>')
        if t.get("prerequisites"):
            pre = t["prerequisites"] if isinstance(t["prerequisites"], list) else [t["prerequisites"]]
            w(f'<dt>Before you start</dt><dd>{e("; ".join(map(str, pre)))}</dd>')
        docs = "".join(f'<div><a href="{e(d["url"])}">{e(d["title"])}</a>'
                       + ('' if d.get("verified") else '<span class="unv">link not verified</span>') + '</div>'
                       for d in x.get("docs", []))
        w(f'<dt>Documentation</dt><dd>{docs}</dd>')
        files = x.get("files") or []
        w('<dt>Files</dt><dd class="files">' + (" ".join(f'<code>{e(f)}</code>' for f in files) or "No code required") + '</dd>')
        w('</dl><div><strong>Do this:</strong><ol>' + "".join(f'<li>{e(a)}</li>' for a in x["actions"]) + '</ol></div><dl class="kv">')
        w(f'<dt>Check it worked</dt><dd>{e(t.get("verification", ""))} <span class="notrun">(NOT RUN)</span></dd>')
        w(f'<dt>If it fails</dt><dd>{e(x["if_it_fails"])}</dd>')
        w(f'<dt>Undo</dt><dd>{e(t.get("rollback", ""))}</dd></dl></div>')
    w('</section>\n')

    w('<section class="card"><h2>Test as you go</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Test</th>'
      '<th>Expected result</th><th>State</th></tr></thead><tbody>')
    for t in bp.get("testCases", []):
        st = t.get("status", "not_run")
        label = "NOT RUN" if st == "not_run" else f"{st} (claim; evidence {t.get('evidenceRef', 'missing')})"
        w(f'<tr><td class="mono">{e(t["id"])}</td><td>{e(t["title"])}</td><td>{e(t.get("expectedResult", ""))}</td>'
          f'<td class="notrun">{e(label)}</td></tr>')
    w('</tbody></table></div></section>\n')

    w('<section class="card"><h2>Walk through one example</h2><ol>'
      + "".join(f'<li>{e(s)}</li>' for s in extras["walkthrough"]) + '</ol></section>\n')
    w('<section class="card"><h2>Fix problems</h2><div class="scroll"><table><thead><tr><th>You see</th><th>Likely cause</th>'
      '<th>What to do</th></tr></thead><tbody>' + "".join(
          f'<tr><td>{e(r["symptom"])}</td><td>{e(r["cause"])}</td><td>{e(r["fix"])}</td></tr>'
          for r in extras["troubleshooting"]) + '</tbody></table></div></section>\n')

    ops = bp.get("operations") or {}
    if ops:
        w('<section class="card"><h2>Run it day to day</h2><dl class="kv">')
        for k, v in ops.items():
            val = "; ".join(map(lambda i: i if isinstance(i, str) else json.dumps(i, ensure_ascii=False), v)) \
                if isinstance(v, list) else (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
            w(f'<dt>{e(k)}</dt><dd>{e(val)}</dd>')
        w('</dl></section>\n')

    w('<section class="card"><h2>Files and how ready they are</h2><div class="scroll"><table><thead><tr><th>File</th>'
      '<th>State</th><th>Note</th></tr></thead><tbody>')
    for a in extras["artifacts"]:
        cls = "st-" + a["state"].split()[0]
        w(f'<tr><td class="mono">{e(a["path"])}</td><td><span class="state {cls}">{e(a["state"])}</span></td>'
          f'<td>{e(a.get("note", ""))}</td></tr>')
    w('</tbody></table></div></section>\n')

    w('<details><summary>Technical appendix (requirements, decisions, risks, open questions)</summary>'
      '<div class="card" style="border:0;padding:16px 0 0">')
    w('<div class="scroll"><table><thead><tr><th>ID</th><th>Requirement</th><th>Status</th><th>Acceptance criteria</th></tr></thead><tbody>')
    for r in bp.get("requirements", []):
        ac = r.get("acceptanceCriteria") or []
        w(f'<tr><td class="mono">{e(r["id"])}</td><td>{e(r["title"])}</td><td>{e(r.get("status", ""))}</td>'
          f'<td>{e("; ".join(ac) if isinstance(ac, list) else ac)}</td></tr>')
    w('</tbody></table></div>')
    for label, key, fields in (("Decisions", "decisions", ("rationale", "alternative", "tradeoff")),
                               ("Risks", "risks", ("severity", "owner", "mitigation")),
                               ("Open questions", "openQuestions", ("blocking", "owner")),
                               ("Conflicts", "conflicts", ("status", "explanation", "resolution"))):
        items = bp.get(key, [])
        if items:
            w(f'<h3>{label}</h3><ul>')
            for it in items:
                extra = "; ".join(f"{f}: {it[f]}" for f in fields if f in it and it[f] not in ("", None))
                w(f'<li><span class="mono">{e(it["id"])}</span> {e(it["title"])}' + (f' — {e(extra)}' if extra else '') + '</li>')
            w('</ul>')
    w('</div></details>\n')

    if validation["code"] == 0:
        vline = f"Validation: executed (validate_blueprint.py: PASS, {validation['warnings']} warnings; not a human approval)"
    else:
        vline = f"Validation: not executed ({validation['reason']})"
    review = "Human review: pending" if bp.get("reviewStatus") != "approved" else \
        "Human review: approval claimed in the blueprint; confirm it in the review system"
    w(f'<div class="footer">{e(vline)}\nDeployment: not performed\n{e(review)}</div>\n</main>\n</body>\n</html>\n')
    return "".join(out)


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Render the FlowPilot build guide")
    ap.add_argument("blueprint")
    ap.add_argument("extras")
    ap.add_argument("output")
    ap.add_argument("--quick", help="quick-design.json to reuse title, summary, glossary and architecture")
    args = ap.parse_args(argv[1:])
    try:
        bp = json.loads(Path(args.blueprint).read_text(encoding="utf-8"))
        extras = json.loads(Path(args.extras).read_text(encoding="utf-8"))
        quick = json.loads(Path(args.quick).read_text(encoding="utf-8")) if args.quick else None
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read input: {exc}", file=sys.stderr)
        return 2
    out = Path(args.output)
    pack = out.resolve().parent

    validator = _load("validate_blueprint")
    code, verrors, warnings = validator.validate(bp, None, pack)
    if code == 1:
        for msg in verrors:
            print(f"ERROR: blueprint: {msg}", file=sys.stderr)
        print("REFUSED: fix the blueprint; no guide written.", file=sys.stderr)
        return 1
    validation = {"code": 0 if code == 0 else 3, "warnings": len(warnings),
                  "reason": "; ".join(verrors) or "validator could not run"}
    errors = check(bp, extras, pack, quick)
    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        print("REFUSED: fix guide-extras.json; no guide written.", file=sys.stderr)
        return 1
    out.write_text(render(bp, extras, quick, validation), encoding="utf-8")
    print(f"OK: wrote {out} ({len(bp.get('implementationTasks', []))} tasks, blueprint status {bp.get('status')}). "
          "Nothing was deployed; this is not a human approval.")
    return 0 if code == 0 else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv))
