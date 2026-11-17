## R48-T003: find a test that distinguishes a wrong palindrome-products implementation

Base repository: `S-AI-Projects/c` (the organisation fork), not upstream.
Task issue: #3. Student: Shiv Raut.

### Result

A deliberately wrong `palindrome()` in a temporary copy of the reference is rejected by the existing suite.

| | |
| --- | --- |
| Mutant **M1** | the "a number ending in `0` is not a palindrome" guard is deleted (10 C tokens change) |
| Rejecting case | `0853f82c-5fc4-44ae-be38-fadb2cced92d`, "find the largest palindrome from single digit factors" (`test_largest_palindrome_from_single_digit_factors`) |
| Expected vs actual | `get_palindrome_product(1, 9)`: largest `9` expected, M1 gives `40` (`Expected 9 Was 40`) |
| Smallest diagnostic input | `get_palindrome_product(2, 5)`: smallest `4` from `(2, 2)` and largest `9` from `(3, 3)`; M1 returns largest `20` from `(4, 5)` |

Five more existing cases also reject M1. The original reference passes all 13 cases; the learner stub still fails the suite.

Three further one-line mutants (M2, M9, M12) pass all 13 existing cases. Each has a proposed case with an explicit input and expected result on the maintenance page. Those are proposals only; no test was changed.

### What changed

- `exercises/practice/palindrome-products/.docs/hints.md` (new): explains why a number ending in `0` is not a palindrome and gives `get_palindrome_product(2, 5)` as a small case to debug with. It has no code and none of the reference.
- `docs/maintenance/palindrome-products.md` (new): the mutant, the rejecting test ID, expected behaviour, the minimal input and how "smallest" was defined, the surviving mutants with proposed cases, and one observation (below).
- `work/R48-T003/` (coursework evidence, not for upstream): `check.py`, `diagnostic_driver.c`, `evidence/`.

No test, stub, reference or metadata file is modified.

### Checks

[`python3 work/R48-T003/check.py`](https://github.com/S-AI-Projects/c/blob/R48-T003/work/R48-T003/check.py) exits 0 here. It needs Python 3.11+, a C compiler and GNU make, and works only in temporary copies. It:

- resolves solution, test and example paths from `.meta/config.json` and copies the exercise including dotfiles;
- substitutes the reference in the copy only and enables every case (12 `TEST_IGNORE` lines);
- runs `make test`, checks every return code, reports the number of executed cases (13) and fails on a zero-test run, a non-zero child exit or an assertion failure, each proved by a control;
- rejects formatting-only mutations;
- compares the original and each mutant on identical inputs against an explicit expected result and an independent oracle written from the instructions, and searches for the smallest differing input;
- checks that the hint and the maintenance page agree with the evidence and that the hint does not reproduce reference code.

Saved in [`work/R48-T003/evidence/`](https://github.com/S-AI-Projects/c/tree/R48-T003/work/R48-T003/evidence): inputs, expected versus actual results, make logs, the mutation diff and tool versions. The evidence is byte-identical across runs.

### Observation for reviewers (not a claim of a defect)

On ranges such as `get_palindrome_product(1, 1)` and `(24, 29)` the reference answers "no palindrome", where the instructions read literally give a result. This happens for 179 of the 1,891 ranges in `0 <= min <= max <= 60`, and the reference never returned a different value. The canonical data has no such case. It is recorded on the maintenance page because it decided which inputs could serve as diagnostics.

### Notes

- `configlet lint` exits 1 on a missing `docs/SIGN_UP_SNIPPET.txt`. It does the same on an untouched `ffe5457`, and this change adds no findings.
- Remove `work/R48-T003/` from any later upstream branch, as the task asks.
- The task text names both `student/e26b07f0554` and `R48-T003` as the branch; this work is on `R48-T003`, branched from `main` so it stays reviewable independently of R48-T002.

### Checklist

- [x] Named case and all other enabled cases pass against the reference; the learner stub is still unsolved
- [x] The check reports executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure
- [x] The original passes and the documented mutant fails the named assertion; the mutation is not formatting-only
- [x] The hint explains the contract and gives a small diagnostic input without publishing the reference
- [ ] Evidence linked in the issue, PR base set to this fork, instructor review requested

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01LZo753bfz58LLcjQ9muJP7
