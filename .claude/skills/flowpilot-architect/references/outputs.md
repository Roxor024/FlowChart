# FlowPilot v0.3 — report presentation and artifact contract

Present a readable executive-first report:
1. Executive overview: requirement, proposal, business impact, confidence, unresolved questions.
2. Requirements table with clear status and measurable acceptance criteria.
3. Architecture diagram (Mermaid) and component responsibilities, Azure service/SKU assumptions, trust boundaries.
4. Alternatives and architecture decisions with rationale and tradeoffs.
5. Ordered implementation playbook including prerequisites, verification and rollback.
6. Tests with expected results and actual execution state; evidence only when truly executed.
7. Prioritized risks with severity, mitigation and ownership.
8. Monitoring, alerts, runbooks, recovery and maintenance responsibilities.
9. Approval and machine validation state, prominently distinguished.
10. Blueprint JSON in a separate downloadable file or appendix, matching the schema exactly.

Use short sentences, legible headings, responsive tables and print-friendly styling. Do not overload the first page. The generated HTML is an overview from blueprint data, not a substitute for a verified architecture diagram. The default report generator escapes user-supplied content.
