# Trace of sum_of_squares (current reference)

Local state that determines the result: loop variable `n` and accumulator `total`.
After the iteration for `n = k`, `total == sum_of_squares(k)` (measured from the
compiled reference, not modelled). The baseline's extra `i = 0` pass added 0.

## sum_of_squares(1) = 1

| n | n*n | total after this iteration |
|---|-----|-----------------------------|
| 1 | 1 | 1 |

## sum_of_squares(5) = 55

| n | n*n | total after this iteration |
|---|-----|-----------------------------|
| 1 | 1 | 1 |
| 2 | 4 | 5 |
| 3 | 9 | 14 |
| 4 | 16 | 30 |
| 5 | 25 | 55 |

## sum_of_squares(100) = 338350

| n | n*n | total after this iteration |
|---|-----|-----------------------------|
| 1 | 1 | 1 |
| 2 | 4 | 5 |
| 3 | 9 | 14 |
| 4 | 16 | 30 |
| 5 | 25 | 55 |
| ... | ... | ... |
| 98 | 9604 | 318549 |
| 99 | 9801 | 328350 |
| 100 | 10000 | 338350 |
