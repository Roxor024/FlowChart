#!/usr/bin/env python3
"""Run every offline check on a FlowPilot build pack in one go and print one summary.

Usage: python check_pack.py <pack-dir> [--blueprint integration-blueprint.json]
Checks: JSON parses · XML well-formed · Python compiles · HTML tags balanced, no remote scripts ·
        local tests (pytest if installed, else unittest) · blueprint validation · secret scan.
Writes <pack-dir>/evidence/check-pack.txt (the full output, incl. test output) and prints its SHA-256.
Exit codes: 0 no check failed (NOT RUN items allowed) · 1 at least one check failed · 2 bad arguments.
Nothing here touches Azure or any other external system; passing these checks is not a production sign-off.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "node_modules", ".venv"}
TEXT_EXT = {".py", ".json", ".xml", ".yaml", ".yml", ".html", ".md", ".txt", ".bicep", ".ps1", ".sh", ".cs", ".js", ".ts"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr",
        "path", "rect", "circle", "line", "polyline", "polygon", "ellipse", "stop", "use"}


def load_validator():
    spec = importlib.util.spec_from_file_location("_fp_validator", Path(__file__).with_name("validate_blueprint.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def files(root: Path, *exts):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP_DIRS) and (not exts or p.suffix.lower() in exts):
            yield p


class _Html(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.problems = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and (a.get("src") or "").startswith(("http:", "https:", "//")):
            self.problems.append(f"remote script {a['src']}")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
        else:
            self.problems.append(f"line {self.getpos()[0]}: stray </{tag}>")


def run_tests(root: Path, runner: str = "auto"):
    test_files = [p for p in files(root, ".py") if p.name.startswith("test_")]
    if not test_files:
        return "NOT RUN", "no test_*.py files", ""
    test_dir = test_files[0].parent
    work = test_dir.parent if (test_dir.name == "tests") else test_dir
    if runner == "pytest" or (runner == "auto" and importlib.util.find_spec("pytest")):
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(test_dir.relative_to(work))]
    else:
        rel = str(test_dir.relative_to(work))
        # The test folder is its own top level, so it does not need an __init__.py.
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", rel, "-t", rel]
    try:
        p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return "FAIL", "tests timed out after 300 s", ""
    output = (p.stdout + p.stderr).strip()
    last = [line for line in output.splitlines() if line.strip()][-1:] or ["(no output)"]
    if re.search(r"\bRan 0 tests\b|no tests ran", output, re.I):
        return "FAIL", f"{' '.join(cmd[2:3])}: no tests found (write unittest.TestCase classes)", output
    return ("PASS" if p.returncode == 0 else "FAIL"), f"{' '.join(cmd[2:3])}: {last[0]}", output


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pack")
    ap.add_argument("--blueprint", default="integration-blueprint.json")
    ap.add_argument("--runner", choices=("auto", "pytest", "unittest"), default="auto",
                    help="test runner for the pack's local tests (default: pytest if installed, else unittest)")
    args = ap.parse_args(argv[1:])
    root = Path(args.pack)
    if not root.is_dir():
        print(f"ERROR: {root} is not a folder", file=sys.stderr)
        return 2

    results = []   # (check, result, detail)

    bad = []
    for p in files(root, ".json"):
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except ValueError as exc:
            bad.append(f"{p.relative_to(root)}: {exc}")
    results.append(("JSON parses", "FAIL" if bad else "PASS", "; ".join(bad) or f"{len(list(files(root, '.json')))} files"))

    bad = []
    for p in files(root, ".xml"):
        try:
            ET.parse(p)
        except ET.ParseError as exc:
            bad.append(f"{p.relative_to(root)}: {exc}")
    n = len(list(files(root, ".xml")))
    results.append(("XML well-formed", "FAIL" if bad else ("PASS" if n else "NOT RUN"), "; ".join(bad) or f"{n} files"))

    bad = []
    for p in files(root, ".py"):
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except (SyntaxError, ValueError) as exc:
            bad.append(f"{p.relative_to(root)}: line {getattr(exc, 'lineno', '?')}: {getattr(exc, 'msg', exc)}")
    n = len(list(files(root, ".py")))
    results.append(("Python compiles", "FAIL" if bad else ("PASS" if n else "NOT RUN"), "; ".join(bad) or f"{n} files"))

    bad = []
    for p in files(root, ".html"):
        h = _Html()
        h.feed(p.read_text(encoding="utf-8"))
        if h.stack:
            h.problems.append(f"unclosed <{'>, <'.join(h.stack[-3:])}>")
        bad += [f"{p.relative_to(root)}: {msg}" for msg in h.problems]
    n = len(list(files(root, ".html")))
    results.append(("HTML balanced, no remote scripts", "FAIL" if bad else ("PASS" if n else "NOT RUN"),
                    "; ".join(bad[:5]) or f"{n} files"))

    yamls = list(files(root, ".yaml", ".yml"))
    if yamls and importlib.util.find_spec("yaml"):
        import yaml  # noqa: PLC0415
        bad = []
        for p in yamls:
            try:
                yaml.safe_load(p.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                bad.append(f"{p.relative_to(root)}: {str(exc).splitlines()[0]}")
        results.append(("YAML parses", "FAIL" if bad else "PASS", "; ".join(bad) or f"{len(yamls)} files"))
    elif yamls:
        results.append(("YAML parses", "NOT RUN", "PyYAML not installed"))

    status, detail, test_output = run_tests(root, args.runner)
    results.append(("Local tests (synthetic data)", status, detail))

    validator = None
    try:
        validator = load_validator()
    except Exception as exc:  # pragma: no cover - only when the skill folder is broken
        results.append(("Blueprint validation", "NOT RUN", f"validator unavailable: {exc}"))
    bp = root / args.blueprint
    if validator and bp.is_file():
        try:
            doc = json.loads(bp.read_text(encoding="utf-8"))
            code, errors, warnings = validator.validate(doc, None, root)
            label = {0: "PASS", 1: "FAIL", 3: "NOT RUN"}.get(code, "FAIL")
            detail = "; ".join(errors[:3]) or (f"{len(warnings)} warnings: " + "; ".join(warnings[:2]) if warnings else "0 warnings")
            results.append(("Blueprint validation", label, f"status={doc.get('status')}; {detail}"))
        except ValueError as exc:
            results.append(("Blueprint validation", "FAIL", f"{bp.name}: {exc}"))
    elif validator:
        results.append(("Blueprint validation", "NOT RUN", f"{args.blueprint} not found"))

    hits = []
    if validator:
        for p in files(root):
            if p.suffix.lower() in TEXT_EXT and "evidence" not in p.relative_to(root).parts:
                text = p.read_text(encoding="utf-8", errors="replace")
                for pat in validator.SECRET_PATTERNS:
                    if pat.search(text):
                        hits.append(str(p.relative_to(root)))
                        break
    results.append(("No secrets in files", "FAIL" if hits else "PASS", ", ".join(hits) or "secret patterns not found"))

    for d in root.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)

    width = max(len(r[0]) for r in results)
    lines = ["FlowPilot pack check (offline only: nothing was run against Azure or other real systems)", ""]
    lines += [f"{name.ljust(width)}  {res:<7}  {detail}" for name, res, detail in results]
    failed = [r for r in results if r[1] == "FAIL"]
    lines += ["", f"Result: {'FAIL' if failed else 'PASS'} ({len(failed)} failed, "
                  f"{sum(r[1] == 'NOT RUN' for r in results)} not run). Not a production sign-off."]
    summary = "\n".join(lines)
    evidence = root / "evidence"
    evidence.mkdir(exist_ok=True)
    report = evidence / "check-pack.txt"
    report.write_text(summary + ("\n\n--- test output ---\n" + test_output if test_output else "") + "\n", encoding="utf-8")
    print(summary)
    print(f"Evidence: {report.relative_to(root)} sha256={hashlib.sha256(report.read_bytes()).hexdigest()}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
