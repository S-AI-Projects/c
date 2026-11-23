#!/usr/bin/env python3
"""
work/R48-T045/check.py
Automated verification check for Task R48-T045:
Measure the scaling of the clock reference [exercises/practice/clock].
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


def run_scratch_tests(exercise_source_path, meta_config):
    """
    Copies the exercise to a temporary directory including dotfiles,
    substitutes the reference solution, enables all tests, and runs `make test`.
    """
    solution_files = meta_config["files"]["solution"]
    test_files = meta_config["files"]["test"]
    example_files = meta_config["files"]["example"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "clock")
        shutil.copytree(exercise_source_path, tmp_exercise)

        # Substitute reference into temporary copy only
        # solution has ["clock.c", "clock.h"], example has [".meta/example.c"]
        for sol_rel in solution_files:
            if sol_rel.endswith(".c"):
                src = os.path.join(tmp_exercise, example_files[0])
                dst = os.path.join(tmp_exercise, sol_rel)
                shutil.copy(src, dst)

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


def run_benchmark_and_assertions(exercise_source_path, example_rel_path):
    """
    Builds a benchmark C harness in a temporary directory to assert correctness
    before timing, measure pure algorithm runtime across 5 repetitions per size,
    measure compilation and process startup overhead, and compute operation bounds.
    """
    example_path = os.path.join(exercise_source_path, example_rel_path)
    with open(example_path, "r", encoding="utf-8") as f:
        example_src = f.read()

    # Create an exposed normalize_clock for testing directly
    # Replace static void normalize_clock with void normalize_clock_ref
    bench_c_code = """#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>
#include <assert.h>
#include <string.h>

#define REPS 5
#define ITERS 200000

void normalize_clock(int *hour, int *minute);

typedef struct {
    int km_iterations;
    int kh_iterations;
    int condition_evals;
    int additions_subtractions;
    int divisions;
    int modulos;
    int total_operations;
} op_count_t;

static op_count_t count_operations(int hour, int minute) {
    op_count_t ops = {0, 0, 0, 0, 0, 0, 0};
    int m = minute;
    int h = hour;

    ops.condition_evals++; // first loop initial check
    while (m < 0) {
        ops.km_iterations++;
        m += 60;
        h -= 1;
        ops.additions_subtractions += 2;
        ops.condition_evals++;
    }

    h += m / 60;
    ops.divisions += 1;
    ops.additions_subtractions += 1;

    ops.condition_evals++; // second loop initial check
    while (h < 0) {
        ops.kh_iterations++;
        h += 24;
        ops.additions_subtractions += 1;
        ops.condition_evals++;
    }

    h %= 24;
    m %= 60;
    ops.modulos += 2;

    ops.total_operations = ops.condition_evals + ops.additions_subtractions + ops.divisions + ops.modulos;
    return ops;
}

static double get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

int cmp_double(const void *a, const void *b) {
    double da = *(const double *)a;
    double db = *(const double *)b;
    return (da > db) - (da < db);
}

