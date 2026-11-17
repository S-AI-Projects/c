#!/usr/bin/env python3
"""
R48-T028  check.py
Task: Map the maintained files for kindergarten-garden
      [exercises/practice/kindergarten-garden]
Student: Tamanna Gupta (e26b07f0713)
"""

import sys
import os
import re
import json
import subprocess
import tempfile
import shutil

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE  = os.path.join(REPO_ROOT, "exercises", "practice", "kindergarten-garden")
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

def validate_config_files(config_path, exercise_root):
    """
    Parse config.json files object. For each declared path:
      - Resolve relative to exercise_root
      - Reject parent traversal (..)
      - Check file exists
    Returns (True, [paths]) on success, (False, reason_str) on failure.
    """
    with open(config_path) as f:
        cfg = json.load(f)

    files_obj = cfg.get("files", {})
    all_paths = []
    for role in ("solution", "test", "example"):
        for p in files_obj.get(role, []):
            all_paths.append((role, p))

    checked = []
    for role, rel_path in all_paths:
        # Reject parent traversal
        if ".." in rel_path.split("/"):
            return False, f"parent traversal in {role} path: {rel_path}"
        abs_path = os.path.normpath(os.path.join(exercise_root, rel_path))
        # Must stay inside exercise_root
        if not abs_path.startswith(os.path.normpath(exercise_root)):
            return False, f"path escapes exercise root ({role}): {rel_path}"
        if not os.path.isfile(abs_path):
            return False, f"declared {role} file does not exist: {rel_path}"
        checked.append((role, rel_path, abs_path))

    return True, checked

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
stub_path = os.path.join(EXERCISE, "kindergarten_garden.c")
stub_src = open(stub_path).read()
if re.search(r'\bplants\s*\(', stub_src):
    fail("kindergarten_garden.c appears to have a plants() body — stub must remain unsolved")
print("PASS: learner stub contains no plants() implementation (unsolved)")

# ---------------------------------------------------------------------------
# Step 2 — MAINTENANCE.md exists and covers required content
# ---------------------------------------------------------------------------
print("\n=== Step 2: MAINTENANCE.md covers required topics ===")
maint_path = os.path.join(META, "MAINTENANCE.md")
if not os.path.isfile(maint_path):
    fail("MAINTENANCE.md not found in .meta/")
maint = open(maint_path).read()

required_topics = [
    ("kindergarten_garden.c",    "names the learner stub file"),
    (".meta/example.c",          "names the reference implementation path"),
    ("test_kindergarten_garden", "names the test file"),
    ("tests.toml",               "mentions tests.toml"),
    ("config.json",              "mentions config.json"),
    ("generated",                "distinguishes generated artifacts"),
    ("configlet",                "mentions the regeneration tool"),
]
for keyword, desc in required_topics:
    if keyword.lower() not in maint.lower():
        fail(f"MAINTENANCE.md does not {desc} (missing '{keyword}')")
print(f"PASS: MAINTENANCE.md covers all {len(required_topics)} required topics")

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

FIRST_UUID = "1fc316ed-17ab-4fba-88ef-3ae78296b692"
if FIRST_UUID not in toml_data:
    fail(f"UUID {FIRST_UUID} not found in tests.toml")
entry = toml_data[FIRST_UUID]
if "comment" not in entry:
    fail(f"No 'comment' key on UUID {FIRST_UUID} in tests.toml")
comment_text = entry["comment"]
for kw in ("config.json", ".meta", "example"):
    if kw.lower() not in comment_text.lower():
        fail(f"comment on {FIRST_UUID} does not mention '{kw}'")
print(f"PASS: tests.toml comment on {FIRST_UUID} covers required keywords")

enabled_count = sum(
    1 for v in toml_data.values()
    if isinstance(v, dict) and v.get("include", True)
)
print(f"      Enabled test cases: {enabled_count}")

# ---------------------------------------------------------------------------
# Step 4 — Validate the REAL config.json (must pass)
# ---------------------------------------------------------------------------
print("\n=== Step 4: real config.json validates ===")
real_config = os.path.join(META, "config.json")
ok, result = validate_config_files(real_config, EXERCISE)
if not ok:
    fail(f"Real config.json failed validation: {result}")
print(f"PASS: real config.json — all {len(result)} declared files exist and are inside exercise root")
for role, rel, _ in result:
    print(f"      [{role}] {rel}")

