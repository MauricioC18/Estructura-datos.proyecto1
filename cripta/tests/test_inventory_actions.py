import unittest

from model.game import Game, IN_PROGRESS
from model.game_state import GameState
from model.item import Item
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from structures.inventory import Inventory


def make_item(item_class, name="Objeto", type_id="itm_x", instance_id="i-1", **extra):
    return Item(
        instance_id=instance_id,
        type_id=type_id,
        name=name,
        item_class=item_class,
        weight=1,
        value=1,
        **extra,
    )


def weapon(bonus=3, instance_id="i-arma", name="Daga"):
    return make_item(Item.WEAPON, name, "itm_daga", instance_id, attack_bonus=bonus)


def armor(bonus=2, instance_id="i-armadura", name="Coraza"):
    return make_item(Item.ARMOR, name, "itm_coraza", instance_id, defense_bonus=bonus)


def healing_potion(heal=8, instance_id="i-pocion"):
    return make_item(Item.POTION, "Pocion", "itm_pocion", instance_id, heal=heal)


def speed_potion(modifier=50, duration=300, instance_id="i-veloz"):
    return make_item(
        Item.POTION,
        "Pocion de velocidad",
        "itm_veloz",
        instance_id,
        speed_modifier=modifier,
        duration=duration,
    )


def torch(duration=500, instance_id="i-antorcha"):
    return make_item(Item.TORCH, "Antorcha", "itm_antorcha", instance_id, duration=duration)


def antidote(instance_id="i-antidoto"):
    return make_item(Item.ANTIDOTE, "Antidoto", "itm_antidoto", instance_id)


def scroll(instance_id="i-pergamino"):
    return make_item(Item.REWIND_SCROLL, "Pergamino", "itm_pergamino", instance_id)


def make_map():
    a, b = Room(1, "Sala 1"), Room(2, "Sala 2")
    a.content_loaded = b.content_loaded = True
    door = Door(1, 2)
    a.add_exit(Exit("N", 2, door))
    b.add_exit(Exit("S", 1, door))
    room_map = RoomMap()
    room_map.add(a)
    room_map.add(b)

    return room_map


def make_game(capacity=10, floor=(), max_health=100, defense=10):
    room_map = make_map()
    room_map.room(1).floor_items.extend(floor)
    player = Player("p-1", "Heroe", max_health, 6, defense, 100, 1)
    player.inventory = Inventory(capacity)

    return Game(GameState(seed=2026), player, None, room_map=room_map), room_map


class TestPickUp(unittest.TestCase):

    def test_picking_up_moves_the_item_from_the_floor(self):
        item = weapon()
        game, room_map = make_game(floor=[item])

        result = game.pick_up(0)

        self.assertTrue(result.accepted)
        self.assertEqual(room_map.room(1).floor_items, [])
        self.assertIs(game.player.inventory.current(), item)

    def test_picking_up_costs_twenty_five(self):
        game, _ = make_game(floor=[weapon()])

        game.pick_up(0)

        self.assertEqual(game.state.clock, 25)

    def test_a_full_inventory_rejects_without_consuming_time(self):
        game, room_map = make_game(
            capacity=1, floor=[weapon("i-1"), armor("i-2")]
        )
        game.pick_up(0)
        clock_before = game.state.clock

        result = game.pick_up(0)

        self.assertFalse(result.accepted)
        self.assertEqual(game.state.clock, clock_before)
        self.assertEqual(len(room_map.room(1).floor_items), 1)

    def test_an_invalid_position_is_rejected(self):
        game, _ = make_game(floor=[weapon()])

        self.assertFalse(game.pick_up(5).accepted)
        self.assertFalse(game.pick_up(-1).accepted)
        self.assertEqual(game.state.clock, 0)

    def test_picking_up_from_an_empty_floor_is_rejected(self):
        game, _ = make_game()

        self.assertFalse(game.pick_up(0).accepted)


