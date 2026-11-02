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

## Mandatory file-by-file build companion

For **every needed implementation file**, include a copyable file with its relative path, language/runtime version, required libraries, purpose, exactly where it belongs, and exact local test command. For Azure Function apps, include host.json, requirements.txt (Python) or appropriate dependencies, trigger entry points, configuration placeholders, exception handling and synthetic tests. For Logic Apps, distinguish a deployable workflow definition from a routing fragment and include required connection references. For Service Bus, supply each required queue's configuration manifest, TTL, DLQ strategy, security/identity and matching function trigger. For SOAP, parse WSDL/XSD only when actually supplied; otherwise synthetic example and explicit mapping gaps. For Dataverse, describe connector authentication, update fields, idempotency/loop guard and response retry or reconciliation; don't claim the update exists if it's only planned.

## Illustrations at each important action

Create an architecture diagram and visual placement references, with numbered callouts matching manual steps. Use SVG/HTML drawings for conceptual Azure Portal illustrations (clearly labeled NOT A SCREENSHOT). Show a distinct picture for creating a Service Bus namespace/queues, configuring a Logic App switch, and configuring a Function trigger; for an actual screenshot use a current authoritative UI capture rather than a fabricated portal image. Keep a text description for accessibility.

## Beginner completeness check

Before delivering, walk through the guide as if the reader has never opened Azure Portal or VS Code. Confirm every named resource has an explicit creation step, every code file has a path, every checkbox has a test, every configured queue is mapped to a Function trigger, and every unimplemented integration boundary is disclosed. Don't use phrases such as "configure as needed" or "set up authentication" without expanding the substeps or marking a blocking decision.
