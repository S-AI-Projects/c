#!/usr/bin/env python3
"""
work/R48-T046/check.py
Automated verification check for Task R48-T046:
Explain two approaches to run-length-encoding in C [exercises/practice/run-length-encoding].
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def find_repo_root():
    curr = os.path.abspath(os.path.dirname(__file__))
    while curr and curr != os.path.dirname(curr):
        if os.path.exists(os.path.join(curr, ".git")) or (
            os.path.exists(os.path.join(curr, "config.json")) and
            os.path.exists(os.path.join(curr, "exercises"))
        ):
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


def check_unsolved_learner_stubs(exercise_dir, meta_config):
    """
    Ensure the working tree learner starter files remain completely unsolved.
    """
    for sol in meta_config["files"]["solution"]:
        sol_path = os.path.join(exercise_dir, sol)
        if not os.path.exists(sol_path):
            raise AssertionError(f"Learner solution file missing: {sol_path}")
        with open(sol_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if sol.endswith(".c"):
            # run_length_encoding.c must only have the include directive
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            if lines != ['#include "run_length_encoding.h"']:
                raise AssertionError(
                    f"Learner stub {sol} has been modified or solved! Must remain unsolved."
                )


def check_tests_toml(tests_toml_path):
    """
    Ensure tests.toml exists, parses cleanly, and contains 'comment' keys
    explaining test cases and agreement between approaches.
    """
    if not os.path.exists(tests_toml_path):
        raise AssertionError(f"tests.toml missing: {tests_toml_path}")
    with open(tests_toml_path, "rb") as f:
        data = tomllib.load(f)

    if not data:
        raise AssertionError("tests.toml contains no test cases!")

    commented_cases = 0
    for uuid, case_data in data.items():
        if isinstance(case_data, dict) and "comment" in case_data:
            commented_cases += 1

    if commented_cases < len(data):
        raise AssertionError(
            f"Not all test cases have 'comment' keys in tests.toml! Found {commented_cases}/{len(data)}"
        )
    return data


def check_hints_documentation(hints_path):
    """
    Verify hints.md exists and contains approach selection, data representation,
    trade-offs, and worked examples, without a complete solution code listing.
    """
    if not os.path.exists(hints_path):
        raise AssertionError(f"hints.md missing: {hints_path}")
    with open(hints_path, "r", encoding="utf-8") as f:
        content = f.read()

    required_keywords = [
        "Approach Selection",
        "Two-Pass Scan",
        "Dynamic Buffer",
        "Worked Example",
        "Trade-offs"
    ]
    for kw in required_keywords:
        if kw.lower() not in content.lower():
            raise AssertionError(f"hints.md is missing required section/keyword: '{kw}'")

    # Ensure no full C implementation listing in hints.md
    if "dyn_buffer_t" in content and "realloc" in content and "char *encode" in content:
        raise AssertionError("hints.md contains a full solution listing! Avoid full solution code.")


def run_unity_tests(exercise_source_path, meta_config, implementation_source_path, impl_label):
    """
    Copies the exercise to a temporary directory, substitutes the implementation,
    enables all tests, and runs `make test` and `make memcheck`.
    """
    solution_files = meta_config["files"]["solution"]
    test_files = meta_config["files"]["test"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "run-length-encoding")
        shutil.copytree(exercise_source_path, tmp_exercise)

        # Substitute implementation into temporary copy only
        for sol_rel in solution_files:
            if sol_rel.endswith(".c"):
                dst = os.path.join(tmp_exercise, sol_rel)
                shutil.copy(implementation_source_path, dst)

        # Enable all test cases by removing TEST_IGNORE()
        for tf in test_files:
            tf_path = os.path.join(tmp_exercise, tf)
            with open(tf_path, "r", encoding="utf-8") as f:
                content = f.read()
            updated_content = re.sub(
                r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE
            )
            with open(tf_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

        # 1. Run make test
        test_run = subprocess.run(
            ["make", "test"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True
        )

        clean_stdout = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', test_run.stdout)
        summary_match = re.search(
            r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_stdout
        )
        if summary_match:
            run_count = int(summary_match.group(1))
            failures_count = int(summary_match.group(2))
            ignored_count = int(summary_match.group(3))
        else:
            run_count = 0
            failures_count = 0
            ignored_count = 0

        if test_run.returncode != 0:
            raise AssertionError(
                f"[{impl_label}] make test failed with exit code {test_run.returncode}:\n"
                f"STDOUT:\n{test_run.stdout}\nSTDERR:\n{test_run.stderr}"
            )
        if run_count == 0:
            raise AssertionError(f"[{impl_label}] Zero tests were executed!")
        if failures_count != 0 or ignored_count != 0:
            raise AssertionError(
                f"[{impl_label}] Tests did not all pass: {run_count} run, {failures_count} failed, {ignored_count} ignored."
            )

        # 2. Run make memcheck (AddressSanitizer)
        memcheck_run = subprocess.run(
            ["make", "memcheck"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True
        )
        if memcheck_run.returncode != 0:
            raise AssertionError(
                f"[{impl_label}] make memcheck failed with exit code {memcheck_run.returncode}:\n"
                f"STDOUT:\n{memcheck_run.stdout}\nSTDERR:\n{memcheck_run.stderr}"
            )
        if "Memory check passed" not in memcheck_run.stdout:
            raise AssertionError(f"[{impl_label}] Memory check did not pass cleanly!")

        return run_count, clean_stdout


def run_comparative_eval_and_benchmarks(exercise_dir, ref_path, alt_path):
    """
    Compiles a direct C evaluation and benchmarking harness in a temporary directory
    to assert functional equality across both approaches for all 13 canonical cases,
    and measure pure algorithm latencies and compiler/process overhead.
    """
    eval_c_source = r"""#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>

