#!/usr/bin/env python3
"""
R48-T029  check.py
Task: Run react without altering its learner files [exercises/practice/react]
Student: Tamanna Gupta (e26b07f0713)
"""

import sys
import os
import re
import json
import subprocess
import tempfile
import shutil
import hashlib

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE  = os.path.join(REPO_ROOT, "exercises", "practice", "react")
META      = os.path.join(EXERCISE, ".meta")
WORK_DIR  = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)

def clean_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

def hash_file(path):
    """SHA-256 of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def hash_learner_files(exercise_root, solution_files):
    """Return dict of filename -> sha256 for all learner stub files."""
    result = {}
    for rel in solution_files:
        abs_path = os.path.join(exercise_root, rel)
        if os.path.isfile(abs_path):
            result[rel] = hash_file(abs_path)
    return result

def run_reference_in_tempdir(exercise_root, cfg, strip_ignore=True):
    """
    Copy exercise to a temp dir, substitute example->solution, run make test.
    Returns (returncode, stdout+stderr, n_tests, n_failures, n_ignored, tmpdir_cleaned).
    Temp dir is always cleaned up.
    """
    solution_files = cfg["files"]["solution"]   # ["react.c", "react.h"]
    example_files  = cfg["files"]["example"]    # [".meta/example.c"]

    tmpdir = tempfile.mkdtemp(prefix="react_check_")
    try:
        shutil.copytree(exercise_root, tmpdir, dirs_exist_ok=True)

        # Substitute: .meta/example.c -> react.c  (by position)
        for ex_rel, sol_rel in zip(example_files, solution_files):
            src = os.path.join(tmpdir, ex_rel)
            dst = os.path.join(tmpdir, sol_rel)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

        # Strip TEST_IGNORE()
        if strip_ignore:
            test_c = os.path.join(tmpdir, "test_react.c")
            if os.path.isfile(test_c):
                content = open(test_c).read()
                content = re.sub(r'TEST_IGNORE\(\s*\)\s*;?', '', content)
                open(test_c, "w").write(content)

        result = subprocess.run(
            ["make", "test"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        combined = clean_ansi(result.stdout + "\n" + result.stderr)

        summary = re.search(r'(\d+) Tests[,\s]+(\d+) Failures[,\s]+(\d+) Ignored', combined)
        n_tests    = int(summary.group(1)) if summary else 0
        n_failures = int(summary.group(2)) if summary else -1
        n_ignored  = int(summary.group(3)) if summary else -1

        return result.returncode, combined, n_tests, n_failures, n_ignored

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ---------------------------------------------------------------------------
# Step 0 — Tool versions
# ---------------------------------------------------------------------------
print("=== Tool versions ===")
for cmd in (["python3", "--version"], ["cc", "--version"], ["make", "--version"]):
    r = subprocess.run(cmd, capture_output=True, text=True)
    print((r.stdout or r.stderr).splitlines()[0])

# ---------------------------------------------------------------------------
# Step 1 — Learner stub must be unsolved
# ---------------------------------------------------------------------------
print("\n=== Step 1: learner stub is unsolved ===")
stub_path = os.path.join(EXERCISE, "react.c")
stub_src = open(stub_path).read()
if re.search(r'\bcreate_reactor\s*\(', stub_src):
    fail("react.c appears to have a create_reactor() body — stub must remain unsolved")
print("PASS: learner stub contains no implementation (unsolved)")

# ---------------------------------------------------------------------------
# Step 2 — tests.toml has comment key
# ---------------------------------------------------------------------------
print("\n=== Step 2: tests.toml has comment key ===")
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

toml_path = os.path.join(META, "tests.toml")
with open(toml_path, "rb") as f:
    toml_data = tomllib.load(f)

FIRST_UUID = "c51ee736-d001-4f30-88d1-0c8e8b43cd07"
if FIRST_UUID not in toml_data:
    fail(f"UUID {FIRST_UUID} not found in tests.toml")
entry = toml_data[FIRST_UUID]
if "comment" not in entry:
    fail(f"No 'comment' key on UUID {FIRST_UUID}")
comment_text = entry["comment"]
for kw in ("temporary", "working tree"):
    if kw.lower() not in comment_text.lower():
        fail(f"comment does not mention '{kw}'")
print(f"PASS: tests.toml comment on {FIRST_UUID} covers required keywords")

enabled_count = sum(
    1 for v in toml_data.values()
    if isinstance(v, dict) and v.get("include", True)
)
print(f"      Enabled test cases: {enabled_count}")

# Load config.json
config_path = os.path.join(META, "config.json")
with open(config_path) as f:
    cfg = json.load(f)

solution_files = cfg["files"]["solution"]

# ---------------------------------------------------------------------------
# Step 3 — Hash learner files BEFORE any run
# ---------------------------------------------------------------------------
print("\n=== Step 3: hashing learner files before runs ===")
hashes_before = hash_learner_files(EXERCISE, solution_files)
for rel, h in hashes_before.items():
    print(f"  {rel}: {h[:16]}...")
print("PASS: learner file hashes captured")

# ---------------------------------------------------------------------------
# Step 4 — SUCCESS run: real reference must pass
# ---------------------------------------------------------------------------
print("\n=== Step 4: SUCCESS run — real reference ===")
rc, combined, n_tests, n_failures, n_ignored = run_reference_in_tempdir(EXERCISE, cfg)

print("--- make output (last 25 lines) ---")
for line in combined.splitlines()[-25:]:
    print(line)
print("---")

if rc != 0:
    fail(f"Real reference run exited with code {rc}")
if n_tests == 0:
    fail("Zero tests executed in real reference run")
if n_failures != 0:
    fail(f"{n_failures} test(s) failed in real reference run")

print(f"PASS: {n_tests} tests run, 0 failures, {n_ignored} ignored")

# Verify learner files unchanged after success run
hashes_after_success = hash_learner_files(EXERCISE, solution_files)
if hashes_before != hashes_after_success:
    fail("Learner files were modified during success run!")
print("PASS: learner file hashes identical after success run")

# ---------------------------------------------------------------------------
# Step 5 — FAILURE run: deliberately broken reference must fail
# ---------------------------------------------------------------------------
print("\n=== Step 5: FAILURE run — deliberately broken reference ===")

BROKEN_C = r"""
#include <stdlib.h>
#include "react.h"

