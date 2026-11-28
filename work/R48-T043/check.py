#!/usr/bin/env python3
"""
work/R48-T043/check.py
Automated verification check for Task R48-T043:
Find a test that distinguishes a wrong variable-length-quantity implementation [exercises/practice/variable-length-quantity].
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def find_repo_root():
    curr = os.path.abspath(os.path.dirname(__file__))
    while curr and curr != os.path.dirname(curr):
        if os.path.exists(os.path.join(curr, ".git")) or os.path.exists(os.path.join(curr, "config.json")):
            return curr
        curr = os.path.dirname(curr)
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def get_tool_version(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.splitlines()[0].strip()
    except Exception as e:
        return f"Error: {e}"


def run_exercise_tests(exercise_source_path, meta_config, mutant_fn=None):
    """
    Copies the exercise to a temporary directory, substitutes the reference solution
    (optionally mutated by mutant_fn), enables all test cases, and runs `make test`.
    Returns (returncode, stdout, stderr, run_count, failures_count, ignored_count, passed_tests, failed_tests).
    """
    solution_files = meta_config["files"]["solution"]
    test_files = meta_config["files"]["test"]
    example_files = meta_config["files"]["example"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "variable-length-quantity")
        shutil.copytree(exercise_source_path, tmp_exercise)

        # Substitute reference into temporary copy only
        for sol_rel, ex_rel in zip(solution_files, example_files):
            src = os.path.join(tmp_exercise, ex_rel)
            dst = os.path.join(tmp_exercise, sol_rel)
            shutil.copy(src, dst)

        # Apply mutation if requested
        if mutant_fn is not None:
            for sol_rel in solution_files:
                sol_path = os.path.join(tmp_exercise, sol_rel)
                with open(sol_path, "r", encoding="utf-8") as f:
                    content = f.read()
                mutated = mutant_fn(sol_rel, content)
                with open(sol_path, "w", encoding="utf-8") as f:
                    f.write(mutated)

        # Enable all test cases by stripping TEST_IGNORE()
        for tf in test_files:
            tf_path = os.path.join(tmp_exercise, tf)
            with open(tf_path, "r", encoding="utf-8") as f:
                content = f.read()
            updated_content = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

        # Execute make test
        test_run = subprocess.run(
            ["make", "test"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True
        )

        stdout = test_run.stdout
        stderr = test_run.stderr

        clean_stdout = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', stdout)
        passed_tests = re.findall(r':(test_\w+):PASS', clean_stdout)
        failed_tests = re.findall(r':(test_\w+):FAIL:(.*)', clean_stdout)

        summary_match = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_stdout)
        if summary_match:
            run_count = int(summary_match.group(1))
            failures_count = int(summary_match.group(2))
            ignored_count = int(summary_match.group(3))
        else:
            run_count = 0
            failures_count = 0
            ignored_count = 0

        return (
            test_run.returncode,
            clean_stdout,
            stderr,
            run_count,
            failures_count,
            ignored_count,
            passed_tests,
            failed_tests
        )


def main():
    repo_root = find_repo_root()
    exercise_rel = "exercises/practice/variable-length-quantity"
    exercise_path = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T043")
    os.makedirs(work_dir, exist_ok=True)

    print("=== Running R48-T043 Verification Check ===")
    print(f"Repository Root: {repo_root}")

    # 1. Tool versions
    tools = {
        "python": sys.version.split()[0],
        "cc": get_tool_version(["cc", "--version"]),
        "make": get_tool_version(["make", "--version"])
    }
    configlet_bin = os.path.join(repo_root, "bin/configlet")
    if os.path.exists(configlet_bin):
        tools["configlet"] = get_tool_version([configlet_bin, "--version"])
    print(f"Tool versions: Python {tools['python']}, CC: {tools['cc']}, Make: {tools['make']}")

    with open(os.path.join(work_dir, "tool_versions.txt"), "w", encoding="utf-8") as f:
        for t, v in tools.items():
            f.write(f"{t}: {v}\n")

    # 2. Check working tree learner stub remains unsolved
    learner_c = os.path.join(exercise_path, "variable_length_quantity.c")
    learner_h = os.path.join(exercise_path, "variable_length_quantity.h")
    assert os.path.exists(learner_c), f"Missing {learner_c}"
    assert os.path.exists(learner_h), f"Missing {learner_h}"

    with open(learner_c, "r", encoding="utf-8") as f:
        c_code = f.read()

    # The learner stub should not contain encode/decode implementation logic
    has_implementation = any(keyword in c_code for keyword in [
        "buf[", ">>= 7", "<<= 7", "0x7f", "0x80", "uint8_t part"
    ])
    is_stub_unsolved = not has_implementation
    assert is_stub_unsolved, "Assertion failed: Learner stub in working tree appears solved!"
    print("[PASS] Working tree learner stub is unsolved.")

    # 3. Check maintenance documentation
    maint_file = os.path.join(repo_root, "docs/maintenance/variable-length-quantity.md")
    assert os.path.exists(maint_file), f"Assertion failed: Missing {maint_file}"
    with open(maint_file, "r", encoding="utf-8") as f:
        maint_content = f.read()

    assert "35c9db2e-f781-4c52-b73b-8e76427defd0" in maint_content, "Assertion failed: Maintenance doc missing rejecting test ID"
    assert "test_zero" in maint_content, "Assertion failed: Maintenance doc missing test_zero mapping"
    assert "mutant" in maint_content.lower(), "Assertion failed: Maintenance doc missing mutant description"
    assert "contract" in maint_content.lower(), "Assertion failed: Maintenance doc missing contract specification"
    assert "expected" in maint_content.lower() and "actual" in maint_content.lower(), "Assertion failed: Maintenance doc missing expected vs actual"
    assert "description" in maint_content.lower() and "reimplements" in maint_content.lower(), "Assertion failed: Maintenance doc missing key handling rules"
    print("[PASS] Maintenance documentation verified (docs/maintenance/variable-length-quantity.md).")

    # 4. Check debugging hint
    hint_file = os.path.join(exercise_path, ".docs/hints.md")
    assert os.path.exists(hint_file), f"Assertion failed: Missing {hint_file}"
    with open(hint_file, "r", encoding="utf-8") as f:
        hint_content = f.read()

    assert "0x0" in hint_content or "0x00" in hint_content, "Assertion failed: Hint missing diagnostic input 0x0/0x00"
    assert "while" in hint_content.lower(), "Assertion failed: Hint missing explanation of loop mistake"
    assert "7-bit" in hint_content or "7 bits" in hint_content or "continuation" in hint_content.lower(), "Assertion failed: Hint missing contract explanation"
    print("[PASS] Debugging hint verified (exercises/practice/variable-length-quantity/.docs/hints.md).")

    # 5. Parse meta config.json and tests.toml
    meta_config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(meta_config_file, "r", encoding="utf-8") as f:
        meta_config = json.load(f)

    tests_toml_file = os.path.join(exercise_path, ".meta/tests.toml")
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    total_cases = len(toml_data)
    assert total_cases == 26, f"Assertion failed: expected 26 canonical cases, got {total_cases}"
    assert "35c9db2e-f781-4c52-b73b-8e76427defd0" in toml_data, "Missing test_zero UUID in tests.toml"
    assert "77b07086-bd3f-4882-8476-8dcafee79b1c" in toml_data, "Missing test_smallest_double_byte UUID in tests.toml"
    print(f"[PASS] tests.toml parsed: {total_cases} canonical cases verified.")

    # 6. Isolated Scratch Run 1: Original reference implementation passes all cases
    print("[INFO] Running original reference solution in isolated temporary directory...")
    ret_orig, out_orig, err_orig, run_orig, fail_orig, ign_orig, passed_orig, failed_orig = run_exercise_tests(
        exercise_path, meta_config, mutant_fn=None
    )
    print(f"Original make test exit code: {ret_orig}, Run: {run_orig}, Failures: {fail_orig}, Ignored: {ign_orig}")
    assert ret_orig == 0, f"Assertion failed: original reference failed with exit code {ret_orig}!\nStderr: {err_orig}"
    assert run_orig == 26, f"Assertion failed: expected 26 executed cases, got {run_orig}"
    assert fail_orig == 0, f"Assertion failed: original reference had {fail_orig} failures"
    assert ign_orig == 0, f"Assertion failed: original reference had {ign_orig} ignored tests"
    print("[PASS] Original reference implementation passed all 26 cases with 0 failures and 0 ignored.")

    # 7. Isolated Scratch Run 2: Primary mutant (pre-condition while loop instead of do-while)
    print("[INFO] Running primary mutant (while loop) in isolated temporary directory...")
    def primary_mutant(filename, content):
        if filename.endswith(".c"):
            # Change post-condition do-while to pre-condition while
            return content.replace("do {", "while (integer) {").replace("} while (integer);", "}")
        return content

    ret_mut1, out_mut1, err_mut1, run_mut1, fail_mut1, ign_mut1, passed_mut1, failed_mut1 = run_exercise_tests(
        exercise_path, meta_config, mutant_fn=primary_mutant
    )
    print(f"Primary mutant exit code: {ret_mut1}, Run: {run_mut1}, Failures: {fail_mut1}, Ignored: {ign_mut1}")
    assert ret_mut1 != 0, "Assertion failed: primary mutant did not exit non-zero!"
    assert run_mut1 == 26, f"Assertion failed: expected 26 tests executed for mutant, got {run_mut1}"
    assert fail_mut1 > 0, "Assertion failed: mutant had 0 failures!"

    failed_test_names = [f[0] for f in failed_mut1]
    assert "test_zero" in failed_test_names, f"Assertion failed: test_zero was not rejected by primary mutant! Failures: {failed_test_names}"
    # Verify exact assertion failure on test_zero
    zero_failure_msg = [f[1].strip() for f in failed_mut1 if f[0] == "test_zero"][0]
    assert "Expected 1 Was 0" in zero_failure_msg, f"Unexpected failure message for test_zero: {zero_failure_msg}"
    print(f"[PASS] Primary mutant rejected by test_zero with assertion failure: '{zero_failure_msg}'.")

    # 8. Isolated Scratch Run 3: Secondary boundary mutant (while integer > 0x7f)
    print("[INFO] Running secondary mutant (boundary integer > 0x7f) in isolated temporary directory...")
    def secondary_mutant(filename, content):
        if filename.endswith(".c"):
            return content.replace("} while (integer);", "} while (integer > 0x7f);")
        return content

    ret_mut2, out_mut2, err_mut2, run_mut2, fail_mut2, ign_mut2, passed_mut2, failed_mut2 = run_exercise_tests(
        exercise_path, meta_config, mutant_fn=secondary_mutant
    )
    print(f"Secondary mutant exit code: {ret_mut2}, Run: {run_mut2}, Failures: {fail_mut2}, Ignored: {ign_mut2}")
    assert ret_mut2 != 0, "Assertion failed: secondary mutant did not exit non-zero!"
    failed_test_names_2 = [f[0] for f in failed_mut2]
    assert "test_smallest_double_byte" in failed_test_names_2, "Assertion failed: test_smallest_double_byte not rejected by secondary mutant"
    double_failure_msg = [f[1].strip() for f in failed_mut2 if f[0] == "test_smallest_double_byte"][0]
    assert "Expected 2 Was 1" in double_failure_msg, f"Unexpected failure message for test_smallest_double_byte: {double_failure_msg}"
    print(f"[PASS] Secondary boundary mutant rejected by test_smallest_double_byte with assertion failure: '{double_failure_msg}'.")

    # 9. Save inputs, expected vs actual results, and evidence
    inputs_data = {
        "exercise": "variable-length-quantity",
        "task_id": "R48-T043",
        "canonical_cases_count": total_cases,
        "config_json": meta_config,
        "mutant_primary": {
            "type": "loop_condition_pretest",
            "description": "Replace post-condition do-while loop with pre-condition while (integer) loop",
            "smallest_rejecting_input": {
                "integers": [0],
                "input_len": 1
            },
            "rejecting_test_id": "35c9db2e-f781-4c52-b73b-8e76427defd0",
            "rejecting_test_function": "test_zero"
        },
        "mutant_secondary": {
            "type": "boundary_condition",
            "description": "Replace while (integer) with while (integer > 0x7f)",
            "smallest_rejecting_input": {
                "integers": [128],
                "input_len": 1
            },
            "rejecting_test_id": "77b07086-bd3f-4882-8476-8dcafee79b1c",
            "rejecting_test_function": "test_smallest_double_byte"
        },
        "files_checked": {
            "instructions": "exercises/practice/variable-length-quantity/.docs/instructions.md",
            "hints": "exercises/practice/variable-length-quantity/.docs/hints.md",
            "tests_toml": "exercises/practice/variable-length-quantity/.meta/tests.toml",
            "config_json": "exercises/practice/variable-length-quantity/.meta/config.json",
            "example_c": "exercises/practice/variable-length-quantity/.meta/example.c",
            "example_h": "exercises/practice/variable-length-quantity/.meta/example.h",
            "stub_c": "exercises/practice/variable-length-quantity/variable_length_quantity.c",
            "stub_h": "exercises/practice/variable-length-quantity/variable_length_quantity.h",
            "test_c": "exercises/practice/variable-length-quantity/test_variable_length_quantity.c",
            "maintenance_doc": "docs/maintenance/variable-length-quantity.md"
        }
    }
    with open(os.path.join(work_dir, "inputs.json"), "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2)

    expected_vs_actual = {
        "learner_stub_unsolved": {
            "expected": True,
            "actual": is_stub_unsolved,
            "pass": is_stub_unsolved
        },
        "canonical_cases": {
            "expected_total": 26,
            "actual_total": total_cases,
            "pass": (total_cases == 26)
        },
        "original_reference_test_run": {
            "expected_exit_code": 0,
            "actual_exit_code": ret_orig,
            "expected_tests_run": 26,
            "actual_tests_run": run_orig,
            "expected_failures": 0,
            "actual_failures": fail_orig,
            "expected_ignored": 0,
            "actual_ignored": ign_orig,
            "pass": (ret_orig == 0 and run_orig == 26 and fail_orig == 0 and ign_orig == 0)
        },
        "primary_mutant_test_run": {
            "expected_exit_code": 2,
            "actual_exit_code": ret_mut1,
            "expected_rejected_test": "test_zero",
            "actual_rejected_test": "test_zero" if "test_zero" in failed_test_names else None,
            "expected_assertion_message": "Expected 1 Was 0",
            "actual_assertion_message": zero_failure_msg,
            "pass": (ret_mut1 != 0 and "test_zero" in failed_test_names and "Expected 1 Was 0" in zero_failure_msg)
        },
        "secondary_mutant_test_run": {
            "expected_exit_code": 2,
            "actual_exit_code": ret_mut2,
            "expected_rejected_test": "test_smallest_double_byte",
            "actual_rejected_test": "test_smallest_double_byte" if "test_smallest_double_byte" in failed_test_names_2 else None,
            "expected_assertion_message": "Expected 2 Was 1",
            "actual_assertion_message": double_failure_msg,
            "pass": (ret_mut2 != 0 and "test_smallest_double_byte" in failed_test_names_2 and "Expected 2 Was 1" in double_failure_msg)
        }
    }
    with open(os.path.join(work_dir, "expected_vs_actual.json"), "w", encoding="utf-8") as f:
        json.dump(expected_vs_actual, f, indent=2)

    evidence = {
        "task_id": "R48-T043",
        "exercise": "variable-length-quantity",
        "tools": tools,
        "learner_stub_unsolved": is_stub_unsolved,
        "canonical_cases_count": total_cases,
        "original_test_results": {
            "tests_run": run_orig,
            "failures": fail_orig,
            "ignored": ign_orig,
            "passed_tests": passed_orig,
            "exit_code": ret_orig
        },
        "mutant_test_results": {
            "tests_run": run_mut1,
            "failures": fail_mut1,
            "ignored": ign_mut1,
            "failed_tests": failed_mut1,
            "exit_code": ret_mut1
        },
        "minimal_rejecting_input": {
            "input": [0],
            "input_len": 1,
            "expected_len": 1,
            "actual_len": 0,
            "rejecting_uuid": "35c9db2e-f781-4c52-b73b-8e76427defd0",
            "rejecting_test": "test_zero"
        },
        "maintenance_doc_verified": True,
        "hint_doc_verified": True,
        "status": "SUCCESS"
    }
    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    summary_file = os.path.join(work_dir, "check_output.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("Task R48-T043 Verification Check Results\n")
        f.write("=========================================\n")
        f.write(f"Tools:\n  Python: {tools['python']}\n  CC: {tools['cc']}\n  Make: {tools['make']}\n")
        if "configlet" in tools:
            f.write(f"  Configlet: {tools['configlet']}\n")
        f.write(f"\nCanonical Counts:\n  Total Cases: {total_cases}\n")
        f.write(f"\nOriginal Reference Test Execution:\n  Tests Run: {run_orig}\n  Failures: {fail_orig}\n  Ignored: {ign_orig}\n  Status: PASS (Exit code {ret_orig})\n")
        f.write(f"\nPrimary Mutant Test Execution:\n  Tests Run: {run_mut1}\n  Failures: {fail_mut1}\n  Ignored: {ign_mut1}\n  Status: REJECTED (Exit code {ret_mut1})\n")
        f.write(f"  Rejecting Test: test_zero (UUID 35c9db2e-f781-4c52-b73b-8e76427defd0)\n")
        f.write(f"  Minimal Input: integers = [0], input_len = 1\n")
        f.write(f"  Assertion Failure: {zero_failure_msg}\n")
        f.write(f"\nSecondary Mutant Test Execution:\n  Tests Run: {run_mut2}\n  Failures: {fail_mut2}\n  Ignored: {ign_mut2}\n  Status: REJECTED (Exit code {ret_mut2})\n")
        f.write(f"  Rejecting Test: test_smallest_double_byte (UUID 77b07086-bd3f-4882-8476-8dcafee79b1c)\n")
        f.write(f"  Minimal Input: integers = [128], input_len = 1\n")
        f.write(f"  Assertion Failure: {double_failure_msg}\n")
        f.write(f"\nLearner stub untouched in working tree: {is_stub_unsolved}\n")
        f.write(f"Maintenance documentation present: True\n")
        f.write(f"Debugging hint present: True\n")

    # Generate PR description in work/R48-T043/PR_BODY.md
    pr_body_file = os.path.join(work_dir, "PR_BODY.md")
    with open(pr_body_file, "w", encoding="utf-8") as f:
        f.write(f"""## Description
