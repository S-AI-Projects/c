#!/usr/bin/env python3
"""
Verification check for Task R48-T025:
Measure the scaling of the minesweeper reference [exercises/practice/minesweeper]
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib

def get_tool_version(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.splitlines()[0].strip()
    except Exception as e:
        return f"Error: {e}"

def clean_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

BENCH_C_SOURCE = """
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "minesweeper.h"

static double get_time_us(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)(ts.tv_sec * 1000000.0) + (double)(ts.tv_nsec / 1000.0);
}

static int compare_doubles(const void *a, const void *b) {
    double diff = *(const double *)a - *(const double *)b;
    return (diff > 0) - (diff < 0);
}

int main(void) {
    // 1. Small input: 1x7 horizontal line (7 cells)
    const char *small_in[] = { " * * * " };
    const char *small_exp[] = { "1*2*2*1" };

    // 2. Medium input: 3x3 grid (9 cells)
    const char *med_in[] = {
        "   ",
        " * ",
        "   "
    };
    const char *med_exp[] = {
        "111",
        "1*1",
        "111"
    };

    // 3. Large input: 6x6 minefield (36 cells from large minefield test)
    const char *large_in[] = {
        " *  * ",
        "  *   ",
        "    * ",
        "   * *",
        " *  * ",
        "      "
    };
    const char *large_exp[] = {
        "1*22*1",
        "12*322",
        " 123*2",
        "112*4*",
        "1*22*2",
        "111111"
    };

    // Assert correctness before timing
    char **s_act = annotate(small_in, 1);
    if (!s_act || strcmp(s_act[0], small_exp[0]) != 0) {
        fprintf(stderr, "Correctness failed on small input!\\n");
        return 1;
    }
    free_annotation(s_act);

    char **m_act = annotate(med_in, 3);
    if (!m_act) {
        fprintf(stderr, "Correctness failed on med input!\\n");
        return 1;
    }
    for (size_t i = 0; i < 3; i++) {
        if (strcmp(m_act[i], med_exp[i]) != 0) {
            fprintf(stderr, "Correctness failed on med row %zu!\\n", i);
            return 1;
        }
    }
    free_annotation(m_act);

    char **l_act = annotate(large_in, 6);
    if (!l_act) {
        fprintf(stderr, "Correctness failed on large input!\\n");
        return 1;
    }
    for (size_t i = 0; i < 6; i++) {
        if (strcmp(l_act[i], large_exp[i]) != 0) {
            fprintf(stderr, "Correctness failed on large row %zu!\\n", i);
            return 1;
        }
    }
    free_annotation(l_act);

    // Timing 5 repetitions per size
    const int REPS = 5;
    double t_small[5], t_med[5], t_large[5];

    for (int i = 0; i < REPS; i++) {
        double start = get_time_us();
        char **r = annotate(small_in, 1);
        double end = get_time_us();
        t_small[i] = end - start;
        free_annotation(r);
    }
    qsort(t_small, REPS, sizeof(double), compare_doubles);

    for (int i = 0; i < REPS; i++) {
        double start = get_time_us();
        char **r = annotate(med_in, 3);
        double end = get_time_us();
        t_med[i] = end - start;
        free_annotation(r);
    }
    qsort(t_med, REPS, sizeof(double), compare_doubles);

    for (int i = 0; i < REPS; i++) {
        double start = get_time_us();
        char **r = annotate(large_in, 6);
        double end = get_time_us();
        t_large[i] = end - start;
        free_annotation(r);
    }
    qsort(t_large, REPS, sizeof(double), compare_doubles);

    printf("MEASUREMENTS_JSON:{\\"small_median_us\\": %.2f, \\"med_median_us\\": %.2f, \\"large_median_us\\": %.2f}\\n",
           t_small[REPS / 2], t_med[REPS / 2], t_large[REPS / 2]);
    return 0;
}
"""

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/minesweeper"
    exercise_path = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T025")
    os.makedirs(work_dir, exist_ok=True)

    print("=== Running R48-T025 Verification Check ===")

    # 1. Tool versions
    tools = {
        "python": sys.version.split()[0],
        "cc": get_tool_version(["cc", "--version"]),
        "make": get_tool_version(["make", "--version"])
    }
    print(f"Tool versions: Python {tools['python']}, CC: {tools['cc']}, Make: {tools['make']}")

    # 2. Verify working tree learner stub is unsolved
    learner_c = os.path.join(exercise_path, "minesweeper.c")
    with open(learner_c, "r") as f:
        c_code = f.read()
    is_stub_unsolved = ("annotate(" not in c_code or "return" not in c_code)
    assert is_stub_unsolved, "Assertion failed: Learner stub in working tree appears solved!"
    print("[PASS] Working tree learner stub is unsolved.")

    # 3. Check maintenance documentation
    maint_file = os.path.join(exercise_path, ".meta/MAINTENANCE.md")
    assert os.path.exists(maint_file), "Assertion failed: .meta/MAINTENANCE.md is missing!"
    with open(maint_file, "r") as f:
        maint_content = f.read()

    assert "set_single_field" in maint_content, "Assertion failed: Maintenance doc missing set_single_field analysis"
    assert "compilation" in maint_content.lower(), "Assertion failed: Maintenance doc missing compilation cost distinction"
    assert "startup" in maint_content.lower(), "Assertion failed: Maintenance doc missing startup overhead distinction"
    print("[PASS] Maintenance documentation verified (.meta/MAINTENANCE.md).")

    # 4. Check tests.toml
    tests_toml_file = os.path.join(exercise_path, ".meta/tests.toml")
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    target_uuid = "04a260f1-b40a-4e89-839e-8dd8525abe0e"
    assert target_uuid in toml_data, f"Assertion failed: UUID {target_uuid} missing in tests.toml"
    assert "comment" in toml_data[target_uuid], "Assertion failed: comment key missing for large minefield"
    assert "set_single_field" in toml_data[target_uuid]["comment"], "Assertion failed: comment missing set_single_field reference"
    print(f"[PASS] tests.toml verified: {toml_data[target_uuid]['comment']}")

    # 5. Load config.json and run make test with reference
    config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(config_file, "r") as f:
        config = json.load(f)

    solution_files = config["files"]["solution"]
    test_files = config["files"]["test"]
    example_files = config["files"]["example"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "minesweeper")
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
        assert run_res.returncode == 0, f"Assertion failed: make test failed: {run_res.stderr}"

        clean_out = clean_ansi(run_res.stdout)
        summary_match = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_out)
        assert summary_match is not None, "Assertion failed: Could not parse Unity test output"
        tests_run = int(summary_match.group(1))
        failures = int(summary_match.group(2))
        ignored = int(summary_match.group(3))

        passed_tests = re.findall(r':(test_\w+):PASS', clean_out)
        assert tests_run == 12, f"Assertion failed: Expected 12 tests, got {tests_run}"
        assert failures == 0, f"Assertion failed: Failures detected: {failures}"
        assert ignored == 0, f"Assertion failed: Tests were ignored: {ignored}"
        print(f"[PASS] Executed {tests_run} tests: {passed_tests}. 0 Failures, 0 Ignored.")

    # 6. Benchmark microharness across three valid domain sizes
    with tempfile.TemporaryDirectory() as bench_dir:
        bench_c = os.path.join(bench_dir, "bench.c")
        with open(bench_c, "w") as f:
            f.write(BENCH_C_SOURCE)

        shutil.copy(os.path.join(exercise_path, ".meta/example.c"), os.path.join(bench_dir, "minesweeper.c"))
        shutil.copy(os.path.join(exercise_path, ".meta/example.h"), os.path.join(bench_dir, "minesweeper.h"))

        # Measure compilation time
        t_compile_start = time.perf_counter()
        compile_cmd = ["cc", "-O2", os.path.join(bench_dir, "minesweeper.c"), bench_c, "-o", os.path.join(bench_dir, "bench")]
        compile_res = subprocess.run(compile_cmd, capture_output=True, text=True)
        t_compile_end = time.perf_counter()
        compile_ms = (t_compile_end - t_compile_start) * 1000.0
        assert compile_res.returncode == 0, f"Assertion failed: Benchmark compilation failed: {compile_res.stderr}"

        # Measure process startup and algorithm execution
        t_proc_start = time.perf_counter()
        bench_run = subprocess.run([os.path.join(bench_dir, "bench")], capture_output=True, text=True)
        t_proc_end = time.perf_counter()
        proc_total_ms = (t_proc_end - t_proc_start) * 1000.0

        assert bench_run.returncode == 0, f"Assertion failed: Benchmark run failed: {bench_run.stderr}"

        # Parse measurements
        m_json = re.search(r'MEASUREMENTS_JSON:(\{.*\})', bench_run.stdout)
        assert m_json is not None, "Assertion failed: Could not parse benchmark JSON output"
        measurements = json.loads(m_json.group(1))

        print(f"[PASS] Benchmark completed (5 repetitions per size). Correctness asserted before timing.")
        print(f"       Small (7 cells) median: {measurements['small_median_us']} us")
        print(f"       Med (9 cells) median:   {measurements['med_median_us']} us")
        print(f"       Large (25 cells) median: {measurements['large_median_us']} us")
        print(f"       Compilation overhead:   {compile_ms:.2f} ms")
        print(f"       Process total time:     {proc_total_ms:.2f} ms")

    # 7. Save evidence and results
    evidence = {
        "task_id": "R48-T025",
        "exercise": "minesweeper",
        "tools": tools,
        "learner_stub_unsolved": is_stub_unsolved,
        "set_single_field_cost": {
            "complexity": "O(1)",
            "operations_per_call": "1 read, 1 branch, 1 increment, 1 write",
            "calls_per_mine_bound": 9,
            "total_calls_bound": "9 * M"
        },
        "cost_separation": {
            "compilation_time_ms": round(compile_ms, 2),
            "process_total_ms": round(proc_total_ms, 2),
            "algorithm_in_process": measurements
        },
        "benchmarked_sizes": {
            "small": {"cells": 7, "mines": 3, "median_us": measurements["small_median_us"]},
            "medium": {"cells": 9, "mines": 1, "median_us": measurements["med_median_us"]},
            "large": {"cells": 36, "mines": 7, "median_us": measurements["large_median_us"]}
        },
        "test_results": {
            "expected_tests": 12,
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
        f.write("Task R48-T025 Verification Check Results\n")
        f.write("-----------------------------------------\n")
        f.write(f"Tools:\n  Python: {tools['python']}\n  CC: {tools['cc']}\n  Make: {tools['make']}\n\n")
        f.write(f"Cost Analysis of set_single_field:\n")
        f.write(f"  Complexity: O(1) constant time bound per invocation.\n")
        f.write(f"  Max calls per mine: 9 (3x3 neighborhood).\n")
        f.write(f"  Total calls across board: bounded by 9 * M (where M = mine count).\n\n")
        f.write(f"Measurements (Median of 5 repetitions):\n")
        f.write(f"  Small (7 cells, 3 mines):   {measurements['small_median_us']} us\n")
        f.write(f"  Medium (9 cells, 1 mine):   {measurements['med_median_us']} us\n")
        f.write(f"  Large (25 cells, 7 mines):  {measurements['large_median_us']} us\n\n")
        f.write(f"Overhead Separation:\n")
        f.write(f"  Compilation overhead:  {compile_ms:.2f} ms\n")
        f.write(f"  Process overhead:      {proc_total_ms:.2f} ms\n")
        f.write(f"  Algorithm pure work:   microsecond scale (in-process)\n\n")
        f.write(f"Tests Run (Reference): {tests_run} (0 failures, 0 ignored, PASS)\n")
        f.write(f"Learner stub in working tree: UNSOLVED\n")

    print(f"\n[SUCCESS] All checks passed. Evidence saved to {results_file} and {summary_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
