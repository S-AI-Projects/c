# square-root — test-generation maintenance (R48-T012)

Reproduce: `python3 work/R48-T012/check.py`
Generate (run from a track root holding `config.json` + `exercises/practice/square-root`): `bin/configlet sync --tests include --update -y -t . -e square-root`
`bin/fetch-configlet` downloads `bin/configlet` (4.0.3) if absent; canonical data is exercism/problem-specifications.
Inputs (`.meta/config.json` files): solution `square_root.c square_root.h`; test `test_square_root.c`; example `.meta/example.c .meta/example.h`.
Generated vs hand: `.meta/tests.toml` = GENERATED (configlet/problem-specifications); `test_square_root.c` = HAND-maintained (Unity); `test-framework/unity.{c,h}` + `unity_internals.h` = vendored Unity.
Anchor `so comments can be added in a "comment" key.` = `.meta/tests.toml:3` (configlet header, not a per-case key). Committed cases map, in order, to `test_square_root.c` RUN_TEST lines:

| # | case (description) | function | line |
|---|--------------------|----------|------|
| 1 | root of 1 | test_root_of_1 | 51 |
| 2 | root of 4 | test_root_of_4 | 52 |
| 3 | root of 25 | test_root_of_25 | 53 |
| 4 | root of 81 | test_root_of_81 | 54 |
| 5 | root of 196 | test_root_of_196 | 55 |
| 6 | root of 62025 | test_root_of_65025 | 56 |

Note on case 6: In canonical-data / tests.toml, description is "root of 62025" (input 65025); the hand-written test function in C is named `test_root_of_65025`, asserting `square_root(65025) == 255`.