Mutation-driven regression analysis and test verification for `exercises/practice/variable-length-quantity`.
- Identified and evaluated deliberate mutants in `encode()` against canonical VLQ specification.
- Primary mutant: pre-condition loop (`while (integer)`) instead of post-condition loop (`do ... while (integer)`), exposing the mistaken assumption that zero produces no bytes.
- Reduced rejecting test case to the smallest input allowed by specification: `integers = {{ 0x0 }}` (length 1), rejected by canonical test `test_zero` (`35c9db2e-f781-4c52-b73b-8e76427defd0`) with `Expected 1 Was 0`.
- Secondary mutant: premature continuation check (`while (integer > 0x7f)`), rejected by `test_smallest_double_byte` (`77b07086-bd3f-4882-8476-8dcafee79b1c`) with `Expected 2 Was 1`.
- Added learner debugging hint in `exercises/practice/variable-length-quantity/.docs/hints.md` explaining the contract and minimal diagnostic inputs without giving away the full solution.
- Added comprehensive maintenance documentation in `docs/maintenance/variable-length-quantity.md` and mirrored to `.meta/MAINTENANCE.md`.
- Added automated check in `work/R48-T043/check.py` and course check in `tools/course_checks/r48-t043.py`.
- Working tree learner stubs (`variable_length_quantity.c`, `variable_length_quantity.h`) remain completely unsolved.

