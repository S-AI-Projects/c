# R48-T002 evidence

Exercise: `/Users/shiv/Desktop/S&AI - Assessment (Open Source)/Task 2/exercises/practice/wordy`
Inputs: solution=['wordy.c', 'wordy.h'] | test=['test_wordy.c'] | example=['.meta/example.c', '.meta/example.h']
Python: 3.15.2
- cc: Apple clang version 21.0.0 (clang-2100.4.1.1)
- make: GNU Make 3.81
- configlet: 4.0.3

## Expected vs actual

| Check | Expected | Actual |
|-------|----------|--------|
| two syncs byte-identical (timestamp strip: none) | True | True |
| UUID set identical in both runs | True | True |
| repo-HEAD cases dropped by sync | 0 | 0 |
| canonical cases added by sync (track drift) | n/a | 4 |
| repo cases in tests.toml | 23 | 23 |
| anchor phrase present in committed tests.toml | True | True |
| Unity cases run (N) | > 0 | 23 |
| Unity failures (M) | 0 | 0 |
| Unity ignored (K) | 0 | 0 |
| RUN_TEST count == committed case count | 23 | 23 |
| every RUN_TEST names a defined function | True | True |
| learner stub unsolved (git diff clean) | True | True |

Track drift: sync deterministically adds 4 canonical case(s) not yet hand-implemented in test_wordy.c: 18983214-1dfc-4ebd-ac77-c110dde699ce, 607c08ee-2241-4288-916d-dae5455c87e6, 6fa05f17-405a-4742-80ae-5d1a8edb0d5d, bb9f2082-171c-46ad-ad4e-c3f72087c1b5. It also rewrites the auto-generated header, so the anchor phrase above is asserted against the committed file.
Result: PASS. 23 Unity cases ran against the reference.

## Negative-run proof (check must exit non-zero)

1. Broken example (reference returns `false` for every question):
   `R48T002_EXERCISE=<copy with .meta/example.c stubbed>` → Unity summary
   `23 Tests 15 Failures 0 Ignored`, `make test` rc != 0, check **exit 1**.
2. Zero cases (all `RUN_TEST(...)` lines removed from `test_wordy.c`):
   `make test` fails to build (`-Werror,-Wunused-function`), check **exit 1**
   (the `N > 0` guard is also exercised when the file still compiles).

Both negatives used a throwaway copy via `R48T002_EXERCISE`; the committed
exercise and the learner stub were never modified.
