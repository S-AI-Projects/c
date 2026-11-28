# Word Count: Exercise File-Role Map & Maintenance Guide

## Overview

This maintenance guide documents and verifies the metadata architecture, file-role contracts, test runner discovery mechanisms, canonical synchronization routes, and isolated verification procedures for the `word-count` practice exercise in the Exercism C track.

- **Exercise Slug**: `word-count`
- **Exercise Directory**: `exercises/practice/word-count`
- **Task ID**: `R48-T048`
- **Pinned Reference Implementation**: [`exercises/practice/word-count/.meta/example.c#L9` at `ffe5457`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/word-count/.meta/example.c#L9)

---

## Exercise-Specific File-Role Map

The exercise layout conforms to Exercism practice exercise specification v3. All paths are resolved relative to `exercises/practice/word-count/`. Declared paths reject parent directory traversal (`..`) and absolute path prefixes, ensuring all components resolve strictly inside the exercise directory.

### Declared File Roles (`.meta/config.json`)

The files object in `exercises/practice/word-count/.meta/config.json` declares the operational roles:

| Role | Declared Relative Path | Full Repository Path | Role Purpose & Runner Handling |
| :--- | :--- | :--- | :--- |
| **`solution`** | `word_count.c` | `exercises/practice/word-count/word_count.c` | Primary implementation file modified and submitted by the learner. In working tree, contains unsolved stub (`#include "word_count.h"`). |
| **`solution`** | `word_count.h` | `exercises/practice/word-count/word_count.h` | Public API header defining data structures (`word_count_word_t`), limits (`MAX_WORDS=20`, `MAX_WORD_LENGTH=50`), error codes, and function prototype `count_words()`. |
| **`test`** | `test_word_count.c` | `exercises/practice/word-count/test_word_count.c` | Unit test suite built with the Unity test framework. Executes test assertions against the function under test. Contains `TEST_IGNORE()` macros on tests 2–14 for progressive learner test unlocking. |
| **`example`** | `.meta/example.c` | `exercises/practice/word-count/.meta/example.c` | Maintained reference implementation providing a complete, conformant solution. Used by track CI and automated course checks to verify exercise solvability. |
| **`editor`** *(implicit)* | *Defaulted* | `word_count.c`, `word_count.h`, `test_word_count.c` | Exercism web editor configuration. When omitted from `.meta/config.json`, the Exercism web interface automatically defaults to displaying the declared `solution` and `test` files. |

### Supporting Exercise Files

| File Path | Classification | Purpose |
| :--- | :--- | :--- |
| `exercises/practice/word-count/.meta/config.json` | Metadata | Exercise metadata: authors (`StevenRoot`), contributors (11 authors), blurb, source, and file role definitions. |
| `exercises/practice/word-count/.meta/tests.toml` | Metadata / Sync Spec | Canonical test tracking configuration mapping upstream problem-specifications UUIDs, descriptions, inclusions, and reimplementations. |
| `exercises/practice/word-count/.docs/instructions.md` | Documentation | Markdown instructions rendered to the student describing the exercise requirements. |
| `exercises/practice/word-count/.docs/instructions.append.md` | Documentation | Track-specific guidance noting C-specific constraints (e.g. maximum words, case insensitivity, apostrophe handling). |
| `exercises/practice/word-count/.docs/introduction.md` | Documentation | Introductory concepts for the practice exercise. |
| `exercises/practice/word-count/makefile` | Build Configuration | GNU Makefile defining targets: `test` (compiles and runs `tests.out`), `memcheck` (runs AddressSanitizer), and `clean`. |
| `exercises/practice/word-count/test-framework/unity.c` | Test Framework | Embedded Unity test framework source implementation. |
| `exercises/practice/word-count/test-framework/unity.h` | Test Framework | Unity test framework public declarations and assertions. |
| `exercises/practice/word-count/test-framework/unity_internals.h` | Test Framework | Unity test internal data structures and colorized output macros. |

---

## Test Runner Discovery Mechanism

Automated test runners, continuous integration pipelines, and CLI tooling interact with the exercise according to well-defined discovery contracts:

### 1. How the Runner Finds `.meta/tests.toml`
- **Convention-Based Discovery**: Exercism tooling (specifically `configlet`) and CI test generators discover `tests.toml` via a standardized directory convention:
  $$\text{Path} = \langle\text{track\_root}\rangle / \text{exercises/practice/} \langle\text{slug}\rangle / \text{.meta/tests.toml}$$
- When `configlet sync --exercise word-count --tests include` is invoked, `configlet` directly reads this location to compare track test status against the canonical problem specification (`problem-specifications/exercises/word-count/canonical-data.json`).
- It parses UUID keys, reads `include` booleans, inspects `reimplements` pointers, and preserves user `comment` annotations.

### 2. How the Runner Finds `.meta/example.c`
- **Configuration-Driven Dynamic Resolution**: Rather than relying on hardcoded file names, the test runner reads `exercises/practice/word-count/.meta/config.json`.
- The runner inspects the `files.example` array:
  ```json
  "files": {
    "example": [
      ".meta/example.c"
    ]
  }
  ```
- It resolves each path relative to `exercises/practice/word-count/`, yielding `exercises/practice/word-count/.meta/example.c`.
- **Reference Execution Strategy**: To validate track health without modifying learner workspace files, the runner:
  1. Creates an isolated temporary directory.
  2. Copies the exercise directory (including dotfiles).
  3. Replaces the declared `solution` source (`word_count.c`) with `.meta/example.c`.
  4. Strips `TEST_IGNORE();` invocations in the scratch `test_word_count.c` to enable the full test suite.
  5. Invokes `make test` using the supplied Makefile and asserts exit code 0 with 0 failures and 0 ignored tests.

---

## Maintained vs Generated Files

| File | Maintenance Category | Origin & Synchronization Route |
| :--- | :--- | :--- |
| `exercises/practice/word-count/word_count.c` | **Hand-Maintained** | Track-maintained learner stub. Must remain unsolved in working tree (`#include "word_count.h"`). |
| `exercises/practice/word-count/word_count.h` | **Hand-Maintained** | Track-maintained public header defining `word_count_word_t` and `count_words()` signature. |
| `exercises/practice/word-count/.meta/example.c` | **Hand-Maintained** | Track-maintained reference solution containing word normalization and frequency counting logic. Pinned at line 9 (`static int word_match(...)`). |
| `exercises/practice/word-count/test_word_count.c` | **Hand-Maintained** | Track-maintained unit tests adapted from canonical specifications to C struct arrays. Uses Unity assertions (`TEST_ASSERT_EQUAL_STRING`, `TEST_ASSERT_EQUAL_INT`). |
| `exercises/practice/word-count/.meta/config.json` | **Hand-Maintained** | Track configuration defining metadata, author credits, and file roles. Linted by `configlet fmt`. |
| `exercises/practice/word-count/.meta/tests.toml` | **Tooling-Generated / Synced** | Generated and synchronized by `configlet sync` from upstream Exercism `problem-specifications/exercises/word-count/canonical-data.json`. |

---

## Key Handling Rules (The Three Named Cases)

When `exercises/practice/word-count/.meta/tests.toml` is synchronized using `configlet sync`, the generator enforces three invariant key-handling rules:

1. **Recreate every `description` key/value pair**:
   - Recreated from canonical test case titles in `canonical-data.json`.
   - Present across all 15 test entries in `tests.toml`.
2. **Recreate every `reimplements` key/value pair, where they exist in problem-specifications**:
   - Recreates explicit links where upstream problem specifications have superseded an earlier test case UUID.
   - Specifically demonstrated by case `4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3` ("with apostrophes"), which carries:
     ```toml
     [4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3]
     description = "with apostrophes"
     reimplements = "4185a902-bdb0-4074-864c-f416e42a0f19"
     ```
3. **Preserve any other key/value pair**:
   - Preserves manual track customization keys such as `include = false` and `comment = "..."`.
   - Specifically demonstrated by case `4185a902-bdb0-4074-864c-f416e42a0f19`:
     ```toml
     [4185a902-bdb0-4074-864c-f416e42a0f19]
     description = "with apostrophes"
     include = false
     comment = "Reimplemented"
     ```
   - Two successive runs of `configlet sync` produce bit-for-bit identical content, proving that custom keys are preserved and no canonical case is dropped.

---

## Canonical Case-to-Output Mapping

The canonical suite defines 15 cases. 1 case is excluded due to reimplementation (`4185a902-bdb0-4074-864c-f416e42a0f19`), leaving 14 active, implemented tests in `test_word_count.c`. All 14 tests execute and pass against the reference solution.

| # | Canonical UUID | Canonical Description | Status | Unity Test Function (`test_word_count.c`) | Input String Under Test |
|---|----------------|-----------------------|:------:|--------------------------------------------|-------------------------|
| 1 | `61559d5f-2cad-48fb-af53-d3973a9ee9ef` | count one word | Active | `test_count_one_word` | `"word"` |
| 2 | `5abd53a3-1aed-43a4-a15a-29f88c09cbbd` | count one of each word | Active | `test_count_one_of_each_word` | `"one of each"` |
| 3 | `2a3091e5-952e-4099-9fac-8f85d9655c0e` | multiple occurrences of a word | Active | `test_multiple_occurrences_of_a_word` | `"one fish two fish red fish blue fish"` |
| 4 | `e81877ae-d4da-4af4-931c-d923cd621ca6` | handles cramped lists | Active | `test_handles_cramped_lists` | `"one,two,three"` |
| 5 | `7349f682-9707-47c0-a9af-be56e1e7ff30` | handles expanded lists | Active | `test_handles_expanded_lists` | `"one,\ntwo,\nthree"` |
| 6 | `a514a0f2-8589-4279-8892-887f76a14c82` | ignore punctuation | Active | `test_ignore_punctuation` | `"car: carpet as java: javascript!!&@$%^&"` |
| 7 | `d2e5cee6-d2ec-497b-bdc9-3ebe092ce55e` | include numbers | Active | `test_include_numbers` | `"testing, 1, 2 testing"` |
| 8 | `dac6bc6a-21ae-4954-945d-d7f716392dbf` | normalize case | Active | `test_normalize_case` | `"go Go GO Stop stop"` |
| 9 | `4185a902-bdb0-4074-864c-f416e42a0f19` | with apostrophes | Excluded | *N/A (Reimplemented by 4ff6c7d7)* | `"First: don't laugh. Then: don't cry."` |
| 10 | `4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3` | with apostrophes | Active | `test_with_apostrophes` | `"First: don't laugh. Then: don't cry."` |
| 11 | `be72af2b-8afe-4337-b151-b297202e4a7b` | with quotations | Active | `test_with_quotations` | `"Joe can't tell between 'large' and large."` |
| 12 | `8d6815fe-8a51-4a65-96f9-2fb3f6dc6ed6` | substrings from the beginning | Active | `test_substrings_from_the_beginning` | `"Joe can't tell between app, apple and a."` |
| 13 | `c5f4ef26-f3f7-4725-b314-855c04fb4c13` | multiple spaces not detected as a word | Active | `test_multiple_spaces_not_detected_as_a_word` | `" multiple   whitespaces"` |
| 14 | `50176e8a-fe8e-4f4c-b6b6-aa9cf8f20360` | alternating word separators not detected as a word | Active | `test_alternating_word_separators_not_detected_as_a_word` | `",\n,one,\n ,two \n 'three'"` |
| 15 | `6d00f1db-901c-4bec-9829-d20eb3044557` | quotation for word with apostrophe | Active | `test_quotation_for_word_with_apostrophe` | `"can, can't, 'can't'"` |

---

## Isolated Verification Procedure

The reference implementation is validated strictly inside an isolated scratch workspace:
1. `validate_files_metadata()` parses `.meta/config.json`, resolves each path, and rejects any parent traversal attempts (`..` or absolute paths).
2. The checker tests three intentionally invalid metadata fixtures:
   - `missing-reference`: declared example file does not exist $\to$ raises `FileNotFoundError`.
   - `missing-test`: declared test file does not exist $\to$ raises `FileNotFoundError`.
   - `outside-exercise`: declared path contains `../outside.c` $\to$ raises `ValueError`.
   All three fixtures fail as intended; the real config passes.
3. A scratch copy of `exercises/practice/word-count` (including hidden directories `.meta` and `.docs`) is created in a temporary directory.
4. `.meta/example.c` is copied over `word_count.c` in the scratch copy only.
5. In the scratch copy of `test_word_count.c`, `TEST_IGNORE();` lines are stripped.
6. `make test` is executed inside the scratch copy using the exercise Makefile.
7. Return code 0, 14 passed tests, 0 failures, and 0 ignored tests are asserted.
8. The working tree remains completely untouched; `word_count.c` remains an unsolved starter stub.

---

## Reproducible Validation Commands

To reproduce the automated verification and canonical synchronization locally:

```bash
# 1. Run the primary automated task verification check
python3 work/R48-T048/check.py

# 2. Run the course check suite
python3 tools/course_checks/r48-t048.py

# 3. Synchronize canonical tests using configlet (offline)
./bin/configlet sync --exercise word-count --tests include --update --yes --offline

# 4. Format exercise configuration
./bin/configlet fmt --exercise word-count
```

---

## Verification & Task Checklists

### Done When Checklist
- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] The real config passes; all three deliberately invalid metadata fixtures fail for the intended reason.
- [x] The maintenance document names the real stub, reference and test paths and distinguishes generated artifacts.

### Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.

### General PR Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [x] I have addressed previous review feedback, if applicable.
