# Workflow and phase gates (v0.4)

## 1. Intake
Classify each statement as confirmed, assumed, unknown or conflicting, with its source. Cover: interfaces and protocols, volume and peaks, payload size, latency (p95/p99, not averages), acceptance vs completion semantics, ordering, idempotency at producer/consumer/target, retry tolerance, RTO/RPO, data classification and residency, identity, network boundaries, budget, environments and operational ownership.

Ask at most five of the highest-impact questions in a response. Record other open questions as `QUE-` items (mark `blocking: true` when the design cannot be finished without the answer). Do not invent critical constraints; mark guesses as `assumed`.

## 2. Conflict gate
Look for combinations that cannot all hold (example: synchronous success within 200 ms while the backend is down for an hour). For each:
- set the affected requirements to `conflicting`;
- add an open `CON-` item with `requirementIds` (at least two), `explanation` and `options`;
- keep the blueprint `provisional` until the user chooses an option;
- when resolved, set the conflict to `resolved` with a `resolution` explaining the decision. Keep resolved conflicts as history.

## 3. Status gate
- Too little information for a full design → `provisional`. Empty components/tests are acceptable; do not fabricate services to fill the schema.
- Full proposal → `draft`. Requires components, decisions, implementation tasks, tests and risks. Every confirmed requirement needs measurable acceptance criteria and at least one test.
- `approved` only with user-supplied external review evidence and no blocking questions, open conflicts, or unknown/conflicting requirements.

## 4. Design
Compare at least two practical patterns against the requirements. Record each choice as an ADR with rationale, alternative and trade-off. Note Azure tier constraints that change the design (networking, geo-replication, throughput units).

## 5. Build
Ordered tasks with prerequisites, `componentIds`, `dependsOn`, verification and rollback. Environments (dev/test/prod), infrastructure as code and a CI/CD approval gate before any apply.

## 6. Test
For each confirmed requirement at least one test with an expected result. Always include: happy path, dependency outage, duplicate submission and redelivery, lost acknowledgement, poison message, authentication failure, replay/recovery and load. All tests stay `not_run` until real evidence exists.

## 7. Operate
Metrics, alert thresholds, distributed tracing, DLQ triage and replay runbook, reconciliation, secret rotation, retention, owners (named roles, not "TBD").

## 8. Report and validate
Write the report from the blueprint, run the validator, and finish with the Validation / Deployment / Human review lines.