struct reactor { int dummy; };
struct cell    { int dummy; };

struct reactor *create_reactor(void) { return calloc(1, sizeof(struct reactor)); }
void destroy_reactor(struct reactor *r) { free(r); }
struct cell *create_input_cell(struct reactor *r, int v) {
    (void)r; (void)v; return NULL; /* always returns NULL — breaks all tests */
}
struct cell *create_compute1_cell(struct reactor *r, struct cell *i, compute1 f) {
    (void)r; (void)i; (void)f; return NULL;
}
struct cell *create_compute2_cell(struct reactor *r, struct cell *i1,
                                  struct cell *i2, compute2 f) {
    (void)r; (void)i1; (void)i2; (void)f; return NULL;
}
int get_cell_value(struct cell *c) { (void)c; return -999; }
void set_cell_value(struct cell *c, int v) { (void)c; (void)v; }
typedef void (*callback)(void *, int);
typedef int callback_id;
callback_id add_callback(struct cell *c, void *o, callback f) {
    (void)c; (void)o; (void)f; return -1;
}
void remove_callback(struct cell *c, callback_id id) { (void)c; (void)id; }
"""

with tempfile.TemporaryDirectory() as tmpdir_broken:
    shutil.copytree(EXERCISE, tmpdir_broken, dirs_exist_ok=True)

    # Write broken reference as react.c
    broken_path = os.path.join(tmpdir_broken, "react.c")
    open(broken_path, "w").write(BROKEN_C)

    # Strip TEST_IGNORE
    test_c = os.path.join(tmpdir_broken, "test_react.c")
    if os.path.isfile(test_c):
        content = open(test_c).read()
        content = re.sub(r'TEST_IGNORE\(\s*\)\s*;?', '', content)
        open(test_c, "w").write(content)

    res_broken = subprocess.run(
        ["make", "test"], cwd=tmpdir_broken, capture_output=True, text=True
    )
    combined_broken = clean_ansi(res_broken.stdout + "\n" + res_broken.stderr)
    summary_b = re.search(r'(\d+) Tests[,\s]+(\d+) Failures[,\s]+(\d+) Ignored', combined_broken)
    n_fail_b = int(summary_b.group(2)) if summary_b else -1

if res_broken.returncode == 0 and n_fail_b == 0:
    fail("Broken reference run unexpectedly passed — failure detection broken")
print(f"PASS: broken reference correctly produces failures (exit={res_broken.returncode}, failures={n_fail_b})")

hashes_after_broken = hash_learner_files(EXERCISE, solution_files)
if hashes_before != hashes_after_broken:
    fail("Learner files were modified during broken reference run!")
print("PASS: learner file hashes identical after broken reference run")

# ---------------------------------------------------------------------------
# Step 6 — ZERO-TEST run: empty test selection must fail
# ---------------------------------------------------------------------------
print("\n=== Step 6: ZERO-TEST run — empty test selection ===")

with tempfile.TemporaryDirectory() as tmpdir_zero:
    shutil.copytree(EXERCISE, tmpdir_zero, dirs_exist_ok=True)

    # Substitute real reference
    for ex_rel, sol_rel in zip(cfg["files"]["example"], solution_files):
        src = os.path.join(tmpdir_zero, ex_rel)
        dst = os.path.join(tmpdir_zero, sol_rel)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    # Comment out ALL test calls so Unity runs 0 tests
    test_c_path = os.path.join(tmpdir_zero, "test_react.c")
    if os.path.isfile(test_c_path):
        content = open(test_c_path).read()
        # Replace RUN_TEST calls with nothing
        content = re.sub(r'\bRUN_TEST\s*\([^)]+\)\s*;', '', content)
        # Also strip TEST_IGNORE
        content = re.sub(r'TEST_IGNORE\(\s*\)\s*;?', '', content)
        open(test_c_path, "w").write(content)

    res_zero = subprocess.run(
        ["make", "test"], cwd=tmpdir_zero, capture_output=True, text=True
    )
    combined_zero = clean_ansi(res_zero.stdout + "\n" + res_zero.stderr)
    summary_z = re.search(r'(\d+) Tests[,\s]+(\d+) Failures[,\s]+(\d+) Ignored', combined_zero)
    n_tests_z = int(summary_z.group(1)) if summary_z else 0

# Zero-test run should produce n_tests == 0 (which our checker treats as failure)
if n_tests_z != 0:
    fail(f"Zero-test run produced {n_tests_z} tests — expected 0")
print(f"PASS: zero-test run produced 0 tests (exit={res_zero.returncode}) — checker would reject this")

hashes_after_zero = hash_learner_files(EXERCISE, solution_files)
if hashes_before != hashes_after_zero:
    fail("Learner files were modified during zero-test run!")
print("PASS: learner file hashes identical after zero-test run")

# ---------------------------------------------------------------------------
# Step 7 — Save results
# ---------------------------------------------------------------------------
print("\n=== Step 7: saving results ===")
os.makedirs(WORK_DIR, exist_ok=True)

results = {
    "task": "R48-T029",
    "exercise": "react",
    "success_run": {"tests": n_tests, "failures": n_failures, "ignored": n_ignored, "exit": 0},
    "broken_run":  {"exit": res_broken.returncode, "failures": n_fail_b, "status": "correctly failed"},
    "zero_test_run": {"tests": n_tests_z, "status": "correctly zero"},
    "learner_hashes_stable": True,
    "comment_key_present": True,
    "status": "PASS",
}
with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

check_output = (
    f"Task R48-T029 — react\n"
    f"Success run: {n_tests} tests, 0 failures\n"
    f"Broken reference run: failures={n_fail_b} (correctly failed)\n"
    f"Zero-test run: 0 tests (correctly detected)\n"
    f"Learner file hashes: stable across all 3 runs\n"
    f"Status: PASS\n"
)
with open(os.path.join(WORK_DIR, "check_output.txt"), "w") as f:
    f.write(check_output)

print(check_output)
print("All checks passed — R48-T029 COMPLETE")
sys.exit(0)
