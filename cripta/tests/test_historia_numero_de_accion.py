"""«historia #k» numera las acciones desde 1 (FR-003 y FR-010 de specs/003-linea-de-tiempo).

#1 es el estado justo antes de la primera acción, el mismo que «historia 0»;
#k es el estado justo antes de la acción k. #0 y un k mayor que las acciones
tomadas se rechazan, sin consumir tiempo ni quedar en la bitácora (FR-006).
La conversión vive en el controlador; el modelo sigue contando desde 0.

Usa los datos offline con la primera cripta que se lista, sin depender de su
id ni de su tamaño.
"""
import io
import os
import tempfile
import unittest

from adapters.fuente_offline import FuenteOffline
from controller.application import InUseIds, _consultar_historia, build_game, play
from controller.commands import WAIT, Command
from controller.game_controller import GameController
from model.consulta_historia import ConsultaRechazada
from repository.repositorio_cripta import RepositorioCripta
from tests.test_linea_de_tiempo import estado_del_resumen
from view.console_view import ConsoleView, lineas_de_historia


OFFLINE_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_offline")
ACCIONES = 3


class EntradaGuionada:
    def __init__(self, lineas):
        self.lineas = list(lineas)

    def __call__(self, prompt):
        if not self.lineas:
            raise EOFError
        return self.lineas.pop(0)


class ConCarpetaTemporal(unittest.TestCase):

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.directorio.cleanup()

    def repositorio(self, nombre):
        in_use = InUseIds()
        repositorio = RepositorioCripta(
            FuenteOffline(OFFLINE_DATA),
            os.path.join(self.directorio.name, nombre),
            consultar_ids_en_uso=in_use,
        )
        in_use.repository = repositorio
        return repositorio, in_use


class TestNumeroDeAccion(ConCarpetaTemporal):

    def setUp(self):
        super().setUp()
        repositorio, in_use = self.repositorio("cache")
        repositorio.iniciar_partida(repositorio.listar_criptas()[0]["id"])
        self.game = build_game(repositorio, 5, in_use=in_use)
        controller = GameController(self.game, repository=repositorio)
        for _ in range(ACCIONES):
            self.assertTrue(controller.execute(Command(WAIT)).accepted)
        if self.game.is_over:
            self.skipTest("la partida terminó antes de tomar las acciones")
        self.tomadas = self.game.timeline.cantidad_de_acciones()

    def foto(self):
        return (self.game.state.clock, self.tomadas, self.game.timeline.cantidad_de_acciones())

    def test_la_primera_accion_es_la_1_y_da_lo_mismo_que_el_instante_0(self):
        """FR-003: «historia #1» es el estado justo antes de la primera acción,
        el mismo que «historia 0», y se muestra como «antes de la accion 1»."""
        por_accion = _consultar_historia(self.game, "#1")
        por_instante = _consultar_historia(self.game, 0)

        self.assertEqual(estado_del_resumen(por_accion), estado_del_resumen(por_instante))
        self.assertEqual(lineas_de_historia(por_accion)[0], "Instante 0 (antes de la accion 1):")

    def test_la_ultima_accion_tomada_es_valida(self):
        """FR-003 y FR-010: con N acciones tomadas, «historia #N» es válido y
        es el estado justo antes de la acción N, no el presente."""
        resumen = _consultar_historia(self.game, f"#{self.tomadas}")
        instante_de_la_ultima = self.game.timeline.acciones()[self.tomadas - 1].reloj

        self.assertEqual(resumen.instante, instante_de_la_ultima)
        self.assertLess(resumen.instante, self.game.state.clock)
        self.assertEqual(
            lineas_de_historia(resumen)[0],
            f"Instante {instante_de_la_ultima} (antes de la accion {self.tomadas}):",
        )

    def test_cada_k_es_la_accion_k(self):
        """FR-003: «historia #k» da el instante en que se tomó la acción k."""
        for k in range(1, self.tomadas + 1):
            with self.subTest(k=k):
                resumen = _consultar_historia(self.game, f"#{k}")
                self.assertEqual(resumen.instante, self.game.timeline.acciones()[k - 1].reloj)

    def test_la_accion_0_se_rechaza_sin_cambiar_nada(self):
        """FR-010: la acción 0 no existe, porque se cuentan desde 1."""
        antes = self.foto()

        with self.assertRaises(ConsultaRechazada) as error:
            _consultar_historia(self.game, "#0")

        self.assertIn("desde 1", str(error.exception))
        self.assertEqual(self.foto(), antes)

    def test_una_accion_no_tomada_se_rechaza_sin_cambiar_nada(self):
        """FR-010: con N acciones tomadas, «historia #N+1» se rechaza."""
        antes = self.foto()

        with self.assertRaises(ConsultaRechazada) as error:
            _consultar_historia(self.game, f"#{self.tomadas + 1}")

        self.assertIn(f"ha tomado {self.tomadas}", str(error.exception))
        self.assertEqual(self.foto(), antes)


class TestComandoEnLaPartida(ConCarpetaTemporal):

    def test_el_comando_numera_desde_1_y_no_queda_en_la_bitacora(self):
        """FR-003, FR-006 y FR-010 desde la consola: #1 y #2 se aceptan, #0 y
        #3 (con dos acciones tomadas) se rechazan, y ninguna consulta consume
        tiempo ni queda en partida.log."""
        repositorio, in_use = self.repositorio("cache_juego")
        cripta = repositorio.listar_criptas()[0]["id"]
        salida = io.StringIO()
        lineas = ["esperar", "esperar", "historia #1", "historia #2", "historia #0",
                  "historia #3", "salir"]
        vista = ConsoleView(output=salida, read_line=EntradaGuionada(lineas))
        bitacoras = os.path.join(self.directorio.name, "partidas")

        juego = play(repositorio, vista, 5, cripta, None, in_use, bitacoras)

        if juego.timeline.cantidad_de_acciones() != 2:
            self.skipTest("la partida no llegó a tomar las dos esperas")
        texto = salida.getvalue()
        self.assertIn("(antes de la accion 1):", texto)
        self.assertIn("(antes de la accion 2):", texto)
        self.assertNotIn("(antes de la accion 3):", texto)
        self.assertIn("las acciones se cuentan desde 1", texto)
        self.assertIn("el jugador ha tomado 2", texto)
        self.assertEqual(juego.player_actions, 2)

        nombres = os.listdir(bitacoras)
        self.assertEqual(len(nombres), 1)
        with open(os.path.join(bitacoras, nombres[0]), encoding="utf-8") as bitacora:
            cuerpo = bitacora.read().split("---\n")[1]
        self.assertEqual(cuerpo.split(), ["esperar", "esperar"])


if __name__ == "__main__":
    unittest.main()
