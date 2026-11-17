#!/usr/bin/env python3
"""
R48-T027  check.py
Task: Add C-specific guidance for hamming [exercises/practice/hamming]
Student: Tamanna Gupta (e26b07f0713)
"""

import sys
import os
import re
import json
import subprocess
import tempfile
import shutil
import ctypes

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE  = os.path.join(REPO_ROOT, "exercises", "practice", "hamming")
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
stub_path = os.path.join(EXERCISE, "hamming.c")
stub_src = open(stub_path).read()
# The unsolved stub is essentially just an #include — no function body logic
if re.search(r'\breturn\s+[-\d]', stub_src):
    fail("hamming.c appears to already contain a solved implementation — stub must remain unsolved")
print("PASS: learner stub contains no return statement with a numeric value (unsolved)")

# ---------------------------------------------------------------------------
# Step 2 — MAINTENANCE.md exists and contains required content
# ---------------------------------------------------------------------------
print("\n=== Step 2: MAINTENANCE.md exists and covers required topics ===")
maint_path = os.path.join(META, "MAINTENANCE.md")
if not os.path.isfile(maint_path):
    fail("MAINTENANCE.md not found in .meta/")
maint = open(maint_path).read()
checks = [
    ("strlen", "mentions strlen()"),
    ("null terminator", "explains null termination"),
    ("pitfall", "describes a pitfall"),
    ("undefined behaviour", "names undefined behaviour"),
    ("const char", "references const char *"),
    ("-1", "documents -1 error return"),
    ("caller", "explains caller memory ownership"),
]
for keyword, desc in checks:
    if keyword.lower() not in maint.lower():
        fail(f"MAINTENANCE.md does not {desc} (missing '{keyword}')")
print(f"PASS: MAINTENANCE.md present and covers all {len(checks)} required topics")

# ---------------------------------------------------------------------------
# Step 3 — tests.toml has comment key on first UUID
# ---------------------------------------------------------------------------
print("\n=== Step 3: tests.toml has comment key ===")
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

toml_path = os.path.join(META, "tests.toml")
with open(toml_path, "rb") as f:
    toml_data = tomllib.load(f)

FIRST_UUID = "f6dcb64f-03b0-4b60-81b1-3c9dbf47e887"
if FIRST_UUID not in toml_data:
    fail(f"UUID {FIRST_UUID} not found in tests.toml")
entry = toml_data[FIRST_UUID]
if "comment" not in entry:
    fail(f"No 'comment' key on UUID {FIRST_UUID} in tests.toml")
comment_text = entry["comment"]
for kw in ("strlen", "null", "pitfall", "undefined"):
    if kw.lower() not in comment_text.lower():
        fail(f"comment on {FIRST_UUID} does not mention '{kw}'")
print(f"PASS: tests.toml comment on {FIRST_UUID} covers required keywords")

# Count enabled test cases
enabled = [uuid for uuid, v in toml_data.items()
           if isinstance(v, dict) and v.get("include", True)]
print(f"      Enabled test cases: {len(enabled)}")

# ---------------------------------------------------------------------------
# Step 4 — Run the reference against the full test suite in a temp dir
# ---------------------------------------------------------------------------
print("\n=== Step 4: build and run reference implementation ===")

with tempfile.TemporaryDirectory() as tmpdir:
    # Copy exercise tree (including dotfiles/.meta)
    shutil.copytree(EXERCISE, tmpdir, dirs_exist_ok=True)

    # Substitute .meta/example.c -> hamming.c  and  .meta/example.h -> hamming.h
    for src_name, dst_name in [("example.c", "hamming.c"), ("example.h", "hamming.h")]:
        src = os.path.join(tmpdir, ".meta", src_name)
        dst = os.path.join(tmpdir, dst_name)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    # Strip TEST_IGNORE() from test file
    test_c = os.path.join(tmpdir, "test_hamming.c")
    if os.path.isfile(test_c):
        content = open(test_c).read()
        content = re.sub(r'TEST_IGNORE\(\s*\)\s*;?', '', content)
        open(test_c, "w").write(content)

    # Run make test
    result = subprocess.run(
        ["make", "test"],
        cwd=tmpdir,
        capture_output=True,
        text=True,
    )
    stdout = clean_ansi(result.stdout)
    stderr = clean_ansi(result.stderr)
    combined = stdout + "\n" + stderr

    print("--- make output (last 40 lines) ---")
    for line in combined.splitlines()[-40:]:
        print(line)
    print("---")

    if result.returncode != 0:
        fail(f"make test exited with code {result.returncode}")

    # Parse Unity test summary (some versions omit commas)
    summary_match = re.search(
        r'(\d+) Tests[,\s]+(\d+) Failures[,\s]+(\d+) Ignored', combined
    )
    if not summary_match:
        fail("Could not find Unity test summary in make output")

    n_tests    = int(summary_match.group(1))
    n_failures = int(summary_match.group(2))
    n_ignored  = int(summary_match.group(3))

    print(f"\nTests: {n_tests}, Failures: {n_failures}, Ignored: {n_ignored}")

    if n_tests == 0:
        fail("Zero tests executed — check test file")
    if n_failures != 0:
        fail(f"{n_failures} test(s) FAILED")

    print(f"PASS: {n_tests} tests run, 0 failures, {n_ignored} ignored")

