## Description
Review and document the canonical test case decisions for `exercises/practice/darts` in accordance with Task R48-T041:
- Reviewed all 13 canonical test cases in `exercises/practice/darts/.meta/tests.toml` (13 included, 0 excluded).
- Resolved and documented precise rationales for UUIDs `9033f731-0a3a-4d9c-b1c0-34a1c8362afb` ("Missed target"), `4c9f6ff4-c489-45fd-be8a-1fcb08b4d0ba` ("On the outer circle"), and `14378687-ee58-4c9b-a323-b089d5274be8` ("On the middle circle") against C language operations (`sqrt`, relational `<=`, off-board score fallback, and negative coordinate squaring).
- Added comments in `exercises/practice/darts/.meta/tests.toml` using both TOML comments and preserved `comment` keys so comments are retained across `configlet sync`.
- Added a comprehensive maintenance guide and mapping table in `docs/maintenance/darts.md` (and mirrored in `exercises/practice/darts/.meta/MAINTENANCE.md`).
- Implemented automated verification checks in `work/R48-T041/check.py` and `tools/course_checks/r48-t041.py`, validating scratch-copy reference compilation and test execution via `make test` without mutating working tree files.

## Related Issue
Fixes: #41

## Type of Change
- [x] Documentation
- [x] Tests
- [x] Refactoring / Maintenance

## Changes Made
- **Metadata Update**: Added TOML comments and preserved `comment` keys to `exercises/practice/darts/.meta/tests.toml` for UUIDs:
  - `9033f731-0a3a-4d9c-b1c0-34a1c8362afb`: Explaining Euclidean distance calculation via `sqrt(x*x + y*y)` in `<math.h>` for `(-9.0F, 9.0F)` yielding $\approx 12.73 > 10.0$ (`OUTER_CIRCLE_RADIUS`), evaluating false across concentric bounds and returning `OFF_BOARD_SCORE = 0`.
  - `4c9f6ff4-c489-45fd-be8a-1fcb08b4d0ba`: Explaining outer circle boundary inclusivity at `(0.0F, 10.0F)` with distance $10.0\text{F} \le 10.0\text{F}$ evaluating true and returning `OUTER_CIRCLE_SCORE = 1`.
  - `14378687-ee58-4c9b-a323-b089d5274be8`: Explaining middle circle boundary test at `(-5.0F, 0.0F)` where coordinate squaring properly handles negative axes with distance $5.0\text{F} \le 5.0\text{F}$ evaluating true and returning `MIDDLE_CIRCLE_SCORE = 5`.
- **Maintenance Documentation**: Added `docs/maintenance/darts.md` and `exercises/practice/darts/.meta/MAINTENANCE.md` with:
  - Pinned reference implementation source: `exercises/practice/darts/.meta/example.c#L14` at `ffe5457`.
  - Complete 13-case canonical mapping table detailing UUID, description, test name, input coordinates, expected score, C evaluation logic, and status.
  - In-depth analysis of the 3 specified UUIDs and C arithmetic/floating-point considerations.
  - Tool prerequisites, reproduction commands, and runner architecture.
- **Automated Check Runner**: Added `work/R48-T041/check.py` and `tools/course_checks/r48-t041.py`:
  - Dynamically resolves paths from `.meta/config.json`.
  - Asserts learner stub (`darts.c`, `darts.h`) is unsolved in working tree.
  - Verifies TOML parsing, canonical counts (13 total, 13 included, 0 excluded), and target UUID rationales.
  - Verifies key preservation across `configlet sync`.
  - Copies exercise to an isolated temporary scratch directory, substitutes reference implementation, removes `TEST_IGNORE()`, and runs `make test`.
  - Verifies 13 tests run, 13 pass, 0 fail, 0 ignored, and exit code 0.
- **Evidence Persistence**: Captured verification outputs in `work/R48-T041/`:
  - `check_output.txt`
  - `expected_vs_actual.json`
  - `inputs.json`
  - `results.json`
  - `tool_versions.txt`

## Testing & Verification Results
- Executed `python3 work/R48-T041/check.py` and `python3 tools/course_checks/r48-t041.py`.
- **13/13 tests passed** with 0 failures and 0 ignored against reference implementation.
- Working tree remains completely clean and unmutated; learner starter files (`darts.c`, `darts.h`) remain unsolved stubs.
- Canonical test counts recorded before and after:
  - Total cases: 13
  - Included: 13 (before: 13, after: 13)
  - Excluded: 0 (before: 0, after: 0)
- Configlet preservation verified via `configlet sync --exercise darts --tests include --update --yes --offline`.

## Done When Checklist
- [x] The named cases (so comments can be added in a "comment" key.) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] Each of 9033f731-0a3a-4d9c-b1c0-34a1c8362afb, 4c9f6ff4-c489-45fd-be8a-1fcb08b4d0ba, 14378687-ee58-4c9b-a323-b089d5274be8 has a rationale that names the test or language limitation; TOML still parses.
- [x] Included/excluded counts are recorded before and after; every changed inclusion has a corresponding passing generated test.

## Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.

## Review Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [x] I have addressed previous review feedback, if applicable.

## Additional Notes
All requirements for Task R48-T041 are fully satisfied and independently verified.