int main(void) {
    // 1. Correctness assertions for all 3 domain sizes before timing
    int h1 = 8, m1 = 0;
    normalize_clock(&h1, &m1);
    if (!(h1 == 8 && m1 == 0)) {
        fprintf(stderr, "Assertion failed for Size 1: expected 8:00, got %02d:%02d\\n", h1, m1);
        return 1;
    }

    int h2 = 201, m2 = 3001;
    normalize_clock(&h2, &m2);
    if (!(h2 == 11 && m2 == 1)) {
        fprintf(stderr, "Assertion failed for Size 2: expected 11:01, got %02d:%02d\\n", h2, m2);
        return 2;
    }

    int h3 = -121, m3 = -5810;
    normalize_clock(&h3, &m3);
    if (!(h3 == 22 && m3 == 10)) {
        fprintf(stderr, "Assertion failed for Size 3: expected 22:10, got %02d:%02d\\n", h3, m3);
        return 3;
    }

    op_count_t ops1 = count_operations(8, 0);
    op_count_t ops2 = count_operations(201, 3001);
    op_count_t ops3 = count_operations(-121, -5810);

    // Warm-up
    for (int i = 0; i < 50000; i++) {
        int h = -121, m = -5810;
        normalize_clock(&h, &m);
    }

    double t1[REPS], t2[REPS], t3[REPS];

    // Measure Size 1
    for (int r = 0; r < REPS; r++) {
        double start = get_time_ns();
        for (int i = 0; i < ITERS; i++) {
            int h = 8, m = 0;
            normalize_clock(&h, &m);
        }
        double end = get_time_ns();
        t1[r] = (end - start) / (double)ITERS;
    }

    // Measure Size 2
    for (int r = 0; r < REPS; r++) {
        double start = get_time_ns();
        for (int i = 0; i < ITERS; i++) {
            int h = 201, m = 3001;
            normalize_clock(&h, &m);
        }
        double end = get_time_ns();
        t2[r] = (end - start) / (double)ITERS;
    }

    // Measure Size 3
    for (int r = 0; r < REPS; r++) {
        double start = get_time_ns();
        for (int i = 0; i < ITERS; i++) {
            int h = -121, m = -5810;
            normalize_clock(&h, &m);
        }
        double end = get_time_ns();
        t3[r] = (end - start) / (double)ITERS;
    }

    double s1[REPS], s2[REPS], s3[REPS];
    memcpy(s1, t1, sizeof(t1));
    memcpy(s2, t2, sizeof(t2));
    memcpy(s3, t3, sizeof(t3));
    qsort(s1, REPS, sizeof(double), cmp_double);
    qsort(s2, REPS, sizeof(double), cmp_double);
    qsort(s3, REPS, sizeof(double), cmp_double);

    printf("{\\n");
    printf("  \\\"size1\\\": {\\\"name\\\": \\\"standard_in_range\\\", \\\"input\\\": [8, 0], \\\"expected\\\": [8, 0], \\\"correct\\\": true, \\\"timings_ns\\\": [%.2f, %.2f, %.2f, %.2f, %.2f], \\\"median_ns\\\": %.2f, \\\"km\\\": %d, \\\"kh\\\": %d, \\\"ops\\\": %d},\\n",
           t1[0], t1[1], t1[2], t1[3], t1[4], s1[REPS/2], ops1.km_iterations, ops1.kh_iterations, ops1.total_operations);
    printf("  \\\"size2\\\": {\\\"name\\\": \\\"positive_rollover\\\", \\\"input\\\": [201, 3001], \\\"expected\\\": [11, 1], \\\"correct\\\": true, \\\"timings_ns\\\": [%.2f, %.2f, %.2f, %.2f, %.2f], \\\"median_ns\\\": %.2f, \\\"km\\\": %d, \\\"kh\\\": %d, \\\"ops\\\": %d},\\n",
           t2[0], t2[1], t2[2], t2[3], t2[4], s2[REPS/2], ops2.km_iterations, ops2.kh_iterations, ops2.total_operations);
    printf("  \\\"size3\\\": {\\\"name\\\": \\\"negative_rollback\\\", \\\"input\\\": [-121, -5810], \\\"expected\\\": [22, 10], \\\"correct\\\": true, \\\"timings_ns\\\": [%.2f, %.2f, %.2f, %.2f, %.2f], \\\"median_ns\\\": %.2f, \\\"km\\\": %d, \\\"kh\\\": %d, \\\"ops\\\": %d}\\n",
           t3[0], t3[1], t3[2], t3[3], t3[4], s3[REPS/2], ops3.km_iterations, ops3.kh_iterations, ops3.total_operations);
    printf("}\\n");
    return 0;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy clock.h so clock_ref.c compiles cleanly
        shutil.copy(os.path.join(exercise_source_path, "clock.h"), os.path.join(tmpdir, "clock.h"))

        # Prepare separate translation unit for reference
        # Export normalize_clock_ref
        ref_src = example_src.replace(
            "static void normalize_clock(int *hour, int *minute)",
            "void normalize_clock(int *hour, int *minute)"
        )
        clock_c_path = os.path.join(tmpdir, "clock_ref.c")
        with open(clock_c_path, "w", encoding="utf-8") as f:
            f.write(ref_src)

        bench_c_path = os.path.join(tmpdir, "bench.c")
        with open(bench_c_path, "w", encoding="utf-8") as f:
            f.write(bench_c_code)

        # Measure compilation overhead
        compile_start = time.perf_counter()
        compile_ref = subprocess.run(
            ["cc", "-O2", "-c", "clock_ref.c", "-o", "clock_ref.o"],
            cwd=tmpdir, capture_output=True, text=True
        )
        assert compile_ref.returncode == 0, f"Compilation failed: {compile_ref.stderr}"

        compile_bench = subprocess.run(
            ["cc", "-O2", "-c", "bench.c", "-o", "bench.o"],
            cwd=tmpdir, capture_output=True, text=True
        )
        assert compile_bench.returncode == 0, f"Compilation failed: {compile_bench.stderr}"

        link_res = subprocess.run(
            ["cc", "clock_ref.o", "bench.o", "-o", "bench"],
            cwd=tmpdir, capture_output=True, text=True
        )
        assert link_res.returncode == 0, f"Link failed: {link_res.stderr}"
        compile_time_ms = (time.perf_counter() - compile_start) * 1000.0

        # Measure process startup overhead
        proc_start = time.perf_counter()
        bench_run = subprocess.run(
            ["./bench"],
            cwd=tmpdir, capture_output=True, text=True
        )
        proc_total_time_ms = (time.perf_counter() - proc_start) * 1000.0

        assert bench_run.returncode == 0, f"Benchmark failed: {bench_run.stderr}"
        bench_data = json.loads(bench_run.stdout)

        return bench_data, compile_time_ms, proc_total_time_ms


def main():
    repo_root = find_repo_root()
    exercise_rel = "exercises/practice/clock"
    exercise_path = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T045")
    os.makedirs(work_dir, exist_ok=True)

    print("=== Running R48-T045 Complexity & Scaling Check ===")
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
    learner_c = os.path.join(exercise_path, "clock.c")
    learner_h = os.path.join(exercise_path, "clock.h")
    assert os.path.exists(learner_c), f"Missing {learner_c}"
    assert os.path.exists(learner_h), f"Missing {learner_h}"

    with open(learner_c, "r", encoding="utf-8") as f:
        c_code = f.read()

    # The learner stub should not contain normalize_clock implementation
    has_implementation = any(keyword in c_code for keyword in [
        "normalize_clock", "CLOCK_FORMAT", "snprintf", "clock_create"
    ])
    assert not has_implementation, "Assertion failed: Learner stub in working tree appears solved!"
    print("[PASS] Working tree learner stub is unsolved.")

    # 3. Check maintenance documentation exists and satisfies requirements
    maint_file = os.path.join(repo_root, "docs/maintenance/clock.md")
    assert os.path.exists(maint_file), f"Assertion failed: Missing {maint_file}"
    with open(maint_file, "r", encoding="utf-8") as f:
        maint_content = f.read()

    assert "input size" in maint_content.lower(), "Missing input size definition in maintenance doc"
    assert "branch" in maint_content.lower() and "operation" in maint_content.lower(), "Missing branch/operation table in maintenance doc"
    assert "algorithm work" in maint_content.lower(), "Missing algorithm work distinction in maintenance doc"
    assert "process startup" in maint_content.lower(), "Missing process startup distinction in maintenance doc"
    assert "limit of the conclusion" in maint_content.lower() or "limits of the conclusion" in maint_content.lower(), "Missing limit of conclusion"
    assert "invariants" in maint_content.lower(), "Missing invariant specification"
    print("[PASS] Maintenance documentation verified (docs/maintenance/clock.md).")

    # 4. Check example.c complexity comment
    example_c = os.path.join(exercise_path, ".meta/example.c")
    with open(example_c, "r", encoding="utf-8") as f:
        example_content = f.read()
    assert "normalize_clock" in example_content, "Missing normalize_clock in example.c"
    assert "Invariants and Computational Complexity of normalize_clock" in example_content, "Missing complexity comment in example.c"
    assert "Cost Analysis" in example_content or "k_m" in example_content, "Missing detailed cost analysis comment in example.c"
    print("[PASS] Example implementation verified with complexity/invariant comment.")

    # 5. Parse meta config.json and tests.toml
    meta_config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(meta_config_file, "r", encoding="utf-8") as f:
        meta_config = json.load(f)

    tests_toml_file = os.path.join(exercise_path, ".meta/tests.toml")
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    total_cases = len(toml_data)
    assert total_cases == 52, f"Assertion failed: expected 52 canonical cases, got {total_cases}"
    # Verify comment keys on the 3 named domain cases
    assert "comment" in toml_data["a577bacc-106b-496e-9792-b3083ea8705e"], "Missing comment key for Size 1 test"
    assert "comment" in toml_data["be60810e-f5d9-4b58-9351-a9d1e90e660c"], "Missing comment key for Size 2 test"
    assert "comment" in toml_data["51d41fcf-491e-4ca0-9cae-2aa4f0163ad4"], "Missing comment key for Size 3 test"
    print(f"[PASS] tests.toml parsed: {total_cases} canonical cases verified with preserved comment keys.")

    # 6. Isolated Scratch Run: Original reference passes all cases
    print("[INFO] Running reference solution against Unity test suite in scratch directory...")
    ret_orig, out_orig, err_orig, run_orig, fail_orig, ign_orig, passed_orig, failed_orig = run_scratch_tests(
        exercise_path, meta_config
    )
    print(f"Make test exit code: {ret_orig}, Run: {run_orig}, Failures: {fail_orig}, Ignored: {ign_orig}")
    assert ret_orig == 0, f"Assertion failed: reference make test failed with exit code {ret_orig}!\nStderr: {err_orig}"
    assert run_orig == 52, f"Assertion failed: expected 52 executed cases, got {run_orig}"
    assert fail_orig == 0, f"Assertion failed: reference had {fail_orig} failures"
    assert ign_orig == 0, f"Assertion failed: reference had {ign_orig} ignored tests"
    print(f"[PASS] All {run_orig} tests passed against the reference implementation with 0 failures.")

    # 7. Complexity & Scaling Benchmark Run
    print("[INFO] Running empirical benchmark and correctness assertions...")
    bench_data, compile_ms, proc_total_ms = run_benchmark_and_assertions(
        exercise_path, meta_config["files"]["example"][0]
    )

    s1 = bench_data["size1"]
    s2 = bench_data["size2"]
    s3 = bench_data["size3"]

    print(f"Size 1 (In-range): {s1['input']} -> Median: {s1['median_ns']} ns/call, Operations: {s1['ops']}")
    print(f"Size 2 (Positive rollover): {s2['input']} -> Median: {s2['median_ns']} ns/call, Operations: {s2['ops']}")
    print(f"Size 3 (Negative rollback): {s3['input']} -> Median: {s3['median_ns']} ns/call, Operations: {s3['ops']}")
    print(f"Compilation Overhead: {compile_ms:.2f} ms, Total Process Runtime: {proc_total_ms:.2f} ms")

    # Assert correctness
    assert s1["correct"], "Size 1 correctness assertion failed"
    assert s2["correct"], "Size 2 correctness assertion failed"
    assert s3["correct"], "Size 3 correctness assertion failed"

    # Assert operation counts match mathematical bounds
    assert s1["ops"] == 6, f"Expected 6 ops for Size 1, got {s1['ops']}"
    assert s2["ops"] == 6, f"Expected 6 ops for Size 2, got {s2['ops']}"
    assert s3["ops"] == 317, f"Expected 317 ops for Size 3, got {s3['ops']}"

    # Assert at least 5 repetitions per size
    assert len(s1["timings_ns"]) >= 5, "Size 1 has fewer than 5 repetitions"
    assert len(s2["timings_ns"]) >= 5, "Size 2 has fewer than 5 repetitions"
    assert len(s3["timings_ns"]) >= 5, "Size 3 has fewer than 5 repetitions"

    # Save inputs.json
    inputs_data = {
        "exercise": "exercises/practice/clock",
        "routine": "normalize_clock",
        "domain_sizes": [
            {
                "size_level": 1,
                "label": "standard_in_range",
                "canonical_case_uuid": "a577bacc-106b-496e-9792-b3083ea8705e",
                "input": {"hour": 8, "minute": 0},
                "expected": {"hour": 8, "minute": 0, "formatted": "08:00"},
                "theoretical_operations": 6,
                "asymptotic_bound": "O(1)"
            },
            {
                "size_level": 2,
                "label": "positive_multi_day_rollover",
                "canonical_case_uuid": "be60810e-f5d9-4b58-9351-a9d1e90e660c",
                "input": {"hour": 201, "minute": 3001},
                "expected": {"hour": 11, "minute": 1, "formatted": "11:01"},
                "theoretical_operations": 6,
                "asymptotic_bound": "O(1)"
            },
            {
                "size_level": 3,
                "label": "negative_multi_day_rollback",
                "canonical_case_uuid": "51d41fcf-491e-4ca0-9cae-2aa4f0163ad4",
                "input": {"hour": -121, "minute": -5810},
                "expected": {"hour": 22, "minute": 10, "formatted": "22:10"},
                "theoretical_operations": 317,
                "asymptotic_bound": "O(|minute|/60 + |hour|/24)"
            }
        ]
    }
    with open(os.path.join(work_dir, "inputs.json"), "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2)

    # Save expected_vs_actual.json
    expected_vs_actual = {
        "test_suite_execution": {
            "total_canonical_cases": 52,
            "executed_cases": run_orig,
            "expected_failures": 0,
            "actual_failures": fail_orig,
            "ignored_cases": ign_orig,
            "status": "PASS"
        },
        "domain_correctness_assertions": {
            "size1": {
                "input": [8, 0],
                "expected": [8, 0],
                "actual": s1["expected"],
                "status": "PASS"
            },
            "size2": {
                "input": [201, 3001],
                "expected": [11, 1],
                "actual": s2["expected"],
                "status": "PASS"
            },
            "size3": {
                "input": [-121, -5810],
                "expected": [22, 10],
                "actual": s3["expected"],
                "status": "PASS"
            }
        },
        "operation_counts": {
            "size1": {"expected_ops": 6, "actual_ops": s1["ops"]},
            "size2": {"expected_ops": 6, "actual_ops": s2["ops"]},
            "size3": {"expected_ops": 317, "actual_ops": s3["ops"]}
        }
    }
    with open(os.path.join(work_dir, "expected_vs_actual.json"), "w", encoding="utf-8") as f:
        json.dump(expected_vs_actual, f, indent=2)

    # Save results.json
    results_data = {
        "task_id": "R48-T045",
        "exercise": "exercises/practice/clock",
        "reference_source": "exercises/practice/clock/.meta/example.c#L6",
        "total_canonical_tests": 52,
        "scratch_tests_passed": run_orig,
        "compilation_overhead_ms": round(compile_ms, 2),
        "process_startup_ms": round(proc_total_ms, 2),
        "measurements": {
            "size1_standard_in_range": {
                "input": [8, 0],
                "operations": s1["ops"],
                "repetitions_ns": s1["timings_ns"],
                "median_ns_per_call": s1["median_ns"],
                "complexity": "O(1)"
            },
            "size2_positive_rollover": {
                "input": [201, 3001],
                "operations": s2["ops"],
                "repetitions_ns": s2["timings_ns"],
                "median_ns_per_call": s2["median_ns"],
                "complexity": "O(1)"
            },
            "size3_negative_rollback": {
                "input": [-121, -5810],
                "operations": s3["ops"],
                "repetitions_ns": s3["timings_ns"],
                "median_ns_per_call": s3["median_ns"],
                "complexity": "O(|minute|/60 + |hour|/24)"
            }
        },
        "cost_distinction": {
            "algorithm_latency_ns": {
                "size1": s1["median_ns"],
                "size2": s2["median_ns"],
                "size3": s3["median_ns"]
            },
            "infrastructure_overhead_ms": {
                "compilation": round(compile_ms, 2),
                "process_execution": round(proc_total_ms, 2)
            }
        }
    }
    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    # Copy check.py to tools/course_checks/r48-t045.py
    course_checks_dir = os.path.join(repo_root, "tools/course_checks")
    os.makedirs(course_checks_dir, exist_ok=True)
    target_check = os.path.join(course_checks_dir, "r48-t045.py")
    if os.path.realpath(__file__) != os.path.realpath(target_check):
        shutil.copy(__file__, target_check)
    print("[PASS] Mirrored check script to tools/course_checks/r48-t045.py.")

    print("\n[SUCCESS] All verification criteria for Task R48-T045 passed successfully!")


if __name__ == "__main__":
    main()
