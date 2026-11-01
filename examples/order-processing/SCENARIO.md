# Order processing reference scenario
20,000 orders per day via REST API; external ERP can be unavailable for 45 minutes. Accepted orders must not disappear, and duplicate business processing must be prevented. Azure preferred.
Unknowns include peak traffic, ordering, end-to-end latency, payload size, ERP API, authentication, client idempotency policy and operational owner.
Use `/flowpilot-architect` to generate a DRAFT architecture, implementation/test plan and blueprint. No deployment or claims of execution.