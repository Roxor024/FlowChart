# FlowPilot output contract — Quick Design / Full Build Pack

**Default: Quick Design.** One page written for someone new to integration work. It tells them what will happen and what they need to decide, in plain words, before any technical detail. Fill `references/quick-design-template.md` in this order:

0. **Status line**: "Draft idea · nothing has been built yet", plus the 4-step progress line (Understood ✓ → Your answers → Starter pack → Human review).
1. **Title and one plain sentence** on what the integration does for the user.
2. **What you asked for, and what you'll get**: numbered plain-language requirements, each tagged Clear / Needs detail / Our guess (internal REQ IDs only in the technical section), and 3–5 outcome checks rewritten from the acceptance criteria, with one worked example using labelled sample values.
3. **How it will work**: at most five numbered steps; the last is the success state.
4. **Architecture**: the systems grouped by trust area (for example Power Platform | Azure | Your company network), main path numbered ①–④, supporting services (Key Vault, monitoring, gateway/private network) shown as secondary, and a numbered legend. Without a rendering client, use the boxed text sketch from the template, labelled as a sketch; a Mermaid block alone is not a rendered diagram.
5. **Our suggestion**: one sentence naming the simplest viable design. Alternatives belong in the technical section.
6. **The scenario's key rule as an example** (for instance "SAP has X · Dataverse has Y → created / skipped / ignored"), and that ambiguous matches are flagged for a person, never guessed.
7. **Mistakes it protects you from**: 3–4 plain promises that the design really delivers.
8. **Questions (at most five)**: plain title, "Why we ask:" in one sentence, 2–4 answer choices lettered A, B, C… with "Not sure" always last (recorded as a gap), and a "For your tech team:" line with the precise technical ask. Ask them as clickable cards when the client has a multiple-choice question tool; otherwise end the list with an answer-code line ("Reply like: 1A 2D 3B 4A 5C"). Answer codes, free text and a mix are all accepted.
9. **Next step**: two labelled choices, "I have the details" (answer the questions) and "I don't have them yet" (say "make a practice version" for a Full Build Pack with sample data and marked TODOs, not for real use).
10. **Technical details for engineers** (optional, last): REQ table with what is still unknown, numbered workflow steps, trade-offs, alternative and "not recommended yet".
11. **Where things stand**: Idea understood · Your answers (0 of N) · Automatically checked · Reviewed by a person · Deployed (never by FlowPilot), followed by the standard Validation / Deployment / Human review lines saying the same thing.
12. **Words you'll see**: at most six terms used in the reply.

Writing rules: sentences of 25 words or fewer, one idea per bullet, no paragraph over three lines, sample values labelled as examples, no invented system names, field names or limits. Keep the ≤5 questions, provisional-status and no-blueprint rules. Do NOT generate the long ten-section manual or code ZIP by default. A worked example is in `examples/quick-design-dataverse-sap.md` at the repository root (not packaged).

**Full Build Pack: opt-in or explicitly requested.** Apply the sections below only in this mode. A provisional build pack may contain synthetic adapters, but its missing WSDL and Dataverse schema must be prominent.

The user's primary output is an implementation guide, not JSON and not an architecture audit. Keep the machine-readable blueprint in a separate advanced export; it provides validation, traceability and future automation.

## Required order