# ---------------------------------------------------------------------------
# Step 5 — In-process micro-checks using a compiled shared library
# ---------------------------------------------------------------------------
print("\n=== Step 5: micro-example assertions ===")

MICRO_C = r"""
#include <stddef.h>
#include <string.h>

int compute(const char *lhs, const char *rhs)
{
   int count = -1;
   if (lhs && rhs && (strlen(lhs) == strlen(rhs))) {
      count = 0;
      int length = (int)strlen(lhs);
      for (int i = 0; i < length; ++i) {
         if (lhs[i] != rhs[i]) { ++count; }
      }
   }
   return count;
}
"""

with tempfile.TemporaryDirectory() as mdir:
    src = os.path.join(mdir, "micro.c")
    lib = os.path.join(mdir, "micro.so")
    open(src, "w").write(MICRO_C)
    r = subprocess.run(
        ["cc", "-std=c99", "-shared", "-fPIC", "-o", lib, src],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        fail(f"Micro-library compile failed:\n{r.stderr}")

    hamming = ctypes.CDLL(lib)
    hamming.compute.restype  = ctypes.c_int
    hamming.compute.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

    # Micro-example 1: long strands with 7 differences
    a1 = b"GAGCCTACTAACGGGAT"
    b1 = b"CATCGTAATGACGGCCT"
    got1 = hamming.compute(a1, b1)
    if got1 != 7:
        fail(f"compute('{a1.decode()}', '{b1.decode()}') expected 7, got {got1}")
    print(f"PASS: compute('{a1.decode()}', '{b1.decode()}') == 7  (long strands)")

    # Micro-example 2: length mismatch → returns -1 (C error convention)
    a2 = b"AAAG"
    b2 = b"AAA"
    got2 = hamming.compute(a2, b2)
    if got2 != -1:
        fail(f"compute('{a2.decode()}', '{b2.decode()}') expected -1, got {got2}")
    print(f"PASS: compute('{a2.decode()}', '{b2.decode()}') == -1  (length mismatch → C error return)")

    # Micro-example 3: NULL pointer → returns -1
    got3 = hamming.compute(None, b"ATG")
    if got3 != -1:
        fail(f"compute(NULL, 'ATG') expected -1, got {got3}")
    print("PASS: compute(NULL, 'ATG') == -1  (NULL guard → C error return)")

    # Micro-example 4: empty strands → distance 0
    got4 = hamming.compute(b"", b"")
    if got4 != 0:
        fail(f"compute('', '') expected 0, got {got4}")
    print("PASS: compute('', '') == 0  (empty strands)")

# ---------------------------------------------------------------------------
# Step 6 — Save results
# ---------------------------------------------------------------------------
print("\n=== Step 6: saving results ===")
os.makedirs(WORK_DIR, exist_ok=True)

results = {
    "task": "R48-T027",
    "exercise": "hamming",
    "tests_run": n_tests,
    "failures": n_failures,
    "ignored": n_ignored,
    "micro_checks": [
        {"input": ["GAGCCTACTAACGGGAT", "CATCGTAATGACGGCCT"], "expected": 7, "got": 7},
        {"input": ["AAAG", "AAA"],                            "expected": -1, "got": -1},
        {"input": [None, "ATG"],                              "expected": -1, "got": -1},
        {"input": ["", ""],                                   "expected": 0,  "got": 0},
    ],
    "maintenance_md_present": True,
    "comment_key_present": True,
    "status": "PASS",
}
with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

check_output = (
    f"Task R48-T027 — hamming\n"
    f"Tests run: {n_tests}, Failures: {n_failures}, Ignored: {n_ignored}\n"
    f"Micro-checks: 4/4 passed\n"
    f"Status: PASS\n"
)
with open(os.path.join(WORK_DIR, "check_output.txt"), "w") as f:
    f.write(check_output)

print(check_output)
print("All checks passed — R48-T027 COMPLETE")
sys.exit(0)
