#!/usr/bin/env python3
"""
Verification check for Task R48-T026:
Explain two approaches to protein-translation in C [exercises/practice/protein-translation]
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

def get_tool_version(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.splitlines()[0].strip()
    except Exception as e:
        return f"Error: {e}"

def clean_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

ALT_APPROACH_C = """
#include <string.h>
#include <stdint.h>
#include "protein_translation.h"

enum { codon_length = 3 };

#define PACK_CODON(c1, c2, c3) (((uint32_t)(uint8_t)(c1) << 16) | ((uint32_t)(uint8_t)(c2) << 8) | (uint32_t)(uint8_t)(c3))

typedef enum {
   CODON_INVALID,
   CODON_AMINO,
   CODON_STOP
} codon_type_t;

static codon_type_t translate_codon(uint32_t key, amino_acid_t *acid)
{
   switch (key) {
      case PACK_CODON('A', 'U', 'G'):
         *acid = Methionine;
         return CODON_AMINO;
      case PACK_CODON('U', 'U', 'U'):
      case PACK_CODON('U', 'U', 'C'):
         *acid = Phenylalanine;
         return CODON_AMINO;
      case PACK_CODON('U', 'U', 'A'):
      case PACK_CODON('U', 'U', 'G'):
         *acid = Leucine;
         return CODON_AMINO;
      case PACK_CODON('U', 'C', 'U'):
      case PACK_CODON('U', 'C', 'C'):
      case PACK_CODON('U', 'C', 'A'):
      case PACK_CODON('U', 'C', 'G'):
         *acid = Serine;
         return CODON_AMINO;
      case PACK_CODON('U', 'A', 'U'):
      case PACK_CODON('U', 'A', 'C'):
         *acid = Tyrosine;
         return CODON_AMINO;
      case PACK_CODON('U', 'G', 'U'):
      case PACK_CODON('U', 'G', 'C'):
         *acid = Cysteine;
         return CODON_AMINO;
      case PACK_CODON('U', 'G', 'G'):
         *acid = Tryptophan;
         return CODON_AMINO;
      case PACK_CODON('U', 'A', 'A'):
      case PACK_CODON('U', 'A', 'G'):
      case PACK_CODON('U', 'G', 'A'):
         return CODON_STOP;
      default:
         return CODON_INVALID;
   }
}

