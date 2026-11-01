# FlowPilot v0.3 — Azure Integration Engineering Skill

An **Azure-first integration design and review assistant** for Claude Code and Claude Desktop / Claude.ai. No automatic cloud deployment.

## Experience
Describe an integration requirement; FlowPilot clarifies constraints, proposes patterns, documents tradeoffs and produces a structured blueprint plus human-readable architecture, build, test and operations guidance. Documents remain draft until human review.

## Claude Desktop / Claude.ai packaging
From the repo root:
```bash
cd .claude/skills
zip -r ../../../flowpilot-architect-v0.3.zip flowpilot-architect
```
Upload the ZIP as a Claude custom Skill. ZIP root must contain `flowpilot-architect/SKILL.md`, `assets/integration-blueprint.schema.json`, `assets/example-blueprint.json`, `scripts/validate_blueprint.py`, and `references/`. When code execution or `jsonschema` is unavailable, report that full validation was not executed. This project does not rely on ChatGPT ZIP downloads.

## Claude Code
Clone branch `flowpilot-v0.3`, start Claude Code at repository root, invoke `/flowpilot-architect`.

## Test locally
```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/validate_blueprint.py examples/order-processing/integration-blueprint.json
python tools/render_report.py examples/order-processing/integration-blueprint.json output/order-processing-report.html
```
Then open `output/order-processing-report.html` in a browser.

## Status
**Prototype**: no customer data, no deployments, no production claims. Validator checks format and evidence fields, not the authenticity of a human or actual test execution. Authenticated organization approvals and tamper-evident records require a future platform service. Independent tests in Claude Desktop and Claude Code still required.

This repository is public. Do not upload employer/customer information.
