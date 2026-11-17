# Maintenance notes: palindrome-products

This page records a mutation test of the maintained reference (`exercises/practice/palindrome-products/.meta/example.c`) against the exercise's existing test file.
It shows what the 13 enabled cases can and cannot tell apart, so a maintainer can see where a wrong implementation would still go green.

**Status: documentation only.**
No test, learner stub, reference or metadata file was changed.
Every mutant exists only in a temporary copy of the exercise.
Nothing here claims that the current reference is defective.

Pinned source: [`example.c` at `ffe5457`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/palindrome-products/.meta/example.c#L7).
The results below were produced by the coursework check `work/R48-T003/check.py` in the S-AI-Projects fork (the `work/` directory is evidence for the course and is not part of an upstream change).

## Documented mutant M1: numbers ending in 0 are accepted as palindromes

**Where:** `palindrome()` in `.meta/example.c`.
**Change:** one guard is deleted. The condition `if ((tail = n % 10) == 0) return false;` is replaced by the bare assignment `tail = n % 10;`, so a last digit of `0` no longer rules a number out.
Ten C tokens change; formatting-only edits are rejected by the check.

**Contract:** a palindromic number reads the same in both directions as it is written.
Numbers have no leading zeros, so apart from `0` itself, a number ending in `0` is never a palindrome (`10` is not `01`).

### Rejecting test

| | |
| --- | --- |
| Test ID (`.meta/tests.toml`) | `0853f82c-5fc4-44ae-be38-fadb2cced92d`, "find the largest palindrome from single digit factors" |
| Unity function | `test_largest_palindrome_from_single_digit_factors` |
| Input | `get_palindrome_product(1, 9)` |
| Expected | largest palindrome `9`, factors `(1, 9)` and `(3, 3)` |
| M1 returns | largest `40`; Unity reports `Expected 9 Was 40` |

Five more existing cases also reject M1: smallest from double, triple and four digit factors, largest from triple digit factors, and "smallest product does not use the smallest factor".
The case above is the one with the smallest input.

### Smallest diagnostic input

| Call | Expected (from `instructions.md`) | M1 returns |
| --- | --- | --- |
| `get_palindrome_product(2, 5)` | smallest `4` from `(2, 2)`, largest `9` from `(3, 3)` | smallest `4` from `(2, 2)`, largest `20` from `(4, 5)` |

"Smallest" means: among ranges with `1 <= min <= max <= 60`, ordered by `max` and then by width, the first range on which the reference and M1 give different answers **and** the reference agrees with an independent oracle written from the instructions.
Ranges such as `(3, 5)`, where the reference itself disagrees with the oracle (see "Observation" below), are excluded, because they would separate the two builds for the wrong reason.

## Mutants the existing cases do not reject

Three further one-line mutants of the reference pass all 13 existing cases.
Each row is a proposed case: an explicit input and the result the instructions call for.
The reference returns exactly that result in every row.

| ID | Mutation | Proposed input | Expected result | Mutant returns |
| --- | --- | --- | --- | --- |
| M2 | `0` is not a palindrome | `get_palindrome_product(0, 1)` | smallest `0` from `(0, 0)` and `(0, 1)`, largest `1` from `(1, 1)` | "no palindrome" error |
| M9 | `n <= smallest` becomes `n < smallest`, so only the first factor pair of the smallest palindrome is kept | `get_palindrome_product(12, 21)` | smallest `252` from `(12, 21)` and `(14, 18)`, largest `323` from `(17, 19)` | smallest `252` from `(12, 21)` only |
| M12 | outer loop `i <= to` becomes `i < to`, so `max * max` is never tried | `get_palindrome_product(1, 2)` | smallest `1` from `(1, 1)`, largest `4` from `(2, 2)` | largest `2` from `(1, 2)` |

What each row exercises:

- **M9** is the "return all the pairs" rule applied to the smallest palindrome. The existing cases only have more than one pair for the largest (`[1, 9]`, `9 = 1 x 9 = 3 x 3`).
- **M12** is the inclusive upper bound. No existing case has `max * max` as its answer.
- **M2** is the explicit `0 is palindrome` branch in the reference. No existing range contains `0`, and canonical data has no such case, so maintainers may prefer to leave it uncovered.

These are proposals only.
`configlet` tracks test cases by their canonical UUID, so a new case would first need to exist in the canonical data in `exercism/problem-specifications`; it should not be added by hand to the test file.

## Observation (not asserted to be a defect)

While searching for minimal inputs, the reference and an independent oracle disagreed on some ranges.
In every disagreement within the search domain the reference reports "no palindrome with factors in the range" where the oracle finds one; it never returned a different value.

| Call | Reference | Oracle (instructions read literally) |
| --- | --- | --- |
| `get_palindrome_product(1, 1)` | "no palindrome" error | smallest `1` and largest `1`, both from `(1, 1)` |
| `get_palindrome_product(24, 29)` | "no palindrome" error | smallest `676` from `(26, 26)`, largest `696` from `(24, 29)` |

Over `0 <= min <= max <= 60`, this happens for 179 of 1,891 ranges.
The branch structure suggests why: `largest` is only updated in the `else if` branch, which is reached only by a palindrome greater than the current `smallest`, so a range whose first palindrome is never exceeded leaves `largest` unset (this was not verified for every range).

The canonical data has no case with exactly one palindromic product, so the suite is silent here, and whether the reference should return a result is a maintainer decision.
It is recorded because it limited which inputs could serve as diagnostics above.
