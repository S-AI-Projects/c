#!/usr/bin/env python3
import pathlib, subprocess, sys
sys.exit(subprocess.call([sys.executable, str(pathlib.Path(__file__).resolve().parents[2] / "tools/course_checks/r48-t002.py"), *sys.argv[1:]]))
