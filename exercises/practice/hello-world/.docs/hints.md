# Hints

## Contract & Selected Cases

`hello-world` is the introductory exercise on the C track. Its objective is to implement a function that produces the classic greeting.

### Function Signature

```c
const char *hello(void);
```

- **Input parameter**: `void` — the function takes no arguments.
- **Return value**: `const char *` — a pointer to a null-terminated sequence of characters.

---

## Input / Output Walkthrough

The canonical specification defines exactly one test case (`Say Hi!`, UUID `af9ffe10-dc13-42d8-a742-e7bdafac449d`):

| Case | Canonical Description | Input | Expected Output |
|---|---|---|---|
| `af9ffe10-dc13-42d8-a742-e7bdafac449d` | Say Hi! | `(void)` | `"Hello, World!"` |

### C Representation

1. **String Literal**:
   In C, returning `"Hello, World!"` produces a pointer to a statically allocated, null-terminated character array:
   ```c
   const char *hello(void)
   {
      return "Hello, World!";
   }
   ```
2. **Storage Duration & Memory Lifetime**:
   - The string literal `"Hello, World!"` has **static storage duration**. Its lifetime extends for the entire execution of the program.
   - It is stored in implementation-defined static storage (typically the read-only `.rodata` segment).
   - The returned pointer is always valid; callers do not need to manage its lifetime.
3. **The `const` Qualifier**:
   - The return type is `const char *`, indicating that the referenced string must not be modified.
   - Attempting to overwrite characters through this pointer violates `const`-correctness and triggers undefined behavior (typically a segmentation fault if `.rodata` is write-protected).

---

## Decision Table

| Input Condition | Contract Status | Expected Result / Behavior | Rationale |
|---|---|---|---|
| Invoke `hello()` | In-contract (specified) | Returns `"Hello, World!"` | Satisfies canonical specification. Null-terminated ASCII string of length 13. |
| Concurrent calls across threads | In-contract (specified) | Returns `"Hello, World!"` | Pure, stateless function; reentrant and thread-safe. |
| Multiple repeated invocations | In-contract (specified) | Returns identical string | Idempotent; no state accumulation or mutation. |
| Attempting to mutate returned buffer (`s[0] = 'h'`) | Outside contract (unspecified) | Undefined behavior | String literal occupies read-only memory; `const` prohibits modification. |
| Attempting to `free((void *)hello())` | Outside contract (unspecified) | Undefined behavior | Pointer was not allocated via `malloc`/`calloc`/`realloc`. |
| Calling with non-void arguments | Outside contract (unspecified) | Compilation error | Prototype is strictly `hello(void)`. |

---

## Specified Behavior vs. Outside the Contract

- **What is specified**:
  - The function must return a pointer to the exact string `"Hello, World!"` (including capitalization, comma, space, and exclamation point).
  - The return type is `const char *`.

- **What is outside the contract (left unspecified)**:
  - **No I/O or printing**: The exercise does not ask to print to standard output (`stdout`) or log via `printf`. It only inspects the returned pointer value.
  - **No dynamic allocation**: No buffer is provided by the caller, and no heap allocation is expected or permitted to be leaked.
  - **No locale / internationalization**: The greeting is fixed in English ASCII; no character encoding conversions or locale adaptations are performed.
  - **No error handling or coercion**: The function cannot fail under valid invocation; no error codes, `errno` settings, or fallback sentinels exist in the contract.
