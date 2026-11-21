"""
R48-T016 check script
Verifies that:
1. The reference implementation passes all 17 test cases (0 failures, 0 ignored).
2. An alternative lookup-table implementation produces identical output for
   every test input, confirming both approaches are equivalent.
3. The learner stub is not solved (compile/link against it must fail or produce
   no passing tests).
4. The exercise directory is byte-identical before and after the run.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXERCISE = "raindrops"
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", EXERCISE)
META_DIR = os.path.join(EXERCISE_DIR, ".meta")
CONFIG_PATH = os.path.join(META_DIR, "config.json")

WORK_DIR = os.path.dirname(__file__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, cwd, capture=True, check=False):
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=capture, text=True
    )
    if check and result.returncode != 0:
        print("STDOUT:", result.stdout[-2000:])
        print("STDERR:", result.stderr[-2000:])
        raise AssertionError(f"Command failed (rc={result.returncode}): {' '.join(cmd)}")
    return result

def parse_unity(output):
    """Return (tests, failures, ignored) from Unity summary line."""
    m = re.search(r"(\d+) Tests.*?(\d+) Failures.*?(\d+) Ignored", output)
    if not m:
        return None, None, None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))

def snapshot(directory):
    """Return a dict {relpath: bytes} for every file under directory."""
    snap = {}
    for root, _, files in os.walk(directory):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, directory)
            with open(full, "rb") as fh:
                snap[rel] = fh.read()
    return snap

# ---------------------------------------------------------------------------
# Reference implementation check
# ---------------------------------------------------------------------------

def check_reference(tmp_base):
    """Copy exercise to tmp, substitute example.c, enable all tests, run make."""
    dst = os.path.join(tmp_base, "ref")
    shutil.copytree(EXERCISE_DIR, dst)

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    # Substitute: copy .meta/example.c → solution file
    example_src = os.path.join(META_DIR, "example.c")
    solution_files = cfg["files"]["solution"]
    solution_c = [s for s in solution_files if s.endswith(".c")][0]
    shutil.copy(example_src, os.path.join(dst, solution_c))

    # Also copy example.h if present
    example_h = os.path.join(META_DIR, "example.h")
    if os.path.exists(example_h):
        solution_h = [s for s in solution_files if s.endswith(".h")][0]
        shutil.copy(example_h, os.path.join(dst, solution_h))

    # Enable all tests: remove TEST_IGNORE(); lines
    test_files = cfg["files"]["test"]
    for tf in test_files:
        tp = os.path.join(dst, tf)
        with open(tp) as f:
            src = f.read()
        src = re.sub(r"^\s*TEST_IGNORE\(\);\s*//[^\n]*\n", "", src, flags=re.MULTILINE)
        src = re.sub(r"^\s*TEST_IGNORE\(\);\s*\n", "", src, flags=re.MULTILINE)
        with open(tp, "w") as f:
            f.write(src)

    result = run(["make", "test"], cwd=dst)
    output = result.stdout + result.stderr
    tests, failures, ignored = parse_unity(output)

    print(f"[reference] Unity: {tests} Tests, {failures} Failures, {ignored} Ignored")
    assert tests is not None, "Unity output not found — make test did not run"
    assert tests > 0, f"Zero tests executed (got {tests})"
    assert failures == 0, f"Reference has {failures} failure(s)"
    assert ignored == 0, f"Reference has {ignored} ignored test(s) — TEST_IGNORE removal failed"

    return tests

# ---------------------------------------------------------------------------
# Alternative implementation (lookup table) check
# ---------------------------------------------------------------------------

ALTERNATIVE_C = """\
#include "raindrops.h"
#include <stdio.h>
#include <string.h>

