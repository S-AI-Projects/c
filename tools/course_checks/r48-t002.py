#!/usr/bin/env python3
"""Verify that the Wordy track test-generation path is reproducible."""

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
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_RELATIVE = Path("exercises/practice/wordy")
EXERCISE = ROOT / EXERCISE_RELATIVE
EVIDENCE_DIR = ROOT / "work/R48-T002"
CONFIG_RELATIVE = Path(".meta/config.json")
TESTS_RELATIVE = Path(".meta/tests.toml")
TEST_TIMEOUT_SECONDS = 120

ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
UNITY_SUMMARY = re.compile(
    r"(?m)^\s*(\d+)\s+Tests?\s+(\d+)\s+Failures?\s+(\d+)\s+Ignored\s*$"
)
IGNORE_LINE = re.compile(
    r"(?m)^[ \t]*TEST_IGNORE\(\);[ \t]*(?://[^\n]*)?(?:\n|$)"
)
TEST_FUNCTION = re.compile(r"(?m)^[ \t]*static[ \t]+void[ \t]+(test_[A-Za-z0-9_]+)[ \t]*\(")
RUN_TEST = re.compile(r"\bRUN_TEST\((test_[A-Za-z0-9_]+)\);")
CASE_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
DESCRIPTION_ALIASES = {
    "reject problem missing an operand": "test_reject_a_problem_missing_an_operand",
}


