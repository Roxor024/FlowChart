"""Shared helpers: import the skill's scripts from their single source location."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "flowpilot-architect"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load("validate_blueprint")
renderer = load("render_report")
EXAMPLE = json.loads((SKILL / "assets" / "example-blueprint.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((SKILL / "assets" / "integration-blueprint.schema.json").read_text(encoding="utf-8"))


def fresh():
    return copy.deepcopy(EXAMPLE)


def run(doc):
    """(exit_code, errors, warnings)"""
    return validator.validate(doc, SCHEMA)


def approve(doc, reviewer="Jane Doe", when="2026-10-30T10:00:00Z", ref="CAB-1234"):
    doc["status"] = "approved"
    doc["reviewStatus"] = "approved"
    doc["reviewEvidence"] = {"reviewer": reviewer, "reviewedAt": when, "evidenceRef": ref}
    for q in doc["openQuestions"]:
        q["blocking"] = False
    for r in doc["requirements"]:
        if r["status"] == "unknown":
            r["status"] = "assumed"
    return doc
