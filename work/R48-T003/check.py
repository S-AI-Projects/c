#!/usr/bin/env python3
"""R48-T003 acceptance check: mutation-driven regression for palindrome-products.

Run from anywhere inside the repository:

    python3 work/R48-T003/check.py

Exit codes: 0 = every assertion passed, 1 = at least one assertion failed,
2 = a prerequisite (Python 3.11+, cc, make) is missing and nothing could be judged.

What it does
------------
The documented mutant M1 deletes the "a number ending in 0 is not a palindrome" guard
from `palindrome()` in `.meta/example.c`. Everything happens in temporary copies of the
exercise (hidden files included); the working tree is never written to, except for the
evidence files under work/R48-T003/evidence/.

 1. Resolve solution/test/example paths from `.meta/config.json`; cross-check the test
    file against `.meta/tests.toml`.
 2. Original reference, all TEST_IGNORE lines disabled: `make test` must exit 0 and run
    every case (the count is reported; zero tests is a failure).
 3. Learner stub, same scratch setup: must NOT pass (it is still unsolved).
 4. Controls proving the harness itself fails correctly: a zero-test run, a non-zero
    child exit and an assertion failure are each rejected.
 5. Mutant M1 against the existing suite: must fail the named test with the named
    expected/actual values. Formatting-only changes are rejected as mutations.
 6. Differential run: original vs mutant on identical inputs, compared with an explicit
    expected result and an independent oracle written from the instructions. The smallest
    differing input is searched, not assumed.
 7. Other mutants (M2, M9, M12) that the existing suite does NOT reject, each with a
    proposed case (explicit input and expected result) that does separate them.
 8. Observation (informational only, never a failure): ranges where the reference reports
    "no palindrome" although the oracle finds one.
 9. The hint and the maintenance page agree with the evidence, and the hint does not
    reproduce the reference solution.
10. The original exercise directory is byte-for-byte unchanged.

Only the standard library is used. Child processes are started without a shell and every
return code is checked.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

sys.dont_write_bytecode = True

try:
    import tomllib
except ImportError:  # pragma: no cover - Python < 3.11
    tomllib = None  # type: ignore[assignment]

SLUG = "palindrome-products"
WORK = Path("work") / "R48-T003"
DRIVER = "diagnostic_driver.c"
HINTS = Path("exercises") / "practice" / SLUG / ".docs" / "hints.md"
MAINTENANCE = Path("docs") / "maintenance" / "palindrome-products.md"
SEARCH_MAX = 60  # minimal-input search domain: ranges with 0 <= min <= max <= SEARCH_MAX
MAX_MUTATION_TOKENS = 20
COMMAND_TIMEOUT = 180
EXIT_OK, EXIT_FAIL, EXIT_SETUP = 0, 1, 2

NAMED_TEST = "test_largest_palindrome_from_single_digit_factors"
NAMED_UUID = "0853f82c-5fc4-44ae-be38-fadb2cced92d"
NAMED_DESCRIPTION = "find the largest palindrome from single digit factors"
NAMED_ASSERTION = "Expected 9 Was 40"

ANSI = re.compile(r"\x1b\[[0-9;]*m")
UNITY_SUMMARY = re.compile(r"(\d+) Tests (\d+) Failures (\d+) Ignored")
UNITY_FAIL = re.compile(r"^(?:\./)?(\S+\.c):(\d+):(test_\w+):FAIL: (.*)$", re.MULTILINE)

Result = tuple  # ("OK", smallest, ((a, b), ...), largest, ((a, b), ...)) or ("ERROR", message)


class SetupError(Exception):
    """A prerequisite is missing; the check cannot run (exit code 2)."""


def ok(smallest: int, sm: list, largest: int, lg: list) -> Result:
    return ("OK", smallest, tuple(sorted(sm)), largest, tuple(sorted(lg)))


def err(message: str) -> Result:
    return ("ERROR", message)


def show(result: Result) -> str:
    if result[0] == "ERROR":
        return f"ERROR {result[1]!r}"
    _, s, sm, lg_value, lg = result
    fmt = lambda pairs: "{" + ", ".join(f"{a}x{b}" for a, b in pairs) + "}"  # noqa: E731
    return f"smallest={s} {fmt(sm)}  largest={lg_value} {fmt(lg)}"


# --------------------------------------------------------------------------- #
# The mutants. `old` must match exactly once in .meta/example.c (whitespace-insensitive).
# `expected` is written out by hand from the instructions, not copied from any run.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Mutant:
    id: str
    title: str
    old: str
    new: str
    min_floor: int  # smallest `min` allowed in the minimal-input search
    probe: tuple
    expected: Result
    mutant_actual: Result  # what the mutant is documented to return on `probe`
    rejected_by: Optional[str]  # existing Unity test that must reject it; None = survives


M1 = Mutant(
    id="M1",
    title="numbers ending in 0 are accepted as palindromes (trailing-zero guard removed)",
    old="if ((tail = n % 10) == 0)\n      return false;\n   n /= 10;",
    new="tail = n % 10;\n   n /= 10;",
    min_floor=1,
    probe=(2, 5),
    expected=ok(4, [(2, 2)], 9, [(3, 3)]),
    mutant_actual=ok(4, [(2, 2)], 20, [(4, 5)]),
    rejected_by=NAMED_TEST,
)
SURVIVORS = [
    Mutant(
        id="M2",
        title="0 is not a palindrome",
        old="if (n == 0)\n      return true;",
        new="if (n == 0)\n      return false;",
        min_floor=0,
        probe=(0, 1),
        expected=ok(0, [(0, 0), (0, 1)], 1, [(1, 1)]),
        mutant_actual=err("no palindrome with factors in the range 0 to 1"),
        rejected_by=None,
    ),
    Mutant(
        id="M9",
        title="only the first factor pair is kept for the smallest palindrome",
        old="if (n <= result->smallest) {",
        new="if (n < result->smallest) {",
        min_floor=1,
        probe=(12, 21),
        expected=ok(252, [(12, 21), (14, 18)], 323, [(17, 19)]),
        mutant_actual=ok(252, [(12, 21)], 323, [(17, 19)]),
        rejected_by=None,
    ),
    Mutant(
        id="M12",
        title="the square of the upper bound is never tried",
        old="for (i = from; i <= to; i++)",
        new="for (i = from; i < to; i++)",
        min_floor=1,
        probe=(1, 2),
        expected=ok(1, [(1, 1)], 4, [(2, 2)]),
        mutant_actual=ok(1, [(1, 1)], 2, [(1, 2)]),
        rejected_by=None,
    ),
]
ALL_MUTANTS = [M1, *SURVIVORS]


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
class Reporter:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.lines: list[str] = []

    def _emit(self, line: str) -> None:
        self.lines.append(line)
        print(line)

    def section(self, title: str) -> None:
        self._emit(f"\n== {title} ==")

    def info(self, message: str) -> None:
        self._emit(f"[INFO] {message}")

    def note(self, message: str) -> None:
        self._emit(f"[NOTE] {message}")

    def check(self, condition: bool, name: str, detail_ok: str = "", detail_fail: str = "") -> bool:
        if condition:
            self._emit(f"[PASS] {name}" + (f": {detail_ok}" if detail_ok else ""))
        else:
            self.failures.append(name)
            self._emit(f"[FAIL] {name}: {detail_fail}")
        return condition


# --------------------------------------------------------------------------- #
# Subprocess and filesystem helpers
# --------------------------------------------------------------------------- #
@dataclass
class Proc:
    argv: list
    rc: int
    out: str  # stdout + stderr, ANSI stripped


def run(argv: list, *, cwd: Optional[Path] = None, stdin: Optional[str] = None) -> Proc:
    """Run argv without a shell. Callers must look at `.rc`."""
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            input=stdin,
            stdin=None if stdin is not None else subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SetupError(f"cannot execute {argv[0]!r}: {exc}") from exc
    except subprocess.TimeoutExpired:
        return Proc(argv, 124, f"timed out after {COMMAND_TIMEOUT}s")
    return Proc(argv, proc.returncode, ANSI.sub("", proc.stdout + proc.stderr))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root: Path) -> dict:
    """relative path -> sha256, hidden files included."""
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


def find_repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "exercises" / "practice" / SLUG / ".meta" / "config.json").is_file():
            return candidate
    raise SetupError("cannot find the repository root (no exercises/practice/palindrome-products above this file)")


@dataclass
class Exercise:
    directory: Path
    solution: list
    test: list
    example: list
    pairs: dict  # example path -> solution path


def resolve_exercise(root: Path) -> Exercise:
    directory = root / "exercises" / "practice" / SLUG
    config_path = directory / ".meta" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    lists = {}
    for key in ("solution", "test", "example"):
        value = config.get("files", {}).get(key)
        if not (isinstance(value, list) and value and all(isinstance(v, str) for v in value)):
            raise SetupError(f"{config_path}: files.{key} must be a non-empty list of strings")
        for item in value:
            if Path(item).is_absolute() or ".." in Path(item).parts:
                raise SetupError(f"{config_path}: files.{key} entry {item!r} escapes the exercise")
            if key != "solution" and not (directory / item).is_file():
                raise SetupError(f"{config_path} lists {item!r} but it does not exist")
        lists[key] = value
    pairs = {}
    for example in lists["example"]:
        partners = [s for s in lists["solution"] if Path(s).suffix == Path(example).suffix]
        if len(partners) != 1:
            raise SetupError(f"cannot pair {example!r} with exactly one solution file (got {partners})")
        pairs[example] = partners[0]
    return Exercise(directory, lists["solution"], lists["test"], lists["example"], pairs)


def c_source_of(ex: Exercise, suffix: str = ".c") -> str:
    """The solution path (relative) that ends with `suffix`."""
    return next(s for s in ex.solution if s.endswith(suffix))


def make_scratch(parent: Path, ex: Exercise, *, reference: bool) -> Path:
    """Copy the exercise (dotfiles included). Optionally substitute the reference in the COPY."""
    scratch = parent / SLUG
    shutil.copytree(ex.directory, scratch, symlinks=True)
    for stale in scratch.glob("*.out"):
        stale.unlink()
    if reference:
        for example, solution in ex.pairs.items():
            shutil.copyfile(scratch / example, scratch / solution)
    return scratch


def enable_all_tests(test_file: Path) -> tuple:
    """Comment out every TEST_IGNORE(); like the track's root makefile. Returns (disabled, RUN_TESTs)."""
    text = test_file.read_text(encoding="utf-8")
    text, disabled = re.subn(r"^(\s*)TEST_IGNORE\(\);", r"\1// TEST_IGNORE();", text, flags=re.MULTILINE)
    if re.search(r"^\s*TEST_IGNORE\(\);", text, flags=re.MULTILINE):
        raise SetupError(f"{test_file.name}: a live TEST_IGNORE() remains after enabling all tests")
    test_file.write_text(text, encoding="utf-8")
    return disabled, len(re.findall(r"^\s*RUN_TEST\(", text, flags=re.MULTILINE))


