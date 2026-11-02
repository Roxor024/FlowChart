# Implementation playbook — every task, for first-time users

## Mandatory IMP-### task panel

**Goal:** one sentence explaining what the task accomplishes.
**Why:** plain-language purpose and how it fits the architecture.
**Before you begin:** specific prerequisites, Azure role/permission, subscription, dependent tasks, budget approvals and unresolved blockers.
**Open:** verified portal navigation or documentation link; otherwise explicitly label instructions illustrative.
**Do:** one numbered action per line. Give relevant field names and SAMPLE values, exact configuration choices, and a short reason. Do not request or print production secrets.
**Check:** safe synthetic input, exact expected output or observable portal/log signal, and what proves the task completed. Execution state NOT RUN by default.
**If it fails:** at least one likely error, safe diagnostic action and resolution.
**Undo safely:** describe rollback; do not advise deleting persistent data or production resources without explicit approval.
**Tick when finished:** unticked human checkbox.
**Advanced references:** related requirement/component/test IDs in a small footer, not the headline.

## Example: receiving a payment webhook (illustrative, not deployment instructions)

1. Obtain the provider's *official* signing specification, retry behavior and safe test payload. If unknown, STOP: the signature algorithm must not be invented.
2. Obtain an approved Azure subscription, resource group, region and least-privilege role; confirm possible service charges.
3. Plan ingress through a verified HTTPS endpoint and a Function validating the exact raw request body before accepting events. Never log or reveal the signing secret.
4. Store each provider event ID once in a durable inbox and publish outbox work transactionally; acknowledge only after durable commit using the provider's specified success response.
5. Send a valid synthetic signed event: expect one durable inbox record. Send a duplicate: expect no second business effect. Send a tampered event: expect rejection and no durable record.
6. Simulate a ledger outage only in an approved disposable test environment; check retry and reconciliation without silently losing events.

These are conceptual stages. The final guide must expand each stage into current, checked navigation, sample code, configuration fields, test instructions and a rollback appropriate to the named provider.
