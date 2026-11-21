#!/usr/bin/env python3
"""R48-T005: cost of is_greatest_in_row in the saddle-points reference.

    python3 work/R48-T005/check.py [--reps N]

Everything that compiles or runs happens in temporary copies of the exercise.
Only work/R48-T005/evidence/ is written. The exit code is non-zero when any
assertion fails, a child process exits non-zero where it should not, or a
test run executes zero tests.

What it does, in order
  1. Resolves solution/test/example paths from .meta/config.json.
  2. Learner stub: still unsolved (content, git state, and `make test` fails).
  3. Reference: copies the exercise (dotfiles included), puts the reference in
     the place of the solution files in the copy only, enables every test
     case, runs `make test` (supplied makefile + Unity), and checks return
     code, test count and that each case named in tests.toml passed.
  4. Negative controls: a zero-test run, a broken reference and the bare stub
     must each be reported as problems by the same evaluator.
  5. Scaling study: for each input size and each input pattern
       - the input is validated against the specification;
       - correctness is asserted first (real saddle_points() against an
         independent O(R*C) oracle);
       - executed comparisons are counted in an instrumented copy and compared
         with an independent Python model and, for the two extreme patterns,
         with closed forms;
       - only after every correctness assertion has passed, the algorithm is
         timed in-process (monotonic clock around the sweep only).
  6. Checks that the exercise directory was not modified, that the comment in
     example.c states the bounds, and that the doc quotes the measured counts.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import itertools
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

TASK = "R48-T005"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EXERCISE = REPO / "exercises" / "practice" / "saddle-points"
DOC = REPO / "docs" / "maintenance" / "saddle-points.md"
EVIDENCE = HERE / "evidence"

# Input sizes as (rows, columns). All are far below the reference's limit:
# is_greatest_in_row takes int16_t indices, so indices must stay <= 32767.
SIZES = [(256, 256), (256, 512), (512, 512)]
PATTERNS = ("worst", "best", "random")
SEED = 48005
MAX_INDEX = 32767
MIN_REPS = 5
DEFAULT_REPS = 7

CC = os.environ.get("CC", "cc")
CFLAGS = ["-std=c99", "-O2", "-Wall", "-Wextra", "-pedantic", "-Werror",
          "-Wmissing-declarations"]
ENV = dict(os.environ, LC_ALL="C")
M64 = (1 << 64) - 1

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SUMMARY = re.compile(r"^(\d+) Tests (\d+) Failures (\d+) Ignored", re.M)
RESULT = re.compile(r"^\S+?:\d+:(\w+):(PASS|FAIL|IGNORE)", re.M)


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------
class Checker:
    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []

    def ok(self, condition: bool, label: str, detail: str = "") -> bool:
        if condition:
            self.passed += 1
            print(f"  ok    {label}")
        else:
            self.failed.append(label)
            print(f"  FAIL  {label}" + (f": {detail}" if detail else ""))
        return bool(condition)


def section(title: str) -> None:
    print(f"\n== {title}")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def run(cmd, cwd=None, timeout=300):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, env=ENV)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha256_file(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def parse_kv(text: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)


def mix(x: int) -> int:
    """splitmix64 finaliser; mirrors mix() in harness.c."""
    x = (x + 0x9E3779B97F4A7C15) & M64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & M64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & M64
    return x ^ (x >> 31)


def points_hash(points) -> int:
    return sum(mix((r << 32) | c) for r, c in points) & M64


STOPWORDS = {"a", "an", "the", "that"}


def words(text: str) -> tuple[str, ...]:
    return tuple(w for w in re.split(r"[^a-z0-9]+", text.lower())
                 if w and w not in STOPWORDS)


def description_key(description: str) -> tuple[str, ...]:
    """tests.toml description -> comparable key ('Can identify ...' dropped)."""
    return words(re.sub(r"^\s*can identify\b", "", description.lower()))


def function_key(function_name: str) -> tuple[str, ...]:
    """test function name -> comparable key. The track's test file drops
    articles that the canonical descriptions have ('in a non square matrix'
    becomes test_..._in_non_square_matrix), so both sides ignore them."""
    return words(re.sub(r"^test_", "", function_name))


# --------------------------------------------------------------------------
# step 1: config
# --------------------------------------------------------------------------
def load_config():
    cfg = json.loads((EXERCISE / ".meta" / "config.json").read_text())
    files = cfg["files"]
    pairs = []  # (example file, solution file it replaces)
    for example in files["example"]:
        same_kind = [s for s in files["solution"]
                     if Path(s).suffix == Path(example).suffix]
        if len(same_kind) != 1:
            sys.exit(f"cannot pair {example} with a solution file: {same_kind}")
        pairs.append((example, same_kind[0]))
    if sorted(s for _, s in pairs) != sorted(files["solution"]):
        sys.exit("config.json: example files do not cover every solution file")
    return files, pairs


def expected_case_names(test_text: str) -> list[tuple[str, str]]:
    """(tests.toml description, test function) for every included case.
    A description with no matching RUN_TEST gets the function name '' so the
    caller reports it instead of silently skipping it."""
    toml = tomllib.loads((EXERCISE / ".meta" / "tests.toml").read_text())
    by_key = {function_key(f): f for f in
              re.findall(r"RUN_TEST\(\s*(\w+)\s*\)", test_text)}
    out = []
    for entry in toml.values():
        if isinstance(entry, dict) and entry.get("include") is not False:
            out.append((entry["description"],
                        by_key.get(description_key(entry["description"]), "")))
    return out


# --------------------------------------------------------------------------
# steps 2-4: make test in scratch copies
# --------------------------------------------------------------------------
def scratch_copy(tmp: Path, name: str, files, pairs, substitute: bool,
                 enable_tests: bool) -> Path:
    dst = tmp / name
    shutil.copytree(EXERCISE, dst, symlinks=True)  # dotfiles included
    if substitute:
        for example, solution in pairs:
            shutil.copyfile(dst / example, dst / solution)
    if enable_tests:
        for test in files["test"]:
            path = dst / test
            text, _ = re.subn(r"^[ \t]*TEST_IGNORE\(\);[^\n]*\n", "",
                              path.read_text(), flags=re.M)
            assert "TEST_IGNORE" not in text
            path.write_text(text)
    return dst


def make_test(directory: Path):
    p = run(["make", "test"], cwd=directory, timeout=180)
    return p.returncode, ANSI.sub("", p.stdout + p.stderr)


def evaluate_make_test(returncode: int, output: str, expected: list[str]):
    """Return (problems, info). No problems means a clean, complete run."""
    problems = []
    results = dict(RESULT.findall(output))
    info = {"returncode": returncode, "tests": None, "failures": None,
            "ignored": None, "results": results}
    if returncode != 0:
        problems.append(f"make test exited with code {returncode}")
    summary = SUMMARY.search(output)
    if summary is None:
        problems.append("no Unity summary line (build or run did not finish)")
    else:
        tests, failures, ignored = (int(x) for x in summary.groups())
        info.update(tests=tests, failures=failures, ignored=ignored)
        if tests == 0:
            problems.append("zero tests were executed")
        elif tests != len(expected):
            problems.append(f"{tests} tests executed, expected {len(expected)}")
        if failures:
            problems.append(f"{failures} test failure(s)")
        if ignored:
            problems.append(f"{ignored} test(s) ignored")
    for name in expected:
        if results.get(name) != "PASS":
            problems.append(f"{name}: {results.get(name, 'not run')}, "
                            "expected PASS")
    return problems, info


# --------------------------------------------------------------------------
# step 5: inputs, oracle, model
# --------------------------------------------------------------------------
def gen_matrix(pattern: str, rows: int, cols: int) -> bytes:
    if pattern == "worst":    # all equal: every cell is a row maximum
        return bytes([128]) * (rows * cols)
    if pattern == "best":     # [255, 0, 0, ...]: only column 1 is a maximum
        return (bytes([255]) + bytes(cols - 1)) * rows
    if pattern == "random":   # 64-bit LCG, fixed seed, top byte of the state
        out = bytearray(rows * cols)
        state = SEED
        for i in range(rows * cols):
            state = (state * 6364136223846793005 + 1442695040888963407) & M64
            out[i] = state >> 56
        # Plant one saddle point so the expected answer is never empty:
        # row r0 is halved (all <= 127), the cell (r0, c0) is set to 127,
        # and every other cell of column c0 gets its top bit set (>= 128).
        r0, c0 = planted_cell(rows, cols)
        for c in range(cols):
            out[r0 * cols + c] >>= 1
        out[r0 * cols + c0] = 127
        for r in range(rows):
            if r != r0:
                out[r * cols + c0] |= 0x80
        return bytes(out)
    raise ValueError(pattern)


def planted_cell(rows: int, cols: int) -> tuple[int, int]:
    """0-based cell of the planted saddle point in the random pattern."""
    return rows // 3, (2 * cols) // 3


def validate_input(rows: int, cols: int, data: bytes) -> list[str]:
    """The exercise's specification: a rectangular grid of uint8_t heights,
    plus the reference's own limit on indices (int16_t)."""
    problems = []
    if not (1 <= rows <= MAX_INDEX + 1 and 1 <= cols <= MAX_INDEX + 1):
        problems.append("dimensions outside 1..32768")
    if len(data) != rows * cols:
        problems.append("not rectangular: length != rows*columns")
    if not isinstance(data, bytes):
        problems.append("heights are not bytes (uint8_t)")
    return problems


