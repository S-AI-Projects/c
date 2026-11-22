#include <stdio.h>
#include "clock.h"

static const char CLOCK_FORMAT[] = "%02d:%02d";

/*
 * Invariants and Computational Complexity of normalize_clock:
 *
 * Preconditions:
 *   - 'hour' and 'minute' are valid, non-null pointers to signed integers.
 *
 * Postconditions / Invariants:
 *   - 0 <= *hour < 24
 *   - 0 <= *minute < 60
 *   - Time equivalence invariant:
 *       (60 * (*hour) + (*minute)) == (60 * hour_in + minute_in) (mod 1440)
 *
 * Cost Analysis across Exercise Domain:
 *   Let k_m = max(0, ceil(-minute_in / 60)) and
 *       k_h = max(0, ceil(-(hour_in - k_m + floor(max(0, minute_in) / 60)) / 24)).
 *
 *   1. Non-negative inputs (hour >= 0, minute >= 0) [e.g. Size 1: (8, 0)]:
 *      Loops do not iterate (k_m = 0, k_h = 0). Evaluates 2 exit conditions,
 *      1 division, 1 addition, and 2 modulos. Exactly 6 operations: O(1) time.
 *
 *   2. Positive rollovers (hour >= 24 or minute >= 60) [e.g. Size 2: (201, 3001)]:
 *      Loops do not iterate (k_m = 0, k_h = 0). Handled via integer division
 *      (*hour += *minute / 60) and modulos (*hour %= 24, *minute %= 60).
 *      Exactly 6 operations: strictly O(1) time regardless of magnitude.
 *
 *   3. Negative rollbacks (hour < 0 or minute < 0) [e.g. Size 3: (-121, -5810)]:
 *      C99 integer division truncates towards zero; the reference relies on
 *      iterative borrow loops adding 60/24 per step.
 *      Executes (3*k_m + 2*k_h + 6) operations: O(k_m + k_h) = O(|minute|/60 + |hour|/24) time.
 *
 * Space Complexity:
 *   - O(1) auxiliary space (in-place pointer normalization).
 */
static void normalize_clock(int *hour, int *minute)
{
   while (*minute < 0) {
      *minute += 60;
      *hour -= 1;
   }
   *hour += *minute / 60;
   while (*hour < 0) {
      *hour += 24;
   }
   *hour %= 24;
   *minute %= 60;
}

static void to_int(clock_t clock, int *hour, int *minute)
{
   sscanf(clock.text, CLOCK_FORMAT, hour, minute);
}

clock_t clock_create(int hour, int minute)
{
   clock_t clock = { { 0 } };
   normalize_clock(&hour, &minute);
   snprintf(clock.text, MAX_STR_LEN, CLOCK_FORMAT, hour, minute);
   return clock;
}

clock_t clock_add(clock_t clock, int minute_add)
{
   int hour = 0, minute = 0;
   to_int(clock, &hour, &minute);
   minute += minute_add;
   return clock_create(hour, minute);
}

clock_t clock_subtract(clock_t clock, int minute_subtract)
{
   int hour = 0, minute = 0;
   to_int(clock, &hour, &minute);
   minute -= minute_subtract;
   return clock_create(hour, minute);
}

bool clock_is_equal(clock_t a, clock_t b)
{
   int ah = 0, am = 0, bh = 0, bm = 0;
   to_int(a, &ah, &am);
   to_int(b, &bh, &bm);
   normalize_clock(&ah, &am);
   normalize_clock(&bh, &bm);
   return (ah == bh) && (am == bm);
}
