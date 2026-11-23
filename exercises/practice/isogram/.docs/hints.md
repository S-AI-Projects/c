# Hints

## General Guidance

An isogram (also known as a "non-pattern word") is a word or phrase without any repeating letters.

- **Case-Insensitive**: Letter matching must be case-insensitive. For example, `'A'` and `'a'` are considered the same letter.
- **Allowed Repetitions**: Spaces (`' '`) and hyphens (`'-'`) are not letters and are allowed to appear multiple times throughout the phrase.
- **Bitmask Strategy**: Since standard English contains only 26 alphabetic letters, you can track seen letters using a single 32-bit unsigned integer bitmask (`uint32_t`), where bit $k \in [0, 25]$ represents whether letter $k$ has been encountered.

---

## C Representation & Interface Contract

The exercise defines the function signature:

```c
#include <stdbool.h>

bool is_isogram(const char phrase[]);
```

- **Parameter**: `const char phrase[]` decays to a pointer to a `const char` (`const char *`). The caller passes either a valid null-terminated C string or `NULL`.
- **Memory Safety & Immutability**: The parameter is `const`-qualified; the function must not attempt to modify the input buffer.
- **Return Value**: The function returns a standard C `bool` (`true` if the input is an isogram, `false` otherwise).
- **Ordering**: The contract does not mandate any specific traversal order (left-to-right, right-to-left, etc.), though scanning left-to-right from index 0 until the null terminator `'\0'` is standard.
- **No Extra Coercion**: No character translation or memory reallocation is required; inspect characters directly in place.

---

## Subtle Contract Cases & Walkthrough

### 1. Empty String (`""`)
- **Input**: `""` (valid pointer to a 1-byte buffer containing `'\0'`).
- **Expected Output**: `true`.
- **Specification Walkthrough**: The definition states an isogram is a word or phrase without a repeating letter. Because an empty string contains zero letters, there are zero duplicate letters. Therefore, the empty string is vacuously an isogram.

### 2. Null Pointer (`NULL`) — C Track Defensive Extension
- **Input**: `NULL` (`phrase == NULL`).
- **Expected Output**: `false`.
- **Specification Walkthrough**: In C, passing a null pointer into a function expecting a string would trigger undefined behavior (typically a segmentation fault) if dereferenced. As a defensive contract rule specific to the C track (`test_null`), the implementation must check `if (phrase == NULL)` and safely return `false`. Note: canonical problem specifications do not specify `null` as it is language-agnostic; this is a C-specific defensive extension.

### 3. Mixed-Case Duplicates (`"Alphabet"`, `"alphAbet"`)
- **Input**: `"Alphabet"` (uppercase 'A' at index 0, lowercase 'a' at index 4) and `"alphAbet"` (lowercase 'a' at index 0, uppercase 'A' at index 4).
- **Expected Output**: `false`.
- **Specification Walkthrough**: Duplication checking is strictly case-insensitive. Both `'A'` and `'a'` represent the same English letter. Normalizing characters via `toupper((unsigned char)c)` or `tolower((unsigned char)c)` maps both occurrences to the same canonical representation or bit position (`1 << (letter - 'A')`).

### 4. Non-Letter Repetitions (`"six-year-old"`, `"Emily Jung Schwartzkopf"`)
- **Input**: Phrases containing multiple hyphens (`'-'`) or multiple spaces (`' '`).
- **Expected Output**: `true`.
- **Specification Walkthrough**: The specification explicitly states: *"however spaces and hyphens are allowed to appear multiple times."* Using `isalpha(phrase[i])` allows non-alphabetic characters to be ignored without marking or recording duplicates.

### 5. Punctuation with Duplicate Letters (`"up-to-date"`, `"thumbscrew-jappingly"`)
- **Input**: `"up-to-date"` (contains two hyphens and repeated letter `'t'`) and `"thumbscrew-jappingly"` (contains one hyphen and repeated letter `'p'`).
- **Expected Output**: `false`.
- **Specification Walkthrough**: While hyphens are exempted from duplicate checks, any repeating alphabetic letter invalidates the isogram property regardless of surrounding punctuation.

### 6. Duplicate Letter Positions (Edges vs Middle)
- **Input**: `"zzyzx"` (adjacent duplicate `'z'` at beginning and end of alphabet), `"accentor"` (adjacent duplicate `'c'` in the middle), `"angola"` (duplicate `'a'` at first and last position).
- **Expected Output**: `false`.
- **Specification Walkthrough**: Position does not alter the contract. Any second observation of an alphabet letter triggers immediate return of `false`.

### 7. Test Metadata & Comment Key Preservation (`tests.toml`)
- **Specification**: In `.meta/tests.toml`, auto-generation comments state that inline comments are stripped during synchronization, but manually added keys are preserved:
  `so comments can be added in a "comment" key.`
- Test suites preserve individual test commentary across `configlet sync` through explicit `comment = "..."` keys.

---

## Decision Table

The following decision table maps each input condition and test case to its required result and contract status:

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
| **Non-ASCII / Multibyte (e.g. "café")** | `"café"` / UTF-8 | Unspecified | Outside Exercise Contract | N/A |
| **Numeric digits & symbols** | `"isogram123!"` | Unspecified | Outside Exercise Contract | N/A |
| **Unterminated / Invalid buffer** | Dangling pointer | Undefined | Outside Exercise Contract | N/A |

---

## Specified vs Unspecified Behavior

### Specified Behavior (Within Exercise Contract)
1. **ASCII Letters A-Z, a-z**: Both uppercase and lowercase ASCII letters are recognized and compared case-insensitively.
2. **Whitespace and Hyphens**: Spaces (`' '`) and hyphens (`'-'`) are permitted in any quantity and must be skipped.
3. **Empty String**: Evaluates to `true`.
4. **Null Pointer**: Evaluates to `false` without crashing (C track contract requirement).

### Unspecified Behavior (Outside Exercise Contract)
1. **Non-ASCII Characters**: Strings with multibyte UTF-8 sequences (such as accented vowels `é`, `ñ`, umlauts `ä`, or emoji) are not specified by the canonical problem domain. Implementations are not required to handle Unicode normalization or multi-byte decodings.
2. **Digits and Special Punctuation**: Characters such as numbers (`'0'`-`'9'`), punctuation marks (`'!'`, `'?'`, `','`, `'_'`), and control characters are outside the canonical specification.
3. **Buffer Validation**: The caller is required to supply a valid pointer to a null-terminated string or `NULL`. Passing unallocated memory, dangling pointers, or unterminated byte arrays is undefined behavior per the C language standard.