1. **What are we building?** Explain goal and business benefit in two simple sentences. Define specialist terms on first use. State unknowns honestly.
2. **At a glance.** Show the steps, prerequisites, expected services, necessary permissions and cost considerations without inventing prices.
3. **Visible architecture diagram.** Render source → ingress/security → persistence → queue → worker → destination, with arrows, labels, trust boundaries and error/retry paths. For HTML use accessible inline SVG or local image; no remote scripts or CDNs. Mermaid source may be exported but cannot substitute for a visibly rendered diagram. For provisional designs mark assumptions and avoid invented services.
4. **Prepare.** Give access/permissions checklist, dependencies, safe SAMPLE names and test payloads, budget approvals and missing business decisions.
5. **Build it step by step.** One detailed section for EVERY implementationTask in blueprint, plus setup dependencies. Follow references/implementation-playbook.md. Each step needs exact actions, check, troubleshooting and rollback.
6. **Test as you go.** Synthetic test input and expected output for each step, completion checklist, with execution state NOT RUN unless evidence exists.
7. **Walk through one example.** Trace synthetic message from source to destination, then duplicate/failure/recovery.
8. **Fix problems.** Symptom → likely cause → safe verification → correction → re-test.
9. **Finish and operate.** Monitoring, alerts, recovery, owner roles, open decisions and handover checklist. State that no Azure deployment or human approval occurred.
10. **Technical appendix (optional).** Blueprint JSON, schema validation, ADRs, traceability, risks, deeper architecture and starter artifacts.

## Presentation rules

- Keep the first screen beginner-friendly and visual; no raw JSON or long tables of IDs.
- Every task ID in the blueprint has a matching practical step. Every required component is accounted for.
- Explain where and how to configure something, with concrete but sanitized examples; do not invent portal labels.
- Don't present code as deployed or checks as passed unless executed; all tests start NOT RUN.
- Users can mark checklist items manually, but nothing is pre-checked.
- For vague requirements, give a decision-first guide rather than pretending there is a complete deployable plan.
- The existing scripts/render_report.py produces a TECHNICAL OVERVIEW, not this guided HTML experience. A new renderer must be built before claiming this is automatic.

## Generated source-code and visual-reference acceptance criteria

- **Files, not code snippets alone:** generate copyable, named source/config files whenever needed (Logic Apps workflow definition, connection parameter references, Azure Functions trigger and implementation, models/mappers, tests, dependency manifest, local-settings.example.json, queue manifest, optional infrastructure-as-code). Show the exact destination path, required edits, test command and expected result for every file.
- **Completeness inventory:** include an explicit matrix marking each artifact as WORKING LOCAL EXAMPLE / UNVERIFIED STARTER / TEMPLATE ONLY / REQUIRES CONTRACT. Never imply a JSON routing sketch is an importable Logic App; never claim SAP calls or Dataverse updates work if not implemented.
- **Seven-operation use cases:** make one routing entry and mapping per business operation; include invalid/unknown route and error handling. Ensure queue names and function trigger bindings match exactly. Protect against Dataverse update loops, duplicate delivery, SAP success plus Dataverse update failure, and poison-message handling.
- **Images where they make the guide easier:** provide a visible system architecture drawing, component-specific step location visuals, a service-bus queue layout, and Logic App/Function routing flows. Prefer generated local SVG with clear numbered callouts and arrows. Mark any mock Azure Portal screenshot as an ILLUSTRATION; use real official screenshots only where authorized and current. Never invent UI states or claim a generated illustration is a screenshot.
- **Don't skip obvious steps:** even creating a resource group, choosing a subscription, selecting a region, naming a namespace, creating each queue, setting up connections, local test run, deployment approval and result observation must be accounted for. If too long for one screen, organize the detail into progressive disclosure panels, not omissions.
- **Evidence:** local unit tests may demonstrate mocked transformations/routing only; clearly mark external SAP, Dataverse and Azure integration tests NOT EXECUTED until actually run.

## Documentation placement

Each implementation stage must contain Requirement, Why, Official Azure documentation (direct Microsoft Learn how-to URL), Code/configuration file and path (or No code required), Actions, Expected outcome, Verify (NOT RUN unless executed), and Troubleshooting/rollback. Place the documentation link beside the relevant task, not only in a bibliography. Example for Logic App Standard: https://learn.microsoft.com/en-us/azure/logic-apps/create-single-tenant-workflows-azure-portal . A generic docs landing page is insufficient when a specific how-to is available. Do not invent links, portal clicks or SAP-specific mappings.
