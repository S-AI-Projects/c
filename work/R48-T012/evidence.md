# R48-T012 evidence

Exercise: `/Users/tanmayaverma/Documents/Snai/c/exercises/practice/square-root`
Inputs: solution=['square_root.c', 'square_root.h'] | test=['test_square_root.c'] | example=['.meta/example.c', '.meta/example.h']
Python: 3.14.6
- cc: Apple clang version 21.0.0 (clang-2100.4.1.1)
- make: GNU Make 3.81
- configlet: 4.0.3

## Expected vs actual

| Check | Expected | Actual |
|-------|----------|--------|
| two syncs byte-identical (timestamp strip: none) | True | True |
| UUID set identical in both runs | True | True |
| repo-HEAD cases dropped by sync | 0 | 0 |
| canonical cases added by sync (track drift) | n/a | 0 |
| repo cases in tests.toml | 6 | 6 |
| anchor phrase present in committed tests.toml | True | True |
| Unity cases run (N) | > 0 | 6 |
| Unity failures (M) | 0 | 0 |
| Unity ignored (K) | 0 | 0 |
| RUN_TEST count == committed case count | 6 | 6 |
| every RUN_TEST names a defined function | True | True |
| learner stub unsolved (git diff clean) | True | True |

Result: PASS. 6 Unity cases ran against the reference.
