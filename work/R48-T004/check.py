#!/usr/bin/env python3
"""R48-T004: check the sum_of_squares readability refactor in the
difference-of-squares reference implementation.

Run from anywhere:  python3 work/R48-T004/check.py

What it does (nothing in the working tree is modified; all builds happen in
temporary copies of the exercise, dotfiles included):

  1. Resolves solution/test/example paths from .meta/config.json.
  2. Static checks: stub, header and test files are unchanged against the
     pinned baseline commit; only sum_of_squares differs in example.c and its
     signature is unchanged.
  3. Runs `make test` (supplied makefile + Unity) with every test enabled for
       - the learner stub            -> must NOT build/pass (still unsolved)
       - the baseline reference      -> must pass all cases
       - the current reference       -> must pass all cases
     and fails on a non-zero exit, a missing summary, a zero-test run, a wrong
     test count, any failure or any ignored test.
  4. Compiles a small driver against baseline and current and sweeps n, comparing
     sum_of_squares / square_of_sum / difference_of_squares with an independent
     closed-form model (mod 2**32) and with each other (before == after).
  5. Negative controls: feeds the harness a broken reference, a zero-test run
     and a non-compiling reference and requires each to be reported as a failure.
  6. Saves inputs, expected-vs-actual results, logs and tool versions to
     work/R48-T004/evidence/. Exit status is non-zero if anything failed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXERCISE = "exercises/practice/difference-of-squares"
BASELINE_REF = "ffe5457101796886a272d6ebbeba8f849229c35a"  # pinned source commit
MOD = 1 << 32  # unsigned int is 32-bit on the supported targets
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVIDENCE = HERE / "evidence"
SWEEP = list(range(0, 301)) + [1000, 4096, 65535, 65536, 100000]
FUNCS = ("sum_of_squares", "square_of_sum", "difference_of_squares")

DRIVER_C = r"""
#include <stdio.h>
#include "difference_of_squares.h"

