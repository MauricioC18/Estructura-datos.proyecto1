"""El comando «mapa» en el bucle de comandos de la aplicación (specs/003-niebla-ir-a, T033).

Cada prueba cita en su docstring los requisitos que comprueba.
"""
import io
import unittest

from controller.application import NO_KNOWN_MAP, _command_loop
from controller.game_controller import GameController
from tests.test_ir_a import BitacoraDePrueba, armar_partida, conectar, explorar, mapa_de_salas
from view.console_view import ConsoleView


class EntradaGuionada:
    """Entrega líneas fijas como si las escribiera el jugador."""

    def __init__(self, lineas):
        self.lineas = list(lineas)

    def __call__(self, prompt):
        if not self.lineas:
            raise EOFError
        return self.lineas.pop(0)


def jugar(controller, lineas):
    salida = io.StringIO()
    vista = ConsoleView(output=salida, read_line=EntradaGuionada(lineas))
    _command_loop(controller, vista)
    return salida.getvalue()


class TestComandoMapa(unittest.TestCase):

    def setUp(self):
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 2, "E", costo=40)
        conectar(room_map, 2, 3, "S")
        self.game, self.mapa = armar_partida(room_map)
        self.bitacora = BitacoraDePrueba()

    def test_muestra_el_mapa_conocido(self):
        """FR-018: el comando muestra las salas exploradas con sus salidas."""
        explorar(self.mapa, 1, 2)
        controller = GameController(self.game, self.bitacora, known_map=self.mapa)

        salida = jugar(controller, ["mapa", "salir"])

        self.assertIn("Mapa conocido:", salida)
        self.assertIn("Sala 1: Sala 1", salida)
        self.assertIn("Sala 2: Sala 2", salida)
        self.assertIn("E -> 2 (costo 40) abierta", salida)
        self.assertIn("S -> hay algo en esa direccion", salida)
        self.assertNotIn("Sala 3:", salida)

    def test_no_consume_tiempo_ni_se_registra(self):
        """FR-019: ver el mapa no consume tiempo, no es acción y no cambia nada."""
        explorar(self.mapa, 1)
        controller = GameController(self.game, self.bitacora, known_map=self.mapa)
        reloj = self.game.state.clock
        acciones = self.game.player_actions
        version = self.mapa.version

        jugar(controller, ["mapa", "mapa", "salir"])

        self.assertEqual(self.game.state.clock, reloj)
        self.assertEqual(self.game.player_actions, acciones)
        self.assertEqual(self.mapa.version, version)
        self.assertEqual(self.bitacora.lineas, [])

    def test_sin_mapa_conocido_se_rechaza_como_ir_a(self):
        """FR-012, FR-019, FR-022: sin mapa conocido, «mapa» e «ir a» se
        rechazan con un mensaje y sin consumir tiempo, en vez de fallar."""
        controller = GameController(self.game, self.bitacora)
        reloj = self.game.state.clock

        salida = jugar(controller, ["mapa", "ir a 2", "salir"])

        self.assertIn(NO_KNOWN_MAP, salida)
        self.assertIn("Todavia no se puede viajar", salida)
        self.assertNotIn("Comando sin atender", salida)
        self.assertEqual(self.game.state.clock, reloj)
        self.assertEqual(self.game.player.room_id, 1)
        self.assertEqual(self.bitacora.lineas, [])


if __name__ == "__main__":
    unittest.main()
