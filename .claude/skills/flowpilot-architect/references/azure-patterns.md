# Azure integration pattern guide (v0.4)

Patterns are starting points, not pre-approved architectures. Verify tier limits and feature availability against current Microsoft documentation before relying on them, and say when a detail is unverified.

## Choosing services
| Need | Prefer | Notes |
|---|---|---|
| Expose, secure and throttle APIs | API Management | `validate-jwt`, rate-limit/quota, request size limits, inject or forward a correlation ID. Networking differs by tier: classic Developer/Premium support VNet injection; Standard v2 has outbound VNet integration and inbound private endpoints; Premium v2 supports full VNet injection. |
| Custom logic, transactions, complex transforms | Azure Functions | Code-first, unit-testable. Good for idempotent intake and workers. |
| Connector-heavy orchestration, B2B, SAP/SaaS connectors, long-running workflows | Logic Apps (Standard for VNet, multiple workflows, local dev) | Prefer when a managed connector replaces custom client code. Often combined: Logic Apps orchestrates, Functions does the logic. |
| Commands / work items that must not be lost, competing consumers, ordering | Service Bus queue (topic + subscriptions for durable fan-out) | Pull-based, DLQ per entity, sessions for ordered processing per key, duplicate detection on Standard/Premium. |
| Reactive notifications to many handlers, Azure resource events | Event Grid | Push, at-least-once, **no ordering guarantee**. Default retry up to 24 h / 30 attempts. Configure a dead-letter storage container; events are dropped without one. |
| Secrets, certificates | Key Vault + managed identity | Prefer managed identity and Entra ID auth to secrets wherever the target supports it. |

## Reliable API → queue → ERP
APIM → intake Function → (order store + outbox, one transaction) → relay → Service Bus queue → worker → ERP.
- **Acceptance vs completion:** return 202 with an order ID only after the order and outbox rows commit. Offer a status endpoint or callback.
- **Producer idempotency:** client-supplied idempotency key with a unique constraint; a repeat returns the original result.
- **Consumer idempotency:** use the order ID as the ERP external reference; on a timeout with unknown outcome, look up before retrying. Never let an older state overwrite a newer one (version column).
- **Duplicate detection** drops repeat `MessageId`s only within its window (default 10 minutes, maximum 7 days). It does not cover consumer redelivery or ERP-side uncertainty, so it is an optimisation, never the guarantee.

### Retry pacing (common failure)
A Service Bus–triggered worker that throws or abandons on every ERP error gets the message back as soon as the lock is released. Each abandon or lock expiry increments the delivery count, and when it exceeds `maxDeliveryCount` (default 10) the message is dead-lettered. During a 45-minute outage this dead-letters healthy orders within minutes. Azure Functions retry policies do not apply to Service Bus triggers.

**Identity rule — read before designing any retry or replay.** Duplicate detection (Standard/Premium) silently drops any message whose `MessageId` was seen within the window (default 10 minutes, up to 7 days); the send still reports success. **Scheduled messages take part in duplicate detection.** Therefore:
- Keep the *business* identity (order ID) in an application property such as `OrderId`, and make the ERP call and all state transitions idempotent on that property.
- Give every retry or replay message its **own** `MessageId`, derived deterministically from the business ID and attempt, e.g. `{orderId}:retry:{attempt}` or `{orderId}:replay:{dlqSequenceNumber}`. Never reuse the original `MessageId` for a retry or a DLQ resubmission.
- Use `MessageId = orderId` only for the *first* publish (from the outbox), where dropping a duplicate is the goal.

