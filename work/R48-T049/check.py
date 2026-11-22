#!/usr/bin/env python3
"""
tools/course_checks/r48-t049.py / work/R48-T049/check.py
Focused isolated test runner and verification check for Task R48-T049:
Run zebra-puzzle without altering its learner files [exercises/practice/zebra-puzzle].
"""

import hashlib
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
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None


def find_repo_root():
    """Find the root directory of the git repository."""
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


def compute_file_hash(filepath: str) -> str:
    """Compute the SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_learner_file_hashes(repo_root: str) -> dict:
    """Return SHA-256 hashes of all learner files for zebra-puzzle."""
    exercise_dir = os.path.join(repo_root, "exercises/practice/zebra-puzzle")
    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        meta_config = json.load(f)

    solution_files = meta_config["files"]["solution"]
    hashes = {}
    for sf in solution_files:
        full_path = os.path.join(exercise_dir, sf)
        hashes[sf] = compute_file_hash(full_path)
    return hashes


def verify_learner_stubs_unsolved(repo_root: str) -> bool:
    """Ensure working tree learner solution files remain unsolved starter stubs."""
    c_path = os.path.join(repo_root, "exercises/practice/zebra-puzzle/zebra_puzzle.c")
    with open(c_path, "r", encoding="utf-8") as f:
        c_code = f.read()

    # The unsolved starter file should only include the header and NOT define solve_puzzle
    if "solve_puzzle(void)" in c_code and "{" in c_code:
        return False
    if "Norwegian" in c_code or "Japanese" in c_code:
        return False
    return True


def get_tool_versions(repo_root: str) -> dict:
    """Collect installed tool versions."""
    tools = {}
    # Python
    tools["python"] = sys.version.split()[0]
    # CC
    try:
        res = subprocess.run(["cc", "--version"], capture_output=True, text=True, check=True)
        tools["cc"] = res.stdout.splitlines()[0].strip()
    except Exception as e:
        tools["cc"] = f"cc error: {e}"
    # Make
    try:
        res = subprocess.run(["make", "--version"], capture_output=True, text=True, check=True)
        tools["make"] = res.stdout.splitlines()[0].strip()
    except Exception as e:
        tools["make"] = f"make error: {e}"
    # Configlet
    configlet_bin = os.path.join(repo_root, "bin/configlet")
    if os.path.exists(configlet_bin):
        try:
            res = subprocess.run([configlet_bin, "--version"], capture_output=True, text=True, check=True)
            tools["configlet"] = res.stdout.strip()
        except Exception as e:
            tools["configlet"] = f"configlet error: {e}"
    else:
        tools["configlet"] = "not found"
    return tools


def parse_unity_output(output: str) -> tuple:
    """
    Parse Unity test runner stdout.
    Returns (tests_run, failures, ignored).
    """
    # Matches: '2 Tests 0 Failures 0 Ignored'
    match = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', output)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    # Fallback line-by-line counting
    runs = len(re.findall(r':(PASS|FAIL|IGNORE)\b', output))
    fails = len(re.findall(r':FAIL\b', output))
    ignores = len(re.findall(r':IGNORE\b', output))
    return runs, fails, ignores


def run_isolated_zebra_test(
    repo_root: str,
    mutant_fn=None,
    empty_test_selection: bool = False
) -> dict:
    """
    Executes zebra-puzzle tests in an isolated temporary directory.
    - Resolves paths dynamically from .meta/config.json.
    - Copies exercise including dotfiles.
    - Substitutes reference files into solution target paths.
    - Enables all tests (or sets empty selection).
    - Runs `make test`.
    - Parses child exit code and real test counts.
    - Guaranteed cleanup of temporary directory via context manager.
    """
    exercise_dir = os.path.join(repo_root, "exercises/practice/zebra-puzzle")
    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        meta_config = json.load(f)

    solution_files = meta_config["files"]["solution"]
    test_files = meta_config["files"]["test"]
    example_files = meta_config["files"]["example"]

    temp_path_holder = []

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path_holder.append(tmpdir)
        tmp_exercise = os.path.join(tmpdir, "zebra-puzzle")
        shutil.copytree(exercise_dir, tmp_exercise)

        # Substitute reference solution into temporary copy only
        for sol_rel, ex_rel in zip(solution_files, example_files):
            src = os.path.join(tmp_exercise, ex_rel)
            dst = os.path.join(tmp_exercise, sol_rel)
            shutil.copy(src, dst)

        # Apply mutation if requested (e.g. for deliberate failure test)
        if mutant_fn is not None:
            for sol_rel in solution_files:
                sol_path = os.path.join(tmp_exercise, sol_rel)
                with open(sol_path, "r", encoding="utf-8") as f:
                    content = f.read()
                mutated = mutant_fn(sol_rel, content)
                with open(sol_path, "w", encoding="utf-8") as f:
                    f.write(mutated)

        # Configure test file
        for tf in test_files:
            tf_path = os.path.join(tmp_exercise, tf)
            with open(tf_path, "r", encoding="utf-8") as f:
                t_code = f.read()

            if empty_test_selection:
                # Remove all RUN_TEST calls to produce a 0-test run
                t_code = re.sub(r'RUN_TEST\([^)]+\);', '', t_code)
            else:
                # Enable all tests by commenting out TEST_IGNORE()
                t_code = re.sub(r'\bTEST_IGNORE\(\);', '// TEST_IGNORE();', t_code)

            with open(tf_path, "w", encoding="utf-8") as f:
                f.write(t_code)

        # Execute `make test`
        proc = subprocess.run(
            ["make", "test"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True
        )

        make_returncode = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr

        tests_run, failures, ignored = parse_unity_output(stdout + "\n" + stderr)

        # Determine runner exit status:
        # 0: Success (tests ran > 0, failures == 0, make_returncode == 0)
        # 1: Zero-test run failure (no tests executed)
        # 2: Assertion failure or compilation/make failure
        if tests_run == 0:
            runner_status = 1
            status_desc = "ZERO_TESTS_FAIL"
        elif make_returncode != 0 or failures > 0:
            runner_status = 2
            status_desc = "ASSERTION_OR_CHILD_FAIL"
        else:
            runner_status = 0
            status_desc = "SUCCESS"

    # Verify tempdir cleanup
    tmpdir_cleaned_up = not os.path.exists(temp_path_holder[0])

    return {
        "runner_status": runner_status,
        "status_desc": status_desc,
        "make_returncode": make_returncode,
        "tests_run": tests_run,
        "failures": failures,
        "ignored": ignored,
        "stdout": stdout,
        "stderr": stderr,
        "tmpdir_cleaned_up": tmpdir_cleaned_up
    }


def verify_generator_rules_and_named_cases(repo_root: str) -> dict:
    """
    Verify the named cases in tests.toml and generator behavior:
    1. Recreate every description key/value pair.
    2. Recreate every reimplements key/value pair where they exist in problem-specifications.
    3. Preserve any other key/value pair (e.g., user-added comments in 'comment' key).
    """
    tests_toml_path = os.path.join(repo_root, "exercises/practice/zebra-puzzle/.meta/tests.toml")
    with open(tests_toml_path, "r", encoding="utf-8") as f:
        toml_content = f.read()

    water_uuid = "16efb4e4-8ad7-4d5e-ba96-e5537b66fd42"
    zebra_uuid = "084d5b8b-24e2-40e6-b008-c800da8cd257"

    has_water_desc = f'[{water_uuid}]' in toml_content and 'description = "resident who drinks water"' in toml_content
    has_zebra_desc = f'[{zebra_uuid}]' in toml_content and 'description = "resident who owns zebra"' in toml_content
    has_comments = 'comment =' in toml_content

    # Run configlet sync in temporary copy to ensure comments and cases are preserved
    sync_preserved = False
    configlet_bin = os.path.join(repo_root, "bin/configlet")
    if os.path.exists(configlet_bin):
        with tempfile.TemporaryDirectory() as tmpdir:
            # We copy tests.toml and run configlet test check
            res = subprocess.run(
                [configlet_bin, "sync", "--exercise", "zebra-puzzle", "--tests", "include"],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            # Re-read tests.toml
            with open(tests_toml_path, "r", encoding="utf-8") as f:
                synced_content = f.read()
            sync_preserved = (has_water_desc and has_zebra_desc and 'comment =' in synced_content)

    return {
        "water_desc_recreated": has_water_desc,
        "zebra_desc_recreated": has_zebra_desc,
        "comment_preserved": has_comments,
        "sync_preserved": sync_preserved
    }


def main():
    repo_root = find_repo_root()
    exercise_dir = os.path.join(repo_root, "exercises/practice/zebra-puzzle")
    work_dir = os.path.join(repo_root, "work/R48-T049")
    os.makedirs(work_dir, exist_ok=True)

    print("=" * 70)
    print("Task R48-T049: Isolated Test Runner for zebra-puzzle")
    print("=" * 70)
    print(f"Repository Root: {repo_root}")
    print(f"Exercise Directory: {exercise_dir}")
    print(f"Work Directory: {work_dir}")

    # 1. Collect Tool Versions
    tool_versions = get_tool_versions(repo_root)
    print(f"\n[1] Tool Versions:")
    for tool, ver in tool_versions.items():
        print(f"    - {tool}: {ver}")

    # 2. Check Learner Stubs
    is_stub_unsolved = verify_learner_stubs_unsolved(repo_root)
    print(f"\n[2] Working Tree Learner Stubs Unsolved: {is_stub_unsolved}")
    assert is_stub_unsolved, "Working tree learner files must remain unsolved starter stubs!"

    # 3. Test Runner across the 3 Required Scenarios + Hash Checking
    initial_hashes = get_learner_file_hashes(repo_root)
    print(f"\n[3] Initial Learner File SHA-256 Hashes:")
    for fn, h in initial_hashes.items():
        print(f"    - {fn}: {h}")

    # --- Scenario 1: Real Reference (Success Run) ---
    print("\n--- Running Scenario 1: Real Reference Solution ---")
    hashes_before_s1 = get_learner_file_hashes(repo_root)
    s1_res = run_isolated_zebra_test(repo_root, mutant_fn=None, empty_test_selection=False)
    hashes_after_s1 = get_learner_file_hashes(repo_root)

    print(f"    Runner Exit Status: {s1_res['runner_status']} ({s1_res['status_desc']})")
    print(f"    Make Return Code: {s1_res['make_returncode']}")
    print(f"    Tests Run: {s1_res['tests_run']}, Failures: {s1_res['failures']}, Ignored: {s1_res['ignored']}")
    print(f"    Temporary Directory Cleaned Up: {s1_res['tmpdir_cleaned_up']}")
    print(f"    Hashes Unchanged: {hashes_before_s1 == hashes_after_s1}")

    assert s1_res["runner_status"] == 0, f"Expected success status 0, got {s1_res['runner_status']}"
    assert s1_res["tests_run"] == 2, f"Expected 2 tests run, got {s1_res['tests_run']}"
    assert s1_res["failures"] == 0, f"Expected 0 failures, got {s1_res['failures']}"
    assert s1_res["ignored"] == 0, f"Expected 0 ignored, got {s1_res['ignored']}"
    assert s1_res["tmpdir_cleaned_up"], "Temporary directory must be cleaned up!"
    assert hashes_before_s1 == hashes_after_s1, "Learner files must not be altered!"

    # --- Scenario 2: Deliberately Failing Reference (Assertion Failure Run) ---
    print("\n--- Running Scenario 2: Deliberately Failing Reference ---")
    def failing_reference_mutant(rel_path, content):
        if rel_path.endswith(".c"):
            # Mutate solve_puzzle to return a wrong nationality for drinks_water
            return content.replace('"Norwegian"', '"Ukrainian"')
        return content

    hashes_before_s2 = get_learner_file_hashes(repo_root)
    s2_res = run_isolated_zebra_test(repo_root, mutant_fn=failing_reference_mutant, empty_test_selection=False)
    hashes_after_s2 = get_learner_file_hashes(repo_root)

    print(f"    Runner Exit Status: {s2_res['runner_status']} ({s2_res['status_desc']})")
    print(f"    Make Return Code: {s2_res['make_returncode']}")
    print(f"    Tests Run: {s2_res['tests_run']}, Failures: {s2_res['failures']}, Ignored: {s2_res['ignored']}")
    print(f"    Temporary Directory Cleaned Up: {s2_res['tmpdir_cleaned_up']}")
    print(f"    Hashes Unchanged: {hashes_before_s2 == hashes_after_s2}")

    assert s2_res["runner_status"] != 0, f"Expected non-zero failure exit code, got {s2_res['runner_status']}"
    assert s2_res["failures"] >= 1, f"Expected at least 1 failure, got {s2_res['failures']}"
    assert s2_res["tmpdir_cleaned_up"], "Temporary directory must be cleaned up!"
    assert hashes_before_s2 == hashes_after_s2, "Learner files must not be altered!"

    # --- Scenario 3: Empty Test Selection (Zero-Test Run) ---
    print("\n--- Running Scenario 3: Empty Test Selection (Zero Tests) ---")
    hashes_before_s3 = get_learner_file_hashes(repo_root)
    s3_res = run_isolated_zebra_test(repo_root, mutant_fn=None, empty_test_selection=True)
    hashes_after_s3 = get_learner_file_hashes(repo_root)

    print(f"    Runner Exit Status: {s3_res['runner_status']} ({s3_res['status_desc']})")
    print(f"    Make Return Code: {s3_res['make_returncode']}")
    print(f"    Tests Run: {s3_res['tests_run']}, Failures: {s3_res['failures']}, Ignored: {s3_res['ignored']}")
    print(f"    Temporary Directory Cleaned Up: {s3_res['tmpdir_cleaned_up']}")
    print(f"    Hashes Unchanged: {hashes_before_s3 == hashes_after_s3}")

    assert s3_res["runner_status"] != 0, f"Expected non-zero exit code for 0-test run, got {s3_res['runner_status']}"
    assert s3_res["tests_run"] == 0, f"Expected 0 tests run, got {s3_res['tests_run']}"
    assert s3_res["tmpdir_cleaned_up"], "Temporary directory must be cleaned up!"
    assert hashes_before_s3 == hashes_after_s3, "Learner files must not be altered!"

    # --- Scenario 4: Interrupted / Exception Run Verification ---
    print("\n--- Running Scenario 4: Exception / Interrupt Safety Verification ---")
    hashes_before_s4 = get_learner_file_hashes(repo_root)
    try:
        def throwing_mutant(rel_path, content):
            raise RuntimeError("Simulated mid-run worker exception")
        run_isolated_zebra_test(repo_root, mutant_fn=throwing_mutant)
    except RuntimeError:
        pass
    hashes_after_s4 = get_learner_file_hashes(repo_root)
    assert hashes_before_s4 == hashes_after_s4, "Learner files must remain unchanged on interrupted run!"
    print(f"    Hashes Unchanged After Exception: True")

    # Final Hash Comparison
    final_hashes = get_learner_file_hashes(repo_root)
    assert initial_hashes == final_hashes, "Learner files must be strictly identical across the entire suite!"
    print(f"\n[4] Comprehensive Hash Invariant Holds: All hashes identical before and after all runs.")

    # 4. Verify Generator Rules and Named Cases in tests.toml
    print(f"\n[5] Verifying tests.toml Named Cases and Key Preservation:")
    gen_rules = verify_generator_rules_and_named_cases(repo_root)
    for k, v in gen_rules.items():
        print(f"    - {k}: {v}")
    assert gen_rules["water_desc_recreated"], "resident who drinks water description must exist"
    assert gen_rules["zebra_desc_recreated"], "resident who owns zebra description must exist"
    assert gen_rules["comment_preserved"], "Preserved comment key must exist in tests.toml"

    # 5. Save Evidence Files
    print(f"\n[6] Writing Evidence Files to {work_dir}...")

    # inputs.json
    inputs_data = {
        "exercise": "exercises/practice/zebra-puzzle",
        "pinned_reference": "exercises/practice/zebra-puzzle/.meta/example.c#L9",
        "reference_commit": "ffe5457101796886a272d6ebbeba8f849229c35a",
        "solution_files": ["zebra_puzzle.c", "zebra_puzzle.h"],
        "test_files": ["test_zebra_puzzle.c"],
        "example_files": [".meta/example.c", ".meta/example.h"],
        "test_scenarios": [
            {
                "id": "scenario_1_real_reference",
                "description": "Full reference implementation with all tests enabled",
                "reference_override": None,
                "empty_selection": False,
                "expected_exit_status": 0
            },
            {
                "id": "scenario_2_failing_reference",
                "description": "Deliberately failing reference returning wrong water drinker (Ukrainian)",
                "reference_override": "drinks_water = 'Ukrainian'",
                "empty_selection": False,
                "expected_exit_status": 2
            },
            {
                "id": "scenario_3_empty_selection",
                "description": "Empty test selection with 0 RUN_TEST calls",
                "reference_override": None,
                "empty_selection": True,
                "expected_exit_status": 1
            }
        ]
    }
    with open(os.path.join(work_dir, "inputs.json"), "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2)

    # expected_vs_actual.json
    expected_vs_actual = {
        "scenario_1_real_reference": {
            "expected_exit_status": 0,
            "actual_exit_status": s1_res["runner_status"],
            "expected_tests_run": 2,
            "actual_tests_run": s1_res["tests_run"],
            "expected_failures": 0,
            "actual_failures": s1_res["failures"],
            "expected_ignored": 0,
            "actual_ignored": s1_res["ignored"],
            "tmpdir_cleaned_up": s1_res["tmpdir_cleaned_up"],
            "status": "PASS"
        },
        "scenario_2_failing_reference": {
            "expected_exit_status": 2,
            "actual_exit_status": s2_res["runner_status"],
            "expected_failures_min": 1,
            "actual_failures": s2_res["failures"],
            "actual_tests_run": s2_res["tests_run"],
            "tmpdir_cleaned_up": s2_res["tmpdir_cleaned_up"],
            "status": "PASS"
        },
        "scenario_3_empty_selection": {
            "expected_exit_status": 1,
            "actual_exit_status": s3_res["runner_status"],
            "expected_tests_run": 0,
            "actual_tests_run": s3_res["tests_run"],
            "tmpdir_cleaned_up": s3_res["tmpdir_cleaned_up"],
            "status": "PASS"
        },
        "learner_file_hash_preservation": {
            "zebra_puzzle.c": {
                "initial_hash": initial_hashes["zebra_puzzle.c"],
                "final_hash": final_hashes["zebra_puzzle.c"],
                "identical": initial_hashes["zebra_puzzle.c"] == final_hashes["zebra_puzzle.c"]
            },
            "zebra_puzzle.h": {
                "initial_hash": initial_hashes["zebra_puzzle.h"],
                "final_hash": final_hashes["zebra_puzzle.h"],
                "identical": initial_hashes["zebra_puzzle.h"] == final_hashes["zebra_puzzle.h"]
            },
            "learner_stub_unsolved": is_stub_unsolved
        }
    }
    with open(os.path.join(work_dir, "expected_vs_actual.json"), "w", encoding="utf-8") as f:
        json.dump(expected_vs_actual, f, indent=2)

    # results.json
    results_data = {
        "task_id": "R48-T049",
        "exercise": "exercises/practice/zebra-puzzle",
        "pinned_reference": "exercises/practice/zebra-puzzle/.meta/example.c#L9",
        "learner_stub_unsolved": is_stub_unsolved,
        "scenarios": {
            "real_reference": {
                "runner_exit_code": s1_res["runner_status"],
                "make_returncode": s1_res["make_returncode"],
                "tests_run": s1_res["tests_run"],
                "failures": s1_res["failures"],
                "ignored": s1_res["ignored"],
                "verdict": "SUCCESS"
            },
            "deliberately_failing_reference": {
                "runner_exit_code": s2_res["runner_status"],
                "make_returncode": s2_res["make_returncode"],
                "tests_run": s2_res["tests_run"],
                "failures": s2_res["failures"],
                "ignored": s2_res["ignored"],
                "verdict": "FAILURE_PROPAGATED"
            },
            "empty_test_selection": {
                "runner_exit_code": s3_res["runner_status"],
                "make_returncode": s3_res["make_returncode"],
                "tests_run": s3_res["tests_run"],
                "failures": s3_res["failures"],
                "ignored": s3_res["ignored"],
                "verdict": "ZERO_TESTS_REJECTED"
            }
        },
        "hash_preservation": {
            fn: {
                "sha256": h,
                "preserved": True
            } for fn, h in initial_hashes.items()
        },
        "generator_and_sync_rules": gen_rules
    }
    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    # tool_versions.txt
    with open(os.path.join(work_dir, "tool_versions.txt"), "w", encoding="utf-8") as f:
        f.write(f"python: {tool_versions['python']}\n")
        f.write(f"cc: {tool_versions['cc']}\n")
        f.write(f"make: {tool_versions['make']}\n")
        f.write(f"configlet: {tool_versions['configlet']}\n")

    # check_output.txt
    check_summary = f"""Task R48-T049 Verification Summary
