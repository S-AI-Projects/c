# R48-T005: cost of `is_greatest_in_row` (saddle-points)

Coursework evidence for the complexity study of
`exercises/practice/saddle-points/.meta/example.c`. This folder is evidence
only: remove `work/R48-T005/` from any later upstream branch.

## Run

```sh
python3 work/R48-T005/check.py            # full check, rewrites evidence/
python3 work/R48-T005/check.py --no-evidence   # same checks, evidence untouched
python3 work/R48-T005/check.py --reps 9   # more timed repetitions (minimum 5)
```

Needs Python 3.11+, a C compiler (`cc`, or set `CC`), GNU make, and the
exercise's own Unity copy. Exit code 0 means every assertion held; any failed
assertion, non-zero child process or zero-test run gives a non-zero exit.

## Files

| Path | Purpose |
| --- | --- |
| `check.py` | The automated check. Works only on temporary copies of the exercise. |
| `harness.c` | Measurement harness. Copied next to a copy of the reference and compiled there. |
| `evidence/inputs.json` | The nine measured inputs: pattern, size, byte count, SHA-256, generator. |
| `evidence/expected_vs_actual.json` | Named cases, test counts, negative controls, correctness and operation counts: expected next to actual. |
| `evidence/measurements.json` | Timings (every repetition), compile time and process start-up floor. |
| `evidence/tool_versions.txt` | Compiler, make, Python, Unity, OS, CPU, git commit. |
| `evidence/make_test.log` | Output of `make test` on the reference in the scratch copy (9 cases). |
| `PR_DESCRIPTION.md` | Text for the pull request. |
| `PR_PROMPT.md` | Short prompt for generating the pull request. |

## What the check asserts

1. Paths for solution, test and example files come from `.meta/config.json`.
2. The learner stub is unsolved: no exercise API in it, identical to git `HEAD`, and `make test` on it fails.
3. With the reference substituted in a copy and every test enabled, `make test` exits 0, executes as many cases as `tests.toml` lists (9), and each named case reports PASS.
4. Negative controls are rejected by the same evaluator: a zero-test run, a wrong reference, and the bare stub.
5. For three sizes and three input patterns: the input meets the specification; the real `saddle_points()` agrees with an independent oracle; the executed comparison count equals an independent model (and a closed form for the two extreme patterns).
6. Timing happens only after every assertion above has passed.
7. The exercise directory is byte-identical before and after, `example.c` carries the comment, and the doc quotes every measured count.
