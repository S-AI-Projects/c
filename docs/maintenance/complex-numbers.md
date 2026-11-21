# Complex Numbers — Isolated Test Runner (R48-T009)

## Command

Run the isolated check from the repository root:

```console
python3 work/R48-T009/check.py
```

To run the runner directly against the exercise:

```console
python3 tools/course_checks/r48-t009.py exercises/practice/complex-numbers --scenario real
```

Scenarios supported by `tools/course_checks/r48-t009.py`:

- `real` — substitutes the reference (`.meta/example.c`) into a temporary copy,
  enables every test case, runs `make test`, and asserts all 40 cases pass.
- `failing` — deliberately breaks `c_add` in the temporary copy only and asserts
  a non-zero exit.
- `empty` — removes all `RUN_TEST` calls in the temporary copy and asserts a
  zero-test run fails.

## Tool requirements

- Python 3
- GCC / CC (C compiler)
- GNU make
- Vendored Unity test framework (in `exercises/practice/complex-numbers/test-framework/`)

## What it checks

1. The reference implementation passes all 40 enabled test cases against the
   real case count reported by Unity.
2. A deliberately failing reference produces a non-zero exit.
3. A zero-test run produces a non-zero exit.
4. Learner file hashes are identical before and after every run (stub remains
   unsolved and unmodified).
5. Temporary files are cleaned up after each run (via `tempfile.TemporaryDirectory`).

## Evidence

All inputs, expected vs actual results, tool versions, and learner hash
comparisons are saved in `work/R48-T009/`:

- `scenario_{real,failing,empty}.{out,err,exit}`
- `expected_vs_actual.md`
- `learner_hashes_before_after.md`
- `tool_versions.txt`
- `results.json`

## Files changed (PR scope)

- `tools/course_checks/r48-t009.py` — new isolated runner
- `docs/maintenance/complex-numbers.md` — this document

No learner files under `exercises/practice/complex-numbers/` are modified.
