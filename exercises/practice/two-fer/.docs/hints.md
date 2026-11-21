# Hints

Two-fer builds a sentence of the form ``"One for X, one for me."``.

## Selected cases

| case | input `name` | returned string |
|---|---|---|
| no name given | `NULL` | ``One for you, one for me.`` |
| a name given | `"Alice"` | ``One for Alice, one for me.`` |
| another name given | `"Bob"` | ``One for Bob, one for me.`` |

## C representation

The function signature is:

```c
void two_fer(char *buffer, const char *name);
```

- `buffer` is the output buffer you write into.
- `name` is the person's name, or `NULL` when it is unknown.
- Use `snprintf(buffer, BUFFER_SIZE, "One for %s, one for me.", ...)` with
  `BUFFER_SIZE` of 100.

When `name` is `NULL`, substitute the literal `"you"` so the result reads
``One for you, one for me.``. When a name is given, print it verbatim.

## Ordering / error requirements

The specification only defines behaviour for a known name versus an unknown
(`NULL`) name. A `NULL` buffer, an empty string `""`, or a name longer than
the buffer are **outside the exercise contract** and left unspecified — the
reference does not impose any extra exception rule, coercion, or ordering
requirement beyond what the source specification states.
