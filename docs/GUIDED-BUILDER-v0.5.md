# Guided Builder v0.5 — human-facing report contract (preview)

The user's primary output is an implementation guide, not JSON and not an architecture audit. Keep the machine-readable blueprint in a separate advanced export; it provides validation, traceability and future automation.

## Required order

1. **What are we building?** Explain goal and business benefit in two simple sentences. Define specialist terms on first use. State unknowns honestly.
2. **At a glance.** Show the steps, prerequisites, expected services, necessary permissions and cost considerations without inventing prices.
3. **Visible architecture diagram.** Render source → ingress/security → persistence → queue → worker → destination, with arrows, labels, trust boundaries and error/retry paths. For HTML use accessible inline SVG or local image; no remote scripts or CDNs. Mermaid source may be exported but cannot substitute for a visibly rendered diagram. For provisional designs mark assumptions and avoid invented services.
4. **Prepare.** Give access/permissions checklist, dependencies, safe SAMPLE names and test payloads, budget approvals and missing business decisions.
5. **Build it step by step.** One detailed section for EVERY implementationTask in blueprint, plus setup dependencies. Follow references/implementation-playbook.md. Each step needs exact actions, check, troubleshooting and rollback.
6. **Test as you go.** Synthetic test input and expected output for each step, completion checklist, with execution state NOT RUN unless evidence exists.
7. **Walk through one example.** Trace synthetic message from source to destination, then duplicate/failure/recovery.
8. **Fix problems.** Symptom → likely cause → safe verification → correction → re-test.
9. **Finish and operate.** Monitoring, alerts, recovery, owner roles, open decisions and handover checklist. State that no Azure deployment or human approval occurred.
10. **Technical appendix (optional).** Blueprint JSON, schema validation, ADRs, traceability, risks, deeper architecture and starter artifacts.

## Presentation rules

- Keep the first screen beginner-friendly and visual; no raw JSON or long tables of IDs.
- Every task ID in the blueprint has a matching practical step. Every required component is accounted for.
- Explain where and how to configure something, with concrete but sanitized examples; do not invent portal labels.
- Don't present code as deployed or checks as passed unless executed; all tests start NOT RUN.
- Users can mark checklist items manually, but nothing is pre-checked.
- For vague requirements, give a decision-first guide rather than pretending there is a complete deployable plan.
- The existing scripts/render_report.py produces a TECHNICAL OVERVIEW, not this guided HTML experience. A new renderer must be built before claiming this is automatic.

# Implementation playbook — every task, for first-time users

## Mandatory IMP-### task panel

**Goal:** one sentence explaining what the task accomplishes.
**Why:** plain-language purpose and how it fits the architecture.
**Before you begin:** specific prerequisites, Azure role/permission, subscription, dependent tasks, budget approvals and unresolved blockers.
**Open:** verified portal navigation or documentation link; otherwise explicitly label instructions illustrative.
**Do:** one numbered action per line. Give relevant field names and SAMPLE values, exact configuration choices, and a short reason. Do not request or print production secrets.
**Check:** safe synthetic input, exact expected output or observable portal/log signal, and what proves the task completed. Execution state NOT RUN by default.
**If it fails:** at least one likely error, safe diagnostic action and resolution.
**Undo safely:** describe rollback; do not advise deleting persistent data or production resources without explicit approval.
**Tick when finished:** unticked human checkbox.
**Advanced references:** related requirement/component/test IDs in a small footer, not the headline.

## Example: receiving a payment webhook (illustrative, not deployment instructions)

1. Obtain the provider's *official* signing specification, retry behavior and safe test payload. If unknown, STOP: the signature algorithm must not be invented.
2. Obtain an approved Azure subscription, resource group, region and least-privilege role; confirm possible service charges.
3. Plan ingress through a verified HTTPS endpoint and a Function validating the exact raw request body before accepting events. Never log or reveal the signing secret.
4. Store each provider event ID once in a durable inbox and publish outbox work transactionally; acknowledge only after durable commit using the provider's specified success response.
5. Send a valid synthetic signed event: expect one durable inbox record. Send a duplicate: expect no second business effect. Send a tampered event: expect rejection and no durable record.
6. Simulate a ledger outage only in an approved disposable test environment; check retry and reconciliation without silently losing events.

These are conceptual stages. The final guide must expand each stage into current, checked navigation, sample code, configuration fields, test instructions and a rollback appropriate to the named provider.
