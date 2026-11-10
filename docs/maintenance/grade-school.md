# Grade School canonical cases

Reviewed all 23 canonical cases in `.meta/tests.toml`. The initial and final
counts are 20 included and 3 excluded; no inclusion statuses changed.

| UUID | Test name | Status | Rationale |
|---|---|---|---|
| `c125dab7-2a53-492f-a99a-56ad511940d8` | `test_cannot_add_same_student_to_multiple_grades_in_roster` | Excluded | Included UUID `7df542f1-57ce-433c-b249-ff77028ec479` covers the same-name/different-grade behavior: `add_student` checks the whole roster with `student_is_on_roster`, which compares names with `strncmp`. The exclusion is redundancy, not a C limitation. |
| `a0c7b9b8-0e89-47f8-8b4a-c50f885e79d1` | `test_cannot_add_student_to_same_grade_more_than_once` | Excluded | Included UUID `87c871c1-6bde-4413-9c44-73d59a259d83` covers same-grade duplicate rejection: `student_is_on_roster` uses `strncmp`, and the test asserts `add_student` returns false. This behavior is supported in C. |
| `6a03b61e-1211-4783-a3cc-fc7f773fba3f` | `test_student_not_added_to_multiple_grades_in_roster` | Excluded | Included UUID `c7ec1c5e-9ab7-4d3b-be5c-29f2f7a237c5` covers the full-roster result: the duplicate is absent and the roster remains ordered after `student_is_on_roster` rejects it using `strncmp`. This is supported behavior, not a C limitation. |

Verification uses `python3 work/R48-T001/check.py`: it copies the exercise,
including dotfiles, to a temporary directory, substitutes `.meta/example.c`
and `.meta/example.h` only in that copy, removes the test ignore markers there,
and runs the supplied `make test` target against the reference implementation.
The script checks the Unity summary, fails on zero executed tests or failures,
and records every case's original and final status, the test output, and tool
versions under `work/R48-T001/`.
