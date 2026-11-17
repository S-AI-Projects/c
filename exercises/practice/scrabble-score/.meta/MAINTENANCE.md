# Maintenance Notes — scrabble-score

## Contract Analysis and Decision Table

This document explains the specification contract for `scrabble-score` (`exercises/practice/scrabble-score/`).

### Contract Decision Table

The exercise specification defines behavior for valid English Scrabble words. The table below connects each input condition to its expected result under the contract:

| Input Condition | Example Input | Expected Score | Rule Justification |
| :--- | :--- | :--- | :--- |
| **Empty string** | `""` | `0` | Contains no letters; score loop terminates immediately on `'\0'`. |
| **Single lowercase letter** | `"a"`, `"f"` | `1`, `4` | Direct letter point lookup from standard table (`a=1`, `f=4`). |
| **Single uppercase letter** | `"A"` | `1` | Case insensitivity required: uppercase letters have identical value to lowercase. |
| **Multi-letter short word** | `"at"` | `2` | Summation of letter values (`a=1`, `t=1` → 1+1 = 2). |
| **High-value word** | `"zoo"`, `"quirky"` | `12`, `22` | Summation with high-value consonants (`z=10`, `q=10`, `k=5`). |
| **Mixed-case word** | `"OxyphenButazone"` | `41` | Case normalization across mixed upper/lower case letters without penalty. |
| **Full English alphabet** | `"abcdefghijklmnopqrstuvwxyz"` | `87` | Sum of all 26 English alphabet letters equals exactly 87 points. |

### Specified vs Unspecified Behavior

#### 1. In-Contract (Specified)
- Input is a valid null-terminated string composed of ASCII letters (`[a-zA-Z]`) and/or the empty string (`""`).
- Case is strictly insensitive: `'A'` is identical in score to `'a'`.
- Score is cumulative: points of individual characters are summed with no word-length multipliers unless specified.

#### 2. Out-of-Contract (Unspecified by Specification)
- **Non-alphabetic characters:** Digits (`"123"`), punctuation (`"hello!"`), spaces (`"a b"`), or accented characters are not part of the problem specification. The reference implementation indexes `score_book[c - 'a']`, which assumes `c` is within `'a'..'z'`.
- **NULL pointer:** Passing a `NULL` pointer is undefined behavior (standard C string convention requires caller to provide valid pointer).
- **No extra exceptions or coercion:** No error codes, exceptions, or special ordering requirements are imposed beyond what the canonical specification requires.