Design instead (choose one primary strategy, always add the backstop):
1. **Classify errors:** transient (ERP unavailable, 429, 5xx, timeout) vs deterministic (validation, contract, 4xx business rejection).
2. **Strategy A — pause consumption (preferred when the whole ERP is down).** A circuit breaker opens after N consecutive transient failures; the worker stops receiving (e.g. `ServiceBusProcessor.StopProcessingAsync` in a self-hosted worker, or a Functions host that can be stopped by an operator runbook) and abandons nothing further. A health probe closes the breaker. Messages wait in the queue without consuming delivery attempts. In-flight messages are abandoned once, so budget a few delivery attempts for this.
3. **Strategy B — scheduled retry with a new identity (for per-message transient errors).** For each retry: schedule a new message with `MessageId = {orderId}:retry:{attempt}`, the same body and `OrderId`, `ScheduledEnqueueTime = now + backoff(attempt) + jitter`, **then** complete the original. Prefer doing both inside one Service Bus transaction (send + complete on the same entity, Standard/Premium; verify SDK support for scheduled sends in transactions). Without a transaction the order must be *schedule first, complete second*: a crash in between causes a duplicate retry (absorbed by idempotency), never a lost order. **Never complete before the retry is durably scheduled.** Cap attempts; after the cap, dead-letter with a reason.
4. **Backstop — reconciliation from the state store (mandatory).** The order database, not the broker, is the source of truth. A scheduled sweeper finds orders in a non-terminal state older than the outage budget plus margin and re-publishes them with `MessageId = {orderId}:sweep:{runId}`. This recovers from any messaging bug, settlement failure or lost retry.
5. Dead-letter only deterministic failures or retries beyond the outage budget; alert on every DLQ arrival. **DLQ resubmission** creates a new message with `MessageId = {orderId}:replay:{dlqSequenceNumber}`.
6. Size queue TTL and backlog alerts to the outage budget; bound concurrency after recovery to avoid a thundering herd.

**Tests to require:** worker crash between schedule and complete; settlement (complete) failure after a successful ERP call; retry sent while duplicate detection is enabled (must be delivered, not dropped); DLQ resubmission inside the duplicate-detection window; sweeper re-publishes a stuck order; breaker open for longer than the outage budget.

## Synchronous API
APIM → Function or Logic App → backend when the caller needs data immediately. Budget p95/p99 latency per hop; set timeouts shorter than the caller's; limited retries only if they fit the budget; circuit breaker with explicit fallback semantics; cache (APIM or Redis) only when staleness is acceptable and stated. Never promise success or latency when the source of truth is unavailable.

## Event-driven fan-out
Event Grid for lightweight notifications; Service Bus topics/subscriptions when each consumer needs durable, independent processing, replay from its own backlog and isolation from others' failures. Compare ordering, delivery guarantees, filtering, replay, per-consumer DLQ and ownership.

## File / SFTP batch
- Azure Blob Storage SFTP requires a hierarchical-namespace (Data Lake Storage Gen2) account and has an hourly charge while enabled. Hierarchical namespace can be set at creation or enabled later on an existing account, but the upgrade is one-way and some Blob features are unsupported with it — check the known-issues list first. Authentication uses local users (SSH key or password); check current docs for Entra ID support.
- Detect completion (marker file or rename convention) before ingestion; trigger on Event Grid `BlobCreated` or a schedule.
- Validate filename, checksum, schema; reject duplicates by file hash; quarantine invalid files; produce an acknowledgement file or message; support reprocessing.
- Alternative: Logic Apps SFTP connector against a partner-hosted server.

## Security, audit and sensitive data
- Managed identities with least-privilege RBAC per component; no shared keys where Entra ID auth exists.
- Private endpoints where data classification requires it. Service Bus private endpoints, VNet integration and geo-replication need the **Premium** tier.
- Audit trail: APIM and Function logs to Log Analytics with retention matched to policy; record who accessed which record and when; restrict log access; redact personal data from traces and DLQ inspection tools.
- Key Vault with RBAC, soft delete and purge protection; rotation schedule; alert on access anomalies.
- Confirm data residency, hybrid connectivity (ExpressRoute/VPN/on-premises gateway) and ERP/SAP authorisation model.

## Resilience
Service Bus Geo-Replication (Premium) replicates data and metadata and is the recommended DR option; Geo-Disaster Recovery replicates metadata only. Availability zones protect within a region. State RTO/RPO before choosing.

## Observability and delivery
W3C `traceparent` propagated through APIM, Functions and message application properties; structured logs keyed by order/correlation ID; dashboards for backlog age, DLQ, outbox lag and dependency health. Separate dev/test/prod, infrastructure as code, a pipeline with a human approval gate before apply, and rollback by redeploying the previous release.
