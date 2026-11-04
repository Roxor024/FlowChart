#!/usr/bin/env python3
"""Thin wrapper kept for README/CI compatibility. Source of truth:
.claude/skills/flowpilot-architect/scripts/validate_blueprint.py (shipped inside the Claude.ai skill ZIP)."""
import runpy
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "flowpilot-architect" / "scripts" / "validate_blueprint.py"
sys.argv[0] = str(TARGET)
runpy.run_path(str(TARGET), run_name="__main__")
