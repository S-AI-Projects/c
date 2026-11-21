Open a pull request for task R48-T005 (issue #5, saddle-points complexity study) in the repository S-AI-Projects/c.

1. Create branch `R48-T005` from the fork's default branch. (Issue #5 also names `student/e26b07f0554` as the assigned working branch; use that name instead if the instructor expects it.)
2. The change is exactly these paths: `exercises/practice/saddle-points/.meta/example.c` (comment only), `docs/maintenance/saddle-points.md`, and the folder `work/R48-T005/`. Do not touch the learner files `saddle_points.c` and `saddle_points.h`.
3. Run `python3 work/R48-T005/check.py`. If it exits non-zero, stop and report the failing lines.
4. Commit with the message "R48-T005: document the cost of is_greatest_in_row in the saddle-points reference" and push the branch.
5. Open the PR with base repository S-AI-Projects/c (the fork, never exercism/c), title "R48-T005: Measure the scaling of the saddle-points reference", and the body taken verbatim from `work/R48-T005/PR_DESCRIPTION.md`. Leave the last three submission checkboxes unchecked, then tick them yourself as you link the PR in issue #5, confirm the base repository, and request instructor review.
