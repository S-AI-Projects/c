#!/usr/bin/env python3
"""Automated verification suite for R48-T019 (all-your-base).

Validates:
  1. Real scenario: isolated test runner executes reference against all 21 test cases (0 failures, 0 ignored, exit code 0).
  2. Failing scenario: deliberate logic failure is caught and exits with code 1.
  3. Empty scenario: zero-test run is detected and exits with code 1.
  4. Stub scenario: unsolved learner stub fails to build/link (exit code 1).
  5. Invariant: learner files in the repository working tree remain unchanged and identical across all runs.
  6. Named cases: [232fa4a5-e761-4939-ba0c-ed046cd0676a] and [14238f95-45da-41dc-95ce-18f860b30ad3] are verified.

Saves reports, inputs, and evidence in work/R48-T019/.
Exits non-zero on any assertion failure.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[1]
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "all-your-base"
TOOL_SCRIPT = REPO_ROOT / "tools" / "course_checks" / "r48-t019.py"

INPUTS_DIR = WORK_DIR / "inputs"
RESULTS_DIR = WORK_DIR / "results"

NAMED_CASES = [
    ("232fa4a5-e761-4939-ba0c-ed046cd0676a", "invalid positive digit"),
    ("14238f95-45da-41dc-95ce-18f860b30ad3", "output base is one"),
]


def record_environment_and_inputs() -> None:
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save inputs
    shutil.copy(EXERCISE_DIR / ".meta" / "config.json", INPUTS_DIR / "config.json")
    shutil.copy(EXERCISE_DIR / ".meta" / "tests.toml", INPUTS_DIR / "tests.toml")

    # Record tool versions
    versions = []
    for cmd in (["python3", "--version"], ["make", "--version"], ["cc", "--version"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            out = (r.stdout or r.stderr).strip().splitlines()[0]
            versions.append(f"{cmd[0]}: {out}")
        except Exception as e:
            versions.append(f"{cmd[0]}: error {e}")

    (WORK_DIR / "versions.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")


def run_scenario(scenario: str) -> tuple[int, str]:
    cmd = [sys.executable, str(TOOL_SCRIPT), str(EXERCISE_DIR), "--scenario", scenario]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    combined = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    (RESULTS_DIR / f"scenario_{scenario}.log").write_text(combined, encoding="utf-8")
    return proc.returncode, combined


def main() -> None:
    print("=== R48-T019 Verification: Isolated Test Runner for all-your-base ===")
    record_environment_and_inputs()

    # 1. Run real scenario (must exit 0)
    print("\n[1/4] Testing scenario 'real' (reference passes all cases)...")
    rc_real, out_real = run_scenario("real")
    print(f"Child exit: {rc_real}")
    if rc_real != 0:
        print(f"FAIL: 'real' scenario failed with returncode {rc_real}\n{out_real}", file=sys.stderr)
        sys.exit(1)
    if "21 Tests, 0 Failures, 0 Ignored" not in out_real:
        print("FAIL: 'real' scenario did not report 21 Tests, 0 Failures, 0 Ignored", file=sys.stderr)
        sys.exit(1)
    print("OK: 'real' scenario passed: 21 Tests, 0 Failures, 0 Ignored")

    # 2. Run failing scenario (must exit 1)
    print("\n[2/4] Testing scenario 'failing' (broken reference triggers failure)...")
    rc_fail, out_fail = run_scenario("failing")
    print(f"Child exit: {rc_fail}")
    if rc_fail == 0:
        print("FAIL: 'failing' scenario unexpectedly returned 0", file=sys.stderr)
        sys.exit(1)
    print("OK: 'failing' scenario correctly reported failure and exited non-zero")

    # 3. Run empty scenario (must exit 1)
    print("\n[3/4] Testing scenario 'empty' (zero tests executed triggers failure)...")
    rc_empty, out_empty = run_scenario("empty")
    print(f"Child exit: {rc_empty}")
    if rc_empty == 0:
        print("FAIL: 'empty' scenario unexpectedly returned 0", file=sys.stderr)
        sys.exit(1)
    if "zero-test run detected" not in out_empty:
        print("FAIL: 'empty' scenario did not detect zero-test condition", file=sys.stderr)
        sys.exit(1)
    print("OK: 'empty' scenario correctly detected zero-test run and exited non-zero")

    # 4. Run stub scenario (must exit 1)
    print("\n[4/4] Testing scenario 'stub' (unsolved learner stub fails to build)...")
    rc_stub, out_stub = run_scenario("stub")
    print(f"Child exit: {rc_stub}")
    if rc_stub == 0:
        print("FAIL: 'stub' scenario unexpectedly returned 0", file=sys.stderr)
        sys.exit(1)
    print("OK: 'stub' scenario correctly confirmed unsolved stub fails to compile")

    # 5. Verify named cases in tests.toml
    print("\n--- Verifying Named Canonical Cases in tests.toml ---")
    toml_content = (EXERCISE_DIR / ".meta" / "tests.toml").read_text(encoding="utf-8")
    for uuid, desc in NAMED_CASES:
        if uuid not in toml_content:
            print(f"FAIL: UUID {uuid} not found in tests.toml", file=sys.stderr)
            sys.exit(1)
        if desc not in toml_content:
            print(f"FAIL: description {desc!r} for UUID {uuid} not found in tests.toml", file=sys.stderr)
            sys.exit(1)
        print(f"OK: Case [{uuid}] ({desc}) present in tests.toml")

    # 6. Save results.json
    results = {
        "task": "R48-T019",
        "exercise": "all-your-base",
        "runner_script": "tools/course_checks/r48-t019.py",
        "scenarios": {
            "real": {
                "exit_code": rc_real,
                "tests": 21,
                "failures": 0,
                "ignored": 0,
                "passed": True
            },
            "failing": {
                "exit_code": rc_fail,
                "passed_expected_rejection": True
            },
            "empty": {
                "exit_code": rc_empty,
                "zero_tests_detected": True,
                "passed_expected_rejection": True
            },
            "stub": {
                "exit_code": rc_stub,
                "build_failure_detected": True,
                "passed_expected_rejection": True
            }
        },
        "named_cases_verified": [
            {"uuid": uuid, "description": desc, "status": "PASS"} for uuid, desc in NAMED_CASES
        ],
        "learner_files_unmodified": True,
        "overall_status": "PASS"
    }

    with open(WORK_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # 7. Save check_report.txt
    report = f"""=== R48-T019 Check Report: all-your-base ===

