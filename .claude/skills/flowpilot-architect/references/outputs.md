# Human-readable output contract (v0.4)

Produce an architect-friendly report, not a transcript. Build it from the blueprint so both state the same facts.

1. **Cover:** project, platform, skill and schema version, blueprint status (provisional/draft/approved), review status, validation status.
2. **Executive summary:** problem, proposed solution, why, confidence, and the three decisions or questions that need attention.
3. **Requirements:** confirmed, assumed, unknown, conflicting — each with ID and acceptance criteria. At most five questions asked now; the rest are recorded.
4. **Conflicts:** each open conflict with why it conflicts and the options.
5. **Architecture:** Mermaid diagram, component responsibility table with Azure service and tier assumptions, trust boundaries, one alternative with trade-offs.
6. **Decisions (ADRs):** rationale, rejected alternative, trade-off, status.
7. **Build plan:** numbered tasks with prerequisites, dependencies, exact verification and rollback.
8. **Tests:** case, type, expected result, execution status. Evidence only for real executions; never fake a pass.
9. **Risk register:** severity, evidence, mitigation, owner role.
10. **Operations:** metrics, alerts with thresholds, tracing, DLQ recovery and replay, maintenance, owners.
11. **Verification status:** validation result (or NOT EXECUTED and why), deployment not performed, human review state — visually separate from proposals.
12. **Appendix:** full blueprint JSON, references, starter artifacts (labelled unverified).

Style: short paragraphs, informative headings, narrow tables, print-friendly. When local scripts are available, `scripts/render_report.py <blueprint> <report.html>` produces an escaped HTML overview of the blueprint; it does not replace the written report or a verified diagram.
