> **Draft idea · nothing has been built yet**
> ✓ 1 We understood your idea → **2 We need a few answers** → 3 We build your starter pack → 4 A person reviews it

# Send new consignment orders from Dataverse to SAP automatically

When someone creates a consignment order, it is created in SAP for them. The product's translations are copied back, and the order is marked **Synced**. No copy-pasting between systems.

## What you asked for, and what you'll get

**Requirements.** Check that we understood you.

| # | Requirement | Status |
|---|---|---|
| 1 | Start when someone creates a consignment order from a work order in Dataverse | Clear |
| 2 | Check that all needed information is there before calling SAP | Needs detail: which fields are required? |
| 3 | Convert the order into SAP's format | Needs detail: SAP's exact format |
| 4 | Create the consignment in SAP | Clear |
| 5 | Find which languages the product has in SAP | Clear |
| 6 | Copy translations only for languages Dataverse also has; skip the rest | Clear |
| 7 | Mark the order "Synced with SAP" | Clear |
| 8 | A few orders a day, one at a time | Our guess: tell us if this is wrong |

**The outcome: how we'll know it works.** Each check will be tested before real use.
- ✓ An order with missing information **never reaches SAP**. You see the reason on the order.
- ✓ "Synced" appears **only** when SAP has confirmed the order and every translation was saved.
- ✓ Only languages in **both** systems get a translation. Skipped languages are listed with a reason.
- ✓ Running it twice **never** creates a second SAP order or duplicate translations.

**Example (sample values):** SAP has English, German, French and Polish. Dataverse has English, German, French and Dutch. Result: 3 translations are created, Polish is skipped, and the order is marked **Synced**.

## How it will work

1. **You create a consignment order**: from a work order in Dataverse, as you do today.
2. **We check nothing is missing**: if something is missing, you see a clear message on the order.
3. **We create it in SAP and double-check**: we confirm SAP really saved it before moving on.
4. **We copy the product's translations**: only for languages both systems use.
5. **The order is marked "Synced"**: only when every step above worked.

## Architecture: which systems talk to each other

Sketch (proposed, not a rendered diagram):

    ┌─ POWER PLATFORM ─────────┐   ┌─ AZURE ─────────────────────┐   ┌─ YOUR COMPANY NETWORK ─────┐
    │  Dataverse               │ ①→│  Logic App                  │ ②→│  SAP                       │
    │  consignment order and   │ ←④│  one automated workflow     │ ←③│  creates the consignment,  │
    │  product translations    │   │   ┊ Key Vault  ┊ Monitoring │   │  holds product texts       │
    └──────────────────────────┘   └─────────────────────────────┘   │  secure connection: TBC    │
                                                                     └────────────────────────────┘

1. Dataverse sends the new order to the workflow.
2. The workflow creates the consignment in SAP.
3. SAP confirms it and returns the product's translations.
4. Matching translations are saved and the order is marked Synced.

Secondary services: the workflow reads the SAP password from Key Vault and sends its run history to Monitoring. All SAP traffic goes through a secure connection (a data gateway or a private network; see question 5).

**Our suggestion:** keep it simple. One Azure Logic App runs all five steps. We'll only add more pieces if your answers show we need them.

## The language rule

