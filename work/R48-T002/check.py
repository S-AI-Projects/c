#!/usr/bin/env python3
"""Run Wordy reference tests and the independent generation reproducibility check."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = Path(__file__).resolve().parent
REGENERATION_CHECK = ROOT / "tools/course_checks/r48-t002.py"


def load_regeneration_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "r48_t002_regeneration_check", REGENERATION_CHECK
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load regeneration checker: {REGENERATION_CHECK}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_report(report: dict[str, Any]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    report: dict[str, Any] = {
        "task": "R48-T002",
        "exercise": "exercises/practice/wordy",
        "checks": {},
        "status": "failed",
    }
    try:
        checker = load_regeneration_check()
        inputs = checker.load_exercise_inputs()
        original_tree = checker.tree_hashes(checker.EXERCISE)
        reference_result = checker.run_reference_tests(EVIDENCE_DIR, inputs)
        if checker.tree_hashes(checker.EXERCISE) != original_tree:
            raise checker.CheckError(
                "Reference testing changed the original Wordy exercise files."
            )
        report["checks"]["reference_tests"] = reference_result

        generation_result = checker.run_generation_roundtrip(EVIDENCE_DIR)
        report["checks"]["generation_roundtrip"] = generation_result
        report["tool_versions"] = checker.tool_versions()
        report["status"] = "passed"
        write_report(report)

        print(
            "PASS: reference implementation passed "
            f"{reference_result['summary']['tests']} Wordy tests "
            f"({reference_result['summary']['failures']} failures, "
            f"{reference_result['summary']['ignored']} ignored)."
        )
        print(
            "PASS: two fresh root-generator runs retained "
            f"{generation_result['case_count']} cases with identical output."
        )
        print(f"Evidence: {EVIDENCE_DIR}")
        return 0
    except checker.CheckError as error:
        report["error"] = str(error)
        write_report(report)
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError, RuntimeError) as error:
        report["error"] = str(error)
        write_report(report)
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
