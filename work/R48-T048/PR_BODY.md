## Description
Map and verify the maintained files and exercise metadata for `exercises/practice/word-count`.
- Pinned reference implementation: `exercises/practice/word-count/.meta/example.c#L9` at commit `ffe5457`.
- Verified and documented the file-role map (`files.solution`, `files.test`, `files.example`, `files.editor`) in `.meta/config.json`.
- Implemented robust path validation:
  - Parses the `files` object directly rather than searching filenames heuristically.
  - Rejects parent traversal (`..`) and absolute path prefixes (`/`), ensuring all components resolve strictly within `exercises/practice/word-count`.
  - Verifies that every declared file exists on disk.
- Tested path validation against three deliberately invalid metadata fixtures:
  1. `missing-reference` (`files.example = [".meta/nonexistent_reference.c"]`) $\to$ fails with `FileNotFoundError`.
  2. `missing-test` (`files.test = ["test_nonexistent_word_count.c"]`) $\to$ fails with `FileNotFoundError`.
  3. `outside-exercise` (`files.solution = ["../outside_solution.c"]`) $\to$ fails with `ValueError` (parent traversal rejected).
  - Confirmed that real metadata in `.meta/config.json` passes validation with 100% accuracy.
- Documented and verified how the test runner finds:
  - `exercises/practice/word-count/.meta/tests.toml`: via standard Exercism convention path `<exercise>/.meta/tests.toml` for canonical synchronization and inclusion tracking.
  - `exercises/practice/word-count/.meta/example.c`: via dynamic parsing of `files.example` in `.meta/config.json`, which is then substituted into the solution path inside an isolated scratch workspace for CI evaluation.
- Verified canonical test specification (`tests.toml`) key handling rules:
  - **Recreate every `description` key/value pair**: verified across all 15 cases.
  - **Recreate every `reimplements` key/value pair, where they exist in problem-specifications**: verified case `4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3` reimplementing `4185a902-bdb0-4074-864c-f416e42a0f19`.
  - **Preserve any other key/value pair**: verified preservation of `include = false` and `comment = "Reimplemented"` on case `4185a902-bdb0-4074-864c-f416e42a0f19`.
  - Verified two successive generations with `configlet sync` produce bit-for-bit identical outputs without dropping cases.
- Executed isolated test suite against reference implementation in a scratch temporary directory:
  - 14/14 enabled canonical tests passed with 0 failures and 0 ignored.
  - Working tree learner starter stub (`word_count.c`) remains completely unsolved (`#include "word_count.h"`).
- Added comprehensive maintenance documentation in `docs/maintenance/word-count.md` (and mirrored to `exercises/practice/word-count/.meta/MAINTENANCE.md`).
- Added automated verification script `work/R48-T048/check.py` and course check `tools/course_checks/r48-t048.py`.

## Related Issue
Fixes: #48

## Type of Change
- [x] Documentation
- [x] Metadata Verification / Maintenance
- [x] Tests

## Changes Made
- `docs/maintenance/word-count.md` & `exercises/practice/word-count/.meta/MAINTENANCE.md`: Added comprehensive exercise file-role map, runner discovery explanation, maintained vs generated file classification, key handling rules, canonical case-to-output mapping table, isolated verification procedure, reproducible commands, and completion checklists.
- `tools/course_checks/r48-t048.py`: Created automated course check verifying learner stub, path parsing and traversal rejection, invalid fixtures, runner discovery, canonical key handling, and scratch `make test` execution.
- `work/R48-T048/check.py`: Automated verification script generating test artifacts.
- `work/R48-T048/`: Saved verification evidence (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`, `PR_BODY.md`).

## Testing & Verification Results
- Executed `python3 work/R48-T048/check.py` and `python3 tools/course_checks/r48-t048.py`.
- **Working Tree Stub**: Verified `word_count.c` contains only `#include "word_count.h"` and is unsolved.
- **Metadata Fixtures**:
  - `missing-reference`: correctly raised `FileNotFoundError`.
  - `missing-test`: correctly raised `FileNotFoundError`.
  - `outside-exercise`: correctly raised `ValueError` (parent traversal rejected).
  - Real metadata: passed validation.
- **Canonical Sync & Key Handling**:
  - 15 total cases in `tests.toml`.
  - Recreated all `description` and `reimplements` pairs.
  - Preserved `comment` and `include = false` pairs.
  - Confirmed 2-generation reproducibility.
- **Scratch `make test`**:
  - Return code: 0.
  - Executed tests: 14.
  - Failures: 0.
  - Ignored: 0.
  - All 14 tests reported `PASS`.

## Done When Checklist
- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The real config passes; all three deliberately invalid metadata fixtures fail for the intended reason.
- [x] The maintenance document names the real stub, reference and test paths and distinguishes generated artifacts.

## Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.

## General PR Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [x] I have addressed previous review feedback, if applicable.
