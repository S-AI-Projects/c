#!/usr/bin/env python3
"""
work/R48-T048/check.py
Automated verification check for Task R48-T048:
Map the maintained files for word-count [exercises/practice/word-count].
"""

import copy
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
        if os.path.exists(os.path.join(curr, ".git")) or (
            os.path.exists(os.path.join(curr, "config.json")) and
            os.path.exists(os.path.join(curr, "exercises"))
        ):
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


def get_tool_versions(repo_root):
    """Collect runtime tool versions."""
    tools = {}
    tools["python"] = sys.version.split()[0]

    try:
        res = subprocess.run(["cc", "--version"], capture_output=True, text=True, check=True)
        tools["cc"] = res.stdout.splitlines()[0].strip()
    except Exception as e:
        tools["cc"] = f"Error: {e}"

    try:
        res = subprocess.run(["make", "--version"], capture_output=True, text=True, check=True)
        tools["make"] = res.stdout.splitlines()[0].strip()
    except Exception as e:
        tools["make"] = f"Error: {e}"

    configlet_path = os.path.join(repo_root, "bin/configlet")
    if os.path.exists(configlet_path):
        try:
            res = subprocess.run([configlet_path, "--version"], capture_output=True, text=True, check=True)
            tools["configlet"] = res.stdout.strip()
        except Exception as e:
            tools["configlet"] = f"Error: {e}"
    else:
        tools["configlet"] = "not found"

    return tools


def verify_learner_stub(repo_root):
    """Verify that learner stub in the working tree remains unsolved."""
    c_path = os.path.join(repo_root, "exercises/practice/word-count/word_count.c")
    assert os.path.exists(c_path), f"Assertion failed: Missing {c_path}"

    with open(c_path, "r", encoding="utf-8") as f:
        code = f.read()

    # The learner stub only has #include "word_count.h" and no implementation
    has_implementation = "count_words(" in code and ("{" in code and "return" in code)
    assert not has_implementation, (
        "Assertion failed: Learner stub exercises/practice/word-count/word_count.c contains "
        "an implementation in working tree! It must remain unsolved."
    )
    return True


def validate_files_metadata(exercise_dir, files_obj):
    """
    Parse the files object rather than searching filenames heuristically.
    Resolve each path, reject parent traversal, and check that every declared file exists.
    """
    if not isinstance(files_obj, dict):
        raise TypeError(f"'files' property must be a dict, got {type(files_obj).__name__}")

    required_roles = ["solution", "test", "example"]
    for role in required_roles:
        if role not in files_obj:
            raise KeyError(f"Missing required file role: '{role}' in config.json files object")

    allowed_roles = {"solution", "test", "example", "editor"}
    resolved_files = {}

    abs_exercise_dir = os.path.abspath(exercise_dir)

    for role, paths in files_obj.items():
        if role not in allowed_roles:
            raise ValueError(f"Unknown file role '{role}' in files object")

        if not isinstance(paths, list) or len(paths) == 0:
            raise ValueError(f"Role '{role}' must be a non-empty list of path strings")

        resolved_files[role] = []
        for rel_path in paths:
            if not isinstance(rel_path, str) or not rel_path.strip():
                raise ValueError(f"Declared path in role '{role}' must be a non-empty string")

            # Reject absolute paths
            if os.path.isabs(rel_path) or rel_path.startswith("/") or rel_path.startswith("\\"):
                raise ValueError(
                    f"Parent traversal / outside exercise path rejected: '{rel_path}' is an absolute path"
                )

            # Reject path traversal (e.g. containing '..')
            norm_parts = os.path.normpath(rel_path).split(os.sep)
            if ".." in norm_parts or rel_path.startswith(".."):
                raise ValueError(
                    f"Parent traversal rejected: '{rel_path}' attempts to traverse outside exercise directory"
                )

            # Resolve path relative to exercise directory
            full_path = os.path.normpath(os.path.join(abs_exercise_dir, rel_path))

            # Ensure resolved path is strictly inside exercise directory
            if not full_path.startswith(abs_exercise_dir + os.sep) and full_path != abs_exercise_dir:
                raise ValueError(
                    f"Path outside exercise rejected: '{rel_path}' resolves outside {exercise_dir}"
                )

            # Check that every declared file exists
            if not os.path.isfile(full_path):
                raise FileNotFoundError(
                    f"Declared file does not exist: role='{role}', path='{rel_path}' (resolved: '{full_path}')"
                )

            resolved_files[role].append(full_path)

    return resolved_files


