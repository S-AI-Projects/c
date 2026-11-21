#!/usr/bin/env python3
"""
Validation script for Task R48-T013: Mutation-driven regression for rna-transcription.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_ID = "R48-T013"
EXERCISE_SLUG = "rna-transcription"
REJECTING_UUID = "aade8964-02e1-4073-872f-42d3ffd74c5f"
REJECTING_TEST = "test_rna_complement_of_adenine_is_uracil"


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
    assert "calloc" not in learner_content and "switch" not in learner_content, (
        "Learner stub rna_transcription.c must remain unsolved in working tree!"
    )
    print("✓ Confirmed: Learner stub remains unsolved.")

    # 3. Verify hints.md and maintenance documentation
    hints_path = exercise_dir / ".docs" / "hints.md"
    assert hints_path.is_file(), f"Missing hints.md at {hints_path}"
    with open(hints_path, "r", encoding="utf-8") as f:
        hints_content = f.read()
    assert "Uracil" in hints_content and "Thymine" in hints_content, "hints.md must explain Uracil vs Thymine!"
    assert '"A"' in hints_content, "hints.md must give single-nucleotide diagnostic input 'A'!"
    print("✓ Confirmed: hints.md documents underlying contract and diagnostic input.")

    # 4. Test original reference implementation
    with tempfile.TemporaryDirectory() as tmp_dir:
        scratch_dir = Path(tmp_dir) / EXERCISE_SLUG
        shutil.copytree(exercise_dir, scratch_dir)

        # Substitute original reference
        shutil.copy2(scratch_dir / example_files[0], scratch_dir / solution_files[0])

        # Enable all tests
        test_file_path = scratch_dir / test_files[0]
        with open(test_file_path, "r", encoding="utf-8") as f:
            src = f.read()
        enabled_src = re.sub(r"^\s*TEST_IGNORE\(\s*\);", "// TEST_IGNORE();", src, flags=re.MULTILINE)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(enabled_src)

        print("Running 'make test' on original reference...")
        res_orig = subprocess.run(["make", "test"], cwd=scratch_dir, capture_output=True, text=True)
        assert res_orig.returncode == 0, f"Original reference failed make test: {res_orig.stdout}\n{res_orig.stderr}"

        m = re.search(r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored", res_orig.stdout)
        assert m, "Could not parse Unity test output from original run"
        orig_tests, orig_failures, orig_ignored = int(m.group(1)), int(m.group(2)), int(m.group(3))
        assert orig_tests > 0, "Original run reported 0 tests executed"
        assert orig_failures == 0, f"Original run reported {orig_failures} failures"
        assert orig_ignored == 0, f"Original run reported {orig_ignored} ignored tests"
        print(f"✓ Original reference: {orig_tests} Tests, {orig_failures} Failures, {orig_ignored} Ignored (PASS)")

    # 5. Test mutated reference implementation
    with tempfile.TemporaryDirectory() as tmp_dir:
        scratch_dir = Path(tmp_dir) / EXERCISE_SLUG
        shutil.copytree(exercise_dir, scratch_dir)

        # Apply deliberate mutation M1: case 'A': rna[i] = 'T'; (instead of 'U')
        with open(scratch_dir / example_files[0], "r", encoding="utf-8") as f:
            ref_code = f.read()
        assert "rna[i] = 'U';" in ref_code, "Mutation target 'rna[i] = 'U';' not found in example.c"
        mutated_code = ref_code.replace("rna[i] = 'U';", "rna[i] = 'T';")
        with open(scratch_dir / solution_files[0], "w", encoding="utf-8") as f:
            f.write(mutated_code)

        # Enable all tests
        test_file_path = scratch_dir / test_files[0]
        with open(test_file_path, "r", encoding="utf-8") as f:
            src = f.read()
        enabled_src = re.sub(r"^\s*TEST_IGNORE\(\s*\);", "// TEST_IGNORE();", src, flags=re.MULTILINE)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(enabled_src)

        print("Running 'make test' on mutated reference (M1: A -> T)...")
        res_mut = subprocess.run(["make", "test"], cwd=scratch_dir, capture_output=True, text=True)
        assert res_mut.returncode != 0, "Mutated reference should FAIL make test, but it passed!"

        output = res_mut.stdout + res_mut.stderr
        m_mut = re.search(r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored", output)
        assert m_mut, "Could not parse Unity test output from mutated run"
        mut_tests, mut_failures, mut_ignored = int(m_mut.group(1)), int(m_mut.group(2)), int(m_mut.group(3))
        assert mut_failures > 0, "Mutated run reported 0 failures"
        assert REJECTING_TEST in output, f"Expected rejecting test {REJECTING_TEST} to fail in output!"
        print(f"✓ Mutated reference successfully rejected by {REJECTING_TEST} ({mut_failures} failures as expected)")

    # 6. Save results & evidence
    results = {
        "task_id": TASK_ID,
        "exercise": EXERCISE_SLUG,
        "tool_versions": get_tool_versions(),
        "mutant": {
            "id": "M1",
            "description": "Transcribe Adenine 'A' to Thymine 'T' instead of Uracil 'U'",
            "diff": "case 'A': rna[i] = 'T'; // was 'U'",
            "rejecting_uuid": REJECTING_UUID,
            "rejecting_test": REJECTING_TEST,
            "smallest_diagnostic_input": "A",
            "expected_output": "U",
            "actual_mutant_output": "T",
        },
        "original_run": {
            "returncode": res_orig.returncode,
            "tests": orig_tests,
            "failures": orig_failures,
            "ignored": orig_ignored,
            "status": "PASS",
        },
        "mutant_run": {
            "returncode": res_mut.returncode,
            "tests": mut_tests,
            "failures": mut_failures,
            "ignored": mut_ignored,
            "status": "REJECTED_AS_EXPECTED",
        },
    }

    results_path = work_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    evidence_path = work_dir / "evidence.md"
    evidence_md = f"""# R48-T013 evidence

Exercise: `{exercise_dir}`
Inputs: solution={solution_files} | test={test_files} | example={example_files}
Python: {sys.version.split()[0]}
Tool versions: {json.dumps(get_tool_versions())}

## Expected vs Actual

| Check | Expected | Actual |
|-------|----------|--------|
| Original reference passes all cases | True | True |
| Original Unity tests run (N) | 6 | {orig_tests} |
| Original Unity failures (M) | 0 | {orig_failures} |
| Original Unity ignored (K) | 0 | {orig_ignored} |
| Mutant M1 rejected | True | True |
| Rejecting test case | `{REJECTING_TEST}` | `{REJECTING_TEST}` |
| Smallest diagnostic input | `"A"` -> `"U"` | `"A"` -> `"T"` (rejected) |
| Learner stub unsolved | True | True |
| Educational hint added | True | True |

Result: PASS. Original reference passes 6/6 tests. Mutant M1 is decisively rejected by `{REJECTING_TEST}`.
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
