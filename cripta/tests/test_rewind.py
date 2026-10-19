import unittest

from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.item import Item
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from model.trap import Trap
from structures.history import History, ReversibleEventQueue
from structures.inventory import Inventory
from structures.trail import PlayerTrail
from tests.verificar_retroceso import assert_rewind_restores


def make_item(item_class, name, type_id, instance_id, **extra):
    return Item(
        instance_id=instance_id,
        type_id=type_id,
        name=name,
        item_class=item_class,
        weight=1,
        value=1,
        **extra,
    )


def scroll(instance_id="i-pergamino"):
    return make_item(Item.REWIND_SCROLL, "Pergamino", "itm_pergamino", instance_id)


def build_game(
    enemies=(),
    traps=(),
    floor=(),
    items=(),
    scrolls=1,
    closed_door=False,
    auto_close=None,
    exit_room_id=None,
):
    """Una cripta de tres salas con historial, rastro y agenda reversible."""
    rooms = [Room(number, f"Sala {number}") for number in (1, 2, 3)]

    for room in rooms:
        room.content_loaded = True

    first = Door(1, 2, closed=closed_door, key_id=None, auto_close=auto_close)
    rooms[0].add_exit(Exit("N", 2, first))
    rooms[1].add_exit(Exit("S", 1, first))

    second = Door(2, 3)
    rooms[1].add_exit(Exit("N", 3, second))
    rooms[2].add_exit(Exit("S", 2, second))

    rooms[0].floor_items.extend(floor)
    rooms[0].traps.extend(traps)

    room_map = RoomMap()

    for room in rooms:
        room_map.add(room)

    state = GameState(seed=2026)
    history = History(state)
    player = Player("p-1", "Heroe", 200, 6, 2, 100, 1)
    player.inventory = Inventory(10, history)

    for number in range(scrolls):
        player.inventory.pick_up(scroll(f"i-pergamino-{number}"))

    for item in items:
        player.inventory.pick_up(item)

    game = Game(
        state,
        player,
        list(enemies),
        room_map=room_map,
        exit_room_id=exit_room_id,
        trail=PlayerTrail(history),
        history=history,
        event_queue=ReversibleEventQueue(history),
    )

    return game, history


def make_enemy(actor_id="e-1", room_id=1, speed=150, health=20, behavior=None):
    return Enemy(
        actor_id=actor_id,
        name="Rata gigante",
        max_health=20,
        attack=4,
        defense=1,
        speed=speed,
        room_id=room_id,
        behavior=Enemy.GUARDIAN if behavior is None else behavior,
        health=health,
    )


def make_trap(instance_id="t-1", damage=3, rearm_interval=200):
    return Trap(
        instance_id=instance_id,
        type_id="trp_dardos",
        name="Dardos",
        damage=damage,
        rearm_interval=rearm_interval,
        room_id=1,
    )


