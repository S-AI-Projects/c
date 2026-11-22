# Darts: Canonical Case Decisions & Maintenance Guide

## Overview

This maintenance guide documents and explains the canonical-case decisions, language-specific considerations, and verification procedures for `exercises/practice/darts` in the Exercism C track (Task R48-T041).

- **Exercise**: `exercises/practice/darts`
- **Pinned Reference Implementation**: [`exercises/practice/darts/.meta/example.c#L14` at `ffe5457`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/darts/.meta/example.c#L14) (`static float distance_from_origin(coordinate_t point)`)
- **Primary Goal**: Review all 13 canonical test cases in `exercises/practice/darts/.meta/tests.toml`, document the rationale for UUIDs `9033f731-0a3a-4d9c-b1c0-34a1c8362afb`, `4c9f6ff4-c489-45fd-be8a-1fcb08b4d0ba`, and `14378687-ee58-4c9b-a323-b089d5274be8` against C language operations and existing tests, preserve metadata across `configlet sync`, and verify reference test execution in an isolated scratch environment.

---

## Canonical Data Source

The canonical test suite originates from Exercism's `problem-specifications` repository:
- **Canonical data file**: `exercises/darts/canonical-data.json`
- **Track metadata**: `exercises/practice/darts/.meta/tests.toml`
- **Exercise configuration**: `exercises/practice/darts/.meta/config.json`
- **Global configuration**: `config.json`

### Maintained vs Generated Files

| File | Maintenance Model | Purpose |
| :--- | :--- | :--- |
| `exercises/practice/darts/.meta/tests.toml` | Tool-synchronized via `configlet` | Records canonical test inclusions, UUIDs, descriptions, and comments |
| `exercises/practice/darts/test_darts.c` | Hand-maintained | C test suite implementing canonical test cases using Unity |
| `exercises/practice/darts/darts.h` & `darts.c` | Hand-maintained | Learner starter files and stubs (must remain unsolved) |
| `exercises/practice/darts/.meta/example.h` & `example.c` | Hand-maintained | Reference implementation used for verification |
| `exercises/practice/darts/.meta/config.json` | Hand-maintained | Declares solution, test, and reference example files |
| `exercises/practice/darts/.docs/instructions.md` | Synchronized / Track docs | Problem description and rules |

*Note on test generator*: The C track does not utilize per-exercise Jinja templates for code generation. Test files (`test_darts.c`) are hand-crafted and maintained according to canonical specifications.

---

## Reproduction and Synchronization Commands

To synchronize canonical test cases and verify metadata integrity:

```bash
# 1. Fetch configlet if not present
./bin/fetch-configlet

# 2. Check sync status against canonical specifications
./bin/configlet sync --exercise darts --tests include --offline

# 3. Update tests.toml while preserving comment keys
./bin/configlet sync --exercise darts --tests include --update --yes --offline
```

Configlet preserves manually added keys such as `comment` in `tests.toml`.

---

## Canonical Test Cases & Mapping Table

All 13 canonical test cases are supported and included (0 exclusions). The target layout consists of concentric circles centered at origin `(0.0F, 0.0F)`:
- Inner circle: Radius $R \le 1.0$ (Score: 10)
- Middle circle: Radius $1.0 < R \le 5.0$ (Score: 5)
- Outer circle: Radius $5.0 < R \le 10.0$ (Score: 1)
- Off board / Miss: Radius $R > 10.0$ (Score: 0)

| # | UUID | Canonical Description | C Test Function Name | Coordinates `(x, y)` | Expected Score | C Operations & Evaluation Rationale | Status |
|:-:|:-----|:----------------------|:---------------------|:---------------------|:--------------:|:------------------------------------|:------:|
| 1 | `9033f731-0a3a-4d9c-b1c0-34a1c8362afb` | Missed target | `test_missed_target` | `(-9.0F, 9.0F)` | 0 | `sqrt(162.0F) ≈ 12.73 > 10.0F`; exceeds outer radius, falls through to `OFF_BOARD_SCORE` (0) | Included |
| 2 | `4c9f6ff4-c489-45fd-be8a-1fcb08b4d0ba` | On the outer circle | `test_on_the_outer_circle` | `(0.0F, 10.0F)` | 1 | `sqrt(100.0F) == 10.0F`; satisfies `distance <= OUTER_CIRCLE_RADIUS` (`10.0F <= 10.0F`) | Included |
| 3 | `14378687-ee58-4c9b-a323-b089d5274be8` | On the middle circle | `test_on_the_middle_circle` | `(-5.0F, 0.0F)` | 5 | `sqrt(25.0F) == 5.0F`; squarings eliminate sign, satisfies `distance <= MIDDLE_CIRCLE_RADIUS` | Included |
| 4 | `849e2e63-85bd-4fed-bc3b-781ae962e2c9` | On the inner circle | `test_on_the_inner_circle` | `(0.0F, -1.0F)` | 10 | `sqrt(1.0F) == 1.0F`; satisfies `distance <= INNER_CIRCLE_RADIUS` (`1.0F <= 1.0F`) | Included |
| 5 | `1c5ffd9f-ea66-462f-9f06-a1303de5a226` | Exactly on centre | `test_exactly_on_center` | `(0.0F, 0.0F)` | 10 | `sqrt(0.0F) == 0.0F`; center point bullseye, satisfies `distance <= INNER_CIRCLE_RADIUS` | Included |
| 6 | `b65abce3-a679-4550-8115-4b74bda06088` | Near the centre | `test_near_the_center` | `(-0.1F, -0.1F)` | 10 | `sqrt(0.02F) ≈ 0.1414F <= 1.0F`; strictly within inner circle | Included |
| 7 | `66c29c1d-44f5-40cf-9927-e09a1305b399` | Just within the inner circle | `test_just_within_the_inner_circle` | `(0.7F, 0.7F)` | 10 | `sqrt(0.98F) ≈ 0.9899F <= 1.0F`; near boundary inside inner circle | Included |
| 8 | `d1012f63-c97c-4394-b944-7beb3d0b141a` | Just outside the inner circle | `test_just_outside_the_inner_circle` | `(0.8F, -0.8F)` | 5 | `sqrt(1.28F) ≈ 1.1314F > 1.0F && <= 5.0F`; enters middle circle band | Included |
| 9 | `ab2b5666-b0b4-49c3-9b27-205e790ed945` | Just within the middle circle | `test_just_within_the_middle_circle` | `(-3.5F, 3.5F)` | 5 | `sqrt(24.5F) ≈ 4.9497F <= 5.0F`; near boundary inside middle circle | Included |
| 10 | `70f1424e-d690-4860-8caf-9740a52c0161` | Just outside the middle circle | `test_just_outside_the_middle_circle` | `(-3.6F, -3.6F)` | 1 | `sqrt(25.92F) ≈ 5.0912F > 5.0F && <= 10.0F`; enters outer circle band | Included |
| 11 | `a7dbf8db-419c-4712-8a7f-67602b69b293` | Just within the outer circle | `test_just_within_the_outer_circle` | `(-7.0F, 7.0F)` | 1 | `sqrt(98.0F) ≈ 9.8995F <= 10.0F`; near boundary inside outer circle | Included |
| 12 | `e0f39315-9f9a-4546-96e4-a9475b885aa7` | Just outside the outer circle | `test_just_outside_the_outer_circle` | `(7.1F, -7.1F)` | 0 | `sqrt(100.82F) ≈ 10.0409F > 10.0F`; misses board, falls through to 0 | Included |
| 13 | `045d7d18-d863-4229-818e-b50828c75d19` | Asymmetric position between inner and middle | `test_asymmetric_position_between_the_inner_and_middle_circles` | `(-0.5F, -4.0F)` | 5 | `sqrt(16.25F) ≈ 4.0311F > 1.0F && <= 5.0F`; asymmetric middle circle test | Included |

---

## Detailed Rationale for Selected UUIDs

### 1. UUID `9033f731-0a3a-4d9c-b1c0-34a1c8362afb` ("Missed target")
- **Test Function**: `test_missed_target`
- **Coordinates**: `landing_position = { -9.0F, 9.0F }`
- **Expected Return Value**: `0` (uint8_t)
- **C Operation & Language Analysis**:
  - Distance computation: In `example.c#L14-L20`, the helper `distance_from_origin` computes:
    $$\text{distance} = \sqrt{x^2 + y^2} = \sqrt{(-9.0\text{F})^2 + (9.0\text{F})^2} = \sqrt{81.0\text{F} + 81.0\text{F}} = \sqrt{162.0\text{F}} \approx 12.727922\text{F}$$
  - The C `sqrt()` function from `<math.h>` (linked via `LIBS = -lm` in `makefile`) operates on standard IEEE-754 single-precision floating-point numbers without precision issues or overflow.
  - Scoring control flow evaluates:
    1. `landingPositionDistanceFromOrigin <= INNER_CIRCLE_RADIUS` ($12.73 \le 1.0 \implies \text{false}$)
    2. `landingPositionDistanceFromOrigin <= MIDDLE_CIRCLE_RADIUS` ($12.73 \le 5.0 \implies \text{false}$)
    3. `landingPositionDistanceFromOrigin <= OUTER_CIRCLE_RADIUS` ($12.73 \le 10.0 \implies \text{false}$)
  - As all conditions evaluate to false, execution falls through and returns the initialized `OFF_BOARD_SCORE = 0`.
- **Inclusion Decision**: Fully supported in C; no track or language limitation exists. Retained as included.

### 2. UUID `4c9f6ff4-c489-45fd-be8a-1fcb08b4d0ba` ("On the outer circle")
- **Test Function**: `test_on_the_outer_circle`
- **Coordinates**: `landing_position = { 0.0F, 10.0F }`
- **Expected Return Value**: `1` (uint8_t)
- **C Operation & Language Analysis**:
  - Distance computation:
    $$\text{distance} = \sqrt{0.0\text{F}^2 + 10.0\text{F}^2} = \sqrt{100.0\text{F}} = 10.0\text{F}$$
  - Coordinates aligned with axes having integer values are representable with exact precision in IEEE-754 single-precision `float` (sign bit: 0, exponent: 130, mantissa: 0.25).
  - Scoring comparison:
    - `landingPositionDistanceFromOrigin <= OUTER_CIRCLE_RADIUS` evaluates `10.0F <= 10.0F`, which is strictly `true` due to the inclusive relational operator `<=`.
    - Returns `OUTER_CIRCLE_SCORE = 1`.
  - This case validates that boundary darts touching the perimeter line of radius 10 are counted as inside the target rather than misses.
- **Inclusion Decision**: Fully supported; verifies inclusive `<=` boundary semantics in C floating-point comparisons. Retained as included.

### 3. UUID `14378687-ee58-4c9b-a323-b089d5274be8` ("On the middle circle")
- **Test Function**: `test_on_the_middle_circle`
- **Coordinates**: `landing_position = { -5.0F, 0.0F }`
- **Expected Return Value**: `5` (uint8_t)
- **C Operation & Language Analysis**:
  - Distance computation:
    $$\text{distance} = \sqrt{(-5.0\text{F})^2 + 0.0\text{F}^2} = \sqrt{25.0\text{F}} = 5.0\text{F}$$
  - C arithmetic handles negative coordinate inputs through squaring `point.x * point.x`, properly discarding the negative sign without requiring explicit `fabs()` calls.
  - Scoring comparison:
    - `landingPositionDistanceFromOrigin <= INNER_CIRCLE_RADIUS` ($5.0\text{F} \le 1.0\text{F} \implies \text{false}$)
    - `landingPositionDistanceFromOrigin <= MIDDLE_CIRCLE_RADIUS` ($5.0\text{F} \le 5.0\text{F} \implies \text{true}$)
    - Returns `MIDDLE_CIRCLE_SCORE = 5`.
  - Verifies quadrant symmetry and inclusive boundary handling at the middle ring.
- **Inclusion Decision**: Fully supported; validates negative coordinate squaring and middle-circle boundary inclusivity. Retained as included.

---

## Technical Considerations in C Implementation

1. **Floating Point Precision**: The coordinates use `float` (32-bit single precision) packed into `coordinate_t` defined in `darts.h`:
   ```c
   typedef struct {
       float x, y;
   } coordinate_t;
   ```
2. **Euclidean Distance Alternatives**: The reference implementation uses `sqrt(x*x + y*y)`. An alternative standard library approach is `hypot(x, y)` from `<math.h>`, which guards against intermediate overflow/underflow for extreme coordinates. In this exercise, coordinates remain well within $10.0$, making both forms equivalent and safe.
3. **Boundary Inclusivity**: The rules specify that landing *on* the circle earns points for that circle. The relational operator `<=` correctly captures points on the boundary.

---

## Verification Architecture & Test Execution

The verification check (`work/R48-T041/check.py` and `tools/course_checks/r48-t041.py`) performs:
1. **Repository Root Discovery**: Resolves the repository tree and exercise metadata.
2. **Learner Stub Immutability**: Asserts that `exercises/practice/darts/darts.c` and `darts.h` are unchanged and unsolved.
3. **Metadata & Rationale Validation**:
   - Parses `exercises/practice/darts/.meta/tests.toml` using Python `tomllib`.
   - Asserts all 13 canonical cases are present with 0 exclusions.
   - Asserts that UUIDs `9033f731-0a3a-4d9c-b1c0-34a1c8362afb`, `4c9f6ff4-c489-45fd-be8a-1fcb08b4d0ba`, and `14378687-ee58-4c9b-a323-b089d5274be8` have explicit rationales citing test names and C operations.
4. **Key Preservation Check**: Confirms comment keys survive `configlet sync`.
5. **Isolated Scratch Copy Execution**:
   - Copies the exercise into a temporary directory using Python `tempfile`.
   - Substitutes reference files (`.meta/example.c`, `.meta/example.h`) only in the temporary scratch directory.
   - Strips `TEST_IGNORE();` from the temporary copy of `test_darts.c` to enable all 13 test cases.
   - Executes `make test` using Unity.
   - Verifies 0 non-zero exit codes, 13 test executions, 0 failures, and 0 ignored tests.
   - Asserts zero mutations occurred in the working tree.
6. **Evidence Persistence**: Records execution logs, tool versions, inputs, and expected vs actual results in `work/R48-T041/`.

---

## Task Verification Status

- [x] Canonical test cases reviewed: 13 included, 0 excluded.
- [x] Rationales documented for UUIDs `9033f731-0a3a-4d9c-b1c0-34a1c8362afb`, `4c9f6ff4-c489-45fd-be8a-1fcb08b4d0ba`, and `14378687-ee58-4c9b-a323-b089d5274be8`.
- [x] TOML comments and `comment` keys added to `exercises/practice/darts/.meta/tests.toml`.
- [x] Automated check `work/R48-T041/check.py` executed successfully.
- [x] Learner stub remains unsolved in working tree.
- [x] Reference implementation passes all 13 test cases in scratch copy.
