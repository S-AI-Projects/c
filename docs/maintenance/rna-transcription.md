# rna-transcription — Mutation-Driven Regression Analysis (R48-T013)

Maintainer note for `exercises/practice/rna-transcription/.meta/example.c`.

## Objective
Evaluate test suite sensitivity against subtle logical errors in RNA transcription and document diagnostic guidance for learners.

## Reference Under Test
- Exercise: `rna-transcription`
- Function: `char *to_rna(const char *dna)`
- Specification: Transcribe DNA nucleotides to RNA complements (`G` $\to$ `C`, `C` $\to$ `G`, `T` $\to$ `A`, `A` $\to$ `U`).

## Deliberate Mutant (M1)
A common mistake among learners is confusing DNA-to-DNA base pairing with DNA-to-RNA transcription (transcribing Adenine `A` into Thymine `T` instead of Uracil `U`).

### Mutant Diff against `.meta/example.c`:
```diff
--- a/exercises/practice/rna-transcription/.meta/example.c
+++ b/exercises/practice/rna-transcription/.meta/example.c
@@ -20,3 +20,3 @@ char *to_rna(const char *dna)
          case 'A':
-            rna[i] = 'U';
+            rna[i] = 'T';
             break;
```

## Rejecting Test Case
- **Canonical UUID**: `aade8964-02e1-4073-872f-42d3ffd74c5f`
- **Description**: `"RNA complement of adenine is uracil"`
- **Test Function**: `test_rna_complement_of_adenine_is_uracil`
- **Smallest Diagnostic Input**: `"A"`
- **Expected Result**: `"U"`
- **Mutant Result**: `"T"`

## Verification Results
1. **Original Reference**:
   - Unity Output: `6 Tests 0 Failures 0 Ignored`
   - Exit Code: `0` (PASS)
2. **Mutated Reference**:
   - Unity Output: `6 Tests 2 Failures 0 Ignored`
   - Rejected at: `test_rna_complement_of_adenine_is_uracil:FAIL: Expected "U" Was "T"`
   - Exit Code: `1` (REJECTED)

## Educational Guidance
Added `exercises/practice/rna-transcription/.docs/hints.md` providing a contract reminder that RNA substitutes Uracil for Thymine, anchoring the diagnosis with the single-character test input `"A" -> "U"` without exposing the full C implementation.
