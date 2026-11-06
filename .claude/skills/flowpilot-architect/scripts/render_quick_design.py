#!/usr/bin/env python3
"""Render a FlowPilot Quick Design page from a small JSON file.

The model writes only the content (quick-design.json); this script owns the layout, so every
page looks the same and no HTML has to be written by hand. Standard library only.

Usage: python render_quick_design.py quick-design.json quick-design.html
Exit codes: 0 page written · 1 content breaks the Quick Design rules (nothing written) · 2 unreadable input
The input format is documented in references/quick-design-template.md; see assets/quick-design.example.json.
"""
import html
import json
import sys
from pathlib import Path

VERSION = "0.4.0"
STATUS = {"clear": ("Clear", "tag-clear"), "needs_detail": ("Needs detail", "tag-detail"),
          "our_guess": ("Our guess", "tag-guess")}
FORBIDDEN_CLAIMS = ("validation: passed", "validated successfully", "production-ready", "production ready")


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def check(doc) -> list[str]:
    """Return rule violations; an empty list means the page may be rendered."""
    errors = []

    def need(cond, msg):
        if not cond:
            errors.append(msg)

    if not isinstance(doc, dict):
        return ["top level must be a JSON object"]
    for key in ("title", "summary", "requirements", "outcomes", "steps", "architecture", "questions"):
        need(key in doc, f"missing '{key}'")
    if errors:
        return errors
    need(isinstance(doc["title"], str) and doc["title"].strip(), "title must be text")
    need(isinstance(doc["summary"], str) and doc["summary"].strip(), "summary must be text")
    reqs = doc["requirements"]
    need(isinstance(reqs, list) and 1 <= len(reqs) <= 12, "requirements: 1-12 items")
    for i, r in enumerate(reqs if isinstance(reqs, list) else [], 1):
        need(isinstance(r, dict) and r.get("text"), f"requirement {i}: needs 'text'")
        need(isinstance(r, dict) and r.get("status") in STATUS,
             f"requirement {i}: status must be one of {', '.join(STATUS)}")
    need(isinstance(doc["outcomes"], list) and 2 <= len(doc["outcomes"]) <= 5, "outcomes: 2-5 checks")
    steps = doc["steps"]
    need(isinstance(steps, list) and 2 <= len(steps) <= 5, "steps: 2-5 steps")
    for i, s in enumerate(steps if isinstance(steps, list) else [], 1):
        need(isinstance(s, dict) and s.get("title") and s.get("text"), f"step {i}: needs 'title' and 'text'")

    check_architecture(doc["architecture"], errors)

    qs = doc["questions"]
    need(isinstance(qs, list) and 1 <= len(qs) <= 5, "questions: 1-5 (never more than five)")
    for i, q in enumerate(qs if isinstance(qs, list) else [], 1):
        if not isinstance(q, dict):
            errors.append(f"question {i}: must be an object")
            continue
        for key in ("title", "why", "tech"):
            need(isinstance(q.get(key), str) and q[key].strip(), f"question {i}: needs '{key}'")
        need("choices" not in q, f"question {i}: questions are open; remove 'choices' (the user answers in their own words)")
    tech = doc.get("technical")
    need(isinstance(tech, dict) and any(tech.get(k) for k in ("requirements", "steps", "notes")),
         "technical: required, with at least one of requirements, steps or notes (engineers read it)")
    need(len(doc.get("protections", [])) <= 4, "protections: at most 4")
    need(len(doc.get("glossary", [])) <= 6, "glossary: at most 6 terms")

    text = json.dumps(doc, ensure_ascii=False).lower()
    for claim in FORBIDDEN_CLAIMS:
        need(claim not in text, f"content claims '{claim}': a Quick Design is never validated or production-ready")
    return errors


