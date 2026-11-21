/*
 * R48-T005 measurement harness. Scratch use only: check.py copies this file
 * next to a COPY of the reference (saddle_points.c / saddle_points.h) and
 * compiles it there. Nothing in this file belongs to the exercise.
 *
 * The harness #includes the reference translation unit so that the static
 * function is_greatest_in_row can be called directly, exactly the way
 * saddle_points() calls it: once for every cell of the grid.
 *
 * usage: harness <solve|sweep> <rows> <columns> <matrix-file> [reps]
 *   matrix-file holds rows*columns raw bytes (uint8_t), row-major.
 *
 *   solve  runs the real saddle_points() once and prints the number of
 *          saddle points plus an order-independent hash of their (row, col).
 *   sweep  plain build:   one untimed warm-up sweep, then `reps` timed
 *                         sweeps; each sweep makes the rows*columns calls to
 *                         is_greatest_in_row that saddle_points() makes.
 *                         Only the sweep is inside the timed region.
 *          counted build: (-DCOUNT_OPS) one sweep, printing executed calls and
 *                         comparisons, with per-call minimum and maximum.
 *   In the counted build, solve also prints the calls and comparisons made by
 *   the real saddle_points().
 */
/* glibc hides clock_gettime under -std=c99 without this; on Apple
   platforms the macro is unnecessary and can hide declarations. */
#if !defined(__APPLE__)
#define _POSIX_C_SOURCE 199309L
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifdef COUNT_OPS
/* Referenced by the counted copy of the reference (see check.py). */
static unsigned long long g_calls; /* calls of is_greatest_in_row */
static unsigned long long g_cmps;  /* executed "matrix[row][c] > candidate" */
#endif

#include "saddle_points.c"

/* splitmix64 finaliser; check.py mirrors this exactly. */
static uint64_t mix(uint64_t x)
{
   x += 0x9E3779B97F4A7C15ULL;
   x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
   x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
   return x ^ (x >> 31);
}

static int run_solve(size_t rows, size_t cols, uint8_t m[][cols])
{
   saddle_points_t *sp = saddle_points(rows, cols, m);
   if (sp == NULL) {
      fprintf(stderr, "saddle_points returned NULL\n");
      return 1;
   }

   uint64_t hash = 0;
   for (size_t i = 0; i < sp->count; ++i)
      hash += mix(((uint64_t)sp->points[i].row << 32) |
                  (uint64_t)sp->points[i].column);

   printf("count=%llu\n", (unsigned long long)sp->count);
   printf("hash=%016llx\n", (unsigned long long)hash);
#ifdef COUNT_OPS
   printf("calls=%llu\n", g_calls);
   printf("cmps=%llu\n", g_cmps);
#endif
   free_saddle_points(sp);
   return 0;
}

#ifdef COUNT_OPS
static int run_sweep(size_t rows, size_t cols, uint8_t m[][cols], unsigned reps)
{
   (void)reps;
   unsigned long long calls0 = g_calls, cmps0 = g_cmps;
   unsigned long long min = ~0ULL, max = 0, trues = 0;

   for (size_t r = 0; r < rows; ++r)
      for (size_t c = 0; c < cols; ++c) {
         unsigned long long before = g_cmps;
         trues += is_greatest_in_row(r, c, cols, m);
         unsigned long long used = g_cmps - before;
         if (used < min)
            min = used;
         if (used > max)
            max = used;
      }

   printf("sweep_calls=%llu\n", g_calls - calls0);
   printf("sweep_cmps=%llu\n", g_cmps - cmps0);
   printf("sweep_min_per_call=%llu\n", min);
   printf("sweep_max_per_call=%llu\n", max);
   printf("true=%llu\n", trues);
   return 0;
}
#else
/* The calls saddle_points() makes to is_greatest_in_row: one per cell. */
static unsigned long long sweep(size_t rows, size_t cols, uint8_t m[][cols])
{
   unsigned long long trues = 0;
   for (size_t r = 0; r < rows; ++r)
      for (size_t c = 0; c < cols; ++c)
         trues += is_greatest_in_row(r, c, cols, m);
   return trues;
}

static int run_sweep(size_t rows, size_t cols, uint8_t m[][cols], unsigned reps)
{
   /* A volatile pointer keeps the compiler from proving that every sweep
      reads the same data and hoisting the work out of the repetition loop. */
   uint8_t(*volatile vm)[cols] = m;
   volatile unsigned long long sink = sweep(rows, cols, vm); /* warm-up */
   unsigned long long expected = sink;

   printf("ns=");
   for (unsigned i = 0; i < reps; ++i) {
      struct timespec t0, t1;
      clock_gettime(CLOCK_MONOTONIC, &t0);
      sink = sweep(rows, cols, vm);
      clock_gettime(CLOCK_MONOTONIC, &t1);
      if (sink != expected) {
         fprintf(stderr, "sweep result changed between repetitions\n");
         return 1;
      }
      long long ns = (long long)(t1.tv_sec - t0.tv_sec) * 1000000000LL +
                     (long long)(t1.tv_nsec - t0.tv_nsec);
      printf("%s%lld", i ? "," : "", ns);
   }
   printf("\ntrue=%llu\n", expected);
   return 0;
}
#endif

int main(int argc, char **argv)
{
   if (argc < 5) {
      fprintf(stderr, "usage: %s <solve|sweep> rows cols file [reps]\n",
              argv[0]);
      return 2;
   }

   size_t rows = strtoul(argv[2], NULL, 10);
   size_t cols = strtoul(argv[3], NULL, 10);
   unsigned reps = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 1;
   if (rows == 0 || cols == 0) {
      fprintf(stderr, "rows and columns must be positive\n");
      return 2;
   }

   FILE *file = fopen(argv[4], "rb");
   if (file == NULL) {
      perror("fopen");
      return 2;
   }
   uint8_t(*m)[cols] = malloc(rows * sizeof *m);
   if (m == NULL) {
      fprintf(stderr, "out of memory\n");
      return 2;
   }
   size_t bytes = rows * cols;
   if (fread(m, 1, bytes, file) != bytes || fgetc(file) != EOF) {
      fprintf(stderr, "matrix file is not exactly rows*columns bytes\n");
      return 2;
   }
   fclose(file);

   int status = 2;
   if (argv[1][0] == 's' && argv[1][1] == 'o')
      status = run_solve(rows, cols, m);
   else if (argv[1][0] == 's' && argv[1][1] == 'w')
      status = run_sweep(rows, cols, m, reps);
   else
      fprintf(stderr, "unknown mode %s\n", argv[1]);

   free(m);
   return status;
}
