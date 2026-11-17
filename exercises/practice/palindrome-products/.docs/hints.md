# Hints

## Numbers that end in zero

A palindromic number reads the same in both directions _as it is written_.
Numbers are not written with leading zeros, so `10` is not the mirror image of `01`.
Apart from `0` itself, a number that ends in `0` can never be a palindrome.

If your solution treats products such as `10` or `20` as palindromes, the largest palindrome it reports will be too big.

## A small case to debug with

When a result looks wrong for a big range, shrink the range until you can check every product by hand.
Take `get_palindrome_product(2, 5)`.

The products of two numbers from `2` to `5` are `4`, `6`, `8`, `9`, `10`, `12`, `15`, `16`, `20` and `25`.
Only `4`, `6`, `8` and `9` are palindromes, so the smallest palindrome is `4` (factors `2` and `2`) and the largest is `9` (factors `3` and `3`).
A solution that accepts `10` or `20` as a palindrome reports `20` (factors `4` and `5`) as the largest instead.
