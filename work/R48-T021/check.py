#!/usr/bin/env python3
"""
Verification check for Task R48-T021:
Explain the canonical-case decisions for resistor-color [exercises/practice/resistor-color]
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

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/resistor-color"
    exercise_path = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T021")
    os.makedirs(work_dir, exist_ok=True)

    print("=== Running R48-T021 Verification Check ===")

    # 1. Collect tool versions
    tools = {
        "python": sys.version.split()[0],
        "cc": get_tool_version(["cc", "--version"]),
        "make": get_tool_version(["make", "--version"])
    }
    print(f"Tool versions: Python {tools['python']}, CC: {tools['cc']}, Make: {tools['make']}")

    # 2. Verify learner stub is unsolved in working tree
    learner_c = os.path.join(exercise_path, "resistor_color.c")
    learner_h = os.path.join(exercise_path, "resistor_color.h")
    with open(learner_c, "r") as f:
        learner_c_content = f.read()
    with open(learner_h, "r") as f:
        learner_h_content = f.read()

    # Learner header has an empty enum and no function declarations
    is_stub_unsolved = ("typedef enum {\n\n} resistor_band_t;" in learner_h_content or
                        "typedef enum {\n} resistor_band_t;" in learner_h_content or
                        "color_code" not in learner_h_content)
    assert is_stub_unsolved, "Assertion failed: Learner stub appears modified or solved in working tree!"
    print("[PASS] Working tree learner stub is unsolved.")

    # 3. Load config.json
    config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(config_file, "r") as f:
        config = json.load(f)

    solution_files = config["files"]["solution"]
    test_files = config["files"]["test"]
    example_files = config["files"]["example"]
    print(f"[INFO] Resolved files from config.json: solutions={solution_files}, tests={test_files}, examples={example_files}")

    # 4. Parse tests.toml and validate UUID rationales
    tests_toml_file = os.path.join(exercise_path, ".meta/tests.toml")
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    target_uuids = {
        "49eb31c5-10a8-4180-9f7f-fea632ab87ef": {
            "name": "Black",
            "test": "test_black",
            "keywords": ["test_black", "black", "0"]
        },
        "0a4df94b-92da-4579-a907-65040ce0b3fc": {
            "name": "White",
            "test": "test_white",
            "keywords": ["test_white", "white", "9"]
        },
        "5f81608d-f36f-4190-8084-f45116b6f380": {
            "name": "Orange",
            "test": "test_orange",
            "keywords": ["test_orange", "orange", "3"]
        }
    }

    # Count included/excluded
    total_canonical_cases = len(toml_data)
    included_count = 0
    excluded_count = 0
    rationales = {}

    for uuid, entry in toml_data.items():
        is_included = entry.get("include", True)
        if is_included:
            included_count += 1
        else:
            excluded_count += 1

    for uuid, spec in target_uuids.items():
        assert uuid in toml_data, f"Assertion failed: UUID {uuid} missing from tests.toml"
        entry = toml_data[uuid]
        assert "comment" in entry and entry["comment"].strip(), f"Assertion failed: comment key missing for UUID {uuid}"
        comment_text = entry["comment"]
        for kw in spec["keywords"]:
            assert kw.lower() in comment_text.lower(), f"Assertion failed: keyword '{kw}' missing from comment for UUID {uuid}"
        rationales[uuid] = {
            "description": entry.get("description"),
            "comment": comment_text
        }
        print(f"[PASS] Validated rationale for UUID {uuid} ({spec['name']}) -> {comment_text}")

    # Included/excluded counts
    counts = {
        "total_cases": total_canonical_cases,
        "included_cases": included_count,
        "excluded_cases": excluded_count,
        "changed_inclusions": 0
    }
    print(f"[INFO] Canonical case counts: Total={total_canonical_cases}, Included={included_count}, Excluded={excluded_count}")

    # 5. Substitute reference only in a temporary copy and run make test
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "resistor-color")
        shutil.copytree(exercise_path, tmp_exercise)

        # Substitute reference files
        for sol_rel, ex_rel in zip(solution_files, example_files):
            src_example = os.path.join(tmp_exercise, ex_rel)
            dst_solution = os.path.join(tmp_exercise, sol_rel)
            shutil.copy(src_example, dst_solution)
        print("[INFO] Substituted reference example files into temporary exercise copy.")

        # Enable all tests by stripping TEST_IGNORE() from test files
        for tf in test_files:
            tf_path = os.path.join(tmp_exercise, tf)
            with open(tf_path, "r") as f:
                content = f.read()
            # Remove TEST_IGNORE(); calls
            updated_content = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w") as f:
                f.write(updated_content)
        print("[INFO] Enabled all test cases in temporary copy.")

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

        # Strip ANSI escape codes
        clean_stdout = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', stdout)

        # Check returncode
        assert test_run.returncode == 0, f"Assertion failed: make test failed with exit code {test_run.returncode}!\nStderr: {stderr}"

        # Parse test outcomes
        passed_tests = re.findall(r':(test_\w+):PASS', clean_stdout)
        summary_match = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_stdout)
        assert summary_match is not None, "Assertion failed: could not parse Unity test summary output"

        run_tests_count = int(summary_match.group(1))
        failures_count = int(summary_match.group(2))
        ignored_count = int(summary_match.group(3))

        assert run_tests_count > 0, f"Assertion failed: zero tests executed (run={run_tests_count})"
        assert failures_count == 0, f"Assertion failed: test failures detected (failures={failures_count})"
        assert ignored_count == 0, f"Assertion failed: tests were ignored (ignored={ignored_count})"
        assert run_tests_count == 4, f"Assertion failed: expected 4 executed tests, got {run_tests_count}"
        print(f"[PASS] Executed {run_tests_count} tests: {passed_tests}. 0 Failures, 0 Ignored.")

    # 6. Save inputs, expected vs actual results, tool versions, and evidence
    evidence = {
        "task_id": "R48-T021",
        "exercise": "resistor-color",
        "tools": tools,
        "learner_stub_unsolved": is_stub_unsolved,
        "canonical_counts": counts,
        "uuids_rationales": rationales,
        "test_results": {
            "expected_tests": 4,
            "actual_tests_run": run_tests_count,
            "failures": failures_count,
            "ignored": ignored_count,
            "passed_tests": passed_tests,
            "exit_code": test_run.returncode
        },
        "status": "SUCCESS"
    }

    results_file = os.path.join(work_dir, "results.json")
    with open(results_file, "w") as f:
        json.dump(evidence, f, indent=2)

    summary_file = os.path.join(work_dir, "check_output.txt")
    with open(summary_file, "w") as f:
        f.write(f"Task R48-T021 Verification Check Results\n")
        f.write(f"-----------------------------------------\n")
        f.write(f"Tools:\n  Python: {tools['python']}\n  CC: {tools['cc']}\n  Make: {tools['make']}\n\n")
        f.write(f"Canonical Counts:\n  Total: {counts['total_cases']}\n  Included: {counts['included_cases']}\n  Excluded: {counts['excluded_cases']}\n\n")
        f.write(f"Test Execution (Reference):\n  Tests Run: {run_tests_count}\n  Failures: {failures_count}\n  Ignored: {ignored_count}\n  Status: PASS\n\n")
        f.write(f"UUID Rationales:\n")
        for u, r in rationales.items():
            f.write(f"  [{u}] ({r['description']}):\n    {r['comment']}\n")
        f.write(f"\nLearner stub untouched in working tree: {is_stub_unsolved}\n")

    print(f"\n[SUCCESS] All checks passed. Evidence saved to {results_file} and {summary_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
