# Azure integration pattern guide (review before production)

## Reliable API -> queue -> ERP
APIM -> secure intake Function -> Service Bus -> worker -> ERP. Persist before HTTP 202. Specify idempotency at producer, consumer and ERP boundary. Define retries, backoff, lock durations, DLQ triage, replay, reconciliation and status endpoint.

## Synchronous API
APIM -> Function or Logic App -> backend when the response needs immediate data. Budget end-to-end latency across every hop. Consider backend timeouts, circuit-breaking, limited retries, caching where permitted, and fallback semantics. Never promise availability independent of an unavailable source of truth.

## Event-driven fan-out
For discrete event delivery consider Event Grid; for independent durable consumer processing consider Service Bus topics/subscriptions. Evaluate delivery/replay, ordering, filtering, per-consumer isolation, security and subscriptions.

## File/SFTP batch
Stage in storage; detect completion before ingestion; validate schemas and filenames; reject duplicates; quarantine invalid files; handle partial uploads, acknowledgments and replay. Consider Azure Storage SFTP or partner-specific integration boundary.

## Sensitive data and hybrid ERP
Use least-privilege identity, Key Vault references, encrypted transport, redacted logs, retention and access review. Confirm hybrid connectivity, ERP protocols, availability and ownership.

All patterns are starting points, not pre-approved architectures. Verify current Microsoft documentation and target SKU restrictions.