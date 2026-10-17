import unittest

from structures.inventory import DoublyLinkedList, Inventory, _Node
from tests.objetos_persona3 import (
    make_armor,
    make_item,
    make_player,
    make_scroll,
    make_weapon,
    names,
)


def filled(capacity, *item_names):
    inventory = Inventory(capacity)
    for name in item_names:
        inventory.pick_up(make_item(name))
    inventory.go_to_start()
    return inventory


class TestDoublyLinkedList(unittest.TestCase):
    def setUp(self):
        self.items = DoublyLinkedList()
        self.nodes = [_Node(value) for value in ("a", "b", "c", "d")]
        for node in self.nodes:
            self.items.append(node)

    def test_both_directions(self):
        self.assertEqual(list(self.items), ["a", "b", "c", "d"])
        self.assertEqual(list(self.items.reversed_items()), ["d", "c", "b", "a"])

    def test_remove_anywhere(self):
        self.items.remove(self.nodes[1])
        self.items.remove(self.nodes[0])
        self.items.remove(self.nodes[3])
        self.assertEqual(list(self.items), ["c"])
        self.assertEqual(len(self.items), 1)

    def test_remove_unlinked_node(self):
        with self.assertRaises(ValueError):
            self.items.remove(_Node("x"))

    def test_move_to_front(self):
        self.items.move_to_front(self.nodes[2])
        self.assertEqual(list(self.items), ["c", "a", "b", "d"])

    def test_insert_twice_is_rejected(self):
        with self.assertRaises(ValueError):
            self.items.append(self.nodes[0])

    def test_insert_after_and_before(self):
        self.items.remove(self.nodes[2])
        self.items.insert_after(self.nodes[1], self.nodes[2])
        self.items.remove(self.nodes[0])
        self.items.insert_before(self.nodes[1], self.nodes[0])
        self.assertEqual(list(self.items), ["a", "b", "c", "d"])


class TestInventoryBasics(unittest.TestCase):
    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            Inventory(0)

    def test_empty(self):
        inventory = Inventory(3)
        self.assertTrue(inventory.is_empty())
        self.assertIsNone(inventory.current())
        self.assertFalse(inventory.next())
        self.assertFalse(inventory.previous())
        self.assertIsNone(inventory.drop_current(make_player()))
        self.assertFalse(inventory.can_equip_current())
        self.assertEqual(inventory.sorted_view("peso"), [])

    def test_full_rejects_pick_up(self):
        inventory = filled(2, "a", "b")
        self.assertTrue(inventory.is_full())
        self.assertFalse(inventory.pick_up(make_item("c")))
        self.assertEqual(names(inventory), ["a", "b"])

    def test_pick_up_after_dropping_when_full(self):
        inventory = filled(1, "a")
        inventory.drop_current()
        self.assertTrue(inventory.pick_up(make_item("b")))

    def test_forward_and_backward(self):
        inventory = filled(5, "a", "b", "c")
        self.assertEqual(inventory.current().name, "a")
        self.assertFalse(inventory.previous())
        self.assertTrue(inventory.next())
        self.assertTrue(inventory.next())
        self.assertFalse(inventory.next())
        self.assertEqual(inventory.current().name, "c")
        self.assertTrue(inventory.previous())
        self.assertEqual(inventory.current().name, "b")

    def test_pick_up_moves_cursor_to_the_new_item(self):
        inventory = filled(5, "a", "b")
        inventory.pick_up(make_item("c"))
        self.assertEqual(inventory.current().name, "c")
        self.assertEqual(names(inventory), ["a", "b", "c"])

    def test_pick_up_then_equip_without_next(self):
        player = make_player()
        inventory = filled(5, "pocion")
        inventory.pick_up(make_weapon("daga", attack_bonus=3))
        self.assertTrue(inventory.can_equip_current())
        inventory.equip_current(player)
        self.assertEqual(player.equipped_weapon.name, "daga")

    def test_rejected_pick_up_keeps_cursor(self):
        inventory = filled(1, "a")
        self.assertFalse(inventory.pick_up(make_item("b")))
        self.assertEqual(inventory.current().name, "a")

    def test_iterates_like_player_inventory(self):
        player = make_player()
        player.inventory = filled(5, "a", "b")
        self.assertEqual([item.name for item in player.inventory], ["a", "b"])