class TestDrop(unittest.TestCase):

    def test_dropping_puts_the_item_on_the_floor(self):
        item = weapon()
        game, room_map = make_game(floor=[item])
        game.pick_up(0)

        result = game.drop()

        self.assertTrue(result.accepted)
        self.assertIn(item, room_map.room(1).floor_items)

    def test_dropping_costs_twenty_five(self):
        game, _ = make_game(floor=[weapon()])
        game.pick_up(0)
        clock_before = game.state.clock

        game.drop()

        self.assertEqual(game.state.clock, clock_before + 25)

    def test_dropping_with_nothing_selected_is_rejected(self):
        game, _ = make_game()

        result = game.drop()

        self.assertFalse(result.accepted)
        self.assertEqual(game.state.clock, 0)

    def test_the_item_lands_in_the_room_where_the_player_is(self):
        item = weapon()
        game, room_map = make_game(floor=[item])
        game.pick_up(0)
        game.move("N")

        game.drop()

        self.assertIn(item, room_map.room(2).floor_items)
        self.assertNotIn(item, room_map.room(1).floor_items)


class TestEquip(unittest.TestCase):

    def test_equipping_a_weapon_raises_the_effective_attack(self):
        game, _ = make_game(floor=[weapon(bonus=3)])
        game.pick_up(0)
        attack_before = game.player.effective_attack

        result = game.equip_item()

        self.assertTrue(result.accepted)
        self.assertEqual(game.player.effective_attack, attack_before + 3)

    def test_equipping_armour_raises_the_effective_defense(self):
        game, _ = make_game(floor=[armor(bonus=4)])
        game.pick_up(0)
        defense_before = game.player.effective_defense

        game.equip_item()

        self.assertEqual(game.player.effective_defense, defense_before + 4)

    def test_equipping_costs_fifty(self):
        game, _ = make_game(floor=[weapon()])
        game.pick_up(0)
        clock_before = game.state.clock

        game.equip_item()

        self.assertEqual(game.state.clock, clock_before + 50)

    def test_a_second_weapon_replaces_the_first(self):
        game, _ = make_game(
            floor=[weapon(bonus=3, instance_id="i-1"), weapon(bonus=7, instance_id="i-2", name="Espada")]
        )
        game.pick_up(0)
        game.equip_item()
        game.pick_up(0)
        game.inventory_next()
        game.equip_item()

        self.assertEqual(game.player.effective_attack, game.player.attack + 7)

    def test_a_potion_cannot_be_equipped(self):
        game, _ = make_game(floor=[healing_potion()])
        game.pick_up(0)
        clock_before = game.state.clock

        result = game.equip_item()

        self.assertFalse(result.accepted)
        self.assertEqual(game.state.clock, clock_before)


