# R48-T013 evidence

Exercise: `/Users/tanmayaverma/Documents/Snai/c/exercises/practice/rna-transcription`
Inputs: solution=['rna_transcription.c', 'rna_transcription.h'] | test=['test_rna_transcription.c'] | example=['.meta/example.c', '.meta/example.h']
Python: 3.9.6
Tool versions: {"python": "3.9.6", "make": "GNU Make 3.81", "cc": "Apple clang version 21.0.0 (clang-2100.4.1.1)"}

## Expected vs Actual

| Check | Expected | Actual |
|-------|----------|--------|
| Original reference passes all cases | True | True |
| Original Unity tests run (N) | 6 | 6 |
| Original Unity failures (M) | 0 | 0 |
| Original Unity ignored (K) | 0 | 0 |
| Mutant M1 rejected | True | True |
| Rejecting test case | `test_rna_complement_of_adenine_is_uracil` | `test_rna_complement_of_adenine_is_uracil` |
| Smallest diagnostic input | `"A"` -> `"U"` | `"A"` -> `"T"` (rejected) |
| Learner stub unsolved | True | True |
| Educational hint added | True | True |

Result: PASS. Original reference passes 6/6 tests. Mutant M1 is decisively rejected by `test_rna_complement_of_adenine_is_uracil`.
