# R48-T008 Maintenance Note — queen-attack metadata mapping

## Purpose
Make `exercises/practice/queen-attack/.meta/config.json` understandable and verifiable: every file declared in its `files` object must resolve inside the exercise, and the runner's discovery of `.meta/tests.toml` and `.meta/example.c` is explained below.

## Real maintained paths (exercises/practice/queen-attack/)

| Role | Path | Notes |
|------|------|-------|
| Metadata | `.meta/config.json` | Declares the `files` object (solution / test / example) plus blurb/source. |
| Solution (learner stub) | `queen_attack.c` | Stub: only `#include "queen_attack.h"`. Left **unsolved** and never modified by the check. |
| Solution header | `queen_attack.h` | Declares `attack_status_t`, `position_t`, `can_attack()`. |
| Test | `test_queen_attack.c` | Unity test file; most cases `TEST_IGNORE()`d, one enabled. |
| Test metadata | `.meta/tests.toml` | 13 cases; first 5 have `include = false` (excluded property tests), remaining 8 are intended/enabled. Found via `files.test` → test file; the toml itself is the per-exercise test catalogue the runner consults to enable/gate cases. |
| Reference implementation | `.meta/example.c` | Full correct `can_attack()`. Found via `files.example[0]` = `.meta/example.c`. |
| Build recipe | `makefile` | `test` target builds `test-framework/unity.c ./*.c` into `tests.out` and runs it. |
| Documentation | `.docs/instructions.md` | Exercise instructions. |

## How the runner finds tests.toml and example.c
The runner parses `.meta/config.json` and reads its `files` object (never by guessing filenames):
- `files.test[0]` → `test_queen_attack.c` (the Unity test file compiled with the solution).
- `files.example[0]` → `.meta/example.c` (the reference implementation).
- `.meta/tests.toml` is the test catalogue co-located in `.meta/`; the runner reads it to determine which cases are intended (`include != false`) and to gate/comment cases (comments live in a `"comment"` key).

## Generated artifacts vs source vs third-party framework
- **Generated artifacts (build outputs, regenerated every run, NOT source):** `tests.out`, `memcheck.out`, `*.o`, `*.out.dSYM`. Produced by `make test` / `make memcheck` in a scratch copy; never committed.
- **Source (maintained):** `queen_attack.c`, `queen_attack.h`, `test_queen_attack.c`, `makefile`, `.meta/config.json`, `.meta/tests.toml`, `.meta/example.c`, `.docs/instructions.md`.
- **Third-party framework (vendored, not generated, not modified):** `test-framework/{unity.c,unity.h,unity_internals.h}` (Unity v2.5.2). Linked into the test build; treated as a dependency, not as exercise output.

## Check summary (work/R48-T008/check.py)
- Real `config.json`: all 4 declared files resolve inside the exercise → PASS.
- 3 invalid fixtures each fail for the intended reason → PASS:
  - `missing-reference`: `.meta/nonexistent.c` declared under `files.example` does not exist.
  - `missing-test`: `nonexistent.c` declared under `files.test` does not exist.
  - `outside-exercise`: `../outside.c` declared under `files.solution` uses parent traversal / resolves outside the exercise.
- Behavioural run: reference (`.meta/example.c`) substituted **only in a temp scratch copy** (working tree untouched), 8 intended cases enabled, `make test` run → 13 tests, 0 failures, 4 ignored, child exit 0 → PASS. The learner stub remains unsolved.

## Files in work/R48-T008/
- `check.py` — the check (Python subprocess + temp dir; never rewrites the working tree).
- `fixtures/{missing-reference,missing-test,outside-exercise}/config.json` — invalid metadata fixtures.
- `inputs/{config.json,tests.toml}` — snapshots of the real metadata used as inputs.
- `results/check_report.txt` — expected vs actual results.
- `results/behavioural_run.log` — compiler + Unity output from the scratch run.
- `versions.txt` — tool versions (python3, make, cc).
- `maintenance.md` — this document.
