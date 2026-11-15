## Approach: Secret Handshake Memory Allocation

- **Callee Allocation & Length Handling:** The `commands` function returns a dynamically allocated array of strings. Callers are responsible for managing/freeing the memory according to the exercise specification.
- **Bitwise Operations:** Uses bit masking (`1 << i`) to determine which handshake actions to include and reverses the array if the reverse flag bit is set.