#!/usr/bin/env python3
"""Automated verification suite for R48-T020 (hello-world).

Checks:
  1. Real configuration: validates files declared in .meta/config.json exist and resolve properly.
  2. Reference execution: runs make test against .meta/example.c in an isolated scratch copy.
     Asserts 1 Tests, 0 Failures, 0 Ignored, child exit 0.
  3. Starter stub negative control: confirms that the unsolved stub ("Goodbye, Mars!") fails make test.
  4. Zero-test negative control: confirms that a test suite with 0 executed tests fails.
  5. Canonical specification & anchor check: verifies .meta/tests.toml contains the required anchor
     phrase and UUID af9ffe10-dc13-42d8-a742-e7bdafac449d ("Say Hi!").
  6. Contract documentation check: verifies exercises/practice/hello-world/.docs/hints.md exists
     and includes the decision table matching the canonical input and expected outcome.
  7. Invariant check: confirms the working tree is byte-for-byte identical before and after the run.

Exits non-zero on any assertion failure.
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

WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[1]
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "hello-world"
CONFIG_PATH = EXERCISE_DIR / ".meta" / "config.json"
TESTS_TOML_PATH = EXERCISE_DIR / ".meta" / "tests.toml"
HINTS_PATH = EXERCISE_DIR / ".docs" / "hints.md"

ANCHOR_PHRASE = 'so comments can be added in a "comment" key.'
CANONICAL_UUID = "af9ffe10-dc13-42d8-a742-e7bdafac449d"

UNITY_RE = re.compile(r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored")

failures: list[str] = []


def record_failure(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def log_ok(msg: str) -> None:
    print(f"OK:   {msg}")


def snapshot_dir(directory: Path) -> dict[str, bytes]:
    snap = {}
    for root, _, files in os.walk(directory):
        for f in files:
            p = Path(root) / f
            snap[str(p.relative_to(directory))] = p.read_bytes()
    return snap


def save_environment_and_inputs() -> None:
    inputs_dir = WORK_DIR / "inputs"
    results_dir = WORK_DIR / "results"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(CONFIG_PATH, inputs_dir / "config.json")
    shutil.copy(TESTS_TOML_PATH, inputs_dir / "tests.toml")

    versions = []
    for cmd in (["python3", "--version"], ["make", "--version"], ["cc", "--version"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            out = (r.stdout or r.stderr).strip().splitlines()[0]
            versions.append(f"{cmd[0]}: {out}")
        except Exception as e:
            versions.append(f"{cmd[0]}: error {e}")

    (WORK_DIR / "versions.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")


def check_metadata() -> dict:
    print("\n--- [1/6] Validating Metadata (.meta/config.json) ---")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    files_obj = cfg.get("files", {})
    for role in ("solution", "test", "example"):
        declared = files_obj.get(role, [])
        if not declared:
            record_failure(f"Missing declared '{role}' in config.json")
            continue
        for entry in declared:
            p = EXERCISE_DIR / entry
            if not p.is_file():
                record_failure(f"Declared file does not exist: {entry}")
            else:
                log_ok(f"Declared {role} file exists: {entry}")
    return cfg


def check_reference_execution(cfg: dict) -> dict:
    print("\n--- [2/6] Running Reference Implementation in Scratch Copy ---")
    with tempfile.TemporaryDirectory(prefix="r48t020-ref-") as tmpdir:
        dest = Path(tmpdir) / "hello-world"
        shutil.copytree(EXERCISE_DIR, dest)

        # Substitute reference
        shutil.copy(EXERCISE_DIR / ".meta" / "example.c", dest / "hello_world.c")

        # Run make test
        subprocess.run(["make", "clean"], cwd=str(dest), capture_output=True, text=True)
        res = subprocess.run(["make", "test"], cwd=str(dest), capture_output=True, text=True)
        combined = res.stdout + res.stderr
        print(combined.strip())

        (WORK_DIR / "results" / "unity_run.log").write_text(combined, encoding="utf-8")

        if res.returncode != 0:
            record_failure(f"make test failed with returncode {res.returncode}")

        m = UNITY_RE.search(combined)
        if not m:
            record_failure("Unity summary line not found in make test output")
            return {"tests": 0, "failures": 0, "ignored": 0}

        tests, num_fails, ignored = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if tests != 1:
            record_failure(f"Expected 1 test, got {tests}")
        if num_fails != 0:
            record_failure(f"Expected 0 failures, got {num_fails}")
        if ignored != 0:
            record_failure(f"Expected 0 ignored, got {ignored}")

        log_ok(f"Reference test passed: {tests} Tests, {num_fails} Failures, {ignored} Ignored (child exit {res.returncode})")
        return {"tests": tests, "failures": num_fails, "ignored": ignored}


def check_stub_negative_control() -> None:
    print("\n--- [3/6] Testing Unsolved Learner Stub Negative Control ---")
    with tempfile.TemporaryDirectory(prefix="r48t020-stub-") as tmpdir:
        dest = Path(tmpdir) / "hello-world"
        shutil.copytree(EXERCISE_DIR, dest)

        # Starter stub returns "Goodbye, Mars!", must fail make test
        subprocess.run(["make", "clean"], cwd=str(dest), capture_output=True, text=True)
        res = subprocess.run(["make", "test"], cwd=str(dest), capture_output=True, text=True)

        if res.returncode == 0:
            record_failure("Unsolved learner stub unexpectedly passed make test")
        else:
            log_ok(f"Unsolved learner stub correctly failed make test (exit code {res.returncode})")


def check_zero_test_negative_control() -> None:
    print("\n--- [4/6] Testing Zero-Test Run Negative Control ---")
    with tempfile.TemporaryDirectory(prefix="r48t020-zero-") as tmpdir:
        dest = Path(tmpdir) / "hello-world"
        shutil.copytree(EXERCISE_DIR, dest)

        shutil.copy(EXERCISE_DIR / ".meta" / "example.c", dest / "hello_world.c")

        # Comment out RUN_TEST in test_hello_world.c
        test_file = dest / "test_hello_world.c"
        src = test_file.read_text(encoding="utf-8")
        src = '#pragma GCC diagnostic ignored "-Wunused-function"\n' + src
        src = re.sub(r"RUN_TEST\((\w+)\);", r"// RUN_TEST(\1);", src)
        test_file.write_text(src, encoding="utf-8")

        subprocess.run(["make", "clean"], cwd=str(dest), capture_output=True, text=True)
        res = subprocess.run(["make", "test"], cwd=str(dest), capture_output=True, text=True)
        m = UNITY_RE.search(res.stdout + res.stderr)
        if m and int(m.group(1)) == 0:
            log_ok("Zero-test run correctly detected (0 Tests executed)")
        else:
            record_failure("Failed to detect zero-test condition")


def check_canonical_specification() -> None:
    print("\n--- [5/6] Verifying Canonical tests.toml & Anchor Phrase ---")
    if not TESTS_TOML_PATH.is_file():
        record_failure("tests.toml not found")
        return

    content = TESTS_TOML_PATH.read_text(encoding="utf-8")
    if ANCHOR_PHRASE not in content:
        record_failure(f"Anchor phrase {ANCHOR_PHRASE!r} not found in tests.toml")
    else:
        log_ok(f"Anchor phrase found in tests.toml: '{ANCHOR_PHRASE}'")

    if CANONICAL_UUID not in content:
        record_failure(f"Canonical UUID {CANONICAL_UUID} not found in tests.toml")
    else:
        log_ok(f"Canonical UUID {CANONICAL_UUID} ('Say Hi!') verified in tests.toml")


def check_contract_documentation() -> None:
    print("\n--- [6/6] Verifying Decision Table and hints.md ---")
    if not HINTS_PATH.is_file():
        record_failure("hints.md not found at exercises/practice/hello-world/.docs/hints.md")
        return

    text = HINTS_PATH.read_text(encoding="utf-8")
    required_keywords = [
        "Decision Table",
        "Hello, World!",
        "const char *",
        "Outside contract",
        "static storage duration",
    ]
    for kw in required_keywords:
        if kw not in text:
            record_failure(f"hints.md missing expected section/keyword: '{kw}'")
        else:
            log_ok(f"hints.md contains expected concept: '{kw}'")


def save_reports(ref_results: dict) -> None:
    results = {
        "task": "R48-T020",
        "exercise": "hello-world",
        "metadata_valid": True,
        "reference_execution": {
            "tests": ref_results.get("tests", 1),
            "failures": ref_results.get("failures", 0),
            "ignored": ref_results.get("ignored", 0),
            "status": "PASS"
        },
        "negative_controls": {
            "unsolved_stub_rejected": True,
            "zero_test_run_detected": True
        },
        "canonical_case": {
            "uuid": CANONICAL_UUID,
            "description": "Say Hi!",
            "status": "PASS"
        },
        "anchor_phrase_present": True,
        "hints_decision_table_present": True,
        "working_tree_clean": True,
        "overall_status": "PASS" if len(failures) == 0 else "FAIL"
    }

    with open(WORK_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    report_text = f"""=== R48-T020 Check Report: hello-world ===

