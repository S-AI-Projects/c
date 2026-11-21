#!/usr/bin/env python3
"""
Validation script for Task R48-T011: prime-factors canonical case decisions.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_ID = "R48-T011"
EXERCISE_SLUG = "prime-factors"
TARGET_UUIDS = [
    "924fc966-a8f5-4288-82f2-6b9224819ccd",
    "17e30670-b105-4305-af53-ddde182cb6ad",
    "238d57c8-4c12-42ef-af34-ae4929f94789",
]


def find_repo_root() -> Path:
    current = Path.cwd().resolve()
    for parent in [current] + list(current.parents):
        if (parent / "exercises" / "practice" / EXERCISE_SLUG).is_dir():
            return parent
    raise FileNotFoundError(
        f"Could not locate repository root containing exercises/practice/{EXERCISE_SLUG}"
    )


def parse_simple_toml(toml_path: Path) -> dict:
    """Robust, standard-library TOML section parser for Python 3.9+."""
    data = {}
    current_section = None
    section_pattern = re.compile(r"^\[([a-f0-9\-]+)\]")
    key_val_pattern = re.compile(r'^([a-zA-Z0-9_\-]+)\s*=\s*(".*?"|true|false|\d+)')

    with open(toml_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sec_match = section_pattern.match(line)
            if sec_match:
                current_section = sec_match.group(1)
                data[current_section] = {}
                continue
            if current_section:
                kv_match = key_val_pattern.match(line)
                if kv_match:
                    key = kv_match.group(1)
                    raw_val = kv_match.group(2)
                    if raw_val.startswith('"') and raw_val.endswith('"'):
                        val = raw_val[1:-1]
                    elif raw_val == "true":
                        val = True
                    elif raw_val == "false":
                        val = False
                    else:
                        val = int(raw_val)
                    data[current_section][key] = val
    return data


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

    assert solution_files, "config.json does not declare solution files"
    assert example_files, "config.json does not declare example files"
    assert test_files, "config.json does not declare test files"

    # 2. Verify learner stub is unsolved in the working tree
    learner_c_path = exercise_dir / solution_files[0]
    with open(learner_c_path, "r", encoding="utf-8") as f:
        learner_content = f.read()
    assert "int count = 0;" not in learner_content and "while ((n % 2 == 0)" not in learner_content, (
        "Learner stub prime_factors.c must remain unsolved in the working tree!"
    )
    print("✓ Confirmed: Learner stub remains unsolved.")

    # 3. Check tests.toml canonical entries and rationales
    toml_path = exercise_dir / ".meta" / "tests.toml"
    assert toml_path.is_file(), f"Missing tests.toml at {toml_path}"
    toml_data = parse_simple_toml(toml_path)

    total_cases = len(toml_data)
    excluded_cases = sum(1 for v in toml_data.values() if v.get("include") is False)
    included_cases = total_cases - excluded_cases

    print(f"Canonical cases recorded: total={total_cases}, included={included_cases}, excluded={excluded_cases}")
    assert total_cases == 12, f"Expected 12 canonical cases in tests.toml, found {total_cases}"
    assert excluded_cases == 0, f"Expected 0 exclusions, found {excluded_cases}"

    rationales = {}
    for uuid in TARGET_UUIDS:
        assert uuid in toml_data, f"Required UUID {uuid} missing from tests.toml"
        comment = toml_data[uuid].get("comment", "").strip()
        assert comment, f"UUID {uuid} ('{toml_data[uuid].get('description')}') is missing a rationale comment!"
        rationales[uuid] = {
            "description": toml_data[uuid].get("description"),
            "comment": comment,
        }
        print(f"✓ UUID {uuid} ({toml_data[uuid].get('description')}): {comment[:60]}...")

    # 4. Copy exercise to temporary directory (including dotfiles) and substitute reference
    with tempfile.TemporaryDirectory() as tmp_dir:
        scratch_dir = Path(tmp_dir) / EXERCISE_SLUG
        shutil.copytree(exercise_dir, scratch_dir)

        # Substitute reference implementation (example.c)
        ref_src = scratch_dir / example_files[0]
        dest_solution = scratch_dir / solution_files[0]
        shutil.copy2(ref_src, dest_solution)

        if len(example_files) > 1 and len(solution_files) > 1:
            shutil.copy2(scratch_dir / example_files[1], scratch_dir / solution_files[1])

        # Enable all test cases in the scratch copy by removing TEST_IGNORE()
        scratch_test_file = scratch_dir / test_files[0]
        with open(scratch_test_file, "r", encoding="utf-8") as f:
            test_src = f.read()
        enabled_test_src = re.sub(r"^\s*TEST_IGNORE\(\s*\);", "// TEST_IGNORE();", test_src, flags=re.MULTILINE)
        with open(scratch_test_file, "w", encoding="utf-8") as f:
            f.write(enabled_test_src)

        # 5. Run 'make test' using Unity
        print("Running 'make test' against reference in scratch directory...")
        res = subprocess.run(
            ["make", "test"],
            cwd=scratch_dir,
            capture_output=True,
            text=True,
        )

        print("--- Output from make test ---")
        print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        print("-----------------------------")

        # Assert non-zero child exit fails check
        assert res.returncode == 0, f"'make test' failed with non-zero exit code: {res.returncode}"

        # 6. Parse and assert Unity test counts
        # Example Unity summary: "12 Tests 0 Failures 0 Ignored"
        match = re.search(r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored", res.stdout)
        assert match, "Could not find Unity test summary ('X Tests Y Failures Z Ignored') in make test output"

        run_count = int(match.group(1))
        failures = int(match.group(2))
        ignored = int(match.group(3))

        print(f"Reported Executed Cases: {run_count} Tests, {failures} Failures, {ignored} Ignored")

        # Fail on zero-test run, non-zero failures, or non-zero ignored tests
        assert run_count > 0, "Test execution reported 0 tests executed!"
        assert run_count == 12, f"Expected 12 passing tests, but found {run_count}"
        assert failures == 0, f"Expected 0 failures, but found {failures}"
        assert ignored == 0, f"Expected 0 ignored tests, but found {ignored}"

    # 7. Record evidence in work/R48-T011/results.json
    results_data = {
        "task_id": TASK_ID,
        "exercise": EXERCISE_SLUG,
        "tool_versions": get_tool_versions(),
        "counts": {
            "before": {"total": 12, "included": 12, "excluded": 0},
            "after": {"total": 12, "included": 12, "excluded": 0},
        },
        "target_uuids": rationales,
        "execution": {
            "returncode": res.returncode,
            "tests_run": run_count,
            "failures": failures,
            "ignored": ignored,
            "status": "PASS",
        },
    }

    results_path = work_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"✓ Evidence and tool versions saved to {results_path}")
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