class TestDrop(unittest.TestCase):
    def test_drop_in_the_middle(self):
        inventory = filled(5, "a", "b", "c")
        inventory.next()
        self.assertEqual(inventory.drop_current().name, "b")
        self.assertEqual(names(inventory), ["a", "c"])
        self.assertEqual(inventory.current().name, "c")

    def test_drop_last_moves_cursor_back(self):
        inventory = filled(5, "a", "b")
        inventory.next()
        inventory.drop_current()
        self.assertEqual(inventory.current().name, "a")

    def test_drop_only_item(self):
        inventory = filled(5, "a")
        inventory.drop_current()
        self.assertTrue(inventory.is_empty())
        self.assertIsNone(inventory.current())

    def test_drop_equipped_unequips(self):
        player = make_player()
        inventory = Inventory(5)
        inventory.pick_up(make_weapon("daga", attack_bonus=3))
        inventory.equip_current(player)
        self.assertEqual(player.effective_attack, 9)
        inventory.drop_current(player)
        self.assertIsNone(player.equipped_weapon)
        self.assertEqual(player.effective_attack, 6)


class TestEquip(unittest.TestCase):
    def setUp(self):
        self.player = make_player()
        self.inventory = Inventory(10)
        self.inventory.pick_up(make_item("pocion"))
        self.inventory.pick_up(make_weapon("daga", attack_bonus=3))
        self.inventory.pick_up(make_armor("cota", defense_bonus=2))
        self.inventory.pick_up(make_weapon("hacha", attack_bonus=5))

    def go_to(self, name):
        self.inventory.go_to_start()
        while self.inventory.current().name != name:
            self.inventory.next()

    def test_moves_to_front(self):
        self.go_to("daga")
        self.assertIsNone(self.inventory.equip_current(self.player))
        self.assertEqual(names(self.inventory), ["daga", "pocion", "cota", "hacha"])
        self.assertEqual(self.player.equipped_weapon.name, "daga")

    def test_replaces_same_kind_and_keeps_it(self):
        self.go_to("daga")
        self.inventory.equip_current(self.player)
        self.go_to("hacha")
        self.assertEqual(self.inventory.equip_current(self.player).name, "daga")
        self.assertEqual(self.player.equipped_weapon.name, "hacha")
        self.assertIn("daga", names(self.inventory))
        self.assertEqual(self.player.effective_attack, 11)

    def test_weapon_and_armor_together(self):
        self.go_to("daga")
        self.inventory.equip_current(self.player)
        self.go_to("cota")
        self.inventory.equip_current(self.player)
        self.assertEqual(self.player.effective_attack, 9)
        self.assertEqual(self.player.effective_defense, 4)
        self.assertEqual(names(self.inventory)[:2], ["cota", "daga"])

    def test_not_equippable(self):
        self.go_to("pocion")
        self.assertFalse(self.inventory.can_equip_current())
        with self.assertRaises(ValueError):
            self.inventory.equip_current(self.player)

    def test_equipping_again_replaces_nothing(self):
        self.go_to("daga")
        self.inventory.equip_current(self.player)
        self.assertIsNone(self.inventory.equip_current(self.player))


class TestSortedViews(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory(10)
        self.inventory.pick_up(make_item("cuerda", weight=3, value=5))
        self.inventory.pick_up(make_item("Antorcha", weight=1, value=5))
        self.inventory.pick_up(make_item("bota", weight=2, value=9))

    def test_by_weight(self):
        self.assertEqual(names(self.inventory.sorted_view("peso")), ["Antorcha", "bota", "cuerda"])

    def test_by_value_descending_is_stable(self):
        self.assertEqual(
            names(self.inventory.sorted_view("valor", reverse=True)),
            ["bota", "cuerda", "Antorcha"],
        )

    def test_by_name_ignores_case(self):
        self.assertEqual(names(self.inventory.sorted_view("nombre")), ["Antorcha", "bota", "cuerda"])

    def test_real_order_unchanged(self):
        self.inventory.sorted_view("peso")
        self.assertEqual(names(self.inventory), ["cuerda", "Antorcha", "bota"])

    def test_invalid_criterion(self):
        with self.assertRaises(ValueError):
            self.inventory.sorted_view("color")


class TestScrolls(unittest.TestCase):
    def test_count_and_consume(self):
        inventory = Inventory(5)
        inventory.pick_up(make_item("a"))
        inventory.pick_up(make_scroll("p1"))
        inventory.pick_up(make_scroll("p2"))
        self.assertEqual(inventory.scroll_count(), 2)
        self.assertEqual(inventory.consume_scroll().name, "p1")
        self.assertEqual(inventory.scroll_count(), 1)
        self.assertEqual(names(inventory), ["a", "p2"])

    def test_consume_without_scrolls(self):
        self.assertIsNone(Inventory(5).consume_scroll())

    def test_scroll_takes_a_slot(self):
        inventory = Inventory(1)
        inventory.pick_up(make_scroll())
        self.assertFalse(inventory.pick_up(make_item("a")))


if __name__ == "__main__":
    unittest.main()