class CheckError(Exception):
    """A prerequisite or reproducibility assertion failed."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes())


def file_hashes(paths: list[Path], base: Path) -> dict[str, str]:
    return {
        path.relative_to(base).as_posix(): file_hash(path)
        for path in sorted(paths)
    }


def tree_hashes(base: Path) -> dict[str, str]:
    return {
        path.relative_to(base).as_posix(): file_hash(path)
        for path in sorted(base.rglob("*"))
        if path.is_file()
    }


def safe_configured_files(config: dict[str, Any], role: str) -> list[Path]:
    files = config.get("files")
    if not isinstance(files, dict):
        raise CheckError("Wordy .meta/config.json must contain a 'files' object.")
    entries = files.get(role)
    if (
        not isinstance(entries, list)
        or not entries
        or not all(isinstance(entry, str) for entry in entries)
    ):
        raise CheckError(
            f"Wordy .meta/config.json must contain a non-empty '{role}' file list."
        )

    paths = []
    for entry in entries:
        relative = Path(entry)
        if relative.is_absolute() or ".." in relative.parts:
            raise CheckError(f"Unsafe configured {role} path: {entry!r}")
        candidate = EXERCISE / relative
        if not candidate.is_file():
            raise CheckError(f"Configured {role} file does not exist: {candidate}")
        paths.append(candidate)
    return paths


def load_exercise_inputs() -> dict[str, Any]:
    if not EXERCISE.is_dir():
        raise CheckError(f"Wordy exercise directory is missing: {EXERCISE}")
    config_path = EXERCISE / CONFIG_RELATIVE
    tests_path = EXERCISE / TESTS_RELATIVE
    if not config_path.is_file() or not tests_path.is_file():
        raise CheckError("Wordy config.json or tests.toml is missing.")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise CheckError("Wordy .meta/config.json must contain a JSON object.")

    solution_files = safe_configured_files(config, "solution")
    test_files = safe_configured_files(config, "test")
    example_files = safe_configured_files(config, "example")
    solutions_by_suffix = {path.suffix: path for path in solution_files}
    examples_by_suffix = {path.suffix: path for path in example_files}
    if (
        len(solutions_by_suffix) != len(solution_files)
        or len(examples_by_suffix) != len(example_files)
        or solutions_by_suffix.keys() != examples_by_suffix.keys()
    ):
        raise CheckError(
            "Configured solution and example files must pair uniquely by file extension."
        )

    try:
        tests = tomllib.loads(tests_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise CheckError(f"Cannot parse Wordy tests.toml: {error}") from error

    cases = {}
    for key, value in tests.items():
        if CASE_UUID.fullmatch(key):
            if not isinstance(value, dict):
                raise CheckError(f"Case {key} must have a TOML table.")
            try:
                uuid.UUID(key)
            except ValueError as error:
                raise CheckError(f"Invalid case UUID in tests.toml: {key}") from error
            description = value.get("description")
            include = value.get("include", True)
            if not isinstance(description, str) or not description:
                raise CheckError(f"Case {key} has no non-empty description.")
            if not isinstance(include, bool):
                raise CheckError(f"Case {key} has a non-boolean include value.")
            cases[key] = {"description": description, "include": include}
    if not cases:
        raise CheckError("No UUID cases were found in Wordy tests.toml.")

    source_text = "\n".join(
        path.read_text(encoding="utf-8") for path in test_files
    )
    functions = TEST_FUNCTION.findall(source_text)
    registrations = RUN_TEST.findall(source_text)
    if len(functions) != len(set(functions)):
        raise CheckError("Wordy test source declares duplicate test functions.")
    if len(registrations) != len(set(registrations)):
        raise CheckError("Wordy test source registers a test function more than once.")
    if set(functions) != set(registrations):
        missing_registrations = sorted(set(functions) - set(registrations))
        missing_functions = sorted(set(registrations) - set(functions))
        raise CheckError(
            "Wordy test functions and RUN_TEST registrations differ: "
            f"unregistered={missing_registrations}, undefined={missing_functions}"
        )

    expected_cases = {}
    for case_id, case in cases.items():
        if not case["include"]:
            continue
        description = case["description"]
        normalized = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")
        function = DESCRIPTION_ALIASES.get(
            description.lower(), f"test_{normalized}"
        )
        if function not in registrations:
            raise CheckError(
                f"Enabled case {case_id} ({description!r}) has no registered "
                f"Unity test named {function!r}."
            )
        expected_cases[case_id] = {
            "description": description,
            "test_function": function,
        }
    if not expected_cases:
        raise CheckError("Wordy tests.toml has no enabled cases.")
    if {case["test_function"] for case in expected_cases.values()} != set(registrations):
        raise CheckError(
            "The enabled cases in tests.toml do not cover exactly the registered "
            "Wordy tests."
        )

    return {
        "config": config,
        "config_path": config_path,
        "tests_path": tests_path,
        "cases": cases,
        "expected_cases": expected_cases,
        "solution_files": solution_files,
        "example_files": example_files,
        "test_files": test_files,
        "test_source": source_text,
        "functions": functions,
        "registrations": registrations,
    }


def command_version(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"unavailable: {error}"
    output = (result.stdout or result.stderr).strip()
    if result.returncode:
        return f"unavailable (exit {result.returncode}): {output}"
    return output.splitlines()[0] if output else "version output was empty"


def tool_versions() -> dict[str, str]:
    compiler = shlex.split(os.environ.get("CC", "cc"))
    if not compiler:
        raise CheckError("CC is set to an empty command.")
    return {
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "make": command_version(["make", "--version"]),
        "c_compiler": command_version(compiler + ["--version"]),
    }


def copy_exercise(destination: Path) -> Path:
    copied = destination / EXERCISE_RELATIVE
    shutil.copytree(EXERCISE, copied)
    if not (copied / ".meta").is_dir() or not (copied / ".docs").is_dir():
        raise CheckError("The temporary Wordy copy is missing hidden directories.")
    return copied


def replace_reference_and_enable_cases(
    copied_exercise: Path, inputs: dict[str, Any]
) -> dict[str, Any]:
    for solution in inputs["solution_files"]:
        relative = solution.relative_to(EXERCISE)
        example = next(
            path
            for path in inputs["example_files"]
            if path.suffix == solution.suffix
        )
        shutil.copy2(example, copied_exercise / relative)

    ignore_count = 0
    for test_file in inputs["test_files"]:
        copied_test = copied_exercise / test_file.relative_to(EXERCISE)
        source = copied_test.read_text(encoding="utf-8")
        updated, removed = IGNORE_LINE.subn("", source)
        ignore_count += removed
        copied_test.write_text(updated, encoding="utf-8")
    expected_ignore_count = len(IGNORE_LINE.findall(inputs["test_source"]))
    if ignore_count != expected_ignore_count:
        raise CheckError(
            f"Expected to enable {expected_ignore_count} ignored tests, "
            f"but removed {ignore_count} ignore markers."
        )
    for test_file in inputs["test_files"]:
        copied_test = copied_exercise / test_file.relative_to(EXERCISE)
        if IGNORE_LINE.search(copied_test.read_text(encoding="utf-8")):
            raise CheckError(f"Ignore markers remain in temporary test file: {copied_test}")
    return {
        "hidden_directories_copied": [".docs", ".meta"],
        "reference_files": [
            {
                "source": example.relative_to(EXERCISE).as_posix(),
                "destination": solution.relative_to(EXERCISE).as_posix(),
            }
            for solution in inputs["solution_files"]
            for example in inputs["example_files"]
            if solution.suffix == example.suffix
        ],
        "ignore_markers_removed": ignore_count,
    }


def run_checked(
    command: list[str],
    cwd: Path,
    timeout: int,
    output_file: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise CheckError(
            f"Command timed out after {timeout} seconds: {command!r}"
        ) from error
    except OSError as error:
        raise CheckError(f"Cannot run command {command!r}: {error}") from error
    if output_file is not None:
        write_log(output_file, result)
    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        raise CheckError(
            f"Command returned {result.returncode}: {command!r}\n{output}"
        )
    return result


def unity_summaries(output: str) -> list[dict[str, int]]:
    clean = ANSI_ESCAPE.sub("", output)
    return [
        {
            "tests": int(tests),
            "failures": int(failures),
            "ignored": int(ignored),
        }
        for tests, failures, ignored in UNITY_SUMMARY.findall(clean)
    ]


def write_log(path: Path, result: subprocess.CompletedProcess[str]) -> None:
    path.write_text(
        result.stdout + result.stderr,
        encoding="utf-8",
    )


def run_reference_tests(
    evidence_dir: Path, inputs: dict[str, Any]
) -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="r48-t002-reference-") as temporary:
        copied_exercise = copy_exercise(Path(temporary))
        copy_details = replace_reference_and_enable_cases(copied_exercise, inputs)
        command = ["make", "test"]
        log_path = evidence_dir / "reference-test-output.txt"
        result = run_checked(
            command, copied_exercise, TEST_TIMEOUT_SECONDS, output_file=log_path
        )

    summaries = unity_summaries(result.stdout + result.stderr)
    if len(summaries) != 1:
        raise CheckError(
            f"Expected one Unity summary from make test, found {len(summaries)}."
        )
    summary = summaries[0]
    expected_count = len(inputs["expected_cases"])
    if summary["tests"] == 0:
        raise CheckError("make test executed zero Unity tests.")
    if summary["tests"] != expected_count:
        raise CheckError(
            f"Expected {expected_count} Unity tests, ran {summary['tests']}."
        )
    if summary["failures"] or summary["ignored"]:
        raise CheckError(
            f"Unity reported {summary['failures']} failures and "
            f"{summary['ignored']} ignored tests."
        )
    return {
        "command": command,
        "exit_code": result.returncode,
        "summary": summary,
        "expected_case_count": expected_count,
        "output_file": log_path.name,
        **copy_details,
    }


def minimal_generator_copy(destination: Path) -> Path:
    repository = destination / "repository"
    repository.mkdir()
    shutil.copy2(ROOT / "makefile", repository / "makefile")
    copy_exercise(repository)
    return repository


def run_generation_roundtrip(evidence_dir: Path) -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    inputs = load_exercise_inputs()
    maintained_paths = [
        ROOT / "makefile",
        *sorted(path for path in EXERCISE.rglob("*") if path.is_file()),
    ]
    expected_input_hashes = file_hashes(maintained_paths, ROOT)
    metadata_bytes = inputs["tests_path"].read_bytes()
    original_test_ids = sorted(inputs["cases"])
    generated_relative = Path("build/exercises/practice/wordy/test_wordy.c")
    runs = []

    for index in (1, 2):
        with tempfile.TemporaryDirectory(
            prefix=f"r48-t002-generation-{index}-"
        ) as temporary:
            repository = minimal_generator_copy(Path(temporary))
            copied_hashes = file_hashes(
                [
                    repository / "makefile",
                    *sorted(
                        path
                        for path in (repository / EXERCISE_RELATIVE).rglob("*")
                        if path.is_file()
                    ),
                ],
                repository,
            )
            if copied_hashes != expected_input_hashes:
                raise CheckError(
                    f"Generation copy {index} did not start with identical maintained inputs."
                )

            command = ["make", "wordy"]
            output_path = evidence_dir / f"generation-run-{index}.txt"
            result = run_checked(
                command, repository, TEST_TIMEOUT_SECONDS, output_file=output_path
            )

            copied_exercise = repository / EXERCISE_RELATIVE
            copied_tests = copied_exercise / TESTS_RELATIVE
            if copied_tests.read_bytes() != metadata_bytes:
                raise CheckError(
                    f"Generation run {index} changed the maintained tests.toml."
                )
            generated_test = repository / generated_relative
            if not generated_test.is_file():
                raise CheckError(
                    f"Generation run {index} did not produce {generated_relative}."
                )
            generated_bytes = generated_test.read_bytes()
            generated_text = generated_bytes.decode("utf-8")
            generated_registrations = RUN_TEST.findall(generated_text)
            if len(generated_registrations) != len(original_test_ids):
                raise CheckError(
                    f"Generation run {index} retained "
                    f"{len(generated_registrations)} test registrations; expected "
                    f"{len(original_test_ids)}."
                )
            if set(generated_registrations) != set(inputs["registrations"]):
                raise CheckError(
                    f"Generation run {index} changed the registered Wordy cases."
                )
            if re.search(r"(?m)^[ \t]*TEST_IGNORE\(\);", generated_text):
                raise CheckError(
                    f"Generation run {index} left an active TEST_IGNORE marker."
                )
            summaries = unity_summaries(result.stdout + result.stderr)
            if len(summaries) < 2:
                raise CheckError(
                    f"Generation run {index} did not report both test and memcheck results."
                )
            for summary in summaries:
                if (
                    summary["tests"] != len(original_test_ids)
                    or summary["failures"]
                    or summary["ignored"]
                ):
                    raise CheckError(
                        f"Generation run {index} had an unexpected Unity summary: "
                        f"{summary}."
                    )

            runs.append(
                {
                    "run": index,
                    "command": command,
                    "exit_code": result.returncode,
                    "input_hashes": copied_hashes,
                    "tests_toml_sha256": file_hash(copied_tests),
                    "generated_test_path": generated_relative.as_posix(),
                    "generated_test_sha256": sha256(generated_bytes),
                    "generated_test_registrations": generated_registrations,
                    "unity_summaries": summaries,
                    "output_file": output_path.name,
                }
            )

    if runs[0]["input_hashes"] != runs[1]["input_hashes"]:
        raise CheckError("The two generation runs did not start from identical inputs.")
    if runs[0]["tests_toml_sha256"] != runs[1]["tests_toml_sha256"]:
        raise CheckError("Wordy tests.toml differs between generation runs.")
    if runs[0]["generated_test_sha256"] != runs[1]["generated_test_sha256"]:
        raise CheckError(
            "Generated test files differ between fresh copies; no normalization "
            "was applied because the generator has no timestamp."
        )
    if file_hashes(maintained_paths, ROOT) != expected_input_hashes:
        raise CheckError("The original working tree inputs changed during generation.")

    return {
        "generator": "root makefile target `make wordy`",
        "metadata_behavior": (
            "The target does not generate tests.toml; it remains byte-identical "
            "to the maintained input."
        ),
        "timestamp_normalization": "none; no generated timestamp is present",
        "case_count": len(original_test_ids),
        "case_ids": original_test_ids,
        "maintained_input_sha256": expected_input_hashes,
        "runs": runs,
        "comparison": {
            "identical_inputs": True,
            "tests_toml_identical": True,
            "generated_test_identical": True,
            "case_ids_retained": True,
            "unexpected_differences": [],
        },
        "tool_versions": tool_versions(),
    }


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    try:
        evidence = run_generation_roundtrip(EVIDENCE_DIR)
    except CheckError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    save_json(EVIDENCE_DIR / "generation-evidence.json", evidence)
    print(
        "PASS: two isolated `make wordy` runs produced identical enabled tests "
        f"({evidence['case_count']} cases); tests.toml remained unchanged."
    )
    print(f"Evidence: {EVIDENCE_DIR / 'generation-evidence.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
