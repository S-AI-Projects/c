#!/usr/bin/env python3
"""
tools/course_checks/r48-t042.py
Focused reusable regeneration and verification check for Task R48-T042:
Make the linked-list test-generation path reproducible [exercises/practice/linked-list].
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def find_repo_root():
    """Find the root directory of the git repository."""
    curr = os.path.abspath(os.path.dirname(__file__))
    while curr and curr != os.path.dirname(curr):
        if os.path.exists(os.path.join(curr, ".git")) or os.path.exists(os.path.join(curr, "config.json")):
            return curr
        curr = os.path.dirname(curr)
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def normalize_toml_content(content: str) -> str:
    """Normalize TOML text by stripping generated timestamp comments if present."""
    lines = []
    for line in content.splitlines():
        if re.match(r'^#\s*(generated|regenerated|date|time|timestamp):?.*$', line, flags=re.IGNORECASE):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def verify_learner_stub(repo_root: str):
    """Ensure the working tree learner files remain unsolved stubs."""
    c_path = os.path.join(repo_root, "exercises/practice/linked-list/linked_list.c")
    with open(c_path, "r", encoding="utf-8") as f:
        c_code = f.read()

    # The learner stub has struct declarations but no function bodies
    has_functions = any(fn in c_code for fn in [
        "list_create(", "list_count(", "list_push(", "list_pop(",
        "list_unshift(", "list_shift(", "list_delete(", "list_destroy("
    ])
    assert not has_functions, "Assertion failed: Learner stub contains implemented functions in working tree!"
    return True


def verify_maintenance_doc(repo_root: str):
    """Verify docs/maintenance/linked-list.md contains the required sections."""
    doc_path = os.path.join(repo_root, "docs/maintenance/linked-list.md")
    assert os.path.exists(doc_path), f"Assertion failed: Missing {doc_path}"

    with open(doc_path, "r", encoding="utf-8") as f:
        doc = f.read().lower()

    assert "configlet sync" in doc, "Maintenance doc must include configlet sync reproduction command"
    assert "description" in doc, "Maintenance doc must document description key recreation"
    assert "reimplements" in doc, "Maintenance doc must document reimplements key recreation"
    assert "preserve" in doc, "Maintenance doc must document key preservation rule"
    assert "comment" in doc, "Maintenance doc must document comment key preservation"
    assert "canonical-data.json" in doc, "Maintenance doc must document canonical-data.json input"
    assert "test_pop_gets_element_from_the_list" in doc, "Maintenance doc must include case mapping"
    return True


def run_test_generation_check(repo_root: str):
    """Verify two fresh generations yield the exact same tests after normalization."""
    configlet = os.path.join(repo_root, "bin/configlet")
    if not os.path.exists(configlet):
        fetch_script = os.path.join(repo_root, "bin/fetch-configlet")
        if os.path.exists(fetch_script):
            subprocess.run(["bash", fetch_script], cwd=repo_root, check=True)
        assert os.path.exists(configlet), "configlet binary not found"

    def generate_in_temp():
        with tempfile.TemporaryDirectory() as tmpdir:
            track_dir = os.path.join(tmpdir, "track")
            os.makedirs(os.path.join(track_dir, "exercises/practice/linked-list/.meta"), exist_ok=True)
            shutil.copy(os.path.join(repo_root, "config.json"), track_dir)
            shutil.copytree(
                os.path.join(repo_root, "exercises/practice/linked-list"),
                os.path.join(track_dir, "exercises/practice/linked-list"),
                dirs_exist_ok=True
            )
            toml_path = os.path.join(track_dir, "exercises/practice/linked-list/.meta/tests.toml")
            if os.path.exists(toml_path):
                os.remove(toml_path)

            cmd = [
                configlet, "sync",
                "--exercise", "linked-list",
                "--tests", "include",
                "--update", "--yes",
                "--track-dir", track_dir
            ]
            # Try offline first; fall back if needed
            res = subprocess.run(cmd + ["--offline"], capture_output=True, text=True)
            if res.returncode != 0:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)

            assert os.path.exists(toml_path), f"tests.toml was not generated: {res.stderr}"
            with open(toml_path, "r", encoding="utf-8") as f:
                content = f.read()

            with open(toml_path, "rb") as f:
                data = tomllib.load(f)

            return normalize_toml_content(content), data

    gen1_text, gen1_data = generate_in_temp()
    gen2_text, gen2_data = generate_in_temp()

    assert gen1_text == gen2_text, "Assertion failed: Two generations of tests.toml do not match!"
    assert len(gen1_data) == 19, f"Assertion failed: Expected 19 canonical test cases, got {len(gen1_data)}"

    # Also verify that comment keys are preserved
    with tempfile.TemporaryDirectory() as tmpdir:
        track_dir = os.path.join(tmpdir, "track")
        os.makedirs(os.path.join(track_dir, "exercises/practice/linked-list/.meta"), exist_ok=True)
        shutil.copy(os.path.join(repo_root, "config.json"), track_dir)
        shutil.copytree(
            os.path.join(repo_root, "exercises/practice/linked-list"),
            os.path.join(track_dir, "exercises/practice/linked-list"),
            dirs_exist_ok=True
        )
        toml_path = os.path.join(track_dir, "exercises/practice/linked-list/.meta/tests.toml")

        # Run sync and ensure existing comment key is preserved
        res = subprocess.run(
            [configlet, "sync", "--exercise", "linked-list", "--tests", "include", "--update", "--yes", "--offline", "--track-dir", track_dir],
            capture_output=True, text=True
        )
        if res.returncode != 0:
            res = subprocess.run(
                [configlet, "sync", "--exercise", "linked-list", "--tests", "include", "--update", "--yes", "--track-dir", track_dir],
                capture_output=True, text=True, check=True
            )
        with open(toml_path, "r", encoding="utf-8") as f:
            synced_content = f.read()
        assert "comment" in synced_content and "test_pop_gets_element_from_the_list" in synced_content, (
            "Assertion failed: comment key was not preserved during regeneration!"
        )

    return len(gen1_data)


def run_reference_test_check(repo_root: str):
    """Run make test against reference in a temporary directory and verify test counts."""
    exercise_path = os.path.join(repo_root, "exercises/practice/linked-list")
    config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(config_file, "r", encoding="utf-8") as f:
        meta_config = json.load(f)

    solution_files = meta_config["files"]["solution"]
    test_files = meta_config["files"]["test"]
    example_files = meta_config["files"]["example"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, "linked-list")
        shutil.copytree(exercise_path, tmp_exercise)

        # Substitute reference into temporary copy
        for sol, ex in zip(solution_files, example_files):
            src = os.path.join(tmp_exercise, ex)
            dst = os.path.join(tmp_exercise, sol)
            shutil.copy(src, dst)

        # Enable all test cases by removing TEST_IGNORE()
        for tf in test_files:
            tf_path = os.path.join(tmp_exercise, tf)
            with open(tf_path, "r", encoding="utf-8") as f:
                content = f.read()
            updated = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w", encoding="utf-8") as f:
                f.write(updated)

        # Run make test
        run_proc = subprocess.run(
            ["make", "test"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True
        )

        assert run_proc.returncode == 0, f"make test failed with return code {run_proc.returncode}:\n{run_proc.stderr}\n{run_proc.stdout}"

        clean_stdout = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', run_proc.stdout)
        summary = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_stdout)
        assert summary is not None, f"Could not parse Unity summary from output:\n{clean_stdout}"

        num_tests = int(summary.group(1))
        num_failures = int(summary.group(2))
        num_ignored = int(summary.group(3))

        assert num_tests > 0, f"Zero tests executed (run={num_tests})"
        assert num_failures == 0, f"Test failures encountered (failures={num_failures})"
        assert num_ignored == 0, f"Ignored tests detected (ignored={num_ignored})"
        assert num_tests == 19, f"Expected 19 tests executed, got {num_tests}"

        passed_tests = re.findall(r':(test_\w+):PASS', clean_stdout)
        return num_tests, passed_tests


def run_all_checks():
    repo_root = find_repo_root()
    print(f"Repository root: {repo_root}")

    print("1. Verifying working tree learner stub remains unsolved...")
    verify_learner_stub(repo_root)
    print("   [PASS] Learner stub is unsolved.")

    print("2. Verifying maintenance documentation...")
    verify_maintenance_doc(repo_root)
    print("   [PASS] Maintenance documentation verified.")

    print("3. Verifying test generation reproducibility & key handling...")
    case_count = run_test_generation_check(repo_root)
    print(f"   [PASS] Two generations match identically ({case_count} cases, no cases dropped).")

    print("4. Executing make test against reference in scratch directory...")
    test_count, passed_tests = run_reference_test_check(repo_root)
    print(f"   [PASS] Executed {test_count} tests with 0 failures and 0 ignored.")

    print("\nAll R48-T042 checks passed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_checks())
