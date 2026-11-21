# Evidence for R48-T019: all-your-base

## Summary of Executed Scenarios

The isolated test runner `tools/course_checks/r48-t019.py` was executed across all four verification scenarios:

1. **`real` scenario**:
   - Substituted `.meta/example.c` and `.meta/example.h` into a temporary scratch directory.
   - Enabled all test cases in `test_all_your_base.c`.
   - Executed `make test`.
   - Result: **21 Tests, 0 Failures, 0 Ignored**, exit code 0.

2. **`failing` scenario**:
   - Deliberately introduced a logic error in `all_your_base.c` in the scratch copy.
   - Verified that test failures were detected and propagated with exit code 1.

3. **`empty` scenario**:
   - Commented out all `RUN_TEST` calls in `test_all_your_base.c` in the scratch copy.
   - Verified that the runner detected zero executed cases and exited with code 1.

4. **`stub` scenario**:
   - Ran `make test` against the unsolved learner stub (`all_your_base.c`).
   - Verified that compilation failed due to missing declarations/definitions with exit code 1.

5. **Learner Invariance**:
   - SHA-256 hashes of all learner files (`all_your_base.c`, `all_your_base.h`, `test_all_your_base.c`, `makefile`) and metadata files were verified byte-identical before and after each run.

## Named Canonical Cases Verified

- `[232fa4a5-e761-4939-ba0c-ed046cd0676a]`: `invalid positive digit` -> `test_invalid_positive_digit` (PASS)
- `[14238f95-45da-41dc-95ce-18f860b30ad3]`: `output base is one` -> `test_output_base_is_one` (PASS)

## Real Scenario Execution Log

```
=== Scenario: real ===
Child exit:    0
Unity summary: 21 Tests, 0 Failures, 0 Ignored
Runner status: PASSED
Exit code:     0
Reason:        all 21 cases passed with 0 failures and 0 ignored

--- stdout snippet ---

./test_all_your_base.c:222:test_multiple_zeros:[42mPASS[00m
./test_all_your_base.c:223:test_leading_zeros:[42mPASS[00m
./test_all_your_base.c:224:test_input_base_is_one:[42mPASS[00m
./test_all_your_base.c:225:test_input_base_is_zero:[42mPASS[00m
./test_all_your_base.c:226:test_input_base_is_negative:[42mPASS[00m
./test_all_your_base.c:227:test_negative_digit:[42mPASS[00m
./test_all_your_base.c:228:test_invalid_positive_digit:[42mPASS[00m
./test_all_your_base.c:229:test_output_base_is_one:[42mPASS[00m
./test_all_your_base.c:230:test_output_base_is_zero:[42mPASS[00m
./test_all_your_base.c:231:test_output_base_is_negative:[42mPASS[00m
./test_all_your_base.c:232:test_both_bases_are_negative:[42mPASS[00m

-----------------------
21 Tests 0 Failures 0 Ignored 
[42mOK[00m
```
