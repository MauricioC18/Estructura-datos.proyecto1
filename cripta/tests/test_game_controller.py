import unittest

from controller.commands import parse_command
from controller.game_controller import GameController
from model.game import IN_PROGRESS, ActionResult, Game
from model.game_state import GameState
from tests.test_game import make_enemy, make_player


class FakeGame:
    """Imita el contrato de Game: cada accion devuelve un ActionResult.

    Registra que metodo se llamo y con que argumento, y acepta o rechaza
    segun se le indique.
    """

    def __init__(self, accept=True):
        self.accept = accept
        self.calls = []
        self.result = IN_PROGRESS

    def _act(self, name, argument=None):
        self.calls.append((name, argument))
        return ActionResult(self.accept, name)

    def move(self, direction):
        return self._act("move", direction)

    def open_door(self, direction):
        return self._act("open_door", direction)

    def attack(self, enemy_id):
        return self._act("attack", enemy_id)

    def wait(self):
        return self._act("wait")

    def pick_up(self, floor_index):
        return self._act("pick_up", floor_index)

    def drop(self):
        return self._act("drop")

    def use_item(self):
        return self._act("use_item")

    def equip_item(self):
        return self._act("equip_item")

    def inventory_next(self):
        return self._act("inventory_next")

    def inventory_previous(self):
        return self._act("inventory_previous")

    def rewind(self):
        return self._act("rewind")


class RecordingLog:

    def __init__(self):
        self.commands = []

    def append(self, command):
        self.commands.append(command)


class TestDispatch(unittest.TestCase):

    def test_each_command_calls_its_game_method(self):
        expected = [
            ("mover N", ("move", "N")),
            ("abrir E", ("open_door", "E")),
            ("atacar e-201", ("attack", "e-201")),
            ("esperar", ("wait", None)),
            ("recoger 2", ("pick_up", 2)),
            ("soltar", ("drop", None)),
            ("usar", ("use_item", None)),
            ("equipar", ("equip_item", None)),
            ("sig", ("inventory_next", None)),
            ("ant", ("inventory_previous", None)),
            ("retroceder", ("rewind", None)),
        ]

        for text, call in expected:
            game = FakeGame()
            GameController(game).execute(parse_command(text))

            self.assertEqual(game.calls, [call], text)

    def test_returns_the_result_of_the_model(self):
        result = GameController(FakeGame(accept=False)).execute(parse_command("esperar"))

        self.assertFalse(result.accepted)

    def test_application_commands_are_refused(self):
        controller = GameController(FakeGame())

        for text in ("ver", "guardar a.bin", "salir", "ayuda"):
            with self.assertRaises(ValueError):
                controller.execute(parse_command(text))


class TestReplayLogging(unittest.TestCase):

    def test_accepted_actions_are_logged(self):
        log = RecordingLog()
        controller = GameController(FakeGame(accept=True), log)

        controller.execute(parse_command("mover N"))
        controller.execute(parse_command("retroceder"))

        self.assertEqual(
            [command.to_text() for command in log.commands],
            ["mover N", "retroceder"],
        )

    def test_rejected_actions_are_not_logged(self):
        log = RecordingLog()
        controller = GameController(FakeGame(accept=False), log)

        controller.execute(parse_command("abrir E"))

        self.assertEqual(log.commands, [])

    def test_without_log_nothing_fails(self):
        result = GameController(FakeGame()).execute(parse_command("esperar"))

        self.assertTrue(result.accepted)


class TestWithRealGame(unittest.TestCase):
    """Usa las acciones que el motor ya implementa: esperar y atacar."""

    def make_controller(self, log=None):
        game = Game(GameState(seed=7), make_player(), [make_enemy()])
        return GameController(game, log)

    def test_waiting_advances_the_clock(self):
        controller = self.make_controller()

        controller.execute(parse_command("esperar"))

        self.assertEqual(controller.visible_state().clock, 100)

    def test_attacking_a_missing_enemy_is_rejected_and_not_logged(self):
        log = RecordingLog()
        controller = self.make_controller(log)

        result = controller.execute(parse_command("atacar e-999"))

        self.assertFalse(result.accepted)
        self.assertEqual(controller.visible_state().clock, 0)
        self.assertEqual(log.commands, [])


if __name__ == "__main__":
    unittest.main()
