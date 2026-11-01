# Workflow and phase gates

## Intake
Classify each statement as confirmed, assumed, unknown or conflicting. Collect interfaces, volume/peaks, latency, acceptance semantics, retry tolerance, data classification, identity, network, ordering, idempotency, RTO/RPO, budget, operations ownership.
Ask at most five of the highest-impact questions in a response. Record other unanswered questions in the blueprint without dumping them at the user.

## Conflict gate
Look for impossible combinations (e.g. synchronous success within 200 ms despite a one-hour backend outage). Explain the conflict and propose options. Do not mark design approved with unresolved blocking questions/conflicts.

## Design
Compare two practical patterns with explicit requirements traceability and Azure service constraints. Record ADRs, dependencies and assumptions.

## Build / Test / Operate
Provide ordered tasks with prerequisites and verification. Tests include happy path, outage, duplicate delivery, poison messages, auth failures and recovery. Operations include alerts, redaction, runbooks and ownership.

## Approval
Draft and unreviewed by default. Require reviewer, date and evidence to mark approved. Report validation status separately from review and test execution.