def oracle_points(rows: int, cols: int, data: bytes):
    """Independent O(R*C) answer: largest in row and smallest in column,
    as 1-based (row, column) pairs in row-major order."""
    row_max = [max(data[r * cols:(r + 1) * cols]) for r in range(rows)]
    col_min = [min(data[c::cols]) for c in range(cols)]
    return [(r + 1, c + 1) for r in range(rows) for c in range(cols)
            if data[r * cols + c] == row_max[r] == col_min[c]]


def model_counts(rows: int, cols: int, data: bytes) -> dict:
    """Exact comparisons executed by is_greatest_in_row over all cells.

    For a cell with value v the loop stops at the first element > v, so it
    runs (index of that element + 1) comparisons, or `cols` when there is
    none. The first element > v is found with a prefix maximum."""
    cmps = true = 0
    lo, hi = None, 0
    for r in range(rows):
        row = data[r * cols:(r + 1) * cols]
        prefix_max = list(itertools.accumulate(row, max))
        for v in row:
            idx = bisect.bisect_right(prefix_max, v)
            k = cols if idx == cols else idx + 1
            true += idx == cols
            cmps += k
            lo = k if lo is None or k < lo else lo
            hi = max(hi, k)
    return {"calls": rows * cols, "cmps": cmps, "min_per_call": lo,
            "max_per_call": hi, "true": true}


