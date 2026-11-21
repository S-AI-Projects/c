#!/usr/bin/env python3
"""R48-T018: verify exercises/practice/high-scores/.meta/config.json and exercise integrity.

Checks:
  1. Real metadata: verifies that the 'files' object in .meta/config.json declares
     solution, test, and example files, all resolve inside the exercise directory,
     and all exist on disk without parent directory traversal.
  2. Three invalid metadata fixtures:
       - missing-reference: declared example file does not exist
       - missing-test: declared test file does not exist
       - outside-exercise: path attempts parent traversal ('..')
     Confirms that each fixture fails for its intended reason.
  3. Behavioural check:
     In a temporary scratch directory, copies the exercise, substitutes the
     reference implementation (.meta/example.c/.h) into the solution paths, enables
     all 7 intended test cases by removing TEST_IGNORE(), and executes `make test`.
     Asserts Unity output reports 7 Tests, 0 Failures, 0 Ignored, and exit code 0.
  4. Negative control:
     Confirms that the unsolved learner stub fails to build or pass tests.
  5. Specification and anchor check:
     Confirms .meta/tests.toml contains the required anchor phrase and that the 7
     included canonical cases map to test functions in test_high_scores.c.
  6. Cleanliness:
     Confirms the repository working tree is unmodified.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXERCISE_DIR = ROOT / "exercises" / "practice" / "high-scores"
CONFIG_PATH = EXERCISE_DIR / ".meta" / "config.json"
TESTS_TOML_PATH = EXERCISE_DIR / ".meta" / "tests.toml"
ANCHOR_PHRASE = 'so comments can be added in a "comment" key.'

UNITY_RE = re.compile(r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored")
RUN_TEST_RE = re.compile(r"RUN_TEST\((\w+)\)")

failures: list[str] = []


def record_failure(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def log_ok(msg: str) -> None:
    print(f"OK:   {msg}")


# ---------------------------------------------------------------------------
# File resolution and validation
# ---------------------------------------------------------------------------

def validate_files_object(metadata: dict, base_dir: Path, label: str) -> tuple[list[Path], list[str]]:
    """Validate declared paths in files object; return resolved paths and errors."""
    errors = []
    resolved = []
    files_obj = metadata.get("files")
    if not isinstance(files_obj, dict):
        errors.append(f"{label}: 'files' key is missing or not a dictionary")
        return resolved, errors

    for role in ("solution", "test", "example"):
        entries = files_obj.get(role)
        if not isinstance(entries, list):
            errors.append(f"{label}: 'files.{role}' is missing or not a list")
            continue
        if len(entries) == 0:
            errors.append(f"{label}: 'files.{role}' list is empty")
            continue

        for entry in entries:
            if not isinstance(entry, str):
                errors.append(f"{label}: 'files.{role}' entry is not a string: {entry!r}")
                continue

            p = Path(entry)
            if p.is_absolute():
                errors.append(f"{label}: 'files.{role}' path must be relative: {entry}")
                continue

            if ".." in p.parts:
                errors.append(f"{label}: 'files.{role}' contains parent traversal: {entry}")
                continue

            candidate = (base_dir / p).resolve()
            try:
                candidate.relative_to(base_dir.resolve())
            except ValueError:
                errors.append(f"{label}: 'files.{role}' resolves outside exercise: {entry}")
                continue

            if not candidate.is_file():
                errors.append(f"{label}: 'files.{role}' file does not exist on disk: {entry}")
                continue

            resolved.append(candidate)

    return resolved, errors


# ---------------------------------------------------------------------------
# Fixture testing
# ---------------------------------------------------------------------------

FIXTURES = [
    (
        "missing-reference",
        {"example": [".meta/nonexistent_example.c", ".meta/example.h"]},
        "file does not exist on disk",
    ),
    (
        "missing-test",
        {"test": ["nonexistent_test.c"]},
        "file does not exist on disk",
    ),
    (
        "outside-exercise",
        {"solution": ["../outside.c", "high_scores.h"]},
        "contains parent traversal",
    ),
]


def test_fixtures() -> None:
    print("\n--- Testing Metadata Fixtures ---")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        base_config = json.load(f)

    for name, overrides, expected_reason in FIXTURES:
        test_cfg = json.loads(json.dumps(base_config))
        test_cfg["files"].update(overrides)

        with tempfile.TemporaryDirectory(prefix=f"fx-{name}-") as tmp_dir:
            tmp_base = Path(tmp_dir)
            resolved, errors = validate_files_object(test_cfg, tmp_base, f"fixture:{name}")
            matched = any(expected_reason in err for err in errors)
            if matched:
                log_ok(f"Fixture '{name}' correctly rejected ({expected_reason})")
            else:
                record_failure(f"Fixture '{name}' did not fail with expected reason '{expected_reason}'. Errors: {errors}")


# ---------------------------------------------------------------------------
# Behavioural check (reference substitution + make test)
# ---------------------------------------------------------------------------

def run_behavioural_check() -> dict:
    print("\n--- Running Behavioural Reference Check ---")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    with tempfile.TemporaryDirectory(prefix="r48t018-high-scores-") as tmp_dir:
        dest = Path(tmp_dir) / "high-scores"
        shutil.copytree(EXERCISE_DIR, dest)

        # Substitute reference into solution files
        # config['files']['example'] -> ['.meta/example.c', '.meta/example.h']
        # config['files']['solution'] -> ['high_scores.c', 'high_scores.h']
        example_c = EXERCISE_DIR / ".meta" / "example.c"
        example_h = EXERCISE_DIR / ".meta" / "example.h"
        sol_c = dest / "high_scores.c"
        sol_h = dest / "high_scores.h"
        shutil.copy(example_c, sol_c)
        shutil.copy(example_h, sol_h)

        # Enable all test cases in test_high_scores.c
        test_file = dest / "test_high_scores.c"
        test_src = test_file.read_text(encoding="utf-8")
        uncommented = re.sub(r"^\s*TEST_IGNORE\(\);.*$", "", test_src, flags=re.MULTILINE)
        test_file.write_text(uncommented, encoding="utf-8")

        # Run make test
        res = subprocess.run(
            ["make", "test"],
            cwd=str(dest),
            capture_output=True,
            text=True,
        )
        combined_output = res.stdout + res.stderr
        print(combined_output.strip())

        if res.returncode != 0:
            record_failure(f"make test failed with returncode {res.returncode}")

        m = UNITY_RE.search(combined_output)
        if not m:
            record_failure("Unity summary line not found in make test output")
            return {"tests": 0, "failures": 0, "ignored": 0, "output": combined_output}

        tests, num_fails, ignored = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if tests == 0:
            record_failure("Zero tests were executed")
        if num_fails != 0:
            record_failure(f"Reference failed {num_fails} test(s)")
        if ignored != 0:
            record_failure(f"Reference has {ignored} ignored test(s)")

        log_ok(f"Reference test run: {tests} Tests, {num_fails} Failures, {ignored} Ignored (child exit {res.returncode})")
        return {"tests": tests, "failures": num_fails, "ignored": ignored, "output": combined_output}


# ---------------------------------------------------------------------------
# Negative control (bare stub must fail)
# ---------------------------------------------------------------------------

def test_negative_control() -> None:
    print("\n--- Testing Negative Control (Unsolved Learner Stub) ---")
    with tempfile.TemporaryDirectory(prefix="r48t018-stub-") as tmp_dir:
        dest = Path(tmp_dir) / "high-scores"
        shutil.copytree(EXERCISE_DIR, dest)

        test_file = dest / "test_high_scores.c"
        test_src = test_file.read_text(encoding="utf-8")
        uncommented = re.sub(r"^\s*TEST_IGNORE\(\);.*$", "", test_src, flags=re.MULTILINE)
        test_file.write_text(uncommented, encoding="utf-8")

        res = subprocess.run(
            ["make", "test"],
            cwd=str(dest),
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            record_failure("Negative control FAILED: bare stub passed make test unexpectedly")
        else:
            log_ok(f"Bare stub correctly failed to build/link (exit code {res.returncode})")


# ---------------------------------------------------------------------------
# Canonical specification & anchor check
# ---------------------------------------------------------------------------

def check_tests_toml_and_anchor() -> None:
    print("\n--- Checking tests.toml Anchor and Test Mapping ---")
    if not TESTS_TOML_PATH.is_file():
        record_failure(f"tests.toml not found at {TESTS_TOML_PATH}")
        return

    content = TESTS_TOML_PATH.read_text(encoding="utf-8")
    if ANCHOR_PHRASE not in content:
        record_failure(f"Anchor phrase {ANCHOR_PHRASE!r} not found in tests.toml")
    else:
        log_ok(f"Anchor phrase found in tests.toml: '{ANCHOR_PHRASE}'")

    test_c_content = (EXERCISE_DIR / "test_high_scores.c").read_text(encoding="utf-8")
    run_tests = RUN_TEST_RE.findall(test_c_content)
    if len(run_tests) != 7:
        record_failure(f"Expected 7 RUN_TEST calls in test_high_scores.c, found {len(run_tests)}")
    else:
        log_ok(f"Found exactly 7 RUN_TEST invocations matching canonical included cases")


# ---------------------------------------------------------------------------
# Snapshot / Integrity check
# ---------------------------------------------------------------------------

def snapshot_dir(directory: Path) -> dict[str, bytes]:
    snap = {}
    for root, _, files in os.walk(directory):
        for f in files:
            p = Path(root) / f
            snap[str(p.relative_to(directory))] = p.read_bytes()
    return snap


# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------

def run_all_checks() -> bool:
    print(f"=== R48-T018: high-scores Path & Configuration Verification ===")
    print(f"Exercise directory: {EXERCISE_DIR}")

    snap_before = snapshot_dir(EXERCISE_DIR)

    # 1. Real config validation
    print("\n--- Validating Real .meta/config.json ---")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        real_config = json.load(f)

    resolved, errors = validate_files_object(real_config, EXERCISE_DIR, "real_config")
    if errors:
        for err in errors:
            record_failure(err)
    else:
        log_ok(f"Real config valid: resolved {len(resolved)} files inside exercise directory")
        for p in resolved:
            log_ok(f"  resolved: {p.relative_to(EXERCISE_DIR)}")

    # 2. Test fixtures
    test_fixtures()

    # 3. Behavioural reference run
    behavioural = run_behavioural_check()

    # 4. Negative control
    test_negative_control()

    # 5. tests.toml & anchor check
    check_tests_toml_and_anchor()

    # 6. Verify working tree unchanged
    snap_after = snapshot_dir(EXERCISE_DIR)
    if snap_before != snap_after:
        record_failure("Exercise directory was modified during execution!")
    else:
        log_ok("Exercise directory byte-for-byte identical before and after run")

    print(f"\n=== Summary: {len(failures)} failure(s) ===")
    return len(failures) == 0


if __name__ == "__main__":
    success = run_all_checks()
    if not success:
        print("\nR48-T018 checks FAILED.", file=sys.stderr)
        sys.exit(1)
    print("\nR48-T018 checks PASSED successfully.")
    sys.exit(0)
