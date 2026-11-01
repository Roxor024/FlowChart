# FlowPilot v0.2

Azure-first **enterprise integration engineering assistant** for Claude Code and Claude.ai. An internal-pilot prototype, not an integration runtime or deployment system.

## What it does
Turns business integration requirements into clarified specifications, a recommended Azure architecture with alternatives, an implementation plan, test cases, risk register and maintenance runbook. It retains a structured integration blueprint and emphasizes readable reports.

## Claude Code
Clone this repository and start `claude` in its root. Invoke `/flowpilot-architect` and supply the scenario from `examples/order-processing/SCENARIO.md`.

## Claude.ai
Package the `.claude/skills/flowpilot-architect` folder with `SKILL.md` at the skill-folder root, ZIP it, and upload as a custom Skill in Claude.ai. The chat environment may not be able to execute local validators; it must report validation not executed.

## Local checks
```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/validate_blueprint.py examples/order-processing/integration-blueprint.json
python tools/render_report.py examples/order-processing/integration-blueprint.json output/order-processing-report.html
```

## Safety / scope
No Azure deployment. Use only synthetic or authorized sanitized data. Never store credentials in blueprints. Human approval is separate from generated advice. See `docs/SECURITY.md`.

## Status
GitHub pilot branch; validate and review artifacts before use. Not yet independently tested across both Claude hosts.