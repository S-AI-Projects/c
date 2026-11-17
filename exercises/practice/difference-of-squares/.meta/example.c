#include "difference_of_squares.h"

unsigned int sum_of_squares(unsigned int number)
{
   unsigned int total = 0;

   // Invariant: after adding natural number n, total == 1*1 + 2*2 + ... + n*n.
   // Counting from 1 matches "the first N natural numbers" (0 adds nothing).
   for (unsigned int n = 1; n <= number; n++) {
      total += n * n;
   }

   return total;
}

unsigned int square_of_sum(unsigned int number)
{
   unsigned int sum = 0;

   for (unsigned int i = 0; i <= number; i++) {
      sum += i;
   }

   return (sum * sum);
}

unsigned int difference_of_squares(unsigned int number)
{
   return (square_of_sum(number) - sum_of_squares(number));
}
