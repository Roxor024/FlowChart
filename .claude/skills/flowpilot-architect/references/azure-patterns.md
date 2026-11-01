# Azure integration architecture guidance

## Reliable API → ERP
APIM authenticates and routes; intake persists an idempotency record and outbox atomically before acknowledgment; relay publishes to Service Bus; worker handles business idempotency, backoff, DLQ, bounded concurrency and reconciliation of uncertain ERP outcomes. Never replace a later order state with an earlier one. Do not promise exactly-once business delivery.

## Low-latency synchronous API
Budget client→APIM→worker/backend latency, distinguish p95/p99 from averages, evaluate caching staleness and source-of-truth limitations, timeouts, limited retries and downstream availability. Do not guarantee a response from an unavailable backend.

## Fan-out
Event Grid supports events and push delivery; Service Bus topics/subscriptions offer brokered message consumption with durable subscriptions. Compare ordering, delivery guarantees, filtering, replay, failure isolation and consumer ownership.

## File / SFTP
Consider Azure Blob Storage SFTP (hierarchical namespace required, feature-specific costs), upload completion markers, checksums, schema validation, duplicate detection, quarantine, acknowledgments and reprocessing.

## Security and hybrid
Use identity and least privilege, APIM policy validation, Key Vault, private connectivity where required, protected logs and retention. Confirm SAP/ERP connectivity, authorization, data residency and on-premises boundaries.

## Cost / tiers / resilience
Service Bus private endpoints and geo-replication require Premium. Distinguish Service Bus geo-disaster-recovery (metadata) from geo-replication (data/state). Validate APIM tier-specific private network capabilities against current Microsoft documentation. Include environment, CI/CD, structured tracing and operational ownership.

## Test guidance
For each confirmed requirement, create a test with an expected outcome. Include outages, duplicates, partial failures, loss of acknowledgment, poison message recovery, and idempotent replay. Mark all tests not_run until independently executed.