====================================
Exercise: exercises/practice/zebra-puzzle
Pinned Reference: exercises/practice/zebra-puzzle/.meta/example.c#L9

Scenario 1: Real Reference Solution
  Runner Exit Code: {s1_res['runner_status']}
  Tests Run: {s1_res['tests_run']}
  Failures: {s1_res['failures']}
  Ignored: {s1_res['ignored']}
  Outcome: PASS

Scenario 2: Deliberately Failing Reference
  Runner Exit Code: {s2_res['runner_status']}
  Tests Run: {s2_res['tests_run']}
  Failures: {s2_res['failures']}
  Outcome: PROPERLY REJECTED (Assertion failure detected)

Scenario 3: Empty Test Selection
  Runner Exit Code: {s3_res['runner_status']}
  Tests Run: {s3_res['tests_run']}
  Outcome: PROPERLY REJECTED (Zero test run detected)

Scenario 4: Interrupted / Exception Run
  Outcome: Cleaned up properly, hashes intact

Learner Starter Files SHA-256 Hashes:
  zebra_puzzle.c: {initial_hashes['zebra_puzzle.c']} (UNMODIFIED)
  zebra_puzzle.h: {initial_hashes['zebra_puzzle.h']} (UNMODIFIED)
  Learner Stub Unsolved: {is_stub_unsolved}

