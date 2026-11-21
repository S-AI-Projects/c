#include <string.h>
#include "robot_simulator.h"

enum {
   INSTRUCTION_LEFT = 'L',
   INSTRUCTION_RIGHT = 'R',
   INSTRUCTION_ADVANCE = 'A'
};

robot_status_t robot_create(robot_direction_t direction, int x, int y)
{
   robot_status_t robot = { direction, { x, y } };

   if ((direction < DIRECTION_NORTH) || (direction >= DIRECTION_MAX))
      robot.direction = DIRECTION_DEFAULT;

   return robot;
}

// Complexity: O(1) time, O(1) space.
// Invariant: robot->direction remains in the fixed finite cyclic domain
// [0, DIRECTION_MAX) ([0, 4)), advancing clockwise by 1:
// NORTH (0) -> EAST (1) -> SOUTH (2) -> WEST (3) -> NORTH (0).
// Executes exactly 1 addition and 1 modulo operation per call without branches or allocations.
static void robot_turn_right(robot_status_t *robot)
{
   robot->direction = (robot->direction + 1) % DIRECTION_MAX;
}

static void robot_turn_left(robot_status_t *robot)
{
   robot->direction = ((robot->direction - 1) + DIRECTION_MAX) % DIRECTION_MAX;
}

static void robot_advance(robot_status_t *robot)
{
   switch (robot->direction) {
      case DIRECTION_NORTH:
         robot->position.y++;
         break;

      case DIRECTION_EAST:
         robot->position.x++;
         break;

      case DIRECTION_SOUTH:
         robot->position.y--;
         break;

      case DIRECTION_WEST:
         robot->position.x--;
         break;

      default:
         break;
   }
}

void robot_move(robot_status_t *robot, const char *instructions)
{
   for (unsigned long index = 0; index < strlen(instructions); index++) {
      switch (instructions[index]) {
         case INSTRUCTION_LEFT:
            robot_turn_left(robot);
            break;

         case INSTRUCTION_RIGHT:
            robot_turn_right(robot);
            break;

         case INSTRUCTION_ADVANCE:
            robot_advance(robot);
            break;

         default:
            break;
      }
   }
}