def closed_form(pattern: str, rows: int, cols: int):
    if pattern == "worst":
        return {"cmps": rows * cols * cols, "min_per_call": cols,
                "max_per_call": cols, "true": rows * cols,
                "saddles": rows * cols}
    if pattern == "best":
        return {"cmps": rows * (2 * cols - 1), "min_per_call": 1,
                "max_per_call": cols, "true": rows, "saddles": rows}
    return None


# --------------------------------------------------------------------------
# step 5: building and running the harness
# --------------------------------------------------------------------------
def counted_source(text: str) -> str:
    """Add call and comparison counters inside is_greatest_in_row only."""
    m = re.search(r"static bool is_greatest_in_row\(.*?\n}\n", text, re.S)
    if m is None:
        sys.exit("is_greatest_in_row not found in the reference")
    body, n1 = re.subn(r"(uint8_t candidate = matrix\[row\]\[column\];)",
                       r"\1\n   ++g_calls;", m.group(0), count=1)
    body, n2 = re.subn(r"if \(matrix\[row\]\[c\] > candidate\)",
                       "if (++g_cmps, matrix[row][c] > candidate)", body)
    if (n1, n2) != (1, 1):
        sys.exit(f"counter patch did not apply exactly once: {n1}, {n2}")
    return text[:m.start()] + body + text[m.end():]


