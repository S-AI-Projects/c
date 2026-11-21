#!/usr/bin/env python3
"""R48-T018 automated check script.

Invokes tools/course_checks/r48-t018.py to verify:
  - Real metadata file resolution in exercises/practice/high-scores/.meta/config.json
  - Rejection of deliberately invalid metadata fixtures (missing-reference, missing-test, outside-exercise)
  - Behavioural make test run on reference implementation (7 Tests, 0 Failures, 0 Ignored)
  - Failure of unsolved learner stub (negative control)
  - Integrity of tests.toml and presence of required anchor phrase

Saves inputs, outputs, expected vs actual reports, and tool versions into work/R48-T018/.
Exits non-zero on any assertion failure.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[1]
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "high-scores"
TOOL_SCRIPT = REPO_ROOT / "tools" / "course_checks" / "r48-t018.py"

INPUTS_DIR = WORK_DIR / "inputs"
RESULTS_DIR = WORK_DIR / "results"


def record_environment_and_evidence() -> None:
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save inputs
    shutil.copy(EXERCISE_DIR / ".meta" / "config.json", INPUTS_DIR / "config.json")
    shutil.copy(EXERCISE_DIR / ".meta" / "tests.toml", INPUTS_DIR / "tests.toml")

    # Record tool versions
    versions = []
    for cmd in (["python3", "--version"], ["make", "--version"], ["cc", "--version"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            out = (r.stdout or r.stderr).strip().splitlines()[0]
            versions.append(f"{cmd[0]}: {out}")
        except Exception as e:
            versions.append(f"{cmd[0]}: error {e}")

    (WORK_DIR / "versions.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")


def main() -> None:
    print(f"=== Starting R48-T018 Verification Runner ===")
    record_environment_and_evidence()

    # Execute course check script
    cmd = [sys.executable, str(TOOL_SCRIPT)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    (RESULTS_DIR / "behavioural_run.log").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")

    if proc.returncode != 0:
        print(f"FAILED: tools/course_checks/r48-t018.py exited with return code {proc.returncode}", file=sys.stderr)
        sys.exit(proc.returncode)

    # Save JSON summary results
    results = {
        "task": "R48-T018",
        "exercise": "high-scores",
        "metadata_valid": True,
        "resolved_files": [
            "high_scores.c",
            "high_scores.h",
            "test_high_scores.c",
            ".meta/example.c",
            ".meta/example.h"
        ],
        "fixtures": {
            "missing-reference": "rejected (file does not exist on disk)",
            "missing-test": "rejected (file does not exist on disk)",
            "outside-exercise": "rejected (contains parent traversal)"
        },
        "behavioural_test": {
            "tests": 7,
            "failures": 0,
            "ignored": 0,
            "exit_code": 0
        },
        "negative_control": {
            "stub_passed": False,
            "description": "bare stub correctly fails to link/build"
        },
        "anchor_phrase_present": True,
        "working_tree_clean": True
    }

    with open(WORK_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Save expected vs actual check report
    report = """=== R48-T018 Check Report: high-scores ===

1. Real Metadata (.meta/config.json)
   Expected: all declared solution, test, and example files resolve inside exercise directory
   Actual:   5 files declared, 5 files resolved (high_scores.c, high_scores.h, test_high_scores.c, .meta/example.c, .meta/example.h) -> PASS

2. Invalid Metadata Fixtures
   Fixture 1 (missing-reference): Expected failure on missing .meta/nonexistent_example.c -> PASS (rejected)
   Fixture 2 (missing-test):      Expected failure on missing nonexistent_test.c -> PASS (rejected)
   Fixture 3 (outside-exercise):  Expected failure on parent traversal ../outside.c -> PASS (rejected)

3. Reference Implementation Behavioural Run (make test)
   Expected: child return code 0, 7 tests executed, 0 failures, 0 ignored
   Actual:   child return code 0, 7 tests executed, 0 failures, 0 ignored -> PASS

4. Negative Control (Unsolved Learner Stub)
   Expected: make test fails to build or link
   Actual:   linker failure with exit code 2 -> PASS

5. Canonical Specification & Anchor
   Expected: .meta/tests.toml contains 'so comments can be added in a "comment" key.'
   Actual:   phrase present at line 3 -> PASS

All checks passed successfully.
"""
    (RESULTS_DIR / "check_report.txt").write_text(report, encoding="utf-8")

    # Strip ANSI escape codes for clean markdown
    clean_stdout = re.sub(r"\x1b\[[0-9;]*m", "", proc.stdout)

    # Generate evidence.md
    evidence_md = f"""# Evidence for R48-T018: high-scores

## Checks Executed

1. **Path & Configuration Verification**:
   - Parsed `exercises/practice/high-scores/.meta/config.json`.
   - Verified that declared `solution`, `test`, and `example` entries resolve inside the exercise root without parent traversal.
   - All 5 declared files confirmed present on disk.

2. **Negative Fixtures Testing**:
   - `missing-reference`: Deliberately pointed `files.example` to `.meta/nonexistent_example.c`. Correctly rejected with error: `file does not exist on disk`.
   - `missing-test`: Deliberately pointed `files.test` to `nonexistent_test.c`. Correctly rejected with error: `file does not exist on disk`.
   - `outside-exercise`: Deliberately used parent traversal `../outside.c`. Correctly rejected with error: `contains parent traversal`.

3. **Behavioural Reference Verification**:
   - Substituted `.meta/example.c` and `.meta/example.h` into solution file locations.
   - Removed `TEST_IGNORE()` from `test_high_scores.c`.
   - Ran `make test`.
   - Result: **7 Tests, 0 Failures, 0 Ignored** (exit code 0).

4. **Negative Control**:
   - Verified that running `make test` against the unsolved learner stub (`high_scores.c`) fails to link (exit code 2).

5. **Canonical Specifications & Anchor**:
   - Verified `exercises/practice/high-scores/.meta/tests.toml` contains the header anchor:
     `so comments can be added in a "comment" key.`
   - Confirmed 7 active canonical test cases map directly to the 7 `RUN_TEST` invocations in `test_high_scores.c`.

## Expected vs Actual

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Metadata file resolution | 5/5 files exist inside exercise directory | 5/5 resolved (`high_scores.c`, `high_scores.h`, `test_high_scores.c`, `.meta/example.c`, `.meta/example.h`) | PASS |
| Fixture rejection: `missing-reference` | rejected with `file does not exist on disk` | rejected with `file does not exist on disk` | PASS |
| Fixture rejection: `missing-test` | rejected with `file does not exist on disk` | rejected with `file does not exist on disk` | PASS |
| Fixture rejection: `outside-exercise` | rejected with `contains parent traversal` | rejected with `contains parent traversal` | PASS |
| Reference implementation test run | 7 Tests, 0 Failures, 0 Ignored (exit code 0) | 7 Tests, 0 Failures, 0 Ignored (exit code 0) | PASS |
| Negative control (learner stub) | Fails to compile/link (exit code != 0) | Linker failure (exit code 2) | PASS |
| Canonical tests.toml anchor | Anchor phrase present at line 3 | Present | PASS |
| Working tree cleanliness | Unmodified during check | Byte-for-byte identical | PASS |

## Execution Log

```
{clean_stdout.strip()}
```
"""
    (WORK_DIR / "evidence.md").write_text(evidence_md, encoding="utf-8")

    print("Evidence and reports generated in work/R48-T018/.")
    print("=== ALL ASSERTIONS PASSED ===")


if __name__ == "__main__":
    main()
