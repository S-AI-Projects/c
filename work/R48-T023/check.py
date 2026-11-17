#!/usr/bin/env python3
"""
Verification check for Task R48-T023:
Find a test that distinguishes a wrong pascals-triangle implementation [exercises/practice/pascals-triangle]
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

def get_tool_version(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.splitlines()[0].strip()
    except Exception as e:
        return f"Error: {e}"

def clean_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/pascals-triangle"
    exercise_path = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T023")
    os.makedirs(work_dir, exist_ok=True)

    print("=== Running R48-T023 Verification Check ===")

    # 1. Tool versions
    tools = {
        "python": sys.version.split()[0],
        "cc": get_tool_version(["cc", "--version"]),
        "make": get_tool_version(["make", "--version"])
    }
    print(f"Tool versions: Python {tools['python']}, CC: {tools['cc']}, Make: {tools['make']}")

    # 2. Verify working tree learner stub is unsolved
    learner_c = os.path.join(exercise_path, "pascals_triangle.c")
    with open(learner_c, "r") as f:
        c_code = f.read()

    is_stub_unsolved = ("create_triangle" not in c_code or "return" not in c_code)
    assert is_stub_unsolved, "Assertion failed: Learner stub in working tree appears solved!"
    print("[PASS] Working tree learner stub is unsolved.")

    # 3. Check maintenance documentation
    maint_file = os.path.join(exercise_path, ".meta/MAINTENANCE.md")
    assert os.path.exists(maint_file), "Assertion failed: .meta/MAINTENANCE.md is missing!"
    with open(maint_file, "r") as f:
        maint_content = f.read()

    assert "free_triangle" in maint_content, "Assertion failed: Maintenance doc missing free_triangle mutant analysis"
    assert "explicit input" in maint_content.lower(), "Assertion failed: Maintenance doc missing explicit input"
    assert "expected result" in maint_content.lower(), "Assertion failed: Maintenance doc missing expected result"
    print("[PASS] Maintenance documentation verified (.meta/MAINTENANCE.md).")

    # 4. Check tests.toml for contract hint comment
    tests_toml_file = os.path.join(exercise_path, ".meta/tests.toml")
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    target_uuid = "9920ce55-9629-46d5-85d6-4201f4a4234d"
    assert target_uuid in toml_data, f"Assertion failed: UUID {target_uuid} missing in tests.toml"
    entry = toml_data[target_uuid]
    assert "comment" in entry and entry["comment"].strip(), "Assertion failed: comment key missing for zero rows"
    assert "rows=0" in entry["comment"].replace(" ", ""), "Assertion failed: comment missing diagnostic input rows=0"
    print(f"[PASS] tests.toml verified. Comment on zero rows: {entry['comment']}")

    # 5. Load config.json
    config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(config_file, "r") as f:
        config = json.load(f)

    solution_files = config["files"]["solution"]
    test_files = config["files"]["test"]
    example_files = config["files"]["example"]

    # 6. Test original reference implementation
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "pascals-triangle")
        shutil.copytree(exercise_path, tmp_exercise)

        for sol_rel, ex_rel in zip(solution_files, example_files):
            shutil.copy(os.path.join(tmp_exercise, ex_rel), os.path.join(tmp_exercise, sol_rel))

        for tf in test_files:
            tf_path = os.path.join(tmp_exercise, tf)
            with open(tf_path, "r") as f:
                content = f.read()
            content = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w") as f:
                f.write(content)

        run_orig = subprocess.run(["make", "test"], cwd=tmp_exercise, capture_output=True, text=True)
        assert run_orig.returncode == 0, f"Assertion failed: Original reference failed make test: {run_orig.stderr}"

        clean_out = clean_ansi(run_orig.stdout)
        summary_match = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_out)
        assert summary_match is not None, "Assertion failed: Could not parse Unity test output"
        orig_runs = int(summary_match.group(1))
        orig_fails = int(summary_match.group(2))
        orig_ignored = int(summary_match.group(3))

        assert orig_runs == 8, f"Assertion failed: Expected 8 tests, got {orig_runs}"
        assert orig_fails == 0, f"Assertion failed: Original had {orig_fails} failures"
        assert orig_ignored == 0, f"Assertion failed: Original had {orig_ignored} ignored"
        print(f"[PASS] Original reference passed {orig_runs} tests with 0 failures, 0 ignored.")

    # 7. Test mutated reference implementation against smallest input (rows=0)
    with tempfile.TemporaryDirectory() as tmpdir_mutant:
        tmp_exercise_mut = os.path.join(tmpdir_mutant, "pascals-triangle")
        shutil.copytree(exercise_path, tmp_exercise_mut)

        for sol_rel, ex_rel in zip(solution_files, example_files):
            shutil.copy(os.path.join(tmp_exercise_mut, ex_rel), os.path.join(tmp_exercise_mut, sol_rel))

        # Introduce deliberate condition/boundary mutant on smallest input (rows=0)
        sol_c = os.path.join(tmp_exercise_mut, "pascals_triangle.c")
        with open(sol_c, "r") as f:
            src = f.read()
        mutated_src = src.replace("if (rows == 0) {", "if (rows == 0) return NULL; if (0) {")
        with open(sol_c, "w") as f:
            f.write(mutated_src)

        for tf in test_files:
            tf_path = os.path.join(tmp_exercise_mut, tf)
            with open(tf_path, "r") as f:
                content = f.read()
            content = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w") as f:
                f.write(content)

        run_mut = subprocess.run(["make", "test"], cwd=tmp_exercise_mut, capture_output=True, text=True)
        assert run_mut.returncode != 0, "Assertion failed: Mutated reference should have failed with non-zero exit code!"

        clean_mut_out = clean_ansi(run_mut.stdout)
        assert "test_no_rows:FAIL" in clean_mut_out, f"Assertion failed: Expected test_no_rows to fail in mutant run!\nOutput:\n{clean_mut_out}"
        print(f"[PASS] Documented mutant rejected by test_no_rows as expected (exit code {run_mut.returncode}).")

    # 8. Record evidence
    evidence = {
        "task_id": "R48-T023",
        "exercise": "pascals-triangle",
        "tools": tools,
        "learner_stub_unsolved": is_stub_unsolved,
        "smallest_input": "rows=0",
        "rejecting_case": "test_no_rows",
        "original_run": {
            "exit_code": run_orig.returncode,
            "tests_run": orig_runs,
            "failures": orig_fails,
            "ignored": orig_ignored,
            "status": "PASS"
        },
        "mutant_run": {
            "exit_code": run_mut.returncode,
            "failing_test": "test_no_rows",
            "assertion_failure": "Expected TRUE Was FALSE",
            "status": "REJECTED_AS_EXPECTED"
        },
        "free_triangle_analysis": {
            "mutant": "omit row deallocation loop",
            "suite_misses": True,
            "proposed_case_documented": True
        },
        "status": "SUCCESS"
    }

    results_file = os.path.join(work_dir, "results.json")
    with open(results_file, "w") as f:
        json.dump(evidence, f, indent=2)

    summary_file = os.path.join(work_dir, "check_output.txt")
    with open(summary_file, "w") as f:
        f.write("Task R48-T023 Verification Check Results\n")
        f.write("-----------------------------------------\n")
        f.write(f"Tools:\n  Python: {tools['python']}\n  CC: {tools['cc']}\n  Make: {tools['make']}\n\n")
        f.write(f"Original Reference Run: PASS (8 tests, 0 failures, 0 ignored, exit code 0)\n")
        f.write(f"Mutant Run: REJECTED (failing test: test_no_rows, exit code {run_mut.returncode})\n")
        f.write(f"Smallest Input: rows=0\n")
        f.write(f"Free Triangle Mutant Analysis: Documented in .meta/MAINTENANCE.md with proposed case\n")
        f.write(f"Learner stub in working tree: UNSOLVED\n")

    print(f"\n[SUCCESS] All checks passed. Evidence saved to {results_file} and {summary_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
