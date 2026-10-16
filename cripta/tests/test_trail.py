import unittest

from model.game_state import GameState
from model.room import Door, Exit, Room
from structures.history import History
from structures.trail import TRAIL_LIFETIME, PlayerTrail


def room_with_exits(*destinations, closed=()):
    room = Room(1, "Centro")
    for direction, destination in zip(("N", "S", "E", "O"), destinations):
        door = Door(1, destination, closed=destination in closed)
        room.add_exit(Exit(direction, destination, door))
    return room


class TestPlayerTrail(unittest.TestCase):
    def setUp(self):
        self.trail = PlayerTrail()

    def test_lifetime_is_400(self):
        self.assertEqual(TRAIL_LIFETIME, 400)

    def test_room_never_visited(self):
        self.assertIsNone(self.trail.time_at(5))
        self.assertFalse(self.trail.is_fresh(5, 0))

    def test_freshness_limit(self):
        self.trail.mark(1, 100)
        self.assertTrue(self.trail.is_fresh(1, 499))
        self.assertFalse(self.trail.is_fresh(1, 500))

    def test_trail_at_time_zero(self):
        self.trail.mark(1, 0)
        self.assertTrue(self.trail.is_fresh(1, 0))

    def test_mark_overwrites(self):
        self.trail.mark(1, 0)
        self.trail.mark(1, 300)
        self.assertEqual(self.trail.time_at(1), 300)

    def test_no_exits(self):
        self.assertIsNone(self.trail.freshest_exit(Room(1, "Cerrada"), 100))

    def test_picks_the_freshest(self):
        room = room_with_exits(3, 5, 2)
        self.trail.mark(3, 100)
        self.trail.mark(5, 300)
        self.trail.mark(2, 200)
        self.assertEqual(self.trail.freshest_exit(room, 350).destination, 5)

    def test_tie_goes_to_lower_room_id(self):
        room = room_with_exits(9, 4, 7)
        for room_id in (9, 4, 7):
            self.trail.mark(room_id, 200)
        self.assertEqual(self.trail.freshest_exit(room, 300).destination, 4)

    def test_ignores_stale_trails(self):
        room = room_with_exits(2, 3)
        self.trail.mark(2, 0)
        self.assertIsNone(self.trail.freshest_exit(room, 400))

    def test_ignores_closed_doors(self):
        room = room_with_exits(2, 3, closed=(2,))
        self.trail.mark(2, 300)
        self.trail.mark(3, 100)
        self.assertEqual(self.trail.freshest_exit(room, 350).destination, 3)

    def test_only_closed_doors(self):
        room = room_with_exits(2, closed=(2,))
        self.trail.mark(2, 300)
        self.assertIsNone(self.trail.freshest_exit(room, 350))


class TestReversibleTrail(unittest.TestCase):
    def setUp(self):
        self.history = History(GameState(seed=1))
        self.trail = PlayerTrail(self.history)

    def test_undo_overwrite(self):
        self.trail.mark(1, 40)
        self.history.begin_action()
        self.trail.mark(1, 300)
        self.history.undo()
        self.assertEqual(self.trail.time_at(1), 40)

    def test_undo_first_visit(self):
        self.history.begin_action()
        self.trail.mark(8, 300)
        self.history.undo()
        self.assertIsNone(self.trail.time_at(8))


if __name__ == "__main__":
    unittest.main()
