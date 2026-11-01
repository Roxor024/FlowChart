# FlowPilot project guidance

This repository contains the Azure-first FlowPilot Architect Claude Skill.
Use `.claude/skills/flowpilot-architect/SKILL.md` and its references when planning integrations.
No cloud deployments, secrets, live customer data or mutating actions.
Treat all output as provisional until reviewed; run local validators when available.
Prefer readable HTML/Markdown engineering reports with diagrams and short actionable sections.
Run `python -m unittest discover -s tests` after changing the skill, schema or scripts. Keep the schema version (0.4.0) identical across SKILL.md, schema, scripts, README and CHANGELOG.
The skill folder must stay self-contained for the Claude.ai ZIP: never reference files outside `.claude/skills/flowpilot-architect/` from SKILL.md.