def test_invalid_metadata_fixtures(exercise_dir, real_config):
    """
    Test the checker with temporary missing-reference, missing-test, and outside-exercise paths;
    the real metadata must pass. All three deliberately invalid fixtures must fail for the intended reason.
    """
    fixture_results = {}

    # 1. Missing reference fixture
    missing_ref_config = copy.deepcopy(real_config["files"])
    missing_ref_config["example"] = [".meta/nonexistent_reference.c"]
    try:
        validate_files_metadata(exercise_dir, missing_ref_config)
        assert False, "missing-reference fixture unexpectedly passed validation!"
    except FileNotFoundError as e:
        assert ".meta/nonexistent_reference.c" in str(e) and "example" in str(e)
        fixture_results["missing_reference"] = {
            "status": "PASS",
            "expected_failure": "FileNotFoundError",
            "error_message": str(e)
        }

    # 2. Missing test fixture
    missing_test_config = copy.deepcopy(real_config["files"])
    missing_test_config["test"] = ["test_nonexistent_word_count.c"]
    try:
        validate_files_metadata(exercise_dir, missing_test_config)
        assert False, "missing-test fixture unexpectedly passed validation!"
    except FileNotFoundError as e:
        assert "test_nonexistent_word_count.c" in str(e) and "test" in str(e)
        fixture_results["missing_test"] = {
            "status": "PASS",
            "expected_failure": "FileNotFoundError",
            "error_message": str(e)
        }

    # 3. Outside exercise fixture (parent traversal)
    outside_config = copy.deepcopy(real_config["files"])
    outside_config["solution"] = ["../outside_solution.c", "word_count.h"]
    try:
        validate_files_metadata(exercise_dir, outside_config)
        assert False, "outside-exercise fixture unexpectedly passed validation!"
    except ValueError as e:
        assert "traversal" in str(e).lower() or "outside" in str(e).lower()
        fixture_results["outside_exercise"] = {
            "status": "PASS",
            "expected_failure": "ValueError",
            "error_message": str(e)
        }

    # 4. Real metadata must pass
    real_resolved = validate_files_metadata(exercise_dir, real_config["files"])
    fixture_results["real_config"] = {
        "status": "PASS",
        "resolved_files_count": {role: len(paths) for role, paths in real_resolved.items()}
    }

    return fixture_results, real_resolved


def verify_test_runner_discovery(exercise_dir, real_config):
    """
    Verify and explain how the runner finds:
    1. exercises/practice/word-count/.meta/tests.toml
    2. exercises/practice/word-count/.meta/example.c
    """
    tests_toml_path = os.path.join(exercise_dir, ".meta/tests.toml")
    assert os.path.isfile(tests_toml_path), f"tests.toml not found at {tests_toml_path}"

    with open(tests_toml_path, "rb") as f:
        toml_data = tomllib.load(f)

    # tests.toml discovery: standard Exercism convention path <exercise>/.meta/tests.toml
    assert len(toml_data) >= 15, f"Expected at least 15 UUID entries in tests.toml, found {len(toml_data)}"

    # example.c discovery: dynamically read from files.example in .meta/config.json
    assert "example" in real_config["files"], "config.json missing files.example"
    example_relative = real_config["files"]["example"][0]
    assert example_relative == ".meta/example.c", f"Unexpected example file path: {example_relative}"

    example_full = os.path.normpath(os.path.join(exercise_dir, example_relative))
    assert os.path.isfile(example_full), f"example file does not exist at {example_full}"

    with open(example_full, "r", encoding="utf-8") as f:
        ex_code = f.read()
    assert "count_words(" in ex_code, "Reference implementation does not define count_words()"
    assert "static int word_match(" in ex_code, "Reference implementation does not contain word_match() at L9"

    discovery_info = {
        "tests_toml": {
            "path": "exercises/practice/word-count/.meta/tests.toml",
            "discovery_mechanism": (
                "Discovered by convention: Exercism track tooling and test runner look at "
                "<track_root>/exercises/practice/<slug>/.meta/tests.toml to find canonical UUID "
                "specifications, comments, reimplements keys, and inclusion status."
            ),
            "total_cases": len(toml_data)
        },
        "example_c": {
            "path": "exercises/practice/word-count/.meta/example.c",
            "discovery_mechanism": (
                "Discovered via explicit metadata mapping: The runner parses "
                "<track_root>/exercises/practice/<slug>/.meta/config.json, reads files.example, "
                "and resolves '.meta/example.c' inside the exercise directory. For validation, "
                "the runner copies this file into the solution path to compile and run tests."
            ),
            "pinned_source": "exercises/practice/word-count/.meta/example.c#L9"
        }
    }
    return discovery_info, toml_data


