import unittest

from controller.commands import (
    Command,
    CommandError,
    is_game_action,
    parse_command,
)


class TestParseCommand(unittest.TestCase):

    def test_move_normalizes_the_direction(self):
        self.assertEqual(parse_command("mover n"), Command("mover", "N"))

    def test_the_command_word_ignores_case_and_spaces(self):
        self.assertEqual(parse_command("  ESPERAR  "), Command("esperar"))

    def test_open_accepts_the_four_directions(self):
        for direction in ("N", "S", "E", "O"):
            self.assertEqual(parse_command(f"abrir {direction}").argument, direction)

    def test_attack_keeps_the_instance_id_as_written(self):
        self.assertEqual(parse_command("atacar e-201"), Command("atacar", "e-201"))

    def test_pick_up_converts_the_position_to_an_integer(self):
        self.assertEqual(parse_command("recoger 3"), Command("recoger", 3))

    def test_view_without_criterion_is_the_real_order(self):
        self.assertEqual(parse_command("ver"), Command("ver"))

    def test_view_with_criterion(self):
        self.assertEqual(parse_command("ver PESO"), Command("ver", "peso"))

    def test_save_keeps_the_file_name(self):
        self.assertEqual(
            parse_command("guardar partida.bin"),
            Command("guardar", "partida.bin"),
        )

    def test_commands_without_arguments(self):
        for name in ("esperar", "soltar", "usar", "equipar", "sig", "ant",
                     "retroceder", "ayuda", "salir"):
            self.assertEqual(parse_command(name), Command(name))


class TestInvalidCommands(unittest.TestCase):

    def assert_rejected(self, text):
        with self.assertRaises(CommandError):
            parse_command(text)

    def test_empty_line(self):
        self.assert_rejected("   ")

    def test_unknown_command(self):
        self.assert_rejected("volar N")

    def test_move_without_direction(self):
        self.assert_rejected("mover")

    def test_invalid_direction(self):
        self.assert_rejected("mover X")

    def test_negative_or_non_numeric_position(self):
        self.assert_rejected("recoger -1")
        self.assert_rejected("recoger daga")

    def test_unknown_sort_criterion(self):
        self.assert_rejected("ver color")

    def test_extra_arguments(self):
        self.assert_rejected("esperar 2")
        self.assert_rejected("atacar e-201 e-202")


class TestCanonicalText(unittest.TestCase):

    def test_parsing_the_canonical_text_gives_the_same_command(self):
        for text in ("mover n", "abrir o", "atacar e-201", "recoger 0",
                     "esperar", "retroceder", "sig"):
            command = parse_command(text)

            self.assertEqual(parse_command(command.to_text()), command)

    def test_canonical_text_is_normalized(self):
        self.assertEqual(parse_command("MOVER  s").to_text(), "mover S")


class TestGameActions(unittest.TestCase):

    def test_model_actions(self):
        for text in ("mover N", "abrir E", "atacar e-1", "esperar", "recoger 0",
                     "soltar", "usar", "equipar", "sig", "ant", "retroceder"):
            self.assertTrue(is_game_action(parse_command(text)), text)

    def test_application_commands_are_not_model_actions(self):
        for text in ("ver", "ver peso", "guardar a.bin", "cargar a.bin",
                     "ayuda", "salir"):
            self.assertFalse(is_game_action(parse_command(text)), text)


class TestComandosDeLaNiebla(unittest.TestCase):
    """Comandos «mapa» e «ir a <sala>» (specs/005-niebla-ir-a)."""

    def test_mapa_sin_argumentos(self):
        """FR-018: el comando para ver el mapa conocido."""
        self.assertEqual(parse_command("mapa"), Command("mapa"))
        self.assertEqual(parse_command("  MAPA "), Command("mapa"))

    def test_mapa_no_lleva_argumentos(self):
        """FR-018."""
        with self.assertRaises(CommandError):
            parse_command("mapa 3")

    def test_mapa_no_es_accion_del_modelo(self):
        """FR-019: ver el mapa no se registra como acción."""
        self.assertFalse(is_game_action(parse_command("mapa")))

    def test_ir_a_convierte_la_sala_a_entero(self):
        """FR-022: <sala> es el identificador numérico."""
        self.assertEqual(parse_command("ir a 7"), Command("ir a", 7))
        self.assertEqual(parse_command("IR A 12"), Command("ir a", 12))

    def test_ir_a_vuelve_a_su_forma_escrita(self):
        """FR-022: parse_command(comando.to_text()) devuelve el mismo comando."""
        comando = parse_command("ir a 7")

        self.assertEqual(comando.to_text(), "ir a 7")
        self.assertEqual(parse_command(comando.to_text()), comando)

    def test_ir_a_mal_escrito_se_rechaza(self):
        """FR-022: sin sala, con una sala que no es número o sin la «a»."""
        for texto in ("ir", "ir a", "ir 7", "ir a siete", "ir a -3", "ir a 7 8", "ir b 7"):
            with self.assertRaises(CommandError, msg=texto):
                parse_command(texto)

    def test_ir_a_no_es_accion_del_modelo(self):
        """FR-031: en la bitácora quedan sus pasos, no la orden."""
        self.assertFalse(is_game_action(parse_command("ir a 7")))

    def test_la_ayuda_los_menciona(self):
        """FR-018, FR-022."""
        from controller.commands import HELP_LINES

        texto = "\n".join(HELP_LINES)
        self.assertIn("mapa", texto)
        self.assertIn("ir a <sala>", texto)


if __name__ == "__main__":
    unittest.main()
