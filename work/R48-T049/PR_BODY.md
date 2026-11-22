## Description
Focused isolated test runner and maintenance verification for `exercises/practice/zebra-puzzle` (Task R48-T049).
- Tested the reference implementation from `exercises/practice/zebra-puzzle/.meta/config.json` in an isolated temporary copy (`tempfile.TemporaryDirectory`).
- Resolved paths dynamically (`solution`, `test`, `example`) from `.meta/config.json`.
- Substituted the reference implementation only in the scratch copy; enabled all canonical cases and executed `make test` using the supplied makefile and Unity test framework.
- Evaluated and validated three execution conditions:
  1. **Real Reference**: Passes all 2 canonical tests (`test_who_drinks_water`, `test_who_owns_the_zebra`) with 0 failures, 0 ignored, and exit code 0.
  2. **Deliberately Failing Reference**: Tested with mutated solution returning incorrect resident; Unity caught the assertion failure (`Expected Norwegian Was Ukrainian`), child exit code 2 was propagated, and runner exited non-zero.
  3. **Empty Test Selection**: Tested with 0 active tests; runner reported zero-test run and exited non-zero (exit code 1).
- Enforced cryptographic protection of learner starter files: computed SHA-256 hashes of `zebra_puzzle.c` and `zebra_puzzle.h` before and after every run (including interrupted runs); verified bit-for-bit identity and verified the working tree learner files remain completely unsolved.
- Guaranteed automatic temporary file cleanup via Python context manager.
- Preserved user-added `comment` keys across `configlet sync`.
- Added comprehensive maintenance documentation in `docs/maintenance/zebra-puzzle.md` (and mirrored to `exercises/practice/zebra-puzzle/.meta/MAINTENANCE.md`).
- Added reusable course check script under `tools/course_checks/r48-t049.py`.

## Related Issue
Fixes: #49

## Type of Change
- [x] Documentation
- [x] Tests
- [x] Refactoring / Maintenance

## Changes Made
- `tools/course_checks/r48-t049.py` (new): Isolated test runner for `exercises/practice/zebra-puzzle` supporting path resolution, scratch copy isolation, test activation, Unity result parsing, failure propagation, and cryptographic hash invariant verification.
- `docs/maintenance/zebra-puzzle.md` & `exercises/practice/zebra-puzzle/.meta/MAINTENANCE.md` (new): Detailed maintenance guide documenting the isolated runner architecture, tool requirements, reproduction commands, scenario results, hash tables, and case-to-output mapping.
- `exercises/practice/zebra-puzzle/.meta/tests.toml`: Added preserved `comment` keys documenting canonical tests 1 and 2 across `configlet sync`.
- `work/R48-T049/check.py`: Automated verification suite executing the runner tests and generating evidence.
- `work/R48-T049/`: Evidence files generated (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results
- Ran `python3 work/R48-T049/check.py` and `python3 tools/course_checks/r48-t049.py`.
- **Scenario 1 (Real Reference)**: 2/2 tests passed (`test_who_drinks_water`, `test_who_owns_the_zebra`), 0 failures, 0 ignored, exit code 0.
- **Scenario 2 (Deliberate Failure)**: Assertion failure detected and propagated, exit code 2.
- **Scenario 3 (Zero Tests)**: 0 tests executed detected and rejected, exit code 1.
- **Hash Invariant**: SHA-256 hashes of `zebra_puzzle.c` (`fea05bdb6415d98b...`) and `zebra_puzzle.h` (`2a72bae85ef42738...`) verified bit-for-bit identical before and after all runs.
- **Learner Stub**: Unsolved starter files in working tree remain completely untouched.

## Done When Checklist
- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] Success, assertion failure and zero-test runs produce the correct exit status; temporary files are cleaned up.
- [x] The learner file hashes are identical before and after every run, including an interrupted or failing run.

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