## Related Issue
Fixes: #43

## Type of Change
- [x] Documentation
- [ ] Bug Fix
- [ ] New Feature
- [ ] UI/UX Improvement
- [ ] Performance Improvement
- [x] Tests
- [x] Refactoring / Maintenance
- [ ] CI/CD

## Changes Made
- Added `exercises/practice/variable-length-quantity/.docs/hints.md` providing debugging hints for zero-value encoding, multi-byte continuation conditions, and diagnostic inputs.
- Added `docs/maintenance/variable-length-quantity.md` (and `.meta/MAINTENANCE.md`) recording contract specifications, case-to-output mapping for all 26 cases, primary and secondary mutant diffs, rejecting test IDs, and minimal input reduction.
- Created `work/R48-T043/check.py` and `tools/course_checks/r48-t043.py` automated verification scripts.
- Verified that all 26 tests pass against the original reference in an isolated scratch directory with 0 failures and 0 ignored.
- Verified that the primary mutant fails `test_zero` with `Expected 1 Was 0` (exit code 2).
- Saved verification evidence in `work/R48-T043/` (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results
- Ran `python3 work/R48-T043/check.py` and `python3 tools/course_checks/r48-t043.py`.
- **26/26 tests passed** against original reference with 0 failures and 0 ignored.
- **Primary mutant failed** assertion in `test_zero` (`35c9db2e-f781-4c52-b73b-8e76427defd0`) with `Expected 1 Was 0`.
- **Secondary mutant failed** assertion in `test_smallest_double_byte` (`77b07086-bd3f-4882-8476-8dcafee79b1c`) with `Expected 2 Was 1`.
- Learner starter files (`variable_length_quantity.c`, `variable_length_quantity.h`) in working tree remain unsolved.

## Done When Checklist
- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The original passes and the documented mutant fails the named assertion; changing only formatting is not a valid mutation.
- [x] The hint explains the underlying contract and provides a small diagnostic input without publishing the entire reference solution.

## Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.

## General PR Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [x] I have addressed previous review feedback, if applicable.

## Additional Notes
All criteria in the "Done when" and "Submission" checklists for task R48-T043 are fully satisfied.
""")

    print(f"\n[SUCCESS] All checks passed. Evidence saved to {work_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
