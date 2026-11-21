# PR Description: R48-T009 — Isolated test runner for complex-numbers

## Summary

Adds an isolated test runner for `exercises/practice/complex-numbers` that tests
the reference implementation (`.meta/example.c`) in a temporary copy without
touching the learner stub files. The runner reports the real executed case count
and propagates failures (non-zero child exit, zero-test run, assertion failure).

## Checklist

- [x] The named case `[9a2c8de9-f068-4f6f-b41c-82232cc6c33e]` ("Arithmetic ->
  Addition -> Add purely real numbers") and all other enabled cases pass against
  the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test
  run, a non-zero child exit or an assertion failure.
- [x] Success, assertion failure and zero-test runs produce the correct exit
  status; temporary files are cleaned up.
- [x] The learner file hashes are identical before and after every run,
  including an interrupted or failing run.
- [x] `python3 work/R48-T009/check.py` is the automated check and exits
  non-zero when an assertion fails.
- [x] Evidence (inputs, expected vs actual results, tool versions) saved in
  `work/R48-T009/`.
- [x] Commit is on branch `R48-T009`.
- [x] PR targets the S-AI-Projects fork as the base repository (not upstream).
- [x] `work/R48-T009/` is kept out of any later upstream branch.
- [x] Each task is independently reviewable.
- [x] Instructor review requested.

## Results

| Scenario   | Expected Exit | Actual Exit | Cases | Hashes Match | Passed |
|------------|---------------|-------------|-------|--------------|--------|
| real       | 0             | 0           | 40    | Yes          | Yes    |
| failing    | non-zero      | non-zero    | 40    | Yes          | Yes    |
| empty      | non-zero      | non-zero    | 0     | Yes          | Yes    |

## Evidence

- `work/R48-T009/results.json` — full results
- `work/R48-T009/expected_vs_actual.md` — expected vs actual per scenario
- `work/R48-T009/learner_hashes_before_after.md` — hash comparison
- `work/R48-T009/tool_versions.txt` — python3, make, gcc, git versions
- `work/R48-T009/scenario_{real,failing,empty}.{out,err,exit}` — raw output

## Links

- Automated check: `python3 work/R48-T009/check.py`
- Runner: `tools/course_checks/r48-t009.py`
- Documentation: `docs/maintenance/complex-numbers.md`
