# Synthetic order processing test

A REST API accepts approximately 20,000 orders/day and sends them to an ERP. The ERP may be unavailable for 45 minutes. Accepted orders cannot disappear, and duplicate business processing must be prevented.

Expected: ask about peak volume, API contract, order uniqueness, acceptance vs completion, ERP capabilities, RTO/RPO, auth, cost, network and operations. Propose a durable buffering design only as a conditional recommendation. Explain producer and consumer idempotency, ERP acknowledgement, dead-letter handling, timeouts, retries and recovery. Include functional and failure tests and a human-readable report. Never deploy.