class TestRewindRestoresEveryAction(unittest.TestCase):

    def test_waiting(self):
        game, _ = build_game(enemies=[make_enemy()])

        assert_rewind_restores(self, game, game.wait, trail=game.trail)

    def test_attacking(self):
        game, _ = build_game(enemies=[make_enemy()])

        assert_rewind_restores(
            self, game, lambda: game.attack("e-1"), trail=game.trail
        )

    def test_killing_an_enemy_that_drops_items(self):
        loot = make_item(Item.POTION, "Pocion", "itm_pocion", "i-loot", heal=5)
        enemy = make_enemy(health=1)
        enemy.drops.append(loot)
        game, _ = build_game(enemies=[enemy])

        assert_rewind_restores(
            self, game, lambda: game.attack("e-1"), trail=game.trail
        )

    def test_moving(self):
        game, _ = build_game(enemies=[make_enemy(room_id=2)])

        assert_rewind_restores(
            self, game, lambda: game.move("N"), trail=game.trail
        )

    def test_moving_into_a_trap(self):
        game, _ = build_game()
        game.room_map.room(2).traps.append(make_trap())

        assert_rewind_restores(
            self, game, lambda: game.move("N"), trail=game.trail
        )

    def test_opening_a_door(self):
        game, _ = build_game(closed_door=True, auto_close=300)

        assert_rewind_restores(
            self, game, lambda: game.open_door("N"), trail=game.trail
        )

    def test_picking_up(self):
        sword = make_item(Item.WEAPON, "Daga", "itm_daga", "i-daga", attack_bonus=3)
        game, _ = build_game(floor=[sword])

        assert_rewind_restores(
            self, game, lambda: game.pick_up(0), trail=game.trail
        )

    def test_dropping(self):
        sword = make_item(Item.WEAPON, "Daga", "itm_daga", "i-daga", attack_bonus=3)
        game, _ = build_game(items=[sword])

        assert_rewind_restores(self, game, game.drop, trail=game.trail)

    def test_equipping(self):
        sword = make_item(Item.WEAPON, "Daga", "itm_daga", "i-daga", attack_bonus=3)
        game, _ = build_game(items=[sword])

        assert_rewind_restores(self, game, game.equip_item, trail=game.trail)

    def test_drinking_a_healing_potion(self):
        potion = make_item(Item.POTION, "Pocion", "itm_pocion", "i-pocion", heal=10)
        game, _ = build_game(items=[potion], enemies=[make_enemy()])
        game.wait()

        assert_rewind_restores(self, game, game.use_item, trail=game.trail)

    def test_drinking_a_speed_potion(self):
        potion = make_item(
            Item.POTION,
            "Pocion veloz",
            "itm_veloz",
            "i-veloz",
            speed_modifier=50,
            duration=300,
        )
        game, _ = build_game(items=[potion])

        assert_rewind_restores(self, game, game.use_item, trail=game.trail)

    def test_lighting_a_torch(self):
        item = make_item(Item.TORCH, "Antorcha", "itm_antorcha", "i-antorcha", duration=400)
        game, _ = build_game(items=[item])

        assert_rewind_restores(self, game, game.use_item, trail=game.trail)

    def test_an_antidote(self):
        item = make_item(Item.ANTIDOTE, "Antidoto", "itm_antidoto", "i-antidoto")
        game, _ = build_game(items=[item])
        game.apply_poison(game.player, 2)

        assert_rewind_restores(self, game, game.use_item, trail=game.trail)

    def test_a_wandering_enemy_moving(self):
        game, _ = build_game(enemies=[make_enemy(room_id=2, behavior=Enemy.WANDERER)])
        game._activate_enemies_in(2)

        assert_rewind_restores(self, game, game.wait, trail=game.trail)

    def test_a_tracker_following_the_trail(self):
        game, _ = build_game(
            enemies=[make_enemy(room_id=3, behavior=Enemy.TRACKER)]
        )
        game._activate_enemies_in(3)
        game.move("N")

        assert_rewind_restores(self, game, game.wait, trail=game.trail)

    def test_winning_the_game(self):
        game, _ = build_game(exit_room_id=2)

        assert_rewind_restores(
            self, game, lambda: game.move("N"), trail=game.trail
        )


