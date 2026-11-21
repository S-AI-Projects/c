# wordy — test-generation maintenance (R48-T002)

Reproduce: `python3 work/R48-T002/check.py`
Generate (run from a track root holding `config.json` + `exercises/practice/wordy`): `bin/configlet sync --tests include --update -y -t . -e wordy`
`bin/fetch-configlet` downloads `bin/configlet` (4.0.3) if absent; canonical data is exercism/problem-specifications.
Inputs (`.meta/config.json` files): solution `wordy.c wordy.h`; test `test_wordy.c`; example `.meta/example.c .meta/example.h`.
Generated vs hand: `.meta/tests.toml` = GENERATED (configlet/problem-specifications); `test_wordy.c` = HAND-maintained (Unity); `test-framework/unity.{c,h}` + `unity_internals.h` = vendored Unity.
Anchor `so comments can be added in a "comment" key.` = `.meta/tests.toml:3` (configlet header, not a per-case key). Committed cases map, in order, to `test_wordy.c` RUN_TEST lines:

| # | case (description) | function | line |
|---|--------------------|----------|------|
| 1 | just a number | test_just_a_number | 252 |
| 2 | addition | test_addition | 253 |
| 3 | more addition | test_more_addition | 254 |
| 4 | addition with negative numbers | test_addition_with_negative_numbers | 255 |
| 5 | large addition | test_large_addition | 256 |
| 6 | subtraction | test_subtraction | 257 |
| 7 | multiplication | test_multiplication | 258 |
| 8 | division | test_division | 259 |
| 9 | multiple additions | test_multiple_additions | 260 |
| 10 | addition and subtraction | test_addition_and_subtraction | 261 |
| 11 | multiple subtraction | test_multiple_subtraction | 262 |
| 12 | subtraction then addition | test_subtraction_then_addition | 263 |
| 13 | multiple multiplication | test_multiple_multiplication | 264 |
| 14 | addition and multiplication | test_addition_and_multiplication | 265 |
| 15 | multiple division | test_multiple_division | 266 |
| 16 | unknown operation | test_unknown_operation | 267 |
| 17 | Non math question | test_non_math_question | 268 |
| 18 | reject problem missing an operand | test_reject_a_problem_missing_an_operand | 269 |
| 19 | reject problem with no operands or operators | test_reject_problem_with_no_operands_or_operators | 270 |
| 20 | reject two operations in a row | test_reject_two_operations_in_a_row | 271 |
| 21 | reject two numbers in a row | test_reject_two_numbers_in_a_row | 272 |
| 22 | reject postfix notation | test_reject_postfix_notation | 273 |
| 23 | reject prefix notation | test_reject_prefix_notation | 274 |

Note: committed `tests.toml` is 4 cases behind canonical data; `sync --update` adds them deterministically (see `work/R48-T002/evidence.md`).