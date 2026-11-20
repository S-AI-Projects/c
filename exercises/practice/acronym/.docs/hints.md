# Hints

## C

The construct to focus on in this exercise is **null termination** (`'\0'`).

In the reference implementation (`.meta/example.c`), `count_words` walks the phrase with:

```c
for (size_t i = 1; phrase[i] != '\0'; ++i)
   if (is_first_letter_of_word(phrase[i], phrase[i - 1]))
      ++count;
```

`is_first_letter_of_word` inspects `phrase[i]` and `phrase[i - 1]`, so it is only safe because the loop stops at the terminating `'\0'`. The null terminator is what bounds the array scan and keeps the helper from reading past the end of the string. `abbreviate` also reserves room for the result's terminator with `calloc(count_words(phrase) + 1, sizeof phrase[0])`.

### Executable micro-example

```c
#include <stdio.h>
#include <string.h>

int main(void)
{
   char term[] = "PNG";
   printf("terminated len=%zu sizeof=%zu scan=PNG\n", strlen(term), sizeof(term));

   char noterm[] = {'P', 'N', 'G'};
   printf("non-terminated sizeof=%zu pitfall=unbounded_scan_reads_past_end\n", sizeof(noterm));
   return 0;
}
```

Compile and run:

```sh
cc -std=c99 -o micro_example micro_example.c
./micro_example
```

Expected output:

```
terminated len=3 sizeof=4 scan=PNG
non-terminated sizeof=3 pitfall=unbounded_scan_reads_past_end
```

### Pitfall

A buffer such as `char noterm[] = {'P', 'N', 'G'};` has `sizeof == 3` and **no** `'\0'` slot. An unbounded scan (for example `strlen(noterm)` or a loop without a `'\0'` guard) reads past the end of the array — undefined behavior / a buffer overread. The terminated array `char term[] = "PNG";` has `sizeof == 4` (the extra byte is `'\0'`), so a scan guarded by `phrase[i] != '\0'` stops cleanly after "PNG".

That is exactly why `count_words` (and `abbreviate`) bound their scans with `'\0'`: it makes `is_first_letter_of_word(phrase[i], phrase[i - 1])` safe.

### Language reference

Null-terminated byte strings: https://en.cppreference.com/c/string/byte (see `strlen`, and the NTBS requirements in ISO/IEC 9899 §7.1.1 / §7.21).
