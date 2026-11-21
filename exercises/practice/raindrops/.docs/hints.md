# Hints

## Approach Selection

There are two genuinely different ways to build `convert` in C. The reference
uses **independent divisibility checks with `strcat`**; a common alternative
is a **lookup table** (an array of `{divisor, sound}` pairs driven by a loop).
Understanding the trade-offs helps you choose the right approach for your
context and explain your decision to a reviewer.

---

### Approach 1 — Independent `if` chains (reference)

```c
if (drops % 3 == 0) strcat(result, "Pling");
if (drops % 5 == 0) strcat(result, "Plang");
if (drops % 7 == 0) strcat(result, "Plong");
if (strlen(result) == 0) snprintf(result, SIZE, "%d", drops);
```

Each divisor gets its own `if` statement. The conditions are **independent**
(not `else if`), so all matching sounds accumulate in order. The final
`strlen` guard falls back to the numeric string when nothing matched.

**When to prefer it:**
- Three rules is the entire problem; adding a fourth would just add one line.
- Control flow is explicit: a reviewer can read off every case in seconds.
- No heap allocation and no extra data structures.

**Cost:** Three remainder operations, one `strlen`, up to three `strcat` calls
(each O(current length) but the string is bounded to 15 characters).
Constant time, constant space.

---

### Approach 2 — Lookup table driven by a loop

```c
static const struct { int div; const char *sound; } rules[] = {
    {3, "Pling"}, {5, "Plang"}, {7, "Plong"},
};
for (size_t i = 0; i < sizeof rules / sizeof rules[0]; i++) {
    if (drops % rules[i].div == 0) strcat(result, rules[i].sound);
}
if (strlen(result) == 0) snprintf(result, SIZE, "%d", drops);
```

The divisor–sound pairs live in a table; the loop applies every rule without
repeating the `strcat` pattern.

**When to prefer it:**
- The number of rules is large or determined at runtime.
- You want to add, remove, or reorder rules without touching the loop body.
- A code-generation tool or configuration file produces the table.

**Cost:** Identical O(1) time and O(1) space for the fixed three-rule case.
The loop overhead is negligible at three iterations.

---

### Trade-off summary

| Property | Independent `if` | Lookup table |
|---|---|---|
| Lines of code | fewer (fixed rules) | more setup |
| Extensibility | add one `if` per rule | add one row to the table |
| Readability | every case visible | loop hides repetition |
| Memory | zero extra | small `static` array |
| Runtime cost | O(1) | O(rules) — same here |

### Worked example: input 105

105 = 3 × 5 × 7, so all three checks fire.

| Check | `drops % div` | Appended |
|---|---|---|
| `% 3` | 0 → matches | `"Pling"` |
| `% 5` | 0 → matches | `"Plang"` |
| `% 7` | 0 → matches | `"Plong"` |
| `strlen` guard | 15 ≠ 0 → skip | — |

Result: `"PlingPlangPlong"`.

Both approaches produce identical output for every input. Choose the one that
matches your team's conventions and the likely direction of change.