def build_harness(directory: Path, scratch: Path, files, pairs, counted: bool):
    directory.mkdir()
    for example, solution in pairs:
        src = (scratch / solution).read_text()
        if solution.endswith(".c") and counted:
            src = counted_source(src)
        (directory / Path(solution).name).write_text(src)
    shutil.copyfile(HERE / "harness.c", directory / "harness.c")
    flags = CFLAGS + (["-DCOUNT_OPS"] if counted else [])
    t0 = time.perf_counter()
    p = run([CC, *flags, "harness.c", "-o", "harness"], cwd=directory)
    ms = (time.perf_counter() - t0) * 1000
    if p.returncode != 0:
        sys.exit(f"harness build failed ({directory.name}):\n{p.stderr}")
    return directory / "harness", ms


def run_harness(exe: Path, mode: str, rows: int, cols: int, path: Path,
                reps: int = 1):
    t0 = time.perf_counter()
    p = run([str(exe), mode, str(rows), str(cols), str(path), str(reps)])
    wall_ms = (time.perf_counter() - t0) * 1000
    return p, parse_kv(p.stdout), wall_ms


# --------------------------------------------------------------------------
# step 6 helpers
# --------------------------------------------------------------------------
def comment_before_function(example_text: str) -> str:
    i = example_text.index("static bool is_greatest_in_row(")
    return example_text[:i]


def cpu_model(cpuinfo: str = "/proc/cpuinfo") -> str:
    """CPU name on Linux (/proc/cpuinfo) or macOS (sysctl); never raises."""
    try:
        for line in Path(cpuinfo).read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    try:
        p = run(["sysctl", "-n", "machdep.cpu.brand_string"], timeout=30)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return platform.processor() or platform.machine() or "unknown"


