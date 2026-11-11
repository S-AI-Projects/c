import os
import sys

def run_check():
    print("Running check for secret-handshake C-specific guidance task...")
    exercise_dir = "exercises/practice/secret-handshake"
    if not os.path.exists(exercise_dir):
        print(f"Error: Exercise directory {exercise_dir} not found.")
        sys.exit(1)
    print("Secret-handshake exercise structure verified successfully.")

if __name__ == "__main__":
    run_check()