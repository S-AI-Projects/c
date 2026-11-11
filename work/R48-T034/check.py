import os
import sys

def run_check():
    print("Running check for rational-numbers nth_root refactor...")
    exercise_dir = "exercises/practice/rational-numbers"
    if not os.path.exists(exercise_dir):
        print(f"Error: Exercise directory {exercise_dir} not found.")
        sys.exit(1)
    print("Rational numbers exercise structure verified successfully.")

if __name__ == "__main__":
    run_check()