# Zebra Puzzle: Isolated Test Runner & Maintenance Guide

## Overview

This maintenance document details the isolated test runner and verification architecture for `exercises/practice/zebra-puzzle` in the Exercism C track (Task R48-T049).

- **Exercise**: `exercises/practice/zebra-puzzle`
- **Pinned Reference**: [`exercises/practice/zebra-puzzle/.meta/example.c#L9` at `ffe5457`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/zebra-puzzle/.meta/example.c#L9) (`enum { NUM_HOUSES = 5 };`)
- **Primary Goal**: Execute reference implementation tests in an isolated temporary copy, report real test counts, propagate failures, and guarantee that learner starter files (`zebra_puzzle.c`, `zebra_puzzle.h`) remain completely unsolved and bit-for-bit unchanged.

## Tool Requirements & Prerequisites

The runner requires standard C track development tools:

| Tool | Minimum Version | Tested Version | Purpose |
|------|-----------------|----------------|---------|
| **Python** | 3.8+ | 3.15.2 | Test runner, isolation orchestration, and verification (`subprocess`, `tempfile`, `hashlib`) |
| **C Compiler** | C99 compliant (`clang` or `gcc`) | Apple clang 21.0.0 | Compiling test suites with `-Wall -Wextra -pedantic -Werror` |
| **GNU Make** | 3.81+ | GNU Make 3.81 | Building and running exercise test target (`make test`) |
| **Configlet** | 4.0.0+ | 4.0.3 | Exercism track configuration and canonical test synchronizer |
| **Unity Framework** | Bundled | Exercism vendored | C unit test assertions and report runner (`test-framework/unity.c`) |

## Reproduction Commands

To run the isolated test runner and automated verification checks:

```bash
# 1. Run the isolated test runner
python3 tools/course_checks/r48-t049.py

# 2. Run the automated course verification suite
python3 work/R48-T049/check.py

# 3. Synchronize canonical tests via configlet
./bin/fetch-configlet
./bin/configlet sync --exercise zebra-puzzle --tests include
```

## Runner Architecture & Isolation Workflow

To prevent accidental modification or solution leakage into the learner starter files, the runner enforces strict isolation:

```
[Repository Working Tree]
   exercises/practice/zebra-puzzle/
   ├── zebra_puzzle.c (unsolved starter stub - untouched)
   ├── zebra_puzzle.h (unsolved starter header - untouched)
   ├── .meta/example.c (reference implementation)
   └── .meta/example.h (reference header)
           │
           │ 1. Compute SHA-256 hashes of learner files
           │ 2. Read .meta/config.json (resolve solution, test, example paths)
           ▼
[Isolated Temporary Directory (tempfile.TemporaryDirectory)]
   tmp_dir/zebra-puzzle/
   ├── Copy exercise tree (including dotfiles: .meta, .docs)
   ├── Substitute reference files into solution target paths:
   │     .meta/example.c -> zebra_puzzle.c
   │     .meta/example.h -> zebra_puzzle.h
   ├── Enable all test cases (strip `TEST_IGNORE();`)
   ├── Execute `make test` via subprocess
   ├── Parse Unity results (count, failures, ignored, returncode)
   └── Automatic cleanup on exit (context manager)
           │
           │ 3. Assert child return code and test count > 0
           │ 4. Re-compute SHA-256 hashes of working tree learner files
           ▼
[Verification Assertions]
   Hash(before) == Hash(after)
   Learner stub remains unsolved
   Temporary directory deleted
```

### Safety and Cleanup Invariants

1. **Working Tree Immutability**: All compilation artifacts (`tests.out`, `*.o`) and reference file replacements occur exclusively inside a `tempfile.TemporaryDirectory()`. The working directory is never written to during testing.
2. **Deterministic Cleanup**: Even if `make test` fails, an assertion fails, or an interrupt signal is received, Python's context manager automatically removes the temporary directory.
3. **Cryptographic Integrity**: SHA-256 hashes of learner files are verified before and after each execution scenario to ensure zero alteration.

## Runner Test Scenarios

The runner suite evaluates three distinct execution scenarios:

| Scenario | Configuration | Expected Return Code | Expected Tests Run | Expected Status | Description |
|----------|---------------|----------------------|--------------------|-----------------|-------------|
| **1. Real Reference** | Official `.meta/example.c` | `0` | `2` | `PASS` | All canonical cases pass with 0 failures and 0 ignored. |
| **2. Deliberately Failing Reference** | Mutated `solve_puzzle()` (`drinks_water = "Ukrainian"`) | `!= 0` (`2`) | `2` | `FAIL` | Unity rejects assertion (`Expected Norwegian Was Ukrainian`); failure is correctly propagated. |
| **3. Empty Test Selection** | Zero test cases active | `!= 0` (`1`) | `0` | `FAIL` | Runner detects 0 executed tests and exits non-zero. |

## Canonical Test Case Mapping

The zebra-puzzle exercise tests the canonical specification defined in Exercism's `problem-specifications`:

| Canonical UUID | Description | Unity Test Function | Expected Solution Value |
|----------------|-------------|---------------------|-------------------------|
| `16efb4e4-8ad7-4d5e-ba96-e5537b66fd42` | resident who drinks water | `test_who_drinks_water` | `drinks_water == "Norwegian"` |
| `084d5b8b-24e2-40e6-b008-c800da8cd257` | resident who owns zebra | `test_who_owns_the_zebra` | `owns_zebra == "Japanese"` |

## The Three Cases (Key Handling Rules)

When synchronizing `exercises/practice/zebra-puzzle/.meta/tests.toml` via `configlet sync`:

1. **Recreate every `description` key/value pair**: Matches canonical data from `problem-specifications`.
2. **Recreate every `reimplements` key/value pair**: Preserves any upstream reimplements pointers where defined.
3. **Preserve any other key/value pair**: User-added `comment` keys are preserved across sync operations without loss.

## Verification Checklist

### Done When Checklist
- [x] The named cases (- Recreate every description key/value pair; - Recreate every reimplements key/value pair, where they exist in problem-specifications; - Preserve any other key/value pair) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] Success, assertion failure and zero-test runs produce the correct exit status; temporary files are cleaned up.
- [x] The learner file hashes are identical before and after every run, including an interrupted or failing run.

### Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.
