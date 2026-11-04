# FlowPilot v0.4.1

Azure-first **integration engineering assistant** packaged as a Claude Skill for Claude Code and Claude.ai. An internal-pilot prototype: it designs and reviews, it never deploys.

## What it does
Turns integration requirements into clarified requirements (with stable IDs and explicit unknowns/conflicts), a recommended Azure architecture with alternatives, ADRs, an implementation plan, a test matrix, a risk register and operations guidance — plus a machine-readable blueprint that an offline validator checks.

## Layout
```
.claude/skills/flowpilot-architect/   ← the skill (this folder is the Claude.ai upload)
  SKILL.md
  references/   workflow, Azure patterns, output contract, reference scenario
  assets/       integration-blueprint.schema.json (0.4.0), example-blueprint.json
  scripts/      validate_blueprint.py, render_report.py, render_quick_design.py
examples/       order-processing (draft), vague-sap-crm and conflicting-erp-sla (provisional),
                quick-design-dataverse-sap.md (markdown Quick Design reply), quick-design-sftp.json (page input)
tools/          thin wrappers + package_skill.py
tests/          unit, regression (adversarial) and packaging tests
```

## Claude Code
Clone the repository, run `claude` in its root and invoke `/flowpilot-architect` with the scenario in `examples/order-processing/SCENARIO.md`.

## Claude.ai
```sh
python tools/package_skill.py          # writes dist/flowpilot-architect.zip
```
Upload the ZIP as a custom skill. It contains the schema, example, validator and renderer. If the chat environment cannot run Python or lacks `jsonschema`, the skill must report `Validation: NOT EXECUTED`.

## Local checks
```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/validate_blueprint.py examples/order-processing/integration-blueprint.json
python tools/render_report.py examples/order-processing/integration-blueprint.json output/order-processing-report.html
python .claude/skills/flowpilot-architect/scripts/render_quick_design.py examples/quick-design-sftp.json output/quick-design-sftp.html
```
Validator exit codes: `0` passed automated checks (not approval) · `1` invalid · `2` unreadable · `3` not executed (`jsonschema` missing). Warnings do not fail validation.

`--evidence-dir DIR` makes the validator check that every `passed`/`failed` test's `artifactHash` matches the SHA-256 of the artifact at `DIR/<evidenceRef>`. Without it, test evidence is reported as NOT VERIFIED.

The renderer validates first and **refuses** to write a report for an invalid or unvalidated blueprint (exit 1, or 3 if `jsonschema` is missing). `--preview` writes a draft marked NOT VALIDATED with any approval claim hidden (exit 4). Approvals are always displayed as claims to confirm in your review system.

## Blueprint status model
| Status | Meaning |
|---|---|
| `provisional` | Requirements too vague or conflicting for a full design; sections may be empty; gaps recorded as questions |
| `draft` | Complete proposal awaiting human review |
| `approved` | Human reviewer, RFC 3339 review time and an external review record; no blocking questions, open conflicts or unknown requirements |

## Safety / scope
No Azure deployment or resource-changing commands. Synthetic or authorised sanitised data only. Never store credentials in blueprints. Approval and test results come from people and CI, never from the model. See `docs/SECURITY.md`.

## Limits
- A blueprint's `approved` status and test results are **claims**. Offline checks verify their shape (and, with `--evidence-dir`, artifact hashes), not who approved or whether a test really ran. Confirm approvals in your PR/change system.
- `tests/test_retry_model.py` models documented Service Bus behaviour; it is not a test against Azure.

## Status
Pilot, based on `flowpilot-v0.3`. Validate and review every artifact before use. See `CHANGELOG.md`.
