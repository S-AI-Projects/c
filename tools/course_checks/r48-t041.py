#!/usr/bin/env python3
"""
tools/course_checks/r48-t041.py
Course check runner for Task R48-T041:
Explain the canonical-case decisions for darts [exercises/practice/darts] #41
"""

import os
import sys

# Add work/R48-T041 to path or invoke check.py directly
curr_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(curr_dir, "../.."))
check_script = os.path.join(repo_root, "work/R48-T041/check.py")

if __name__ == "__main__":
    if not os.path.exists(check_script):
        print(f"Error: check script not found at {check_script}", file=sys.stderr)
        sys.exit(1)
    
    # Execute check script
    import subprocess
    res = subprocess.run([sys.executable, check_script], cwd=repo_root)
    sys.exit(res.returncode)
