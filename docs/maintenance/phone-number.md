# Phone Number: Isolated Test Runner Rationale

- **Isolated Runner:** Executes tests for `exercises/practice/phone-number` using a temporary copy of the exercise directory, protecting the learner's starting files from unintended modifications.
- **Validation Command:** Run the isolated check script using:
  ```bash
  python3 work/R48-T039/check.py