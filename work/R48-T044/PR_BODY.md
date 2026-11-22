## R48-T044: Clarify mstrlen in the crypto-square reference

### Summary

This PR improves readability in the reference implementation `exercises/practice/crypto-square/.meta/example.c` by clarifying the local state and invariant in `mstrlen`:

1. **Scoped Readability Refactoring**:
   - Renamed ambiguous local accumulator `size_t i = 0` to `size_t normalized_len = 0` in `mstrlen`. While single-letter identifiers like `i` conventionally represent loop indices, here it accumulates the count of valid normalized alphanumeric characters.
   - Added an exercise-specific invariant comment:
     ```c
     /* Invariant: only alphanumeric characters are retained in normalized plaintext,
      * which determines the crypto-square rectangle dimensions (r x c). */
     ```
   - Preserved function signature, return type (`size_t`), ordering, and error behavior.
   - Preserved public API `char *ciphertext(const char *input)`.

2. **Integrity & Verification**:
   - Learner starter stub files (`crypto_square.c`, `crypto_square.h`) remain untouched and unsolved.
   - Verified that all 8 test cases in `test_crypto_square.c` pass (8 run, 0 failures, 0 ignored) and AddressSanitizer memory check (`make memcheck`) passes cleanly.
   - Verified before/after behavioral equivalence across all enabled cases.
   - Added automated verification script `work/R48-T044/check.py` and course check `tools/course_checks/r48-t044.py`.

### Verification Results

- **Canonical cases baseline**: All 9 cases in `.meta/tests.toml` preserved (descriptions recreated, reimplements recreated, other keys preserved).
- **Test execution in scratch directory**: 8 tests run, 0 failures, 0 ignored (Exit code 0).
- **Memory safety**: `make memcheck` passed with zero errors under AddressSanitizer.
- **Working tree integrity**: Preserved, learner stub completely unsolved.

### Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.