def verify_canonical_generation_and_key_handling(repo_root, toml_data):
    """
    Verify the three key handling rules in tests.toml:
    1. Recreate every description key/value pair
    2. Recreate every reimplements key/value pair, where they exist in problem-specifications
    3. Preserve any other key/value pair (such as comment, include = false)
    And verify two successive generations match identically.
    """
    configlet = os.path.join(repo_root, "bin/configlet")
    if not os.path.exists(configlet):
        fetch_script = os.path.join(repo_root, "bin/fetch-configlet")
        if os.path.exists(fetch_script):
            subprocess.run(["bash", fetch_script], cwd=repo_root, check=True)
        assert os.path.exists(configlet), "configlet binary not found"

    # Rule 1: Every case must have a description key
    missing_desc = [uuid for uuid, data in toml_data.items() if "description" not in data]
    assert not missing_desc, f"UUIDs missing description key: {missing_desc}"

    # Rule 2: Recreate every reimplements key/value pair where they exist
    reimplements_cases = {uuid: data["reimplements"] for uuid, data in toml_data.items() if "reimplements" in data}
    assert len(reimplements_cases) > 0, "No reimplements key found in tests.toml!"
    assert "4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3" in reimplements_cases, (
        "Expected reimplements case 4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3 not found"
    )
    assert reimplements_cases["4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3"] == "4185a902-bdb0-4074-864c-f416e42a0f19"

    # Rule 3: Preserve other keys (such as comment, include = false)
    comment_cases = {uuid: data["comment"] for uuid, data in toml_data.items() if "comment" in data}
    assert len(comment_cases) > 0, "No comment key found in tests.toml!"
    assert "4185a902-bdb0-4074-864c-f416e42a0f19" in comment_cases
    assert toml_data["4185a902-bdb0-4074-864c-f416e42a0f19"].get("include") is False

    # Two generations reproducibility in temporary directory
    def run_sync_in_temp():
        with tempfile.TemporaryDirectory() as tmpdir:
            track_dir = os.path.join(tmpdir, "track")
            os.makedirs(os.path.join(track_dir, "exercises/practice/word-count/.meta"), exist_ok=True)
            shutil.copy(os.path.join(repo_root, "config.json"), track_dir)
            shutil.copytree(
                os.path.join(repo_root, "exercises/practice/word-count"),
                os.path.join(track_dir, "exercises/practice/word-count"),
                dirs_exist_ok=True
            )
            toml_path = os.path.join(track_dir, "exercises/practice/word-count/.meta/tests.toml")

            cmd = [
                configlet, "sync",
                "--exercise", "word-count",
                "--tests", "include",
                "--update", "--yes",
                "--track-dir", track_dir
            ]
            res = subprocess.run(cmd + ["--offline"], capture_output=True, text=True)
            if res.returncode != 0:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)

            with open(toml_path, "r", encoding="utf-8") as f:
                content = f.read()

            with open(toml_path, "rb") as f:
                parsed = tomllib.load(f)

            return content, parsed

    content1, parsed1 = run_sync_in_temp()
    content2, parsed2 = run_sync_in_temp()

    assert content1 == content2, "Two generations yielded differing tests.toml outputs!"
    assert len(parsed1) == len(toml_data), f"Generation dropped cases: {len(parsed1)} vs {len(toml_data)}"

    # Ensure comment and reimplements keys were preserved
    assert "4185a902-bdb0-4074-864c-f416e42a0f19" in parsed1
    assert parsed1["4185a902-bdb0-4074-864c-f416e42a0f19"].get("comment") == "Reimplemented"
    assert parsed1["4185a902-bdb0-4074-864c-f416e42a0f19"].get("include") is False
    assert parsed1["4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3"].get("reimplements") == "4185a902-bdb0-4074-864c-f416e42a0f19"

    return {
        "two_generations_identical": True,
        "total_cases": len(parsed1),
        "reimplements_cases": reimplements_cases,
        "comment_cases": comment_cases,
        "preserved_other_keys": True
    }


