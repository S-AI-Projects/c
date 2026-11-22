## Description
Document and verify the test-generation and synchronization path for `exercises/practice/linked-list/.meta/tests.toml`. Anchored the checks on:
- Recreating `description` key/value pairs from canonical data (`canonical-data.json`).
- Recreating `reimplements` key/value pairs where specified in problem specifications.
- Preserving any other key/value pairs across `configlet sync` (specifically verifying that comments can be added and preserved in a `comment` key).
- Documenting that no per-exercise Jinja template exists for C; tests in `test_linked_list.c` are maintained directly by hand according to canonical specifications.
- Adding comprehensive maintenance documentation and a reusable course check script under `tools/course_checks/r48-t042.py`.

## Related Issue
Fixes: #42

## Type of Change
- [x] Documentation
- [ ] Bug Fix
- [ ] New Feature
- [ ] UI/UX Improvement
- [ ] Performance Improvement
- [x] Tests
- [x] Refactoring / Maintenance
- [ ] CI/CD

## Changes Made
- Added `docs/maintenance/linked-list.md` (and mirrored in `exercises/practice/linked-list/.meta/MAINTENANCE.md`) documenting the canonical data source, reproduction commands (`./bin/fetch-configlet` and `./bin/configlet sync --exercise linked-list --tests include --update --yes`), maintained vs generated files distinction, the three key handling rules during regeneration, and an exhaustive 19-case-to-output mapping table.
- Added a preserved `comment` key under canonical test case `7f7e3987-b954-41b8-8084-99beca08752c` in `exercises/practice/linked-list/.meta/tests.toml`.
- Created `tools/course_checks/r48-t042.py` as a reusable check verifying generation reproducibility, key preservation across sync, unsolved learner stubs, maintenance doc completeness, and scratch-copy reference test execution.
- Created `work/R48-T042/check.py` to automate multi-generation verification across temporary copies with timestamp normalization, ensuring no cases are dropped (Total=19, Included=19, Dropped=0).
- Substituted the reference implementation (`.meta/example.c`, `.meta/example.h`) only within an isolated temporary directory and verified all 19 tests pass via `make test` with 0 failures and 0 ignored.
- Saved execution evidence, canonical counts, and tool versions in `work/R48-T042/results.json`, `work/R48-T042/check_output.txt`, `work/R48-T042/expected_vs_actual.json`, `work/R48-T042/inputs.json`, and `work/R48-T042/tool_versions.txt`.

## Testing & Verification Results
- Ran `python3 work/R48-T042/check.py` and `python3 tools/course_checks/r48-t042.py`.
- **19/19 tests passed** with 0 failures and 0 ignored against reference implementation.
- Learner stub in working tree (`linked_list.c`, `linked_list.h`) remains unsolved.
- Two fresh temporary generations yield identical `tests.toml` after timestamp normalization with 0 cases dropped.
- Preserved `comment` key verified across `configlet sync`.

## Done When Checklist
- [x] The named cases (so comments can be added in a "comment" key.) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] Two generations yield the same tests after the documented timestamp normalization; no case is silently dropped.
- [x] The maintenance page identifies the source of the three cases (so comments can be added in a "comment" key.) and the command that reproduces them.

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
All criteria in the "Done when" and "Submission" checklists for task R48-T042 are fully satisfied and verified.
