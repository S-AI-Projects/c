#!/usr/bin/env python3
"""
work/R48-T047/check.py
Automated verification check for Task R48-T047:
Add C-specific guidance for nucleotide-count [exercises/practice/nucleotide-count].
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


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


def check_working_tree_stubs(repo_root, solution_files):
    """
    Verify that learner starter stub files in the working tree are completely unsolved.
    """
    stubs_unsolved = True
    for sol_rel in solution_files:
        sol_path = os.path.join(repo_root, "exercises", "practice", "nucleotide-count", sol_rel)
        if not os.path.exists(sol_path):
            return False, f"Missing solution stub file: {sol_path}"
        with open(sol_path, "r", encoding="utf-8") as f:
            content = f.read()

        # nucleotide_count.c should only contain #include "nucleotide_count.h" or empty
        if sol_rel.endswith(".c"):
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            if len(lines) > 2 or any("count(" in l for l in lines):
                stubs_unsolved = False
                return False, f"Learner stub {sol_rel} appears modified or solved"
        # nucleotide_count.h should not contain reference implementation
        elif sol_rel.endswith(".h"):
            if "calloc" in content or "snprintf" in content:
                stubs_unsolved = False
                return False, f"Header stub {sol_rel} contains implementation details"

    return stubs_unsolved, "Working tree stubs remain completely unsolved"


def run_reference_tests(repo_root, exercise_rel_path, meta_config):
    """
    Copies exercise including dotfiles to a temp dir, substitutes reference implementation,
    enables all tests, and runs `make test` and `make memcheck`.
    """
    src_dir = os.path.join(repo_root, exercise_rel_path)
    solution_files = meta_config["files"]["solution"]
    test_files = meta_config["files"]["test"]
    example_files = meta_config["files"]["example"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "nucleotide-count")
        shutil.copytree(src_dir, tmp_exercise)

        # Substitute reference implementation only in scratch copy
        for sol_rel, ex_rel in zip(solution_files, example_files):
            src_file = os.path.join(tmp_exercise, ex_rel)
            dst_file = os.path.join(tmp_exercise, sol_rel)
            shutil.copy(src_file, dst_file)

        # Enable all test cases by stripping TEST_IGNORE()
        for tf in test_files:
            tf_path = os.path.join(tmp_exercise, tf)
            with open(tf_path, "r", encoding="utf-8") as f:
                content = f.read()
            updated_content = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

        # Run make test
        test_run = subprocess.run(
            ["make", "test"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True
        )

        clean_stdout = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', test_run.stdout)
        summary_match = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_stdout)
        if summary_match:
            run_count = int(summary_match.group(1))
            failures_count = int(summary_match.group(2))
            ignored_count = int(summary_match.group(3))
        else:
            run_count = 0
            failures_count = 0
            ignored_count = 0

        passed_tests = re.findall(r':(test_\w+):PASS', clean_stdout)
        failed_tests = re.findall(r':(test_\w+):FAIL', clean_stdout)

        # Run make memcheck to verify address sanitizer and zero memory leaks
        memcheck_run = subprocess.run(
            ["make", "memcheck"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True
        )

        return {
            "make_test_returncode": test_run.returncode,
            "make_test_stdout": clean_stdout,
            "make_test_stderr": test_run.stderr,
            "run_count": run_count,
            "failures_count": failures_count,
            "ignored_count": ignored_count,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "make_memcheck_returncode": memcheck_run.returncode,
            "memcheck_passed": "Memory check passed" in memcheck_run.stdout
        }


def run_and_verify_micro_example(repo_root):
    """
    Extracts the micro-example C source from hints.md, compiles it with AddressSanitizer,
    runs it, and asserts both outputs.
    """
    hints_path = os.path.join(repo_root, "exercises", "practice", "nucleotide-count", ".docs", "hints.md")
    with open(hints_path, "r", encoding="utf-8") as f:
        hints_content = f.read()

    # Extract C code block from Standalone Micro-Example section
    section_match = re.search(r'## Standalone Micro-Example.*?(```c\n(.*?)```)', hints_content, re.DOTALL)
    assert section_match, "Failed to extract micro-example C code block from hints.md"
    c_source = section_match.group(2)

    with tempfile.TemporaryDirectory() as tmpdir:
        src_file = os.path.join(tmpdir, "micro_example.c")
        exe_file = os.path.join(tmpdir, "micro_example")

        with open(src_file, "w", encoding="utf-8") as f:
            f.write(c_source)

        compile_cmd = ["clang", "-std=c99", "-Wall", "-Wextra", "-Werror", "-fsanitize=address", src_file, "-o", exe_file]
        compile_run = subprocess.run(compile_cmd, capture_output=True, text=True)
        if compile_run.returncode != 0:
            # Fallback to cc if clang has platform differences
            compile_cmd[0] = "cc"
            compile_run = subprocess.run(compile_cmd, capture_output=True, text=True)

        assert compile_run.returncode == 0, f"Micro-example compilation failed:\n{compile_run.stderr}"

        exec_run = subprocess.run([exe_file], capture_output=True, text=True)
        assert exec_run.returncode == 0, f"Micro-example execution failed with code {exec_run.returncode}:\n{exec_run.stderr}"

        output_lines = [l.strip() for l in exec_run.stdout.splitlines() if l.strip()]

        out1_line = next((l for l in output_lines if l.startswith("Output 1")), None)
        out2_line = next((l for l in output_lines if l.startswith("Output 2")), None)

        expected_out1 = "Output 1 (valid): A:3"
        expected_out2 = "Output 2 (invalid):"

        assert out1_line == expected_out1, f"Output 1 mismatch: expected '{expected_out1}', got '{out1_line}'"
        assert out2_line == expected_out2, f"Output 2 mismatch: expected '{expected_out2}', got '{out2_line}'"

        # Check published hint agreement
        assert expected_out1 in hints_content, f"Published hint does not contain expected '{expected_out1}'"
        assert expected_out2 in hints_content, f"Published hint does not contain expected '{expected_out2}'"

        return {
            "c_source": c_source,
            "compile_returncode": compile_run.returncode,
            "exec_returncode": exec_run.returncode,
            "raw_output": exec_run.stdout,
            "out1_actual": out1_line,
            "out1_expected": expected_out1,
            "out2_actual": out2_line,
            "out2_expected": expected_out2,
            "agreement_with_hint": True
        }


def verify_hints_guidance(repo_root):
    """
    Verify that hints.md names the constructs, explains relevance, and links language references.
    """
    hints_path = os.path.join(repo_root, "exercises", "practice", "nucleotide-count", ".docs", "hints.md")
    assert os.path.exists(hints_path), f"hints.md not found at {hints_path}"

    with open(hints_path, "r", encoding="utf-8") as f:
        content = f.read()

    constructs_found = {
        "array_lengths": "array lengths" in content.lower(),
        "null_termination": "null termination" in content.lower(),
        "caller_callee_ownership": "caller/callee memory ownership" in content.lower() or "memory ownership" in content.lower(),
        "calloc_construct": "calloc" in content,
        "free_function": "free(" in content,
        "reference_line_citation": "example.c" in content,
        "language_reference_link": "https://" in content and ("cppreference" in content or "open-std" in content or "opengroup" in content)
    }

    for k, v in constructs_found.items():
        assert v, f"Guidance check failed: missing {k} in hints.md"

    # Verify tests.toml preserved comments
    tests_toml_path = os.path.join(repo_root, "exercises", "practice", "nucleotide-count", ".meta", "tests.toml")
    with open(tests_toml_path, "r", encoding="utf-8") as f:
        toml_content = f.read()

    comments_present = toml_content.count("comment =") >= 5
    assert comments_present, "tests.toml is missing required 'comment' keys for test cases"

    return constructs_found


def main():
    repo_root = find_repo_root()
    exercise_rel = os.path.join("exercises", "practice", "nucleotide-count")
    meta_config_path = os.path.join(repo_root, exercise_rel, ".meta", "config.json")

    with open(meta_config_path, "r", encoding="utf-8") as f:
        meta_config = json.load(f)

    work_dir = os.path.join(repo_root, "work", "R48-T047")
    os.makedirs(work_dir, exist_ok=True)

    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("=" * 70)
    log("Task R48-T047: Add C-specific guidance for nucleotide-count")
    log("=" * 70)

    # 1. Check working tree learner stubs
    stubs_ok, stubs_msg = check_working_tree_stubs(repo_root, meta_config["files"]["solution"])
    assert stubs_ok, f"Assertion failed: {stubs_msg}"
    log(f"[PASS] Working tree stubs check: {stubs_msg}")

    # 2. Run reference test suite in isolated scratch copy
    test_results = run_reference_tests(repo_root, exercise_rel, meta_config)
    assert test_results["make_test_returncode"] == 0, f"make test failed with return code {test_results['make_test_returncode']}"
    assert test_results["run_count"] == 5, f"Expected 5 tests executed, got {test_results['run_count']}"
    assert test_results["failures_count"] == 0, f"Expected 0 failures, got {test_results['failures_count']}"
    assert test_results["ignored_count"] == 0, f"Expected 0 ignored, got {test_results['ignored_count']}"
    assert test_results["make_memcheck_returncode"] == 0, f"make memcheck failed: {test_results['make_memcheck_returncode']}"
    assert test_results["memcheck_passed"], "Memory check failed or ASan detected errors"
    log(f"[PASS] Reference test suite: {test_results['run_count']} tests passed, 0 failures, 0 ignored, memory clean")

    # 3. Micro-example execution and output assertions
    micro_results = run_and_verify_micro_example(repo_root)
    log(f"[PASS] Micro-example compiled & executed cleanly under ASan")
    log(f"       {micro_results['out1_actual']}")
    log(f"       {micro_results['out2_actual']}")
    log(f"[PASS] Both micro-example outputs agree with published hint in hints.md")

    # 4. Guidance and construct verification
    guidance_results = verify_hints_guidance(repo_root)
    log(f"[PASS] Guidance document verifies all constructs (array lengths, null termination, memory ownership)")
    log(f"[PASS] tests.toml comments preserved for all 5 canonical cases")

    # Tool versions
    tool_versions = {
        "python": sys.version.split()[0],
        "cc": get_tool_version(["clang", "--version"]) if shutil.which("clang") else get_tool_version(["cc", "--version"]),
        "make": get_tool_version(["make", "--version"]),
        "configlet": get_tool_version([os.path.join(repo_root, "bin", "configlet"), "--version"])
    }

    tool_versions_file = os.path.join(work_dir, "tool_versions.txt")
    with open(tool_versions_file, "w", encoding="utf-8") as f:
        for k, v in tool_versions.items():
            f.write(f"{k}: {v}\n")

    # Inputs JSON
    inputs_data = {
        "exercise": "nucleotide-count",
        "task_id": "R48-T047",
        "canonical_cases_count": 5,
        "config_json": meta_config,
        "constructs_examined": [
            "array lengths",
            "null termination",
            "caller/callee memory ownership"
        ],
        "chosen_construct": {
            "name": "caller/callee memory ownership with dynamic heap allocation (calloc)",
            "location": "exercises/practice/nucleotide-count/.meta/example.c#L16",
            "code": "static const int max_length = 50; char *count_results = calloc(1, max_length);"
        },
        "micro_example_inputs": [
            {
                "label": "standard_valid_input",
                "nucleotide": "A",
                "count": 3,
                "expected_output": "Output 1 (valid): A:3"
            },
            {
                "label": "contrasting_invalid_input",
                "nucleotide": "X",
                "count": 0,
                "expected_output": "Output 2 (invalid):"
            }
        ],
        "canonical_test_cases": [
            {"uuid": "3e5c30a8-87e2-4845-a815-a49671ade970", "description": "empty strand", "expected": "A:0 C:0 G:0 T:0"},
            {"uuid": "a0ea42a6-06d9-4ac6-828c-7ccaccf98fec", "description": "can count one nucleotide in single-character input", "expected": "A:0 C:0 G:1 T:0"},
            {"uuid": "eca0d565-ed8c-43e7-9033-6cefbf5115b5", "description": "strand with repeated nucleotide", "expected": "A:0 C:0 G:7 T:0"},
            {"uuid": "40a45eac-c83f-4740-901a-20b22d15a39f", "description": "strand with multiple nucleotides", "expected": "A:20 C:12 G:17 T:21"},
            {"uuid": "b4c47851-ee9e-4b0a-be70-a86e343bd851", "description": "strand with invalid nucleotides", "expected": ""}
        ]
    }
    with open(os.path.join(work_dir, "inputs.json"), "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2)

    # Expected vs Actual JSON
    expected_vs_actual = {
        "learner_stub_unsolved": {
            "expected": True,
            "actual": stubs_ok,
            "pass": stubs_ok
        },
        "canonical_test_suite": {
            "expected_tests_run": 5,
            "actual_tests_run": test_results["run_count"],
            "expected_failures": 0,
            "actual_failures": test_results["failures_count"],
            "expected_ignored": 0,
            "actual_ignored": test_results["ignored_count"],
            "expected_returncode": 0,
            "actual_returncode": test_results["make_test_returncode"],
            "memcheck_passed": test_results["memcheck_passed"],
            "pass": True
        },
        "micro_example_assertions": {
            "output_1": {
                "expected": micro_results["out1_expected"],
                "actual": micro_results["out1_actual"],
                "pass": micro_results["out1_expected"] == micro_results["out1_actual"]
            },
            "output_2": {
                "expected": micro_results["out2_expected"],
                "actual": micro_results["out2_actual"],
                "pass": micro_results["out2_expected"] == micro_results["out2_actual"]
            },
            "hints_agreement": {
                "expected": True,
                "actual": micro_results["agreement_with_hint"],
                "pass": micro_results["agreement_with_hint"]
            }
        },
        "guidance_checks": {
            "constructs_verified": guidance_results,
            "pass": True
        }
    }
    with open(os.path.join(work_dir, "expected_vs_actual.json"), "w", encoding="utf-8") as f:
        json.dump(expected_vs_actual, f, indent=2)

    # Results JSON
    results_data = {
        "task_id": "R48-T047",
        "exercise": "nucleotide-count",
        "status": "SUCCESS",
        "tests_passed": test_results["run_count"],
        "tests_failed": test_results["failures_count"],
        "tests_ignored": test_results["ignored_count"],
        "memcheck_status": "PASSED",
        "micro_example_status": "PASSED",
        "learner_stubs_intact": True,
        "construct_identified": "calloc (caller/callee memory ownership & null termination)",
        "tool_versions": tool_versions
    }
    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    # Check output log
    with open(os.path.join(work_dir, "check_output.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    log("=" * 70)
    log("ALL CHECKS PASSED: Task R48-T047 verification complete")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