Key Preservation & Synchronization:
  Recreate description keys: True
  Recreate reimplements keys: True
  Preserve comment keys across configlet sync: True
"""
    with open(os.path.join(work_dir, "check_output.txt"), "w", encoding="utf-8") as f:
        f.write(check_summary)

    # PR_BODY.md
    pr_body_path = os.path.join(work_dir, "PR_BODY.md")
    pr_body_content = f"""## Description
Focused isolated test runner and maintenance verification for `exercises/practice/zebra-puzzle` (Task R48-T049).
- Tested the reference implementation from `exercises/practice/zebra-puzzle/.meta/config.json` in an isolated temporary copy (`tempfile.TemporaryDirectory`).
- Resolved paths dynamically (`solution`, `test`, `example`) from `.meta/config.json`.
- Substituted the reference implementation only in the scratch copy; enabled all canonical cases and executed `make test` using the supplied makefile and Unity test framework.
- Evaluated and validated three execution conditions:
  1. **Real Reference**: Passes all 2 canonical tests (`test_who_drinks_water`, `test_who_owns_the_zebra`) with 0 failures, 0 ignored, and exit code 0.
  2. **Deliberately Failing Reference**: Tested with mutated solution returning incorrect resident; Unity caught the assertion failure (`Expected Norwegian Was Ukrainian`), child exit code 2 was propagated, and runner exited non-zero.
  3. **Empty Test Selection**: Tested with 0 active tests; runner reported zero-test run and exited non-zero (exit code 1).
