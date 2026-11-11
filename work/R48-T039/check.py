import os
import sys

def run_check():
    print("Running check for phone-number isolated test runner task...")
    exercise_dir = "exercises/practice/phone-number"
    if not os.path.exists(exercise_dir):
        print(f"Error: Exercise directory {exercise_dir} not found.")
        sys.exit(1)
    print("Phone-number exercise structure verified successfully.")

if __name__ == "__main__":
    run_check()