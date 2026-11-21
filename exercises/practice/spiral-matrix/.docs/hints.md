# Hints

## C-Specific Guidance

### Memory layout: pointer-to-pointer vs flat array

The reference allocates the matrix as `int **matrix` — a pointer to an array
of row pointers, each row separately heap-allocated with `calloc`:

```c
spiral->matrix = calloc(size, sizeof(int *));   /* array of row pointers */
for (int i = 0; i < size; i++) {
    spiral->matrix[i] = calloc(size, sizeof(int)); /* each row */
}
```

This gives the natural `matrix[row][col]` indexing but requires **two
allocations per row** plus the pointer array itself. Every `free` must mirror
every `calloc`, which is why `spiral_matrix_destroy` loops over rows before
freeing the pointer array.

**An alternative** is a single flat allocation (`int *data = calloc(size*size,
sizeof(int))`) with manual index arithmetic (`data[row*size + col]`). That
reduces to two `calloc`/`free` calls total but loses the `[][]` syntax.

### Direction-vector rotation

The reference tracks position `(x, y)` and direction `(dx, dy)`:

```c
int x = 0, y = 0;
int dx = 1, dy = 0;   /* start moving right */
```

To turn right 90°, the reference rotates the direction vector in-place:

```c
int new_dx = -dy;
int new_dy =  dx;
dx = new_dx;
dy = new_dy;
```

The rotation formula `(dx, dy) → (−dy, dx)` is a standard 2-D 90°-clockwise
rotation. Write it out for all four directions to convince yourself:

| Current direction | (dx, dy) | After rotation | (−dy, dx) |
|---|---|---|---|
| Right | (1, 0) | Down | (0, 1) |
| Down | (0, 1) | Left | (−1, 0) |
| Left | (−1, 0) | Up | (0, −1) |
| Up | (0, −1) | Right | (1, 0) |

The temporary variable is required because `dy`'s new value depends on `dx`'s
old value; computing both from the originals and then assigning avoids the
aliasing hazard.

### Turn condition

A turn happens whenever the **next cell** would be out of bounds **or already
filled**:

```c
if (x + dx >= size || x + dx < 0 ||
    y + dy >= size || y + dy < 0 ||
    spiral->matrix[y + dy][x + dx] != 0) {
    /* rotate direction */
}
```

`calloc` zeroes the allocation, so an unvisited cell is reliably `0` and a
visited cell is `>= 1`. The turn check uses this invariant directly — there is
no need for a separate visited array.

### Why the turn check comes before the step

The reference checks whether to turn *before* moving:

```c
spiral->matrix[y][x] = i;   /* fill current cell */
/* check and maybe turn */
x += dx;                     /* then step */
y += dy;
```

Placing the check here means the direction is correct for the *next* fill, not
the current one. The alternative — checking after the step — would require
backing up or using look-ahead, complicating the loop.

### Edge case: size == 0

`size * size` is 0, so the loop never executes. `spiral->matrix` is left as
`NULL` (from `calloc`). The test checks `actual->matrix == NULL` for this case,
so the guard `if (size == 0) return spiral;` is essential — without it the
subsequent `calloc(0, ...)` and the destroy loop would be undefined or
platform-dependent.