class TestUseItem(unittest.TestCase):

    def test_a_healing_potion_restores_health(self):
        game, _ = make_game(floor=[healing_potion(heal=8)], max_health=100)
        game.player.take_damage(20)
        game.pick_up(0)
        health_before = game.player.health

        result = game.use_item()

        self.assertTrue(result.accepted)
        self.assertEqual(game.player.health, health_before + 8)

    def test_healing_never_passes_the_maximum(self):
        game, _ = make_game(floor=[healing_potion(heal=50)], max_health=100)
        game.pick_up(0)

        game.use_item()

        self.assertEqual(game.player.health, 100)

    def test_using_costs_fifty(self):
        game, _ = make_game(floor=[healing_potion()])
        game.pick_up(0)
        clock_before = game.state.clock

        game.use_item()

        self.assertEqual(game.state.clock, clock_before + 50)

    def test_the_item_is_consumed_and_does_not_reach_the_floor(self):
        potion = healing_potion()
        game, room_map = make_game(floor=[potion])
        game.pick_up(0)

        game.use_item()

        self.assertTrue(game.player.inventory.is_empty())
        self.assertNotIn(potion, room_map.room(1).floor_items)

    def test_a_torch_turns_on_and_shows_as_an_effect(self):
        game, _ = make_game(floor=[torch(duration=500)])
        game.pick_up(0)

        game.use_item()

        self.assertTrue(game.torch_lit)
        self.assertIn("antorcha", [e.name for e in game.visible_state().effects])

    def test_a_speed_potion_changes_the_speed(self):
        game, _ = make_game(floor=[speed_potion(modifier=50, duration=300)])
        game.pick_up(0)
        speed_before = game.player.speed

        game.use_item()

        self.assertEqual(game.player.speed, speed_before + 50)

    def test_the_speed_returns_when_the_potion_ends(self):
        game, _ = make_game(floor=[speed_potion(modifier=50, duration=200)])
        game.pick_up(0)
        game.use_item()

        for _ in range(8):
            game.wait()

        self.assertEqual(game.player.speed, 100)

    def test_an_antidote_cancels_the_poison(self):
        game, _ = make_game(floor=[antidote()], max_health=100)
        game.pick_up(0)
        game.apply_poison(game.player, 3)

        game.use_item()
        health_after_using = game.player.health

        for _ in range(6):
            game.wait()

        self.assertEqual(game.player.health, health_after_using)

    def test_a_weapon_cannot_be_used(self):
        game, _ = make_game(floor=[weapon()])
        game.pick_up(0)
        clock_before = game.state.clock

        result = game.use_item()

        self.assertFalse(result.accepted)
        self.assertEqual(game.state.clock, clock_before)

    def test_a_rewind_scroll_points_to_its_own_action(self):
        game, _ = make_game(floor=[scroll()])
        game.pick_up(0)

        result = game.use_item()

        self.assertFalse(result.accepted)
        self.assertIn("retroceder", result.message)

    def test_using_with_nothing_selected_is_rejected(self):
        game, _ = make_game()

        self.assertFalse(game.use_item().accepted)


class TestInventoryNavigation(unittest.TestCase):

    def game_with_two_items(self):
        game, _ = make_game(
            floor=[weapon(instance_id="i-1", name="Daga"), armor(instance_id="i-2", name="Coraza")]
        )
        game.pick_up(0)
        game.pick_up(0)

        return game

    def test_navigation_consumes_no_time(self):
        game = self.game_with_two_items()
        clock_before = game.state.clock

        game.inventory_next()
        game.inventory_previous()

        self.assertEqual(game.state.clock, clock_before)

    def test_navigation_is_not_a_player_action(self):
        game = self.game_with_two_items()
        actions_before = game.player_actions

        game.inventory_next()

        self.assertEqual(game.player_actions, actions_before)

    def test_navigation_moves_the_cursor(self):
        game = self.game_with_two_items()
        current = game.player.inventory.current()

        game.inventory_next()

        self.assertIsNot(game.player.inventory.current(), current)

    def test_navigating_past_the_end_is_rejected(self):
        game, _ = make_game(floor=[weapon()])
        game.pick_up(0)

        self.assertFalse(game.inventory_next().accepted)
        self.assertFalse(game.inventory_previous().accepted)

    def test_dropping_acts_on_what_the_cursor_shows(self):
        game = self.game_with_two_items()
        game.inventory_next()
        shown = game.player.inventory.current()

        game.drop()

        self.assertIn(shown, game.room_map.room(1).floor_items)


class TestInventoryAndTheEndOfTheGame(unittest.TestCase):

    def test_a_finished_game_rejects_every_inventory_action(self):
        game, _ = make_game(floor=[weapon()], max_health=1, defense=0)
        game.pick_up(0)
        game.result = "derrota"

        self.assertFalse(game.pick_up(0).accepted)
        self.assertFalse(game.drop().accepted)
        self.assertFalse(game.use_item().accepted)
        self.assertFalse(game.equip_item().accepted)
        self.assertFalse(game.inventory_next().accepted)

    def test_without_an_inventory_the_actions_say_what_is_missing(self):
        room_map = make_map()
        player = Player("p-1", "Heroe", 30, 6, 2, 100, 1)
        game = Game(GameState(seed=1), player, None, room_map=room_map)

        self.assertEqual(game.result, IN_PROGRESS)
        self.assertIn("inventario", game.drop().message)


if __name__ == "__main__":
    unittest.main()