CSS = """
*{box-sizing:border-box}body{margin:0;background:#F4F6F8;color:#17202B;font:16px/1.55 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
.mono,code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.top{background:#FFF;border-bottom:1px solid #E2E6EB}.bar{max-width:1200px;margin:0 auto;padding:14px 24px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
.brand{font-weight:700}.brand span{font-weight:400;color:#5B6573}
.draft{background:#FFF7ED;color:#9A3F07;border:1px solid #F6D7B8;padding:6px 12px;border-radius:999px;font-size:14px;font-weight:600}
.wrap{max-width:1200px;margin:0 auto;padding:32px 24px 72px;display:flex;flex-direction:column;gap:28px}
.steps-bar{display:flex;flex-wrap:wrap;gap:8px}.steps-bar span{padding:8px 14px;border-radius:999px;font-size:14px;font-weight:600;background:#FFF;border:1px solid #D5DAE0;color:#4A5563}
.steps-bar .done{background:#EAF6EF;border-color:#EAF6EF;color:#115E39}.steps-bar .now{background:#1F5FD1;border-color:#1F5FD1;color:#FFF}
h1{margin:0;font-size:40px;line-height:1.15;font-weight:800;letter-spacing:-.02em;max-width:820px}.lead{margin:0;font-size:19px;color:#3D4652;max-width:820px}
.cols{display:flex;flex-wrap:wrap;gap:28px;align-items:flex-start}.main{flex:999 1 560px;min-width:0;display:flex;flex-direction:column;gap:28px}.side{flex:1 1 300px;min-width:0;display:flex;flex-direction:column;gap:20px}
.card{background:#FFF;border:1px solid #E2E6EB;border-radius:16px;padding:28px;display:flex;flex-direction:column;gap:20px}
h2{margin:0;font-size:24px}.sub{margin:0;color:#4A5563}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:16px;align-items:start}
.box{border:1px solid #E2E6EB;border-radius:12px;padding:20px;display:flex;flex-direction:column;gap:12px}
.good{border:2px solid #157347;background:#F6FBF8}
h3{margin:0;font-size:18px}ol.reqs{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:10px}
ol.reqs li{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.tag{flex:none;padding:2px 8px;border-radius:999px;font-size:13px;font-weight:700}.tag-clear{background:#EAF6EF;color:#115E39}.tag-detail{background:#FFF7ED;color:#9A3F07}.tag-guess{background:#EEF1F5;color:#3D4652}
.note{font-size:13px;color:#4A5563}ul.checks{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:10px}ul.checks li::before{content:"\\2713";color:#157347;font-weight:700;margin-right:8px}
.example{font-size:14px;background:#FFF;border:1px solid #D5E9DD;border-radius:10px;padding:12px;color:#3D4652}
.flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,128px),1fr));gap:12px}
.step{background:#F7F9FC;border:1px solid #E2E6EB;border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:6px}.step.last{background:#EAF6EF;border-color:#BFE3CD}
.step small{font-weight:700;color:#5B6573;font-size:13px}.step b{font-size:16px}.step span{font-size:14px;color:#4A5563}
.tip{background:#F7F9FC;border-radius:12px;padding:16px}
.arch{display:flex;align-items:stretch;gap:0;overflow-x:auto}
.area{flex:1 1 0;min-width:190px;border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:12px}
.area0{background:#F4F1FA}.area1{background:#EEF3FC}.area2{background:#F6F3EE}
.area h4{margin:0;min-height:2.6em;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#3D4652}
.sys{background:#FFF;border:1px solid #C9D0D8;border-radius:12px;padding:12px;text-align:center;font-size:14px}.sys.core{border:2px solid #1F5FD1}.sys b{display:block;font-size:16px}
.sys.support{border-style:dashed;font-size:13px}.sys.support b{font-size:14px}
.link{flex:none;width:84px;display:flex;flex-direction:column;justify-content:center;gap:10px;align-items:center;font-weight:700;color:#3D4652}
.n{display:inline-flex;width:24px;height:24px;border-radius:999px;background:#17202B;color:#FFF;font-size:13px;align-items:center;justify-content:center;flex:none}
.legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,170px),1fr));gap:12px;font-size:14px}.legend div{display:flex;gap:10px}
.rule{display:flex;flex-direction:column;gap:8px}.rule div{display:flex;gap:10px}.rule b{min-width:120px}
.protect{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,170px),1fr));gap:12px}.protect div{border:1px solid #E2E6EB;border-radius:12px;padding:16px}.protect span{display:block;font-size:14px;color:#4A5563}
ol.qs{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:12px}
ol.qs li{border:1px solid #E2E6EB;border-radius:14px;padding:18px 20px;display:flex;gap:14px}
.qn{flex:none;width:32px;height:32px;border-radius:999px;background:#17202B;color:#FFF;font-weight:700;display:flex;align-items:center;justify-content:center}
.qb{display:flex;flex-direction:column;gap:6px;min-width:0}.q{font-size:18px;font-weight:700}.why{color:#4A5563;font-size:15px}
.tech{font-size:13px;color:#5B6573}.code{font-family:ui-monospace,Menlo,Consolas,monospace;background:#FFF7ED;color:#9A3F07;padding:1px 6px;border-radius:4px}
.next{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:16px}.next div{border-radius:16px;padding:24px;display:flex;flex-direction:column;gap:10px}
.dark{background:#17202B;color:#FFF}.dark small{color:#B9C6FF}.light{background:#FFF;border:1px solid #E2E6EB}.light small{color:#4A5563}
.next small{font-weight:700;font-size:14px;text-transform:uppercase}.next b{font-size:20px}.reply{align-self:flex-start;background:#FFF;color:#17202B;border:1px solid #17202B;border-radius:10px;padding:10px 14px;font-weight:700}
details{background:#FFF;border:1px solid #E2E6EB;border-radius:16px;padding:20px 28px}summary{cursor:pointer;font-weight:700;font-size:18px;min-height:44px;display:flex;align-items:center}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}th,td{text-align:left;padding:8px 10px;border-top:1px solid #E2E6EB;vertical-align:top}.scroll{overflow-x:auto}
.stand{display:flex;flex-direction:column;gap:10px;font-size:15px}.stand div{display:flex;justify-content:space-between;gap:8px}.ok{color:#115E39;font-weight:700}.wait{color:#9A3F07;font-weight:700}.no{color:#4A5563;font-weight:600}
.small{font-size:13px;color:#5B6573}dl{margin:0;font-size:14px}dt{font-weight:700}dt:not(:first-child){margin-top:12px}dd{margin:0;color:#4A5563}
.footer{font-size:13px;color:#4A5563;white-space:pre-line}
.v{display:none}
@media (max-width:720px){h1{font-size:30px}.arch{flex-direction:column}.area h4{min-height:0}.link{width:auto;flex-direction:row;gap:24px;padding:8px 0}.h{display:none}.v{display:inline}}
"""


