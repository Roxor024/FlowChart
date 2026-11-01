#!/usr/bin/env python3
"""Human-readable static report: all sections from one blueprint, escaped HTML."""
import html,json,sys
from pathlib import Path
def esc(v):return html.escape(str(v))
def render(d):
 css="""*{box-sizing:border-box}body{background:#f5f7fb;color:#19283a;font:16px/1.65 system-ui,-apple-system,sans-serif;margin:0}main{max-width:1020px;margin:0 auto;padding:44px 22px}header,section{background:#fff;border:1px solid #e2e8f0;border-radius:18px;padding:30px;margin-bottom:18px}h1{font-size:34px;line-height:1.2;margin:0 0 14px}h2{font-size:23px;margin:0 0 12px}h3{font-size:17px;margin:14px 0 4px}p{margin:6px 0 12px}small,.meta{color:#60718a}.tag{display:inline-block;background:#eaf0f8;padding:3px 12px;border-radius:99px}li{margin:10px 0;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid #e6eaf0;padding:9px;vertical-align:top}th{font-size:13px;color:#52657b}nav a{margin-right:12px;color:#235ca6;text-decoration:none}nav{margin:12px 0}.highlight{background:#f1f5fa;padding:15px;border-radius:10px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}@media(max-width:700px){.grid{grid-template-columns:1fr}header,section{padding:20px}}@media print{body{background:#fff}header,section{break-inside:avoid;border-color:#ddd}nav{display:none}}"""
 out=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>FlowPilot Engineering Report</title><style>'+css+'</style><main>']
 out.append('<header><small>FLOWPILOT · ENGINEERING DESIGN REVIEW · v0.3</small><h1>'+esc(d["project"])+'</h1><span class="tag">'+esc(d["status"])+'</span> <span class="tag">Review: '+esc(d["reviewStatus"])+'</span><p>'+esc(d.get("summary","Proposed integration; requirements and decisions require review."))+'</p><nav>'+''.join('<a href="#'+key+'">'+esc(label)+'</a>' for key,label in [("requirements","Requirements"),("components","Architecture"),("decisions","Decisions"),("implementationTasks","Build"),("testCases","Tests"),("risks","Risks"),("operations","Operate")])+'</nav></header>')
 out.append('<section><h2>At a glance</h2><div class="grid">'+''.join('<div class="highlight"><strong>'+str(len(d.get(k,[])))+'</strong><p>'+esc(label)+'</p></div>' for k,label in [("requirements","Requirements"),("testCases","Test cases"),("risks","Risks")])+'</div><p><strong>Required decisions:</strong> '+str(sum(q.get("blocking",False) for q in d["openQuestions"]))+' blocking questions; '+str(sum(c["status"]=="open" for c in d["conflicts"]))+' open conflicts.</p></section>')
 for key,title in [("requirements","Requirements & acceptance criteria"),("components","Architecture components"),("decisions","Architecture decisions & alternatives"),("implementationTasks","Implementation steps & verification"),("testCases","Test plan & evidence"),("risks","Risk register & mitigations"),("openQuestions","Questions to resolve"),("conflicts","Requirement conflicts")]:
  out.append('<section id="'+key+'"><h2>'+title+'</h2>')
  if not d[key]:out.append('<p class="meta">None documented. This may reflect a provisional design.</p>')
  for x in d[key]:
   out.append('<article><h3>'+esc(x["id"])+' · '+esc(x["title"])+'</h3>')
   labels={"acceptanceCriteria":"Acceptance","azureService":"Azure service","sku":"SKU","responsibility":"Responsibility","rationale":"Rationale","alternative":"Alternative","tradeoff":"Trade-off","verification":"Verification","rollback":"Rollback","expectedResult":"Expected result","status":"Status","severity":"Severity","owner":"Owner","mitigation":"Mitigation","evidence":"Evidence","resolution":"Resolution"}
   for k,label in labels.items():
    if x.get(k):out.append('<p><strong>'+label+':</strong> '+esc(x[k])+'</p>')
   if x.get("requirementIds"):out.append('<small>Traceability: '+esc(", ".join(x["requirementIds"]))+'</small>')
   out.append('</article>')
  out.append('</section>')
 out.append('<section id="operations"><h2>Operations & maintenance</h2>')
 for key in ("monitoring","alerts","recovery","owners"):
  out.append('<h3>'+esc(key.title())+'</h3><ul>'+''.join('<li>'+esc(v)+'</li>' for v in d.get("operations",{}).get(key,[]))+'</ul>')
 out.append('</section><section><h2>Approval & validation</h2><p>Deployment: not performed. Machine validation must be run separately. Human review: '+esc(d["reviewStatus"])+'. Tests shown as passed require evidence reviewed by an authorized human.</p></section></main></html>')
 return "\n".join(out)
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("usage: python tools/render_report.py blueprint.json report.html")
 d=json.loads(Path(sys.argv[1]).read_text());p=Path(sys.argv[2]);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render(d),encoding="utf8");print(p)
