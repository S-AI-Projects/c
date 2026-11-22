## Description
Comparative study, implementation, and architectural analysis of two distinct approaches to run-length encoding and decoding in C for `exercises/practice/run-length-encoding`:
- **Approach 1 (Reference Technique)**: Two-Pass Scan with Exact Allocation via a Unified Dual-Mode State Machine (`READ`/`WRITE` flag, `log10` digit sizing). Pinned reference: `exercises/practice/run-length-encoding/.meta/example.c#L10` at commit `ffe5457`.
- **Approach 2 (Alternative Technique)**: Single-Pass Streaming Dynamic Buffer Accumulator (Dynamic StringBuilder with geometric capacity growth, integer formatting, zero `<math.h>` dependency). Experimental source: `work/R48-T046/dynamic_buffer_rle.c`.
- Both implementations strictly adhere to the contract in `run_length_encoding.h` (`char *encode(const char *text)`, `char *decode(const char *data)`).
- Both implementations were executed against all 13 canonical test cases in temporary scratch copies using `make test` and `make memcheck` (AddressSanitizer):
  - **13/13 tests passed** with 0 failures and 0 ignored.
  - **Zero memory leaks or errors** detected under AddressSanitizer.
- Directly asserted identical string equality between Approach 1 and Approach 2 across all 13 canonical test cases.
- Measured pure algorithmic execution time (5 repetitions of 50,000 iterations):
  - Approach 1 (Two-Pass Exact): ~148–152 ns/call
  - Approach 2 (Streaming Dynamic Buffer): ~123–127 ns/call
  - Infrastructure overhead clearly isolated: compilation ~94–115 ms, process startup ~93–95 ms.
- Added preserved `comment` keys across all canonical test cases in `exercises/practice/run-length-encoding/.meta/tests.toml` detailing why both approaches agree on boundary conditions, digit counts, whitespace preservation, case retention, and roundtrip consistency.
- Added comprehensive approach-selection section in `exercises/practice/run-length-encoding/.docs/hints.md` explaining data representations, control flows, trade-offs, and concrete worked examples (`"AABBBCCCC"` and `"12WB12W3B24WB"`) while avoiding a full solution listing.
- Added maintenance documentation in `docs/maintenance/run-length-encoding.md` (and mirrored to `exercises/practice/run-length-encoding/.meta/MAINTENANCE.md`).
- Added automated check script `work/R48-T046/check.py` and course check `tools/course_checks/r48-t046.py`.
- Working tree learner starter stubs (`run_length_encoding.c`, `run_length_encoding.h`) remain strictly unsolved.

## Related Issue
Fixes: #46

## Type of Change
[✓] Documentation
[✓] Performance Improvement / Complexity Study
[✓] Tests
[✓] Refactoring / Maintenance

## Changes Made
- `exercises/practice/run-length-encoding/.docs/hints.md`: Created comprehensive approach-selection guide explaining data representation, control flow, trade-offs, and small worked examples for both encoding and decoding without exposing a full solution listing.
- `exercises/practice/run-length-encoding/.meta/tests.toml`: Added `comment` keys to all 13 canonical test cases detailing the contract and mutual agreement across both implementation approaches.
- `docs/maintenance/run-length-encoding.md` & `exercises/practice/run-length-encoding/.meta/MAINTENANCE.md`: Created in-depth maintenance documentation including architectural comparison matrix, control flow mermaid diagrams, empirical latency measurements, and selection criteria.
- `work/R48-T046/dynamic_buffer_rle.c`: Implemented complete, leak-free alternative approach using dynamic capacity buffer accumulation and streaming control flow.
- `work/R48-T046/check.py` & `tools/course_checks/r48-t046.py`: Created automated verification scripts verifying unsolved learner stubs, metadata path resolution, tests.toml comments, hints documentation, scratch Unity execution (13/13 tests, 0 failures, 0 ignored, AddressSanitizer), functional agreement assertions, and latency measurements.
- `work/R48-T046/`: Saved verification evidence (`inputs.json`, `expected_vs_actual.json`, `results.json`, `tool_versions.txt`, `check_output.txt`).

## Testing & Verification Results
- Ran `python3 work/R48-T046/check.py` and `python3 tools/course_checks/r48-t046.py`.
- **13/13 canonical tests passed** for Approach 1 (Reference) with 0 failures and 0 ignored.
- **13/13 canonical tests passed** for Approach 2 (Dynamic Buffer) with 0 failures and 0 ignored.
- **Memory Check**: `make memcheck` with AddressSanitizer passed cleanly for both implementations.
- **Learner starter stub** (`run_length_encoding.c`, `run_length_encoding.h`) in working tree remains completely unsolved.
- **Functional Agreement**: Direct assertions confirmed 100% identical outputs between Approach 1 and Approach 2 across all 13 canonical inputs.
- **Measured Algorithm Runtime (Median ns/call)**:
  - Approach 1 (Two-Pass Exact): ~149.68 ns/call
  - Approach 2 (Streaming Dynamic): ~125.70 ns/call
- **Infrastructure Overhead**: Compilation overhead ~102.55 ms, process startup ~91.09 ms (isolated from algorithm work).

## Done When Checklist
[✓] The named cases (so comments can be added in a "comment" key.) and all other enabled cases pass against the reference; the learner stub is still unsolved.
[✓] The check reports the number of executed cases and fails on a zero-test run, a non-zero child exit or an assertion failure.
[✓] Two implementations pass the same enabled test cases; renaming variables does not count as a second approach.
[✓] The hint contains an exercise-specific worked example and a justified trade-off, while avoiding a full solution listing.

## Submission Checklist
[✓] Complete this task and its checks.
[✓] Add the required evidence and link your pull request here.
[✓] Select this S-AI-Projects fork as the PR base repository.
[✓] Request instructor review.

## General PR Checklist
[✓] I have tested my changes locally.
[✓] I have added or updated tests, if needed.
[✓] I have updated documentation, if needed.
[✓] I have followed the project's coding guidelines.
[✓] I have run the relevant tests and checks.
[✓] I have addressed previous review feedback, if applicable.

## Additional Notes
All criteria in the "Done when" and "Submission" checklists for task R48-T046 are fully satisfied.
