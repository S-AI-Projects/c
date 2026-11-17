#!/usr/bin/env python3
"""
R48-T030  check.py
Task: Explain the subtle contract cases in scrabble-score [exercises/practice/scrabble-score]
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
EXERCISE  = os.path.join(REPO_ROOT, "exercises", "practice", "scrabble-score")
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
stub_path = os.path.join(EXERCISE, "scrabble_score.c")
stub_src = open(stub_path).read()
if re.search(r'\bscore\s*\(', stub_src):
    fail("scrabble_score.c appears to contain a score() body — stub must remain unsolved")
print("PASS: learner stub contains no score() implementation (unsolved)")

# ---------------------------------------------------------------------------
# Step 2 — MAINTENANCE.md exists and covers required topics
# ---------------------------------------------------------------------------
print("\n=== Step 2: MAINTENANCE.md exists and covers contract ===")
maint_path = os.path.join(META, "MAINTENANCE.md")
if not os.path.isfile(maint_path):
    fail("MAINTENANCE.md not found in .meta/")
maint = open(maint_path).read()

required_topics = [
    ("decision table", "contains decision table"),
    ("empty string",   "covers empty string contract"),
    ("case insensitivity", "covers case insensitivity"),
    ("unspecified",    "separates unspecified inputs"),
    ("87",             "records 87 alphabet score"),
]
for keyword, desc in required_topics:
    if keyword.lower() not in maint.lower():
        fail(f"MAINTENANCE.md does not {desc} (missing '{keyword}')")
print(f"PASS: MAINTENANCE.md present and covers all {len(required_topics)} required topics")

# ---------------------------------------------------------------------------
# Step 3 — tests.toml has comment keys on subtle contract cases
# ---------------------------------------------------------------------------
print("\n=== Step 3: tests.toml comments on subtle contract cases ===")
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

toml_path = os.path.join(META, "tests.toml")
with open(toml_path, "rb") as f:
    toml_data = tomllib.load(f)

contract_cases = [
    ("f7794b49-f13e-45d1-a933-4e48459b2201", "uppercase letter"),
    ("9336f0ba-9c2b-4fa0-bd1c-2e2d328cf967", "long, mixed-case word"),
    ("4efe3169-b3b6-4334-8bae-ff4ef24a7e4f", "empty input"),
    ("3b305c1c-f260-4e15-a5b5-cb7d3ea7c3d7", "entire alphabet available"),
]

for uuid, desc in contract_cases:
    if uuid not in toml_data:
        fail(f"UUID {uuid} ({desc}) missing from tests.toml")
    entry = toml_data[uuid]
    if "comment" not in entry or not entry["comment"].strip():
        fail(f"UUID {uuid} ({desc}) missing 'comment' key")
    print(f"  ✓ UUID {uuid[:8]} ({desc}): {entry['comment'][:50]}...")

print("PASS: all designated contract cases have explanatory comment keys")

enabled_count = sum(
    1 for v in toml_data.values()
    if isinstance(v, dict) and v.get("include", True)
)
print(f"      Enabled test cases: {enabled_count}")

# ---------------------------------------------------------------------------
# Step 4 — Run reference implementation against test suite in temp dir
# ---------------------------------------------------------------------------
print("\n=== Step 4: build and run reference implementation ===")
config_path = os.path.join(META, "config.json")
with open(config_path) as f:
    cfg = json.load(f)

solution_files = cfg["files"]["solution"]   # ["scrabble_score.c", "scrabble_score.h"]
example_files  = cfg["files"]["example"]    # [".meta/example.c", ".meta/example.h"]

with tempfile.TemporaryDirectory() as tmpdir:
    shutil.copytree(EXERCISE, tmpdir, dirs_exist_ok=True)

    # Substitute example files -> solution files
    for ex_rel, sol_rel in zip(example_files, solution_files):
        src = os.path.join(tmpdir, ex_rel)
        dst = os.path.join(tmpdir, sol_rel)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    # Strip TEST_IGNORE()
    test_c = os.path.join(tmpdir, "test_scrabble_score.c")
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
    stdout = clean_ansi(result.stdout)
    stderr = clean_ansi(result.stderr)
    combined = stdout + "\n" + stderr

    print("--- make output (last 30 lines) ---")
    for line in combined.splitlines()[-30:]:
        print(line)
    print("---")

    if result.returncode != 0:
        fail(f"make test exited with code {result.returncode}")

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
# Step 5 — Decision table verification directly against reference
# ---------------------------------------------------------------------------
print("\n=== Step 5: decision table verification ===")

decision_table = [
    ("",                           0,  "empty input"),
    ("a",                          1,  "single lowercase letter"),
    ("A",                          1,  "single uppercase letter (case insensitivity)"),
    ("f",                          4,  "valuable letter"),
    ("at",                         2,  "short word"),
    ("zoo",                        12, "short valuable word"),
    ("street",                     6,  "medium word"),
    ("quirky",                     22, "medium valuable word"),
    ("OxyphenButazone",            41, "long mixed-case word"),
    ("pinata",                     8,  "english-like word"),
    ("abcdefghijklmnopqrstuvwxyz", 87, "full alphabet available"),
]

with tempfile.TemporaryDirectory() as lib_dir:
    src_path = os.path.join(lib_dir, "scrabble.c")
    so_path  = os.path.join(lib_dir, "scrabble.so")

    shutil.copy2(os.path.join(META, "example.c"), src_path)
    shutil.copy2(os.path.join(META, "example.h"), os.path.join(lib_dir, "scrabble_score.h"))

    compile_res = subprocess.run(
        ["cc", "-std=c99", "-shared", "-fPIC", "-I", lib_dir, "-o", so_path, src_path],
        capture_output=True,
        text=True
    )
    if compile_res.returncode != 0:
        fail(f"Failed to compile reference as shared lib:\n{compile_res.stderr}")

    scrabble = ctypes.CDLL(so_path)
    scrabble.score.restype = ctypes.c_uint
    scrabble.score.argtypes = [ctypes.c_char_p]

    verified_cases = []
    for word, expected, desc in decision_table:
        actual = scrabble.score(word.encode("ascii"))
        if actual != expected:
            fail(f"Decision table mismatch for '{word}' ({desc}): expected {expected}, got {actual}")
        verified_cases.append({"word": word, "expected": expected, "actual": actual, "description": desc})
        print(f"  ✓ {desc:45} : '{word}' -> {actual}")

print(f"PASS: all {len(decision_table)} decision table rows verified against reference")

# ---------------------------------------------------------------------------
# Step 6 — Save results
# ---------------------------------------------------------------------------
print("\n=== Step 6: saving results ===")
os.makedirs(WORK_DIR, exist_ok=True)

results = {
    "task": "R48-T030",
    "exercise": "scrabble-score",
    "tests_run": n_tests,
    "failures": n_failures,
    "ignored": n_ignored,
    "decision_table_verified": verified_cases,
    "maintenance_md_present": True,
    "comment_keys_present": True,
    "status": "PASS",
}
with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

check_output = (
    f"Task R48-T030 — scrabble-score\n"
    f"Tests run: {n_tests}, Failures: {n_failures}, Ignored: {n_ignored}\n"
    f"Decision table cases: {len(decision_table)} verified\n"
    f"Status: PASS\n"
)
with open(os.path.join(WORK_DIR, "check_output.txt"), "w") as f:
    f.write(check_output)

print(check_output)
print("All checks passed — R48-T030 COMPLETE")
sys.exit(0)
