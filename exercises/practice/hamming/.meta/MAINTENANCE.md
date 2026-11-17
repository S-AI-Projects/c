# Maintenance Notes — hamming

## C-Specific Language Construct: `strlen()` on `const char *`

### Chosen construct

The reference implementation (`exercises/practice/hamming/.meta/example.c`) uses
`strlen()` on two `const char *` parameters to determine strand lengths:

```c
int compute(const char *lhs, const char *rhs) {
   int count = -1;
   if (lhs && rhs && (strlen(lhs) == strlen(rhs))) {
      count = 0;
      int length = (int)strlen(lhs);
      for (int i = 0; i < length; ++i) {
         if (lhs[i] != rhs[i]) { ++count; }
      }
   }
   return count;
}
```

There is **no explicit length parameter**. `strlen()` counts bytes up to and
including the first `'\0'` null terminator, so the function relies on the
C string convention: every string must be properly null-terminated.

### Small standalone example

```c
#include <stdio.h>
#include <string.h>

int main(void) {
    const char *a = "GAGCCTACTAACGGGAT";
    const char *b = "CATCGTAATGACGGCCT";
    printf("len(a) = %zu\n", strlen(a));  /* 17 */
    printf("len(b) = %zu\n", strlen(b));  /* 17 */
    /* Both lengths equal → Hamming distance can be computed */
    return 0;
}
```

Output:
```
len(a) = 17
len(b) = 17
```

### Contrasting pitfall input

```c
char buf[3] = {'A', 'T', 'G'};   /* NO null terminator */
compute(buf, "ATG");              /* undefined behaviour: strlen(buf)
                                     reads past the array boundary */
```

A string literal like `"ATG"` is always null-terminated by the compiler.
A `char` array initialised with explicit element values is **not**
null-terminated unless `'\0'` is included or the array has spare capacity.
Passing such an array to `compute()` causes undefined behaviour because
`strlen()` will scan beyond the array looking for `'\0'`.

**Correct versions:**
```c
char buf1[] = "ATG";          /* compiler adds '\0' — length 4 bytes */
char buf2[4] = {'A','T','G','\0'};  /* explicit null terminator */
```

### Memory ownership

Both `lhs` and `rhs` are `const char *` owned by the **caller**.
`compute()` is read-only: it never allocates, frees, or modifies the
strings. The caller is responsible for the lifetime of both buffers.

### Error-return convention

`compute()` returns `-1` for two distinct error conditions:
1. Either pointer is `NULL`.
2. The two strings have different lengths.

This is the standard C error convention: since C has no exceptions or
algebraic result types, sentinel return values (`-1`, `NULL`, negative
integers) signal errors out-of-band. Callers must check the return value
before trusting the result.

## Test-suite notes

Enabled test cases (9 total) cover:
- Both strands empty → distance 0
- Equal single-character strands → 0
- Different single-character strands → 1
- Long identical strands → 0
- Long different strands → 7
- First strand longer → -1 (error)
- Second strand longer → -1 (error)
- Empty first strand → -1 (error)
- Empty second strand → -1 (error)

Several cases were reimplemented in the C track (marked `include = false,
comment = "reimplemented"`) because the original problem-specification
cases overlap with the C-specific error-return convention.

## Regeneration

To sync test cases with upstream problem-specifications:

```bash
configlet sync --exercise hamming --update
```

Manually maintained files: `.meta/example.c`, `.meta/example.h`,
`.meta/MAINTENANCE.md`, `.meta/tests.toml` (comment keys).
