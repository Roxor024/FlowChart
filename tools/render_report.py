#!/usr/bin/env python3
"""Create a readable HTML design review report without external services."""
import html,json,sys
from pathlib import Path
def h(x):return html.escape(str(x))
def render(doc):
    css="body{margin:0;background:#f4f7fb;color:#18283b;font:16px/1.65 system-ui,sans-serif}main{max-width:940px;margin:auto;padding:40px 24px}header,section{background:white;padding:30px;border:1px solid #e3e9f0;border-radius:16px;margin-bottom:18px}h1{font-size:34px;line-height:1.2}h2{font-size:22px;margin-top:0}li{padding:6px 0}.meta{color:#5a697b;font-size:14px}strong{font-weight:650}@media print{body{background:#fff}header,section{break-inside:avoid}}"
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>FlowPilot Review</title><style>'+css+'</style><main>']
    parts.append('<header><p class="meta">FLOWPILOT · INTEGRATION ENGINEERING REPORT · 0.2</p><h1>'+h(doc.get("project","Untitled integration"))+'</h1><p class="meta">Status: '+h(doc.get("status","draft"))+' · Human review: '+h(doc.get("reviewStatus","unreviewed"))+'</p><p>Proposed engineering blueprint. No production deployment is implied.</p></header>')
    for title,key in [("Requirements","requirements"),("Architecture components","components"),("Architecture decisions","decisions"),("Implementation steps","implementationTasks"),("Test cases","testCases"),("Risks","risks"),("Questions to resolve","openQuestions")]:
        parts.append('<section><h2>'+title+'</h2><ol>')
        for item in doc.get(key,[]):
            parts.append('<li><strong>'+h(item.get("id",""))+' — '+h(item.get("title",""))+'</strong>'+(('<div class="meta">Status: '+h(item["status"])+'</div>') if "status" in item else "")+'</li>')
        parts.append('</ol></section>')
    parts.append('<section><h2>Verification</h2><p>Human review: pending unless evidenced. Test results must come from actual executions. Deployment: not performed.</p></section></main></html>')
    return "\n".join(parts)
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: python tools/render_report.py blueprint.json report.html")
    doc=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(render(doc),encoding="utf-8");print(out)
