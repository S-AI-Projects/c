#!/usr/bin/env python3
"""Run all Grade School tests against the maintained reference implementation."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_RELATIVE = Path("exercises/practice/grade-school")
EXERCISE = ROOT / EXERCISE_RELATIVE
EVIDENCE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path(".meta/config.json")
TESTS_PATH = Path(".meta/tests.toml")
BASELINE_COUNTS = {"total": 23, "included": 20, "excluded": 3}
BASELINE_REVISION = "ffe5457101796886a272d6ebbeba8f849229c35a"
TEST_TIMEOUT_SECONDS = 120

SELECTED_CASES = {
    "c125dab7-2a53-492f-a99a-56ad511940d8": {
        "description": "A student can't be in two different grades",
        "test_name": "test_cannot_add_same_student_to_multiple_grades_in_roster",
        "coverage_uuid": "7df542f1-57ce-433c-b249-ff77028ec479",
        "reimplements": None,
    },
    "a0c7b9b8-0e89-47f8-8b4a-c50f885e79d1": {
        "description": "A student can only be added to the same grade in the roster once",
        "test_name": "test_cannot_add_student_to_same_grade_more_than_once",
        "coverage_uuid": "87c871c1-6bde-4413-9c44-73d59a259d83",
        "reimplements": "c125dab7-2a53-492f-a99a-56ad511940d8",
    },
    "6a03b61e-1211-4783-a3cc-fc7f773fba3f": {
        "description": "A student cannot be added to more than one grade in the sorted roster",
        "test_name": "test_student_not_added_to_multiple_grades_in_roster",
        "coverage_uuid": "c7ec1c5e-9ab7-4d3b-be5c-29f2f7a237c5",
        "reimplements": "c125dab7-2a53-492f-a99a-56ad511940d8",
    },
}

UNITY_SUMMARY = re.compile(
    r"(?m)^\s*(\d+)\s+Tests?\s+(\d+)\s+Failures?\s+(\d+)\s+Ignored\s*$"
)
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
IGNORE_LINE = re.compile(r"(?m)^[ \t]*TEST_IGNORE\(\);[ \t]*(?://[^\n]*)?(?:\n|$)")


class VerificationError(Exception):
    """A check prerequisite or verification condition was not satisfied."""


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalized_output(output: str) -> str:
    clean = ANSI_ESCAPE.sub("", output)
    lines = [line.rstrip() for line in clean.splitlines()]
    return "\n".join(lines).rstrip() + ("\n" if lines else "")


def version_output(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"unavailable: {error}"
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        return f"unavailable (exit {result.returncode}): {output}"
    return output.splitlines()[0] if output else "version output was empty"


def tool_versions() -> dict[str, str]:
    compiler = shlex.split(os.environ.get("CC", "cc"))
    if not compiler:
        raise VerificationError("CC is set to an empty command.")
    return {
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "c_compiler": version_output(compiler + ["--version"]),
        "gnu_make": version_output(["make", "--version"]),
    }


def require_file(base: Path, relative: str, role: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise VerificationError(f"Invalid {role} path in config.json: {relative!r}")
    path = base / candidate
    if not path.is_file():
        raise VerificationError(f"Configured {role} file is missing: {path}")
    return path


def configured_paths(config: dict[str, Any], role: str, base: Path) -> list[Path]:
    files = config.get("files")
    if not isinstance(files, dict):
        raise VerificationError("config.json must contain a 'files' object.")
    paths = files.get(role)
    if not isinstance(paths, list) or not paths or not all(
        isinstance(path, str) for path in paths
    ):
        raise VerificationError(f"config.json must define a non-empty '{role}' path list.")
    return [require_file(base, path, role) for path in paths]


def toml_case_counts(tests: dict[str, Any]) -> dict[str, int]:
    cases = {
        key: value
        for key, value in tests.items()
        if isinstance(value, dict) and re.fullmatch(r"[0-9a-f-]{36}", key)
    }
    if not cases:
        raise VerificationError("No UUID case entries were found in tests.toml.")
    excluded = sum(case.get("include") is False for case in cases.values())
    return {
        "total": len(cases),
        "included": len(cases) - excluded,
        "excluded": excluded,
    }


def case_statuses(tests: dict[str, Any]) -> dict[str, str]:
    entries = {
        key: value
        for key, value in tests.items()
        if isinstance(value, dict) and re.fullmatch(r"[0-9a-f-]{36}", key)
    }
    statuses = {}
    for uuid, case in entries.items():
        include = case.get("include", True)
        if not isinstance(include, bool):
            raise VerificationError(f"Invalid include value for canonical case {uuid}.")
        statuses[uuid] = "included" if include else "excluded"
    return statuses


def load_baseline_tests() -> dict[str, Any]:
    path_in_repo = (EXERCISE_RELATIVE / TESTS_PATH).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_REVISION}:{path_in_repo}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        raise VerificationError(
            f"Cannot read baseline tests.toml from {BASELINE_REVISION}: "
            f"{result.stderr.strip()}"
        )
    return tomllib.loads(result.stdout)


def validate_selected_cases(
    tests: dict[str, Any], test_sources: list[Path]
) -> list[dict[str, str]]:
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in test_sources)
    selected_results = []
    for uuid, expected in SELECTED_CASES.items():
        case = tests.get(uuid)
        if not isinstance(case, dict):
            raise VerificationError(f"Selected UUID is missing from tests.toml: {uuid}")
        if case.get("description") != expected["description"]:
            raise VerificationError(f"Description changed unexpectedly for {uuid}.")
        if case.get("include") is not False:
            raise VerificationError(f"Selected UUID must remain excluded: {uuid}")
        if case.get("reimplements") != expected["reimplements"]:
            raise VerificationError(f"reimplements metadata changed unexpectedly for {uuid}.")
        comment = case.get("comment")
        if (
            not isinstance(comment, str)
            or expected["test_name"] not in comment
            or expected["coverage_uuid"] not in comment
        ):
            raise VerificationError(
                f"Rationale comment is missing the test name or coverage UUID for {uuid}."
            )
        if expected["test_name"] not in source_text:
            raise VerificationError(
                f"Documented test function is not present in configured test files: "
                f"{expected['test_name']}"
            )
        selected_results.append(
            {
                "uuid": uuid,
                "description": case["description"],
                "test_name": expected["test_name"],
                "coverage_uuid": expected["coverage_uuid"],
                "status": "excluded",
                "comment": comment,
            }
        )
    return selected_results


def validate_maintenance_doc(selected: list[dict[str, str]]) -> None:
    doc_path = ROOT / "docs/maintenance/grade-school.md"
    if not doc_path.is_file():
        raise VerificationError(f"Maintenance documentation is missing: {doc_path}")
    contents = doc_path.read_text(encoding="utf-8")
    if "Reviewed all 23 canonical cases" not in contents:
        raise VerificationError("Maintenance documentation does not record the case total.")
    if "20 included and 3 excluded" not in contents:
        raise VerificationError("Maintenance documentation does not record case counts.")
    for case in selected:
        row_start = f"| `{case['uuid']}` | `{case['test_name']}` | Excluded |"
        if row_start not in contents or case["coverage_uuid"] not in contents:
            raise VerificationError(
                f"Maintenance mapping does not match tests.toml for {case['uuid']}."
            )


def solution_example_pairs(
    config: dict[str, Any], exercise_copy: Path
) -> list[tuple[Path, Path]]:
    solution_files = configured_paths(config, "solution", exercise_copy)
    example_files = configured_paths(config, "example", exercise_copy)
    solution_by_suffix: dict[str, list[Path]] = {}
    for path in solution_files:
        solution_by_suffix.setdefault(path.suffix, []).append(path)

    pairs = []
    for example in example_files:
        matches = solution_by_suffix.get(example.suffix, [])
        if len(matches) != 1:
            raise VerificationError(
                f"Cannot uniquely match configured example {example} to a solution "
                f"file by extension {example.suffix!r}."
            )
        pairs.append((example, matches[0]))
    if len(pairs) != len(solution_files):
        raise VerificationError(
            "The configured example files do not cover every solution file."
        )
    return pairs


def solution_hashes(paths: list[Path]) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "task": "R48-T001",
        "status": "failed",
        "expected_baseline_counts": BASELINE_COUNTS,
        "selected_cases": [],
    }
    test_output_path = EVIDENCE_DIR / "test-output.txt"
    report_path = EVIDENCE_DIR / "verification.json"

    try:
        report["tool_versions"] = tool_versions()
        if not shutil.which("make"):
            raise VerificationError("GNU Make is required but 'make' is not on PATH.")
        if not shutil.which(shlex.split(os.environ.get("CC", "cc"))[0]):
            raise VerificationError("The configured C compiler is not on PATH.")

        config_path = require_file(EXERCISE, str(CONFIG_PATH), "configuration")
        tests_path = require_file(EXERCISE, str(TESTS_PATH), "canonical tests")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        tests = tomllib.loads(tests_path.read_text(encoding="utf-8"))
        baseline_tests = load_baseline_tests()
        counts = toml_case_counts(tests)
        original_counts = toml_case_counts(baseline_tests)
        original_statuses = case_statuses(baseline_tests)
        final_statuses = case_statuses(tests)
        if original_counts != BASELINE_COUNTS:
            raise VerificationError(
                f"Baseline canonical counts differ from the recorded baseline: "
                f"expected {BASELINE_COUNTS}, found {original_counts}."
            )
        report["final_counts"] = counts
        report["original_counts"] = original_counts
        report["baseline_revision"] = BASELINE_REVISION
        if counts != BASELINE_COUNTS:
            raise VerificationError(
                f"Canonical case counts differ from the unchanged baseline: "
                f"expected {BASELINE_COUNTS}, found {counts}."
            )
        if original_statuses.keys() != final_statuses.keys():
            raise VerificationError("Canonical UUID entries changed from the baseline.")

        baseline_case_data = {
            uuid: case
            for uuid, case in baseline_tests.items()
            if uuid in original_statuses
        }
        final_case_data = {
            uuid: case for uuid, case in tests.items() if uuid in final_statuses
        }
        for uuid, original_case in baseline_case_data.items():
            final_case = final_case_data[uuid]
            original_metadata = dict(original_case)
            final_metadata = dict(final_case)
            if uuid in SELECTED_CASES:
                original_metadata.pop("comment", None)
                final_metadata.pop("comment", None)
            if original_metadata != final_metadata:
                raise VerificationError(
                    f"Canonical metadata other than the selected rationale comments "
                    f"changed for {uuid}."
                )
        report["case_metadata_preserved"] = True
        report["canonical_cases"] = [
            {
                "uuid": uuid,
                "description": final_case_data[uuid].get("description"),
                "original_status": original_statuses[uuid],
                "final_status": final_statuses[uuid],
            }
            for uuid in original_statuses
        ]

        configured_tests = configured_paths(config, "test", EXERCISE)
        report["selected_cases"] = validate_selected_cases(tests, configured_tests)
        validate_maintenance_doc(report["selected_cases"])

        solution_files = configured_paths(config, "solution", EXERCISE)
        before_hashes = solution_hashes(solution_files)
        report["learner_solution_sha256_before"] = before_hashes

        makefiles = [
            EXERCISE / name
            for name in ("GNUmakefile", "makefile", "Makefile")
            if (EXERCISE / name).is_file()
        ]
        if not makefiles:
            raise VerificationError(f"No Makefile found in the exercise: {EXERCISE}")

        with tempfile.TemporaryDirectory(prefix="grade-school-R48-T001-") as temp_dir:
            scratch_exercise = Path(temp_dir) / EXERCISE_RELATIVE.name
            shutil.copytree(EXERCISE, scratch_exercise)
            hidden_source = {
                path.name for path in EXERCISE.iterdir() if path.name.startswith(".")
            }
            hidden_copy = {
                path.name
                for path in scratch_exercise.iterdir()
                if path.name.startswith(".")
            }
            if not hidden_source.issubset(hidden_copy):
                raise VerificationError("The scratch copy is missing hidden exercise files.")
            report["scratch_hidden_entries"] = sorted(hidden_copy)
            scratch_config = json.loads(
                (scratch_exercise / CONFIG_PATH).read_text(encoding="utf-8")
            )
            for example, solution in solution_example_pairs(
                scratch_config, scratch_exercise
            ):
                shutil.copy2(example, solution)

            ignore_markers_removed = 0
            for relative_test in scratch_config["files"]["test"]:
                scratch_test = require_file(scratch_exercise, relative_test, "test")
                original = scratch_test.read_text(encoding="utf-8")
                updated, removed = IGNORE_LINE.subn("", original)
                ignore_markers_removed += removed
                scratch_test.write_text(updated, encoding="utf-8")
                if "TEST_IGNORE()" in updated:
                    raise VerificationError(
                        f"An ignored test remains enabled in scratch file {relative_test}."
                    )

            report["ignore_markers_removed_in_scratch"] = ignore_markers_removed
            report["test_command"] = ["make", "test"]
            try:
                result = subprocess.run(
                    ["make", "test"],
                    cwd=scratch_exercise,
                    capture_output=True,
                    text=True,
                    timeout=TEST_TIMEOUT_SECONDS,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                stdout = error.stdout or ""
                stderr = error.stderr or ""
                if isinstance(stdout, bytes):
                    stdout = stdout.decode(errors="replace")
                if isinstance(stderr, bytes):
                    stderr = stderr.decode(errors="replace")
                test_output_path.write_text(
                    normalized_output(
                        f"Timed out after {TEST_TIMEOUT_SECONDS} seconds.\n"
                        f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}"
                    ),
                    encoding="utf-8",
                )
                report["failure"] = f"make test timed out after {TEST_TIMEOUT_SECONDS}s."
                report["test_output_file"] = str(test_output_path.relative_to(ROOT))
                save_json(report_path, report)
                print(report["failure"], file=sys.stderr)
                return 1

            combined_output = result.stdout + result.stderr
            clean_output = normalized_output(combined_output)
            test_output_path.write_text(clean_output, encoding="utf-8")
            summary_matches = list(UNITY_SUMMARY.finditer(clean_output))
            if len(summary_matches) != 1:
                report["child_return_code"] = result.returncode
                report["failure"] = (
                    "Unity summary was missing or ambiguous; cannot verify a test count."
                )
                report["compilation_or_execution_failure"] = True
                report["test_output_file"] = str(test_output_path.relative_to(ROOT))
                save_json(report_path, report)
                print(report["failure"], file=sys.stderr)
                return 1

            match = summary_matches[0]
            tests_reported, failures, ignored = map(int, match.groups())
            executed = tests_reported - ignored
            passed = tests_reported - failures - ignored
            assertion_failure = failures > 0 or bool(
                re.search(r"(?im)(?:^|:)FAIL(?:$|[\r\n])", clean_output)
            )
            report.update(
                {
                    "child_return_code": result.returncode,
                    "unity_tests_reported": tests_reported,
                    "tests_executed": executed,
                    "tests_passed": passed,
                    "tests_failed": failures,
                    "tests_ignored": ignored,
                    "expected_tests": counts["included"],
                    "assertion_failure_detected": assertion_failure,
                    "compilation_or_execution_failure": result.returncode != 0
                    and not assertion_failure,
                    "test_output_file": str(test_output_path.relative_to(ROOT)),
                }
            )

            reasons = []
            if result.returncode != 0:
                reasons.append(f"make test returned {result.returncode}")
            if executed == 0:
                reasons.append("zero tests executed")
            if failures != 0:
                reasons.append(f"{failures} test failure(s)")
            if ignored != 0:
                reasons.append(f"{ignored} test(s) remained ignored")
            if executed != counts["included"]:
                reasons.append(
                    f"executed {executed} tests, expected {counts['included']}"
                )
            if passed != counts["included"]:
                reasons.append(
                    f"passed {passed} tests, expected {counts['included']}"
                )
            report["status"] = "passed" if not reasons else "failed"
            if reasons:
                report["failure"] = "; ".join(reasons)

        after_hashes = solution_hashes(solution_files)
        report["learner_solution_sha256_after"] = after_hashes
        report["learner_solution_unchanged"] = before_hashes == after_hashes
        if not report["learner_solution_unchanged"]:
            report["status"] = "failed"
            report["failure"] = "Learner solution files changed during verification."
        save_json(report_path, report)
        if report["status"] != "passed":
            print(report.get("failure", "Verification failed."), file=sys.stderr)
            return 1

        print(
            f"PASS: {report['tests_passed']} tests passed; "
            f"{report['tests_failed']} failed; "
            f"{report['tests_ignored']} ignored."
        )
        print(f"Evidence: {report_path}")
        print(f"Unity output: {test_output_path}")
        return 0
    except (
        OSError,
        ValueError,
        VerificationError,
        tomllib.TOMLDecodeError,
        subprocess.SubprocessError,
    ) as error:
        report["failure"] = str(error)
        if not test_output_path.exists():
            test_output_path.write_text(
                f"Test execution did not complete: {error}\n", encoding="utf-8"
            )
        report["test_output_file"] = str(test_output_path.relative_to(ROOT))
        save_json(report_path, report)
        print(f"Verification error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
