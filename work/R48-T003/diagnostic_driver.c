/* R48-T003 differential driver.
 *
 * Reads "min max" pairs (one per line) from stdin, calls get_palindrome_product()
 * for each, and prints one normalised line per pair. It is linked against exactly
 * one implementation per build, so the same input file can be run against the
 * maintained reference and against a mutant and the outputs compared line by line.
 *
 * Output (one line per input):
 *   <min> <max> OK smallest=<n> sm=<a*b,...> largest=<n> lg=<a*b,...>
 *   <min> <max> ERROR <message>
 *   <min> <max> NULL
 *
 * A result is reported as ERROR when the implementation left a sentinel in
 * `smallest` or `largest`; that is the only case in which `error` is guaranteed
 * to have been written.
 */
#include "palindrome_products.h"

#include <limits.h>
#include <stdio.h>

static void print_factors(const factor_t *f)
{
   const char *sep = "";
   for (; f != NULL; f = f->next) {
      printf("%s%d*%d", sep, f->factor_a, f->factor_b);
      sep = ",";
   }
}

int main(void)
{
   int from, to;
   while (scanf("%d %d", &from, &to) == 2) {
      product_t *p = get_palindrome_product(from, to);
      if (p == NULL) {
         printf("%d %d NULL\n", from, to);
         continue;
      }
      if (p->smallest == INT_MAX || p->largest == INT_MIN) {
         printf("%d %d ERROR %s\n", from, to, p->error);
      } else {
         printf("%d %d OK smallest=%d sm=", from, to, p->smallest);
         print_factors(p->factors_sm);
         printf(" largest=%d lg=", p->largest);
         print_factors(p->factors_lg);
         printf("\n");
      }
      free_product(p);
   }
   return 0;
}
