# Synthetic order-processing scenario (v0.4)

A REST API accepts approximately 20,000 orders/day (≈0.23/s on average; peak unknown) and sends them to an external ERP. The ERP may be unavailable for 45 minutes. Accepted orders cannot disappear, and duplicate business processing must be prevented. Azure is preferred. Some requirements are deliberately missing.

Expected behaviour:
- Ask at most five questions now, prioritising: peak rate, ERP idempotency/external-reference support, validation rules, data classification, caller authentication. Record the rest (ordering, latency target, payload size, RTO/RPO, owners) as `QUE-` items.
- Propose durable asynchronous acceptance as a conditional recommendation: 202 means accepted, not completed; offer a status endpoint.
- Explain producer idempotency (client key + unique constraint), the transactional outbox, consumer idempotency (order ID as ERP external reference, lookup on uncertain outcome) and why Service Bus duplicate detection is not exactly-once.
- Show retry pacing that survives a 45-minute outage without dead-lettering healthy orders, and never reuses the original `MessageId` for retries or replays (duplicate detection would silently drop them). Include the reconciliation sweeper backstop (see `azure-patterns.md` → Retry pacing).
- Include functional and failure tests: outage, duplicate submission, redelivery, lost acknowledgement, relay crash, poison message, auth failure, load, crash between retry scheduling and completion, settlement failure, retry under duplicate detection, DLQ replay, sweeper recovery. All `not_run`.
- Produce a human-readable report and a blueprint that validates; never deploy.

`assets/example-blueprint.json` is a worked example of this scenario.
