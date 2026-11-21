# all-your-base — Isolated Test Runner (R48-T019)

## Command

Run the automated check suite from the repository root:

```sh
python3 work/R48-T019/check.py
```

To run the runner directly against the exercise:

```sh
python3 tools/course_checks/r48-t019.py exercises/practice/all-your-base --scenario real
```

Supported runner scenarios (`tools/course_checks/r48-t019.py`):

- `real` — copies the exercise into a temporary directory, substitutes the reference implementation (`.meta/example.c` and `.meta/example.h`) into the solution paths, enables all test cases, executes `make test`, and asserts all 21 test cases pass with 0 failures and 0 ignored.
- `failing` — introduces a deliberate mutation in the scratch copy reference to assert that test failures propagate with a non-zero exit code.
- `empty` — comments out all `RUN_TEST()` calls in the scratch copy test suite to assert that zero-test runs fail with a non-zero exit code.

---

## Tool Requirements

- **Python 3** (stdlib: `argparse`, `hashlib`, `json`, `pathlib`, `re`, `shutil`, `subprocess`, `tempfile`)
- **C Compiler**: Clang or GCC (`cc`) with C99 support
- **Build tool**: GNU `make`
- **Test framework**: Unity (vendored in `exercises/practice/all-your-base/test-framework/`)

---

## What It Checks

1. **Isolation**:
   - The runner resolves `files.solution`, `files.test`, and `files.example` from `exercises/practice/all-your-base/.meta/config.json`.
   - All compilation and test execution occur inside an isolated `tempfile.TemporaryDirectory`.
   - Scratch directories are automatically removed upon completion or interruption.
2. **Learner Invariant Preservation**:
   - SHA-256 hashes of all learner files (`all_your_base.c`, `all_your_base.h`, `test_all_your_base.c`, `makefile`) and metadata files (`.meta/config.json`, `.meta/tests.toml`) are captured before and after every run.
   - Hashes are confirmed byte-identical across successful, failing, and empty runs. The learner stub is never modified or solved in the working tree.
3. **Reference Verification**:
   - When substituting the reference (`.meta/example.c` + `.meta/example.h`), all 21 test cases pass with 0 failures, 0 ignored, and exit code 0.
4. **Named Canonical Cases**:
   - `[232fa4a5-e761-4939-ba0c-ed046cd0676a]`: description = `"invalid positive digit"` (`test_invalid_positive_digit`)
   - `[14238f95-45da-41dc-95ce-18f860b30ad3]`: description = `"output base is one"` (`test_output_base_is_one`)
   Both cases are verified passing against the reference.
5. **Fault Injection (Negative Controls)**:
   - A broken reference fails `make test` and yields exit code 1.
   - An empty test suite executes 0 tests and yields exit code 1.
   - Running tests against the unsolved learner stub fails to compile/link (exit code 2).

---

## Canonical Test Case Inventory

`exercises/practice/all-your-base/.meta/tests.toml` tracks 21 canonical cases (20 included, 1 excluded: `empty list`). The exercise test file `test_all_your_base.c` implements 21 test functions, all of which pass against the reference:

| # | UUID | Canonical Description | Status | C Test Function |
|---|---|---|---|---|
| 1 | `5ce422f9-7a4b-4f44-ad29-49c67cb32d2c` | single bit one to decimal | Included | `test_single_bit_to_decimal` |
| 2 | `0cc3fea8-bb79-46ac-a2ab-5a2c93051033` | binary to single decimal | Included | `test_binary_to_single_decimal` |
| 3 | `f12db0f9-0d3d-42c2-b3ba-e38cb375a2b8` | single decimal to binary | Included | `test_single_decimal_to_binary` |
| 4 | `2c45cf54-6da3-4748-9733-5a3c765d925b` | binary to multiple decimal | Included | `test_binary_to_multiple_decimal` |
| 5 | `65ddb8b4-8899-4fcc-8618-181b2cf0002d` | decimal to binary | Included | `test_decimal_to_binary` |
| 6 | `8d418419-02a7-4824-8b7a-352d33c6987e` | trinary to hexadecimal | Included | `test_trinary_to_hexadecimal` |
| 7 | `d3901c80-8190-41b9-bd86-38d988efa956` | hexadecimal to trinary | Included | `test_hexadecimal_to_trinary` |
| 8 | `5d42f85e-21ad-41bd-b9be-a3e8e4258bbf` | 15-bit integer | Included | `test_15_bit_integer` |
| 9 | `d68788f7-66dd-43f8-a543-f15b6d233f83` | empty list | Excluded (`include = false`) | `test_empty_list` |
| 10 | `5e27e8da-5862-4c5f-b2a9-26c0382b6be7` | single zero | Included | `test_single_zero` |
| 11 | `2e1c2573-77e4-4b9c-8517-6c56c5bcfdf2` | multiple zeros | Included | `test_multiple_zeros` |
| 12 | `3530cd9f-8d6d-43f5-bc6e-b30b1db9629b` | leading zeros | Included | `test_leading_zeros` |
| 13 | `a6b476a1-1901-4f2a-92c4-4d91917ae023` | input base is one | Included | `test_input_base_is_one` |
| 14 | `e21a693a-7a69-450b-b393-27415c26a016` | input base is zero | Included | `test_input_base_is_zero` |
| 15 | `54a23be5-d99e-41cc-88e0-a650ffe5fcc2` | input base is negative | Included | `test_input_base_is_negative` |
| 16 | `9eccf60c-dcc9-407b-95d8-c37b8be56bb6` | negative digit | Included | `test_negative_digit` |
| 17 | `232fa4a5-e761-4939-ba0c-ed046cd0676a` | invalid positive digit | Included | `test_invalid_positive_digit` |
| 18 | `14238f95-45da-41dc-95ce-18f860b30ad3` | output base is one | Included | `test_output_base_is_one` |
| 19 | `73dac367-da5c-4a37-95fe-c87fad0a4047` | output base is zero | Included | `test_output_base_is_zero` |
| 20 | `13f81f42-ff53-4e24-89d9-37603a48ebd9` | output base is negative | Included | `test_output_base_is_negative` |
| 21 | `0e6c895d-8a5d-4868-a345-309d094cfe8d` | both bases are negative | Included | `test_both_bases_are_negative` |

---

## Files Changed

- `tools/course_checks/r48-t019.py`: Isolated test runner implementing scenario execution, hash verification, and Unity parsing.
- `docs/maintenance/all-your-base.md`: This maintenance document.

No learner files under `exercises/practice/all-your-base/` are modified.
