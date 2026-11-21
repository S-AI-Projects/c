# R48-T005: Measure the scaling of the saddle-points reference

Closes #5

## Summary

This PR states and measures the cost of `is_greatest_in_row` in `exercises/practice/saddle-points/.meta/example.c`.
The only change to the exercise is a comment next to the function. No code and no learner file changed.

**Result.** With R rows and C columns, `saddle_points()` calls `is_greatest_in_row` once per cell (R × C calls).
One call does between 1 and C comparisons.
Over a whole grid the function executes between R × (2C − 1) and R × C² comparisons, using O(1) extra space.

| Input (R × C) | Calls | Comparisons: worst | Comparisons: best | Comparisons: random |
| --- | ---: | ---: | ---: | ---: |
| 256 × 256 | 65,536 | 16,777,216 | 130,816 | 442,736 |
| 256 × 512 | 131,072 | 67,108,864 | 261,888 | 1,081,880 |
| 512 × 512 | 262,144 | 134,217,728 | 523,776 | 2,144,948 |

The counts are exact and match an independent model for every input.
The worst case is R × C² on the nose: ×4 when C doubles at fixed R, ×2 when R doubles at fixed C.
Timings (in-process, 7 repetitions, median) are supporting evidence only and are in the doc.

**What the conclusion does not cover.** Only `is_greatest_in_row` was costed, not the whole of `saddle_points()`.
Timings are from one virtual machine at `-O2`.
Nothing above 512 × 512 was run.
No speedup is claimed and no alternative implementation was measured.

## Changes

| File | Change |
| --- | --- |
| [`exercises/practice/saddle-points/.meta/example.c`](https://github.com/S-AI-Projects/c/blob/R48-T005/exercises/practice/saddle-points/.meta/example.c) | Comment only: invariant, best and worst case, whole-grid bounds, `int16_t` index limit. |
| [`docs/maintenance/saddle-points.md`](https://github.com/S-AI-Projects/c/blob/R48-T005/docs/maintenance/saddle-points.md) | Supported input sizes, measured operations and timings, algorithm vs start-up and compile time, limits of the conclusion. |
| [`work/R48-T005/check.py`](https://github.com/S-AI-Projects/c/blob/R48-T005/work/R48-T005/check.py) | The automated check. |
| [`work/R48-T005/harness.c`](https://github.com/S-AI-Projects/c/blob/R48-T005/work/R48-T005/harness.c) | Measurement harness, compiled only inside a temporary copy. |
| [`work/R48-T005/evidence/`](https://github.com/S-AI-Projects/c/blob/R48-T005/work/R48-T005/evidence) | Inputs, expected vs actual, measurements, tool versions, `make test` log. |
| [`work/R48-T005/README.md`](https://github.com/S-AI-Projects/c/blob/R48-T005/work/R48-T005/README.md) | How to run the check and what it asserts. |

`work/R48-T005/` is evidence only and must be removed from any later upstream branch.

## How to check

```sh
python3 work/R48-T005/check.py
```

Last run: **128 assertions passed, 0 failed; 9 exercise test cases executed.**

The check works on temporary copies (dotfiles included), takes the solution, test and example paths from `.meta/config.json`, substitutes the reference only in the copy, enables every test case there, and runs the supplied `make test` with Unity.
It checks child return codes and the test count against `tests.toml`, and exits non-zero on a failed assertion, a non-zero child exit or a zero-test run.

Beyond the exercise's tests, the check also:

- compares the real `saddle_points()` against an independent O(R × C) oracle on all nine measured inputs, and confirms that each answer is non-empty;
- counts executed comparisons in an instrumented copy and compares them with an independent Python model and, for the two extreme inputs, with closed forms;
- takes timings only after every correctness and count assertion has passed;
- confirms the exercise directory is byte-identical before and after the run.

Negative controls built into the check: a zero-test run, a reference with the comparison flipped, and the bare stub must each be reported as problems.
Six faults were also injected into a scratch copy of the repository (flipped comparison, zero tests, cost silently doubled while tests still pass, edited learner stub, broken reference header, doc missing a count); each made the check exit non-zero.

## Checklist

### Done when

- [x] The named cases and all other enabled cases pass against the reference; the learner stub is still unsolved. (9 of 9 cases pass; the stub is identical to git `HEAD` and `make test` on it fails to build.)
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The cost statement distinguishes algorithm work from process-startup or compilation time. (Compile about 84 ms and process start-up floor about 1.4 ms, against 0.05 to 46.6 ms for the timed sweep.)
- [x] All measured inputs satisfy the specification; correctness is asserted before timing and no speedup is claimed without measurements.

### Submission checklist

- [x] Complete this task and its checks.
- [x] Add the required evidence (`work/R48-T005/evidence/`).
- [ ] Link this pull request in issue #5.
- [ ] Select this S-AI-Projects fork as the PR base repository.
- [ ] Request instructor review.

The last three items are actions on GitHub, so they are left for whoever opens the pull request.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01LZo756cipRzWBHGyr1NkXR
