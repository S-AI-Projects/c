import os
import sys

def run_check():
    print("Running check for largest-series-product metadata task...")
    exercise_dir = "exercises/practice/largest-series-product"
    if not os.path.exists(exercise_dir):
        print(f"Error: Exercise directory {exercise_dir} not found.")
        sys.exit(1)
    print("Largest-series-product exercise structure verified successfully.")

if __name__ == "__main__":
    run_check()