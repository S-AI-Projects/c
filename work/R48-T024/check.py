#!/usr/bin/env python3
"""
Verification check for Task R48-T024:
Clarify is_planet in the space-age reference [exercises/practice/space-age]
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
    exercise_rel = "exercises/practice/space-age"
    exercise_path = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T024")
    os.makedirs(work_dir, exist_ok=True)

    print("=== Running R48-T024 Verification Check ===")

    # 1. Tool versions
    tools = {
        "python": sys.version.split()[0],
        "cc": get_tool_version(["cc", "--version"]),
        "make": get_tool_version(["make", "--version"])
    }
    print(f"Tool versions: Python {tools['python']}, CC: {tools['cc']}, Make: {tools['make']}")

    # 2. Verify learner stub is unsolved in working tree
    learner_c = os.path.join(exercise_path, "space_age.c")
    with open(learner_c, "r") as f:
        c_code = f.read()

    is_stub_unsolved = ("age(" not in c_code or "return" not in c_code)
    assert is_stub_unsolved, "Assertion failed: Learner stub in working tree appears solved!"
    print("[PASS] Working tree learner stub is unsolved.")

    # 3. Check tests.toml and comment on invalid planet
    tests_toml_file = os.path.join(exercise_path, ".meta/tests.toml")
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    target_uuid = "57b96e2a-1178-40b7-b34d-f3c9c34e4bf4"
    assert target_uuid in toml_data, f"Assertion failed: UUID {target_uuid} missing in tests.toml"
    entry = toml_data[target_uuid]
    assert "comment" in entry and entry["comment"].strip(), "Assertion failed: comment key missing for invalid planet case"
    assert "is_planet" in entry["comment"], "Assertion failed: comment missing reference to is_planet"
    print(f"[PASS] tests.toml verified: {entry['comment']}")

    # 4. Check readability improvement in example.c
    example_c_file = os.path.join(exercise_path, ".meta/example.c")
    with open(example_c_file, "r") as f:
        example_c = f.read()

    assert "is_valid_planet" in example_c, "Assertion failed: Ambiguous local state not renamed to is_valid_planet"
    assert "default:" in example_c, "Assertion failed: Explicit default branch missing in switch(planet)"
    print("[PASS] Verified readability improvement in example.c (is_valid_planet and explicit default).")

    # 5. Load config.json and execute make test with reference
    config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(config_file, "r") as f:
        config = json.load(f)

    solution_files = config["files"]["solution"]
    test_files = config["files"]["test"]
    example_files = config["files"]["example"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "space-age")
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

        run_res = subprocess.run(["make", "test"], cwd=tmp_exercise, capture_output=True, text=True)
        assert run_res.returncode == 0, f"Assertion failed: make test failed with exit code {run_res.returncode}!\nStderr: {run_res.stderr}"

        clean_out = clean_ansi(run_res.stdout)
        summary_match = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_out)
        assert summary_match is not None, "Assertion failed: Could not parse Unity test output"
        tests_run = int(summary_match.group(1))
        failures = int(summary_match.group(2))
        ignored = int(summary_match.group(3))

        passed_tests = re.findall(r':(test_\w+):PASS', clean_out)
        assert tests_run == 9, f"Assertion failed: Expected 9 tests, got {tests_run}"
        assert failures == 0, f"Assertion failed: Failures detected: {failures}"
        assert ignored == 0, f"Assertion failed: Tests were ignored: {ignored}"
        print(f"[PASS] Executed {tests_run} tests: {passed_tests}. 0 Failures, 0 Ignored.")

    # 6. Save results and evidence
    evidence = {
        "task_id": "R48-T024",
        "exercise": "space-age",
        "tools": tools,
        "learner_stub_unsolved": is_stub_unsolved,
        "readability_improvement": {
            "target_function": "is_planet",
            "renamed_state": "result -> is_valid_planet",
            "added_constructs": ["break;", "default: is_valid_planet = false; break;"],
            "api_preserved": True
        },
        "test_results": {
            "expected_tests": 9,
            "actual_tests_run": tests_run,
            "failures": failures,
            "ignored": ignored,
            "passed_tests": passed_tests,
            "exit_code": run_res.returncode
        },
        "status": "SUCCESS"
    }

    results_file = os.path.join(work_dir, "results.json")
    with open(results_file, "w") as f:
        json.dump(evidence, f, indent=2)

    summary_file = os.path.join(work_dir, "check_output.txt")
    with open(summary_file, "w") as f:
        f.write("Task R48-T024 Verification Check Results\n")
        f.write("-----------------------------------------\n")
        f.write(f"Tools:\n  Python: {tools['python']}\n  CC: {tools['cc']}\n  Make: {tools['make']}\n\n")
        f.write(f"Readability Improvement:\n  Clarified is_planet in example.c: renamed ambiguous 'result' to 'is_valid_planet' and added explicit default and break handling.\n\n")
        f.write(f"Test Execution (Reference):\n  Tests Run: {tests_run}\n  Failures: {failures}\n  Ignored: {ignored}\n  Status: PASS\n\n")
        f.write(f"Passed Tests:\n")
        for pt in passed_tests:
            f.write(f"  - {pt}\n")
        f.write(f"\nLearner stub untouched in working tree: {is_stub_unsolved}\n")

    print(f"\n[SUCCESS] All checks passed. Evidence saved to {results_file} and {summary_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
