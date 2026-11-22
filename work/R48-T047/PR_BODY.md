## Description
Language-specific guidance and memory ownership documentation for `exercises/practice/nucleotide-count`.
- Examined array lengths, null termination, and caller/callee memory ownership across the C track interface.
- Selected and documented the construct actually used by the maintained reference implementation (`exercises/practice/nucleotide-count/.meta/example.c#L16`): `calloc(1, max_length)` dynamic heap allocation with caller/callee memory ownership and automatic zeroed null termination.
- Implemented a small executable standalone micro-example (`format_nucleotide_summary`) that reproduces the memory allocation and error semantics without solving the entire exercise.
- Provided standard valid input (`'A'`, count `3`) and contrasting invalid input (`'X'`, count `0`) demonstrating why the outcomes differ and how `calloc` guarantees safe deallocation and null termination for both paths.
- Documented three critical learner pitfalls: returning a local stack buffer (dangling pointer), returning a string literal on error (`free()` invalid pointer abort), and using `malloc` without zero-initialization (uninitialized indeterminate bytes).
- Preserved all 5 canonical test case descriptions in `exercises/practice/nucleotide-count/.meta/tests.toml` while adding explanatory `comment` keys detailing the memory ownership contract.
- Added comprehensive maintenance documentation in `docs/maintenance/nucleotide-count.md` and mirrored to `.meta/MAINTENANCE.md`.
- Implemented automated verification checker in `work/R48-T047/check.py` and course check in `tools/course_checks/r48-t047.py`.
- Verified that all 5 canonical test cases pass against the reference implementation in an isolated scratch directory under `make test` and `make memcheck` (AddressSanitizer) with zero leaks and zero errors.
- Verified that learner starter stubs (`nucleotide_count.c`, `nucleotide_count.h`) in the working tree remain completely untouched and unsolved.

## Related Issue
Fixes: #47

## Type of Change
- [x] Documentation
- [x] Tests
- [x] Refactoring / Maintenance

## Changes Made
- `exercises/practice/nucleotide-count/.docs/hints.md`: Added comprehensive C-specific guidance comparing array lengths, null termination, and caller/callee memory ownership, citing `example.c#L16`, providing an executable standalone micro-example with expected outputs, explaining learner pitfalls, and linking official C99, cppreference, and POSIX language standards.
- `exercises/practice/nucleotide-count/.meta/tests.toml`: Added informative `comment` keys to all 5 canonical test cases explaining expected string outputs and the caller-freed heap buffer contract.
- `docs/maintenance/nucleotide-count.md` & `exercises/practice/nucleotide-count/.meta/MAINTENANCE.md`: Created detailed maintenance guide documenting C interface memory model, canonical test mappings, and learner pitfalls.
- `work/R48-T047/check.py` & `tools/course_checks/r48-t047.py`: Implemented automated checker validating untouched learner stubs, scratch-directory reference test execution (5/5 passed, 0 failures, 0 ignored), AddressSanitizer clean memory check, micro-example compilation and dual-output assertions agreeing with published hint, and preserved tests.toml comments.
- `work/R48-T047/`: Recorded complete verification artifacts (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results
- Ran `python3 work/R48-T047/check.py` and `python3 tools/course_checks/r48-t047.py`.
- **5/5 canonical test cases passed** against reference implementation with 0 failures and 0 ignored.
- **AddressSanitizer (`make memcheck`) passed** with zero memory leaks and zero invalid accesses.
- **Micro-example compiled & executed cleanly under ASan**:
  - Valid output (`'A'`, count `3`): `Output 1 (valid): A:3`
  - Contrasting output (`'X'`, count `0`): `Output 2 (invalid): `
  - Both outputs asserted and verified to agree with published hint in `hints.md`.
- **Working tree learner stubs** (`nucleotide_count.c`, `nucleotide_count.h`) remain completely unsolved.

## Done When Checklist
- [x] The named cases (so comments can be added in a "comment" key.) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] Both micro-example outputs are asserted by the checker and agree with the published hint.
- [x] The guidance names a construct actually present in the reference and explains its relevance to this exercise.

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
All criteria in the "Done when" and "Submission" checklists for task R48-T047 are fully satisfied.
