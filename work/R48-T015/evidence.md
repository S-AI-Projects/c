# R48-T015 evidence

Exercise: `/Users/tanmayaverma/Documents/Snai/c/exercises/practice/robot-simulator`
Inputs: solution=['robot_simulator.c', 'robot_simulator.h'] | test=['test_robot_simulator.c'] | example=['.meta/example.c']
Python: 3.9.6
Tool versions: {"python": "3.9.6", "make": "GNU Make 3.81", "cc": "Apple clang version 21.0.0 (clang-2100.4.1.1)"}

## Expected vs Actual

| Check | Expected | Actual |
|-------|----------|--------|
| Reference passes all unit tests | True | True |
| Unity tests run (N) | 18 | 18 |
| Unity failures (M) | 0 | 0 |
| Unity ignored (K) | 0 | 0 |
| Learner stub unsolved | True | True |
| Complexity/invariant comment adjacent to `robot_turn_right` | True | True |
| Correctness asserted before timing | True | True |
| Measured across 3 input sizes (N=10, 100, 1000) | True | True |
| Repetitions per size (>= 5) | >= 5 | 7 |

## Benchmark Results (Median ns)
- Size N=10: 0.0 ns (0.00 ns/turn)
- Size N=100: 0.0 ns (0.00 ns/turn)
- Size N=1000: 34000.0 ns (34.00 ns/turn)

Result: PASS. All 18 Unity cases ran and passed with 0 failures. Scaling study demonstrates strictly O(1) cost per turn.
