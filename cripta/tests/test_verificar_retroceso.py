import unittest

from model.enemy import Enemy
from model.game import ActionResult, Game
from model.game_state import GameState
from model.room import Door, Exit, Room, RoomMap
from model.trap import Trap
from structures.history import History, ReversibleEventQueue, use_rewind_scroll
from structures.inventory import Inventory
from structures.trail import PlayerTrail
from tests.objetos_persona3 import make_item, make_player, make_scroll
from tests.verificar_retroceso import assert_rewind_restores, differences, snapshot


def build_game():
    state = GameState(seed=5)
    history = History(state)
    rooms = RoomMap()
    first = Room(1, "Entrada")
    second = Room(2, "Pasillo")
    door = Door(1, 2)
    first.add_exit(Exit("E", 2, door))
    second.add_exit(Exit("O", 1, door))
    second.traps.append(Trap("t-1", "trp_dardos", "Dardos", 3, 300, 2))
    first.content_loaded = True
    second.content_loaded = True
    rooms.add(first)
    rooms.add(second)

    player = make_player(room_id=1)
    player.inventory = Inventory(5, history)
    player.inventory.pick_up(make_scroll())
    player.inventory.pick_up(make_item("cuerda"))
    rat = Enemy("e-1", "Rata", 20, 4, 1, 150, 2, Enemy.GUARDIAN)

    game = Game(
        state,
        player,
        [rat],
        room_map=rooms,
        history=history,
        event_queue=ReversibleEventQueue(history),
    )
    return game, history


class RewindableGame(Game):
    """Game con rewind() conectado, solo para probar el verificador.

    Game ya recibe el historial por su parametro history, asi que esta
    subclase solo agrega rewind().
    """

    def rewind(self):
        if use_rewind_scroll(self.player.inventory, self.history):
            return ActionResult(True, "El tiempo retrocede.")
        return ActionResult(False, "No se puede retroceder.")


class TestSnapshot(unittest.TestCase):
    def test_equal_snapshots_have_no_differences(self):
        game, _ = build_game()
        self.assertEqual(differences(snapshot(game), snapshot(game)), [])

    def test_unrecorded_change_is_reported_by_name(self):
        game, _ = build_game()
        before = snapshot(game)
        game.room_map.room(2).traps[0].armed = False
        self.assertEqual(
            differences(before, snapshot(game)),
            ["sala 2.trampa t-1.armada: antes True, despues del retroceso False"],
        )

    def test_scrolls_are_ignored(self):
        game, _ = build_game()
        before = snapshot(game)
        game.player.inventory.consume_scroll()
        game.room_map.room(1).floor_items.append(make_scroll("otro"))
        self.assertEqual(differences(before, snapshot(game)), [])

    def test_trail_is_compared_when_given(self):
        game, _ = build_game()
        trail = PlayerTrail()
        trail.mark(1, 0)
        before = snapshot(game, trail)
        trail.mark(2, 50)
        self.assertEqual(
            differences(before, snapshot(game, trail)),
            ["sala 2.rastro: antes None, despues del retroceso 50"],
        )


class TestAssertRewindRestores(unittest.TestCase):
    def setUp(self):
        state = GameState(seed=5)
        self.history = History(state)
        self.player = make_player()
        self.player.inventory = Inventory(5, self.history)
        self.player.inventory.pick_up(make_scroll())
        self.game = RewindableGame(
            state,
            self.player,
            history=self.history,
            event_queue=ReversibleEventQueue(self.history),
        )

    def well_recorded_wait(self):
        self.history.begin_action()
        self.history.assign(self.game, "player_actions", self.game.player_actions)
        return self.game.wait()

    def test_passes_when_everything_is_recorded(self):
        assert_rewind_restores(self, self.game, self.well_recorded_wait)

    def test_fails_naming_the_missing_field(self):
        def forgetful_wait():
            self.history.begin_action()
            self.player.health -= 5
            return self.game.wait()

        with self.assertRaises(AssertionError) as caught:
            assert_rewind_restores(self, self.game, forgetful_wait)

        self.assertIn("jugador.vida: antes 30", str(caught.exception))

    def test_requires_a_scroll(self):
        self.player.inventory.consume_scroll()
        with self.assertRaises(AssertionError):
            assert_rewind_restores(self, self.game, self.well_recorded_wait)


if __name__ == "__main__":
    unittest.main()