int main(void)
{
   unsigned long n;

   while (scanf("%lu", &n) == 1) {
      unsigned int v = (unsigned int)n;
      printf("%u %u %u %u\n", v, sum_of_squares(v), square_of_sum(v),
             difference_of_squares(v));
   }
   return 0;
}
"""

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m|\[\d+m")
PASS_RE = re.compile(r"^\S*:\d+:(\w+):PASS", re.M)
FAIL_RE = re.compile(r"^\S*:\d+:(\w+):FAIL", re.M)
SUMMARY_RE = re.compile(r"(\d+) Tests (\d+) Failures (\d+) Ignored")
ASSERT_RE = re.compile(r"TEST_ASSERT_EQUAL\((\d+),\s*(\w+)\((\d+)\)\)")
UUID_HEADER_RE = re.compile(r"^\[([0-9a-f-]{36})\]\s*$", re.M)
FUNC_RE = re.compile(r"^unsigned int (\w+)\(.*\)$", re.M)


class CheckError(Exception):
    """Environment/setup problem that prevents the check from running."""


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def run(cmd, cwd=None, stdin=None, timeout=120):
    try:
        p = subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "timed out after %ss" % timeout
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    return p.returncode, ANSI_RE.sub("", p.stdout), ANSI_RE.sub("", p.stderr)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_tree(root: Path) -> dict:
    return {str(p.relative_to(root)): sha256(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()}


def git_show(ref: str, rel: str) -> bytes:
    p = subprocess.run(["git", "show", "%s:%s" % (ref, rel)], cwd=REPO,
                       capture_output=True)
    if p.returncode != 0:
        raise CheckError("cannot read %s at %s (try `git fetch --unshallow`): %s"
                         % (rel, ref, p.stderr.decode().strip()))
    return p.stdout


def load_config(ex: Path):
    cfg = json.loads((ex / ".meta" / "config.json").read_text())
    files = cfg["files"]
    return files["solution"], files["test"], files["example"]


def pair_solution_to_example(solution, example) -> dict:
    pairs = {}
    for sol in solution:
        same_kind = [e for e in example if Path(e).suffix == Path(sol).suffix]
        if len(same_kind) != 1:
            raise CheckError("cannot pair %s with an example file in config.json" % sol)
        pairs[sol] = same_kind[0]
    return pairs


def model(n: int):
    """Independent closed-form reference, reduced mod 2**32 like unsigned int."""
    sos = n * (n + 1) * (2 * n + 1) // 6
    sq = (n * (n + 1) // 2) ** 2
    return sos % MOD, sq % MOD, (sq - sos) % MOD


def split_functions(src: str):
    marks = list(FUNC_RE.finditer(src))
    if not marks:
        raise CheckError("no functions found in example.c")
    chunks = {"<preamble>": src[:marks[0].start()]}
    sigs = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(src)
        chunks[m.group(1)] = src[m.start():end]
        sigs[m.group(1)] = m.group(0)
    return chunks, sigs


# --------------------------------------------------------------------------
# scratch build + run
# --------------------------------------------------------------------------
def build_scratch(src: Path, dest: Path, substitutions: dict, test_rel: str,
                  drop_run_tests: bool = False) -> int:
    """Copy the exercise (dotfiles included), substitute files, enable all tests."""
    shutil.copytree(src, dest)
    for dot in (".meta", ".docs"):
        if not (dest / dot).is_dir():
            raise CheckError("scratch copy lost %s (dotfiles not copied)" % dot)
    for rel, data in substitutions.items():
        (dest / rel).write_bytes(data)
    test_file = dest / test_rel
    text = test_file.read_text()
    text, removed = re.subn(r"^[ \t]*TEST_IGNORE\(\);.*\n", "", text, flags=re.M)
    if drop_run_tests:
        # Turn RUN_TEST(x); into (void)x; so the build still succeeds (-Werror would
        # reject unused static functions) and Unity reports a genuine "0 Tests" run.
        text = re.sub(r"^([ \t]*)RUN_TEST\((\w+)\);", r"\1(void)\2;", text, flags=re.M)
    test_file.write_text(text)
    return removed


def run_make_test(scratch: Path, tmp: Path) -> dict:
    rc, out, err = run(["make", "test"], cwd=scratch)
    log = (out + err).replace(str(tmp), "<scratch>")
    log = re.sub(r"(\S*/cc[A-Za-z0-9]{6,}\.o|[A-Za-z0-9_]+-[A-Za-z0-9]{6}\.o)", "<tmp>.o", log)  # random compiler temp names
    summary = SUMMARY_RE.search(log)
    return {
        "returncode": rc,
        "tests": int(summary.group(1)) if summary else None,
        "failures": int(summary.group(2)) if summary else None,
        "ignored": int(summary.group(3)) if summary else None,
        "passed": PASS_RE.findall(log),
        "failed": FAIL_RE.findall(log),
        "log": log,
    }


def make_problems(res: dict, expected: int) -> list:
    problems = []
    if res["returncode"] != 0:
        problems.append("make test exited with status %d" % res["returncode"])
    if res["tests"] is None:
        problems.append("no Unity summary line (build or run failed)")
        return problems
    if res["tests"] == 0:
        problems.append("zero tests executed")
    elif res["tests"] != expected:
        problems.append("executed %d tests, expected %d" % (res["tests"], expected))
    if res["failures"]:
        problems.append("%d test failure(s): %s" % (res["failures"], ", ".join(res["failed"])))
    if res["ignored"]:
        problems.append("%d test(s) ignored" % res["ignored"])
    if len(res["passed"]) != expected:
        problems.append("%d PASS lines, expected %d" % (len(res["passed"]), expected))
    return problems


def run_driver(scratch: Path, tmp: Path):
    """Compile driver.c against the scratch solution; return ({n: (sos, sq, diff)}, error)."""
    work = tmp / "driver"
    work.mkdir()
    (work / "driver.c").write_text(DRIVER_C)
    exe = work / "driver"
    rc, out, err = run(["cc", "-std=c99", "-Wall", "-Wextra", "-pedantic", "-Werror",
                        "-Wmissing-declarations", "-I", str(scratch),
                        str(scratch / "difference_of_squares.c"),
                        str(work / "driver.c"), "-o", str(exe)])
    if rc != 0:
        return None, "driver build failed: " + (out + err).strip()[:300]
    rc, out, err = run([str(exe)], stdin="\n".join(map(str, SWEEP)) + "\n", timeout=60)
    if rc != 0:
        return None, "driver exited with status %d" % rc
    rows = {}
    for line in out.splitlines():
        n, sos, sq, diff = map(int, line.split())
        rows[n] = (sos, sq, diff)
    if sorted(rows) != sorted(SWEEP):
        return None, "driver returned %d rows, expected %d" % (len(rows), len(SWEEP))
    return rows, None


def assess(label: str, src: Path, substitutions: dict, test_rel: str, expected: int,
           with_driver: bool, drop_run_tests: bool = False) -> dict:
    with tempfile.TemporaryDirectory(prefix="r48t004-%s-" % label) as t:
        tmp = Path(t)
        scratch = tmp / "exercise"
        removed = build_scratch(src, scratch, substitutions, test_rel, drop_run_tests)
        res = run_make_test(scratch, tmp)
        res["ignores_removed_in_scratch"] = removed
        problems = make_problems(res, expected)
        rows, driver_error = (None, None)
        if with_driver:
            rows, driver_error = run_driver(scratch, tmp)
            if driver_error:
                problems.append(driver_error)
            else:
                bad = [n for n in SWEEP if rows[n] != model(n)]
                if bad:
                    problems.append("driver output differs from model for n=%s%s"
                                    % (bad[:5], " ..." if len(bad) > 5 else ""))
        return {"label": label, "make": res, "rows": rows, "problems": problems}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline-ref", default=BASELINE_REF,
                    help="git ref holding the pre-refactor reference (default: pinned commit)")
    ap.add_argument("--skip-negative-controls", action="store_true")
    args = ap.parse_args(argv)

    checks = []

    def record(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name, "  - " + detail if detail else ""))

    ex = REPO / EXERCISE
    if not ex.is_dir():
        raise CheckError("exercise directory not found: %s" % ex)
    solution, tests, example = load_config(ex)
    if len(tests) != 1:
        raise CheckError("expected exactly one test file in config.json, got %r" % tests)
    test_rel = tests[0]
    pairs = pair_solution_to_example(solution, example)
    print("config.json: solution=%s test=%s example=%s" % (solution, tests, example))

    tree_before = hash_tree(ex)

    # ---- inputs -----------------------------------------------------------
    test_text = (ex / test_rel).read_text()
    canonical = [(f, int(n), int(e)) for e, f, n in ASSERT_RE.findall(test_text)]
    n_run_tests = len(re.findall(r"^[ \t]*RUN_TEST\(", test_text, re.M))
    toml = (ex / ".meta" / "tests.toml").read_text()
    blocks = re.split(r"(?m)^(?=\[[0-9a-f-]{36}\]\s*$)", toml)[1:]
    n_toml = sum(1 for b in blocks if not re.search(r"(?m)^include\s*=\s*false", b))
    record("case counts agree (RUN_TEST / TEST_ASSERT_EQUAL / tests.toml)",
           n_run_tests == len(canonical) == n_toml and n_run_tests > 0,
           "%d / %d / %d" % (n_run_tests, len(canonical), n_toml))
    expected = n_run_tests
    record("sweep covers every canonical input", all(n in SWEEP for _, n, _ in canonical))
    record("canonical expectations match closed-form model",
           all(model(n)[FUNCS.index(f)] == e for f, n, e in canonical))

    # ---- static checks against the baseline commit -------------------------
    base_bytes = {sol: git_show(args.baseline_ref, "%s/%s" % (EXERCISE, ex_rel))
                  for sol, ex_rel in pairs.items()}
    cur_bytes = {sol: (ex / ex_rel).read_bytes() for sol, ex_rel in pairs.items()}
    unchanged = [rel for rel in solution + tests + [".meta/tests.toml", ".meta/config.json"]]
    drift = [rel for rel in unchanged
             if (ex / rel).read_bytes() != git_show(args.baseline_ref, "%s/%s" % (EXERCISE, rel))]
    record("stub, test and metadata files unchanged vs baseline", not drift, ", ".join(drift))

    c_sol = next(s for s in solution if s.endswith(".c"))
    h_sol = next(s for s in solution if s.endswith(".h"))
    record("example.h (public API) unchanged vs baseline",
           base_bytes[h_sol] == cur_bytes[h_sol])
    stub_text = (ex / c_sol).read_text()
    record("learner stub contains no implementation",
           not re.search(r"\b(sum_of_squares|square_of_sum|difference_of_squares)\s*\(", stub_text))

    record("example.c differs from baseline (a refactor is present)",
           base_bytes[c_sol] != cur_bytes[c_sol])
    b_chunks, b_sigs = split_functions(base_bytes[c_sol].decode())
    c_chunks, c_sigs = split_functions(cur_bytes[c_sol].decode())
    record("only sum_of_squares changed; other functions and includes identical",
           set(b_chunks) == set(c_chunks)
           and all(b_chunks[k] == c_chunks[k] for k in b_chunks if k != "sum_of_squares")
           and b_chunks["sum_of_squares"] != c_chunks["sum_of_squares"])
    record("sum_of_squares signature (return/param types) unchanged",
           b_sigs.get("sum_of_squares") == c_sigs.get("sum_of_squares"),
           c_sigs.get("sum_of_squares", "missing"))

    # ---- make test runs ------------------------------------------------------
    stub = assess("stub", ex, {}, test_rel, expected, with_driver=False)
    stub_log = stub["make"]["log"]
    stub_link_error = any(
        msg in stub_log.lower()
        for msg in ("undefined reference", "undefined symbol", "symbol(s) not found")
    )
    record("learner stub is unsolved (make test does not build/pass)",
           stub["make"]["returncode"] != 0 and stub["make"]["tests"] is None
           and stub_link_error,
           "exit %d" % stub["make"]["returncode"])

    base = assess("baseline", ex, base_bytes, test_rel, expected, with_driver=True)
    cur = assess("current", ex, cur_bytes, test_rel, expected, with_driver=True)
    for v, name in ((base, "baseline reference"), (cur, "current reference")):
        m = v["make"]
        record("%s: make test passes all enabled cases" % name, not v["problems"],
               "%s tests, %s failures, %s ignored, exit %s%s" % (
                   m["tests"], m["failures"], m["ignored"], m["returncode"],
                   "; " + "; ".join(v["problems"]) if v["problems"] else ""))

    same_make = all(base["make"][k] == cur["make"][k]
                    for k in ("returncode", "tests", "failures", "ignored", "passed"))
    record("before/after make test results identical", same_make)
    same_rows = base["rows"] is not None and base["rows"] == cur["rows"]
    record("before/after outputs identical for %d inputs x 3 functions" % len(SWEEP), same_rows)
    if cur["rows"]:
        invariant_ok = all((cur["rows"][k][0] - cur["rows"][k - 1][0]) % MOD == (k * k) % MOD
                           for k in range(1, 301))
        record("invariant: sum_of_squares(k) - sum_of_squares(k-1) == k*k (k=1..300)", invariant_ok)

    # ---- negative controls: the harness must catch broken inputs ------------
    controls = []
    if not args.skip_negative_controls:
        cur_c = cur_bytes[c_sol].decode()
        mutants = [
            ("off-by-one loop bound", {c_sol: cur_c.replace("<= number", "< number", 1).encode(),
                                       h_sol: cur_bytes[h_sol]}, False, "failure"),
            ("zero-test run", cur_bytes, True, "zero tests executed"),
            ("does not compile", {c_sol: (cur_c + "\nnot valid C;\n").encode(),
                                  h_sol: cur_bytes[h_sol]}, False, "no Unity summary"),
        ]
        for name, subs, drop, needle in mutants:
            if name == "off-by-one loop bound" and subs[c_sol].decode() == cur_c:
                record("negative control: %s" % name, False, "mutation did not apply")
                continue
            r = assess("neg", ex, subs, test_rel, expected, with_driver=(not drop and name != "does not compile"),
                       drop_run_tests=drop)
            caught = any(needle in p for p in r["problems"])
            controls.append({"name": name, "caught": caught, "problems": r["problems"]})
            record("negative control caught: %s" % name, caught, "; ".join(r["problems"])[:160])

    # ---- working tree untouched ---------------------------------------------
    record("working tree not modified by this check", hash_tree(ex) == tree_before)

    # ---- evidence --------------------------------------------------------------
    write_evidence(checks, stub, base, cur, canonical, controls, args.baseline_ref,
                   base_bytes[c_sol], cur_bytes[c_sol], expected)

    failed = [c for c in checks if not c["ok"]]
    executed = cur["make"]["tests"] or 0
    print("\nexecuted cases (current reference, make test): %d of %d expected" % (executed, expected))
    print("%d checks, %d failed; evidence in %s" % (len(checks), len(failed), EVIDENCE.relative_to(REPO)))
    return 1 if failed else 0


def tool_versions() -> dict:
    v = {"python": sys.version.split()[0], "platform": platform.platform()}
    for label, cmd in (("cc", ["cc", "--version"]), ("gcc", ["gcc", "--version"]),
                       ("make", ["make", "--version"]), ("git", ["git", "--version"]),
                       ("clang-format", ["clang-format", "--version"])):
        rc, out, err = run(cmd)
        text = (out or err).strip()
        v[label] = text.splitlines()[0] if rc == 0 and text else "not available"
    unity = REPO / EXERCISE / "test-framework" / "unity.c"
    v["unity.c sha256"] = sha256(unity.read_bytes())
    return v


def write_evidence(checks, stub, base, cur, canonical, controls, ref, base_c, cur_c, expected):
    if EVIDENCE.exists():
        shutil.rmtree(EVIDENCE)
    EVIDENCE.mkdir(parents=True)
    (EVIDENCE / "tool_versions.txt").write_text(
        "".join("%s: %s\n" % kv for kv in tool_versions().items()))
    (EVIDENCE / "inputs.json").write_text(json.dumps({
        "exercise": EXERCISE, "baseline_ref": ref, "expected_case_count": expected,
        "canonical_cases": [{"function": f, "n": n, "expected": e} for f, n, e in canonical],
        "sweep": SWEEP, "modulus": MOD}, indent=2) + "\n")

    def actual(v, f, n):
        return v["rows"][n][FUNCS.index(f)] if v["rows"] else None

    results = {
        "example_c_sha256": {"baseline": sha256(base_c), "current": sha256(cur_c)},
        "canonical_expected_vs_actual": [
            {"function": f, "n": n, "expected": e,
             "baseline": actual(base, f, n), "current": actual(cur, f, n),
             "ok": actual(base, f, n) == e == actual(cur, f, n)}
            for f, n, e in canonical],
        "make_test": {v["label"]: {k: v["make"][k] for k in
                                   ("returncode", "tests", "failures", "ignored",
                                    "passed", "failed", "ignores_removed_in_scratch")}
                      for v in (stub, base, cur)},
        "negative_controls": controls,
        "checks": checks,
    }
    (EVIDENCE / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    for v in (stub, base, cur):
        (EVIDENCE / ("make_test_%s.log" % v["label"])).write_text(v["make"]["log"])

    with open(EVIDENCE / "sweep.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "function", "expected_model", "baseline", "current"])
        for n in SWEEP:
            for i, f in enumerate(FUNCS):
                w.writerow([n, f, model(n)[i], base["rows"][n][i] if base["rows"] else "",
                            cur["rows"][n][i] if cur["rows"] else ""])

    # trace of the accumulator: its value after iteration k equals sum_of_squares(k)
    lines = ["# Trace of sum_of_squares (current reference)", "",
             "Local state that determines the result: loop variable `n` and accumulator `total`.",
             "After the iteration for `n = k`, `total == sum_of_squares(k)` (measured from the",
             "compiled reference, not modelled). The baseline's extra `i = 0` pass added 0.", ""]
    for target in (1, 5, 100):
        lines += ["## sum_of_squares(%d) = %s" % (target, cur["rows"][target][0] if cur["rows"] else "?"), "",
                  "| n | n*n | total after this iteration |", "|---|-----|-----------------------------|"]
        ks = list(range(1, target + 1)) if target <= 10 else [1, 2, 3, 4, 5, None, 98, 99, 100]
        for k in ks:
            if k is None:
                lines.append("| ... | ... | ... |")
            elif cur["rows"]:
                lines.append("| %d | %d | %d |" % (k, k * k, cur["rows"][k][0]))
        lines.append("")
    (EVIDENCE / "trace_sum_of_squares.md").write_text("\n".join(lines))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CheckError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        sys.exit(2)
