# Changelog

## Unreleased: beginner-friendly Quick Design
The default Quick Design reply is now written for readers who are new to integration work.
- New `references/quick-design-template.md` sets the section order:
  1. Plain status line.
  2. Requirements tagged Clear / Needs detail / Our guess.
  3. Outcome checks with one worked example.
  4. Five-step flow.
  5. Architecture grouped by trust area, with a numbered legend.
  6. Protections.
  7. At most five questions, each with "Why we ask", a "Not sure" choice and a "For your tech team" line.
  8. Two next-step choices.
  9. Optional technical details.
  10. "Where things stand".
  11. Glossary.
- New `assets/quick-design-page.html`: a self-contained HTML version (no external scripts, fonts or images), filled with the Dataverse → SAP worked example.
- New `examples/quick-design-dataverse-sap.md`: the same worked example as a markdown reply.
- `SKILL.md`, `references/outputs.md` and `references/workflow.md` point Quick Design at the template.
- "make a practice version" is accepted as the same request as "generate a synthetic starter".
- How users answer:
  - Clients with a multiple-choice question tool (AskUserQuestion in Claude Code, question cards in Claude.ai) get the questions as clickable cards.
  - Otherwise choices are lettered (2–4 per question, "Not sure" last) and the reply ends with an answer-code line, e.g. `1A 2D 3B 4A 5C`.
  - The HTML page no longer shows buttons that do nothing; it tells the user to reply in chat.
- Unchanged: the ≤5-question limit, the provisional status, no blueprint by default, the Full Build Pack contract, the schema and the validator.
- `tests/test_quick_design_layout.py` checks the template, the example and the HTML page.

## 0.4.1 — 2026-11-02
Fixes from the independent audit of the v0.4 review candidate. Rebased on `flowpilot-v0.3` (includes v0.3.1).

### P0 — Service Bus retry design
- **Fixed a design that could silently lose orders.** v0.4 advised completing a failed message and scheduling a re-send with the same `MessageId`. Duplicate detection also applies to scheduled messages, so the re-send could be dropped inside the window after the original was completed; a crash between the two steps also lost the order.
- New identity rule: only the first publish uses `MessageId = order ID`; retries, DLQ replays and sweeps get their own deterministic IDs; idempotency keys on the `OrderId` property.
- Retries are scheduled **before** the original is completed (or both in one Service Bus transaction); circuit breaker pauses consumption during outages; mandatory reconciliation sweeper backstop.
- Example blueprint: new sweeper component (CMP-009), ADR-006 rewritten, six new failure tests (TST-013 to TST-018).
- `tests/test_retry_model.py`: executable model of documented Service Bus semantics proving the recommended design loses no orders under crashes, and that the rejected designs do (a model, not an Azure test).
- Guard test prevents the flawed advice from returning.

### P1
- Renderer validates first and **fails closed** (exit 1, no file) on invalid or unvalidated blueprints; `--preview` renders with a NOT VALIDATED banner and hides approval claims. Approvals are always shown as claims to verify, never as a trusted status.
- Renderer adds a traceability matrix and highlights confirmed requirements without tests.
- Validator `--evidence-dir`: passed/failed tests must match the SHA-256 of a real artifact; without it, evidence is reported as NOT VERIFIED. Approvals are reported as claims to confirm in the review system.
- Secret detection: credential-only names (api_key, client_secret, AccountKey, sig, …) no longer require a digit; placeholders are allowed; GitHub and Slack tokens added. CI adds a gitleaks secret scan.
- Validator warns on exactly-once / guaranteed-delivery wording.

### Carried over from v0.3.1
- All 31 negative cases from the v0.3.1 test suite are kept (`tests/test_v031_regression.py`).
- AI-reviewer check now uses word boundaries: v0.3.1's substring match rejected real names such as "Abbott" or "Modelski".
- Single source for schema and validator inside the skill folder; root `schemas/` and the duplicate `tools/` validator removed (wrappers remain).


## 0.4.0 — 2026-11-01
Fixes from the independent evaluation of v0.2 (repo) and v0.3 (Claude.ai package).

### Packaging
- Skill folder is self-contained: schema, example, validator and renderer moved into `assets/` and `scripts/` so the Claude.ai ZIP works. `tools/` keeps thin wrappers.
- `tools/package_skill.py` builds `dist/flowpilot-architect.zip`; a test checks its contents.
- One version (0.4.0) across SKILL.md, schema, validator, renderer, README and docs, enforced by a test.

### Schema 0.4.0
- New `provisional` status and `conflicting` requirement status; components and tests may be empty when provisional.
- Strict per-section ID prefixes and `additionalProperties: false` on every object.
- Conflicts have `status`, `explanation`, `options`, `resolution` (required when resolved) and at least two distinct requirements.
- Tasks gain `dependsOn`, `componentIds`, `prerequisites`, `verification`, `rollback`; tests gain `type`, `expectedResult`, `artifactHash` (SHA-256); risks gain `severity`, `owner`, `mitigation`; new `operations` section.
- Typed `reviewEvidence` with RFC 3339 `reviewedAt` and an `evidenceRef`.

### Validator
- Enforces `date-time` with a built-in checker (no optional packages needed).
- Resolves component and task references, rejects self-dependencies and dependency cycles.
- Approval blocked by blocking questions, open conflicts, and unknown/conflicting requirements; resolved conflicts no longer block.
- Rejects AI/tool reviewer names (e.g. "Claude Opus", "FlowPilot AI", "automated reviewer").
- `passed`/`failed` tests need evidence, time, environment and SHA-256; `not_run` tests must not carry evidence.
- Broader secret detection (API keys, APIM subscription keys, bearer tokens, JWTs, client secrets, SAS signatures).
- Clean errors instead of tracebacks; exit codes 0/1/2/3; warnings for weak criteria, orphan components and unowned high risks.

### Guidance
- Retry pacing for Service Bus workers (circuit breaker / scheduled re-send; DLQ only for deterministic failures).
- Blob SFTP: hierarchical namespace can be enabled on existing accounts (one-way upgrade) — corrected during the v0.4 re-test.
- Logic Apps vs Functions criteria, Event Grid delivery semantics, duplicate-detection window, APIM tier networking, Blob SFTP, audit and sensitive-data guidance, W3C tracing.
- SKILL.md: absolute validator path, never request credentials, honest provisional status, injection handling.

### Renderer
- Shows conflicts, acceptance criteria, evidence, review record, operations and test counts; footer reflects actual review state.

### Tests
- 50+ regression cases from the evaluation, renderer escaping, packaging and version-consistency tests; GitHub Actions on Python 3.10–3.13.

## 0.3.1
- Rejected AI reviewers and API keys; aligned provisional negative cases (branch `flowpilot-v0.3.1`).

## 0.3.0 — proposed, not production certified
- Bundled schema, validator and golden example inside the skill folder; provisional state; richer ADR/risk/test/operations fields; conflict history; CI; responsive HTML report.

## 0.2.0
Initial GitHub pilot.