# ---------------------------------------------------------------------------
# Step 5 — Deliberately invalid fixtures must FAIL for the right reason
# ---------------------------------------------------------------------------
print("\n=== Step 5: invalid metadata fixtures fail correctly ===")

with tempfile.TemporaryDirectory() as fdir:

    # Load real config
    with open(real_config) as f:
        base_cfg = json.load(f)

    # Fixture A: missing reference file
    cfg_a = json.loads(json.dumps(base_cfg))
    cfg_a["files"]["example"] = [".meta/nonexistent_ref.c"]
    cfg_a_path = os.path.join(fdir, "config_a.json")
    with open(cfg_a_path, "w") as f:
        json.dump(cfg_a, f)
    ok_a, result_a = validate_config_files(cfg_a_path, EXERCISE)
    if ok_a:
        fail("Fixture A (missing reference) should have failed but passed")
    print(f"PASS: Fixture A (missing reference) → rejected: {result_a}")

    # Fixture B: missing test file
    cfg_b = json.loads(json.dumps(base_cfg))
    cfg_b["files"]["test"] = ["test_nonexistent.c"]
    cfg_b_path = os.path.join(fdir, "config_b.json")
    with open(cfg_b_path, "w") as f:
        json.dump(cfg_b, f)
    ok_b, result_b = validate_config_files(cfg_b_path, EXERCISE)
    if ok_b:
        fail("Fixture B (missing test file) should have failed but passed")
    print(f"PASS: Fixture B (missing test)      → rejected: {result_b}")

    # Fixture C: outside-exercise path (parent traversal)
    cfg_c = json.loads(json.dumps(base_cfg))
    cfg_c["files"]["solution"] = ["../hamming/hamming.c", "kindergarten_garden.h"]
    cfg_c_path = os.path.join(fdir, "config_c.json")
    with open(cfg_c_path, "w") as f:
        json.dump(cfg_c, f)
    ok_c, result_c = validate_config_files(cfg_c_path, EXERCISE)
    if ok_c:
        fail("Fixture C (parent traversal) should have failed but passed")
    print(f"PASS: Fixture C (parent traversal)  → rejected: {result_c}")

# ---------------------------------------------------------------------------
# Step 6 — Build and run reference in temp dir
# ---------------------------------------------------------------------------
print("\n=== Step 6: build and run reference implementation ===")

with open(real_config) as f:
    cfg = json.load(f)

solution_files = cfg["files"]["solution"]   # ["kindergarten_garden.c","kindergarten_garden.h"]
example_files  = cfg["files"]["example"]    # [".meta/example.c",".meta/example.h"]

with tempfile.TemporaryDirectory() as tmpdir:
    shutil.copytree(EXERCISE, tmpdir, dirs_exist_ok=True)

    # Substitute example files -> solution files (by position)
    for ex_rel, sol_rel in zip(example_files, solution_files):
        src = os.path.join(tmpdir, ex_rel)
        dst = os.path.join(tmpdir, sol_rel)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    # Strip TEST_IGNORE()
    test_c = os.path.join(tmpdir, "test_kindergarten_garden.c")
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

    print("--- make output (last 40 lines) ---")
    for line in combined.splitlines()[-40:]:
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
# Step 7 — Save results
# ---------------------------------------------------------------------------
print("\n=== Step 7: saving results ===")
os.makedirs(WORK_DIR, exist_ok=True)

results = {
    "task": "R48-T028",
    "exercise": "kindergarten-garden",
    "tests_run": n_tests,
    "failures": n_failures,
    "ignored": n_ignored,
    "config_validation": {
        "real_config": "PASS",
        "fixture_a_missing_reference": "FAIL (expected)",
        "fixture_b_missing_test": "FAIL (expected)",
        "fixture_c_parent_traversal": "FAIL (expected)",
    },
    "maintenance_md_present": True,
    "comment_key_present": True,
    "status": "PASS",
}
with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

check_output = (
    f"Task R48-T028 — kindergarten-garden\n"
    f"Tests run: {n_tests}, Failures: {n_failures}, Ignored: {n_ignored}\n"
    f"Config validation: real=PASS, 3 invalid fixtures=FAIL (expected)\n"
    f"Status: PASS\n"
)
with open(os.path.join(WORK_DIR, "check_output.txt"), "w") as f:
    f.write(check_output)

print(check_output)
print("All checks passed — R48-T028 COMPLETE")
sys.exit(0)
