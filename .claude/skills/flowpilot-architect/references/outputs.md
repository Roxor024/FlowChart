# Human-readable output contract

Produce an architect-friendly report, not a raw AI transcript.

1. Cover: project, platform, version, draft status, review/validation status.
2. Executive summary: problem, proposed solution, why, 3 decisions needing attention.
3. Requirements: confirmed, assumptions, blocking unknowns (no more than five questions asked at once).
4. Architecture: clear Mermaid diagram, plain-language component responsibility table, one alternative with tradeoffs.
5. Decisions (ADRs): rationale, rejected alternative, acceptance conditions.
6. Build: numbered, checkable implementation tasks, prerequisites, exact verification and rollback guidance.
7. Testing: test case, expected result, evidence and execution status; never fake pass.
8. Risk register: severity, evidence, mitigation, owner/decision required.
9. Operations: metrics, alerts, tracing, DLQ recovery, maintenance and change process.
10. Appendix: full blueprint JSON, references and generated starter artifacts.

Keep paragraphs short, avoid horizontal wide tables, use informative headings, and present a readable HTML/Markdown report when the host allows. Clearly separate proposals from proven tests.