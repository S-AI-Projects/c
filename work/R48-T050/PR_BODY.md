## Description
Comprehensive contract analysis, subtle case walkthrough, and decision table documentation for `exercises/practice/isogram`.
- Pinned reference implementation: [`exercises/practice/isogram/.meta/example.c#L6` at commit `ffe5457`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/isogram/.meta/example.c#L6).
- Analyzed subtle contract cases and separated specified behavior from inputs outside the exercise contract:
  - **Vacuously True Case**: Empty string `""` contains zero letters, and therefore zero duplicate letters (`test_empty_string` $\to$ `true`).
  - **Defensive Extension Case**: Null pointer `phrase == NULL` safely returns `false` without segmentation fault (`test_null` $\to$ `false`), established as a C track defensive contract rule outside the canonical language-agnostic specification.
  - **Case-Insensitivity**: Both uppercase and lowercase letters map to identical alphabet positions (`"Alphabet"`, `"alphAbet"` $\to$ `false`).
  - **Allowed Non-Letter Repetitions**: Whitespace and hyphens are permitted to repeat indefinitely without triggering duplicate failures (`"six-year-old"`, `"Emily Jung Schwartzkopf"` $\to$ `true`).
  - **Punctuation with Duplicates**: Letter duplicates in the presence of hyphens correctly fail (`"up-to-date"` $\to$ `false`).
  - **Position Independence**: Duplicate letters at string boundaries or internal positions trigger immediate failure (`"zzyzx"`, `"accentor"`, `"angola"` $\to$ `false`).
- Built complete Decision Table connecting each input condition to required results and explicit classification of specified vs unspecified behaviors (non-ASCII, numbers, dangling pointers).
- Added `exercises/practice/isogram/.docs/hints.md` providing a short input/output walkthrough for the selected cases, explaining C representation (`const char phrase[]`, pointer semantics, null byte termination) without altering canonical instructions.
- Added preserved `comment` key in `exercises/practice/isogram/.meta/tests.toml` verifying that metadata comments survive `configlet sync` (`so comments can be added in a "comment" key.`).
- Added maintenance guide in `docs/maintenance/isogram.md` (and mirrored in `exercises/practice/isogram/.meta/MAINTENANCE.md`).
- Implemented automated verification check in `work/R48-T050/check.py` and course check in `tools/course_checks/r48-t050.py`.
- Verified in isolated scratch directory that all 15 test cases pass against the reference with 0 failures and 0 ignored; working tree learner stub (`isogram.c`) remains unsolved.

## Related Issue
Fixes: #50

## Type of Change
- [x] Documentation
- [x] Tests
- [x] Refactoring / Maintenance

## Changes Made
- `exercises/practice/isogram/.docs/hints.md`: Added walkthrough of subtle contract cases, C representation details, decision table, and explicit statements on specified vs unspecified behaviors.
- `exercises/practice/isogram/.meta/tests.toml`: Added preserved `comment` key under canonical test case `a0e97d2d-669e-47c7-8134-518a1e2c4555` (`so comments can be added in a "comment" key.`).
- `docs/maintenance/isogram.md` & `exercises/practice/isogram/.meta/MAINTENANCE.md`: Created maintenance documentation detailing the contract, canonical data source, key handling rules, decision table, and reference implementation invariants.
- `tools/course_checks/r48-t050.py` & `work/R48-T050/check.py`: Automated check scripts verifying unsolved learner stub, hints guidance, maintenance docs, `tests.toml` sync preservation, decision table alignment, and scratch reference test execution.
- `work/R48-T050/`: Saved verification evidence (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results
- Ran `python3 work/R48-T050/check.py` and `python3 tools/course_checks/r48-t050.py`.
- **15/15 tests passed** against reference implementation with 0 failures and 0 ignored.
- **Learner stub** in working tree (`isogram.c`) remains unsolved.
- **Decision table verified**: Exactly aligns with all 15 test inputs and outcomes.
- **Metadata preservation**: `tests.toml` comment key verified across `configlet sync --exercise isogram --tests include --offline`.
- No extra coercion, exception rule, or ordering constraint imposed.

## Done When Checklist
- [x] The named cases (so comments can be added in a "comment" key.) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The decision table matches the exact selected test inputs and outcomes.
- [x] No extra exception rule, coercion or ordering requirement is imposed unless the source specification requires it.

## Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.

## Review Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [x] I have addressed previous review feedback, if applicable.
