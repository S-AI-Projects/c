# Maintenance Notes — react

## Isolated Runner & Learner Protection

This exercise implements a reactive system (`exercises/practice/react/`).
To ensure learners are not exposed to reference code and their starter files remain untouched, the verification runner follows strict isolation:

### File Roles
- **Learner stub (solution):** `react.c`, `react.h` — maintained unsolved in the exercise tree.
- **Reference implementation:** `.meta/example.c` — maintained in `.meta/`.
- **Test suite:** `test_react.c` (using Unity framework).
- **Metadata:** `.meta/tests.toml`, `.meta/config.json`.

### Verification Strategy
1. **Isolated execution:** The test suite runs inside a clean temporary directory (`tempfile.TemporaryDirectory()`).
2. **Reference substitution:** `.meta/example.c` is copied over `react.c` inside the temporary directory only.
3. **Learner file integrity:** SHA-256 hashes of `react.c` and `react.h` in the working tree are measured before and after every execution (including failing and zero-test runs) to prove zero modification.
4. **Failure and zero-test propagation:** The runner detects and fails if test cases fail or if zero tests are executed.
