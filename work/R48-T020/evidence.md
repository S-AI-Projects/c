# Evidence for R48-T020: hello-world

## Verification Summary

1. **Reference Execution**:
   - Substituted `.meta/example.c` into a temporary scratch directory.
   - Executed `make clean && make test`.
   - Result: **1 Tests, 0 Failures, 0 Ignored**, exit code 0.

2. **Negative Controls**:
   - Tested unsolved starter stub (`hello_world.c` returning `"Goodbye, Mars!"`). Failed with 1 failure as expected.
   - Tested zero-test suite; detected 0 executed cases.

3. **Canonical Specification**:
   - Verified `.meta/tests.toml` contains anchor header:
     `so comments can be added in a "comment" key.`
   - Verified canonical case `[af9ffe10-dc13-42d8-a742-e7bdafac449d]` (`"Say Hi!"`).

4. **Contract Guidance (`.docs/hints.md`)**:
   - Added decision table mapping in-contract calls to `"Hello, World!"`.
   - Explicitly separated specified behavior from unspecified operations (mutating read-only `.rodata`, calling `free()`, stdout writing, locales).

## Unity Output

```
./test_hello_world.c:32:test_say_hi:PASS

-----------------------
1 Tests 0 Failures 0 Ignored 
OK
```