def architecture_html(arch) -> str:
    """The 2-3 area diagram with numbered arrows and legend; shared with render_build_guide.py."""
    e = esc
    out = []
    w = out.append
    areas, flow = arch["areas"], arch.get("flow", [])
    w('<section class="card"><div><h2>Architecture: which systems talk to each other</h2>'
      '<p class="sub">The numbers show the order things happen. Dashed boxes are supporting services.</p></div>'
      '<div class="arch">')
    for i, a in enumerate(areas):
        if i:
            fwd = [n for n, f in enumerate(flow, 1) if f["from"] == i - 1 and f["to"] == i]
            back = [n for n, f in enumerate(flow, 1) if f["from"] == i and f["to"] == i - 1]
            w('<div class="link" aria-hidden="true">')
            if fwd:
                w('<div>' + "".join(f'<span class="n">{n}</span>' for n in fwd) + ' <span class="h">→</span><span class="v">↓</span></div>')
            if back:
                w('<div><span class="h">←</span><span class="v">↑</span> ' + "".join(f'<span class="n">{n}</span>' for n in back) + '</div>')
            w('</div>')
        w(f'<div class="area area{i}"><h4>{e(a["name"])}</h4>'
          f'<div class="sys core"><b>{e(a["main"]["name"])}</b>{e(a["main"].get("text", ""))}</div>')
        for s in a.get("support", []):
            w(f'<div class="sys support"><b>{e(s["name"])}</b>{e(s.get("text", ""))}</div>')
        w('</div>')
    w('</div><div class="legend">')
    for n, f in enumerate(flow, 1):
        w(f'<div><span class="n">{n}</span><span>{e(f["text"])}</span></div>')
    w('</div>')
    if arch.get("note"):
        w(f'<div class="small">{e(arch["note"])}</div>')
    w('</section>\n')
    return "".join(out)


