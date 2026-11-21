# high-scores — exercise maintenance and file-role map (R48-T018)

## Overview

This maintenance document establishes the file-role mapping and verification procedures for `exercises/practice/high-scores`. It documents how the exercise metadata in `.meta/config.json` resolves, explains how the Exercism test runner and tooling locate canonical test configurations and reference implementations, and distinguishes hand-maintained files from generated or vendored artifacts.

## Reproducible Validation

Run the automated verification suite from the repository root:

```sh
python3 work/R48-T018/check.py
```

or directly via the course check tool:

```sh
python3 tools/course_checks/r48-t018.py
```

The check verifies:
1. All declared files in `.meta/config.json` resolve inside `exercises/practice/high-scores` with no parent traversal (`..`) or absolute paths.
2. Deliberately invalid fixtures (`missing-reference`, `missing-test`, `outside-exercise`) fail for their intended reasons.
3. The reference implementation (`.meta/example.c` + `.meta/example.h`) builds and passes all 7 intended Unity test cases (0 failures, 0 ignored).
4. The learner stub (`high_scores.c`) remains unsolved (fails to link or pass).
5. The working tree is unmodified during execution.

---

## File-Role Map

All file paths resolve relative to `exercises/practice/high-scores/`:

| Role | Path | Lifecycle | Description |
|---|---|---|---|
| **Solution (stub)** | `high_scores.c` | Hand-maintained | Learner stub. Contains only `#include "high_scores.h"`; must remain unsolved. |
| **Solution (header)** | `high_scores.h` | Hand-maintained | Public interface defining `latest()`, `personal_best()`, and `personal_top_three()`. |
| **Test** | `test_high_scores.c` | Hand-maintained | Unity test suite declaring 7 active test cases mapped from canonical specifications. |
| **Example (C)** | `.meta/example.c` | Hand-maintained | Canonical reference implementation used by CI to validate test suite. |
| **Example (H)** | `.meta/example.h` | Hand-maintained | Reference header accompanying `example.c` (identical to `high_scores.h`). |
| **Config** | `.meta/config.json` | Hand-maintained | Track metadata mapping authors, contributors, blurb, and file roles. |
| **Tests TOML** | `.meta/tests.toml` | Generated / Synced | Canonical test-case inclusion map synced from `problem-specifications` via `configlet`. |
| **Instructions** | `.docs/instructions.md` | Generated / Synced | Upstream problem instructions synced from `problem-specifications`. |
| **Instructions Append** | `.docs/instructions.append.md` | Hand-maintained | C-track-specific notes explaining array layout and output buffer parameters. |
| **Build** | `makefile` | Hand-maintained | GNU Makefile configuring compiler flags, include paths, and Unity target `test`. |
| **Framework** | `test-framework/unity.c` | Vendored | Unity test framework C implementation. |
| **Framework** | `test-framework/unity.h` | Vendored | Unity test framework main header. |
| **Framework** | `test-framework/unity_internals.h` | Vendored | Unity test framework internal definitions. |

---

## Artifact Categories

1. **Hand-maintained files**:
   - `high_scores.c`: Learner stub. Maintained as a minimal skeleton so students have a clean starting point.
   - `high_scores.h`: Public API contract. Defines standard types (`int32_t`, `size_t`) and function prototypes.
   - `test_high_scores.c`: Written in C using Unity. Exercises the API contracts with test helpers (`check_personal_top_three`).
   - `.meta/example.c` & `.meta/example.h`: Complete reference implementation used to prove test suite correctness.
   - `.docs/instructions.append.md`: Track-specific appendix detailing array conventions and memory expectations for C students.
   - `makefile`: Standard track build harness with strict warnings (`-Wall -Wextra -pedantic`).

2. **Generated / Synced artifacts**:
   - `.meta/tests.toml`: Created and updated by `configlet sync --tests`. Contains UUID-based inclusion records derived from `exercism/problem-specifications`. The header comment includes:
     `# Regular comments will be removed when this file is regenerated. Regenerating will not touch any manually added keys, so comments can be added in a "comment" key.`
   - `.docs/instructions.md`: Synced from canonical problem specifications. Do not edit directly; upstream changes propagate via `configlet sync --docs`.

3. **Vendored artifacts**:
   - `test-framework/unity.*`: Upstream Unity test harness files. Vendored directly into each exercise directory so exercises can build standalone without external package dependencies.

---

