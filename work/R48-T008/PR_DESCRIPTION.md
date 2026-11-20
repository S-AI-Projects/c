# R48-T008: Map the maintained files for queen-attack

## Summary

Make the metadata in `exercises/practice/queen-attack/.meta/config.json` understandable and verifiable: the `files` object (solution / test / example) resolves inside `exercises/practice/queen-attack`, parent traversal and missing references are rejected, and the runner's discovery of `.meta/tests.toml` and `.meta/example.c` is explained and checked.

## What changed

Added `work/R48-T008/` (self-contained, independently reviewable):

- **`work/R48-T008/check.py`** — Python subprocess-based checker that:
  - Parses the `files` object from `.meta/config.json` (no filename heuristics).
  - Resolves each declared path relative to the exercise; rejects absolute paths, `..` parent traversal, and paths resolving outside the exercise directory.
  - Asserts every declared file exists.
  - Copies the exercise (including dotfiles `.meta`, `test-framework`, `.docs`) into a `tempfile.mkdtemp()` scratch copy.
  - Substitutes the reference (`.meta/example.c`) **only in the scratch copy** over `queen_attack.c`; the working tree and learner stub are never modified.
  - Enables the intended cases from `.meta/tests.toml` (cases without `include = false`) in the scratch test file.
  - Runs `make test` (exercise makefile + Unity v2.5.2) via `subprocess.run`, checks child return code and Unity test count/failures.
  - Exits non-zero on any assertion failure, zero-test run, or non-zero child exit.
- **`work/R48-T008/fixtures/{missing-reference,missing-test,outside-exercise}/config.json`** — three invalid metadata fixtures.
- **`work/R48-T008/inputs/`** — snapshots of real `config.json` and `tests.toml`.
- **`work/R48-T008/results/`** — `check_report.txt` (expected vs actual) and `behavioural_run.log`.
- **`work/R48-T008/versions.txt`** — tool versions (python3 3.15.2, make 3.81, cc Apple clang 21.0.0).
- **`work/R48-T008/maintenance.md`** — names real stub/reference/test paths and distinguishes generated artifacts from source/vendored framework.

## Verification results

```
== summary: 0 failure(s) ==
exit code: 0
```

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Real config metadata validation | all declared solution/test/example files resolve inside exercise | all 4 resolve | PASS |
| Fixture: missing-reference | fail (declared example file missing) | failed as intended | PASS |
| Fixture: missing-test | fail (declared test file missing) | failed as intended | PASS |
| Fixture: outside-exercise | fail (parent traversal outside exercise) | failed as intended | PASS |
| Behavioural run (reference + intended cases) | child exit 0, tests > 0, failures == 0 | exit 0, 13 tests, 0 failures, 4 ignored | PASS |

The 8 intended cases (from `.meta/tests.toml` entries without `include = false`) plus the always-on `test_invalid_if_on_same_position` pass against the reference implementation. The learner stub `queen_attack.c` remains unsolved (working tree untouched).

## Checklist

- [x] The named cases and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The real config passes; all three deliberately invalid metadata fixtures fail for the intended reason.
- [x] The maintenance document names the real stub, reference and test paths and distinguishes generated artifacts.

## Links

- Check implementation: `work/R48-T008/check.py`
- Evidence report: `work/R48-T008/results/check_report.txt`
- Behavioural run log: `work/R48-T008/results/behavioural_run.log`
- Maintenance document: `work/R48-T008/maintenance.md`
- Fixtures: `work/R48-T008/fixtures/`

## How to apply

```bash
# In a clone of your S-AI-Projects fork:
git checkout -b student/e26b07f0554
# add work/R48-T008/ files
git add work/R48-T008/
git commit -m "R48-T008: map maintained files for queen-attack + verification checks"
git push origin student/e26b07f0554
# Open a PR against S-AI-Projects/c with base repo = your fork,
# linking this check and referencing issue #8.
```

> `work/R48-T008/` should be removed from a later upstream branch once this task is reviewed/merged, per the task guidance.
