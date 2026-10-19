import io
import os
import tempfile
import unittest

from adapters.scoreboard import Scoreboard, ScoreboardError, ScoreEntry
from tests.test_application import OFFLINE_DATA, ScriptedInput
from view.console_view import ConsoleView


def entry(name, result="victoria", clock=500, actions=5, defeated=1, crypt="cripta-01"):
    return ScoreEntry(name, crypt, "v1", result, actions, defeated, clock)


class TestScoreboard(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, "puntajes.txt")
        self.board = Scoreboard(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def names(self, entries):
        return [item.player_name for item in entries]

    def test_without_file_there_are_no_entries(self):
        self.assertEqual(self.board.ranking(), [])

    def test_entries_survive_in_the_file_in_playing_order(self):
        self.board.add(entry("Ana"))
        self.board.add(entry("Beto"))

        self.assertEqual(self.names(Scoreboard(self.path).entries()), ["Ana", "Beto"])

    def test_victories_go_first_then_lower_clock(self):
        self.board.add(entry("Derrota rapida", result="derrota", clock=100))
        self.board.add(entry("Lenta", clock=900))
        self.board.add(entry("Rapida", clock=300))

        self.assertEqual(
            self.names(self.board.ranking()), ["Rapida", "Lenta", "Derrota rapida"]
        )

    def test_ties_break_by_actions_then_enemies(self):
        self.board.add(entry("Muchas acciones", actions=9))
        self.board.add(entry("Pocos enemigos", actions=5, defeated=0))
        self.board.add(entry("Mejor", actions=5, defeated=3))

        self.assertEqual(
            self.names(self.board.ranking()),
            ["Mejor", "Pocos enemigos", "Muchas acciones"],
        )

    def test_ranking_by_crypt_and_limit(self):
        for number in range(30):
            self.board.add(entry(f"J{number}", clock=1000 - number))
        self.board.add(entry("Otra", clock=1, crypt="cripta-02"))

        top = self.board.ranking("cripta-01", limit=3)

        self.assertEqual(self.names(top), ["J29", "J28", "J27"])

    def test_a_name_with_tabs_does_not_break_the_file(self):
        self.board.add(entry("Ana\tla\nbrava"))

        self.assertEqual(self.names(self.board.entries()), ["Ana la brava"])

    def test_a_foreign_file_is_reported(self):
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("otra cosa\n")

        with self.assertRaises(ScoreboardError):
            self.board.entries()


class TestRecordAtTheEnd(unittest.TestCase):

    def test_a_finished_game_is_recorded_and_shown(self):
        from adapters.fuente_offline import FuenteOffline
        from controller.application import InUseIds, play
        from repository.repositorio_cripta import RepositorioCripta

        with tempfile.TemporaryDirectory() as directory:
            in_use = InUseIds()
            repository = RepositorioCripta(
                FuenteOffline(OFFLINE_DATA), os.path.join(directory, "cache"),
                consultar_ids_en_uso=in_use,
            )
            in_use.repository = repository
            output = io.StringIO()
            view = ConsoleView(output, ScriptedInput(["mover N"] + ["esperar"] * 20))
            board = Scoreboard(os.path.join(directory, "puntajes.txt"))

            game = play(repository, view, 5, "cripta-01", "Steven", in_use,
                        os.path.join(directory, "partidas"), board)

            recorded = board.entries()

        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0].player_name, "Steven")
        self.assertEqual(recorded[0].result, game.result)
        self.assertEqual(recorded[0].final_clock, game.state.clock)
        self.assertIn("Puntajes de cripta-01", output.getvalue())

    def test_an_interrupted_game_is_not_recorded(self):
        from adapters.fuente_offline import FuenteOffline
        from controller.application import InUseIds, play
        from repository.repositorio_cripta import RepositorioCripta

        with tempfile.TemporaryDirectory() as directory:
            repository = RepositorioCripta(
                FuenteOffline(OFFLINE_DATA), os.path.join(directory, "cache"),
            )
            view = ConsoleView(io.StringIO(), ScriptedInput(["salir"]))
            board = Scoreboard(os.path.join(directory, "puntajes.txt"))

            play(repository, view, 5, "cripta-01", None, InUseIds(),
                 os.path.join(directory, "partidas"), board)

            self.assertEqual(board.entries(), [])


if __name__ == "__main__":
    unittest.main()
