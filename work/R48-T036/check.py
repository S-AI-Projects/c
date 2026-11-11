import os
import sys

def run_check():
    print("Running check for binary-search-tree approach comparison task...")
    exercise_dir = "exercises/practice/binary-search-tree"
    if not os.path.exists(exercise_dir):
        print(f"Error: Exercise directory {exercise_dir} not found.")
        sys.exit(1)
    print("Binary search tree exercise structure verified successfully.")

if __name__ == "__main__":
    run_check()