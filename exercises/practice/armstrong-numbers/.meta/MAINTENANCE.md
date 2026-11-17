# Armstrong Numbers: Test Generation & Maintenance Guide

## Overview

This document describes the test generation and maintenance path for the `armstrong-numbers` exercise in the Exercism C track.

## Canonical Data Source

The canonical test cases originate from the Exercism problem-specifications repository:
- **Source**: `exercism/problem-specifications/exercises/armstrong-numbers/canonical-data.json`
- **Track Metadata**: `exercises/practice/armstrong-numbers/.meta/tests.toml`

## Synchronization / Generation Route

The canonical tests are tracked and synchronized using Exercism's `configlet` utility.

### Command to Reproduce

To synchronize and regenerate `tests.toml`:
```bash
# 1. Fetch configlet if not present
./bin/fetch-configlet

# 2. Synchronize exercise tests metadata
./bin/configlet sync --exercise armstrong-numbers --tests
```

### Key Handling Rules During Regeneration

When regenerating `exercises/practice/armstrong-numbers/.meta/tests.toml`, the generator anchors on three rules:
1. **Recreate every `description` key/value pair**: Matches the upstream canonical test description from `canonical-data.json`.
2. **Recreate every `reimplements` key/value pair**: Recreates any reimplemented test UUIDs where specified in `problem-specifications`.
3. **Preserve any other key/value pair**:
   - Preserves manual exclusions such as `include = false`.
   - Preserves custom rationale comments added via the `comment` key.

### Excluded Cases Rationale

In `exercises/practice/armstrong-numbers/.meta/tests.toml`, two canonical test cases are excluded:
- UUID `5ee2fdf8-334e-4a46-bb8d-e5c19c02c148` ("Armstrong number containing seven zeroes")
- UUID `12ffbf10-307a-434e-b4ad-c925680e1dd4` ("The largest and last Armstrong number")

**Reason**: Standard C99 primitive integer types (`int`, `uint64_t`) cannot natively represent arbitrary-precision integers or 39-digit Armstrong numbers without an external BigInt dependency. Therefore, `include = false` with explanatory `comment` keys are preserved across synchronizations.

## Maintained vs Generated Files

- **Generated / Synchronized:**
  - `exercises/practice/armstrong-numbers/.meta/tests.toml`: Managed via `configlet sync`.
- **Maintained by Hand:**
  - `test_armstrong_numbers.c`: Unit tests implementing Unity test assertions corresponding to the enabled canonical test cases. No per-exercise Jinja template exists for C test generation; tests are maintained directly.
  - `armstrong_numbers.h` & `armstrong_numbers.c`: Learner starter interface and stub.
  - `.meta/example.h` & `.meta/example.c`: Reference solution.
  - `.meta/config.json`: Exercise metadata and file configuration.
  - `.docs/instructions.md`: Problem description.