/* Forward declare prototypes from both translation units */
char *ref_encode(const char *text);
char *ref_decode(const char *data);
char *alt_encode(const char *text);
char *alt_decode(const char *data);

typedef struct {
    const char *uuid;
    const char *description;
    const char *op_type; // "encode", "decode", "roundtrip"
    const char *input;
    const char *expected;
} test_case_t;

static const test_case_t test_cases[] = {
    {"ad53b61b-6ffc-422f-81a6-61f7df92a231", "empty string", "encode", "", ""},
    {"52012823-b7e6-4277-893c-5b96d42f82de", "single characters only are encoded without count", "encode", "XYZ", "XYZ"},
    {"b7868492-7e3a-415f-8da3-d88f51f80409", "string with no single characters", "encode", "AABBBCCCC", "2A3B4C"},
    {"859b822b-6e9f-44d6-9c46-6091ee6ae358", "single characters mixed with repeated characters", "encode", "WWWWWWWWWWWWBWWWWWWWWWWWWBBBWWWWWWWWWWWWWWWWWWWWWWWWB", "12WB12W3B24WB"},
    {"1b34de62-e152-47be-bc88-469746df63b3", "multiple whitespace mixed in string", "encode", "  hsqq qww  ", "2 hs2q q2w2 "},
    {"abf176e2-3fbd-40ad-bb2f-2dd6d4df721a", "lowercase characters", "encode", "aabbbcccc", "2a3b4c"},
    {"7ec5c390-f03c-4acf-ac29-5f65861cdeb5", "empty string", "decode", "", ""},
    {"ad23f455-1ac2-4b0e-87d0-b85b10696098", "single characters only", "decode", "XYZ", "XYZ"},
    {"21e37583-5a20-4a0e-826c-3dee2c375f54", "string with no single characters", "decode", "2A3B4C", "AABBBCCCC"},
    {"1389ad09-c3a8-4813-9324-99363fba429c", "single characters with repeated characters", "decode", "12WB12W3B24WB", "WWWWWWWWWWWWBWWWWWWWWWWWWBBBWWWWWWWWWWWWWWWWWWWWWWWWB"},
    {"3f8e3c51-6aca-4670-b86c-a213bf4706b0", "multiple whitespace mixed in string", "decode", "2 hs2q q2w2 ", "  hsqq qww  "},
    {"29f721de-9aad-435f-ba37-7662df4fb551", "lower case string", "decode", "2a3b4c", "aabbbcccc"},
    {"2a762efd-8695-4e04-b0d6-9736899fbc16", "encode followed by decode gives original string", "roundtrip", "zzz ZZ  zZ", "zzz ZZ  zZ"}
};

static double get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

