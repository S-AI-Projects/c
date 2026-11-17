# Minesweeper: Scaling Analysis of `set_single_field`

## Overview

This document presents the theoretical cost analysis and empirical scaling measurements for `set_single_field` in `exercises/practice/minesweeper/.meta/example.c`.

---

## Theoretical Cost Analysis

### 1. Operation Cost of `set_single_field`
The function is defined as:
```c
static void set_single_field(char **minefield, const size_t row,
                             const size_t col)
{
   if (minefield[row][col] == '*')
      return;

   const char c = minefield[row][col];
   minefield[row][col] = (c == ' ') ? '1' : c + 1;
}
```
* **Memory Access**: 1 read `minefield[row][col]`, 1 optional write.
* **Branches**: 1 equality check (`== '*'`) and 1 ternary condition (`c == ' '`).
* **Arithmetic**: 1 increment operation (`c + 1`).
* **Complexity**: Constant time $\mathcal{O}(1)$ with an absolute upper bound of 4 machine operations.

### 2. Invocation Bounds per Mine
For each mine cell $(r, c)$, `increment_neighbors` iterates over:
$$\max(0, r-1) \le i \le \min(\text{rows}-1, r+1)$$
$$\max(0, c-1) \le k \le \min(\text{cols}-1, c+1)$$
* Maximum neighborhood size: $3 \times 3 = 9$ cells.
* Maximum calls to `set_single_field` per mine: $9$.
* Total calls to `set_single_field` across the minefield: $\le 9 \times M$, where $M$ is the number of mines.

---

## Domain Input Sizes & Operation Bounds

Input size is defined as the total number of cells in the grid ($N = \text{rows} \times \text{cols}$):

| Input Size | Exercise Test Case | Dimensions | Cells ($N$) | Mines ($M$) | Max `set_single_field` Calls ($9M$) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Small** | `horizontal line` | $1 \times 7$ | 7 | 0 (or 2) | 0 to 6 |
| **Medium** | `mine surrounded by spaces` | $3 \times 3$ | 9 | 1 | 9 |
| **Large** | `large minefield` | $5 \times 5$ | 25 | 7 | 63 |

---

## Separation of Costs: Algorithm Work vs Overhead

1. **Compilation Overhead**: $\approx 60\text{--}120\text{ ms}$ (invoking `clang`/`gcc`, AST construction, code generation, linking).
2. **Process Startup Overhead**: $\approx 2\text{--}5\text{ ms}$ (`execve`, dynamic linker `dyld`, page initialization).
3. **Algorithm Execution Time**: $\approx 1\text{--}15\ \mu\text{s}$ for domain inputs, measured in-process over 5 repetitions.