def check_architecture(arch, errors) -> None:
    """Rule checks for the architecture block; appends messages to errors."""
    areas = arch.get("areas") if isinstance(arch, dict) else None
    if not (isinstance(areas, list) and 2 <= len(areas) <= 3):
        errors.append("architecture.areas: 2-3 areas")
        return
    for i, a in enumerate(areas):
        if not (isinstance(a, dict) and a.get("name") and isinstance(a.get("main"), dict) and a["main"].get("name")):
            errors.append(f"area {i}: needs 'name' and 'main': {{'name', 'text'}}")
        elif len(a.get("support", [])) > 2:
            errors.append(f"area {i}: at most 2 support boxes")
    flow = arch.get("flow", [])
    if not (isinstance(flow, list) and 1 <= len(flow) <= 6):
        errors.append("architecture.flow: 1-6 numbered steps")
        return
    for i, f in enumerate(flow, 1):
        ok = isinstance(f, dict) and isinstance(f.get("from"), int) and isinstance(f.get("to"), int)
        if not (ok and f.get("text")):
            errors.append(f"flow {i}: needs integer 'from', 'to' and 'text'")
        elif not (0 <= f["from"] < len(areas) and 0 <= f["to"] < len(areas)):
            errors.append(f"flow {i}: area index out of range")
        elif abs(f["from"] - f["to"]) != 1:
            errors.append(f"flow {i}: arrows only between neighbouring areas")