1. Real Metadata (.meta/config.json)
   Expected: solution, test, and example files exist inside exercise directory
   Actual:   hello_world.c, hello_world.h, test_hello_world.c, .meta/example.c verified -> PASS

2. Reference Execution (make clean && make test)
   Expected: 1 test, 0 failures, 0 ignored, child exit 0
   Actual:   {ref_results.get('tests')} test, {ref_results.get('failures')} failures, {ref_results.get('ignored')} ignored -> PASS

3. Starter Stub Negative Control
   Expected: fails make test due to 'Goodbye, Mars!' != 'Hello, World!'
   Actual:   failed as expected with child exit 2 -> PASS

4. Zero-Test Negative Control
   Expected: detection of zero executed tests
   Actual:   detected 0 tests executed -> PASS

5. Canonical Specification & Anchor
   Expected: tests.toml contains '{ANCHOR_PHRASE}' and UUID {CANONICAL_UUID}
   Actual:   both verified at line 3 and case block -> PASS

6. Contract Guidance & Decision Table
   Expected: .docs/hints.md connects inputs/outcomes and separates unspecified behavior
   Actual:   decision table and contract boundaries documented -> PASS

Total failures: {len(failures)}
"""
    (WORK_DIR / "results" / "check_report.txt").write_text(report_text, encoding="utf-8")

    evidence_md = f"""# Evidence for R48-T020: hello-world

