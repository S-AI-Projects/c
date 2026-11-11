import os
import sys

def run_check():
    print("Running check for bob exercise test generation path...")
    exercise_dir = "exercises/practice/bob"
    if not os.path.exists(exercise_dir):
        print(f"Error: Exercise directory {exercise_dir} not found.")
        sys.exit(1)
    
    docs_file = os.path.join(exercise_dir, ".docs", "bob.md")
    if not os.path.exists(docs_file):
        print(f"Error: Maintenance docs file {docs_file} not found.")
        sys.exit(1)
        
    print("Bob exercise structure and documentation verified successfully.")

if __name__ == "__main__":
    run_check()