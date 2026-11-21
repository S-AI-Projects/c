# Evidence for R48-T018: high-scores

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
=== R48-T018: high-scores Path & Configuration Verification ===
Exercise directory: /Users/tanmayaverma/Documents/Snai/c/exercises/practice/high-scores

--- Validating Real .meta/config.json ---
OK:   Real config valid: resolved 5 files inside exercise directory
OK:     resolved: high_scores.c
OK:     resolved: high_scores.h
OK:     resolved: test_high_scores.c
OK:     resolved: .meta/example.c
OK:     resolved: .meta/example.h

--- Testing Metadata Fixtures ---
OK:   Fixture 'missing-reference' correctly rejected (file does not exist on disk)
OK:   Fixture 'missing-test' correctly rejected (file does not exist on disk)
OK:   Fixture 'outside-exercise' correctly rejected (contains parent traversal)

--- Running Behavioural Reference Check ---
Compiling tests.out
./test_high_scores.c:94:test_latest_score:PASS
./test_high_scores.c:95:test_personal_best:PASS
./test_high_scores.c:96:test_personal_top_three_from_a_list_of_scores:PASS
./test_high_scores.c:97:test_personal_top_highest_to_lowest:PASS
./test_high_scores.c:98:test_personal_top_when_there_is_a_tie:PASS
./test_high_scores.c:99:test_personal_top_when_there_are_less_than_3:PASS
./test_high_scores.c:100:test_personal_top_when_there_is_only_one:PASS

-----------------------
7 Tests 0 Failures 0 Ignored 
OK
OK:   Reference test run: 7 Tests, 0 Failures, 0 Ignored (child exit 0)

--- Testing Negative Control (Unsolved Learner Stub) ---
OK:   Bare stub correctly failed to build/link (exit code 2)

--- Checking tests.toml Anchor and Test Mapping ---
OK:   Anchor phrase found in tests.toml: 'so comments can be added in a "comment" key.'
OK:   Found exactly 7 RUN_TEST invocations matching canonical included cases
OK:   Exercise directory byte-for-byte identical before and after run

=== Summary: 0 failure(s) ===

R48-T018 checks PASSED successfully.
```
