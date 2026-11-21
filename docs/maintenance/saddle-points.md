# saddle-points: cost of `is_greatest_in_row`

Maintainer note for `exercises/practice/saddle-points/.meta/example.c`.
It states what the helper `is_greatest_in_row` costs, shows the evidence, and says where the conclusion stops.

## Input size

The input is a grid of tree heights with **R rows** and **C columns**.
Heights are `uint8_t` (0 to 255).
`saddle_points()` asks `is_greatest_in_row` about every cell, so a grid of R rows and C columns produces **R × C calls**.
Each call scans one row, so the length of a row (**C**) sets the cost of a call.

## Cost statement

| Quantity | Best case | Worst case |
| --- | --- | --- |
| Comparisons in one call | 1 (`matrix[row][0]` is already greater than the candidate) | C (the candidate is a row maximum, so the whole row is scanned) |
| Comparisons over a whole grid | R × (2C − 1) | R × C × C |
| Extra space | O(1) | O(1) |

- The loop stops at the first element greater than the candidate. Ties do not stop it, so every maximum of a row (including equal ones) scans the full row.
- The lower bound holds because each row has at least one cell equal to its maximum (C comparisons) and each of the other C − 1 cells needs at least one comparison.
- The call is the left operand of `&&` in `saddle_points()`, so it is never skipped. `is_least_in_column` runs only for cells that pass it.
- The cost depends on the data, not only on R and C. The two extremes are reached by the "worst" and "best" inputs below.

## Supported input sizes

- **Specification:** any rectangular grid with at least one row and one column, heights 0 to 255. The empty grid (0 rows or 0 columns) makes no call to `is_greatest_in_row`.
- **Exercise tests:** the largest grids are 3 × 3, 2 × 3, 4 × 1 and 1 × 4, plus the empty grid.
- **This study:** 256 × 256, 256 × 512 and 512 × 512. The domain is not fixed-size, so the study measures instead of tabulating a fixed bound.
- **Reference limit (from reading the code, not tested):** `is_greatest_in_row` takes its row and column indices as `int16_t`, so indices above 32767 are outside what the reference supports. In practice that means at most 32,768 rows and 32,768 columns. Nothing above 512 was run.

## Measured operations

Executed comparisons of `if (matrix[row][c] > candidate)`, counted in an instrumented copy of the reference and equal, for every input, to an independent Python model.
The counts for the whole `saddle_points()` call match the sweep, so the helper is called exactly R × C times.

Inputs (all deterministic, hashes in `work/R48-T005/evidence/inputs.json`):

- **worst:** every cell is 128, so every cell is a row maximum.
- **best:** every row is `[255, 0, 0, …, 0]`, so only column 1 is a row maximum.
- **random:** bytes from a 64-bit LCG with seed 48005, with one saddle point planted so the expected answer is never empty.

| Input | R × C | Calls (R × C) | Comparisons | Per call (min / max) | Bounds R(2C−1) … R·C² |
| --- | --- | ---: | ---: | --- | --- |
| worst | 256 × 256 | 65,536 | 16,777,216 | 256 / 256 | 130,816 … 16,777,216 |
| best | 256 × 256 | 65,536 | 130,816 | 1 / 256 | 130,816 … 16,777,216 |
| random | 256 × 256 | 65,536 | 442,736 | 1 / 256 | 130,816 … 16,777,216 |
| worst | 256 × 512 | 131,072 | 67,108,864 | 512 / 512 | 261,888 … 67,108,864 |
| best | 256 × 512 | 131,072 | 261,888 | 1 / 512 | 261,888 … 67,108,864 |
| random | 256 × 512 | 131,072 | 1,081,880 | 1 / 512 | 261,888 … 67,108,864 |
| worst | 512 × 512 | 262,144 | 134,217,728 | 512 / 512 | 523,776 … 134,217,728 |
| best | 512 × 512 | 262,144 | 523,776 | 1 / 512 | 523,776 … 134,217,728 |
| random | 512 × 512 | 262,144 | 2,144,948 | 1 / 512 | 523,776 … 134,217,728 |

What the counts show:

- The worst input hits R × C² exactly. Doubling C at fixed R (256 × 256 to 256 × 512) multiplies it by 4. Doubling R at fixed C (256 × 512 to 512 × 512) multiplies it by 2. This separates R × C² from other growth laws that would also give ×8 for 256 × 256 to 512 × 512.
- The best input hits R × (2C − 1) exactly, about 2 comparisons per call.
- The random input sits between the bounds at about 7 to 8 comparisons per call (6.8, 8.3 and 8.2 for the three sizes). That is one input per size and one data distribution; it says nothing general about typical data.

## Timings (supporting evidence only)

Timings cover **only the sweep of R × C calls to `is_greatest_in_row`**, measured inside the process with a monotonic clock, after one untimed warm-up sweep, 7 repetitions per input, median reported.
They exclude `is_least_in_column`, `add`/`realloc` and the rest of `saddle_points()`.
The function was timed through a harness that includes the reference translation unit, compiled with `-O2`.

| Input | R × C | Median ms | Range ms (min to max) | Median ns per comparison |
| --- | --- | ---: | --- | ---: |
| worst | 256 × 256 | 6.551 | 5.987 to 11.750 | 0.39 |
| best | 256 × 256 | 0.054 | 0.050 to 0.071 | 0.41 |
| random | 256 × 256 | 0.583 | 0.553 to 0.623 | 1.32 |
| worst | 256 × 512 | 23.976 | 22.387 to 28.998 | 0.36 |
| best | 256 × 512 | 0.093 | 0.092 to 0.109 | 0.35 |
| random | 256 × 512 | 1.183 | 1.171 to 1.234 | 1.09 |
| worst | 512 × 512 | 46.648 | 44.588 to 58.458 | 0.35 |
| best | 512 × 512 | 0.270 | 0.246 to 0.307 | 0.52 |
| random | 512 × 512 | 2.286 | 2.252 to 2.346 | 1.07 |

Machine for this run: Intel Xeon 2.10 GHz, 2 vCPUs (virtual machine), Linux, GCC 13.3.0, GNU Make 4.3, Unity 2.5.2, Python 3.13.
Full details are in `work/R48-T005/evidence/tool_versions.txt` and `measurements.json`.

### Algorithm work versus start-up and compilation

| Cost | Measured | What it is |
| --- | --- | --- |
| Compiling the harness | about 84 ms | Compiler time, paid once per build, not part of the algorithm |
| Process start-up floor | about 1.4 ms | A whole harness process on a 1 × 1 grid, including loading and reading the file |
| The algorithm | 0.05 ms to 46.6 ms per sweep | Only the timed region above |

For the smallest inputs the process start-up (about 1.4 ms) is larger than the algorithm itself (0.05 ms for best 256 × 256), which is why the timing is taken inside the process and not by timing the program from outside.

What the timings show, and what they do not:

- The worst-case timings move in the direction the counts predict: ×3.7 for the ×4 step and ×1.9 for the ×2 step. They do not track the counts exactly, and the spread between repetitions reaches 1.8 times the median (worst, 256 × 256).
- The cost per comparison is not constant: about 0.35 ns on the worst input and about 1.1 to 1.3 ns on the random input. A likely reason is that the early exit is harder for the processor to predict on random data, but that was not investigated. The counts, not the timings, carry the scaling argument.

## Limits of this conclusion

- The cost bounds follow from the loop structure and were confirmed on nine inputs. They were not proved by running every possible grid.
- Only `is_greatest_in_row` was costed. The cost of `saddle_points()` as a whole (including `is_least_in_column` and the `realloc` growth in `add`) was **not** timed or analysed here.
- Timings come from one virtual machine, one compiler and one optimisation level (`-O2`). The exercise's own makefile builds tests without optimisation, so a learner's build will differ in constants.
- Sizes above 512 and the `int16_t` index limit were not exercised.
- **No speedup is claimed.** No alternative implementation was written or measured.

## Reproduce

```sh
python3 work/R48-T005/check.py
```

The check works on temporary copies, passes only when every assertion holds, and rewrites `work/R48-T005/evidence/`.
Comparison counts are exactly reproducible; timings will differ from the table above on another machine.
Use `--no-evidence` to run the check without rewriting the recorded evidence.
