## Description
Algorithmic complexity study, operation counting, and empirical scaling analysis of `normalize_clock` for `exercises/practice/clock`.
- Pinned reference implementation: `exercises/practice/clock/.meta/example.c#L6` at commit `ffe5457`.
- Defined three valid input regimes from the exercise domain:
  - **Size 1 (Standard in-range)**: `(hour = 8, minute = 0)` from canonical test `test_on_the_hour` (`a577bacc-106b-496e-9792-b3083ea8705e`). Executes 0 loop iterations ($k_m=0, k_h=0$), performing exactly 6 elementary operations in $O(1)$ constant time.
  - **Size 2 (Positive rollover)**: `(hour = 201, minute = 3001)` from canonical test `test_hour_and_minutes_roll_over_continuously` (`be60810e-f5d9-4b58-9351-a9d1e90e660c`). Handled via integer division and modulo in exactly 6 elementary operations ($O(1)$ time).
  - **Size 3 (Negative rollback)**: `(hour = -121, minute = -5810)` from canonical test `test_negative_hour_and_minutes_both_roll_over_continuously` (`51d41fcf-491e-4ca0-9cae-2aa4f0163ad4`). Relies on iterative borrow loops ($k_m = 97, k_h = 10$), performing 317 elementary operations and scaling linearly as $O(|minute|/60 + |hour|/24)$.
- Built complete Branch / Operation Table documenting condition checks, arithmetic additions/subtractions, divisions, modulos, and total operation counts.
- Empirically measured pure algorithmic execution time using monotonic timers inside C (5 repetitions of 200,000 iterations per size) and clearly distinguished algorithm work (~1.3 ns to ~115 ns/call) from compiler invocation and process-startup overhead (~80 to 150 ms).
- Pre-timing correctness asserted for all test cases before timing; no speedup claimed without measurements.
- Added comprehensive complexity and invariant comment adjacent to `normalize_clock` in `exercises/practice/clock/.meta/example.c`.
- Added preserved `comment` keys documenting domain sizes in `exercises/practice/clock/.meta/tests.toml`.
- Added detailed maintenance documentation in `docs/maintenance/clock.md` (and mirrored to `exercises/practice/clock/.meta/MAINTENANCE.md`).
- Added automated check script `work/R48-T045/check.py` and course check `tools/course_checks/r48-t045.py`.
- Working tree learner starter stubs (`clock.c`, `clock.h`) remain completely unsolved.

## Related Issue
Fixes: #45

## Type of Change
- [x] Documentation
- [ ] Bug Fix
- [ ] New Feature
- [ ] UI/UX Improvement
- [x] Performance Improvement / Complexity Study
- [x] Tests
- [x] Refactoring / Maintenance
- [ ] CI/CD

## Changes Made
- `exercises/practice/clock/.meta/example.c`: Added precise invariant, precondition/postcondition, and piecewise complexity comments adjacent to `normalize_clock`.
- `exercises/practice/clock/.meta/tests.toml`: Added `comment` keys identifying the three domain sizes on canonical cases `a577bacc-106b-496e-9792-b3083ea8705e`, `be60810e-f5d9-4b58-9351-a9d1e90e660c`, and `51d41fcf-491e-4ca0-9cae-2aa4f0163ad4`.
- `docs/maintenance/clock.md` & `exercises/practice/clock/.meta/MAINTENANCE.md`: Created maintenance guide detailing domain input sizes, formal invariants, branch/operation table, empirical timings, distinction of algorithm work vs process startup, and limits of the conclusion.
- `work/R48-T045/check.py` & `tools/course_checks/r48-t045.py`: Created automated verification scripts verifying unsolved learner stubs, maintenance documentation, tests.toml comments, reference execution of 52 tests, pre-timing correctness assertion, operation counts, and median latency measurements.
- `work/R48-T045/`: Saved verification evidence (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results
- Ran `python3 work/R48-T045/check.py` and `python3 tools/course_checks/r48-t045.py`.
- **52/52 canonical tests passed** against reference implementation with 0 failures and 0 ignored.
- **Learner starter stub** (`clock.c`, `clock.h`) in working tree remains completely unsolved.
- **Pre-timing assertions**: Correctness verified for all 3 domain inputs prior to timing.
- **Operation bounds verified**:
  - Size 1 (`8, 0`): 6 operations ($O(1)$)
  - Size 2 (`201, 3001`): 6 operations ($O(1)$)
  - Size 3 (`-121, -5810`): 317 operations ($O(k_m + k_h)$)
- **Measured Algorithm Runtime (Median ns/call)**:
  - Size 1: 1.29 ns/call
  - Size 2: 1.35 ns/call
  - Size 3: 115.82 ns/call
- **Infrastructure Overhead**: Compilation overhead ~84-102 ms, process startup ~140-160 ms (isolated from algorithm work).

## Done When Checklist
- [x] The named cases (so comments can be added in a "comment" key.) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The cost statement distinguishes algorithm work from process-startup or compilation time.
- [x] All measured inputs satisfy the specification; correctness is asserted before timing and no speedup is claimed without measurements.

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
All criteria in the "Done when" and "Submission" checklists for task R48-T045 are fully satisfied.
