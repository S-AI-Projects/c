# Pascal's Triangle: Mutation Analysis & Maintenance Guide

## Overview

This document documents the contract for `pascals-triangle`, analyzes deliberate mutation behavior against the test suite, and proposes test cases for `free_triangle`.

## Pascal's Triangle Contract

1. **`uint8_t **create_triangle(size_t rows)`**:
   - For `rows == 0`: The C track specification requires returning a valid allocated $1 \times 1$ array containing `{ { 0 } }` rather than `NULL`.
   - For `rows > 0`: Returns a dynamic 2D array of `rows` rows where row $i$ has $i+1$ valid values computed according to Pascal's triangle binomial coefficients, with remaining elements in the allocated row padded or zeroed.
   - On allocation failure: Returns `NULL` and frees any previously allocated rows.
   - **Smallest valid input**: `rows = 0`.

2. **`void free_triangle(uint8_t **triangle, size_t rows)`**:
   - Frees every row pointer `triangle[i]` for $0 \le i < \text{rows}$.
   - Frees the outer pointer array `triangle`.

---

## Mutation Analysis

### 1. Boundary & Condition Mutation (create_triangle)
- **Mutant**: Changing the `rows == 0` boundary to return `NULL` instead of allocating `{ { 0 } }`.
- **Outcome**: Detected immediately by existing test `test_no_rows` (UUID `9920ce55-9629-46d5-85d6-4201f4a4234d`).
- **Assertion failure**: `test_no_rows: Expected TRUE Was FALSE`.
- **Diagnostic Input**: `rows = 0` (the smallest input allowed by specification).

### 2. Deliberate Mutant of `free_triangle`
- **Mutant**: Omitting the deallocation loop:
  ```c
  void free_triangle(uint8_t **triangle, size_t rows)
  {
     // Deliberate mutant: omit row freeing (memory leak)
     // for (size_t i = 0; i < rows; i++) free(triangle[i]);
     free(triangle);
  }
  ```
- **Why the existing suite misses it**:
  The existing test executable (`tests.out` compiled via `make test`) only checks value equality via `check_triangle`. It does not monitor heap allocation statistics, pointer ownership, or memory leaks unless compiled with AddressSanitizer under `make memcheck`.

---

## Proposed Test Case for `free_triangle`

To ensure full contract coverage without assuming the current implementation is buggy, the following test case is proposed:

### Case: `test_free_triangle_contract_and_null_safety`
- **Explicit Input**:
  1. `actual = create_triangle(1); free_triangle(actual, 1);`
  2. `free_triangle(NULL, 0);`
- **Expected Result**:
  1. All heap blocks allocated by `create_triangle` (both the outer pointer array and inner row arrays) are cleanly freed with zero memory leaks.
  2. Calling `free_triangle(NULL, 0)` must not dereference `NULL` and must safely return.
