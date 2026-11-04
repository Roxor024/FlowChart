#!/usr/bin/env python3
"""Build the Claude.ai upload: dist/flowpilot-architect.zip with SKILL.md at the skill-folder root.

Only files inside .claude/skills/flowpilot-architect are packaged, so the ZIP is self-contained
(schema, example, validator and renderer included). Caches and hidden files are excluded.
Usage: python tools/package_skill.py [output.zip]
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "flowpilot-architect"
REQUIRED = ["SKILL.md", "references/workflow.md", "references/azure-patterns.md", "references/outputs.md",
            "references/order-processing-scenario.md", "assets/integration-blueprint.schema.json",
            "assets/example-blueprint.json", "scripts/validate_blueprint.py", "scripts/render_report.py"]


def skill_files() -> list[Path]:
    return sorted(p for p in SKILL.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                  and not any(part.startswith(".") for part in p.relative_to(SKILL).parts))


def build(out: Path) -> list[str]:
    missing = [r for r in REQUIRED if not (SKILL / r).is_file()]
    if missing:
        raise SystemExit("missing skill files: " + ", ".join(missing))
    out.parent.mkdir(parents=True, exist_ok=True)
    names = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in skill_files():
            name = "flowpilot-architect/" + path.relative_to(SKILL).as_posix()
            zf.write(path, name)
            names.append(name)
    return names


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "flowpilot-architect.zip"
    for n in build(target):
        print(" ", n)
    print(target)
