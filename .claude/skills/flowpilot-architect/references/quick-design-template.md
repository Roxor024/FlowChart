# Quick Design reply template (beginner-friendly)

Use this for every Quick Design reply. Keep the headings and their order. Replace everything in `[brackets]`. Delete the guidance lines in *italics*.

The reader is new to integration work. They must understand, within one scroll:
1. what the integration will do,
2. what you understood from them,
3. what they need to decide next.

Technical detail is welcome, but it goes last.

## How to deliver it

- **Preferred: a rendered page.**
  1. Write the content as `quick-design.json`, in the same shape as `assets/quick-design.example.json`.
  2. Run `scripts/render_quick_design.py quick-design.json quick-design.html` and deliver the page.
  3. In chat, give a 3–5 line summary and then the questions.
  The renderer owns the layout and refuses content that breaks the rules below, so never write the HTML yourself.
- **Fallback (no Python or files): markdown** using the template further down.

`quick-design.json` fields:
- **`title`, `summary`**: one plain line each.
- **`requirements`**: 1–12 of `{text, status, note?}`. `status` is `clear`, `needs_detail` or `our_guess`.
- **`outcomes`**: 2–5 checks. **`example`**: one worked example with sample values.
- **`steps`**: 2–5 of `{title, text}`. The last step is the success state. **`suggestion`**: one sentence.
- **`architecture`**:
  - `areas`: 2–3, each `{name, main: {name, text}, support?: [≤2 boxes]}`.
  - `flow`: 1–6 of `{from, to, text}` between neighbouring areas (index 0, 1, 2).
  - `note`: optional.
- **`key_rule`**: `{title, items: [{label, text}], note?}`. **`protections`**: up to 4 of `{title, text}`.
- **`questions`**: 1–5 of `{title, why, choices, tech}`. `choices` has 2–4 entries, and the last starts with "Not sure".
- **`technical`**: optional `{requirements: [{id, text, unknown}], steps: [...], notes: [...]}`.
- **`glossary`**: up to 6 of `{term, meaning}`.

## Writing rules

- Use plain words first. Put a technical term only:
  - in a "For your tech team:" line,
  - in the technical section,
  - or in the glossary.
- Keep sentences to 25 words or fewer. Write one idea per bullet. Never write a paragraph longer than three lines.
- Label sample values as examples. Never invent real system names, table or field names, service limits or prices.
- Ask at most FIVE questions. Never mark a question as answered unless the user answered it.
- Give each question 2–4 choices lettered A, B, C…, with "Not sure" always last.
- Where to ask them:
  - If the client has a multiple-choice question tool (e.g. AskUserQuestion in Claude Code, question cards in Claude.ai), ask them there as clickable cards, after the reply text. Follow the tool's own limits, e.g. split five questions into two calls if it takes four at a time.
  - Otherwise keep them in the reply and end with the answer-code line, so the user can reply with something like `1A 2D 3B`.
  - Accept answer codes, free text or a mix. Ask again only about answers you could not map.
- Keep the design provisional while blockers are open. Do not create a blueprint unless the user asks for one.

| Instead of | Write |
|---|---|
| "Idempotency check on the external reference" | "Running it twice never creates a second order" |
| "BAPI Auto Commit does not commit on warnings" | "SAP can say OK and still not save, so we read the order back" |
| "Intersect via the SPRAS↔LCID mapping" | "Only languages both systems use get a translation" |
| "REQ-006 confirmed" | "6. Copy translations only for shared languages — Clear" |

---

## Template

