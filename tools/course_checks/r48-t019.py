#!/usr/bin/env python3
"""Isolated test runner for exercises/practice/all-your-base.

Runs the reference implementation from .meta/config.json in an isolated
temporary copy, reports the real executed case count, and propagates
failures. The learner stub files in the working tree are never modified.

Usage:
    python3 tools/course_checks/r48-t019.py [exercise_dir] [--scenario {real,failing,empty,stub}]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXERCISE = ROOT / "exercises" / "practice" / "all-your-base"

LEARNER_FILES = (
    "all_your_base.c",
    "all_your_base.h",
    "test_all_your_base.c",
    "makefile",
)
META_FILES = (
    ".meta/config.json",
    ".meta/tests.toml",
    ".meta/example.c",
    ".meta/example.h",
)

UNITY_SUMMARY_RE = re.compile(
    r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def hash_tree(exercise_dir: Path, files: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in files:
        p = exercise_dir / name
        if p.exists():
            result[name] = sha256_file(p)
    return result


def load_config(exercise_dir: Path) -> dict:
    config_path = exercise_dir / ".meta" / "config.json"
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def copy_tree_with_dotfiles(src: Path, dst: Path) -> None:
    """Copy the entire exercise tree including dotfiles into dst."""
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False)


def substitute_reference(scratch: Path, config: dict) -> None:
    """Substitute reference implementation files into solution paths in scratch copy only."""
    example_files = config["files"]["example"]
    solution_files = config["files"]["solution"]

    for ex_rel in example_files:
        ex_path = scratch / ex_rel
        if not ex_path.exists():
            raise FileNotFoundError(f"Reference file not found: {ex_path}")

        suffix = ex_path.suffix
        sol_matches = [s for s in solution_files if s.endswith(suffix)]
        if not sol_matches:
            raise ValueError(f"No matching solution file for {ex_rel}")

        sol_path = scratch / sol_matches[0]
        sol_path.write_text(ex_path.read_text(encoding="utf-8"), encoding="utf-8")


def enable_all_cases(scratch: Path, config: dict) -> None:
    """Remove TEST_IGNORE() from test file in scratch copy."""
    test_rel = config["files"]["test"][0]
    test_path = scratch / test_rel
    text = test_path.read_text(encoding="utf-8")
    stripped = re.sub(r"^\s*TEST_IGNORE\(\);.*$", "", text, flags=re.MULTILINE)
    test_path.write_text(stripped, encoding="utf-8")


def run_make_test(scratch: Path, timeout: float = 120.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["make", "test"],
        cwd=str(scratch),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def parse_unity_summary(output: str) -> tuple[int, int, int] | None:
    m = UNITY_SUMMARY_RE.search(output)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def run_once(
    exercise_dir: Path,
    scenario: str = "real",
    expected_cases: int = 21,
    timeout: float = 120.0,
) -> dict:
    """Execute one isolated run and return a detailed result dict."""
    result: dict = {
        "scenario": scenario,
        "expected_cases": expected_cases,
        "exit_code": 0,
        "child_exit": None,
        "tests": None,
        "failures": None,
        "ignored": None,
        "passed": False,
        "reason": "",
        "stdout": "",
        "stderr": "",
    }

    # 1. Hash learner and metadata files BEFORE run
    learner_hashes_before = hash_tree(exercise_dir, LEARNER_FILES)
    meta_hashes_before = hash_tree(exercise_dir, META_FILES)
    result["learner_hashes_before"] = learner_hashes_before
    result["meta_hashes_before"] = meta_hashes_before

    config = load_config(exercise_dir)

    # 2. Copy exercise to temp directory (automatically cleaned up)
    with tempfile.TemporaryDirectory(prefix=f"r48-t019-{scenario}-") as tmpdir:
        scratch = Path(tmpdir) / "all-your-base"
        copy_tree_with_dotfiles(exercise_dir, scratch)

        if scenario != "stub":
            substitute_reference(scratch, config)

        # Apply scenario-specific mutations in scratch copy only
        if scenario == "failing":
            # Introduce deliberate logic failure: always return 0
            sol_path = scratch / "all_your_base.c"
            code = sol_path.read_text(encoding="utf-8")
            mutated = code.replace(
                "return new_num_digits;",
                "return 0; /* DELIBERATE MUTANT FAILURE */",
            )
            sol_path.write_text(mutated, encoding="utf-8")
        elif scenario == "empty":
            # Suppress unused function warnings and comment out all RUN_TEST calls
            test_path = scratch / config["files"]["test"][0]
            code = test_path.read_text(encoding="utf-8")
            code = '#pragma GCC diagnostic ignored "-Wunused-function"\n' + code
            mutated = re.sub(r"RUN_TEST\((\w+)\);", r"// RUN_TEST(\1);", code)
            test_path.write_text(mutated, encoding="utf-8")

        # Enable all remaining test cases
        enable_all_cases(scratch, config)

        # Run make test inside scratch
        proc = run_make_test(scratch, timeout=timeout)
        result["child_exit"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr

        summary = parse_unity_summary(proc.stdout)
        if summary:
            result["tests"], result["failures"], result["ignored"] = summary

    # 3. Hash learner and metadata files AFTER run
    learner_hashes_after = hash_tree(exercise_dir, LEARNER_FILES)
    meta_hashes_after = hash_tree(exercise_dir, META_FILES)
    result["learner_hashes_after"] = learner_hashes_after
    result["meta_hashes_after"] = meta_hashes_after

    # 4. Check learner file invariance
    if learner_hashes_before != learner_hashes_after:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = "FATAL: learner files modified during execution"
        return result

    if meta_hashes_before != meta_hashes_after:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = "FATAL: meta files modified during execution"
        return result

    # 5. Evaluate scenario-specific outcome
    # The runner must propagate failures and report real case count
    if proc.returncode != 0:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = f"non-zero child exit: {proc.returncode}"
        return result

    if summary is None:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = "could not parse Unity test summary"
        return result

    tests, num_fails, ignored = summary

    if tests == 0:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = "zero-test run detected (0 tests executed)"
        return result

    if num_fails != 0:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = f"{num_fails} test failure(s) detected"
        return result

    if ignored != 0:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = f"{ignored} test(s) ignored"
        return result

    if tests != expected_cases:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = f"expected {expected_cases} tests, executed {tests}"
        return result

    # All assertions passed cleanly
    result["exit_code"] = 0
    result["passed"] = True
    result["reason"] = f"all {tests} cases passed with 0 failures and 0 ignored"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Isolated test runner for exercises/practice/all-your-base"
    )
    parser.add_argument(
        "exercise_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_EXERCISE,
        help="Path to all-your-base exercise directory",
    )
    parser.add_argument(
        "--scenario",
        choices=["real", "failing", "empty", "stub"],
        default="real",
        help="Execution scenario",
    )
    parser.add_argument(
        "--expected-cases",
        type=int,
        default=21,
        help="Expected number of executed test cases for 'real' scenario",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Timeout in seconds for make test",
    )
    args = parser.parse_args()

    exercise_dir: Path = args.exercise_dir.resolve()
    if not exercise_dir.is_dir():
        print(f"ERROR: exercise directory not found: {exercise_dir}", file=sys.stderr)
        return 2

    res = run_once(
        exercise_dir,
        scenario=args.scenario,
        expected_cases=args.expected_cases,
        timeout=args.timeout,
    )

    print(f"=== Scenario: {res['scenario']} ===")
    print(f"Child exit:    {res['child_exit']}")
    if res["tests"] is not None:
        print(f"Unity summary: {res['tests']} Tests, {res['failures']} Failures, {res['ignored']} Ignored")
    print(f"Runner status: {'PASSED' if res['passed'] else 'FAILED'}")
    print(f"Exit code:     {res['exit_code']}")
    print(f"Reason:        {res['reason']}")

    if res["stdout"] and res["scenario"] == "real":
        print(f"\n--- stdout snippet ---\n{res['stdout'].strip()[-800:]}")
    if res["stderr"]:
        print(f"\n--- stderr snippet ---\n{res['stderr'].strip()[-800:]}")

    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
