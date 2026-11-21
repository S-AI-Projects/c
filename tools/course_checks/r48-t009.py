#!/usr/bin/env python3
"""Isolated test runner for exercises/practice/complex-numbers.

Runs the reference implementation from .meta/config.json in an isolated
temporary copy, reports the real executed case count, and propagates
failures. The learner stub files in the working tree are never modified.
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


# Files whose learner hashes are verified unchanged across a run.
LEARNER_FILES = ("complex_numbers.c", "complex_numbers.h", "test_complex_numbers.c", "makefile")
META_FILES = (".meta/config.json", ".meta/tests.toml")

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
    """Overwrite the solution .c with .meta/example.c in the scratch copy only."""
    example_rel = config["files"]["example"][0]
    example_path = scratch / example_rel
    solution_rel = config["files"]["solution"][0]
    solution_path = scratch / solution_rel

    if not example_path.exists():
        raise FileNotFoundError(f"Reference example not found: {example_path}")

    reference_text = example_path.read_text(encoding="utf-8")
    solution_path.write_text(reference_text, encoding="utf-8")


def enable_all_cases(scratch: Path, config: dict) -> None:
    """Remove every TEST_IGNORE() line from the test file in the scratch copy."""
    test_rel = config["files"]["test"][0]
    test_path = scratch / test_rel
    text = test_path.read_text(encoding="utf-8")
    # Strip standalone TEST_IGNORE(); lines (with trailing newline).
    stripped = text.replace("TEST_IGNORE();\n", "")
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
    expected_cases: int = 40,
    timeout: float = 120.0,
) -> dict:
    """Execute one isolated run and return a result dict."""
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

    # --- 1. Hash learner files BEFORE ---
    learner_hashes_before = hash_tree(exercise_dir, LEARNER_FILES)
    meta_hashes_before = hash_tree(exercise_dir, META_FILES)
    result["learner_hashes_before"] = learner_hashes_before
    result["meta_hashes_before"] = meta_hashes_before

    # --- 2. Load config ---
    config = load_config(exercise_dir)

    # --- 3. Copy exercise to temp dir (auto-cleans on exit / exception) ---
    with tempfile.TemporaryDirectory(prefix="r48-t009-") as tmpdir:
        scratch = Path(tmpdir) / "complex-numbers"
        copy_tree_with_dotfiles(exercise_dir, scratch)

        # --- 4. Substitute reference only in scratch copy ---
        substitute_reference(scratch, config)

        # --- 5. Scenario-specific mutations in scratch copy only ---
        if scenario == "failing":
            # Deliberately break c_add in the scratch copy only.
            sol_path = scratch / config["files"]["solution"][0]
            text = sol_path.read_text(encoding="utf-8")
            text = text.replace(
                "result.real = a.real + b.real;",
                "result.real = a.real - b.real;  /* BROKEN */",
            )
            sol_path.write_text(text, encoding="utf-8")
        elif scenario == "empty":
            # Zero intended cases: comment out every RUN_TEST call.
            test_path = scratch / config["files"]["test"][0]
            text = test_path.read_text(encoding="utf-8")
            text = re.sub(r"RUN_TEST\((\w+)\);", r"// RUN_TEST(\1);", text)
            test_path.write_text(text, encoding="utf-8")

        # --- 6. Enable all intended cases ---
        enable_all_cases(scratch, config)

        # --- 7. Run make test ---
        proc = run_make_test(scratch, timeout=timeout)
        result["child_exit"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr

        # --- 8. Parse Unity summary ---
        summary = parse_unity_summary(proc.stdout)
        if summary:
            result["tests"], result["failures"], result["ignored"] = summary

    # --- 9. Hash learner files AFTER ---
    learner_hashes_after = hash_tree(exercise_dir, LEARNER_FILES)
    meta_hashes_after = hash_tree(exercise_dir, META_FILES)
    result["learner_hashes_after"] = learner_hashes_after
    result["meta_hashes_after"] = meta_hashes_after

    # --- 10. Assertions ---
    checks: list[str] = []

    if learner_hashes_before != learner_hashes_after:
        checks.append("learner files changed during run")

    if meta_hashes_before != meta_hashes_after:
        checks.append("meta files changed during run")

    if proc.returncode != 0:
        checks.append(f"non-zero child exit: {proc.returncode}")

    if summary is None:
        checks.append("could not parse Unity test summary")
    else:
        tests, failures, ignored = summary
        if tests == 0:
            checks.append("zero tests executed")
        if tests != expected_cases:
            checks.append(
                f"expected {expected_cases} cases, got {tests}"
            )
        if failures != 0:
            checks.append(f"{failures} test failure(s)")
        if ignored != 0:
            checks.append(f"{ignored} test(s) ignored")

    if checks:
        result["exit_code"] = 1
        result["passed"] = False
        result["reason"] = "; ".join(checks)
    else:
        result["exit_code"] = 0
        result["passed"] = True
        result["reason"] = "all checks passed"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Isolated test runner for exercises/practice/complex-numbers"
    )
    parser.add_argument(
        "exercise_dir",
        type=Path,
        help="Path to the exercise directory (e.g. exercises/practice/complex-numbers)",
    )
    parser.add_argument(
        "--scenario",
        choices=["real", "failing", "empty"],
        default="real",
        help="Test scenario to execute",
    )
    parser.add_argument(
        "--expected-cases",
        type=int,
        default=40,
        help="Expected number of executed test cases",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Timeout in seconds for make test",
    )
    args = parser.parse_args()

    exercise_dir: Path = args.exercise_dir
    if not exercise_dir.is_dir():
        print(f"ERROR: exercise directory not found: {exercise_dir}", file=sys.stderr)
        return 2

    result = run_once(
        exercise_dir,
        scenario=args.scenario,
        expected_cases=args.expected_cases,
        timeout=args.timeout,
    )

    print(f"Scenario: {result['scenario']}")
    print(f"Expected cases: {result['expected_cases']}")
    print(f"Child exit: {result['child_exit']}")
    if result["tests"] is not None:
        print(f"Tests: {result['tests']}, Failures: {result['failures']}, Ignored: {result['ignored']}")
    print(f"Exit code: {result['exit_code']}")
    print(f"Reason: {result['reason']}")
    if result["stdout"]:
        print(f"\n--- stdout ---\n{result['stdout']}")
    if result["stderr"]:
        print(f"\n--- stderr ---\n{result['stderr']}")

    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