Example languages:
- **SAP has:** English, German, French, Polish
- **Dataverse has:** English, German, French, Dutch
- **Result:**
  - created: English, German, French
  - skipped: Polish (Dataverse doesn't use it)
  - ignored: Dutch (SAP has no Dutch text for this product)

If a language could match two options (for example English → US or UK), we don't guess. We flag it for a person to check. If no languages match at all, the order shows **Needs checking** instead of Synced.

## Mistakes it protects you from

- **No duplicate orders**: if the flow runs twice, SAP still gets only one order.
- **No false "success"**: SAP can say "OK" with warnings and still not save. We read the order back to be sure.
- **No endless loops**: when we mark the order "Synced", that change won't start the flow again.
- **Problems are visible**: if anything is unsure, the order says "Needs checking" instead of failing silently.

## 5 quick questions before we build

Pick the closest answer. "Not sure" is fine; we'll mark it as a gap.

**1. How does SAP accept a new consignment order?**
Why we ask: we have to send orders in exactly the format SAP expects, or SAP rejects them.
- **A** Web service (SOAP) · **B** BAPI / RFC function · **C** IDoc or OData · **D** Not sure, I'll ask the SAP team

*For your tech team:* WSDL/XSD, BAPI/RFC name, IDoc type or OData service for create and for reading product texts. One product line or several per consignment?

**2. How can we be sure SAP really saved the order?**
Why we ask: SAP can reply "OK" and still not save it. Checking stops lost or doubled orders.
- **A** We can look the order up in SAP · **B** SAP can store our Dataverse order ID · **C** Both · **D** Not sure

*For your tech team:* commit behaviour and read-back operation. Can SAP store the Dataverse consignment ID as an external reference, so a retry can find the order?

**3. Where are the languages kept in Dataverse?**
Why we ask: to match languages correctly. For example, SAP calls German "D" and Dataverse calls it 1031.
- **A** Dataverse's built-in languages · **B** Our own language table · **C** Not sure

*For your tech team:* provisioned LCIDs or a custom table. We also need:
- the SAP SPRAS/LAISO to Dataverse mapping,
- the names of the consignment and translation tables,
- their key columns.

**4. Should the user wait for SAP, or just see a status?**
Why we ask: SAP can be slow. Showing a status (Processing → Synced) avoids timeouts.
- **A** Show a status (recommended) · **B** Wait for the result · **C** Not sure

*For your tech team:* trigger type (Power Automate, plugin/webhook or Dataverse connector) and the list of required fields.

**5. Where does your SAP system run?**
Why we ask: this decides how Azure can reach SAP safely, and it affects cost.
- **A** In our own data centre · **B** In a private cloud network · **C** Not sure

*For your tech team:* on-premises data gateway or VNet path; Logic Apps Consumption or Standard; identity to use for Dataverse.

**How to answer:** reply with the question number and letter, e.g. `1B 2C 3A 4A 5C`. You can add words too: `1B, 3: we use our own table`. If your chat shows clickable question cards, just click your answers there.

## What happens next

| I have the details | I don't have them yet |
|---|---|
| Reply with your answer codes. You'll get the real plan: workflow, tests and a step-by-step setup guide. | Say **"make a practice version"**. You'll get the same pack with sample data. Anything unknown is marked `TODO`. Safe to explore, not for real use. |

---

## Technical details for engineers (optional; you can skip this)

| ID | Requirement | Status | Still unknown |
|---|---|---|---|
| REQ-001 | Dataverse calls the Logic App when a consignment order is created | confirmed | Trigger mechanism |
| REQ-002 | Validate payload before SAP | confirmed | Required field list |
| REQ-003 | Map JSON → SAP XML | confirmed | WSDL / XSD / IDoc |
| REQ-004 | Create consignment in SAP | confirmed | Interface, commit, idempotency |
| REQ-005 | Read product translations from SAP | confirmed | Read operation, line count |
| REQ-006 | Translations only for SAP ∩ active Dataverse languages | confirmed | SPRAS/LAISO ↔ LCID mapping |
| REQ-007 | Mark order Synced | confirmed | Status field; meaning after partial failure |
| REQ-008 | Low volume, one order at a time | assumed | Volume and peaks |

Workflow (one stateful Logic App):
1. Trigger with a status gate: start only when status = `Submitted`. This prevents loops.
2. Validate the required fields. On failure, write the reason and set `Failed`.
3. Idempotency check: is there an existing SAP number or a pending state?
4. Map JSON → XML against the real SAP schema. No invented mappings.
5. Create in SAP:
   - Check RETURN and warnings, commit, then read the order back.
   - If the result is uncertain, set `NeedsVerification`. Never re-create blindly.
6. Get the product translations from SAP.
7. Get the active Dataverse languages and intersect through one confirmed mapping.
   - If one SAP language matches several Dataverse languages, quarantine it.
   - If there are zero matches, set `NeedsVerification`.
8. Upsert translations keyed by consignment + language, and log the omitted languages.
9. Write the SAP number and set `Synced`, only if steps 5 and 8 fully succeeded.

Trade-offs:
- **Sync vs async:** waiting for SAP risks timeouts, so a status field is safer.
- **SAP succeeds but Dataverse fails:** store the SAP number first, and resume retries at step 6.
- **Connectivity:** an on-premises SAP needs the data gateway (Consumption) or VNet integration (Standard).

**Alternative:** add an Azure Function for the mapping and the language intersection if the rules get complex. The cost is one more component to deploy and monitor.

**Not recommended yet:** a Service Bus queue. It only earns its cost if you need to ride out long SAP outages or large peaks.

---

## Where things stand

| | |
|---|---|
| Idea understood | Done |
| Your answers | 0 of 5 |
| Automatically checked | Not yet |
| Reviewed by a person | Not yet |
| Deployed | Never. FlowPilot only designs; your team deploys. |

**Words you'll see:**
- **Dataverse**: where your work orders and consignment orders live.
- **SAP**: your business system with the official consignment and product data.
- **Logic App**: an automated workflow in Azure.
- **Translation**: the product's name and description in another language.
- **Synced**: SAP and Dataverse agree, and the order is done.
- **Needs checking**: something was unclear, so a person should look.

Validation: not executed (Quick Design mode; no blueprint produced)
Deployment: not performed
Human review: pending