def run_scratch_make_test(repo_root, real_config):
    """
    Copy the exercise including dotfiles into a temporary directory,
    substitute the reference only in that copy, enable all intended cases,
    and run make test. Check child return codes and test counts.
    Do not rewrite the working tree.
    """
    exercise_path = os.path.join(repo_root, "exercises/practice/word-count")

    solution_files = real_config["files"]["solution"]
    test_files = real_config["files"]["test"]
    example_files = real_config["files"]["example"]

    with tempfile.TemporaryDirectory() as tmpdir:
        scratch_exercise = os.path.join(tmpdir, "word-count")
        shutil.copytree(exercise_path, scratch_exercise)

        # Substitute reference into solution files in scratch directory
        # word_count.c is replaced by .meta/example.c
        for sol_file in solution_files:
            if sol_file.endswith(".c"):
                ref_src = os.path.join(scratch_exercise, example_files[0])
                sol_dst = os.path.join(scratch_exercise, sol_file)
                shutil.copyfile(ref_src, sol_dst)

        # Enable all test cases by removing TEST_IGNORE() from test file in scratch directory
        for tf in test_files:
            tf_path = os.path.join(scratch_exercise, tf)
            with open(tf_path, "r", encoding="utf-8") as f:
                content = f.read()
            updated = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w", encoding="utf-8") as f:
                f.write(updated)

        # Execute make test
        run_proc = subprocess.run(
            ["make", "test"],
            cwd=scratch_exercise,
            capture_output=True,
            text=True
        )

        assert run_proc.returncode == 0, (
            f"make test failed with return code {run_proc.returncode}:\n"
            f"STDOUT:\n{run_proc.stdout}\nSTDERR:\n{run_proc.stderr}"
        )

        clean_stdout = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', run_proc.stdout)
        summary = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_stdout)
        assert summary is not None, f"Could not parse Unity summary line from stdout:\n{clean_stdout}"

        num_tests = int(summary.group(1))
        num_failures = int(summary.group(2))
        num_ignored = int(summary.group(3))

        assert num_tests > 0, f"Zero tests executed (run={num_tests})"
        assert num_failures == 0, f"Test failures encountered (failures={num_failures})"
        assert num_ignored == 0, f"Ignored tests detected (ignored={num_ignored})"
        assert num_tests == 14, f"Expected 14 tests executed, got {num_tests}"

        passed_tests = re.findall(r':(test_\w+):PASS', clean_stdout)
        assert len(passed_tests) == 14, f"Expected 14 passed test functions, parsed {len(passed_tests)}"

        return {
            "returncode": run_proc.returncode,
            "num_tests": num_tests,
            "num_failures": num_failures,
            "num_ignored": num_ignored,
            "passed_tests": passed_tests,
            "stdout": clean_stdout
        }


