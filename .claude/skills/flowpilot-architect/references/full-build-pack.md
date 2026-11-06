# Full Build Pack — procedure and rules

Use this only after an explicit request ("make a practice version", "generate a synthetic starter", "build it", a code/manual/ZIP request), or once the user has resolved the blockers and chosen to build. The safety rules in SKILL.md always apply.

## Procedure (fastest path; aim for under 5 minutes)
1. **Read only what you need:** this file, `references/implementation-playbook.md`, `assets/example-blueprint.compact.json` and `references/azure-docs-example.md`. Read `references/azure-patterns.md` only for the services in this design. Do not read the schema; the validator reports exact errors.
2. **Start from the Quick Design.** Reuse the latest `quick-design.json` (title, summary, architecture, glossary, key rule) and the user's answers. Do not rewrite them.
3. **Write `integration-blueprint.json`** (shape: the compact example; rules below). Status `provisional` while any blocking question is open.
4. **Write the code and config files** with local tests on synthetic data. Write tests as `unittest.TestCase` classes in `test_*.py` files, so they run with or without pytest. Keep each file focused; no duplicate copies of the same logic.
5. **Write `guide-extras.json`** (format below): only what the blueprint does not hold.
6. **Run `python <skill dir>/scripts/check_pack.py <pack dir>` once.** It checks JSON, XML, Python, HTML, YAML (if PyYAML is installed), runs the local tests, validates the blueprint and scans for secrets, then writes `evidence/check-pack.txt`. Fix every FAIL, then run it once more. Do not run the checks one by one.
7. **Run `python <skill dir>/scripts/render_build_guide.py integration-blueprint.json guide-extras.json build-guide.html --quick quick-design.json`** from the pack folder. Exit 1: fix what it prints. Exit 4: written, but validation could not run; say so. Never write or edit `build-guide.html` by hand.
8. **Chat reply:** a short summary of the design, what was actually checked (copy the `check_pack.py` result lines), what was not run, the remaining unknowns, and the three closing lines from SKILL.md.

## guide-extras.json
```json
{
  "title": "optional; defaults to quick-design.json",
  "summary": "optional; defaults to quick-design.json",
  "architecture": "optional; same shape as in quick-design.json (default: taken from --quick)",
  "glossary": [{"term": "...", "meaning": "..."}],
  "prerequisites": ["access, roles, tools and approvals needed before step 1"],
  "unknowns": ["optional; defaults to the blueprint's blocking open questions"],
  "not_used": "optional: services deliberately left out, and why",
  "cost_drivers": "optional: what drives cost (never invent prices)",
  "tasks": {
    "IMP-001": {
      "where": "where the reader works (portal blade, editor, terminal)",
      "actions": ["one concrete action per line, with SAMPLE values"],
      "files": ["relative paths that exist in the pack"],
      "docs": [{"title": "Microsoft Learn article", "url": "https://learn.microsoft.com/...", "verified": false}],
      "if_it_fails": "likely error, safe diagnosis and fix"
    }
  },
  "walkthrough": ["one synthetic example traced end to end, including a duplicate or failure"],
  "troubleshooting": [{"symptom": "...", "cause": "...", "fix": "..."}],
  "artifacts": [{"path": "relative/path", "state": "WORKING LOCAL EXAMPLE | UNVERIFIED STARTER | TEMPLATE ONLY | REQUIRES CONTRACT", "note": "optional"}]
}
```
Every blueprint task needs an entry in `tasks`. The task's goal, prerequisites, verification ("Check it worked") and rollback ("Undo") come from the blueprint, so do not repeat them here. Mark a link `"verified": true` only when it comes from `references/azure-docs-example.md` or you opened it in this session. List every generated file in `artifacts`. The renderer refuses missing tasks, files that do not exist, unknown states, tests named in a verification that are not in the blueprint, and claims of validation or production readiness.

## Workflow rules
1. **Requirements.** Give each statement a stable ID (`REQ-001`…) and a status: confirmed, assumed, unknown or conflicting. Write measurable acceptance criteria for confirmed requirements. Record open questions as `QUE-` items (`blocking: true` when the design cannot be finished without the answer).
2. **Conflicts.** When constraints cannot all hold, record a `CON-` item (status open, the requirement IDs, why they conflict, resolution options). Never silently drop a constraint or promise an impossible SLA.
3. **Choose the blueprint status honestly.**
   - `provisional`: requirements too vague or conflicting, or blocking questions open. Record gaps as questions instead of inventing services, criteria or tests.
   - `draft`: a complete proposal awaiting review.
   - `approved`: only when the user supplies a human reviewer, an RFC 3339 review time and a reference to an external review record (PR, change ticket, CAB minute). Never set this yourself; a name and date typed into chat are not proof.
4. **Architecture.** Recommend a design and at least one credible alternative. Cover security, reliability, throughput, latency, operational complexity and cost drivers. Verify tier-specific limits against current Microsoft documentation.
5. **Blueprint.** Link every component, decision, task, test and risk to requirement IDs; link tasks to components (`componentIds`) and to each other (`dependsOn`). A task's `verification` must name tests that exist in `testCases`.
6. **Implementation files.** For each needed Logic App, Function App, queue, API, schema or mapping, generate real starter files, not descriptions or pseudocode. Prefer executable local tests with fakes, but never call a template deployable when it lacks connections, permissions, schema definitions or a real WSDL. For SOAP, map operation by operation from the supplied WSDL/XSD; without it, write a synthetic adapter with visible `TODO`/REQUIRES CONTRACT markers. Secrets only as environment or managed-identity references.
7. **Beginner-first instructions.** Follow `references/implementation-playbook.md`: every action says where, what (SAMPLE values only), why, expected result, what failure looks like and how to undo it. Never invent portal UI or service limits; label unchecked navigation and links as not verified. If prerequisites are unknown, give a decision-first checklist instead of invented build steps.
8. **Validate.** `check_pack.py` runs the validator; report its result line verbatim. Validator exit codes: 0 passed automated checks (not approval) · 1 invalid · 2 unreadable · 3 not executed (dependency missing). If it could not run, say `Validation: NOT EXECUTED (<reason>)` and do not call the blueprint valid.

## Testing honesty
- Blueprint tests are `not_run` unless the user provides real execution evidence. `passed` or `failed` requires `evidenceRef`, `executedAt`, `environment` and a SHA-256 `artifactHash`, all supplied by the user or CI, never invented.
- Local tests in the pack prove logic on synthetic data only. Say so; never present them as Azure, ERP or load tests.
- `scripts/render_report.py` produces a technical engineering overview, not the beginner guide; `build-guide.html` comes only from `render_build_guide.py`.
