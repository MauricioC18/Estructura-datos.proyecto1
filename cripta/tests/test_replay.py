import os
import tempfile
import unittest

from controller.commands import parse_command
from controller.game_controller import GameController
from model.game import DEFEAT, Game
from model.game_state import GameState
from replay.replay import ReplayDivergence, replay_commands
from replay.replay_log import (
    LoggedCommand,
    ReplayHeader,
    ReplayLogWriter,
    read_replay_log,
)
from tests.test_game import make_enemy, make_player
from tests.test_game_controller import FakeGame


def make_game(seed):
    enemies = [
        make_enemy("e-201", speed=150, room_id=1, max_health=30),
        make_enemy("e-202", speed=90, room_id=1, max_health=30),
    ]

    return Game(GameState(seed=seed), make_player(), enemies)


def snapshot(game):
    state = game.visible_state()
    enemies = [(enemy.actor_id, enemy.health) for enemy in state.enemies]

    return (state.clock, state.health, state.result, enemies, list(state.messages))


def logged(texts):
    return [LoggedCommand(index + 8, parse_command(text)) for index, text in enumerate(texts)]


class TestReplayReproducesTheGame(unittest.TestCase):
    """Misma semilla y mismas acciones deben dar la misma partida (seccion 2.6)."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, "partida.log")

    def tearDown(self):
        self.directory.cleanup()

    def test_replaying_the_log_gives_the_same_final_state(self):
        seed = 2026
        original = make_game(seed)
        header = ReplayHeader("cripta-prueba", "v1", "cat-v1", seed)

        with ReplayLogWriter(self.path, header) as log:
            controller = GameController(original, log)

            for text in ("atacar e-201", "esperar", "atacar e-999",
                         "atacar e-202", "atacar e-201", "esperar"):
                controller.execute(parse_command(text))

        replay_log = read_replay_log(self.path)
        reproduced = make_game(replay_log.header.seed)
        replay_commands(GameController(reproduced), replay_log.commands)

        self.assertEqual(snapshot(reproduced), snapshot(original))

    def test_the_rejected_action_was_not_logged(self):
        original = make_game(1)
        header = ReplayHeader("cripta-prueba", "v1", "cat-v1", 1)

        with ReplayLogWriter(self.path, header) as log:
            controller = GameController(original, log)
            controller.execute(parse_command("atacar e-999"))
            controller.execute(parse_command("esperar"))

        texts = [c.command.to_text() for c in read_replay_log(self.path).commands]

        self.assertEqual(texts, ["esperar"])

    def test_replay_does_not_write_a_new_log(self):
        reproduced = make_game(5)
        controller = GameController(reproduced)

        replay_commands(controller, logged(["esperar"]))

        self.assertIsNone(controller.replay_log)


class TestDivergence(unittest.TestCase):

    def test_a_rejected_action_stops_the_replay(self):
        controller = GameController(FakeGame(accept=False))

        with self.assertRaises(ReplayDivergence) as context:
            replay_commands(controller, logged(["esperar"]))

        self.assertIn("Linea 8", str(context.exception))

    def test_actions_after_the_end_of_the_game_are_a_divergence(self):
        game = FakeGame()
        game.result = DEFEAT

        with self.assertRaises(ReplayDivergence):
            replay_commands(GameController(game), logged(["esperar"]))

        self.assertEqual(game.calls, [])

    def test_on_result_receives_each_step(self):
        steps = []

        replay_commands(
            GameController(FakeGame()),
            logged(["esperar", "mover N"]),
            on_result=lambda entry, result: steps.append(entry.command.to_text()),
        )

        self.assertEqual(steps, ["esperar", "mover N"])


if __name__ == "__main__":
    unittest.main()
