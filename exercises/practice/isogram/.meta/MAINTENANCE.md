# Isogram: Contract Specification & Maintenance Guide

## Overview

This maintenance guide documents the contract requirements, subtle edge cases, decision table, and test suite maintenance for `exercises/practice/isogram`.

- **Exercise**: `exercises/practice/isogram`
- **Pinned Reference Implementation**: [`exercises/practice/isogram/.meta/example.c#L6` at `ffe5457`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/isogram/.meta/example.c#L6)
- **Task ID**: `R48-T050`

---

## Canonical Data Source & Key Handling Rules

Canonical test cases originate from Exercism's `problem-specifications` repository:
- **Canonical data**: `exercises/isogram/canonical-data.json`
- **Track metadata**: `exercises/practice/isogram/.meta/tests.toml`
- **Exercise configuration**: `exercises/practice/isogram/.meta/config.json`

### Key Handling Rules (tests.toml)

When regenerating or synchronizing `tests.toml` via `configlet sync`:
1. **Recreate every `description` key/value pair**: Matches canonical problem descriptions.
2. **Recreate every `reimplements` key/value pair**: Preserves canonical UUID tracking where tests are reimplemented.
3. **Preserve any other key/value pair**: Manually added keys such as `comment` keys are preserved by the tooling (`so comments can be added in a "comment" key.`).

---

## Maintained vs Generated Files

- **Synchronized by Tooling:**
  - `exercises/practice/isogram/.meta/tests.toml`: Synchronized from canonical data using `./bin/configlet sync --exercise isogram --tests include --update --yes`.
- **Maintained by Hand:**
  - `test_isogram.c`: Unity test suite containing unit tests mapped to canonical specifications plus C-track defensive cases (`test_null`).
  - `isogram.h` & `isogram.c`: Learner starter stub.
  - `.meta/example.h` & `.meta/example.c`: Reference solution.
  - `.docs/instructions.md`: Canonical problem instructions.
  - `.docs/hints.md`: Walkthrough of subtle contract cases and decision table.
  - `.meta/config.json`: File path mappings and author metadata.

---

## C Contract & Interface Walkthrough

```c
#include <stdbool.h>

bool is_isogram(const char phrase[]);
```

### 1. Pointer Semantics & Defensive Handling
In C, strings are represented as pointers to null-terminated `char` arrays (`const char *`).
- When `phrase == NULL`, dereferencing it triggers undefined behavior.
- The C track test suite includes `test_null`, requiring `is_isogram(NULL)` to safely return `false`.
- This is a C-specific defensive extension outside the language-agnostic canonical problem specification.

### 2. Vacuous Truth (Empty String)
- `""` has length 0 and contains no letters.
- Because an empty string has no repeating letters, it satisfies the definition of an isogram vacuously.
- Returns `true`.

### 3. Case Insensitivity
- Duplication checks are case-insensitive.
- Both uppercase `'A'` and lowercase `'a'` map to the same letter.
- Tested by `"Alphabet"` and `"alphAbet"`, both returning `false`.

### 4. Non-Letter Repetitions
- Spaces (`' '`) and hyphens (`'-'`) are explicitly exempted from duplicate checking.
- Tested by `"six-year-old"` (multiple hyphens) and `"Emily Jung Schwartzkopf"` (multiple spaces), both returning `true`.
- Any repeating letter alongside hyphens (e.g. `"up-to-date"`) returns `false`.

---

## Decision Table

| Input Condition | Test Case Input | Expected Output | Contract Status | Canonical UUID |
| :--- | :--- | :---: | :--- | :--- |
| **Empty string** | `""` | `true` | Specified (Canonical) | `a0e97d2d-669e-47c7-8134-518a1e2c4555` |
| **Null pointer** | `NULL` | `false` | Specified (C Track Defensive) | N/A (`test_null`) |
| **Lowercase isogram** | `"isogram"` | `true` | Specified (Canonical) | `9a001b50-f194-4143-bc29-2af5ec1ef652` |
| **Single duplicate** | `"eleven"` | `false` | Specified (Canonical) | `8ddb0ca3-276e-4f8b-89da-d95d5bae78a4` |
| **End of alphabet duplicate** | `"zzyzx"` | `false` | Specified (Canonical) | `6450b333-cbc2-4b24-a723-0b459b34fe18` |
| **Longest English isogram** | `"subdermatoglyphic"` | `true` | Specified (Canonical) | `a15ff557-dd04-4764-99e7-02cc1a385863` |
| **Mixed-case duplicate (upper first)** | `"Alphabet"` | `false` | Specified (Canonical) | `f1a7f6c7-a42f-4915-91d7-35b2ea11c92e` |
| **Mixed-case duplicate (lower first)** | `"alphAbet"` | `false` | Specified (Canonical) | `14a4f3c1-3b47-4695-b645-53d328298942` |
| **Isogram with hyphen** | `"thumbscrew-japingly"` | `true` | Specified (Canonical) | `423b850c-7090-4a8a-b057-97f1cadd7c42` |
| **Duplicate following hyphen** | `"thumbscrew-jappingly"` | `false` | Specified (Canonical) | `93dbeaa0-3c5a-45c2-8b25-428b8eacd4f2` |
| **Multiple hyphens isogram** | `"six-year-old"` | `true` | Specified (Canonical) | `36b30e5c-173f-49c6-a515-93a3e825553f` |
| **Multiple spaces & mixed case** | `"Emily Jung Schwartzkopf"` | `true` | Specified (Canonical) | `cdabafa0-c9f4-4c1f-b142-689c6ee17d93` |
| **Duplicate in middle** | `"accentor"` | `false` | Specified (Canonical) | `5fc61048-d74e-48fd-bc34-abfc21552d4d` |
| **Same first and last characters** | `"angola"` | `false` | Specified (Canonical) | `310ac53d-8932-47bc-bbb4-b2b94f25a83e` |
| **Duplicate with two hyphens** | `"up-to-date"` | `false` | Specified (Canonical) | `0d0b8644-0a1e-4a31-a432-2b3ee270d847` |
| **Non-ASCII / UTF-8 multi-byte** | `"café"` | Unspecified | Outside Contract | N/A |
| **Numeric digits & symbols** | `"1234!"` | Unspecified | Outside Contract | N/A |
| **Dangling / Invalid buffer** | Wild pointer | Undefined | Outside Contract | N/A |

---

## Specified vs Unspecified Behavior Statement

1. **Specified Behavior**:
   - Case-insensitive English alphabet letters ($a-z, A-Z$) are uniquely tracked.
   - Whitespace and hyphens are skipped and do not trigger duplicate failures.
   - Empty string input returns `true`.
   - Null pointer input returns `false` (C track defensive requirement).

2. **Unspecified Behavior**:
   - The exercise specification leaves multi-byte UTF-8, non-ASCII characters, accented letters, and numbers unspecified.
   - Memory management of invalid or non-null-terminated buffers is undefined under standard C pointer semantics.
