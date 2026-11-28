# Hints

## General

- Variable Length Quantity (VLQ) encoding packs integers into a sequence of 7-bit bytes, output in big-endian order (most significant 7-bit chunk first).
- In the encoded output, bit 7 (the continuation bit, `0x80`) indicates whether more bytes follow for the current integer:
  - Bit 7 is **set** (`1`) on all leading bytes.
  - Bit 7 is **clear** (`0`) on the final (least significant) byte.

## Encoding

- Be careful with how your chunking loop handles an input value of `0`:
  - In VLQ, every integer must produce at least one output byte. The value `0` encodes to the single byte `0x00`.
  - If you use a pre-condition loop (such as `while (value > 0)` or `while (value)`), the loop will terminate immediately on `0` and emit zero bytes.
  - Consider using a post-condition loop (such as `do { ... } while (value);`) so that every input integer executes at least once and produces at least one 7-bit chunk.
- Small diagnostic input to verify your loop entry and continuation:
  - Input: `integers = { 0x0 }` (length 1).
  - Expected output: `{ 0x00 }` (length 1).
  - If your encoder returns length 0 or fails to write `0x00`, ensure that the loop executes for zero.
- Pay attention to multi-byte continuation conditions:
  - Since 7 bits are shifted off on each step (`value >>= 7`), another byte is required whenever any non-zero bits remain (`value > 0`).
  - Do not check `value > 0x7f` after shifting; after extracting the first 7 bits of `0x80`, the remaining value is `1` (which is `<= 0x7f`), but still requires a second byte.
  - Diagnostic input: `integers = { 0x80 }` (length 1) must produce two bytes `{ 0x81, 0x00 }`.
