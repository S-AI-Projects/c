## Description

Scoped readability refactoring of the reference implementation in `exercises/practice/crypto-square/.meta/example.c` focusing on `mstrlen`:
- Clarified the local accumulator state in `mstrlen`: renamed ambiguous `size_t i = 0` to `size_t normalized_len = 0`. While single-letter identifiers like `i` conventionally denote loop indices, here it accumulates the count of valid normalized alphanumeric characters.
- Added an exercise-specific invariant comment explaining that only alphanumeric characters are retained in normalized plaintext, which determines the crypto-square rectangle dimensions (r x c).
- Retained exact return types, ordering, error behavior, and public API (`char *ciphertext(const char *input)`).
- Learner starter stub files (`crypto_square.c`, `crypto_square.h`) remain untouched and unsolved.
- Added automated check in `work/R48-T044/check.py` and course check in `tools/course_checks/r48-t044.py`.
- Verified that all 8 test cases pass against the reference in an isolated scratch directory with 0 failures and 0 ignored, with AddressSanitizer passing cleanly (`make memcheck`).
- Verified 100% behavioral equivalence between before and after versions on all test inputs.

## Related Issue

Fixes: #44

## Type of Change

- [x] Documentation
- [x] Tests
- [x] Refactoring / Maintenance

## Changes Made

- Modified `exercises/practice/crypto-square/.meta/example.c`: clarified `mstrlen` local state (`normalized_len`) and added the exercise-specific invariant comment.
- Created `work/R48-T044/check.py` and `tools/course_checks/r48-t044.py` automated verification scripts.
- Verified test execution (8/8 passed, 0 failures, 0 ignored, exit code 0) and memory safety under AddressSanitizer (`make memcheck`).
- Saved verification evidence in `work/R48-T044/` (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results

- Ran `python3 work/R48-T044/check.py` and `python3 tools/course_checks/r48-t044.py`.
- **8/8 tests passed** against both original and refactored reference with 0 failures and 0 ignored.
- **make memcheck** passed with zero memory errors under AddressSanitizer.
- Working tree learner starter files (`crypto_square.c`, `crypto_square.h`) remain completely unsolved.
- Baseline cases in `tests.toml` preserved: all 9 cases verified (descriptions recreated, reimplements recreated, other keys preserved).

## Done When Checklist

- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The diff identifies one concrete readability improvement and explains why it helps this exercise.
- [x] Before/after outputs agree on all enabled cases; no new dependency or public API change is introduced.

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

## Additional Notes

All criteria in the "Done when" and "Submission" checklists for task R48-T044 are fully satisfied.