def tool_versions() -> str:
    def first_line(cmd):
        try:
            p = run(cmd, timeout=30)
            return (p.stdout or p.stderr).splitlines()[0]
        except Exception as exc:  # noqa: BLE001 - recorded, not hidden
            return f"unavailable ({exc})"

    unity = (EXERCISE / "test-framework" / "unity.h").read_text()
    uv = [re.search(rf"UNITY_VERSION_{k}\s+(\d+)", unity).group(1)
          for k in ("MAJOR", "MINOR", "BUILD")]
    cpu = cpu_model()
    commit = first_line(["git", "-C", str(REPO), "rev-parse", "HEAD"])
    lines = [
        f"generated   {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"compiler    {first_line([CC, '--version'])}",
        f"make        {first_line(['make', '--version'])}",
        f"python      {platform.python_version()} ({platform.python_implementation()})",
        f"unity       {'.'.join(uv)} (exercise test-framework/unity.h)",
        f"os          {platform.platform()}",
        f"cpu         {cpu} x{os.cpu_count()}",
        f"git HEAD    {commit}",
        f"harness     {' '.join([CC, *CFLAGS])}",
    ]
    return "\n".join(lines) + "\n"


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--reps", type=int, default=DEFAULT_REPS,
                    help=f"timed repetitions per case (>= {MIN_REPS})")
    ap.add_argument("--no-evidence", action="store_true",
                    help="run every check but do not rewrite evidence/ "
                         "(keeps the recorded timings)")
    args = ap.parse_args()
    if args.reps < MIN_REPS:
        ap.error(f"--reps must be at least {MIN_REPS}")

    chk = Checker()
    if not args.no_evidence:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
    expected_vs_actual: dict = {"task": TASK}
    inputs_record: list = []
    measurements: dict = {"reps": args.reps}

    before = manifest(EXERCISE)

    # ---- 1. config ------------------------------------------------------
    section("1. paths from .meta/config.json")
    files, pairs = load_config()
    for kind in ("solution", "test", "example"):
        for rel in files[kind]:
            chk.ok((EXERCISE / rel).is_file(), f"{kind}: {rel} exists")
    test_text = (EXERCISE / files["test"][0]).read_text()
    cases = expected_case_names(test_text)
    names = [n for _, n in cases]
    run_tests = re.findall(r"RUN_TEST\(\s*(\w+)\s*\)", test_text)
    chk.ok(len(cases) > 0, f"tests.toml lists {len(cases)} cases")
    chk.ok(all(names) and sorted(run_tests) == sorted(names),
           "every tests.toml case maps to exactly one RUN_TEST in the test file",
           f"unmatched={[d for d, n in cases if not n]} "
           f"file-only={sorted(set(run_tests) - set(names))}")

    with tempfile.TemporaryDirectory(prefix=f"{TASK.lower()}-") as tmpname:
        tmp = Path(tmpname)

        # ---- 2. learner stub is unsolved --------------------------------
        section("2. learner stub is still unsolved")
        stub_text = "".join((EXERCISE / s).read_text()
                            for s in files["solution"])
        chk.ok(not re.search(r"saddle_point_t|saddle_points_t|"
                             r"free_saddle_points", stub_text),
               "stub files declare nothing from the exercise API")
        g = run(["git", "-C", str(REPO), "rev-parse", "--is-inside-work-tree"])
        if g.returncode == 0:
            d = run(["git", "-C", str(REPO), "diff", "--quiet", "HEAD", "--",
                     *[str(EXERCISE / s) for s in files["solution"]]])
            chk.ok(d.returncode == 0, "stub files identical to git HEAD")
        stub_dir = scratch_copy(tmp, "stub", files, pairs, False, True)
        rc, out = make_test(stub_dir)
        problems, _ = evaluate_make_test(rc, out, names)
        chk.ok(rc != 0 and problems, "make test on the bare stub is rejected",
               f"rc={rc}")
        expected_vs_actual["unsolved_stub"] = {
            "expected": "make test fails to build", "actual_returncode": rc,
            "problems": problems}

        # ---- 3. reference passes every case -----------------------------
        section("3. reference: make test with every case enabled")
        ref_dir = scratch_copy(tmp, "reference", files, pairs, True, True)
        for example, solution in pairs:
            chk.ok((ref_dir / example).read_bytes() ==
                   (ref_dir / solution).read_bytes(),
                   f"{solution} in the copy is {example}")
        rc, out = make_test(ref_dir)
        if not args.no_evidence:
            (EVIDENCE / "make_test.log").write_text(out)
        problems, info = evaluate_make_test(rc, out, names)
        chk.ok(not problems, "make test clean", "; ".join(problems))
        chk.ok(info["tests"] == len(names) and info["tests"] > 0,
               f"executed cases: {info['tests']} (expected {len(names)})")
        for description, name in cases:
            chk.ok(info["results"].get(name) == "PASS",
                   f"case passed: {description}")
        expected_vs_actual["named_cases"] = [
            {"description": d, "function": n, "expected": "PASS",
             "actual": info["results"].get(n, "not run")} for d, n in cases]
        expected_vs_actual["test_counts"] = {
            "expected": len(names), "actual": info["tests"],
            "failures": info["failures"], "ignored": info["ignored"],
            "returncode": rc}

        # ---- 4. negative controls ---------------------------------------
        section("4. negative controls: the evaluator must reject these")
        controls = []

        zero = scratch_copy(tmp, "zero", files, pairs, True, True)
        zt = zero / files["test"][0]
        text, n = re.subn(r"RUN_TEST\(", "(void)(", zt.read_text())
        zt.write_text(text)
        rc, out = make_test(zero)
        problems, _ = evaluate_make_test(rc, out, names)
        chk.ok(n == len(names) and rc == 0 and
               "zero tests were executed" in problems,
               "zero-test run (exit 0) is reported", f"rc={rc} {problems}")
        controls.append({"name": "zero-test run", "returncode": rc,
                         "problems": problems})

        broken = scratch_copy(tmp, "broken", files, pairs, True, True)
        bc = broken / next(s for s in files["solution"] if s.endswith(".c"))
        text, n = re.subn(r"matrix\[row\]\[c\] > candidate",
                          "matrix[row][c] < candidate", bc.read_text())
        bc.write_text(text)
        rc, out = make_test(broken)
        problems, info_b = evaluate_make_test(rc, out, names)
        chk.ok(n == 1 and rc != 0 and (info_b["failures"] or 0) > 0 and
               problems, "wrong reference (comparison flipped) is reported",
               f"rc={rc} {problems}")
        controls.append({"name": "comparison flipped in is_greatest_in_row",
                         "returncode": rc, "problems": problems})

        controls.append({"name": "bare stub (step 2)",
                         "returncode": expected_vs_actual["unsolved_stub"]
                         ["actual_returncode"],
                         "problems": expected_vs_actual["unsolved_stub"]
                         ["problems"]})
        expected_vs_actual["negative_controls"] = controls

        # ---- 5. scaling study -------------------------------------------
        section("5. scaling study (sizes, patterns, correctness, counts)")
        plain, plain_ms = build_harness(tmp / "plain", ref_dir, files, pairs,
                                        False)
        counted, counted_ms = build_harness(tmp / "counted", ref_dir, files,
                                            pairs, True)
        measurements["compile_ms"] = {"plain": round(plain_ms, 1),
                                      "counted": round(counted_ms, 1)}
        chk.ok(True, "harness built (plain and counted), "
                     f"{plain_ms:.0f} ms and {counted_ms:.0f} ms to compile")

        # process start-up floor: a 1x1 grid, so the algorithm does 1 call
        one = tmp / "one.bin"
        one.write_bytes(bytes([7]))
        floor, floor_codes = [], []
        for _ in range(MIN_REPS):
            p, kv, wall = run_harness(plain, "sweep", 1, 1, one, 1)
            floor_codes.append(p.returncode)
            floor.append(wall)
        chk.ok(floor_codes == [0] * MIN_REPS,
               f"start-up baseline: {MIN_REPS} runs on a 1x1 grid exit 0",
               str(floor_codes))
        measurements["process_startup_floor_ms"] = {
            "median": round(statistics.median(floor), 2),
            "runs": [round(x, 2) for x in floor]}

        case_data = []
        correctness, op_counts = [], []
        for rows, cols in SIZES:
            for pattern in PATTERNS:
                cid = f"{pattern}-{rows}x{cols}"
                data = gen_matrix(pattern, rows, cols)
                path = tmp / f"{cid}.bin"
                path.write_bytes(data)
                bad = validate_input(rows, cols, data)
                chk.ok(not bad, f"{cid}: input satisfies the specification",
                       "; ".join(bad))
                inputs_record.append({
                    "id": cid, "pattern": pattern, "rows": rows,
                    "columns": cols, "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "generator": {
                        "worst": "every cell 128",
                        "best": "every row is [255, 0, 0, ..., 0]",
                        "random": f"64-bit LCG seed {SEED}, top byte of "
                                  "state, row-major; one planted saddle "
                                  "point of height 127 at "
                                  f"(row {planted_cell(rows, cols)[0] + 1}, "
                                  f"column {planted_cell(rows, cols)[1] + 1})"
                        }[pattern]})
                case_data.append((cid, pattern, rows, cols, path, data))

        # phase A: correctness and operation counts for every case
        for cid, pattern, rows, cols, path, data in case_data:
            points = oracle_points(rows, cols, data)
            exp_count, exp_hash = len(points), points_hash(points)
            chk.ok(exp_count > 0, f"{cid}: expected answer is not empty "
                                  f"({exp_count} saddle points)")
            cf = closed_form(pattern, rows, cols)
            if cf:
                chk.ok(exp_count == cf["saddles"],
                       f"{cid}: oracle agrees with closed form "
                       f"({exp_count} saddle points)")
            if pattern == "random":
                r0, c0 = planted_cell(rows, cols)
                planted = (r0 + 1, c0 + 1)
                chk.ok(planted in points,
                       f"{cid}: oracle finds the planted saddle point "
                       f"at {planted}")
            record = {"case": cid, "expected": {
                "count": exp_count, "hash": f"{exp_hash:016x}"}}
            for label, exe in (("plain", plain), ("counted", counted)):
                p, kv, _ = run_harness(exe, "solve", rows, cols, path)
                got = (kv.get("count"), kv.get("hash"))
                good = (p.returncode == 0 and
                        got == (str(exp_count), f"{exp_hash:016x}"))
                chk.ok(good, f"{cid}: saddle_points() correct ({label} build)",
                       f"rc={p.returncode} got={got} "
                       f"want={(exp_count, f'{exp_hash:016x}')} {p.stderr}")
                record[label] = {"count": got[0], "hash": got[1]}
                if label == "counted":
                    solve_calls, solve_cmps = (int(kv.get("calls", -1)),
                                               int(kv.get("cmps", -1)))
            correctness.append(record)

            model = model_counts(rows, cols, data)
            p, kv, _ = run_harness(counted, "sweep", rows, cols, path)
            actual = {"calls": int(kv.get("sweep_calls", -1)),
                      "cmps": int(kv.get("sweep_cmps", -1)),
                      "min_per_call": int(kv.get("sweep_min_per_call", -1)),
                      "max_per_call": int(kv.get("sweep_max_per_call", -1)),
                      "true": int(kv.get("true", -1))}
            chk.ok(p.returncode == 0 and actual == model,
                   f"{cid}: measured counts equal the model "
                   f"({actual['cmps']:,} comparisons)",
                   f"rc={p.returncode} actual={actual} model={model}")
            chk.ok((solve_calls, solve_cmps) == (rows * cols, model["cmps"]),
                   f"{cid}: real saddle_points() makes {rows * cols:,} calls "
                   "and the same comparisons",
                   f"calls={solve_calls} cmps={solve_cmps}")
            if cf:
                chk.ok(all(model[k] == cf[k] for k in
                           ("cmps", "min_per_call", "max_per_call", "true")),
                       f"{cid}: model equals closed form",
                       f"model={model} closed={cf}")
            chk.ok(1 <= model["min_per_call"] and model["max_per_call"] <= cols,
                   f"{cid}: every call does between 1 and C={cols} "
                   "comparisons")
            lower, upper = rows * (2 * cols - 1), rows * cols * cols
            chk.ok(lower <= model["cmps"] <= upper,
                   f"{cid}: total within R(2C-1)..R*C^2 = "
                   f"{lower:,}..{upper:,}")
            op_counts.append({
                "case": cid, "rows": rows, "columns": cols,
                "model": model, "closed_form": cf, "measured_sweep": actual,
                "measured_real_saddle_points": {
                    "calls": solve_calls, "cmps": solve_cmps},
                "bounds": {"lower_R(2C-1)": lower, "upper_R*C^2": upper}})

        expected_vs_actual["correctness"] = correctness
        expected_vs_actual["operation_counts"] = op_counts

        # phase B: timing, only if every assertion so far held
        section("6. timing (in-process, sweep only)")
        timings = []
        if chk.failed:
            print("  skipped: an earlier assertion failed, so no timings are "
                  "taken or reported")
        else:
            for cid, pattern, rows, cols, path, data in case_data:
                model = next(o["model"] for o in op_counts if o["case"] == cid)
                p, kv, wall = run_harness(plain, "sweep", rows, cols, path,
                                          args.reps)
                ns = [int(x) for x in kv.get("ns", "").split(",") if x]
                good = (p.returncode == 0 and len(ns) == args.reps and
                        all(x > 0 for x in ns) and
                        int(kv.get("true", -1)) == model["true"])
                chk.ok(good, f"{cid}: {args.reps} timed repetitions, result "
                             "unchanged", f"rc={p.returncode} {p.stderr}")
                if good:
                    timings.append({
                        "case": cid, "rows": rows, "columns": cols,
                        "pattern": pattern, "comparisons": model["cmps"],
                        "reps": len(ns), "ns": ns,
                        "median_ms": round(statistics.median(ns) / 1e6, 3),
                        "min_ms": round(min(ns) / 1e6, 3),
                        "max_ms": round(max(ns) / 1e6, 3),
                        "ns_per_comparison_median": round(
                            statistics.median(ns) / model["cmps"], 3),
                        "process_wall_ms_all_reps": round(wall, 1)})
            measurements["timings"] = timings

    # ---- 7. hygiene, comment, doc ----------------------------------------
    section("7. working tree, source comment, documentation")
    after = manifest(EXERCISE)
    chk.ok(before == after, "exercise directory unchanged by this check")
    example_text = (EXERCISE / ".meta" / "example.c").read_text()
    comment = comment_before_function(example_text).rstrip()
    chk.ok(comment.endswith("*/") and "is_greatest_in_row" in comment and
           re.search(r"best case:\s+1 comparison", comment) and
           re.search(r"worst case:\s+C comparisons", comment) and
           "R * (2C - 1)" in comment and "R * C * C" in comment,
           "example.c: comment next to is_greatest_in_row states the bounds")
    if chk.ok(DOC.is_file(), f"{DOC.relative_to(REPO)} exists"):
        doc = DOC.read_text()
        missing = [f"{o['model']['cmps']:,}" for o in op_counts
                   if f"{o['model']['cmps']:,}" not in doc]
        chk.ok(not missing, "doc quotes every measured comparison count",
               f"missing {missing}")
        chk.ok("int16_t" in doc and "32767" in doc.replace(",", ""),
               "doc states the supported input size limit")

    # ---- evidence ----------------------------------------------------------
    if not args.no_evidence:
        write_json(EVIDENCE / "inputs.json", inputs_record)
        write_json(EVIDENCE / "expected_vs_actual.json", expected_vs_actual)
        write_json(EVIDENCE / "measurements.json", measurements)
        (EVIDENCE / "tool_versions.txt").write_text(tool_versions())

    # ---- summary -----------------------------------------------------------
    section("summary")
    if measurements.get("timings"):
        floor_ms = measurements["process_startup_floor_ms"]["median"]
        print(f"  compile: {measurements['compile_ms']['plain']} ms; "
              f"process start-up floor: {floor_ms} ms (1x1 grid)")
        print(f"  {'case':<18}{'comparisons':>14}{'median ms':>11}"
              f"{'min':>9}{'max':>9}{'ns/cmp':>8}")
        for t in measurements["timings"]:
            print(f"  {t['case']:<18}{t['comparisons']:>14,}"
                  f"{t['median_ms']:>11.3f}{t['min_ms']:>9.3f}"
                  f"{t['max_ms']:>9.3f}{t['ns_per_comparison_median']:>8.2f}")
    executed = expected_vs_actual["test_counts"]["actual"]
    print(f"\n  exercise test cases executed: {executed}")
    print(f"  assertions passed: {chk.passed}, failed: {len(chk.failed)}")
    if chk.failed:
        print("\nR48-T005 check FAILED:")
        for label in chk.failed:
            print(f"  - {label}")
        return 1
    print("\nR48-T005 check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
