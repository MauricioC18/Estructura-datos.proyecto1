import unittest

from model.item import Item
from model.room import DIRECTIONS, Door, Exit, Room, RoomMap, direction_index
from model.trap import DEFAULT_REARM_INTERVAL, Trap


class TestDirections(unittest.TestCase):

    def test_order_is_north_south_east_west(self):
        self.assertEqual(DIRECTIONS, ("N", "S", "E", "O"))

    def test_index_of_each_direction(self):
        for expected, direction in enumerate(DIRECTIONS):
            self.assertEqual(direction_index(direction), expected)

    def test_invalid_direction(self):
        for direction in ("W", "n", "", None):
            with self.assertRaises(ValueError):
                direction_index(direction)


class TestDoor(unittest.TestCase):

    def test_open_by_default(self):
        door = Door(1, 2)

        self.assertTrue(door.is_open)
        self.assertIsNone(door.key_id)
        self.assertIsNone(door.auto_close)

    def test_closed_with_key(self):
        door = Door(2, 5, closed=True, key_id="itm_llave_bronce", auto_close=500)

        self.assertFalse(door.is_open)
        self.assertEqual(door.key_id, "itm_llave_bronce")
        self.assertEqual(door.auto_close, 500)

    def test_other_side(self):
        door = Door(2, 5)

        self.assertEqual(door.other_side(2), 5)
        self.assertEqual(door.other_side(5), 2)
        self.assertTrue(door.connects(5))
        self.assertFalse(door.connects(3))

    def test_other_side_of_unrelated_room(self):
        with self.assertRaises(ValueError):
            Door(2, 5).other_side(3)


class TestRoom(unittest.TestCase):

    def test_new_room_is_empty(self):
        room = Room(1, "Entrada derruida")

        self.assertEqual(room.exits(), [])
        self.assertEqual(room.floor_items, [])
        self.assertEqual(room.traps, [])
        self.assertFalse(room.content_loaded)
        for direction in DIRECTIONS:
            self.assertIsNone(room.exit_towards(direction))

    def test_exits_come_back_in_direction_order(self):
        room = Room(2, "Pasillo de las urnas")
        room.add_exit(Exit("E", 5, Door(2, 5)))
        room.add_exit(Exit("S", 1, Door(1, 2)))
        room.add_exit(Exit("N", 3, Door(2, 3)))

        self.assertEqual([e.direction for e in room.exits()], ["N", "S", "E"])
        self.assertEqual(room.exit_towards("E").destination, 5)

    def test_two_exits_in_the_same_direction(self):
        room = Room(2, "Pasillo de las urnas")
        room.add_exit(Exit("N", 3, Door(2, 3)))

        with self.assertRaises(ValueError):
            room.add_exit(Exit("N", 4, Door(2, 4)))

    def test_shared_door_is_seen_from_both_rooms(self):
        door = Door(2, 5, closed=True)
        west_room = Room(2, "Pasillo")
        east_room = Room(5, "Nicho")
        west_room.add_exit(Exit("E", 5, door))
        east_room.add_exit(Exit("O", 2, door))

        west_room.exit_towards("E").door.closed = False

        self.assertTrue(east_room.exit_towards("O").door.is_open)


class TestRoomMap(unittest.TestCase):

    def test_lookup_by_id(self):
        room_map = RoomMap()
        for room_id in (3, 1, 2):
            room_map.add(Room(room_id, f"Sala {room_id}"))

        self.assertEqual(len(room_map), 3)
        self.assertEqual(room_map.room(2).name, "Sala 2")
        self.assertEqual(room_map.room_ids(), [3, 1, 2])
        self.assertTrue(room_map.contains(1))
        self.assertFalse(room_map.contains(9))

    def test_missing_room(self):
        with self.assertRaises(ValueError):
            RoomMap().room(9)

    def test_repeated_room(self):
        room_map = RoomMap()
        room_map.add(Room(1, "A"))

        with self.assertRaises(ValueError):
            room_map.add(Room(1, "B"))


class TestItemAndTrap(unittest.TestCase):

    def test_item_defaults_do_not_apply_bonuses(self):
        item = Item("o-1-0", "itm_antorcha", "Antorcha", Item.TORCH, 1, 5, duration=2000)

        self.assertEqual(item.attack_bonus, 0)
        self.assertEqual(item.defense_bonus, 0)
        self.assertEqual(item.duration, 2000)
        self.assertIsNone(item.opens)

    def test_item_class_constants_match_the_catalog(self):
        self.assertEqual(
            (Item.WEAPON, Item.ARMOR, Item.POTION, Item.ANTIDOTE,
             Item.KEY, Item.TORCH, Item.REWIND_SCROLL),
            ("arma", "armadura", "pocion", "antidoto",
             "llave", "antorcha", "pergamino_retroceso"),
        )

    def test_trap_starts_armed(self):
        trap = Trap("t-17", "trp_dardos", "Dardos en la pared", 4, DEFAULT_REARM_INTERVAL, 2)

        self.assertTrue(trap.armed)
        self.assertEqual(trap.rearm_interval, 300)


if __name__ == "__main__":
    unittest.main()
