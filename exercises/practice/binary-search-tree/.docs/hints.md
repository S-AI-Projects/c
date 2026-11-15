## Approach: Binary Search Tree Representation

- **Recursive Node Allocation (Reference):** Dynamically allocates individual nodes on the heap, linking left and right children pointers. It is clean and idiomatic for dynamic insertions, but incurs allocation overhead per node.
- **Alternative Representation:** Flat array or iterative allocation can reduce pointer-chasing overhead for static datasets, though dynamic updates become more complex.