import os
import tempfile
import unittest

from controller.commands import parse_command
from replay.replay_log import (
    ReplayHeader,
    ReplayLogError,
    ReplayLogWriter,
    read_replay_log,
)


HEADER = ReplayHeader("cripta-01", "a3f91c", "cat-2026-08-01", 12345)


class LogFileTestCase(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, "partida.log")

    def tearDown(self):
        self.directory.cleanup()

    def write_text(self, text):
        with open(self.path, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)

    def read_text(self):
        with open(self.path, encoding="utf-8") as file:
            return file.read()


class TestWriter(LogFileTestCase):

    def test_writes_the_header_and_one_line_per_command(self):
        with ReplayLogWriter(self.path, HEADER) as log:
            log.append(parse_command("mover n"))
            log.append(parse_command("atacar e-201"))

        self.assertEqual(
            self.read_text(),
            "# CRIPTA replay\n"
            "formato=1\n"
            "cripta=cripta-01\n"
            "version_cripta=a3f91c\n"
            "version_catalogo=cat-2026-08-01\n"
            "semilla=12345\n"
            "---\n"
            "mover N\n"
            "atacar e-201\n",
        )

    def test_each_line_is_on_disk_before_closing(self):
        log = ReplayLogWriter(self.path, HEADER)
        log.append(parse_command("esperar"))

        self.assertTrue(self.read_text().endswith("---\nesperar\n"))

        log.close()

    def test_never_overwrites_an_existing_log(self):
        self.write_text("otra partida\n")

        with self.assertRaises(FileExistsError):
            ReplayLogWriter(self.path, HEADER)

        self.assertEqual(self.read_text(), "otra partida\n")

    def test_rejects_header_values_with_line_breaks(self):
        header = ReplayHeader("cripta-01", "a3\nf9", "cat", 1)

        with self.assertRaises(ValueError):
            ReplayLogWriter(self.path, header)


class TestReader(LogFileTestCase):

    def test_reads_back_what_was_written(self):
        with ReplayLogWriter(self.path, HEADER) as log:
            log.append(parse_command("mover N"))
            log.append(parse_command("recoger 0"))

        replay_log = read_replay_log(self.path)

        self.assertEqual(replay_log.header, HEADER)
        self.assertEqual(
            [logged.command.to_text() for logged in replay_log.commands],
            ["mover N", "recoger 0"],
        )

    def test_reports_the_line_number_of_each_command(self):
        with ReplayLogWriter(self.path, HEADER) as log:
            log.append(parse_command("esperar"))

        self.assertEqual(read_replay_log(self.path).commands[0].line_number, 8)

    def test_ignores_blank_lines_and_comments_in_the_body(self):
        with ReplayLogWriter(self.path, HEADER) as log:
            log.append(parse_command("esperar"))

        with open(self.path, "a", encoding="utf-8") as file:
            file.write("\n# aqui aparece el error\nmover S\n")

        commands = read_replay_log(self.path).commands

        self.assertEqual([c.command.to_text() for c in commands], ["esperar", "mover S"])

    def test_empty_body_is_a_game_without_actions(self):
        ReplayLogWriter(self.path, HEADER).close()

        self.assertEqual(read_replay_log(self.path).commands, [])

    def test_a_loaded_session_keeps_its_saved_game_and_digest(self):
        header = ReplayHeader(
            "cripta-01", "a3f91c", "cat-2026-08-01", 12345,
            "partida.cripta", "ab12",
        )
        ReplayLogWriter(self.path, header).close()

        self.assertIn("partida_cargada=partida.cripta\n", self.read_text())
        self.assertEqual(read_replay_log(self.path).header, header)

    def test_a_new_game_writes_no_saved_game_lines(self):
        ReplayLogWriter(self.path, HEADER).close()

        self.assertNotIn("partida_cargada", self.read_text())
        self.assertEqual(read_replay_log(self.path).header.saved_game, "")


class TestInvalidLogs(LogFileTestCase):

    VALID_HEADER = (
        "# CRIPTA replay\n"
        "formato=1\n"
        "cripta=cripta-01\n"
        "version_cripta=a3f91c\n"
        "version_catalogo=cat-2026-08-01\n"
        "semilla=12345\n"
    )

    def assert_invalid(self, text, fragment):
        self.write_text(text)

        with self.assertRaises(ReplayLogError) as context:
            read_replay_log(self.path)

        self.assertIn(fragment, str(context.exception))

    def test_not_a_replay_log(self):
        self.assert_invalid("hola\n", "no es un log")

    def test_header_without_separator(self):
        self.assert_invalid(self.VALID_HEADER, "---")

    def test_other_format_version_is_incompatible(self):
        text = self.VALID_HEADER.replace("formato=1", "formato=2") + "---\n"

        self.assert_invalid(text, "formato 2")

    def test_missing_seed(self):
        text = self.VALID_HEADER.replace("semilla=12345\n", "") + "---\n"

        self.assert_invalid(text, "semilla")

    def test_seed_must_be_an_integer(self):
        text = self.VALID_HEADER.replace("12345", "doce") + "---\n"

        self.assert_invalid(text, "entero")

    def test_unknown_header_key(self):
        self.assert_invalid(self.VALID_HEADER + "color=rojo\n---\n", "color")

    def test_saved_game_without_digest(self):
        text = self.VALID_HEADER + "partida_cargada=p.cripta\n---\n"

        self.assert_invalid(text, "huella_partida")

    def test_invalid_command_reports_its_line(self):
        self.assert_invalid(self.VALID_HEADER + "---\nvolar N\n", "Linea 8")

    def test_application_commands_are_not_allowed_in_the_body(self):
        self.assert_invalid(self.VALID_HEADER + "---\nguardar a.bin\n", "Linea 8")


if __name__ == "__main__":
    unittest.main()