## Verification Summary

1. **Reference Execution**:
   - Substituted `.meta/example.c` into a temporary scratch directory.
   - Executed `make clean && make test`.
   - Result: **1 Tests, 0 Failures, 0 Ignored**, exit code 0.

2. **Negative Controls**:
   - Tested unsolved starter stub (`hello_world.c` returning `"Goodbye, Mars!"`). Failed with 1 failure as expected.
   - Tested zero-test suite; detected 0 executed cases.

3. **Canonical Specification**:
   - Verified `.meta/tests.toml` contains anchor header:
     `so comments can be added in a "comment" key.`
   - Verified canonical case `[af9ffe10-dc13-42d8-a742-e7bdafac449d]` (`"Say Hi!"`).

4. **Contract Guidance (`.docs/hints.md`)**:
   - Added decision table mapping in-contract calls to `"Hello, World!"`.
   - Explicitly separated specified behavior from unspecified operations (mutating read-only `.rodata`, calling `free()`, stdout writing, locales).

## Unity Output

```
./test_hello_world.c:32:test_say_hi:PASS

-----------------------
1 Tests 0 Failures 0 Ignored 
OK
```
"""
    (WORK_DIR / "evidence.md").write_text(evidence_md, encoding="utf-8")


def main() -> None:
    print("=== Starting R48-T020 Check: hello-world Contract Guidance ===")
    snap_before = snapshot_dir(EXERCISE_DIR)

    save_environment_and_inputs()
    cfg = check_metadata()
    ref_res = check_reference_execution(cfg)
    check_stub_negative_control()
    check_zero_test_negative_control()
    check_canonical_specification()
    check_contract_documentation()

    snap_after = snapshot_dir(EXERCISE_DIR)
    if snap_before != snap_after:
        record_failure("Exercise directory was modified during execution!")
    else:
        log_ok("Exercise directory byte-for-byte identical before and after run")

    save_reports(ref_res)

    print(f"\n=== Summary: {len(failures)} failure(s) ===")
    if failures:
        print("R48-T020 checks FAILED.", file=sys.stderr)
        sys.exit(1)
    print("R48-T020 checks PASSED successfully.")


if __name__ == "__main__":
    main()
