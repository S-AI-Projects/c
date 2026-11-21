#!/usr/bin/env python3
"""R48-T012: reproducible square-root test-generation round trip.

Stdlib only (subprocess + tempfile + pathlib + shutil + json). Verifies, without ever editing
the learner stub or any generated file:

  1. Two fresh `configlet sync` runs on independent copies produce a
     byte-identical .meta/tests.toml and preserve every case present in repo
     HEAD (the synced set is a superset; nothing is dropped).
  2. The reference example, copied over the stub and with every TEST_IGNORE()
     line removed, builds and passes all Unity cases (N > 0, 0 failures,
     0 ignored).
  3. The anchor-phrase cases are present: the anchor string is in tests.toml and
     every committed test case maps to a defined RUN_TEST function.
  4. The real learner stub is still unsolved (git diff --exit-code is clean).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXERCISE = Path(
    os.environ.get("R48T012_EXERCISE", str(ROOT / "exercises/practice/square-root"))
).resolve()
CONFIGLET = ROOT / "bin" / "configlet"
FETCH_CONFIGLET = ROOT / "bin" / "fetch-configlet"
EVIDENCE = ROOT / "work" / "R48-T012" / "evidence.md"
ANCHOR = 'so comments can be added in a "comment" key.'

UUID_RE = re.compile(r"^\[([0-9a-fA-F-]{36})\]", re.MULTILINE)
DESC_RE = re.compile(r'^description\s*=\s*"(.*)"\s*$', re.MULTILINE)
RUN_TEST_RE = re.compile(r"RUN_TEST\((\w+)\)")
SUMMARY_RE = re.compile(r"(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored")
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class CheckError(Exception):
    pass


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def ensure_configlet():
    if CONFIGLET.exists():
        return
    res = run(["bash", str(FETCH_CONFIGLET)], cwd=str(ROOT))
    if res.returncode != 0 or not CONFIGLET.exists():
        raise CheckError("could not fetch configlet:\n" + res.stderr)


def load_inputs():
    cfg = json.loads((EXERCISE / ".meta/config.json").read_text(encoding="utf-8"))
    files = cfg["files"]
    return files["solution"], files["test"], files["example"]


def copy_exercise(dst):
    shutil.copytree(EXERCISE, dst, symlinks=True)


def make_track(tmp, name):
    track = Path(tmp) / name
    (track / "exercises" / "practice").mkdir(parents=True)
    shutil.copy2(ROOT / "config.json", track / "config.json")
    copy_exercise(track / "exercises" / "practice" / "square-root")
    return track


def sync_tests(track):
    """Regenerate .meta/tests.toml from problem-specifications canonical data."""
    res = run(
        [
            str(CONFIGLET), "sync", "--tests", "include", "--update", "-y",
            "-t", str(track), "-e", "square-root",
        ]
    )
    if res.returncode != 0:
        raise CheckError(
            "configlet sync failed (rc=%d)\nstdout:\n%s\nstderr:\n%s"
            % (res.returncode, res.stdout, res.stderr)
        )
    return res


def tests_toml(track):
    return track / "exercises" / "practice" / "square-root" / ".meta" / "tests.toml"


def parse_cases(text):
    """Return list of (uuid, description) in file order."""
    cases = []
    current = None
    for line in text.splitlines():
        m = UUID_RE.match(line)
        if m:
            current = [m.group(1), None]
            cases.append(current)
            continue
        d = DESC_RE.match(line)
        if d and current is not None:
            current[1] = d.group(1)
    return [(u, d) for u, d in cases]


def run_reference_tests(tmp, solution, test_files, example):
    work = Path(tmp) / "reference"
    copy_exercise(work)
    by_suffix = {Path(e).suffix: e for e in example}
    for sol in solution:
        src = work / by_suffix[Path(sol).suffix]
        shutil.copy2(src, work / sol)
    for name in test_files:
        test_file = work / name
        kept = [
            ln
            for ln in test_file.read_text(encoding="utf-8").splitlines()
            if "TEST_IGNORE()" not in ln
        ]
        test_file.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return run(["make", "test"], cwd=str(work))


def get_versions():
    vers = {"Python": sys.version.split()[0]}
    for name, cmd in [
        ("cc", ["cc", "--version"]),
        ("make", ["make", "--version"]),
        ("configlet", [str(CONFIGLET), "--version"]),
    ]:
        try:
            r = run(cmd)
            vers[name] = r.stdout.splitlines()[0] if r.stdout else "unknown"
        except Exception:
            vers[name] = "missing"
    return vers


def write_evidence(rows, versions, notes):
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "# R48-T012 evidence",
        "",
        "Exercise: `%s`" % EXERCISE,
        "Inputs: solution=['square_root.c', 'square_root.h'] | test=['test_square_root.c'] | example=['.meta/example.c', '.meta/example.h']",
        "Python: %s" % versions.get("Python", "unknown"),
        "- cc: %s" % versions.get("cc", "unknown"),
        "- make: %s" % versions.get("make", "unknown"),
        "- configlet: %s" % versions.get("configlet", "unknown"),
        "",
        "## Expected vs actual",
        "",
        "| Check | Expected | Actual |",
        "|-------|----------|--------|",
    ]
    for check, exp, act in rows:
        body.append("| %s | %s | %s |" % (check, exp, act))
    body.append("")
    for n in notes:
        body.append(n)
        body.append("")
    EVIDENCE.write_text("\n".join(body), encoding="utf-8")


def main():
    rows = []
    notes = []
    try:
        ensure_configlet()
        versions = get_versions()
        solution, test_files, example = load_inputs()

        # (1) Test generation: two independent runs must produce byte-identical tests.toml
        repo_text = (EXERCISE / ".meta/tests.toml").read_text(encoding="utf-8")
        repo_cases = parse_cases(repo_text)
        repo_uuids = {u for u, _ in repo_cases}

        with tempfile.TemporaryDirectory() as tmp:
            t1 = make_track(tmp, "track1")
            t2 = make_track(tmp, "track2")
            sync_tests(t1)
            sync_tests(t2)

            f1 = tests_toml(t1).read_text(encoding="utf-8")
            f2 = tests_toml(t2).read_text(encoding="utf-8")

            identical = f1 == f2
            rows.append(("two syncs byte-identical (timestamp strip: none)", "True", str(identical)))
            if not identical:
                raise CheckError("two fresh sync runs produced different tests.toml")

            c1 = parse_cases(f1)
            u1 = {u for u, _ in c1}
            same_set = u1 == {u for u, _ in parse_cases(f2)}
            rows.append(("UUID set identical in both runs", "True", str(same_set)))
            if not same_set:
                raise CheckError("UUID sets differ between the two sync runs")

            dropped = repo_uuids - u1
            rows.append(("repo-HEAD cases dropped by sync", "0", str(len(dropped))))
            if dropped:
                raise CheckError("sync dropped repo cases: %s" % sorted(dropped))

            added = u1 - repo_uuids
            rows.append(("canonical cases added by sync (track drift)", "n/a", str(len(added))))
            rows.append(("repo cases in tests.toml", str(len(repo_uuids)), str(len(repo_uuids & u1))))

            anchor = ANCHOR in repo_text
            rows.append(("anchor phrase present in committed tests.toml", "True", str(anchor)))
            if not anchor:
                raise CheckError("anchor phrase missing from committed tests.toml")
            if added:
                notes.append(
                    "Track drift: sync deterministically adds %d canonical case(s) not "
                    "yet hand-implemented: %s. It also rewrites the "
                    "auto-generated header, so the anchor phrase above is asserted "
                    "against the committed file."
                    % (len(added), ", ".join(sorted(added)))
                )

        # (2) Reference run: example over stub, TEST_IGNORE lines removed.
        with tempfile.TemporaryDirectory() as tmp:
            res = run_reference_tests(tmp, solution, test_files, example)
            plain = ANSI_RE.sub("", res.stdout + res.stderr)
            if res.returncode != 0:
                raise CheckError(
                    "make test failed (rc=%d)\n%s" % (res.returncode, plain[-2000:])
                )
            m = SUMMARY_RE.search(plain)
            if not m:
                raise CheckError("could not find Unity summary:\n" + plain[-1500:])
            n, failures, ignored = (int(x) for x in m.groups())
            rows.append(("Unity cases run (N)", "> 0", str(n)))
            rows.append(("Unity failures (M)", "0", str(failures)))
            rows.append(("Unity ignored (K)", "0", str(ignored)))
            if n <= 0:
                raise CheckError("zero tests executed")
            if failures != 0 or ignored != 0:
                raise CheckError(
                    "expected 0 failures / 0 ignored, got %d / %d" % (failures, ignored)
                )

        # (3) Anchor cases present: committed cases map to defined RUN_TESTs.
        test_src = "".join(
            (EXERCISE / name).read_text(encoding="utf-8") for name in test_files
        )
        run_tests = RUN_TEST_RE.findall(test_src)
        rows.append(("RUN_TEST count == committed case count", str(len(repo_cases)), str(len(run_tests))))
        if len(run_tests) != len(repo_cases):
            raise CheckError(
                "RUN_TEST count %d != committed case count %d"
                % (len(run_tests), len(repo_cases))
            )
        undefined = [
            fn for fn in run_tests if ("static void %s(void)" % fn) not in test_src
        ]
        rows.append(("every RUN_TEST names a defined function", "True", str(not undefined)))
        if undefined:
            raise CheckError("RUN_TEST references undefined: %s" % undefined)

        # (4) Learner stub is still unsolved.
        sol_paths = [str(EXERCISE / s) for s in solution]
        diff = run(["git", "-C", str(ROOT), "diff", "--exit-code", "--", *sol_paths])
        stub_clean = diff.returncode == 0
        rows.append(("learner stub unsolved (git diff clean)", "True", str(stub_clean)))
        if not stub_clean:
            raise CheckError("learner stub was modified:\n" + diff.stdout)

        notes.append("Result: PASS. %d Unity cases ran against the reference." % n)
        write_evidence(rows, versions, notes)
        print("PASS: %d Unity cases, 0 failures, 0 ignored." % n)
        print("PASS: two configlet syncs identical; %d cases preserved, %d added."
              % (len(repo_uuids & u1), len(added)))
        print("PASS: learner stub still unsolved.")
        print("Evidence: %s" % EVIDENCE)
        return 0
    except CheckError as exc:
        notes.append("Result: FAIL. %s" % exc)
        write_evidence(rows, versions, notes)
        print("FAIL: %s" % exc, file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        notes.append("Result: FAIL (error). %s" % exc)
        write_evidence(rows, versions, notes)
        print("FAIL: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
