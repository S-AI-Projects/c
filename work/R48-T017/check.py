"""
R48-T017 check script
Verifies that:
1. The reference implementation passes all 6 test cases (0 failures, 0 ignored).
2. The learner stub is not solved (compile/link must fail or produce failures).
3. The exercise directory is byte-identical before and after the run.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXERCISE = "spiral-matrix"
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", EXERCISE)
META_DIR = os.path.join(EXERCISE_DIR, ".meta")
CONFIG_PATH = os.path.join(META_DIR, "config.json")

WORK_DIR = os.path.dirname(__file__)


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def parse_unity(output):
    m = re.search(r"(\d+) Tests.*?(\d+) Failures.*?(\d+) Ignored", output)
    if not m:
        return None, None, None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def snapshot(directory):
    snap = {}
    for root, _, files in os.walk(directory):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, directory)
            with open(full, "rb") as fh:
                snap[rel] = fh.read()
    return snap


def enable_all_tests(dst, cfg):
    for tf in cfg["files"]["test"]:
        tp = os.path.join(dst, tf)
        with open(tp) as f:
            src = f.read()
        src = re.sub(r"^\s*TEST_IGNORE\(\);\s*//[^\n]*\n", "", src, flags=re.MULTILINE)
        src = re.sub(r"^\s*TEST_IGNORE\(\);\s*\n", "", src, flags=re.MULTILINE)
        with open(tp, "w") as f:
            f.write(src)


def check_reference(tmp_base):
    dst = os.path.join(tmp_base, "ref")
    shutil.copytree(EXERCISE_DIR, dst)

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    # Substitute example files into solution slots
    for ex_file in cfg["files"]["example"]:
        ex_path = os.path.join(EXERCISE_DIR, ex_file)
        # derive solution filename: .meta/example.c -> spiral_matrix.c
        basename = os.path.basename(ex_file)
        sol_name = basename.replace("example", EXERCISE.replace("-", "_"))
        sol_path = os.path.join(dst, sol_name)
        shutil.copy(ex_path, sol_path)

    enable_all_tests(dst, cfg)

    result = run(["make", "test"], cwd=dst)
    output = result.stdout + result.stderr
    tests, failures, ignored = parse_unity(output)

    print(f"[reference] Unity: {tests} Tests, {failures} Failures, {ignored} Ignored")
    assert tests is not None, "Unity output not found"
    assert tests > 0, f"Zero tests executed"
    assert failures == 0, f"Reference has {failures} failure(s)"
    assert ignored == 0, f"Reference has {ignored} ignored test(s)"
    return tests


def check_stub_fails(tmp_base, expected_tests):
    dst = os.path.join(tmp_base, "stub")
    shutil.copytree(EXERCISE_DIR, dst)

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    enable_all_tests(dst, cfg)

    result = run(["make", "test"], cwd=dst)
    output = result.stdout + result.stderr
    tests, failures, ignored = parse_unity(output)

    if tests is not None and failures == 0 and ignored == 0 and tests == expected_tests:
        raise AssertionError(
            "Negative control FAILED: bare stub passed all tests — stub may already be solved!"
        )
    print(f"[stub] correctly fails (tests={tests}, failures={failures}, rc={result.returncode})")


def main():
    print("=== R48-T017 check: spiral-matrix ===")

    before = snapshot(EXERCISE_DIR)

    with tempfile.TemporaryDirectory() as tmp:
        expected_tests = check_reference(tmp)
        check_stub_fails(tmp, expected_tests)

    after = snapshot(EXERCISE_DIR)
    assert before == after, "Exercise directory was modified during check!"
    print("[snapshot] Exercise directory unchanged ✓")

    results = {
        "task": "R48-T017",
        "exercise": EXERCISE,
        "reference_tests": expected_tests,
        "reference_failures": 0,
        "reference_ignored": 0,
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
