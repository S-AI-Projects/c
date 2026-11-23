# Hints

## General

- The goal of this exercise is to count the occurrences of the four DNA nucleotides (`'A'`, `'C'`, `'G'`, and `'T'`) in a given DNA strand.
- On valid input, the function must return a formatted string representing the counts in the exact format:
  `"A:<count> C:<count> G:<count> T:<count>"`
- If the input strand contains any invalid character (a character other than `'A'`, `'C'`, `'G'`, or `'T'`), the function must signal an error by returning an empty string `""`.

## C Language Constructs: Array Lengths, Null Termination, and Memory Ownership

When implementing a function in C with signature:
```c
char *count(const char *dna_strand);
```
there are three fundamental language constructs to consider:

1. **Array lengths**:
   In C, arrays decay into pointers when passed to or returned from functions; they do not carry length metadata. Many C APIs handle buffers by accepting an explicit length parameter (e.g., `size_t length`) or returning a struct containing a pointer and a length. However, the signature for `nucleotide-count` takes only `const char *dna_strand` and returns `char *`. It does not accept or return explicit array length parameters.

2. **Null termination**:
   C strings are null-terminated sequences of characters (`'\0'`). The input parameter `dna_strand` is a null-terminated string, and `count` relies on null termination to determine when the input ends (e.g. via `strlen` or iterating until `dna_strand[i] == '\0'`). The returned `char *` must also be a valid null-terminated string. When an invalid nucleotide is encountered, the function must return an empty string `""`, which in C is a buffer whose first byte is `'\0'`.

3. **Caller/callee memory ownership**:
   Because `count` returns a pointer to a string (`char *`), the lifetime and allocation of that memory are critical.
   - In C, a function cannot return a pointer to a local array allocated on the stack because local variables are deallocated when the function returns.
   - The test runner in `test_nucleotide_count.c` unconditionally calls `free(actual_count);` after evaluating every test assertion.
   - Therefore, the memory ownership contract requires the **callee** (`count`) to allocate heap memory dynamically and transfer ownership to the **caller**, which assumes responsibility for freeing it.

## Reference Implementation Construct

The maintained reference implementation in [`exercises/practice/nucleotide-count/.meta/example.c#L16`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/nucleotide-count/.meta/example.c#L16) implements this caller/callee memory ownership model using `calloc`:

```c
static const int max_length = 50;
char *count_results = calloc(1, max_length);
```

Using `calloc(1, max_length)` satisfies both memory ownership and null termination:
1. **Dynamic heap allocation**: Allocating via `calloc` ensures the buffer resides in heap memory, safely transferring ownership to the caller so that `free(actual_count)` in the test suite succeeds without undefined behavior.
2. **Zero-initialization for error handling**: `calloc` initializes all allocated bytes to zero (`0x00`). When an invalid character is encountered, `snprintf` is skipped entirely. Because every byte in `count_results` was initialized to `'\0'`, `count_results[0]` is already `'\0'`, representing the expected null-terminated empty string `""` without requiring duplicate allocation or manual error termination logic.

## Standalone Micro-Example

The following standalone C snippet reproduces the memory ownership and allocation semantics used in `example.c` on a single nucleotide summary without solving the complete exercise:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

char *format_nucleotide_summary(char nucleotide, size_t count)
{
    static const int max_length = 50;
    // Callee allocates heap memory and zero-initializes it
    char *result = calloc(1, max_length);
    if (!result) {
        return NULL;
    }

    bool valid = (nucleotide == 'A' || nucleotide == 'C' ||
                  nucleotide == 'G' || nucleotide == 'T');
    if (valid) {
        snprintf(result, max_length, "%c:%zu", nucleotide, count);
    }
    // On invalid input, calloc guarantees result is an empty string "" ('\0').
    // Ownership of the allocated heap pointer is transferred to the caller.
    return result;
}

int main(void)
{
    // Standard valid input: 'A' with count 3
    char *valid_res = format_nucleotide_summary('A', 3);
    printf("Output 1 (valid): %s\n", valid_res);
    free(valid_res); // Caller deallocates heap memory

    // Contrasting invalid input: 'X' with count 0
    char *invalid_res = format_nucleotide_summary('X', 0);
    printf("Output 2 (invalid): %s\n", invalid_res);
    free(invalid_res); // Caller deallocates heap memory

    return 0;
}
```

### Expected Output

Running this micro-example yields the following expected output:

```text
Output 1 (valid): A:3
Output 2 (invalid): 
```

- For the valid input `'A'`, `valid` is `true`, and `snprintf` writes `"A:3"`.
- For the contrasting invalid input `'X'`, `valid` is `false`, and formatting is bypassed. The zero-initialized buffer represents `""`.
- In both cases, the returned pointer is allocated on the heap, allowing the caller to safely invoke `free()`.

## Exercise-Relevant Pitfalls

When managing memory and return values in this exercise, learners commonly encounter three pitfalls:

1. **Returning a local stack buffer**:
   ```c
   char buffer[50];
   snprintf(buffer, sizeof(buffer), ...);
   return buffer; // PITFALL: Returning address of stack memory
   ```
   *Why it fails*: Automatic local arrays are deallocated as soon as the function returns. The returned pointer becomes a dangling pointer. Attempting to read it or call `free(actual_count)` triggers undefined behavior and memory crashes.

2. **Returning a string literal on error**:
   ```c
   if (invalid) {
       return ""; // PITFALL: Returning pointer to read-only static memory
   }
   ```
   *Why it fails*: The test runner in `test_strand_count` unconditionally executes `free(actual_count)`. String literals reside in read-only static storage, not on the heap. Calling `free()` on a pointer not returned by `malloc`/`calloc` aborts the program with an invalid pointer error.

3. **Using `malloc` without zero-initialization on error**:
   ```c
   char *result = malloc(max_length); // uninitialized memory
   if (!invalid_char) {
       snprintf(result, max_length, ...);
   }
   return result; // PITFALL: On error, result contains indeterminate bytes
   ```
   *Why it fails*: Unlike `calloc`, `malloc` does not zero-initialize allocated memory. If `snprintf` is skipped on invalid input, `result[0]` contains arbitrary uninitialized bytes rather than `'\0'`, causing `strcmp(actual_count, "") == 0` to fail or read uninitialized memory.

## Applicable Language References

- **ISO C99 Standard (ISO/IEC 9899:1999)**:
  - Section 7.20.3: *Memory management functions* (`calloc`, `free`, `malloc`)
  - [ISO C99 Committee Draft (WG14 N1256)](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1256.pdf)
- **cppreference**:
  - [`calloc`](https://en.cppreference.com/w/c/memory/calloc)
  - [`free`](https://en.cppreference.com/w/c/memory/free)
  - [`snprintf`](https://en.cppreference.com/w/c/io/fprintf)
- **The Open Group Base Specifications (POSIX.1-2017)**:
  - [`calloc`](https://pubs.opengroup.org/onlinepubs/9699919799/functions/calloc.html)
  - [`free`](https://pubs.opengroup.org/onlinepubs/9699919799/functions/free.html)