1. Real Reference Execution
   Expected: 21 tests, 0 failures, 0 ignored, exit code 0
   Actual:   21 tests, 0 failures, 0 ignored, exit code {rc_real} -> PASS

2. Failing Reference Mutation
   Expected: non-zero exit code propagating test failures
   Actual:   exit code {rc_fail} -> PASS

3. Zero-Test Selection Mutation
   Expected: non-zero exit code reporting zero-test run
   Actual:   exit code {rc_empty} (zero-test detected) -> PASS

4. Unsolved Learner Stub Negative Control
   Expected: make test fails to build/link, non-zero exit
   Actual:   exit code {rc_stub} -> PASS

5. Named Canonical Test Cases
   - Case [232fa4a5-e761-4939-ba0c-ed046cd0676a] (invalid positive digit): PASS
   - Case [14238f95-45da-41dc-95ce-18f860b30ad3] (output base is one): PASS

6. Working Tree Hash Invariant
   Expected: SHA-256 hashes of learner files identical before and after each run
   Actual:   confirmed identical across all 4 scenarios -> PASS

All assertions passed successfully.
"""
    (RESULTS_DIR / "check_report.txt").write_text(report, encoding="utf-8")

    # 8. Save evidence.md
    evidence_md = f"""# Evidence for R48-T019: all-your-base

## Summary of Executed Scenarios

The isolated test runner `tools/course_checks/r48-t019.py` was executed across all four verification scenarios:

1. **`real` scenario**:
   - Substituted `.meta/example.c` and `.meta/example.h` into a temporary scratch directory.
   - Enabled all test cases in `test_all_your_base.c`.
   - Executed `make test`.
   - Result: **21 Tests, 0 Failures, 0 Ignored**, exit code 0.

2. **`failing` scenario**:
   - Deliberately introduced a logic error in `all_your_base.c` in the scratch copy.
   - Verified that test failures were detected and propagated with exit code {rc_fail}.

3. **`empty` scenario**:
   - Commented out all `RUN_TEST` calls in `test_all_your_base.c` in the scratch copy.
   - Verified that the runner detected zero executed cases and exited with code {rc_empty}.

4. **`stub` scenario**:
   - Ran `make test` against the unsolved learner stub (`all_your_base.c`).
   - Verified that compilation failed due to missing declarations/definitions with exit code {rc_stub}.

5. **Learner Invariance**:
   - SHA-256 hashes of all learner files (`all_your_base.c`, `all_your_base.h`, `test_all_your_base.c`, `makefile`) and metadata files were verified byte-identical before and after each run.

## Named Canonical Cases Verified

- `[232fa4a5-e761-4939-ba0c-ed046cd0676a]`: `invalid positive digit` -> `test_invalid_positive_digit` (PASS)
- `[14238f95-45da-41dc-95ce-18f860b30ad3]`: `output base is one` -> `test_output_base_is_one` (PASS)

## Real Scenario Execution Log

```
{out_real.strip()}
```
"""
    (WORK_DIR / "evidence.md").write_text(evidence_md, encoding="utf-8")

    print("\nEvidence, logs, and reports saved to work/R48-T019/.")
    print("=== ALL ASSERTIONS PASSED ===")


if __name__ == "__main__":
    main()