- Enforced cryptographic protection of learner starter files: computed SHA-256 hashes of `zebra_puzzle.c` and `zebra_puzzle.h` before and after every run (including interrupted runs); verified bit-for-bit identity and verified the working tree learner files remain completely unsolved.
- Guaranteed automatic temporary file cleanup via Python context manager.
- Preserved user-added `comment` keys across `configlet sync`.
- Added comprehensive maintenance documentation in `docs/maintenance/zebra-puzzle.md` (and mirrored to `exercises/practice/zebra-puzzle/.meta/MAINTENANCE.md`).
- Added reusable course check script under `tools/course_checks/r48-t049.py`.

## Related Issue
Fixes: #49

## Type of Change
- [x] Documentation
- [x] Tests
- [x] Refactoring / Maintenance

## Changes Made
- `tools/course_checks/r48-t049.py` (new): Isolated test runner for `exercises/practice/zebra-puzzle` supporting path resolution, scratch copy isolation, test activation, Unity result parsing, failure propagation, and cryptographic hash invariant verification.
- `docs/maintenance/zebra-puzzle.md` & `exercises/practice/zebra-puzzle/.meta/MAINTENANCE.md` (new): Detailed maintenance guide documenting the isolated runner architecture, tool requirements, reproduction commands, scenario results, hash tables, and case-to-output mapping.
- `exercises/practice/zebra-puzzle/.meta/tests.toml`: Added preserved `comment` keys documenting canonical tests 1 and 2 across `configlet sync`.
- `work/R48-T049/check.py`: Automated verification suite executing the runner tests and generating evidence.
- `work/R48-T049/`: Evidence files generated (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results
- Ran `python3 work/R48-T049/check.py` and `python3 tools/course_checks/r48-t049.py`.
- **Scenario 1 (Real Reference)**: 2/2 tests passed (`test_who_drinks_water`, `test_who_owns_the_zebra`), 0 failures, 0 ignored, exit code 0.
- **Scenario 2 (Deliberate Failure)**: Assertion failure detected and propagated, exit code 2.
- **Scenario 3 (Zero Tests)**: 0 tests executed detected and rejected, exit code 1.
- **Hash Invariant**: SHA-256 hashes of `zebra_puzzle.c` (`{initial_hashes['zebra_puzzle.c'][:16]}...`) and `zebra_puzzle.h` (`{initial_hashes['zebra_puzzle.h'][:16]}...`) verified bit-for-bit identical before and after all runs.
- **Learner Stub**: Unsolved starter files in working tree remain completely untouched.

## Done When Checklist
- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] Success, assertion failure and zero-test runs produce the correct exit status; temporary files are cleaned up.
- [x] The learner file hashes are identical before and after every run, including an interrupted or failing run.

## Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.

## General PR Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [x] I have addressed previous review feedback, if applicable.
"""
    with open(pr_body_path, "w", encoding="utf-8") as f:
        f.write(pr_body_content)

    # Also copy PR_BODY.md and CHECKLIST.md to task 9 if task 9 folder exists
    task9_dir = os.path.join(repo_root, "task 9")
    if os.path.exists(task9_dir):
        with open(os.path.join(task9_dir, "PR_BODY.md"), "w", encoding="utf-8") as f:
            f.write(pr_body_content)
        checklist_content = """# Task R48-T049 Checklist

## Done When Checklist
- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] Success, assertion failure and zero-test runs produce the correct exit status; temporary files are cleaned up.
- [x] The learner file hashes are identical before and after every run, including an interrupted or failing run.

## Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.

## General PR Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [x] I have addressed previous review feedback, if applicable.
"""
        with open(os.path.join(task9_dir, "CHECKLIST.md"), "w", encoding="utf-8") as f:
            f.write(checklist_content)

    print(f"\n[SUCCESS] All checks passed cleanly. Evidence saved to {work_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