def render(doc) -> str:
    e = esc
    out = []
    w = out.append
    w('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
      '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
      f'<title>Quick Design — {e(doc["title"])}</title>\n'
      f'<meta name="generator" content="FlowPilot render_quick_design.py {VERSION}">\n'
      f'<style>{CSS}</style>\n</head>\n<body>\n')
    w('<div class="top"><div class="bar"><div class="brand">FlowPilot <span>/ Quick Design</span></div>'
      '<div class="draft">Draft idea · nothing has been built yet</div></div></div>\n<main class="wrap">\n')
    w('<div class="steps-bar" aria-label="Progress"><span class="done">✓ 1 · We understood your idea</span>'
      '<span class="now">2 · We need a few answers</span><span>3 · We build your starter pack</span>'
      '<span>4 · A person reviews it</span></div>\n')
    w(f'<h1>{e(doc["title"])}</h1>\n<p class="lead">{e(doc["summary"])}</p>\n')
    w('<div class="cols">\n<div class="main">\n')

    # What you asked for, and what you'll get
    w('<section class="card"><div><h2>What you asked for, and what you’ll get</h2>'
      '<p class="sub">Check that we understood you. If something is wrong, say so in your answers.</p></div>'
      '<div class="grid"><div class="box"><h3>Requirements</h3><ol class="reqs">')
    for i, r in enumerate(doc["requirements"], 1):
        label, cls = STATUS[r["status"]]
        note = f'<div class="note">{e(r["note"])}</div>' if r.get("note") else ""
        w(f'<li><span><strong>{i}.</strong> {e(r["text"])}{note}</span><span class="tag {cls}">{label}</span></li>')
    w('</ol></div><div class="box good"><h3>The outcome: how we’ll know it works</h3>'
      '<div class="note">Each check will be tested before real use.</div><ul class="checks">')
    for o in doc["outcomes"]:
        w(f'<li>{e(o)}</li>')
    w('</ul>')
    if doc.get("example"):
        w(f'<div class="example"><strong>Example (sample values):</strong> {e(doc["example"])}</div>')
    w('</div></div></section>\n')

    # How it will work
    w('<section class="card"><div><h2>How it will work</h2></div><div class="flow">')
    steps = doc["steps"]
    for i, s in enumerate(steps, 1):
        last = " last" if i == len(steps) else ""
        w(f'<div class="step{last}"><small>STEP {i}</small><b>{e(s["title"])}</b><span>{e(s["text"])}</span></div>')
    w('</div>')
    if doc.get("suggestion"):
        w(f'<div class="tip"><strong>Our suggestion:</strong> {e(doc["suggestion"])}</div>')
    w('</section>\n')

    # Architecture
    w(architecture_html(doc["architecture"]))

    # Key rule
    rule = doc.get("key_rule")
    if rule:
        w(f'<section class="card"><div><h2>{e(rule.get("title", "The key rule"))}</h2></div><div class="rule">')
        for it in rule.get("items", []):
            w(f'<div><b>{e(it["label"])}</b><span>{e(it["text"])}</span></div>')
        w('</div>')
        if rule.get("note"):
            w(f'<div class="tip">{e(rule["note"])}</div>')
        w('</section>\n')

    # Protections
    if doc.get("protections"):
        w('<section class="card"><div><h2>Mistakes it protects you from</h2></div><div class="protect">')
        for p in doc["protections"]:
            w(f'<div><strong>{e(p["title"])}</strong><span>{e(p["text"])}</span></div>')
        w('</div></section>\n')

    # Questions
    qs = doc["questions"]
    w(f'<section class="card" id="questions"><div><h2>Questions we need answered before we build</h2>'
      '<p class="sub">Answer in your own words in the chat. “I don’t know” is a fine answer; we’ll mark it as a gap. '
      'This page can’t send anything.</p></div><ol class="qs">')
    for i, q in enumerate(qs, 1):
        w(f'<li><span class="qn">{i}</span><div class="qb"><div class="q">{e(q["title"])}</div>'
          f'<div class="why"><strong>Why we ask:</strong> {e(q["why"])}</div>'
          f'<div class="tech">For your tech team: <span class="mono">{e(q["tech"])}</span></div></div></li>')
    w('</ol></section>\n')

    # Next step
    w('<section class="next"><div class="dark"><small>I have the details</small><b>Answer the questions and get the real plan</b>'
      '<span>You’ll get the workflow, tests and a step-by-step setup guide.</span>'
      '<span class="reply">Reply in chat, e.g. <span class="mono">1: … 2: …</span></span></div>'
      '<div class="light"><small>I don’t have them yet</small><b>Make a practice version with sample data</b>'
      '<span>Same pack, but anything unknown is marked <span class="code">TODO</span>. Safe to explore, not for real use.</span>'
      '<span class="reply">Reply in chat: <span class="mono">make a practice version</span></span></div></section>\n')

    # Technical details
    tech = doc.get("technical") or {}
    if tech:
        w('<details open><summary>Technical details for engineers</summary><div class="card" style="border:0;padding:16px 0 0">')
        if tech.get("requirements"):
            w('<div class="scroll"><table><thead><tr><th>ID</th><th>Requirement</th><th>Still unknown</th></tr></thead><tbody>')
            for r in tech["requirements"]:
                w(f'<tr><td class="mono">{e(r["id"])}</td><td>{e(r["text"])}</td><td>{e(r.get("unknown", ""))}</td></tr>')
            w('</tbody></table></div>')
        if tech.get("steps"):
            w('<div><h3>Workflow steps</h3><ol>' + "".join(f'<li>{e(s)}</li>' for s in tech["steps"]) + '</ol></div>')
        if tech.get("notes"):
            w('<ul>' + "".join(f'<li>{e(s)}</li>' for s in tech["notes"]) + '</ul>')
        w('</div></details>\n')
    w('</div>\n<aside class="side">\n')

    # Where things stand + glossary
    w('<div class="card"><h3>Where things stand</h3><div class="stand">'
      '<div><span>Idea understood</span><span class="ok">Done</span></div>'
      f'<div><span>Your answers</span><span class="wait">0 of {len(qs)}</span></div>'
      '<div><span>Automatically checked</span><span class="no">Not yet</span></div>'
      '<div><span>Reviewed by a person</span><span class="no">Not yet</span></div>'
      '<div><span>Deployed</span><span class="no">Never by FlowPilot</span></div></div>'
      '<div class="small">FlowPilot only designs. It never connects to your real systems or deploys anything.</div></div>\n')
    if doc.get("glossary"):
        w('<div class="card"><h3>Words you’ll see</h3><dl>')
        for g in doc["glossary"]:
            w(f'<dt>{e(g["term"])}</dt><dd>{e(g["meaning"])}</dd>')
        w('</dl></div>\n')
    w('</aside>\n</div>\n')
    w('<div class="footer">Validation: not executed (Quick Design mode; no blueprint produced)\n'
      'Deployment: not performed\nHuman review: pending</div>\n</main>\n</body>\n</html>\n')
    return "".join(out)


def main(argv) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[3], file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read {argv[1]}: {exc}", file=sys.stderr)
        return 2
    errors = check(doc)
    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        print("No page written. Fix the JSON and run again.", file=sys.stderr)
        return 1
    Path(argv[2]).write_text(render(doc), encoding="utf-8")
    print(f"OK: wrote {argv[2]} ({len(doc['questions'])} questions). This page is a draft; nothing was validated or deployed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
