## R48-T042: Make the linked-list test-generation path reproducible

### Summary

This PR establishes and verifies the test generation and synchronization route for `exercises/practice/linked-list`:
- Documents the generation command (`./bin/configlet sync --exercise linked-list --tests include --update --yes`), input files, maintained vs generated files, and case-to-output mapping in `docs/maintenance/linked-list.md`.
- Records that no per-exercise Jinja template exists for C; tests in `test_linked_list.c` are maintained directly by hand according to canonical specifications.
- Adds the reusable focused regeneration check `tools/course_checks/r48-t042.py` verifying test generation reproducibility, key handling rules (description, reimplements, preserve other keys such as `comment` key), and reference execution.
- Verifies that all 19 canonical test cases pass against the reference implementation in an isolated scratch directory without modifying the working tree or learner starter files.
- Learner starter stub files (`linked_list.c`, `linked_list.h`) remain completely unsolved.

### Verification Results

- **Canonical cases**: 19 total, 19 included, 0 dropped.
- **Two generations identical**: Yes (verified after timestamp normalization).
- **Key preservation**: Verified preservation of `comment` key across regeneration.
- **Reference test execution**: 19 run, 0 failures, 0 ignored (Exit code 0).
- **Working tree integrity**: Preserved, no modifications to learner solution files.