def verify_maintenance_doc(repo_root):
    """Verify docs/maintenance/word-count.md contains all required sections and mappings."""
    doc_path = os.path.join(repo_root, "docs/maintenance/word-count.md")
    assert os.path.exists(doc_path), f"Missing maintenance doc: {doc_path}"

    with open(doc_path, "r", encoding="utf-8") as f:
        doc = f.read()

    assert "exercises/practice/word-count/word_count.c" in doc, "Maintenance doc must name stub word_count.c"
    assert "exercises/practice/word-count/word_count.h" in doc, "Maintenance doc must name header word_count.h"
    assert "exercises/practice/word-count/.meta/example.c" in doc, "Maintenance doc must name reference example.c"
    assert "exercises/practice/word-count/test_word_count.c" in doc, "Maintenance doc must name test_word_count.c"
    assert "exercises/practice/word-count/.meta/tests.toml" in doc, "Maintenance doc must name tests.toml"
    assert "exercises/practice/word-count/.meta/config.json" in doc, "Maintenance doc must name config.json"
    assert "solution" in doc and "test" in doc and "example" in doc, "Maintenance doc must detail file roles"
    assert "description" in doc, "Maintenance doc must document description key recreation"
    assert "reimplements" in doc, "Maintenance doc must document reimplements key recreation"
    assert "preserve" in doc.lower(), "Maintenance doc must document preservation of other keys"
    assert "configlet sync" in doc, "Maintenance doc must provide configlet sync reproduction command"
    assert "python3 work/R48-T048/check.py" in doc, "Maintenance doc must provide validation command"
    assert "test_count_one_word" in doc, "Maintenance doc must include case mapping table"
    assert "Done when" in doc or "Done When" in doc, "Maintenance doc must include Done When checklist"
    assert "Submission" in doc, "Maintenance doc must include Submission checklist"
    return True


def save_artifacts(repo_root, evidence):
    """Persist verification artifacts to work/R48-T048/."""
    work_dir = os.path.join(repo_root, "work/R48-T048")
    os.makedirs(work_dir, exist_ok=True)

    with open(os.path.join(work_dir, "inputs.json"), "w", encoding="utf-8") as f:
        json.dump(evidence["inputs"], f, indent=2)

    with open(os.path.join(work_dir, "expected_vs_actual.json"), "w", encoding="utf-8") as f:
        json.dump(evidence["expected_vs_actual"], f, indent=2)

    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(evidence["results"], f, indent=2)

    with open(os.path.join(work_dir, "tool_versions.txt"), "w", encoding="utf-8") as f:
        for tool, ver in evidence["tools"].items():
            f.write(f"{tool}: {ver}\n")