def mutate_text(text: str, mutant: Mutant) -> str:
    """Replace the single place where `mutant.old` occurs, ignoring differences in whitespace.

    A reformat of example.c (the track runs clang-format) must not silently disable the
    mutation, so tokens are matched with `\\s*` between them. Exactly one match is required.
    """
    tokens = re.findall(r"\w+|[^\s\w]", mutant.old)
    pattern = re.compile(r"\s*".join(re.escape(t) for t in tokens))
    found = pattern.findall(text)
    if len(found) != 1:
        raise SetupError(f"{mutant.id}: the mutation target occurs {len(found)} times in the reference, expected 1 "
                         f"(target: {mutant.old!r})")
    return pattern.sub(lambda _m: mutant.new, text, count=1)


def apply_mutation(scratch: Path, ex: Exercise, mutant: Mutant) -> tuple:
    """Mutate the reference in the scratch copy. Returns (original_text, mutated_text)."""
    path = scratch / c_source_of(ex)
    before = path.read_text(encoding="utf-8")
    after = mutate_text(before, mutant)
    path.write_text(after, encoding="utf-8")
    return before, after


def code_tokens(text: str) -> list:
    """C tokens with comments and whitespace removed, so formatting-only edits compare equal."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", " ", text)
    return re.findall(r"\w+|[^\s\w]", text)


def changed_token_count(before: str, after: str) -> int:
    a, b = code_tokens(before), code_tokens(after)
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal")


def make_test(scratch: Path) -> Proc:
    return run(["make", "--no-print-directory", "-C", str(scratch), "test"])


def unity_summary(out: str) -> Optional[tuple]:
    m = UNITY_SUMMARY.search(out)
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


def judge(proc: Proc, expected_tests: int) -> list:
    """Every reason a `make test` run must be rejected. Empty list = clean pass."""
    problems = []
    summary = unity_summary(proc.out)
    if proc.rc != 0:
        problems.append(f"child exit code {proc.rc}")
    if summary is None:
        problems.append("no Unity summary line (nothing was executed)")
        return problems
    tests, failures, ignored = summary
    if tests == 0:
        problems.append("zero tests executed")
    elif tests != expected_tests:
        problems.append(f"executed {tests} tests but the test file has {expected_tests} RUN_TEST calls")
    if failures:
        problems.append(f"{failures} assertion failure(s)")
    if ignored:
        problems.append(f"{ignored} test(s) ignored")
    return problems


def failing_tests(out: str) -> dict:
    return {m[3]: m[4] for m in UNITY_FAIL.finditer(out)}


# --------------------------------------------------------------------------- #
# Oracle, driver and result parsing
# --------------------------------------------------------------------------- #
def oracle(lo: int, hi: int) -> Result:
    """Independent reading of instructions.md: every palindromic product, all factor pairs."""
    if lo > hi:
        return err(f"invalid input: min is {lo} and max is {hi}")
    palindromes: dict = {}
    for i in range(lo, hi + 1):
        for k in range(i, hi + 1):
            n = i * k
            if str(n) == str(n)[::-1]:
                palindromes.setdefault(n, []).append((i, k))
    if not palindromes:
        return err(f"no palindrome with factors in the range {lo} to {hi}")
    s, g = min(palindromes), max(palindromes)
    return ok(s, palindromes[s], g, palindromes[g])


def _pairs(text: str) -> list:
    return [tuple(sorted(map(int, p.split("*")))) for p in text.split(",")] if text else []


def parse_driver_line(line: str) -> tuple:
    m = re.match(r"(-?\d+) (-?\d+) (OK|ERROR|NULL)\s*(.*)$", line)
    if not m:
        raise ValueError(f"unparseable driver output: {line!r}")
    key = (int(m[1]), int(m[2]))
    if m[3] == "OK":
        g = re.match(r"smallest=(-?\d+) sm=(\S*) largest=(-?\d+) lg=(\S*)$", m[4])
        if not g:
            raise ValueError(f"unparseable driver output: {line!r}")
        return key, ok(int(g[1]), _pairs(g[2]), int(g[3]), _pairs(g[4]))
    return key, err(m[4] if m[3] == "ERROR" else "NULL result")


def search_ranges() -> list:
    """All ranges 0 <= min <= max <= SEARCH_MAX, ordered by max, then by width (narrowest first)."""
    return [(lo, hi) for hi in range(SEARCH_MAX + 1) for lo in range(hi, -1, -1)]


def build_driver(tmp: Path, name: str, root: Path, ex: Exercise, mutant: Optional[Mutant]) -> Path:
    build = tmp / f"driver-{name}"
    build.mkdir()
    for example, solution in ex.pairs.items():
        shutil.copyfile(ex.directory / example, build / Path(solution).name)
    if mutant is not None:
        source = build / Path(c_source_of(ex)).name
        source.write_text(mutate_text(source.read_text(encoding="utf-8"), mutant), encoding="utf-8")
    shutil.copyfile(root / WORK / DRIVER, build / DRIVER)
    cc = run(["cc", "-std=c99", "-Wall", "-Wextra", "-pedantic", "-Werror", "-Wmissing-declarations",
              DRIVER, Path(c_source_of(ex)).name, "-o", "driver", "-lm"], cwd=build)
    if cc.rc != 0:
        raise SetupError(f"driver for {name} failed to compile:\n{cc.out}")
    return build / "driver"


def run_driver(exe: Path, ranges: list) -> dict:
    proc = run([str(exe)], stdin="".join(f"{lo} {hi}\n" for lo, hi in ranges))
    if proc.rc != 0:
        raise SetupError(f"driver {exe.parent.name} exited with {proc.rc}:\n{proc.out[-800:]}")
    results = dict(parse_driver_line(line) for line in proc.out.splitlines())
    if set(results) != set(ranges):
        raise SetupError(f"driver {exe.parent.name} answered {len(results)} of {len(ranges)} ranges")
    return results


def smallest_difference(ranges: list, original: dict, mutant: dict, floor: int) -> Optional[tuple]:
    """First range (max, then width) where the mutant differs from a reference that agrees with the oracle."""
    for lo, hi in ranges:
        if lo < floor or original[(lo, hi)] == mutant[(lo, hi)]:
            continue
        if original[(lo, hi)] == oracle(lo, hi):
            return (lo, hi)
    return None


# --------------------------------------------------------------------------- #
# Evidence
# --------------------------------------------------------------------------- #
class Evidence:
    def __init__(self) -> None:
        self.files: dict = {}

    def add(self, name: str, content: str) -> None:
        self.files[name] = content if content.endswith("\n") else content + "\n"

    def add_json(self, name: str, data: object) -> None:
        self.add(name, json.dumps(data, indent=2, sort_keys=True))

    def write(self, directory: Path) -> None:
        if directory.exists():
            shutil.rmtree(directory)
        for name, content in self.files.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


def log_text(label: str, proc: Proc, scratch: Path) -> str:
    cleaned = proc.out.replace(str(scratch), "<SCRATCH>")
    cleaned = re.sub(r"\S*/cc\w{6}\.o", "<LINKER-TEMP>.o", cleaned)  # gcc's random temp object name
    return f"# {label}\n$ make --no-print-directory -C <SCRATCH> test\nexit code: {proc.rc}\n{cleaned}"


def tool_versions(ex: Exercise) -> str:
    first = lambda p: (p.out.splitlines() or ["unknown"])[0]  # noqa: E731
    lines = [f"python: {sys.version.split()[0]}", f"cc: {first(run(['cc', '--version']))}",
             f"make: {first(run(['make', '--version']))}"]
    unity = (ex.directory / "test-framework" / "unity.h").read_text(encoding="utf-8", errors="replace")
    parts = {k: re.search(rf"#define\s+UNITY_VERSION_{k}\s+(\d+)", unity) for k in ("MAJOR", "MINOR", "BUILD")}
    if all(parts.values()):
        lines.append("unity: " + ".".join(parts[k][1] for k in ("MAJOR", "MINOR", "BUILD")))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# The checks
# --------------------------------------------------------------------------- #
def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="R48-T003 acceptance check for palindrome-products.")
    parser.add_argument("--evidence-dir", help="evidence directory (default: work/R48-T003/evidence)")
    parser.add_argument("--no-evidence", action="store_true", help="do not write evidence files")
    args = parser.parse_args(argv)

    try:
        if tomllib is None:
            raise SetupError("Python 3.11+ is required (stdlib tomllib)")
        for tool in ("cc", "make"):
            if shutil.which(tool) is None:
                raise SetupError(f"`{tool}` not found on PATH")
        root = find_repo_root()
        ex = resolve_exercise(root)
        report = Reporter()
        evidence = Evidence()
        with tempfile.TemporaryDirectory(prefix="r48-t003-") as tmp_name:
            tmp = Path(tmp_name)
            if root.resolve() in tmp.resolve().parents:
                raise SetupError("scratch directory is inside the repository")
            execute_checks(root, ex, tmp, report, evidence)
    except SetupError as exc:
        print(f"[ERROR] prerequisite missing or unusable: {exc}", file=sys.stderr)
        return EXIT_SETUP

    if not args.no_evidence:
        evidence_dir = Path(args.evidence_dir) if args.evidence_dir else root / WORK / "evidence"
        evidence.add("summary.txt", "\n".join(report.lines).lstrip("\n")
                     + f"\n\nRESULT: {'PASS' if not report.failures else 'FAIL'}")
        evidence.write(evidence_dir)
    if report.failures:
        print(f"\nRESULT: FAIL ({len(report.failures)} failed check(s))")
        for name in report.failures:
            print(f"  - {name}")
        return EXIT_FAIL
    print("\nRESULT: PASS")
    return EXIT_OK


def execute_checks(root: Path, ex: Exercise, tmp: Path, rep: Reporter, evidence: Evidence) -> None:
    before = manifest(ex.directory)
    test_rel = ex.test[0]
    test_text = (ex.directory / test_rel).read_text(encoding="utf-8")
    run_test_calls = len(re.findall(r"^\s*RUN_TEST\(", test_text, flags=re.MULTILINE))

    # ---- 1. configuration ------------------------------------------------- #
    rep.section("1. Exercise files resolved from .meta/config.json")
    rep.info("solution: " + ", ".join(ex.solution))
    rep.info("test:     " + ", ".join(ex.test))
    rep.info("example:  " + ", ".join(f"{e} -> {s}" for e, s in ex.pairs.items()))
    cases = tomllib.loads((ex.directory / ".meta" / "tests.toml").read_text(encoding="utf-8"))
    included = [u for u, t in cases.items() if t.get("include", True)]
    rep.check(len(included) == run_test_calls and run_test_calls > 0,
              "tests.toml includes one case per RUN_TEST in the test file",
              f"{len(included)} == {run_test_calls}",
              f"tests.toml includes {len(included)} case(s) but the test file has {run_test_calls} RUN_TEST calls")
    rep.check(cases.get(NAMED_UUID, {}).get("description") == NAMED_DESCRIPTION,
              "named test ID exists in tests.toml with the expected description",
              f"{NAMED_UUID} = {NAMED_DESCRIPTION!r}",
              f"{NAMED_UUID} is missing or its description changed")
    rep.check(f"static void {NAMED_TEST}(void)" in test_text and f"RUN_TEST({NAMED_TEST})" in test_text,
              "named test function is defined and run in the test file", NAMED_TEST,
              f"{NAMED_TEST} not found in {test_rel}")

    # ---- 2. original reference ------------------------------------------- #
    rep.section("2. Maintained reference passes every enabled case")
    d = tmp / "original"
    d.mkdir()
    scratch = make_scratch(d, ex, reference=True)
    disabled, runs = enable_all_tests(scratch / test_rel)
    rep.info(f"scratch copy: reference substituted, {disabled} TEST_IGNORE line(s) disabled, {runs} RUN_TEST calls")
    original_proc = make_test(scratch)
    problems = judge(original_proc, run_test_calls)
    summary = unity_summary(original_proc.out)
    rep.check(not problems, "`make test` exits 0 and every case passes",
              f"executed {summary[0]} case(s), {summary[1]} failures, {summary[2]} ignored" if summary else "",
              "; ".join(problems) + "\n" + original_proc.out[-1200:])
    executed_original = summary[0] if summary else 0
    evidence.add("logs/original-make-test.log", log_text("original reference, all cases enabled", original_proc, scratch))

    # ---- 3. learner stub -------------------------------------------------- #
    rep.section("3. Learner stub is still unsolved")
    d = tmp / "stub"
    d.mkdir()
    scratch = make_scratch(d, ex, reference=False)
    enable_all_tests(scratch / test_rel)
    stub_proc = make_test(scratch)
    stub_summary = unity_summary(stub_proc.out)
    stub_passes = stub_proc.rc == 0 and stub_summary is not None and stub_summary[0] > 0 and stub_summary[1] == 0
    rep.check(stub_proc.rc != 0 and not stub_passes, "stub fails the full suite (it is not a solution)",
              f"`make test` exit code {stub_proc.rc}", "the unmodified stub passes, so it looks solved")
    evidence.add("logs/learner-stub-make-test.log", log_text("learner stub, all cases enabled", stub_proc, scratch))

    # ---- 4. controls for the harness itself -------------------------------- #
    rep.section("4. The harness rejects a zero-test run, a failing child process and an assertion failure")
    d = tmp / "control-zero"
    d.mkdir()
    scratch = make_scratch(d, ex, reference=True)
    enable_all_tests(scratch / test_rel)
    zero_file = scratch / test_rel
    zero_file.write_text(re.sub(r"RUN_TEST\((\w+)\);", r"(void)\1;", zero_file.read_text(encoding="utf-8")),
                         encoding="utf-8")
    zero_proc = make_test(scratch)
    zero_problems = judge(zero_proc, run_test_calls)
    rep.check(any("zero tests" in p for p in zero_problems) and unity_summary(zero_proc.out) == (0, 0, 0),
              "zero-test run is rejected", f"child exit {zero_proc.rc}, but: {'; '.join(zero_problems)}",
              f"not rejected as a zero-test run (problems: {zero_problems})")
    d = tmp / "control-exit"
    d.mkdir()
    scratch = make_scratch(d, ex, reference=True)
    enable_all_tests(scratch / test_rel)
    with (scratch / c_source_of(ex)).open("a", encoding="utf-8") as handle:
        handle.write("\nthis line is not C;\n")
    exit_proc = make_test(scratch)
    exit_problems = judge(exit_proc, run_test_calls)
    rep.check(exit_proc.rc != 0 and any("child exit code" in p for p in exit_problems),
              "non-zero child exit is rejected (build error control)", "; ".join(exit_problems),
              f"not rejected (rc={exit_proc.rc}, problems={exit_problems})")

    # ---- 5. mutant M1 against the existing suite -------------------------- #
    rep.section(f"5. Mutant {M1.id}: {M1.title}")
    d = tmp / "mutant-m1"
    d.mkdir()
    scratch = make_scratch(d, ex, reference=True)
    src_before, src_after = apply_mutation(scratch, ex, M1)
    changed = changed_token_count(src_before, src_after)
    rep.check(code_tokens(src_before) != code_tokens(src_after) and 0 < changed <= MAX_MUTATION_TOKENS,
              "mutation changes code, not just formatting or comments, and stays small",
              f"{changed} token(s) changed", f"token change count {changed} (limit {MAX_MUTATION_TOKENS})")
    mutation_diff = "".join(difflib.unified_diff(src_before.splitlines(True), src_after.splitlines(True),
                                                 "reference/example.c", "mutant/example.c", n=2))
    evidence.add("mutation-M1.diff", mutation_diff)
    enable_all_tests(scratch / test_rel)
    mutant_proc = make_test(scratch)
    mutant_problems = judge(mutant_proc, run_test_calls)
    mutant_summary = unity_summary(mutant_proc.out)
    failing = failing_tests(mutant_proc.out)
    rep.check(mutant_proc.rc != 0 and mutant_summary is not None and mutant_summary[0] == executed_original
              and mutant_summary[1] > 0,
              "mutant fails the suite: non-zero exit and the same number of cases executed",
              f"exit {mutant_proc.rc}; executed {mutant_summary[0]} case(s), {mutant_summary[1]} failed",
              f"exit {mutant_proc.rc}; summary {mutant_summary}; problems {mutant_problems}")
    rep.check(NAMED_TEST in failing and NAMED_ASSERTION in failing.get(NAMED_TEST, ""),
              f"mutant fails the named case {NAMED_UUID[:8]} ({NAMED_TEST})",
              f"{failing.get(NAMED_TEST)!r}",
              f"named test not among failures {sorted(failing)}, or wrong message {failing.get(NAMED_TEST)!r}")
    others = sorted(t for t in failing if t != NAMED_TEST)
    rep.info(f"other cases that also reject {M1.id}: {', '.join(t.removeprefix('test_') for t in others) or 'none'}")
    evidence.add("logs/mutant-M1-make-test.log", log_text("mutant M1, all cases enabled", mutant_proc, scratch))

    # ---- 6. differential run and minimal input --------------------------- #
    rep.section("6. Original vs mutants on identical inputs (diagnostic driver)")
    ranges = search_ranges()
    drivers_dir = tmp / "drivers"
    drivers_dir.mkdir()
    results = {"original": run_driver(build_driver(drivers_dir, "original", root, ex, None), ranges)}
    for mutant in ALL_MUTANTS:
        results[mutant.id] = run_driver(build_driver(drivers_dir, mutant.id, root, ex, mutant), ranges)
    rep.info(f"{len(ranges)} ranges per implementation (0 <= min <= max <= {SEARCH_MAX}), "
             "ordered by max then width; same input file for every build")

    comparison = {}
    for mutant in ALL_MUTANTS:
        probe = mutant.probe
        original_result, mutant_result = results["original"][probe], results[mutant.id][probe]
        oracle_result = oracle(*probe)
        label = f"{mutant.id} on get_palindrome_product({probe[0]}, {probe[1]})"
        rep.check(mutant.expected == oracle_result == original_result,
                  f"{label}: explicit expectation = independent oracle = original",
                  show(original_result),
                  f"expected {show(mutant.expected)} | oracle {show(oracle_result)} | original {show(original_result)}")
        rep.check(mutant_result == mutant.mutant_actual and mutant_result != mutant.expected,
                  f"{label}: mutant differs, as documented", show(mutant_result),
                  f"mutant returned {show(mutant_result)}; documented {show(mutant.mutant_actual)}")
        found = smallest_difference(ranges, results["original"], results[mutant.id], mutant.min_floor)
        rep.check(found == probe, f"{mutant.id}: documented input is the smallest differing range",
                  f"no smaller range with min >= {mutant.min_floor} and max <= {SEARCH_MAX} separates them",
                  f"smallest differing range is {found}, documented {probe}")
        comparison[mutant.id] = {
            "input": {"min": probe[0], "max": probe[1]},
            "expected_explicit": show(mutant.expected),
            "oracle": show(oracle_result),
            "original_actual": show(original_result),
            "mutant_actual": show(mutant_result),
            "mutation": {"old": mutant.old, "new": mutant.new},
            "search_domain": f"{mutant.min_floor} <= min <= max <= {SEARCH_MAX}",
            "smallest_differing_range": list(found) if found else None,
        }

    # ---- 7. surviving mutants ---------------------------------------------- #
    rep.section("7. Mutants the existing 13 cases do not reject (proposed cases above separate them)")
    survivors_info = {}
    for mutant in SURVIVORS:
        d = tmp / f"survivor-{mutant.id}"
        d.mkdir()
        scratch = make_scratch(d, ex, reference=True)
        apply_mutation(scratch, ex, mutant)
        enable_all_tests(scratch / test_rel)
        proc = make_test(scratch)
        survived = not judge(proc, run_test_calls)
        rep.note(f"{mutant.id} ({mutant.title}): "
                 + ("passes all existing cases, so the suite does not distinguish it"
                    if survived else f"is rejected by {sorted(failing_tests(proc.out))}: the proposal below is redundant"))
        survivors_info[mutant.id] = {"passes_existing_suite": survived}
    evidence.add_json("survivors.json", survivors_info)

    # ---- 8. observation ----------------------------------------------------- #
    rep.section("8. Observation about the reference itself (informational, never a failure)")
    original = results["original"]
    disagree = [r for r in ranges if original[r] != oracle(*r)]
    wrong_value = [r for r in disagree if original[r][0] == "OK"]
    rep.note(f"{len(disagree)} of {len(ranges)} ranges: the reference answers 'no palindrome' although the "
             f"independent oracle finds one; reference returned a different value in {len(wrong_value)} ranges")
    for probe in [(1, 1), (24, 29)]:
        rep.note(f"get_palindrome_product({probe[0]}, {probe[1]}): reference {show(original[probe])} | "
                 f"oracle {show(oracle(*probe))}")
    evidence.add_json("observation.json", {
        "domain": f"0 <= min <= max <= {SEARCH_MAX}",
        "ranges": len(ranges),
        "reference_reports_no_palindrome_but_oracle_finds_one": len(disagree),
        "reference_returns_different_value": len(wrong_value),
        "examples": {f"{a},{b}": {"reference": show(original[(a, b)]), "oracle": show(oracle(a, b))}
                     for a, b in [(1, 1), (3, 5), (24, 29)]},
        "status": "observation only; not asserted to be a defect",
    })

    # ---- 9. documentation consistency -------------------------------------- #
    rep.section("9. Hint and maintenance page agree with the evidence")
    hints_path, maintenance_path = root / HINTS, root / MAINTENANCE
    rep.check(hints_path.is_file(), "hints.md exists", str(HINTS), f"missing {HINTS}")
    rep.check(maintenance_path.is_file(), "maintenance page exists", str(MAINTENANCE), f"missing {MAINTENANCE}")
    if hints_path.is_file():
        hints = hints_path.read_text(encoding="utf-8")
        call = f"get_palindrome_product({M1.probe[0]}, {M1.probe[1]})"
        rep.check(call in hints, "hint gives the small diagnostic input", call, f"{call} not found in {HINTS}")
        reference_lines = {ln.strip() for ln in (ex.directory / ".meta" / "example.c").read_text(encoding="utf-8").splitlines()
                           if len(ln.strip()) >= 20}
        leaked = sorted(ln for ln in reference_lines if ln in hints)
        rep.check(not leaked, "hint does not reproduce reference code", "no reference line of 20+ characters appears",
                  f"lines copied from the reference: {leaked}")
        rep.check("```" not in hints, "hint contains no code block", "", "hint contains a fenced code block")
    if maintenance_path.is_file():
        page = maintenance_path.read_text(encoding="utf-8")
        wanted = [NAMED_UUID, NAMED_TEST, NAMED_ASSERTION] + [
            f"get_palindrome_product({m.probe[0]}, {m.probe[1]})" for m in ALL_MUTANTS] + [m.id for m in ALL_MUTANTS]
        missing = [w for w in wanted if w not in page]
        rep.check(not missing, "maintenance page records the mutants, probes, test ID and assertion",
                  f"{len(wanted)} items found", f"missing from {MAINTENANCE}: {missing}")

    # ---- 10. integrity ------------------------------------------------------ #
    rep.section("10. Working tree untouched")
    rep.check(manifest(ex.directory) == before, "exercise directory (learner stub, tests, reference, metadata) unchanged",
              f"{len(before)} files hashed before and after", "the original exercise directory changed during the check")

    # ---- evidence ------------------------------------------------------------ #
    evidence.add("tool-versions.txt", tool_versions(ex))
    evidence.add("inputs.sha256.txt", "".join(f"{h}  {p}\n" for p, h in sorted(before.items())))
    evidence.add_json("inputs.json", {
        "exercise": f"exercises/practice/{SLUG}",
        "config_paths": {"solution": ex.solution, "test": ex.test, "example": ex.example},
        "make_command": "make --no-print-directory -C <scratch> test",
        "all_cases_enabled_by": "commenting out every TEST_IGNORE(); in the scratch copy",
        "named_case": {"uuid": NAMED_UUID, "description": NAMED_DESCRIPTION, "function": NAMED_TEST,
                       "assertion": NAMED_ASSERTION},
        "cases_executed_original": executed_original,
        "minimal_input_search": {"domain": f"0 <= min <= max <= {SEARCH_MAX}", "order": "max ascending, then width ascending",
                                 "filter": "reference output must equal the independent oracle"},
        "mutants": {m.id: {"title": m.title, "probe": list(m.probe), "rejected_by_existing_suite": m.rejected_by}
                    for m in ALL_MUTANTS},
    })
    evidence.add_json("expected-vs-actual.json", comparison)
    evidence.add("expected-vs-actual.txt", "\n".join(
        f"{mid}  get_palindrome_product({c['input']['min']}, {c['input']['max']})\n"
        f"  expected (explicit): {c['expected_explicit']}\n  oracle:              {c['oracle']}\n"
        f"  original actual:     {c['original_actual']}\n  mutant actual:       {c['mutant_actual']}\n"
        for mid, c in comparison.items()))


if __name__ == "__main__":
    sys.exit(main())