class TestTheScrollItself(unittest.TestCase):

    def test_the_scroll_is_consumed(self):
        game, _ = build_game(enemies=[make_enemy()], scrolls=2)
        before = game.player.inventory.scroll_count()

        game.wait()
        game.rewind()

        self.assertEqual(game.player.inventory.scroll_count(), before - 1)

    def test_the_rewind_does_not_give_the_scroll_back(self):
        game, _ = build_game(enemies=[make_enemy()], scrolls=1)

        game.wait()
        game.rewind()

        self.assertEqual(game.player.inventory.scroll_count(), 0)
        self.assertFalse(game.rewind().accepted)

    def test_a_scroll_picked_up_in_the_interval_is_not_given_back(self):
        """Apendice B: la cantidad refleja solo la unidad consumida."""
        game, _ = build_game(floor=[scroll("i-pergamino-suelo")], scrolls=1)

        game.pick_up(0)

        self.assertEqual(game.player.inventory.scroll_count(), 2)

        game.rewind()

        self.assertEqual(game.player.inventory.scroll_count(), 1)
        self.assertEqual(list(game.room_map.room(1).floor_items), [])

    def test_a_scroll_dropped_in_the_interval_stays_on_the_floor(self):
        """La excepcion de la seccion 2.11 aplica en los dos sentidos."""
        game, _ = build_game(scrolls=2)

        game.drop()
        floor = game.room_map.room(1).floor_items

        self.assertEqual(len(floor), 1)

        game.rewind()

        self.assertEqual(game.player.inventory.scroll_count(), 0)
        self.assertEqual(len(floor), 1)

    def test_without_a_scroll_it_is_rejected(self):
        game, _ = build_game(enemies=[make_enemy()], scrolls=0)
        game.wait()

        result = game.rewind()

        self.assertFalse(result.accepted)
        self.assertIn("pergamino", result.message)

    def test_with_nothing_to_undo_it_is_rejected(self):
        game, _ = build_game(scrolls=1)

        self.assertFalse(game.rewind().accepted)

    def test_rewinding_consumes_no_time(self):
        game, _ = build_game(enemies=[make_enemy()], scrolls=1)
        game.wait()
        clock_after_waiting = game.state.clock

        game.rewind()

        self.assertLess(game.state.clock, clock_after_waiting)

    def test_rewinding_is_not_a_player_action(self):
        game, _ = build_game(enemies=[make_enemy()], scrolls=1)
        game.wait()
        actions = game.player_actions

        game.rewind()

        self.assertEqual(game.player_actions, actions - 1)

    def test_two_rewinds_in_a_row(self):
        game, _ = build_game(enemies=[make_enemy()], scrolls=2)
        start = game.state.clock

        game.wait()
        game.wait()
        first_clock = game.state.clock

        self.assertTrue(game.rewind().accepted)
        middle_clock = game.state.clock

        self.assertTrue(game.rewind().accepted)

        self.assertLess(middle_clock, first_clock)
        self.assertEqual(game.state.clock, start)

    def test_more_than_five_actions_back_is_not_possible(self):
        game, history = build_game(enemies=[make_enemy()], scrolls=10)

        for _ in range(8):
            game.wait()

        undone = 0

        while game.rewind().accepted:
            undone += 1

        self.assertEqual(undone, history.max_actions)

    def test_a_defeated_player_can_come_back(self):
        """§2.11 no condiciona el pergamino al estado de la partida, y el
        resultado se anota en el historial como cualquier otro cambio."""
        enemy = make_enemy(speed=400)
        enemy.attack = 500
        game, _ = build_game(enemies=[enemy], scrolls=1)

        game.wait()

        self.assertEqual(game.result, "derrota")
        self.assertTrue(game.rewind().accepted)
        self.assertEqual(game.result, "en_curso")
        self.assertTrue(game.player.is_alive)


class TestTheInventoryNeverGoesOverTheMaximum(unittest.TestCase):
    """El caso que §4.6 de DECISIONES.md dejaba abierto: soltar, recoger un
    pergamino y retroceder hasta antes de soltar. Cada retroceso devuelve a lo
    sumo un objeto y consume un pergamino, asi que el total no pasa del tope."""

    def test_dropping_then_picking_up_a_scroll_and_rewinding_twice(self):
        daggers = [
            make_item("arma", "Daga", "itm_daga", f"i-daga-{number}")
            for number in range(8)
        ]
        game, _ = build_game(
            floor=[scroll("i-pergamino-suelo")], scrolls=2, items=daggers
        )
        inventory = game.player.inventory

        self.assertTrue(inventory.is_full())

        game.drop()
        game.pick_up(0)
        sizes = [len(inventory)]

        for _ in range(2):
            self.assertTrue(game.rewind().accepted)
            sizes.append(len(inventory))

        self.assertEqual(sizes, [10, 9, 9])
        self.assertEqual(inventory.scroll_count(), 1)
        self.assertEqual(
            [item.instance_id for item in inventory if item.type_id == "itm_daga"],
            [item.instance_id for item in daggers],
        )


if __name__ == "__main__":
    unittest.main()
