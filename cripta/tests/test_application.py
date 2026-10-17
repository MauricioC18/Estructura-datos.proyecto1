"""Flujo de la aplicacion con los datos offline: jugar, registrar y reproducir."""
import io
import os
import tempfile
import unittest

from adapters.fuente_offline import FuenteOffline
from controller.application import InUseIds, play, replay
from main import parse_arguments
from model.game import DEFEAT
from repository.repositorio_cripta import RepositorioCripta
from view.console_view import ConsoleView


OFFLINE_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_offline")


class ScriptedInput:
    """Entrega lineas fijas como si las escribiera el jugador."""

    def __init__(self, lines):
        self.lines = list(lines)

    def __call__(self, prompt):
        if not self.lines:
            raise EOFError
        return self.lines.pop(0)


class TestApplication(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.logs = os.path.join(self.directory.name, "partidas")

    def tearDown(self):
        self.directory.cleanup()

    def repository(self, cache_name):
        in_use = InUseIds()
        repository = RepositorioCripta(
            FuenteOffline(OFFLINE_DATA),
            os.path.join(self.directory.name, cache_name),
            consultar_ids_en_uso=in_use,
        )
        in_use.repository = repository
        return repository, in_use

    def play_lines(self, lines, crypt_id=None):
        repository, in_use = self.repository("cache_juego")
        output = io.StringIO()
        view = ConsoleView(output=output, read_line=ScriptedInput(lines))
        game = play(repository, view, 5, crypt_id, None, in_use, self.logs)
        return game, output.getvalue()

    def only_log(self):
        names = os.listdir(self.logs)
        self.assertEqual(len(names), 1)
        return os.path.join(self.logs, names[0])

    def test_a_game_is_played_logged_and_replayed_the_same(self):
        original, _ = self.play_lines(["mover N", "ver", "zzz", "esperar", "esperar"], "cripta-01")

        repository, in_use = self.repository("cache_replay")
        lines = []
        reproduced = replay(repository, self.only_log(), lines.append, in_use)

        self.assertIsNotNone(reproduced)
        self.assertEqual(reproduced.state.clock, original.state.clock)
        self.assertEqual(reproduced.player.health, original.player.health)
        self.assertEqual(reproduced.result, original.result)
        self.assertEqual(list(reproduced.messages), list(original.messages))

    def test_only_accepted_actions_reach_the_log(self):
        self.play_lines(["mover E", "ver", "ayuda", "mover N", "salir"], "cripta-01")

        with open(self.only_log(), encoding="utf-8") as log:
            body = log.read().split("---\n")[1]

        self.assertEqual(body.split(), ["mover", "N"])

    def test_the_crypt_can_be_chosen_by_number(self):
        game, output = self.play_lines(["1", "salir"])

        self.assertIsNotNone(game)
        self.assertIn("Criptas publicadas", output)

    def test_an_empty_choice_cancels_without_a_game(self):
        game, _ = self.play_lines([""])

        self.assertIsNone(game)

    def test_the_view_shows_exits_and_floor(self):
        _, output = self.play_lines(["salir"], "cripta-01")

        self.assertIn("Salidas:", output)

    def test_dying_ends_the_loop(self):
        game, output = self.play_lines(["mover N"] + ["esperar"] * 20, "cripta-01")

        self.assertEqual(game.result, DEFEAT)
        self.assertIn("Derrota", output)

    def test_a_log_with_another_version_is_not_replayed(self):
        self.play_lines(["mover N", "salir"], "cripta-01")
        path = self.only_log()

        with open(path, encoding="utf-8") as log:
            text = log.read()

        old = os.path.join(self.directory.name, "viejo.log")
        with open(old, "w", encoding="utf-8") as log:
            lines = [
                "version_cripta=otra" if line.startswith("version_cripta=") else line
                for line in text.splitlines()
            ]
            log.write("\n".join(lines) + "\n")

        repository, in_use = self.repository("cache_replay")
        output = []

        self.assertIsNone(replay(repository, old, output.append, in_use))
        self.assertIn("reproducción fiel", output[-1])


class TestArguments(unittest.TestCase):

    def test_offline_without_folder_uses_the_default_package(self):
        self.assertEqual(parse_arguments(["--offline"]).offline, "datos_offline")

    def test_defaults(self):
        arguments = parse_arguments([])

        self.assertIsNone(arguments.offline)
        self.assertEqual(arguments.cache_size, 25)
        self.assertFalse(arguments.bench)


if __name__ == "__main__":
    unittest.main()