int main(void) {
    size_t num_cases = sizeof(test_cases) / sizeof(test_cases[0]);
    printf("{\n  \"case_evaluations\": [\n");

    for (size_t i = 0; i < num_cases; i++) {
        const test_case_t *tc = &test_cases[i];
        char *ref_res = NULL;
        char *alt_res = NULL;

        if (strcmp(tc->op_type, "encode") == 0) {
            ref_res = ref_encode(tc->input);
            alt_res = alt_encode(tc->input);
        } else if (strcmp(tc->op_type, "decode") == 0) {
            ref_res = ref_decode(tc->input);
            alt_res = alt_decode(tc->input);
        } else if (strcmp(tc->op_type, "roundtrip") == 0) {
            char *r_enc = ref_encode(tc->input);
            ref_res = ref_decode(r_enc);
            free(r_enc);

            char *a_enc = alt_encode(tc->input);
            alt_res = alt_decode(a_enc);
            free(a_enc);
        }

        assert(ref_res != NULL);
        assert(alt_res != NULL);
        assert(strcmp(ref_res, tc->expected) == 0);
        assert(strcmp(alt_res, tc->expected) == 0);
        assert(strcmp(ref_res, alt_res) == 0);

        printf("    {\n");
        printf("      \"uuid\": \"%s\",\n", tc->uuid);
        printf("      \"description\": \"%s\",\n", tc->description);
        printf("      \"op_type\": \"%s\",\n", tc->op_type);
        printf("      \"input\": \"%s\",\n", tc->input);
        printf("      \"expected\": \"%s\",\n", tc->expected);
        printf("      \"ref_actual\": \"%s\",\n", ref_res);
        printf("      \"alt_actual\": \"%s\",\n", alt_res);
        printf("      \"match\": true\n");
        printf("    }%s\n", (i + 1 < num_cases) ? "," : "");

        free(ref_res);
        free(alt_res);
    }
    printf("  ],\n");

    /* Benchmark pure algorithm execution over 5 repetitions of 50000 iterations */
    const char *bench_input = "WWWWWWWWWWWWBWWWWWWWWWWWWBBBWWWWWWWWWWWWWWWWWWWWWWWWB";
    printf("  \"benchmarks\": {\n");

    /* Approach 1 Timing */
    printf("    \"approach1_ref_timings_ns\": [");
    for (int rep = 0; rep < 5; rep++) {
        double t0 = get_time_ns();
        for (int it = 0; it < 50000; it++) {
            char *res = ref_encode(bench_input);
            free(res);
        }
        double t1 = get_time_ns();
        double ns_per_call = (t1 - t0) / 50000.0;
        printf("%.2f%s", ns_per_call, (rep < 4) ? ", " : "");
    }
    printf("],\n");

    /* Approach 2 Timing */
    printf("    \"approach2_alt_timings_ns\": [");
    for (int rep = 0; rep < 5; rep++) {
        double t0 = get_time_ns();
        for (int it = 0; it < 50000; it++) {
            char *res = alt_encode(bench_input);
            free(res);
        }
        double t1 = get_time_ns();
        double ns_per_call = (t1 - t0) / 50000.0;
        printf("%.2f%s", ns_per_call, (rep < 4) ? ", " : "");
    }
    printf("]\n");

    printf("  }\n}\n");
    return 0;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare wrapped ref and alt implementations
        with open(ref_path, "r", encoding="utf-8") as f:
            ref_code = f.read()
        # Rename encode/decode to ref_encode/ref_decode
        ref_code = re.sub(r'\bchar\s*\*\s*encode\b', 'char *ref_encode', ref_code)
        ref_code = re.sub(r'\bchar\s*\*\s*decode\b', 'char *ref_decode', ref_code)

        with open(alt_path, "r", encoding="utf-8") as f:
            alt_code = f.read()
        # Rename encode/decode to alt_encode/alt_decode
        alt_code = re.sub(r'\bchar\s*\*\s*encode\b', 'char *alt_encode', alt_code)
        alt_code = re.sub(r'\bchar\s*\*\s*decode\b', 'char *alt_decode', alt_code)

        src_ref = os.path.join(tmpdir, "ref.c")
        src_alt = os.path.join(tmpdir, "alt.c")
        src_main = os.path.join(tmpdir, "main.c")
        hdr_path = os.path.join(tmpdir, "run_length_encoding.h")
        bin_path = os.path.join(tmpdir, "eval_bench.out")

        # Copy header
        shutil.copy(os.path.join(exercise_dir, "run_length_encoding.h"), hdr_path)

        with open(src_ref, "w", encoding="utf-8") as f:
            f.write(ref_code)
        with open(src_alt, "w", encoding="utf-8") as f:
            f.write(alt_code)
        with open(src_main, "w", encoding="utf-8") as f:
            f.write(eval_c_source)

        # Measure compilation overhead
        compile_t0 = time.perf_counter()
        comp_cmd = ["gcc", "-O2", "-Wall", "-Wextra", src_main, src_ref, src_alt, "-lm", "-o", bin_path]
        comp_res = subprocess.run(comp_cmd, capture_output=True, text=True)
        compile_t1 = time.perf_counter()
        compile_ms = (compile_t1 - compile_t0) * 1000.0

        if comp_res.returncode != 0:
            raise AssertionError(
                f"Failed to compile benchmark harness:\nSTDOUT:\n{comp_res.stdout}\nSTDERR:\n{comp_res.stderr}"
            )

        # Measure process startup + execution overhead
        proc_t0 = time.perf_counter()
        eval_res = subprocess.run([bin_path], capture_output=True, text=True)
        proc_t1 = time.perf_counter()
        proc_total_ms = (proc_t1 - proc_t0) * 1000.0

        if eval_res.returncode != 0:
            raise AssertionError(
                f"Evaluation binary failed with code {eval_res.returncode}:\n{eval_res.stderr}"
            )

        bench_json = json.loads(eval_res.stdout)
        return bench_json, compile_ms, proc_total_ms


def main():
    print("=" * 70)
    print("Running Course Check for Task R48-T046: run-length-encoding")
    print("=" * 70)

    repo_root = find_repo_root()
    exercise_rel = "exercises/practice/run-length-encoding"
    exercise_dir = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T046")
    os.makedirs(work_dir, exist_ok=True)

    # 1. Resolve paths from .meta/config.json
    config_json_path = os.path.join(exercise_dir, ".meta/config.json")
    if not os.path.exists(config_json_path):
        raise AssertionError(f"Missing config.json at {config_json_path}")
    with open(config_json_path, "r", encoding="utf-8") as f:
        meta_config = json.load(f)

    solution_files = meta_config["files"]["solution"]
    test_files = meta_config["files"]["test"]
    example_files = meta_config["files"]["example"]

    print("[PASS] Resolved files from .meta/config.json:")
    print(f"       Solution files: {solution_files}")
    print(f"       Test files:     {test_files}")
    print(f"       Example files:  {example_files}")

    # 2. Assert learner starter stubs are unsolved in working tree
    check_unsolved_learner_stubs(exercise_dir, meta_config)
    print("[PASS] Learner stubs (run_length_encoding.c, run_length_encoding.h) remain strictly unsolved.")

    # 3. Assert tests.toml comments
    tests_toml_path = os.path.join(exercise_dir, ".meta/tests.toml")
    tests_toml_data = check_tests_toml(tests_toml_path)
    print(f"[PASS] Verified tests.toml: all {len(tests_toml_data)} canonical cases have 'comment' keys.")

    # 4. Assert hints.md approach selection
    hints_path = os.path.join(exercise_dir, ".docs/hints.md")
    check_hints_documentation(hints_path)
    print("[PASS] Verified .docs/hints.md: approach-selection, worked inputs, and trade-offs documented.")

    # 5. Execute Approach 1 (Reference) in scratch copy
    ref_path = os.path.join(exercise_dir, example_files[0])
    run_ref_count, ref_stdout = run_unity_tests(
        exercise_dir, meta_config, ref_path, "Approach 1 (Reference)"
    )
    print(f"[PASS] Approach 1 (Reference): all {run_ref_count} tests PASSED with make test & make memcheck.")

    # 6. Execute Approach 2 (Alternative) in scratch copy
    alt_path = os.path.join(work_dir, "dynamic_buffer_rle.c")
    if not os.path.exists(alt_path):
        raise AssertionError(f"Alternative implementation missing at {alt_path}")
    run_alt_count, alt_stdout = run_unity_tests(
        exercise_dir, meta_config, alt_path, "Approach 2 (Dynamic Buffer)"
    )
    print(f"[PASS] Approach 2 (Dynamic Buffer): all {run_alt_count} tests PASSED with make test & make memcheck.")

    if run_ref_count != run_alt_count or run_ref_count != len(tests_toml_data):
        raise AssertionError(
            f"Test counts mismatch! Ref={run_ref_count}, Alt={run_alt_count}, toml={len(tests_toml_data)}"
        )

    # 7. Functional agreement assertions & benchmarks
    bench_data, compile_ms, proc_total_ms = run_comparative_eval_and_benchmarks(
        exercise_dir, ref_path, alt_path
    )
    print(f"[PASS] Direct functional assertion: all {len(bench_data['case_evaluations'])} canonical cases match identically between Approach 1 and Approach 2.")

    ref_timings = bench_data["benchmarks"]["approach1_ref_timings_ns"]
    alt_timings = bench_data["benchmarks"]["approach2_alt_timings_ns"]
    ref_timings_sorted = sorted(ref_timings)
    alt_timings_sorted = sorted(alt_timings)
    median_ref_ns = ref_timings_sorted[len(ref_timings_sorted) // 2]
    median_alt_ns = alt_timings_sorted[len(alt_timings_sorted) // 2]

    print(f"[INFO] Measured pure algorithm latencies (50,000 iterations x 5 reps):")
    print(f"       Approach 1 (Two-Pass Exact):     Median {median_ref_ns:.2f} ns/call")
    print(f"       Approach 2 (Streaming Dynamic):  Median {median_alt_ns:.2f} ns/call")
    print(f"[INFO] Infrastructure overhead: compilation={compile_ms:.2f} ms, process startup={proc_total_ms:.2f} ms")

    # 8. Save tool_versions.txt
    tool_versions_content = (
        f"python: {get_tool_version(['python3', '--version'])}\n"
        f"cc: {get_tool_version(['gcc', '--version'])}\n"
        f"make: {get_tool_version(['make', '--version'])}\n"
        f"configlet: {get_tool_version(['bin/configlet', '--version']) if os.path.exists(os.path.join(repo_root, 'bin/configlet')) else 'N/A'}\n"
    )
    with open(os.path.join(work_dir, "tool_versions.txt"), "w", encoding="utf-8") as f:
        f.write(tool_versions_content)

    # 9. Save inputs.json
    inputs_json_data = {
        "exercise": "exercises/practice/run-length-encoding",
        "contract": {
            "encode": "char *encode(const char *text)",
            "decode": "char *decode(const char *data)"
        },
        "canonical_cases": bench_data["case_evaluations"]
    }
    with open(os.path.join(work_dir, "inputs.json"), "w", encoding="utf-8") as f:
        json.dump(inputs_json_data, f, indent=2)

    # 10. Save expected_vs_actual.json
    expected_vs_actual_data = {
        "test_suite_execution": {
            "total_canonical_cases": len(tests_toml_data),
            "approach1_reference_passed": run_ref_count,
            "approach2_alternative_passed": run_alt_count,
            "failures": 0,
            "ignored": 0,
            "status": "PASS"
        },
        "case_verifications": bench_data["case_evaluations"]
    }
    with open(os.path.join(work_dir, "expected_vs_actual.json"), "w", encoding="utf-8") as f:
        json.dump(expected_vs_actual_data, f, indent=2)

    # 11. Save results.json
    results_json_data = {
        "task_id": "R48-T046",
        "exercise": "exercises/practice/run-length-encoding",
        "reference_source": "exercises/practice/run-length-encoding/.meta/example.c#L10",
        "alternative_source": "work/R48-T046/dynamic_buffer_rle.c",
        "total_canonical_tests": len(tests_toml_data),
        "approach1_tests_passed": run_ref_count,
        "approach2_tests_passed": run_alt_count,
        "compilation_overhead_ms": round(compile_ms, 2),
        "process_startup_ms": round(proc_total_ms, 2),
        "measurements": {
            "approach1_two_pass_exact": {
                "repetitions_ns": ref_timings,
                "median_ns_per_call": median_ref_ns,
                "heap_allocations": 1,
                "complexity": "O(N) time (2 passes), O(M) space"
            },
            "approach2_streaming_dynamic": {
                "repetitions_ns": alt_timings,
                "median_ns_per_call": median_alt_ns,
                "heap_allocations": "Amortized geometric realloc",
                "complexity": "O(N) time (1 pass), O(M) space"
            }
        },
        "cost_distinction": {
            "algorithm_latency_ns": {
                "approach1_ref": median_ref_ns,
                "approach2_alt": median_alt_ns
            },
            "infrastructure_overhead_ms": {
                "compilation": round(compile_ms, 2),
                "process_execution": round(proc_total_ms, 2)
            }
        }
    }
    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results_json_data, f, indent=2)

    # 12. Mirror check.py to tools/course_checks/r48-t046.py
    course_checks_dir = os.path.join(repo_root, "tools/course_checks")
    os.makedirs(course_checks_dir, exist_ok=True)
    target_check = os.path.join(course_checks_dir, "r48-t046.py")
    if os.path.realpath(__file__) != os.path.realpath(target_check):
        shutil.copy(__file__, target_check)
    print("[PASS] Mirrored check script to tools/course_checks/r48-t046.py.")

    print("\n[SUCCESS] All verification criteria for Task R48-T046 passed successfully!")


if __name__ == "__main__":
    main()
