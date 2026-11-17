# Protein Translation: Two Approaches in C

## Overview

This document compares two distinct implementation strategies for the `protein-translation` contract in C, analyzing their representations, control flow, and computational trade-offs.

---

## The Contract

Given an RNA sequence (string of nucleotide characters), translate each 3-character codon into its corresponding amino acid:
- Stop translation when a STOP codon (`UAA`, `UAG`, `UGA`) is encountered.
- Return a `protein_t` struct containing `bool valid`, `size_t count`, and `amino_acid_t amino_acids[MAX_AMINO_ACIDS]`.
- Set `valid = false` if codon length is not a multiple of 3 or if an unrecognized codon is encountered.

---

## Approach 1: Linear Table Lookup with String Matching (Reference)

### Design & Control Flow
- **Representation**: A static table of structs containing string literals:
  ```c
  typedef struct {
     const char *const codon;
     amino_acid_t amino_acid;
     bool stop;
  } amino_acid_translation_t;

  static const amino_acid_translation_t translations[] = {
     { "AUG", Methionine, false },
     { "UUU", Phenylalanine, false },
     ...
     { "UAA", 0, true },
  };
  ```
- **Control Flow**: For each 3-character codon in `rna`, iterate sequentially through `translations` calling `strncmp(rna + i, translations[j].codon, 3)`.

### Worked Example
For codon `"AUG"`:
- Iteration $j = 0$: `strncmp("AUG", "AUG", 3) == 0` $\rightarrow$ Match! Appends `Methionine`, breaks inner loop.

### Trade-offs
- **Clarity**: Very easy to read and extend with additional codons without altering logic.
- **Cost**: Up to 17 string comparisons per codon ($\mathcal{O}(T)$ where $T = 17$). Each `strncmp` call involves function call overhead and pointer arithmetic.

---

## Approach 2: Integer Bit-Packed Switch Dispatch (Alternative)

### Design & Control Flow
- **Representation**: Since codons are exactly 3 ASCII characters, pack the 3 bytes into a single 24-bit integer constant:
  ```c
  #define PACK_CODON(c1, c2, c3) (((uint32_t)(uint8_t)(c1) << 16) | \
                                  ((uint32_t)(uint8_t)(c2) << 8)  | \
                                  (uint32_t)(uint8_t)(c3))
  ```
- **Control Flow**: Direct `switch(key)` dispatch:
  ```c
  switch (key) {
     case PACK_CODON('A', 'U', 'G'): *acid = Methionine; return CODON_AMINO;
     case PACK_CODON('U', 'U', 'U'):
     case PACK_CODON('U', 'U', 'C'): *acid = Phenylalanine; return CODON_AMINO;
     ...
     case PACK_CODON('U', 'A', 'A'): return CODON_STOP;
     default: return CODON_INVALID;
  }
  ```

### Worked Example
For codon `"AUG"`:
- Key calculation: `('A' << 16) | ('U' << 8) | 'G' = 0x00415547`.
- Single `switch` evaluates key directly via compiler-generated jump table or binary comparison tree in $\mathcal{O}(1)$ time with zero string comparison calls.

### Trade-offs
- **Performance**: Constant-time $\mathcal{O}(1)$ codon identification, zero function call overhead, no heap access.
- **Clarity / Maintenance**: Slightly more complex macro construct than simple string arrays, but eliminates all runtime string searching and provides immediate rejection of invalid codons via `default:`.

---

## Summary of Empirical Comparison

Both techniques were tested against the entire Exercism test suite:
- **Test Suite Pass Rate**: 31/31 tests passed identically by both implementations.
- **Correctness & Safety**: Identical contract adherence on invalid lengths, unknown codons, and stop sequence handling.