```markdown
> **Draft idea · nothing has been built yet**
> ✓ 1 We understood your idea → **2 We need a few answers** → 3 We build your starter pack → 4 A person reviews it

# [Plain title: "Send new X from A to B automatically"]

[One sentence: what happens for the user, in business words. Example: "When someone creates a consignment order, it is created in SAP for them, the product's translations are copied back, and the order is marked Synced."]

## What you asked for, and what you'll get

**Requirements.** Check that we understood you.

| # | Requirement | Status |
|---|---|---|
| 1 | [plain requirement] | Clear |
| 2 | [plain requirement] | Needs detail — [what is missing, in a few words] |
| 3 | [plain requirement] | Our guess — tell us if this is wrong |

**The outcome: how we'll know it works.** Each check will be tested before real use.
- ✓ [Outcome check 1, e.g. "An order with missing information never reaches SAP. You see the reason on the order."]
- ✓ [Outcome check 2]
- ✓ [Outcome check 3]
- ✓ [Outcome check 4]

**Example (sample values):** [one concrete before → after case, e.g. "SAP has English, German, French, Polish. Dataverse has English, German, French, Dutch. → 3 translations created, Polish skipped, order marked Synced."]

## How it will work

1. **[Action title]**: [one sentence]
2. **[Action title]**: [one sentence]
3. **[Action title]**: [one sentence]
4. **[Action title]**: [one sentence]
5. **[Success state]**: [only when every step above worked]

## Architecture: which systems talk to each other

*In the rendered page this is drawn from `architecture` in `quick-design.json`. In a markdown reply, use the boxed sketch below and keep its label.*

Sketch (proposed, not a rendered diagram):

    ┌─ [AREA 1, e.g. POWER PLATFORM] ┐  ┌─ [AREA 2, e.g. AZURE] ─────┐  ┌─ [AREA 3, e.g. YOUR NETWORK] ┐
    │  [System A]                    │①→│  [Workflow]                │②→│  [System B]                  │
    │  [what it holds]               │←④│  [what it does]            │←③│  [what it does]              │
    └────────────────────────────────┘  │   ┊ secrets   ┊ monitoring │  │  [secure connection — TBC]   │
                                        └────────────────────────────┘  └──────────────────────────────┘

1. [What step ① sends]
2. [What step ② does]
3. [What comes back in step ③]
4. [What step ④ saves; the success state]

*Dashed or secondary: secret storage (Key Vault), monitoring, and the network path (gateway or private network). These are supporting services, not extra steps.*

**Our suggestion:** [one sentence, the simplest design, e.g. "Keep it simple: one Azure Logic App runs every step. We only add more pieces if your answers need them."]

## [The scenario's key rule, e.g. "The language rule"]

[Show it as an example with labelled sample values:]
- **[System A] has:** [values]
- **[System B] has:** [values]
- **Result:** created [values] · skipped [values] (reason) · ignored [values] (reason)

If a match is ambiguous, we don't guess. We flag it for a person to check.

## Mistakes it protects you from

- **[Promise 1, e.g. No duplicate orders]**: [one sentence]
- **[Promise 2, e.g. No false "success"]**: [one sentence]
- **[Promise 3, e.g. No endless loops]**: [one sentence]
- **[Promise 4, e.g. Problems are visible]**: [one sentence]

*Only promise what the design really does.*

## [N] quick questions before we build

Pick the closest answer. "Not sure" is fine; we'll mark it as a gap.

**1. [Plain question]**
Why we ask: [one sentence on the consequence]
- **A** [choice] · **B** [choice] · **C** [choice] · **D** Not sure

*For your tech team:* [precise technical ask, e.g. WSDL/XSD or BAPI name; one or several product lines?]

*(repeat; at most five questions; most important first)*

**How to answer:** reply with the question number and letter, e.g. `1A 2D 3B 4A 5C`. You can add words too: `1A, 3: we use our own table`.

## What happens next

| I have the details | I don't have them yet |
|---|---|
| Reply with your answer codes. You'll get the real plan: workflow, tests and a step-by-step setup guide. | Say **"make a practice version"**. You'll get the same pack with sample data. Anything unknown is marked `TODO`. Safe to explore, not for real use. |

---

## Technical details for engineers (optional; you can skip this)

- Requirements with IDs: REQ-001… with status (confirmed / assumed / unknown) and what is still unknown.
- Workflow steps, numbered, including validation, the idempotency check, commit and read-back, and the conditions for setting the success state.
- Trade-offs (sync vs async, partial failure, connectivity, security).
- Alternative, and what is not recommended yet, each with the reason.

---

## Where things stand

| | |
|---|---|
| Idea understood | Done |
| Your answers | 0 of [N] |
| Automatically checked | Not yet |
| Reviewed by a person | Not yet |
| Deployed | Never. FlowPilot only designs; your team deploys. |

**Words you'll see:** **[Term]**: [plain meaning] · **[Term]**: [plain meaning] *(at most six terms)*

Validation: not executed (Quick Design mode; no blueprint produced)
Deployment: not performed
Human review: pending
```
