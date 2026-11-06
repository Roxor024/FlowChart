# FlowPilot v0.4.1

FlowPilot is a free, open-source **Claude Skill that helps you design Azure integrations**: connecting apps such as an ERP, CRM, SAP or Dataverse through Azure services like API Management, Functions, Logic Apps, Service Bus, Event Grid and SFTP.

You describe what should happen in plain words. FlowPilot replies with a one-page **Quick Design**:
- what it understood;
- how the integration would work, with a diagram;
- what could go wrong;
- the few questions that still need answering.

When you're ready, it can make a **build pack**: a step-by-step guide, starter code, local tests and a checked design file.

> **Important: FlowPilot designs; it never deploys.** It creates nothing in Azure and never asks for passwords or keys. Everything it produces is a draft for a person to review. A "practice version" uses sample data and is not for real use. Read the [disclaimer](#disclaimer) before relying on any output.

## Install

### Claude.ai (Pro, Max, Team or Enterprise)
1. Download `flowpilot-architect.zip` from the latest [release](../../releases), or build it yourself with `python tools/package_skill.py` (it writes `dist/flowpilot-architect.zip`).
2. In Claude, open **Customize > Skills** and upload the ZIP. Code execution must be turned on in your settings.
3. Start a chat and describe your integration, for example: *"Our mobile app needs to show order status from our ERP, which only has a SOAP interface."*

### Claude Code
Clone this repository and run `claude` in its root. The skill in `.claude/skills/flowpilot-architect/` is picked up automatically. Try it with the scenario in `examples/order-processing/SCENARIO.md`.

## How a session goes
1. **Describe the integration.** You get a Quick Design page and up to five plain questions. Answer them in your own words; "I don't know" is fine.
2. **Answer the questions.** You get an updated page with the settled design.
3. **Say "build it"** when nothing is blocking, or **"make a practice version"** to explore with sample data. Either way you get a build pack with a guide page, code, tests and a check report.

## What's in this repository
```
.claude/skills/flowpilot-architect/   the skill (this folder is what the ZIP contains)
  SKILL.md       instructions Claude follows
  references/    templates, procedures, Azure patterns, checked documentation links
  assets/        blueprint schema (0.4.0) and examples
  scripts/       validate_blueprint.py, render_report.py, render_quick_design.py,
                 render_build_guide.py, check_pack.py
examples/        worked examples (order processing, vague and conflicting requests, Quick Designs)
tools/           packaging and thin wrappers around the scripts
tests/           unit, regression and packaging tests (synthetic data only)
```

## Local checks (for contributors)
```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/validate_blueprint.py examples/order-processing/integration-blueprint.json
python tools/render_report.py examples/order-processing/integration-blueprint.json output/order-processing-report.html
python .claude/skills/flowpilot-architect/scripts/render_quick_design.py examples/quick-design-sftp.json output/quick-design-sftp.html
python .claude/skills/flowpilot-architect/scripts/check_pack.py tests/fixtures/sample-pack
```
Validator exit codes: `0` passed automated checks (not approval) · `1` invalid · `2` unreadable · `3` not executed (`jsonschema` missing). Warnings do not fail validation.

`--evidence-dir DIR` makes the validator check that every `passed`/`failed` test's `artifactHash` matches the SHA-256 of the artifact at `DIR/<evidenceRef>`. Without it, test evidence is reported as NOT VERIFIED.

The report renderer validates first and **refuses** to write a report for an invalid or unvalidated blueprint (exit 1, or 3 if `jsonschema` is missing). `--preview` writes a draft marked NOT VALIDATED with any approval claim hidden (exit 4). Approvals are always displayed as claims to confirm in your review system.

## Blueprint status model
| Status | Meaning |
|---|---|
| `provisional` | Requirements too vague or conflicting for a full design; sections may be empty; gaps recorded as questions |
| `draft` | Complete proposal awaiting human review |
| `approved` | Human reviewer, RFC 3339 review time and an external review record; no blocking questions, open conflicts or unknown requirements |

## Safety
- No Azure deployment or resource-changing commands.
- Use synthetic or sanitised data. Don't paste customer data, passwords, keys or connection strings into a chat.
- Credentials never go in blueprints; the validator rejects common secret formats.
- Approval and test results come from people and CI, never from the model.

See [`docs/SECURITY.md`](docs/SECURITY.md) for details and how to report a problem.

## Disclaimer
FlowPilot is an experimental design aid, provided "as is" under the [MIT License](LICENSE) without warranty of any kind. Its output can be wrong or incomplete: service limits, prices and portal steps change, and documentation links may go stale. A qualified engineer must review every design, run the tests in a safe environment and follow your organisation's security and change processes before anything reaches production. Approvals and test results in a blueprint are **claims**: offline checks verify their shape (and, with `--evidence-dir`, artifact hashes), not who approved or whether a test really ran. `tests/test_retry_model.py` models documented Service Bus behaviour; it is not a test against Azure.

FlowPilot is a community project. It is not affiliated with or endorsed by Microsoft or Anthropic. Azure and the Azure service names are trademarks of Microsoft.

## Contributing
Issues and pull requests are welcome. Please run the local checks above and keep all examples synthetic. See `CHANGELOG.md` for the history.
