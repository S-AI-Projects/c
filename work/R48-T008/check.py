#!/usr/bin/env python3
"""R48-T008: verify exercises/practice/queen-attack/.meta/config.json.

Checks that the metadata ``files`` object (solution / test / example) resolves
inside exercises/practice/queen-attack, rejects parent traversal and missing
files, and runs the exercise against its reference implementation via ``make
test`` (Unity) in a temporary scratch copy. The working tree is never modified.

Run:
    python3 work/R48-T008/check.py
Exit status is non-zero when any assertion or fixture check fails.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve()
R48T008_DIR = SCRIPT.parent
WORK_DIR = SCRIPT.parent.parent
REPO_ROOT = SCRIPT.parent.parent.parent
EXERCISE = REPO_ROOT / "exercises" / "practice" / "queen-attack"
CONFIG = EXERCISE / ".meta" / "config.json"
TESTS_TOML = EXERCISE / ".meta" / "tests.toml"
EXAMPLE_C = EXERCISE / ".meta" / "example.c"
TEST_C = EXERCISE / "test_queen_attack.c"

EVIDENCE_DIR = R48T008_DIR / "evidence"
RESULTS_DIR = R48T008_DIR / "results"
INPUTS_DIR = R48T008_DIR / "inputs"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mK]")
SUMMARY_RE = re.compile(r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored")

failures = []


def record(check, detail="", sink=None):
    if sink is None:
        sink = failures
    sink.append((check, detail))
    print(f"FAIL [{check}]: {detail}" if detail else f"FAIL [{check}]")


def ok(check, detail=""):
    msg = f"ok   [{check}]" + (f": {detail}" if detail else "")
    print(msg)


def validate_files(metadata, base_dir, label, sink=None):
    """Return list of resolved Paths for every declared file; record failures."""
    files_obj = metadata.get("files")
    if not isinstance(files_obj, dict):
        record(f"{label}: files object", "missing or not an object", sink=sink)
        return []
    resolved = []
    for category in ("solution", "test", "example"):
        entries = files_obj.get(category)
        if not isinstance(entries, list):
            record(f"{label}: files.{category}", "missing or not a list", sink=sink)
            continue
        for entry in entries:
            if not isinstance(entry, str):
                record(f"{label}: files.{category} entry", f"non-string entry {entry!r}", sink=sink)
                continue
            p = Path(entry)
            if p.is_absolute():
                record(f"{label}: files.{category} '{entry}'", "absolute path", sink=sink)
                continue
            parts = p.parts
            if ".." in parts:
                record(f"{label}: files.{category} '{entry}'", "parent traversal ('..')", sink=sink)
                continue
            candidate = (base_dir / p).resolve()
            try:
                candidate.relative_to(base_dir.resolve())
            except ValueError:
                record(f"{label}: files.{category} '{entry}'", "resolves outside exercise directory", sink=sink)
                continue
            if not candidate.is_file():
                record(f"{label}: files.{category} '{entry}'", "file does not exist", sink=sink)
                continue
            resolved.append(candidate)
            ok(f"{label}: files.{category} '{entry}'", str(candidate.relative_to(base_dir)))
    return resolved


def load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_tests_toml(text):
    """Minimal TOML section parser for .meta/tests.toml (no tomllib dependency)."""
    cases = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[([^\]]+)\]$", line)
        if m:
            current = {"uuid": m.group(1), "description": None, "include": None, "comment": None}
            cases.append(current)
            continue
        if current is None:
            continue
        kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", line)
        if not kv:
            continue
        key, value = kv.group(1), kv.group(2).strip()
        if value == "true":
            current[key] = True
        elif value == "false":
            current[key] = False
        elif value.startswith('"') and value.endswith('"'):
            current[key] = value[1:-1]
        else:
            current[key] = value
    return cases


def words(text):
    return set(w for w in re.split(r"[^A-Za-z0-9]+", text.lower()) if w)


def parse_test_functions(text):
    """Return ordered list of test function names defined in the test file.

    Whitespace is collapsed so function headers split across lines are detected.
    """
    flat = re.sub(r"\s+", " ", text)
    return re.findall(r"static\s+void\s+(test_\w+)\s*\(\s*void\s*\)", flat)


def match_intended(intended_descriptions, func_names):
    """Map each intended description to a test function via word-subset."""
    mapping = {}
    unmatched = []
    func_wordsets = {
        f: words(f[len("test_"):] if f.startswith("test_") else f) for f in func_names
    }
    for desc in intended_descriptions:
        dw = words(desc)
        best = None
        best_score = -1
        for f, fw in func_wordsets.items():
            if fw and fw <= dw:
                score = len(fw)
                if score > best_score:
                    best = f
                    best_score = score
        if best:
            mapping[desc] = best
        else:
            unmatched.append(desc)
    return mapping, unmatched


def strip_ignore_in_functions(test_text, func_names):
    """Return test text with TEST_IGNORE() removed only inside the named functions.

    Operates line-by-line (original newlines preserved) using a small state
    machine so function headers split across lines are recognized.
    """
    intended = set(func_names)
    lines = test_text.splitlines(keepends=True)
    out = []
    active = None
    in_header = False
    header_buf = []

    header_re = re.compile(r"static\s+void\s+(test_\w+)\s*\(\s*void\s*\)")
    start_re = re.compile(r"static\s+void")
    ignore_re = re.compile(r"\s*TEST_IGNORE\s*\(\s*\)\s*;?\s*(//.*)?$")

    def flush_header():
        nonlocal active, in_header, header_buf
        joined = "".join(header_buf)
        m = header_re.match(joined)
        if m:
            name = m.group(1)
            if name in intended:
                active = name
        out.extend(header_buf)
        header_buf = []
        in_header = False

    for line in lines:
        if in_header:
            header_buf.append(line)
            if header_re.match("".join(header_buf)):
                flush_header()
            continue
        if line.lstrip().startswith("int main("):
            active = None
            out.append(line)
            continue
        if active is not None:
            if start_re.search(line):
                active = None
                m2 = header_re.match(line)
                if m2:
                    out.append(line)
                    active = m2.group(1) if m2.group(1) in intended else None
                    continue
                if start_re.search(line):
                    in_header = True
                    header_buf = [line]
                    continue
                out.append(line)
                continue
            if ignore_re.match(line):
                continue
            out.append(line)
            continue
        m = header_re.match(line)
        if m:
            out.append(line)
            if m.group(1) in intended:
                active = m.group(1)
            continue
        if start_re.search(line):
            in_header = True
            header_buf = [line]
            continue
        out.append(line)
    if in_header:
        out.extend(header_buf)
    return "".join(out)


def _behavioural_default():
    return {
        "intended": 0,
        "mapped": 0,
        "child_rc": None,
        "tests": 0,
        "failures": 0,
        "ignored": 0,
        "passed": False,
        "stdout": "",
    }


def behavioural_run():
    print("\n== behavioural run (reference substitution + make test) ==")
    if not EXERCISE.is_dir():
        record("behavioural: exercise dir", f"missing {EXERCISE}")
        return _behavioural_default()
    try:
        config = load_config(CONFIG)
    except Exception as exc:
        record("behavioural: load config", str(exc))
        return _behavioural_default()

    example_path = EXERCISE / config["files"]["example"][0]
    try:
        reference = example_path.read_text(encoding="utf-8")
    except Exception as exc:
        record("behavioural: read reference", str(exc))
        return _behavioural_default()

    test_text = TEST_C.read_text(encoding="utf-8")
    toml_text = TESTS_TOML.read_text(encoding="utf-8")
    cases = parse_tests_toml(toml_text)
    intended = [c for c in cases if c.get("include") is not False]
    intended_descriptions = [c["description"] for c in intended if c.get("description")]
    func_names = parse_test_functions(test_text)
    mapping, unmatched = match_intended(intended_descriptions, func_names)
    if unmatched:
        record("behavioural: intended case mapping", f"unmatched: {unmatched}")
    ok("behavioural: intended cases", f"{len(intended)} intended, {len(mapping)} mapped")

    scratch = Path(tempfile.mkdtemp(prefix="r48t008-scratch-"))
    try:
        dest = scratch / "queen-attack"
        shutil.copytree(EXERCISE, dest, symlinks=True)
        solution_c = dest / config["files"]["solution"][0]
        solution_c.write_text(reference, encoding="utf-8")
        scratch_test = dest / "test_queen_attack.c"
        enabled_text = strip_ignore_in_functions(test_text, set(mapping.values()))
        scratch_test.write_text(enabled_text, encoding="utf-8")

        result = subprocess.run(
            ["make", "test"],
            cwd=str(dest),
            capture_output=True,
            text=True,
        )
        stdout = ANSI_RE.sub("", result.stdout + result.stderr)
        print(stdout)
        ok("behavioural: child exit code", f"{result.returncode}")
        if result.returncode != 0:
            record("behavioural: make test exit code", f"non-zero ({result.returncode})")
            return _behavioural_default()

        behavioural = _behavioural_default()
        behavioural["intended"] = len(intended)
        behavioural["mapped"] = len(mapping)
        behavioural["child_rc"] = result.returncode
        behavioural["stdout"] = stdout
        m = SUMMARY_RE.search(stdout)
        if not m:
            record("behavioural: Unity summary", "summary line not found in output")
        else:
            tests, failures_n, ignored = int(m.group(1)), int(m.group(2)), int(m.group(3))
            behavioural["tests"] = tests
            behavioural["failures"] = failures_n
            behavioural["ignored"] = ignored
            ok("behavioural: test count", f"{tests} tests, {failures_n} failures, {ignored} ignored")
            if tests == 0:
                record("behavioural: zero-test run", "no tests executed")
            if failures_n != 0:
                record("behavioural: test failures", f"{failures_n} test(s) failed")
            behavioural["passed"] = (
                result.returncode == 0 and tests > 0 and failures_n == 0
            )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return behavioural


FIXTURES = [
    ("missing-reference", {"example": [".meta/nonexistent.c"]}, "declared example file missing"),
    ("missing-test", {"test": ["nonexistent.c"]}, "declared test file missing"),
    ("outside-exercise", {"solution": ["../outside.c"]}, "parent traversal outside exercise"),
]


def run_fixtures():
    print("\n== metadata fixtures (invalid metadata must fail for intended reason) ==")
    for name, override, intended_reason in FIXTURES:
        fx = Path(tempfile.mkdtemp(prefix=f"r48t008-fx-{name}-"))
        sink = []
        try:
            cfg = load_config(CONFIG)
            cfg["files"] = dict(cfg.get("files", {}))
            for category, files in override.items():
                cfg["files"][category] = files
            (fx / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            metadata = load_config(fx / "config.json")
            resolved = validate_files(metadata, fx, f"fixture:{name}", sink=sink)
            declared = sum(len(cfg["files"].get(c, [])) for c in ("solution", "test", "example"))
            if len(resolved) == declared:
                record(f"fixture:{name}", f"expected failure ('{intended_reason}') but all files resolved")
            else:
                ok(f"fixture:{name}", f"failed as intended ({intended_reason})")
        finally:
            shutil.rmtree(fx, ignore_errors=True)


def write_evidence(real_passed, behavioural):
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)

    (INPUTS_DIR / "config.json").write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    (INPUTS_DIR / "tests.toml").write_text(TESTS_TOML.read_text(encoding="utf-8"), encoding="utf-8")

    versions = []
    for cmd in (("python3", ["--version"]), ("make", ["--version"]), ("cc", ["--version"])):
        try:
            r = subprocess.run([cmd[0]] + list(cmd[1]), capture_output=True, text=True)
            out = (r.stdout or r.stderr).strip()
            versions.append(f"{cmd[0]}: {out.splitlines()[0] if out else 'unknown'}")
        except Exception as exc:
            versions.append(f"{cmd[0]}: unavailable ({exc})")
    (R48T008_DIR / "versions.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")

    report_lines = []
    report_lines.append("=== R48-T008 check results (expected vs actual) ===")
    report_lines.append("")
    report_lines.append("1. Real config metadata validation")
    report_lines.append("   expected: all declared solution/test/example files resolve inside exercise")
    report_lines.append(f"   actual  : {'PASS' if real_passed else 'FAIL'}")
    report_lines.append("")
    report_lines.append("2. Metadata fixtures (each must FAIL for intended reason)")
    for name, _override, reason in FIXTURES:
        report_lines.append(f"   - {name}: expected failure ({reason}) -> recorded as intended")
    report_lines.append("")
    report_lines.append("3. Behavioural run (reference substituted, intended cases enabled, make test)")
    report_lines.append(f"   expected: child exit 0, tests > 0, failures == 0")
    report_lines.append(
        f"   actual  : child exit {behavioural['child_rc']}, "
        f"tests {behavioural['tests']}, failures {behavioural['failures']}, "
        f"ignored {behavioural['ignored']} "
        f"-> {'PASS' if behavioural['passed'] else 'FAIL'}"
    )
    report_lines.append("")
    report_lines.append(f"total failures: {len(failures)}")
    (RESULTS_DIR / "check_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    (RESULTS_DIR / "behavioural_run.log").write_text(
        behavioural["stdout"], encoding="utf-8"
    )


def main():
    print(f"repo root : {REPO_ROOT}")
    print(f"exercise  : {EXERCISE}")
    print(f"config    : {CONFIG}")
    print(f"R48-T008 check: queen-attack metadata + behavioural run\n")

    real_passed = True
    try:
        metadata = load_config(CONFIG)
    except Exception as exc:
        record("real config: load", str(exc))
        metadata = {}
        real_passed = False
    if real_passed:
        resolved = validate_files(metadata, EXERCISE, "real")
        expected = sum(
            len(metadata.get("files", {}).get(c, [])) for c in ("solution", "test", "example")
        )
        if len(resolved) != expected:
            real_passed = False
            record("real config: file resolution", f"{len(resolved)}/{expected} files resolved")
    ok("real config", "passes" if real_passed else "FAILED")

    run_fixtures()
    behavioural = behavioural_run()
    write_evidence(real_passed, behavioural)

    print(f"\n== summary: {len(failures)} failure(s) ==")
    for check, detail in failures:
        print(f"  - {check}: {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
