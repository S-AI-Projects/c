#!/usr/bin/env python3
"""
Validation script for Task R48-T014: Clarify advance_pos in the say reference.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_ID = "R48-T014"
EXERCISE_SLUG = "say"


def find_repo_root() -> Path:
    current = Path.cwd().resolve()
    for parent in [current] + list(current.parents):
        if (parent / "exercises" / "practice" / EXERCISE_SLUG).is_dir():
            return parent
    raise FileNotFoundError(
        f"Could not locate repository root containing exercises/practice/{EXERCISE_SLUG}"
    )


def get_tool_versions() -> dict:
    versions = {"python": sys.version.split()[0]}
    for tool in ["make", "cc"]:
        try:
            res = subprocess.run([tool, "--version"], capture_output=True, text=True, check=True)
            versions[tool] = res.stdout.splitlines()[0]
        except Exception:
            versions[tool] = "unknown"
    return versions


def run_tests_in_temp(exercise_dir, example_rel_path, solution_rel_path, test_rel_path):
    with tempfile.TemporaryDirectory() as tmp_dir:
        scratch_dir = Path(tmp_dir) / EXERCISE_SLUG
        shutil.copytree(exercise_dir, scratch_dir)

        # Substitute reference
        shutil.copy2(scratch_dir / example_rel_path, scratch_dir / solution_rel_path)

        # Enable all tests
        test_file_path = scratch_dir / test_rel_path
        with open(test_file_path, "r", encoding="utf-8") as f:
            src = f.read()
        enabled_src = re.sub(r"^\s*TEST_IGNORE\(\s*\);", "// TEST_IGNORE();", src, flags=re.MULTILINE)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(enabled_src)

        res = subprocess.run(["make", "test"], cwd=scratch_dir, capture_output=True, text=True)
        m = re.search(r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored", res.stdout + res.stderr)
        assert m, f"Could not parse Unity test output:\n{res.stdout}\n{res.stderr}"

        tests = int(m.group(1))
        failures = int(m.group(2))
        ignored = int(m.group(3))
        return res.returncode, tests, failures, ignored, res.stdout


def main():
    repo_root = find_repo_root()
    exercise_dir = repo_root / "exercises" / "practice" / EXERCISE_SLUG
    work_dir = repo_root / "work" / TASK_ID
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Starting QA Check for {TASK_ID} ({EXERCISE_SLUG}) ===")
    print(f"Repository root: {repo_root}")

    # 1. Resolve paths from .meta/config.json
    config_path = exercise_dir / ".meta" / "config.json"
    assert config_path.is_file(), f"Missing config.json at {config_path}"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_files = config.get("files", {}).get("solution", [])
    example_files = config.get("files", {}).get("example", [])
    test_files = config.get("files", {}).get("test", [])

    assert solution_files, "config.json missing solution files"
    assert example_files, "config.json missing example files"
    assert test_files, "config.json missing test files"

    # 2. Verify learner stub is unsolved in the working tree
    learner_c_path = exercise_dir / solution_files[0]
    with open(learner_c_path, "r", encoding="utf-8") as f:
        learner_content = f.read()
    assert "advance_pos" not in learner_content and "floor(log10" not in learner_content, (
        "Learner stub say.c must remain unsolved in working tree!"
    )
    print("✓ Confirmed: Learner stub remains unsolved.")

    # 3. Verify public API in say.h is untouched
    header_path = exercise_dir / solution_files[1]
    with open(header_path, "r", encoding="utf-8") as f:
        header_content = f.read()
    assert "int say(int64_t input, char **ans);" in header_content, "Public API signature in say.h changed!"
    print("✓ Confirmed: Public API contract in say.h is preserved.")

    # 4. Verify refactored example.c has invariant comment and improved naming
    example_path = exercise_dir / example_files[0]
    with open(example_path, "r", encoding="utf-8") as f:
        example_content = f.read()
    assert "Invariant:" in example_content, "Missing invariant comment in example.c"
    assert "advance_pos(char **cursor, const char *word, size_t word_len)" in example_content, (
        "advance_pos parameters not clarified as expected"
    )
    print("✓ Confirmed: example.c includes invariant explanation and clarified cursor/word names.")

    # 5. Run tests with current refactored reference
    print("Running 'make test' with refactored reference...")
    rc, tests, failures, ignored, output = run_tests_in_temp(
        exercise_dir, example_files[0], solution_files[0], test_files[0]
    )

    print(f"Reported Unity Results: {tests} Tests, {failures} Failures, {ignored} Ignored (rc={rc})")
    assert rc == 0, f"'make test' failed with exit code {rc}"
    assert tests == 19, f"Expected 19 tests, got {tests}"
    assert failures == 0, f"Expected 0 failures, got {failures}"
    assert ignored == 0, f"Expected 0 ignored, got {ignored}"
    print("✓ All 19 tests pass against refactored reference.")

    # 6. Save evidence
    results = {
        "task_id": TASK_ID,
        "exercise": EXERCISE_SLUG,
        "tool_versions": get_tool_versions(),
        "refactor": {
            "target": "advance_pos",
            "clarified_parameters": ["char **cursor", "const char *word", "size_t word_len"],
            "invariant_documented": True,
            "public_api_intact": True,
        },
        "execution": {
            "returncode": rc,
            "tests_run": tests,
            "failures": failures,
            "ignored": ignored,
            "status": "PASS",
        },
    }

    results_path = work_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    evidence_path = work_dir / "evidence.md"
    evidence_md = f"""# R48-T014 evidence

Exercise: `{exercise_dir}`
Inputs: solution={solution_files} | test={test_files} | example={example_files}
Python: {sys.version.split()[0]}
Tool versions: {json.dumps(get_tool_versions())}

## Expected vs Actual

| Check | Expected | Actual |
|-------|----------|--------|
| Refactored reference passes all cases | True | True |
| Unity tests run (N) | 19 | {tests} |
| Unity failures (M) | 0 | {failures} |
| Unity ignored (K) | 0 | {ignored} |
| Learner stub unsolved | True | True |
| Public API contract preserved | True | True |
| advance_pos parameter clarity improved | True | True |
| Invariant comment documented | True | True |

Result: PASS. All 19 Unity cases ran and passed with 0 failures and 0 ignored.
"""
    with open(evidence_path, "w", encoding="utf-8") as f:
        f.write(evidence_md)

    print(f"✓ Evidence saved to {results_path} and {evidence_path}")
    print(f"=== ALL CHECKS PASSED FOR {TASK_ID} ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"❌ ASSERTION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)
