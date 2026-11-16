# Wordy test maintenance

## Sources and generated files

`.meta/tests.toml` is the canonical case registry: it contains 23 UUIDs and
descriptions, with no case explicitly excluded. The test assertions and their
Unity registrations are maintained in `test_wordy.c`; the test names correspond
to the registry descriptions, with “reject problem missing an operand” named
`test_reject_a_problem_missing_an_operand`.

The root `makefile` generates
`build/exercises/practice/wordy/test_wordy.c` from `test_wordy.c`. Its `sed`
recipe comments out `TEST_IGNORE();` in that build copy so the full test suite is
run. The same target copies `.meta/example.c` and `.meta/example.h` to the build
directory, then invokes the exercise makefile. The working exercise and
reference files are not changed.

The exercise makefile compiles `test-framework/unity.c` and the exercise C
sources into `tests.out` using the configured C compiler, then runs the binary.
The `make test` target runs that binary. At the exercise level, tests marked
with `TEST_IGNORE();` remain disabled; the root track target enables them in its
generated copy.

## Reproduction

From the repository root, run:

```console
make wordy
```

The target has no Wordy-specific generator flags. CI runs the same root
Makefile via `make -j <available-thread-count>`. `make wordy` runs both the
normal tests and the exercise's AddressSanitizer memcheck target.

The repository does not contain a per-exercise Jinja template or a local
command that regenerates `.meta/tests.toml`. Its auto-generated header is
metadata, not an instruction to treat the Make target as a TOML generator.
Accordingly, reproducibility checks compare the TOML input unchanged, compare
the actual generated enabled-test source from two fresh runs, and verify that
all 23 registered cases are represented and executed. The generator produces
no timestamp, so no timestamp normalization is appropriate.

The reference implementation used for checks is `.meta/example.c` and
`.meta/example.h`; the example source matches upstream revision
`ffe5457101796886a272d6ebbeba8f849229c35a`.
