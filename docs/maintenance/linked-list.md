# Linked List: Test Generation & Maintenance Guide

## Overview

This maintenance page documents and verifies the test synchronization, generation route, and contract mapping for the `linked-list` practice exercise in the Exercism C track.

Pinned reference implementation source: [`exercises/practice/linked-list/.meta/example.c#L51` at `ffe5457`](https://github.com/exercism/c/blob/ffe5457101796886a272d6ebbeba8f849229c35a/exercises/practice/linked-list/.meta/example.c#L51).

## Canonical Data Source

The canonical test cases originate from the upstream Exercism `problem-specifications` repository:
- **Canonical data file**: `exercises/linked-list/canonical-data.json`
- **Track metadata**: `exercises/practice/linked-list/.meta/tests.toml`
- **Exercise configuration**: `exercises/practice/linked-list/.meta/config.json`
- **Track configuration**: `config.json`

## Maintained vs Generated Files

- **Generated / Synchronized by Tooling:**
  - `exercises/practice/linked-list/.meta/tests.toml`: Synchronized from upstream `problem-specifications/exercises/linked-list/canonical-data.json` using Exercism's `configlet` CLI.
- **Maintained by Hand:**
  - `exercises/practice/linked-list/test_linked_list.c`: Test file containing unit tests using the Unity test framework (`test-framework/unity.h`). **Note on test generator:** No per-exercise Jinja template exists for C test generation in this track; the test file is maintained by hand following the canonical test specifications.
  - `exercises/practice/linked-list/linked_list.h` & `linked_list.c`: Learner starter interface and stub.
  - `exercises/practice/linked-list/.meta/example.h` & `example.c`: Reference solution.
  - `exercises/practice/linked-list/.meta/config.json`: File paths and exercise metadata.
  - `exercises/practice/linked-list/.docs/instructions.md`: Problem description.

## Reproduction and Synchronization Command

To fetch the official `configlet` tool and synchronize `tests.toml`:

```bash
# 1. Fetch configlet if not already present in ./bin
./bin/fetch-configlet

# 2. Synchronize tests.toml against canonical-data.json
./bin/configlet sync --exercise linked-list --tests include --update --yes
```

If operating in an environment without internet access where `problem-specifications` is already cached (e.g. in `~/.cache/exercism/configlet` or `~/Library/Caches/exercism/configlet`), append `--offline`:

```bash
./bin/configlet sync --exercise linked-list --tests include --update --yes --offline
```

## Key Handling Rules (The Three Cases)

When regenerating or synchronizing `exercises/practice/linked-list/.meta/tests.toml` from canonical data, the generator follows three key handling rules:

1. **Recreate every `description` key/value pair**: Matches the upstream canonical test case description from `canonical-data.json`.
2. **Recreate every `reimplements` key/value pair**: Preserves/recreates tracking for any reimplemented canonical test UUIDs where specified in `problem-specifications`.
3. **Preserve any other key/value pair**:
   - Preserves custom rationale comments added in a `comment` key: as stated in the `tests.toml` header:
     `# Regular comments will be removed when this file is regenerated. Regenerating will not touch any manually added keys, so comments can be added in a "comment" key.`
   - Preserves exclusions such as `include = false` where specific cases are omitted by track policy.

Two successive runs of `configlet sync` produce bit-for-bit identical `tests.toml` content (modulo documented timestamp comments), ensuring complete determinism. No canonical case is dropped.

## Case-to-Output Mapping

All 19 canonical test cases from `canonical-data.json` are implemented in `test_linked_list.c` and enabled against the reference solution.

| # | Canonical UUID | Canonical Description | Unity Test Function (`test_linked_list.c`) | C API Operations Exercised |
|---|----------------|-----------------------|--------------------------------------------|----------------------------|
| 1 | `7f7e3987-b954-41b8-8084-99beca08752c` | pop gets element from the list | `test_pop_gets_element_from_the_list` | `list_push`, `list_pop` |
| 2 | `c3f67e5d-cfa2-4c3e-a18f-7ce999c3c885` | push/pop respectively add/remove at the end of the list | `test_push_pop_respectively_add_remove_at_the_end_of_the_list` | `list_push`, `list_pop` |
| 3 | `00ea24ce-4f5c-4432-abb4-cc6e85462657` | shift gets an element from the list | `test_shift_gets_an_element_from_the_list` | `list_push`, `list_shift` |
| 4 | `37962ee0-3324-4a29-b588-5a4c861e6564` | shift gets first element from the list | `test_shift_gets_first_element_from_the_list` | `list_push`, `list_shift` |
| 5 | `30a3586b-e9dc-43fb-9a73-2770cec2c718` | unshift adds element at start of the list | `test_unshift_adds_element_at_start_of_the_list` | `list_unshift`, `list_shift` |
| 6 | `042f71e4-a8a7-4cf0-8953-7e4f3a21c42d` | pop, push, shift, and unshift can be used in any order | `test_pop_push_shift_and_unshift_can_be_used_in_any_order` | `list_push`, `list_pop`, `list_unshift`, `list_shift` |
| 7 | `88f65c0c-4532-4093-8295-2384fb2f37df` | count an empty list | `test_count_an_empty_list` | `list_count` |
| 8 | `fc055689-5cbe-4cd9-b994-02e2abbb40a5` | count a list with items | `test_count_a_list_with_items` | `list_push`, `list_count` |
| 9 | `8272cef5-130d-40ea-b7f6-5ffd0790d650` | count is correct after mutation | `test_count_is_correct_after_mutation` | `list_push`, `list_unshift`, `list_shift`, `list_pop`, `list_count` |
| 10 | `229b8f7a-bd8a-4798-b64f-0dc0bb356d95` | popping to empty doesn't break the list | `test_popping_to_empty_does_not_break_the_list` | `list_push`, `list_pop`, `list_count` |
| 11 | `4e1948b4-514e-424b-a3cf-a1ebbfa2d1ad` | shifting to empty doesn't break the list | `test_shifting_to_empty_does_not_break_the_list` | `list_push`, `list_shift`, `list_count` |
| 12 | `e8f7c600-d597-4f79-949d-8ad8bae895a6` | deletes the only element | `test_deletes_the_only_element` | `list_push`, `list_delete`, `list_count` |
| 13 | `fd65e422-51f3-45c0-9fd0-c33da638f89b` | deletes the element with the specified value from the list | `test_deletes_the_element_with_the_specified_value_from_the_list` | `list_push`, `list_delete`, `list_count`, `list_pop`, `list_shift` |
| 14 | `59db191a-b17f-4ab7-9c5c-60711ec1d013` | deletes the element with the specified value from the list, re-assigns tail | `test_deletes_the_element_with_the_specified_value_from_the_list_reassigns_tail` | `list_push`, `list_delete`, `list_count`, `list_pop` |
| 15 | `58242222-5d39-415b-951d-8128247f8993` | deletes the element with the specified value from the list, re-assigns head | `test_deletes_the_element_with_the_specified_value_from_the_list_reassigns_head` | `list_push`, `list_delete`, `list_count`, `list_shift` |
| 16 | `ee3729ee-3405-4bd2-9bad-de0d4aa5d647` | deletes the first of two elements | `test_deletes_the_first_of_two_elements` | `list_push`, `list_delete`, `list_count`, `list_pop` |
| 17 | `47e3b3b4-b82c-4c23-8c1a-ceb9b17cb9fb` | deletes the second of two elements | `test_deletes_the_second_of_two_elements` | `list_push`, `list_delete`, `list_count`, `list_pop` |
| 18 | `7b420958-f285-4922-b8f9-10d9dcab5179` | delete does not modify the list if the element is not found | `test_delete_does_not_modify_the_list_if_the_element_is_not_found` | `list_push`, `list_delete`, `list_count` |
| 19 | `7e04828f-6082-44e3-a059-201c63252a76` | deletes only the first occurrence | `test_deletes_only_the_first_occurrence` | `list_push`, `list_delete`, `list_count`, `list_pop` |

## Isolated Verification Procedure

The reference implementation is verified in an isolated temporary directory without modifying learner files or the working tree:
1. Parse exercise paths from `exercises/practice/linked-list/.meta/config.json`.
2. Copy the exercise directory (including dotfiles) to a scratch temporary directory.
3. Substitute reference files (`.meta/example.c` -> `linked_list.c`, `.meta/example.h` -> `linked_list.h`) only within the temporary copy.
4. Enable all test cases by stripping `TEST_IGNORE();` from the scratch copy's test file.
5. Execute `make test` using the supplied exercise makefile.
6. Verify child exit code 0, 19 passing tests, 0 failures, and 0 ignored tests.

## Verification & Task Checklist

### Done When Checklist
- [x] The named cases (so comments can be added in a "comment" key.) and all other enabled cases pass against the reference; the learner stub is still unsolved.
- [x] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
- [x] Two generations yield the same tests after the documented timestamp normalization; no case is silently dropped.
- [x] The maintenance page identifies the source of the three cases (so comments can be added in a "comment" key.) and the command that reproduces them.

### Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