def run_all_checks():
    repo_root = find_repo_root()
    exercise_dir = os.path.join(repo_root, "exercises/practice/word-count")
    config_path = os.path.join(exercise_dir, ".meta/config.json")

    print(f"=== Running Task R48-T048 Verification ===")
    print(f"Repository Root: {repo_root}")
    print(f"Exercise Directory: {exercise_dir}")

    with open(config_path, "r", encoding="utf-8") as f:
        real_config = json.load(f)

    tools = get_tool_versions(repo_root)
    print(f"Tools detected: {tools}")

    print("\n1. Verifying learner stub in working tree remains unsolved...")
    verify_learner_stub(repo_root)
    print("   [PASS] Learner stub word_count.c is unsolved.")

    print("\n2. Validating files metadata object and rejecting parent traversal...")
    fixture_results, real_resolved = test_invalid_metadata_fixtures(exercise_dir, real_config)
    print(f"   [PASS] missing-reference fixture failed as expected: {fixture_results['missing_reference']['expected_failure']}")
    print(f"   [PASS] missing-test fixture failed as expected: {fixture_results['missing_test']['expected_failure']}")
    print(f"   [PASS] outside-exercise fixture failed as expected: {fixture_results['outside_exercise']['expected_failure']}")
    print(f"   [PASS] Real config.json validated successfully: {fixture_results['real_config']['resolved_files_count']}")

    print("\n3. Verifying runner discovery mechanism for tests.toml and example.c...")
    discovery_info, toml_data = verify_test_runner_discovery(exercise_dir, real_config)
    print("   [PASS] Runner discovery mechanism verified and documented.")

    print("\n4. Verifying canonical tests.toml key handling & two-generation reproducibility...")
    canonical_res = verify_canonical_generation_and_key_handling(repo_root, toml_data)
    print(f"   [PASS] tests.toml verified: {canonical_res['total_cases']} cases, "
          f"reimplements={list(canonical_res['reimplements_cases'].keys())}, "
          f"comments={list(canonical_res['comment_cases'].keys())}, identical across generations.")

    print("\n5. Executing make test against reference in scratch temporary directory...")
    test_run = run_scratch_make_test(repo_root, real_config)
    print(f"   [PASS] make test executed {test_run['num_tests']} tests: "
          f"{test_run['num_failures']} failures, {test_run['num_ignored']} ignored.")

    print("\n6. Verifying maintenance documentation docs/maintenance/word-count.md...")
    verify_maintenance_doc(repo_root)
    print("   [PASS] Maintenance documentation verified.")

    # Structure evidence
    inputs_data = {
        "task_id": "R48-T048",
        "exercise": "exercises/practice/word-count",
        "config_json_path": "exercises/practice/word-count/.meta/config.json",
        "declared_files": real_config["files"],
        "discovery_routes": discovery_info,
        "fixtures_tested": [
            "missing-reference (.meta/nonexistent_reference.c)",
            "missing-test (test_nonexistent_word_count.c)",
            "outside-exercise (../outside_solution.c)"
        ],
        "canonical_cases_count": len(toml_data)
    }

    expected_vs_actual = {
        "learner_stub_unsolved": {
            "expected": True,
            "actual": True,
            "pass": True
        },
        "real_metadata_validation": {
            "expected": "PASS",
            "actual": fixture_results["real_config"]["status"],
            "pass": True
        },
        "fixtures": {
            "missing_reference": {
                "expected": "FileNotFoundError",
                "actual": fixture_results["missing_reference"]["expected_failure"],
                "pass": True
            },
            "missing_test": {
                "expected": "FileNotFoundError",
                "actual": fixture_results["missing_test"]["expected_failure"],
                "pass": True
            },
            "outside_exercise": {
                "expected": "ValueError",
                "actual": fixture_results["outside_exercise"]["expected_failure"],
                "pass": True
            }
        },
        "canonical_tests_toml": {
            "expected_cases": len(toml_data),
            "actual_cases": canonical_res["total_cases"],
            "recreated_description": True,
            "recreated_reimplements": True,
            "preserved_other_keys": True,
            "two_generation_reproducibility": canonical_res["two_generations_identical"],
            "pass": True
        },
        "scratch_make_test": {
            "expected_returncode": 0,
            "actual_returncode": test_run["returncode"],
            "expected_tests_run": 14,
            "actual_tests_run": test_run["num_tests"],
            "expected_failures": 0,
            "actual_failures": test_run["num_failures"],
            "expected_ignored": 0,
            "actual_ignored": test_run["num_ignored"],
            "pass": True
        },
        "maintenance_documentation": {
            "expected": True,
            "actual": True,
            "pass": True
        }
    }

    results_data = {
        "task_id": "R48-T048",
        "exercise": "exercises/practice/word-count",
        "status": "SUCCESS",
        "tools": tools,
        "files_resolved": real_resolved,
        "fixtures_passed": True,
        "canonical_cases": {
            "total": canonical_res["total_cases"],
            "enabled_tests": test_run["num_tests"],
            "excluded_cases": canonical_res["total_cases"] - test_run["num_tests"],
            "reimplements_mapping": canonical_res["reimplements_cases"]
        },
        "scratch_test_execution": {
            "returncode": test_run["returncode"],
            "executed_cases": test_run["num_tests"],
            "failures": test_run["num_failures"],
            "ignored": test_run["num_ignored"],
            "passed_tests": test_run["passed_tests"]
        },
        "learner_stub_unsolved": True,
        "maintenance_doc_verified": True
    }

    evidence = {
        "tools": tools,
        "inputs": inputs_data,
        "expected_vs_actual": expected_vs_actual,
        "results": results_data
    }

    save_artifacts(repo_root, evidence)
    print("\n[SUCCESS] All artifacts persisted to work/R48-T048/ successfully.")
    print("=== Task R48-T048 Checks Completed Successfully ===")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_checks())