protein_t protein(const char *const rna)
{
   protein_t result = { .valid = true, .count = 0 };
   size_t rna_length = strlen(rna);

   for (size_t i = 0; i < rna_length; i += codon_length) {
      if (i + codon_length > rna_length) {
         result.valid = false;
         return result;
      }

      uint32_t key = PACK_CODON(rna[i], rna[i + 1], rna[i + 2]);
      amino_acid_t acid = (amino_acid_t)0;
      codon_type_t type = translate_codon(key, &acid);

      if (type == CODON_STOP) {
         return result;
      } else if (type == CODON_AMINO) {
         result.amino_acids[result.count++] = acid;
      } else {
         result.valid = false;
         return result;
      }
   }

   return result;
}
"""

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/protein-translation"
    exercise_path = os.path.join(repo_root, exercise_rel)
    work_dir = os.path.join(repo_root, "work/R48-T026")
    os.makedirs(work_dir, exist_ok=True)

    print("=== Running R48-T026 Verification Check ===")

    # 1. Tool versions
    tools = {
        "python": sys.version.split()[0],
        "cc": get_tool_version(["cc", "--version"]),
        "make": get_tool_version(["make", "--version"])
    }
    print(f"Tool versions: Python {tools['python']}, CC: {tools['cc']}, Make: {tools['make']}")

    # 2. Verify working tree learner stub is unsolved
    learner_c = os.path.join(exercise_path, "protein_translation.c")
    with open(learner_c, "r") as f:
        c_code = f.read()
    is_stub_unsolved = ("protein(" not in c_code or "return" not in c_code)
    assert is_stub_unsolved, "Assertion failed: Learner stub in working tree appears solved!"
    print("[PASS] Working tree learner stub is unsolved.")

    # 3. Check maintenance documentation
    maint_file = os.path.join(exercise_path, ".meta/MAINTENANCE.md")
    assert os.path.exists(maint_file), "Assertion failed: .meta/MAINTENANCE.md is missing!"
    with open(maint_file, "r") as f:
        maint_content = f.read()

    assert "Linear Table Lookup" in maint_content, "Assertion failed: Approach 1 missing in doc"
    assert "Integer Bit-Packed" in maint_content, "Assertion failed: Approach 2 missing in doc"
    assert "Trade-offs" in maint_content, "Assertion failed: Trade-offs missing in doc"
    print("[PASS] Maintenance documentation verified (.meta/MAINTENANCE.md).")

    # 4. Check tests.toml
    tests_toml_file = os.path.join(exercise_path, ".meta/tests.toml")
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    target_uuid = "96d3d44f-34a2-4db4-84cd-fff523e069be"
    assert target_uuid in toml_data, f"Assertion failed: UUID {target_uuid} missing in tests.toml"
    assert "comment" in toml_data[target_uuid], "Assertion failed: comment key missing for Methionine case"
    assert "linear table lookup" in toml_data[target_uuid]["comment"].lower(), "Assertion failed: comment missing approach hint"
    print(f"[PASS] tests.toml verified: {toml_data[target_uuid]['comment']}")

    # 5. Load config.json
    config_file = os.path.join(exercise_path, ".meta/config.json")
    with open(config_file, "r") as f:
        config = json.load(f)

    solution_files = config["files"]["solution"]
    test_files = config["files"]["test"]
    example_files = config["files"]["example"]

    # 6. Run Approach 1 (Reference) make test
    with tempfile.TemporaryDirectory() as tmpdir_ref:
        tmp_exercise_ref = os.path.join(tmpdir_ref, "protein-translation")
        shutil.copytree(exercise_path, tmp_exercise_ref)

        for sol_rel, ex_rel in zip(solution_files, example_files):
            shutil.copy(os.path.join(tmp_exercise_ref, ex_rel), os.path.join(tmp_exercise_ref, sol_rel))

        for tf in test_files:
            tf_path = os.path.join(tmp_exercise_ref, tf)
            with open(tf_path, "r") as f:
                content = f.read()
            content = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w") as f:
                f.write(content)

        run_ref = subprocess.run(["make", "test"], cwd=tmp_exercise_ref, capture_output=True, text=True)
        assert run_ref.returncode == 0, f"Assertion failed: Approach 1 make test failed: {run_ref.stderr}"

        clean_out_ref = clean_ansi(run_ref.stdout)
        summary_ref = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_out_ref)
        assert summary_ref is not None, "Assertion failed: Could not parse Approach 1 test summary"
        ref_runs = int(summary_ref.group(1))
        ref_fails = int(summary_ref.group(2))
        ref_ignored = int(summary_ref.group(3))

        assert ref_runs == 31, f"Assertion failed: Expected 31 tests, got {ref_runs}"
        assert ref_fails == 0, f"Assertion failed: Approach 1 had {ref_fails} failures"
        assert ref_ignored == 0, f"Assertion failed: Approach 1 had {ref_ignored} ignored"
        print(f"[PASS] Approach 1 (Reference Table Lookup) passed all {ref_runs} tests.")

    # 7. Run Approach 2 (Alternative Bit-Packed) make test
    with tempfile.TemporaryDirectory() as tmpdir_alt:
        tmp_exercise_alt = os.path.join(tmpdir_alt, "protein-translation")
        shutil.copytree(exercise_path, tmp_exercise_alt)

        # Substitute alternative C implementation
        sol_c_path = os.path.join(tmp_exercise_alt, "protein_translation.c")
        with open(sol_c_path, "w") as f:
            f.write(ALT_APPROACH_C)
        shutil.copy(os.path.join(tmp_exercise_alt, ".meta/example.h"), os.path.join(tmp_exercise_alt, "protein_translation.h"))

        for tf in test_files:
            tf_path = os.path.join(tmp_exercise_alt, tf)
            with open(tf_path, "r") as f:
                content = f.read()
            content = re.sub(r'^\s*TEST_IGNORE\(\);\s*(//.*)?$', '', content, flags=re.MULTILINE)
            with open(tf_path, "w") as f:
                f.write(content)

        run_alt = subprocess.run(["make", "test"], cwd=tmp_exercise_alt, capture_output=True, text=True)
        assert run_alt.returncode == 0, f"Assertion failed: Approach 2 make test failed: {run_alt.stderr}"

        clean_out_alt = clean_ansi(run_alt.stdout)
        summary_alt = re.search(r'(\d+)\s+Tests\s+(\d+)\s+Failures\s+(\d+)\s+Ignored', clean_out_alt)
        assert summary_alt is not None, "Assertion failed: Could not parse Approach 2 test summary"
        alt_runs = int(summary_alt.group(1))
        alt_fails = int(summary_alt.group(2))
        alt_ignored = int(summary_alt.group(3))

        assert alt_runs == 31, f"Assertion failed: Expected 31 tests, got {alt_runs}"
        assert alt_fails == 0, f"Assertion failed: Approach 2 had {alt_fails} failures"
        assert alt_ignored == 0, f"Assertion failed: Approach 2 had {alt_ignored} ignored"
        print(f"[PASS] Approach 2 (Bit-Packed Switch Dispatch) passed all {alt_runs} tests.")

    # 8. Save evidence
    evidence = {
        "task_id": "R48-T026",
        "exercise": "protein-translation",
        "tools": tools,
        "learner_stub_unsolved": is_stub_unsolved,
        "approach_1": {
            "name": "Linear Table Lookup with String Matching (Reference)",
            "technique": "Array of struct translations with strncmp",
            "tests_run": ref_runs,
            "failures": ref_fails,
            "ignored": ref_ignored,
            "status": "PASS"
        },
        "approach_2": {
            "name": "Integer Bit-Packed Switch Dispatch (Alternative)",
            "technique": "24-bit packed codon integer key with direct switch evaluation",
            "tests_run": alt_runs,
            "failures": alt_fails,
            "ignored": alt_ignored,
            "status": "PASS"
        },
        "comparison_result": "Both approaches passed all 31 tests identically with 0 failures",
        "status": "SUCCESS"
    }

    results_file = os.path.join(work_dir, "results.json")
    with open(results_file, "w") as f:
        json.dump(evidence, f, indent=2)

    summary_file = os.path.join(work_dir, "check_output.txt")
    with open(summary_file, "w") as f:
        f.write("Task R48-T026 Verification Check Results\n")
        f.write("-----------------------------------------\n")
        f.write(f"Tools:\n  Python: {tools['python']}\n  CC: {tools['cc']}\n  Make: {tools['make']}\n\n")
        f.write(f"Approach 1 (Reference Table Lookup): 31/31 tests passed (0 failures, 0 ignored)\n")
        f.write(f"Approach 2 (Bit-Packed Switch Dispatch): 31/31 tests passed (0 failures, 0 ignored)\n\n")
        f.write(f"Both implementations independently satisfy the contract and pass all test cases.\n")
        f.write(f"Learner stub in working tree: UNSOLVED\n")

    print(f"\n[SUCCESS] All checks passed. Evidence saved to {results_file} and {summary_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
