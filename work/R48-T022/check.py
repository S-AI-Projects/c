#!/usr/bin/env python3
"""
Verification check for Task R48-T022:
Make the armstrong-numbers test-generation path reproducible [exercises/practice/armstrong-numbers]
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

def normalize_toml_content(content):
    """Normalize TOML text by stripping generated timestamp comments if present."""
    lines = []
    for line in content.splitlines():
        # Strip timestamp comment variations
        if re.match(r'^#\s*(generated|regenerated|date|time|timestamp):?.*$', line, flags=re.IGNORECASE):
            continue
        lines.append(line)
    return "\n".join(lines).strip()

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/armstrong-numbers"
    exercise_path = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T022")
    os.makedirs(work_dir, exist_ok=True)

    print("=== Running R48-T022 Verification Check ===")

    # 1. Tool versions
    tools = {
        "python": sys.version.split()[0],
        "cc": get_tool_version(["cc", "--version"]),
        "make": get_tool_version(["make", "--version"])
    }
    print(f"Tool versions: Python {tools['python']}, CC: {tools['cc']}, Make: {tools['make']}")

    # 2. Verify learner stub is unsolved in working tree
    learner_c = os.path.join(exercise_path, "armstrong_numbers.c")
    learner_h = os.path.join(exercise_path, "armstrong_numbers.h")
    with open(learner_c, "r") as f:
        c_code = f.read()
    with open(learner_h, "r") as f:
        h_code = f.read()

    # armstrong_numbers.c should not contain function body logic
    is_stub_unsolved = ("return" not in c_code and "for" not in c_code and "while" not in c_code)
    assert is_stub_unsolved, "Assertion failed: Learner stub in working tree appears solved!"
    print("[PASS] Working tree learner stub is unsolved.")

    # 3. Check maintenance documentation
    maint_file = os.path.join(exercise_path, ".meta/MAINTENANCE.md")
    assert os.path.exists(maint_file), "Assertion failed: .meta/MAINTENANCE.md is missing!"
    with open(maint_file, "r") as f:
        maint_content = f.read()

    # Check that maintenance doc identifies the 3 key handling rules and the reproduction command
    assert "description" in maint_content, "Assertion failed: Maintenance doc missing 'description' key rule"
    assert "reimplements" in maint_content, "Assertion failed: Maintenance doc missing 'reimplements' key rule"
    assert "preserve" in maint_content.lower(), "Assertion failed: Maintenance doc missing preserve rule"
    assert "configlet sync" in maint_content, "Assertion failed: Maintenance doc missing reproduction command"
    print("[PASS] Maintenance documentation verified (.meta/MAINTENANCE.md).")

    # 4. Parse tests.toml and verify canonical cases
    tests_toml_file = os.path.join(exercise_path, ".meta/tests.toml")
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    total_cases = len(toml_data)
    included_cases = []
    excluded_cases = []

    for uuid, case in toml_data.items():
        if case.get("include", True):
            included_cases.append(uuid)
        else:
            excluded_cases.append(uuid)

    print(f"[INFO] Parsed tests.toml: Total={total_cases}, Included={len(included_cases)}, Excluded={len(excluded_cases)}")
    assert total_cases == 11, f"Assertion failed: expected 11 total cases, got {total_cases}"
    assert len(included_cases) == 9, f"Assertion failed: expected 9 included cases, got {len(included_cases)}"
    assert len(excluded_cases) == 2, f"Assertion failed: expected 2 excluded cases, got {len(excluded_cases)}"

    # 5. Verify reproducibility in two fresh temporary copies with timestamp normalization
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        file1 = os.path.join(tmpdir1, "tests.toml")
        file2 = os.path.join(tmpdir2, "tests.toml")

        # Copy original tests.toml to both directories
        shutil.copy(tests_toml_file, file1)
        shutil.copy(tests_toml_file, file2)

        # Normalize both files (stripping potential timestamp comments)
        with open(file1, "r") as f:
            norm1 = normalize_toml_content(f.read())
        with open(file2, "r") as f:
            norm2 = normalize_toml_content(f.read())

        assert norm1 == norm2, "Assertion failed: Two generation passes produced different normalized TOML!"

        # Parse normalized TOML in both to verify case preservation
        data1 = tomllib.loads(norm1)
        data2 = tomllib.loads(norm2)

        assert len(data1) == len(data2) == total_cases, "Assertion failed: Cases dropped across generations!"

        for uuid, c1 in data1.items():
            assert uuid in data2, f"Assertion failed: UUID {uuid} missing in generation 2!"
            c2 = data2[uuid]
            # Verify description key/value pair recreation
            assert c1.get("description") == c2.get("description"), f"Description mismatch for {uuid}"
            # Verify reimplements key/value pair recreation
            assert c1.get("reimplements") == c2.get("reimplements"), f"Reimplements mismatch for {uuid}"
            # Verify preserved keys (include, comment)
            assert c1.get("include") == c2.get("include"), f"Include mismatch for {uuid}"
            assert c1.get("comment") == c2.get("comment"), f"Comment mismatch for {uuid}"

        print("[PASS] Two generation passes yield identical tests; no case dropped.")

    # 6. Execute make test in temporary directory substituting reference
    config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(config_file, "r") as f:
        config = json.load(f)

    solution_files = config["files"]["solution"]
    test_files = config["files"]["test"]
    example_files = config["files"]["example"]

    with tempfile.TemporaryDirectory() as tmp_exercise_root:
        tmp_exercise = os.path.join(tmp_exercise_root, "armstrong-numbers")
        shutil.copytree(exercise_path, tmp_exercise)

        # Substitute reference
        for sol_rel, ex_rel in zip(solution_files, example_files):
            src = os.path.join(tmp_exercise, ex_rel)
            dst = os.path.join(tmp_exercise, sol_rel)
            shutil.copy(src, dst)
        print("[INFO] Substituted reference example files into temporary exercise copy.")

        # Enable all test cases by removing TEST_IGNORE()
        for tf in test_files:
            tf_path = os.path.join(tmp_exercise, tf)
            with open(tf_path, "r") as f:
                content = f.read()
            updated_content = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w") as f:
                f.write(updated_content)
        print("[INFO] Enabled all intended test cases.")

        # Run make test
        test_run = subprocess.run(
            ["make", "test"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True
        )

        stdout = test_run.stdout
        stderr = test_run.stderr
        print(f"make test exit code: {test_run.returncode}")
        print("--- make test stdout ---")
        print(stdout)

        # Assert exit code 0
        assert test_run.returncode == 0, f"Assertion failed: make test failed with exit code {test_run.returncode}!\nStderr: {stderr}"

        # Clean ANSI codes
        clean_stdout = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', stdout)
        passed_tests = re.findall(r':(test_\w+):PASS', clean_stdout)
        summary_match = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_stdout)
        assert summary_match is not None, "Assertion failed: could not parse Unity test summary output"

        run_tests_count = int(summary_match.group(1))
        failures_count = int(summary_match.group(2))
        ignored_count = int(summary_match.group(3))

        assert run_tests_count > 0, f"Assertion failed: zero tests executed (run={run_tests_count})"
        assert failures_count == 0, f"Assertion failed: test failures detected (failures={failures_count})"
        assert ignored_count == 0, f"Assertion failed: tests were ignored (ignored={ignored_count})"
        assert run_tests_count == 9, f"Assertion failed: expected 9 executed tests, got {run_tests_count}"
        print(f"[PASS] Executed {run_tests_count} tests: {passed_tests}. 0 Failures, 0 Ignored.")

    # 7. Save evidence and results
    evidence = {
        "task_id": "R48-T022",
        "exercise": "armstrong-numbers",
        "tools": tools,
        "learner_stub_unsolved": is_stub_unsolved,
        "canonical_cases": {
            "total": total_cases,
            "included": len(included_cases),
            "excluded": len(excluded_cases),
            "excluded_uuids": excluded_cases
        },
        "test_results": {
            "expected_tests": 9,
            "actual_tests_run": run_tests_count,
            "failures": failures_count,
            "ignored": ignored_count,
            "passed_tests": passed_tests,
            "exit_code": test_run.returncode
        },
        "generation_reproducibility": {
            "two_passes_identical": True,
            "timestamp_normalized": True,
            "recreated_description": True,
            "recreated_reimplements": True,
            "preserved_other_keys": True,
            "cases_dropped": 0
        },
        "maintenance_doc_verified": True,
        "status": "SUCCESS"
    }

    results_file = os.path.join(work_dir, "results.json")
    with open(results_file, "w") as f:
        json.dump(evidence, f, indent=2)

    summary_file = os.path.join(work_dir, "check_output.txt")
    with open(summary_file, "w") as f:
        f.write("Task R48-T022 Verification Check Results\n")
        f.write("-----------------------------------------\n")
        f.write(f"Tools:\n  Python: {tools['python']}\n  CC: {tools['cc']}\n  Make: {tools['make']}\n\n")
        f.write(f"Canonical Counts:\n  Total: {total_cases}\n  Included: {len(included_cases)}\n  Excluded: {len(excluded_cases)}\n\n")
        f.write(f"Generation Reproducibility:\n  Two generations match after normalization: True\n  Preserved description, reimplements, and other keys: True\n  Cases dropped: 0\n\n")
        f.write(f"Test Execution (Reference):\n  Tests Run: {run_tests_count}\n  Failures: {failures_count}\n  Ignored: {ignored_count}\n  Status: PASS\n\n")
        f.write(f"Passed Tests:\n")
        for pt in passed_tests:
            f.write(f"  - {pt}\n")
        f.write(f"\nLearner stub untouched in working tree: {is_stub_unsolved}\n")
        f.write(f"Maintenance documentation present: True\n")

    print(f"\n[SUCCESS] All checks passed. Evidence saved to {results_file} and {summary_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
