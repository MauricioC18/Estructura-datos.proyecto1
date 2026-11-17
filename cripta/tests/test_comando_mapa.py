"""El comando «mapa» en el bucle de comandos de la aplicación (specs/005-niebla-ir-a, T033).

Cada prueba cita en su docstring los requisitos que comprueba.
"""
import io
import os
import tempfile
import unittest

from adapters.fuente_offline import FuenteOffline
from controller.application import NO_KNOWN_MAP, InUseIds, _command_loop, build_game
from controller.commands import MOVE, Command
from controller.game_controller import GameController
from repository.repositorio_cripta import RepositorioCripta
from structures.mapa_conocido import MapaConocido
from tests.test_ir_a import BitacoraDePrueba, armar_partida, conectar, explorar, mapa_de_salas
from view.console_view import ConsoleView


OFFLINE_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_offline")


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


class TestPartidaReal(unittest.TestCase):
    """De punta a punta con los datos offline: la partida que arma la
    aplicación trae el mapa conocido y «mapa» e «ir a» lo usan. La cripta es
    la primera publicada, sin depender de su id ni de su tamaño."""

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.in_use = InUseIds()
        self.repository = RepositorioCripta(
            FuenteOffline(OFFLINE_DATA),
            os.path.join(self.directorio.name, "cache"),
            consultar_ids_en_uso=self.in_use,
        )
        self.in_use.repository = self.repository

    def tearDown(self):
        self.directorio.cleanup()

    def partida(self):
        primera = self.repository.listar_criptas()[0]["id"]
        self.repository.iniciar_partida(primera)
        return build_game(self.repository, 5, in_use=self.in_use)

    def test_la_partida_nueva_trae_el_mapa_conocido(self):
        """FR-003, FR-012, FR-018: la sala inicial está explorada y el
        comando la muestra."""
        game = self.partida()
        controller = GameController(game, BitacoraDePrueba(), self.repository)

        salida = jugar(controller, ["mapa", "salir"])

        self.assertIsInstance(game.known_map, MapaConocido)
        self.assertIs(controller.known_map, game.known_map)
        self.assertTrue(game.known_map.esta_explorada(game.player.room_id))
        self.assertIn(f"Sala {game.player.room_id}:", salida)

    def test_ir_a_usa_lo_que_el_motor_registro(self):
        """FR-002, FR-022, FR-023, FR-025: tras moverse con el motor real,
        «ir a» hacia la sala inicial se acepta y da al menos un paso, sin que
        nadie haya armado el conocimiento a mano."""
        game = self.partida()
        controller = GameController(game, BitacoraDePrueba(), self.repository)
        inicio = game.player.room_id
        salida = None

        for candidata in game.room_map.room(inicio).exits():
            if candidata.door.is_open:
                salida = candidata
                break

        if salida is None:
            self.skipTest("la sala inicial no tiene ninguna salida abierta")

        self.assertTrue(controller.execute(Command(MOVE, salida.direction)).accepted)
        if game.is_over:
            self.skipTest("la partida terminó al entrar a la sala vecina")
        self.assertTrue(game.known_map.esta_explorada(salida.destination))

        viaje = controller.travel(inicio)

        self.assertTrue(viaje.accepted)
        self.assertGreaterEqual(viaje.steps, 1)


if __name__ == "__main__":
    unittest.main()
