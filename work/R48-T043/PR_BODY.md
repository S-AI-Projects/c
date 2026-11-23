## Description
Mutation-driven regression analysis and test verification for `exercises/practice/variable-length-quantity`.
- Identified and evaluated deliberate mutants in `encode()` against canonical VLQ specification.
- Primary mutant: pre-condition loop (`while (integer)`) instead of post-condition loop (`do ... while (integer)`), exposing the mistaken assumption that zero produces no bytes.
- Reduced rejecting test case to the smallest input allowed by specification: `integers = { 0x0 }` (length 1), rejected by canonical test `test_zero` (`35c9db2e-f781-4c52-b73b-8e76427defd0`) with `Expected 1 Was 0`.
- Secondary mutant: premature continuation check (`while (integer > 0x7f)`), rejected by `test_smallest_double_byte` (`77b07086-bd3f-4882-8476-8dcafee79b1c`) with `Expected 2 Was 1`.
- Added learner debugging hint in `exercises/practice/variable-length-quantity/.docs/hints.md` explaining the contract and minimal diagnostic inputs without giving away the full solution.
- Added comprehensive maintenance documentation in `docs/maintenance/variable-length-quantity.md` and mirrored to `.meta/MAINTENANCE.md`.
- Added automated check in `work/R48-T043/check.py` and course check in `tools/course_checks/r48-t043.py`.
- Working tree learner stubs (`variable_length_quantity.c`, `variable_length_quantity.h`) remain completely unsolved.

## Related Issue
Fixes: #43

## Type of Change
- [x] Documentation
- [x] Tests
- [x] Refactoring / Maintenance

## Changes Made
- Added `exercises/practice/variable-length-quantity/.docs/hints.md` providing debugging hints for zero-value encoding, multi-byte continuation conditions, and diagnostic inputs.
- Added `docs/maintenance/variable-length-quantity.md` (and `.meta/MAINTENANCE.md`) recording contract specifications, case-to-output mapping for all 26 cases, primary and secondary mutant diffs, rejecting test IDs, and minimal input reduction.
- Created `work/R48-T043/check.py` and `tools/course_checks/r48-t043.py` automated verification scripts.
- Verified that all 26 tests pass against the original reference in an isolated scratch directory with 0 failures and 0 ignored.
- Verified that the primary mutant fails `test_zero` with `Expected 1 Was 0` (exit code 2).
- Saved verification evidence in `work/R48-T043/` (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results
- Ran `python3 work/R48-T043/check.py` and `python3 tools/course_checks/r48-t043.py`.
- **26/26 tests passed** against original reference with 0 failures and 0 ignored.
- **Primary mutant failed** assertion in `test_zero` (`35c9db2e-f781-4c52-b73b-8e76427defd0`) with `Expected 1 Was 0`.
- **Secondary mutant failed** assertion in `test_smallest_double_byte` (`77b07086-bd3f-4882-8476-8dcafee79b1c`) with `Expected 2 Was 1`.
- Learner starter files (`variable_length_quantity.c`, `variable_length_quantity.h`) in working tree remain unsolved.

## Done When Checklist
- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The original passes and the documented mutant fails the named assertion; changing only formatting is not a valid mutation.
- [x] The hint explains the underlying contract and provides a small diagnostic input without publishing the entire reference solution.

## Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.

## General PR Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [x] I have addressed previous review feedback, if applicable.

## Additional Notes
All criteria in the "Done when" and "Submission" checklists for task R48-T043 are fully satisfied.