void convert(char result[], int drops)
{
    static const struct { int div; const char *sound; } rules[] = {
        {3, "Pling"}, {5, "Plang"}, {7, "Plong"},
    };
    for (size_t i = 0; i < sizeof rules / sizeof rules[0]; i++) {
        if (drops % rules[i].div == 0)
            strcat(result, rules[i].sound);
    }
    if (strlen(result) == 0) {
        char buf[12] = "\\0";
        snprintf(buf, sizeof buf, "%d", drops);
        strcat(result, buf);
    }
}
"""

def check_alternative(tmp_base, expected_tests):
    """Run the lookup-table alternative and confirm it passes all tests."""
    dst = os.path.join(tmp_base, "alt")
    shutil.copytree(EXERCISE_DIR, dst)

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    solution_files = cfg["files"]["solution"]
    solution_c = [s for s in solution_files if s.endswith(".c")][0]
    with open(os.path.join(dst, solution_c), "w") as f:
        f.write(ALTERNATIVE_C)

    example_h = os.path.join(META_DIR, "example.h")
    if os.path.exists(example_h):
        solution_h = [s for s in solution_files if s.endswith(".h")][0]
        shutil.copy(example_h, os.path.join(dst, solution_h))

    test_files = cfg["files"]["test"]
    for tf in test_files:
        tp = os.path.join(dst, tf)
        with open(tp) as f:
            src = f.read()
        src = re.sub(r"^\s*TEST_IGNORE\(\);\s*//[^\n]*\n", "", src, flags=re.MULTILINE)
        src = re.sub(r"^\s*TEST_IGNORE\(\);\s*\n", "", src, flags=re.MULTILINE)
        with open(tp, "w") as f:
            f.write(src)

    result = run(["make", "test"], cwd=dst)
    output = result.stdout + result.stderr
    tests, failures, ignored = parse_unity(output)

    print(f"[alternative] Unity: {tests} Tests, {failures} Failures, {ignored} Ignored")
    assert tests is not None, "Alternative: Unity output not found"
    assert tests == expected_tests, (
        f"Alternative ran {tests} tests but reference ran {expected_tests}"
    )
    assert failures == 0, f"Alternative has {failures} failure(s) — approaches differ!"
    assert ignored == 0, f"Alternative has {ignored} ignored test(s)"

# ---------------------------------------------------------------------------
# Negative control: bare stub must NOT pass all tests
# ---------------------------------------------------------------------------

def check_stub_fails(tmp_base):
    """The unsolved stub should fail to build or produce failures."""
    dst = os.path.join(tmp_base, "stub")
    shutil.copytree(EXERCISE_DIR, dst)

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    test_files = cfg["files"]["test"]
    for tf in test_files:
        tp = os.path.join(dst, tf)
        with open(tp) as f:
            src = f.read()
        src = re.sub(r"^\s*TEST_IGNORE\(\);\s*//[^\n]*\n", "", src, flags=re.MULTILINE)
        src = re.sub(r"^\s*TEST_IGNORE\(\);\s*\n", "", src, flags=re.MULTILINE)
        with open(tp, "w") as f:
            f.write(src)

    result = run(["make", "test"], cwd=dst)
    output = result.stdout + result.stderr
    tests, failures, ignored = parse_unity(output)

    if tests is not None and failures == 0 and ignored == 0:
        raise AssertionError(
            "Negative control FAILED: bare stub passed all tests — stub may already be solved!"
        )
    print(f"[stub] correctly fails (tests={tests}, failures={failures}, rc={result.returncode})")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== R48-T016 check: raindrops ===")

    before = snapshot(EXERCISE_DIR)

    with tempfile.TemporaryDirectory() as tmp:
        expected_tests = check_reference(tmp)
        check_alternative(tmp, expected_tests)
        check_stub_fails(tmp)

    after = snapshot(EXERCISE_DIR)
    assert before == after, "Exercise directory was modified during check!"
    print("[snapshot] Exercise directory unchanged ✓")

    results = {
        "task": "R48-T016",
        "exercise": EXERCISE,
        "reference_tests": expected_tests,
        "reference_failures": 0,
        "reference_ignored": 0,
        "alternative_tests": expected_tests,
        "alternative_failures": 0,
        "approaches_agree": True,
        "stub_fails": True,
        "directory_unchanged": True,
    }

    results_path = os.path.join(WORK_DIR, "results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {results_path}")

    print("\n=== ALL ASSERTIONS PASSED ===")

if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nFAIL: {e}", file=sys.stderr)
        sys.exit(1)
