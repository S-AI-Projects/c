# Variable Length Quantity: Test Maintenance & Mutation Analysis Guide

## Overview

This maintenance page documents the contract, test cases, and mutation-driven regression analysis for the `variable-length-quantity` practice exercise in the Exercism C track.

- **Track exercise**: `exercises/practice/variable-length-quantity`
- **Pinned reference implementation source**: [`exercises/practice/variable-length-quantity/.meta/example.c#L3` at `ffe5457`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/variable-length-quantity/.meta/example.c#L3).
- **Task ID**: `R48-T043`

## Canonical Data Source & Key Handling Rules

Canonical test cases originate from Exercism's `problem-specifications` repository:
- **Canonical data**: `exercises/variable-length-quantity/canonical-data.json`
- **Track metadata**: `exercises/practice/variable-length-quantity/.meta/tests.toml`
- **Exercise configuration**: `exercises/practice/variable-length-quantity/.meta/config.json`

### Key Handling Rules (tests.toml)

When regenerating or synchronizing `tests.toml` via `configlet sync`:
1. **Recreate every `description` key/value pair**: Matches canonical problem descriptions.
2. **Recreate every `reimplements` key/value pair**: Preserves canonical UUID tracking where tests are reimplemented.
3. **Preserve any other key/value pair**: Preserves custom metadata and comments added via `comment` keys (as inline `#` comments are not preserved by the generator).

## Maintained vs Generated Files

- **Synchronized by Tooling:**
  - `exercises/practice/variable-length-quantity/.meta/tests.toml`: Synchronized from canonical data using `configlet sync`.
- **Maintained by Hand:**
  - `test_variable_length_quantity.c`: Unity test suite containing unit tests mapped to canonical specifications.
  - `variable_length_quantity.h` & `variable_length_quantity.c`: Learner starter stub.
  - `.meta/example.h` & `.meta/example.c`: Reference solution.
  - `.docs/instructions.md`: Problem instructions.
  - `.docs/hints.md`: Learner debugging hints.
  - `.meta/config.json`: File path mappings and author metadata.

## Contract Specification

Variable Length Quantity (VLQ) encodes 32-bit unsigned integers into a sequence of 7-bit bytes:
- The 7 significant bits of each byte are right-justified.
- Encoded bytes are arranged in **big-endian** order (most significant 7-bit group first).
- **Continuation bit (bit 7, `0x80`)**:
  - In all leading bytes of an integer's encoding, bit 7 is **set** (`1`).
  - In the final (least significant) byte of the sequence, bit 7 is **cleared** (`0`).
- **Zero Value Contract**:
  - The value `0` is a valid 32-bit unsigned integer and must be encoded as exactly one byte: `[0x00]`.
- **Single-byte Range**: Integers from `0` to `127` (`0x00` to `0x7f`) encode as a single byte.
- **Multi-byte Range**: Integers `>= 128` (`0x80`) require multiple bytes, with continuation bits set on all bytes except the terminal byte.

## Case-to-Output Mapping

All 26 canonical test cases (18 encode, 8 decode) are implemented in `test_variable_length_quantity.c`:

| # | Canonical UUID | Canonical Description | Unity Test Function | Expected Behavior |
|---|----------------|-----------------------|---------------------|-------------------|
| 1 | `35c9db2e-f781-4c52-b73b-8e76427defd0` | Encode: zero | `test_zero` | `{ 0x0 }` -> `{ 0x0 }` (len 1) |
| 2 | `be44d299-a151-4604-a10e-d4b867f41540` | Encode: arbitrary single byte | `test_arbitrary_single_byte` | `{ 0x40 }` -> `{ 0x40 }` (len 1) |
| 3 | `ea399615-d274-4af6-bbef-a1c23c9e1346` | Encode: largest single byte | `test_largest_single_byte` | `{ 0x7f }` -> `{ 0x7f }` (len 1) |
| 4 | `77b07086-bd3f-4882-8476-8dcafee79b1c` | Encode: smallest double byte | `test_smallest_double_byte` | `{ 0x80 }` -> `{ 0x81, 0x0 }` (len 2) |
| 5 | `63955a49-2690-4e22-a556-0040648d6b2d` | Encode: arbitrary double byte | `test_arbitrary_double_byte` | `{ 0x2000 }` -> `{ 0xc0, 0x0 }` (len 2) |
| 6 | `29da7031-0067-43d3-83a7-4f14b29ed97a` | Encode: largest double byte | `test_largest_double_byte` | `{ 0x3fff }` -> `{ 0xff, 0x7f }` (len 2) |
| 7 | `3345d2e3-79a9-4999-869e-d4856e3a8e01` | Encode: smallest triple byte | `test_smallest_triple_byte` | `{ 0x4000 }` -> `{ 0x81, 0x80, 0x0 }` (len 3) |
| 8 | `5df0bc2d-2a57-4300-a653-a75ee4bd0bee` | Encode: arbitrary triple byte | `test_arbitrary_triple_byte` | `{ 0x100000 }` -> `{ 0xc0, 0x80, 0x0 }` (len 3) |
| 9 | `f51d8539-312d-4db1-945c-250222c6aa22` | Encode: largest triple byte | `test_largest_triple_byte` | `{ 0x1fffff }` -> `{ 0xff, 0xff, 0x7f }` (len 3) |
| 10 | `da78228b-544f-47b7-8bfe-d16b35bbe570` | Encode: smallest quadruple byte | `test_smallest_quadruple_byte` | `{ 0x200000 }` -> `{ 0x81, 0x80, 0x80, 0x0 }` (len 4) |
| 11 | `11ed3469-a933-46f1-996f-2231e05d7bb6` | Encode: arbitrary quadruple byte | `test_arbitrary_quadruple_byte` | `{ 0x8000000 }` -> `{ 0xc0, 0x80, 0x80, 0x0 }` (len 4) |
| 12 | `d5f3f3c3-e0f1-4e7f-aad0-18a44f223d1c` | Encode: largest quadruple byte | `test_largest_quadruple_byte` | `{ 0xfffffff }` -> `{ 0xff, 0xff, 0xff, 0x7f }` (len 4) |
| 13 | `91a18b33-24e7-4bfb-bbca-eca78ff4fc47` | Encode: smallest quintuple byte | `test_smallest_quintuple_byte` | `{ 0x10000000 }` -> `{ 0x81, 0x80, 0x80, 0x80, 0x0 }` (len 5) |
| 14 | `5f34ff12-2952-4669-95fe-2d11b693d331` | Encode: arbitrary quintuple byte | `test_arbitrary_quintuple_byte` | `{ 0xff000000 }` -> `{ 0x8f, 0xf8, 0x80, 0x80, 0x0 }` (len 5) |
| 15 | `7489694b-88c3-4078-9864-6fe802411009` | Encode: maximum 32-bit integer | `test_maximum_32_bit_integer_input` | `{ 0xffffffff }` -> `{ 0x8f, 0xff, 0xff, 0xff, 0x7f }` (len 5) |
| 16 | `f9b91821-cada-4a73-9421-3c81d6ff3661` | Encode: two single-byte values | `test_two_single_byte_values` | `{ 0x40, 0x7f }` -> `{ 0x40, 0x7f }` (len 2) |
| 17 | `68694449-25d2-4974-ba75-fa7bb36db212` | Encode: two multi-byte values | `test_two_multi_byte_values` | `{ 0x4000, 0x123456 }` -> `{ 0x81, 0x80, 0x0, 0xc8, 0xe8, 0x56 }` (len 6) |
| 18 | `51a06b5c-de1b-4487-9a50-9db1b8930d85` | Encode: many multi-byte values | `test_many_multi_byte_values` | 6 integers -> 15 bytes |
| 19 | `baa73993-4514-4915-bac0-f7f585e0e59a` | Decode: one byte | `test_one_byte` | `{ 0x7f }` -> `{ 0x7f }` (len 1) |
| 20 | `72e94369-29f9-46f2-8c95-6c5b7a595aee` | Decode: two bytes | `test_two_bytes` | `{ 0xc0, 0x0 }` -> `{ 0x2000 }` (len 1) |
| 21 | `df5a44c4-56f7-464e-a997-1db5f63ce691` | Decode: three bytes | `test_three_bytes` | `{ 0xff, 0xff, 0x7f }` -> `{ 0x1fffff }` (len 1) |
| 22 | `1bb58684-f2dc-450a-8406-1f3452aa1947` | Decode: four bytes | `test_four_bytes` | `{ 0x81, 0x80, 0x80, 0x0 }` -> `{ 0x200000 }` (len 1) |
| 23 | `cecd5233-49f1-4dd1-a41a-9840a40f09cd` | Decode: maximum 32-bit integer | `test_maximum_32_bit_integer` | 5 bytes -> `{ 0xffffffff }` (len 1) |
| 24 | `e7d74ba3-8b8e-4bcb-858d-d08302e15695` | Decode: incomplete sequence error | `test_incomplete_sequence_causes_error` | `{ 0xff }` -> `-1` (error) |
| 25 | `aa378291-9043-4724-bc53-aca1b4a3fcb6` | Decode: incomplete sequence error (zero) | `test_incomplete_sequence_causes_error_even_if_value_is_zero` | `{ 0x80 }` -> `-1` (error) |
| 26 | `a91e6f5a-c64a-48e3-8a75-ce1a81e0ebee` | Decode: multiple values | `test_multiple_values` | 15 bytes -> 6 integers |

## Deliberate Mutant Analysis

### Primary Mutant: Pre-conditioned Loop Mutation in `encode()`

A common implementation pitfall is assuming that integer conversion can be done via a pre-condition loop (`while (integer)`), as is common in decimal or hexadecimal formatting routines. In a temporary reference copy, we introduce this deliberate mutant by switching from a post-condition `do ... while (integer);` loop to a pre-condition `while (integer)` loop:

#### Mutant Diff

```diff
--- a/exercises/practice/variable-length-quantity/.meta/example.c
+++ b/exercises/practice/variable-length-quantity/variable_length_quantity.c
@@ -10,12 +10,11 @@ int encode(const uint32_t *integers, size_t integers_len, uint8_t *output)
       uint8_t buf[5];   // lifo
       int buf_idx = 0;
       // push
-      do {
+      while (integer) {
          uint8_t part = (uint8_t)(integer & 0x7f);
          integer >>= 7;
          buf[buf_idx++] = part | mask;
          mask |= 0x80;
-      } while (integer);
+      }
       // pop
       while (buf_idx--) {
          output[output_index++] = buf[buf_idx];
```

#### Mistaken Assumption Exposed

The developer mistakenly assumes that if an integer is zero, no 7-bit chunks need to be extracted or pushed to the output buffer. Under this assumption:
- For input `0`, the loop condition `while (integer)` evaluates to false immediately.
- Zero bytes are written to the output buffer (`response_len = 0`).
- This violates the VLQ specification: every integer, including `0`, must produce at least one byte (`0x00`).

#### Rejecting Test Case & Minimal Input Reduction

When running against identical test inputs, the mutant causes failures in:
1. `test_zero` (input `{ 0x0 }`): fails with `Expected 1 Was 0`.
2. `test_many_multi_byte_values` (contains `0x0` among 6 values): fails with `Expected 15 Was 14`.

Reducing this to the **smallest input allowed by the specification**:
- **Rejecting Test ID**: `35c9db2e-f781-4c52-b73b-8e76427defd0`
- **Unity Test Function**: `test_zero`
- **Input**: `integers = { 0x0 }`, `integers_len = 1` (the minimal possible 32-bit unsigned integer)
- **Expected Result**: `expected_len = 1`, `response = { 0x00 }`
- **Actual Mutant Result**: `response_len = 0` (0 bytes emitted)
- **Named Assertion Failure**:
  ```text
  ./test_variable_length_quantity.c:22:test_zero:FAIL: Expected 1 Was 0
  ```

### Secondary Mutant: Premature Termination Boundary Mutation

A second deliberate mutant alters the loop boundary condition from `while (integer)` to `while (integer > 0x7f)`.

#### Mutant Diff

```diff
--- a/exercises/practice/variable-length-quantity/.meta/example.c
+++ b/exercises/practice/variable-length-quantity/variable_length_quantity.c
@@ -18,1 +18,1 @@
-      } while (integer);
+      } while (integer > 0x7f);
```

#### Mistaken Assumption Exposed

The developer assumes that multi-byte encoding should continue only while the remaining value exceeds the single-byte maximum (`0x7f`). However, because 7 bits have already been shifted off (`integer >>= 7`), any non-zero remainder (`integer > 0`) indicates another byte is required. For `0x80`, `0x80 >> 7 == 1` (which is `<= 0x7f`), causing the loop to exit after 1 byte instead of 2.

#### Rejecting Test Case & Minimal Input Reduction

- **Rejecting Test ID**: `77b07086-bd3f-4882-8476-8dcafee79b1c`
- **Unity Test Function**: `test_smallest_double_byte`
- **Input**: `integers = { 0x80 }`, `integers_len = 1` (the smallest input requiring multi-byte encoding)
- **Expected Result**: `expected_len = 2`, `expected = { 0x81, 0x00 }`
- **Actual Mutant Result**: `response_len = 1`, `response = { 0x00 }`
- **Named Assertion Failure**:
  ```text
  ./test_variable_length_quantity.c:61:test_smallest_double_byte:FAIL: Expected 2 Was 1
  ```

## Evaluation of Existing Test Suite Coverage

The task instructions specify:
> "If the suite misses it, add a proposed case with an explicit input and expected result to the maintenance page; do not assert that the current implementation is buggy."

**Assessment**:
Both deliberate mutants are immediately rejected by existing canonical test cases:
1. `test_zero` (`35c9db2e-f781-4c52-b73b-8e76427defd0`) rejects the pre-condition loop mutant at the smallest input allowed by the specification (`0x0`).
2. `test_smallest_double_byte` (`77b07086-bd3f-4882-8476-8dcafee79b1c`) rejects the boundary condition mutant at the smallest multi-byte input (`0x80`).

Thus, the canonical test suite already possesses complete boundary coverage for these mutations. The proposed diagnostic cases are fully reflected in `tests.toml` and documented in `.docs/hints.md`.

## Isolated Scratch Copy Verification Procedure

All regression tests are executed in an isolated temporary directory without modifying learner files or the working tree:
1. Resolve solution, test, and example file paths from `exercises/practice/variable-length-quantity/.meta/config.json`.
2. Copy the exercise directory (including dotfiles) to a temporary directory.
3. Substitute reference files (`.meta/example.c` -> `variable_length_quantity.c`, `.meta/example.h` -> `variable_length_quantity.h`) only within the temporary copy.
4. Enable all 26 test cases by stripping `TEST_IGNORE();` from `test_variable_length_quantity.c`.
5. Execute `make test` using the supplied Makefile and Unity test framework.
6. Verify exit code 0 and all 26 tests pass with 0 failures and 0 ignored.
7. Repeat with the mutated implementation to verify the child fails with non-zero exit code and reports the named failure in `test_zero`.
