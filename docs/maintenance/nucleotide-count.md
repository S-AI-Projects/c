# Maintenance Guide: nucleotide-count

## Overview

The `nucleotide-count` exercise requires counting the occurrences of each nucleotide (`A`, `C`, `G`, `T`) in a DNA strand string and returning a formatted summary or an empty string on invalid characters.

## C Interface and Memory Contract

In C, the function signature is defined in `nucleotide_count.h`:
```c
char *count(const char *dna_strand);
```

### Analysis of Language Constructs

When connecting the specification to C, three core constructs arise:
1. **Array lengths**: In C, arrays do not track their length across function boundaries; strings rely on delimiters. Unlike APIs that accept a buffer and capacity or return an explicit length, `count` takes `const char *` and returns `char *`.
2. **Null termination**: C strings must terminate with `'\0'`. Both the input parameter `dna_strand` and the returned buffer use null termination to establish string boundaries. On invalid input, an empty string `""` (`'\0'`) must be returned.
3. **Caller/callee memory ownership**: Functions in C cannot return stack-allocated arrays. In `test_nucleotide_count.c`, the test framework explicitly runs `free(actual_count);` after testing the returned string. Thus, the callee `count` must allocate memory on the heap and transfer ownership to the caller.

### Maintained Reference Implementation

The reference implementation at `exercises/practice/nucleotide-count/.meta/example.c#L16` uses:
```c
static const int max_length = 50;
char *count_results = calloc(1, max_length);
```
- `calloc(1, max_length)` allocates heap memory and zero-initializes all bytes.
- On valid input, `snprintf` writes `"A:%zu C:%zu G:%zu T:%zu"` into `count_results`.
- On invalid input, `snprintf` is skipped. Because memory was zeroed by `calloc`, `count_results[0] == '\0'`, immediately representing `""` without extra allocation or error paths.
- The returned pointer is always a valid heap block that the caller can safely deallocate with `free()`.

## Canonical Test Cases and Preservation

All five canonical test cases are defined in `exercises/practice/nucleotide-count/.meta/tests.toml`:

| UUID | Description | Input | Expected Output | Ownership & Return Behavior |
| --- | --- | --- | --- | --- |
| `3e5c30a8-87e2-4845-a815-a49671ade970` | empty strand | `""` | `"A:0 C:0 G:0 T:0"` | Heap buffer allocated via `calloc`, caller frees |
| `a0ea42a6-06d9-4ac6-828c-7ccaccf98fec` | can count one nucleotide in single-character input | `"G"` | `"A:0 C:0 G:1 T:0"` | Heap buffer allocated via `calloc`, caller frees |
| `eca0d565-ed8c-43e7-9033-6cefbf5115b5` | strand with repeated nucleotide | `"GGGGGGG"` | `"A:0 C:0 G:7 T:0"` | Heap buffer allocated via `calloc`, caller frees |
| `40a45eac-c83f-4740-901a-20b22d15a39f` | strand with multiple nucleotides | `"AGCTTTTCATTCTGACTGCAACGGGCAATATGTCTCTGTGTGGATTAAAAAAAGAGTGTCTGATAGCAGC"` | `"A:20 C:12 G:17 T:21"` | Heap buffer allocated via `calloc`, caller frees |
| `b4c47851-ee9e-4b0a-be70-a86e343bd851` | strand with invalid nucleotides | `"AGXXACT"` | `""` | Zero-initialized heap buffer `""`, caller frees |

Each case preserves a `comment` key documenting the memory contract.

## Learner Pitfalls

1. **Stack Allocation**: Returning `char buffer[50]` causes undefined behavior and segmentation faults upon return or during caller `free()`.
2. **String Literal Return**: Returning `""` on invalid input violates caller ownership and causes an invalid pointer abort on `free(actual_count)`.
3. **Uninitialized `malloc`**: Using `malloc(50)` without writing `'\0'` on error leaves indeterminate bytes, failing `strcmp(actual_count, "") == 0`.
