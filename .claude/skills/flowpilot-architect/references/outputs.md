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
