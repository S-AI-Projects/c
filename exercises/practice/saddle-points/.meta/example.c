#include "saddle_points.h"
#include <stdlib.h>
#include <stdbool.h>

static saddle_points_t *noSaddlePoints(void)
{
   saddle_points_t *saddle_points = malloc(sizeof(saddle_points_t));

   if (saddle_points)
      saddle_points->count = 0;

   return saddle_points;
}

static saddle_points_t *add(saddle_points_t *saddle_points, size_t row,
                            size_t column)
{
   size_t count = 0;
   if (saddle_points)
      count = saddle_points->count;

   saddle_points_t *new_saddle_points =
       realloc(saddle_points,
               sizeof(saddle_points_t) + sizeof(saddle_point_t) * ++count);

   if (new_saddle_points) {
      saddle_points = new_saddle_points;
      saddle_points->count = count;
      saddle_points->points[count - 1] = (saddle_point_t){ row, column };
   } else {
      free(saddle_points);
      saddle_points = NULL;
   }

   return saddle_points;
}

/*
 * is_greatest_in_row: true if matrix[row][column] is >= every element of its
 * row. Ties count, so every maximum of a row qualifies.
 *
 * Invariant: when the loop tests index c, matrix[row][0..c-1] are all
 * <= candidate. The first element greater than candidate ends the scan.
 *
 * Cost, with C = columns: one comparison per iteration, O(1) extra space.
 *   best case:  1 comparison (matrix[row][0] > candidate);
 *   worst case: C comparisons (candidate is a row maximum: full scan).
 * saddle_points() calls this once for each of the R * C cells (it is the left
 * operand of &&, so it is never skipped). Over a whole grid of R rows the
 * function therefore executes between R * (2C - 1) and R * C * C comparisons.
 * Measurements: docs/maintenance/saddle-points.md.
 *
 * The index parameters are int16_t, so row and column indices above 32767 are
 * outside what this reference supports.
 */
static bool is_greatest_in_row(int16_t row, int16_t column, size_t columns,
                               uint8_t matrix[][columns])
{
   uint8_t candidate = matrix[row][column];
   for (size_t c = 0; c < columns; ++c)
      if (matrix[row][c] > candidate)
         return false;
   return true;
}

static bool is_least_in_column(int16_t row, int16_t column, size_t rows,
                               size_t columns, uint8_t matrix[][columns])
{
   uint8_t candidate = matrix[row][column];
   for (size_t r = 0; r < rows; ++r)
      if (matrix[r][column] < candidate)
         return false;
   return true;
}

saddle_points_t *saddle_points(size_t rows, size_t columns,
                               uint8_t matrix[][columns])
{
   saddle_points_t *saddle_points = noSaddlePoints();

   if (rows > 0 && columns > 0 && matrix != NULL)
      for (size_t row = 0; row < rows; ++row)
         for (size_t column = 0; column < columns; ++column)
            if (is_greatest_in_row(row, column, columns, matrix) &&
                is_least_in_column(row, column, rows, columns, matrix))
               saddle_points = add(saddle_points, row + 1, column + 1);

   return saddle_points;
}

void free_saddle_points(saddle_points_t *saddle_points)
{
   free(saddle_points);
}
