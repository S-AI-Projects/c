# R48-T002 — Phase 1 findings (Wordy test-generation reconnaissance)

Recorded **before** any checker code was written. Every claim below was verified
against the actual source or by running the real tool, not taken from documentation.

## Headline

**This track has no test generator.** There is no per-exercise template, no
`bin/generate-*` script and no track-level generation command.

| Artifact | Status | Evidence |
| --- | --- | --- |
| `test_wordy.c` | **Hand-written.** Not generated. | `docs/CONTRIBUTING.md`: "Tests should be written to satisfy `canonical-data.json`". `bin/` holds only `check-include-guards`, `check-unitybegin`, `fetch-configlet`, `verify-exercises-in-docker`, `verify-unity-version`. |
| `.meta/tests.toml` | **The only generated file.** Written by `configlet sync`. Its header says "auto-generated". | configlet `src/sync/exercises.nim` (`toToml`, `writeTestsToml`). |
| Everything else in the exercise | Maintained manually (stub `wordy.c`/`wordy.h`, `makefile`, `.meta/example.*`, `.meta/config.json`, vendored `test-framework/`). `.docs/instructions.md` is synced by `configlet sync --docs`. | — |

Consequence for the task constraints: "do not hand-edit generated test files"
applies to `.meta/tests.toml`. The `test_wordy.c` file is not generated, but it
was not modified either.

## Answers to the Phase 1 questions

**Authoritative test source.** `exercises/wordy/canonical-data.json` in
`exercism/problem-specifications` defines the set of cases. The track records
which of them it implements in `.meta/tests.toml` (`include = false` marks a
deliberate exclusion). The executable tests live in the hand-written `test_wordy.c`.

**Command that generates Wordy's tests.** None exists. The nearest real command is
the one that regenerates `tests.toml`:

```
configlet --track-dir <track> sync --exercise wordy --offline --update --tests include
```

**What CI actually runs.** `.github/workflows/run-configlet-sync.yml` (monthly cron)
calls `exercism/github-actions/.github/workflows/configlet-sync.yml@main`
(read at commit `0917b77`). Its test job runs `./bin/configlet sync --tests` in
**check mode** (no `-u`) and opens an issue when the exit code is non-zero. It never
regenerates `tests.toml`. `configlet.yml` runs `configlet lint`. `test.yml` runs `make`
at the repo root. Those sync jobs are gated on `github.repository_owner == 'exercism'`,
so they do not run on this fork.

**Supported flags** (from `configlet --help`, version 4.0.3, matching `src/cli.nim`):

- Global: `-t, --track-dir <dir>` (hyphenated), `-v, --verbosity`.
- `sync`: `-e, --exercise <slug>`, `-o, --offline`, `-u, --update`, `-y, --yes`,
  `--docs`, `--filepaths`, `--metadata`, `--tests [include|exclude|choose]`.
- There is **no** option to point at a problem-specifications directory. The location
  is `getCacheDir()/exercism/configlet/problem-specifications` (`XDG_CACHE_HOME`
  honoured on Linux). Offline mode requires a full, non-shallow, clean clone whose
  root commit is `8ba81069…` and whose `HEAD` is an ancestor of `main`.
- `configlet sync` only rewrites `tests.toml` when the exercise is out of sync
  (`syncIfNeeded`). On an in-sync exercise it is a no-op.

**Generated timestamps.** None. `toToml` emits a static header, and a grep of
`src/sync/*.nim` finds no clock or date use. Confirmed empirically (see Phase 2
evidence). **No timestamp normalization is therefore applied.**

**Unity build and execution.** The exercise `makefile` compiles
`test-framework/unity.c ./*.c` with `-std=c99 -Wall -Wextra -pedantic -Werror
-Wmissing-declarations` into `tests.out` and runs it; `make memcheck` repeats with
AddressSanitizer. The root `makefile` builds each exercise in `build/` using
`.meta/example.*` in place of the stub and runs both targets. Unity exits non-zero when
a test fails.

**Disabled and excluded cases.** Two separate mechanisms:

1. `tests.toml`: `include = false` for a canonical case the track deliberately skips.
   configlet preserves it and treats the exercise as in sync.
2. `test_wordy.c`: `TEST_IGNORE();` skips a test at runtime. The root `makefile`
   comments every `TEST_IGNORE();` out with `sed` so all tests run against the example.

**Pinned upstream reference.** `example.c#L19` at commit `ffe5457…` is the
`answer()` definition. The local `main` `HEAD` is that same commit, and
`exercises/practice/wordy` is byte-identical to it.

## Findings that need a maintainer decision (reported, not changed)

1. **`tests.toml` is behind canonical data.** Canonical has 27 cases, `tests.toml`
   tracks 23. Missing: `just a zero`, `just a negative number`,
   `addition with a left hand zero`, `addition with a right hand zero`. Real
   `configlet sync --tests` exits 1 on this. Adding them is a separate sync PR (it
   also needs matching tests in `test_wordy.c`), so the working tree is left as is.
2. **`test_wordy.c` deviates from canonical data.** `reject two numbers in a row`
   uses `"What is 1 plus plus 2 1?"`. Canonical is `"What is 1 plus 2 1?"`.
   Evidence that the test file is maintained by hand and has drifted.
3. **Header drift.** The committed `tests.toml` has the older 3-line header.
   configlet 4.0.3 writes a longer one, so any regeneration changes the header even
   when no case changes. The checker reports this explicitly and does not normalize it.

## Environment

| Tool | Version |
| --- | --- |
| configlet | 4.0.3 (official release asset, sha256 `082daca08f50481e076d8dcdd903e37d51b0e309e91c5a872f0db6208663fc2e`) |
| problem-specifications | `84a96854db1bda581317164d3e6ac6aa01723182` (2026-11-11) |
| Python | 3.13.18 (stdlib `tomllib`) |
| gcc / clang | 13.3.0 / 18.1.3 |
| GNU make / git | 4.3 / 2.43.0 |

## Limitations

- The configlet binary's minisign signature was **not** verified (no `minisign`
  available in the sandbox). It came from the official release URL over TLS.
- The task text was cut off mid-sentence in section 4A ("Enable all"). Phase 4 was
  implemented from the complete parts plus the track's own mechanism for enabling
  tests (the root `makefile`'s `TEST_IGNORE` handling). See the header of
  `check.py` for which checks come from the spec and which are inferred.
