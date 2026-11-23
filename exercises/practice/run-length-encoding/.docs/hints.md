# Hints

## General

- Run-length encoding (RLE) is a simple, lossless compression technique: consecutive identical characters (a "run") are replaced by a single count and the character itself.
- For single-character runs (count equal to 1), the count is omitted (for example, `"XYZ"` encodes to `"XYZ"`, not `"1X1Y1Z"`).
- Decoding reverses this process: numbers preceding a character determine how many times to repeat that character in the output. Characters without leading numbers appear once.
- Pay attention to memory ownership: in C, `encode` and `decode` must return dynamically allocated, null-terminated strings (`char *`) that the caller will `free()`.
- When passed an empty string (`""`), return an allocated empty string (such as via `calloc(1, 1)`) rather than a string literal, allowing the caller to safely call `free()`.

## Approach Selection

When designing an implementation in C, the primary architectural decision revolves around memory allocation strategy and input stream traversal. Two primary approaches can be considered:

### Approach 1: Two-Pass Scan with Exact Allocation (Reference Technique)

- **Data Representation**: Direct traversal using raw C string pointers without auxiliary container structures. Sizing and buffer serialization share a unified helper parameterized by a mode flag (e.g. `READ` vs `WRITE`).
- **Control Flow**:
  1. *Pass 1 (Length Calculation)*: Scan the input string to calculate the exact output byte count.
     - For encoding: calculate run lengths, and for counts $> 1$, count digits (using integer math or `log10(count) + 1` from `<math.h>`).
     - For decoding: accumulate decimal digit values to determine repetition lengths.
  2. *Allocation*: Allocate the exact buffer size needed in a single call: `malloc(length + 1)`.
  3. *Pass 2 (Serialization)*: Scan the input string a second time, writing counts and characters directly into the pre-allocated buffer, followed by the null terminator.
- **Trade-offs**:
  - *Memory Efficiency*: Minimal heap consumption ($O(M)$ where $M$ is the exact output length). Zero buffer reallocation and zero wasted capacity.
  - *Compute Cost*: Double-traversal overhead ($2N$ operations). Calling mathematical functions such as `log10` introduces floating-point operations and requires linking the math library (`-lm`).
  - *Code Coupling*: Sharing a single loop for both sizing and writing requires conditional branching (`if (mode == WRITE)`) throughout the traversal.

### Approach 2: Single-Pass Dynamic Buffer Accumulation (Streaming StringBuilder)

- **Data Representation**: A lightweight dynamic buffer structure encapsulating a pointer, length, and capacity (`typedef struct { char *data; size_t len; size_t cap; } buffer_t;`).
- **Control Flow**:
  1. *Single Pass (Streaming)*: Traverse the input string exactly once from start to finish.
  2. *Encoding Phase*: Measure each run of identical characters. If the run length $> 1$, format the count into ASCII digits using integer formatting (`snprintf` or division/modulo) and append it to the buffer, followed by the run character.
  3. *Decoding Phase*: Accumulate consecutive digit characters into an integer count. When encountering a non-digit character, append that character to the buffer repeated `count` times (or once if no digits preceded it).
  4. *Dynamic Growth*: If appending exceeds the buffer capacity, reallocate geometrically (`cap * 2`) via `realloc`.
  5. *Finalization*: Null-terminate the buffer and return `data`.
- **Trade-offs**:
  - *Execution Efficiency*: Processes the input stream in a single linear pass ($O(N)$ operations). Well-suited for streaming or pipe-like inputs where rewinding or reading twice is infeasible.
  - *No Math Library*: Avoids `log10` and `<math.h>` dependencies, using straightforward integer arithmetic.
  - *Memory Overhead*: During execution, dynamic growth may temporarily allocate up to twice the needed capacity until finalization. Requires occasional `realloc` operations.
  - *Separation of Concerns*: Clean, unidirectional control flow without dual-mode state flags.

---

### Worked Example: Encoding `"AABBBCCCC"`

1. **Initial state**: Input is `"AABBBCCCC"`.
2. **First Run (`'A'`)**:
   - Count consecutive `'A'` characters: count is $2$.
   - Since $2 > 1$, output count `'2'` followed by `'A'` $\rightarrow$ `"2A"`.
3. **Second Run (`'B'`)**:
   - Count consecutive `'B'` characters: count is $3$.
   - Output count `'3'` followed by `'B'` $\rightarrow$ `"3B"`.
4. **Third Run (`'C'`)**:
   - Count consecutive `'C'` characters: count is $4$.
   - Output count `'4'` followed by `'C'` $\rightarrow$ `"4C"`.
5. **Final Output**: `"2A3B4C"`.

*Under Approach 1*: Pass 1 determines output length is $2 + 2 + 2 = 6$ bytes, allocates 7 bytes (`malloc(7)`), and Pass 2 writes `"2A3B4C\0"`.
*Under Approach 2*: The dynamic buffer begins with an initial capacity (e.g. 16 bytes), appends `"2A"`, `"3B"`, and `"4C"` sequentially in one pass, null-terminates, and returns.

---

### Worked Example: Decoding `"12WB12W3B24WB"`

1. **Read `12` then `'W'`**: Multi-digit number `12` parsed $\rightarrow$ append 12 `'W'` characters.
2. **Read `'B'`**: No preceding digit (implicit count 1) $\rightarrow$ append 1 `'B'` character.
3. **Read `12` then `'W'`**: Append 12 `'W'` characters.
4. **Read `3` then `'B'`**: Append 3 `'B'` characters.
5. **Read `24` then `'W'`**: Multi-digit number `24` parsed $\rightarrow$ append 24 `'W'` characters.
6. **Read `'B'`**: Implicit count 1 $\rightarrow$ append 1 `'B'` character.
7. **Reconstructed Length**: $12 + 1 + 12 + 3 + 24 + 1 = 53$ characters.
