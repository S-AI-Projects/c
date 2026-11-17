# Maintenance Notes — kindergarten-garden

## Maintained File Map

All paths below are relative to `exercises/practice/kindergarten-garden/`.

| Role | Path(s) | Generated? |
|---|---|---|
| Learner stub (solution) | `kindergarten_garden.c`, `kindergarten_garden.h` | No — maintained by hand |
| Test file | `test_kindergarten_garden.c` | Yes — via `configlet sync` from problem-specifications |
| Reference implementation | `.meta/example.c`, `.meta/example.h` | No — maintained by hand |
| Test case metadata | `.meta/tests.toml` | Partially — `description`/`reimplements` keys regenerated; `comment` keys preserved |
| Exercise metadata | `.meta/config.json` | No — maintained by hand |
| Build system | `makefile` | No — maintained by hand |
| Test framework | `test-framework/` | Shared — not regenerated per exercise |

## How the Runner Locates Key Files

### `tests.toml`
The Exercism track tooling (`configlet`) locates `tests.toml` by convention:
```
<exercise-root>/.meta/tests.toml
```
It is **not** discovered by filename search. The `.meta/` subdirectory is a fixed contract between `configlet` and the track repository.

### `example.c` / `example.h`
The runner identifies the reference implementation via the `files.example` array in `config.json`:
```json
{
  "files": {
    "example": [".meta/example.c", ".meta/example.h"]
  }
}
```
Paths are relative to the exercise root and must stay inside it (no `../` traversal).  
The CI substitutes `.meta/example.c` → `kindergarten_garden.c` and `.meta/example.h` → `kindergarten_garden.h` before building.

## `config.json` Files Object — Annotated

```json
{
  "files": {
    "solution": [
      "kindergarten_garden.c",    ← learner writes this
      "kindergarten_garden.h"     ← learner writes this
    ],
    "test": [
      "test_kindergarten_garden.c"  ← generated; never edit directly
    ],
    "example": [
      ".meta/example.c",          ← reference; substituted at test time
      ".meta/example.h"           ← reference header; substituted at test time
    ]
  }
}
```

**Validity rules enforced by the checker:**
1. Every path must resolve to a file that actually exists in the exercise directory.
2. No path may use `..` to escape the exercise root (parent traversal is rejected).
3. The `example` files must differ from the `solution` files (they live under `.meta/`).

## Regeneration

To sync test cases from upstream problem-specifications:

```bash
configlet sync --exercise kindergarten-garden --update
```

This regenerates `description` and `reimplements` keys in `tests.toml` and updates `test_kindergarten_garden.c`.  
Manually maintained files are **not** touched: `.meta/example.c`, `.meta/example.h`, `.meta/MAINTENANCE.md`, `.meta/config.json` (comment keys in `tests.toml` are preserved).