## Tooling & Runner Path Resolution

### How the test runner finds `.meta/config.json` and `.meta/example.c`

1. **Exercise Discovery**:
   - The Exercism test runner (and CI workflows) locates the exercise directory by track convention: `exercises/practice/<slug>`.
   - In this case, `<slug>` is `high-scores`.

2. **Metadata Parsing**:
   - The runner opens `exercises/practice/high-scores/.meta/config.json`.
   - The JSON object must contain a top-level `"files"` dictionary with three required arrays:
     - `"files.solution"`: `["high_scores.c", "high_scores.h"]`
     - `"files.test"`: `["test_high_scores.c"]`
     - `"files.example"`: `[".meta/example.c", ".meta/example.h"]`

3. **Locating the Reference Implementation (`.meta/example.c`)**:
   - The runner resolves paths in `files.example` relative to the exercise directory:
     `exercises/practice/high-scores/` + `.meta/example.c` = `exercises/practice/high-scores/.meta/example.c`.
   - For automated verification in CI, the test runner copies `.meta/example.c` over the solution file `high_scores.c` (and `.meta/example.h` over `high_scores.h`), enables all test cases in `test_high_scores.c`, and invokes `make test`.

### How the tooling finds `.meta/tests.toml`

1. **Configlet Convention**:
   - `configlet` (the Exercism track maintenance CLI) expects the test-case configuration at the fixed relative path:
     `<exercise_dir>/.meta/tests.toml`.
   - During `configlet sync --tests -e high-scores`, configlet fetches the canonical data for `high-scores` from `exercism/problem-specifications/exercises/high-scores/canonical-data.json`.
   - It reads `.meta/tests.toml` to determine which UUIDs are included (`include = true` or default) and which are omitted (`include = false`).
   - If a test case in `tests.toml` is marked `include = false`, track maintainers do not generate or maintain a corresponding C test function.

---

## Canonical Test Case Mapping

`exercises/practice/high-scores/.meta/tests.toml` records 12 canonical test cases. 7 are included and implemented in `test_high_scores.c`; 5 are excluded (`include = false`) because mutable state inspection methods are not part of this C track exercise contract:

| # | UUID | Canonical Description | Status | C Test Function |
|---|---|---|---|---|
| 1 | `1035eb93-2208-4c22-bab8-fef06769a73c` | List of scores | Excluded (`include = false`) | — |
| 2 | `6aa5dbf5-78fa-4375-b22c-ffaa989732d2` | Latest score | Included | `test_latest_score` |
| 3 | `b661a2e1-aebf-4f50-9139-0fb817dd12c6` | Personal best | Included | `test_personal_best` |
| 4 | `3d996a97-c81c-4642-9afc-80b80dc14015` | Top 3 scores -> Personal top three from a list of scores | Included | `test_personal_top_three_from_a_list_of_scores` |
| 5 | `1084ecb5-3eb4-46fe-a816-e40331a4e83a` | Top 3 scores -> Personal top highest to lowest | Included | `test_personal_top_highest_to_lowest` |
| 6 | `e6465b6b-5a11-4936-bfe3-35241c4f4f16` | Top 3 scores -> Personal top when there is a tie | Included | `test_personal_top_when_there_is_a_tie` |
| 7 | `f73b02af-c8fd-41c9-91b9-c86eaa86bce2` | Top 3 scores -> Personal top when there are less than 3 | Included | `test_personal_top_when_there_are_less_than_3` |
| 8 | `16608eae-f60f-4a88-800e-aabce5df2865` | Top 3 scores -> Personal top when there is only one | Included | `test_personal_top_when_there_is_only_one` |
| 9 | `2df075f9-fec9-4756-8f40-98c52a11504f` | Top 3 scores -> Latest score after personal top scores | Excluded (`include = false`) | — |
| 10 | `809c4058-7eb1-4206-b01e-79238b9b71bc` | Top 3 scores -> Scores after personal top scores | Excluded (`include = false`) | — |
| 11 | `ddb0efc0-9a86-4f82-bc30-21ae0bdc6418` | Top 3 scores -> Latest score after personal best | Excluded (`include = false`) | — |
| 12 | `6a0fd2d1-4cc4-46b9-a5bb-2fb667ca2364` | Top 3 scores -> Scores after personal best | Excluded (`include = false`) | — |

The anchor phrase `so comments can be added in a "comment" key.` is present at line 3 of `.meta/tests.toml`.
