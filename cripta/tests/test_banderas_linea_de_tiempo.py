"""Banderas --checkpoint-cada y --replay --hasta (FR-014, FR-015 y FR-025 de specs/003-linea-de-tiempo).

Usan los datos offline con la primera cripta que se lista, sin depender de su
id ni de su tamaño. Cada prueba cita en su docstring los requisitos que
comprueba.
"""
import io
import os
import tempfile
import unittest
from unittest import mock

from adapters.fuente_offline import FuenteOffline
from controller.application import InUseIds, play, replay
from model.consulta_historia import PARTIDA_TERMINO_ANTES
from main import parse_arguments
from repository.repositorio_cripta import RepositorioCripta
from structures.linea_de_tiempo import COPIAS_CADA
from view.console_view import ConsoleView


OFFLINE_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_offline")


class EntradaGuionada:
    def __init__(self, lineas):
        self.lineas = list(lineas)

    def __call__(self, prompt):
        if not self.lineas:
            raise EOFError
        return self.lineas.pop(0)


class TestArgumentos(unittest.TestCase):

    def test_checkpoint_cada_tiene_valor_por_omision(self):
        """FR-015: sin la bandera se usa el valor por omisión."""
        self.assertEqual(parse_arguments([]).checkpoint_cada, COPIAS_CADA)

    def test_checkpoint_cada_se_configura(self):
        """FR-015."""
        self.assertEqual(parse_arguments(["--checkpoint-cada", "7"]).checkpoint_cada, 7)

    def test_checkpoint_cada_menor_que_uno_se_rechaza(self):
        """FR-015: K tiene que ser al menos 1."""
        with mock.patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_arguments(["--checkpoint-cada", "0"])

    def test_hasta_solo_con_replay(self):
        """FR-014: --hasta no tiene sentido sin una bitácora que reproducir."""
        with mock.patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_arguments(["--hasta", "100"])

        argumentos = parse_arguments(["--replay", "x.log", "--hasta", "100"])
        self.assertEqual(argumentos.hasta, 100)


class TestConPartidaReal(unittest.TestCase):

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.bitacoras = os.path.join(self.directorio.name, "partidas")

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

    def primera_cripta_y_salida(self):
        repositorio, _ = self.repositorio("cache_mirar")
        cripta = repositorio.listar_criptas()[0]["id"]
        repositorio.iniciar_partida(cripta)
        mapa = repositorio.crear_mapa()
        inicio = repositorio.crear_jugador().room_id
        for salida in mapa.room(inicio).exits():
            if salida.door.is_open:
                return cripta, salida.direction
        self.skipTest("la sala inicial no tiene ninguna salida abierta")

    def jugar(self, lineas, cripta, copias_cada=COPIAS_CADA):
        repositorio, in_use = self.repositorio("cache_juego")
        vista = ConsoleView(output=io.StringIO(), read_line=EntradaGuionada(lineas))
        return play(repositorio, vista, 5, cripta, None, in_use, self.bitacoras,
                    copias_cada=copias_cada)

    def unica_bitacora(self):
        nombres = os.listdir(self.bitacoras)
        self.assertEqual(len(nombres), 1)
        return os.path.join(self.bitacoras, nombres[0])

    def reproducir(self, **opciones):
        repositorio, in_use = self.repositorio("cache_replay")
        salida = []
        with mock.patch.object(ConsoleView, "__init__", side_effect=AssertionError("vista")):
            juego = replay(repositorio, self.unica_bitacora(), salida.append, in_use,
                           verbose=False, **opciones)
        return juego, salida

    def test_la_partida_nueva_usa_el_k_pedido(self):
        """FR-015: --checkpoint-cada llega a la línea de tiempo de la partida."""
        cripta, _ = self.primera_cripta_y_salida()

        juego = self.jugar(["esperar", "salir"], cripta, copias_cada=3)

        self.assertEqual(juego.timeline.copias_cada, 3)

    def test_replay_hasta_imprime_el_resumen_sin_la_vista(self):
        """FR-014 de la línea de tiempo, FR-016 de la niebla: al reproducir
        hasta el instante 0 se imprime su resumen, con el mapa conocido de
        ese instante, sin instanciar la vista."""
        cripta, direccion = self.primera_cripta_y_salida()
        original = self.jugar([f"mover {direccion}", "esperar", "salir"], cripta)

        juego, salida = self.reproducir(hasta=0)

        texto = "\n".join(salida)
        self.assertEqual(juego.state.clock, original.state.clock)
        self.assertIn("Instante 0 (antes de la accion 1):", texto)
        self.assertIn("Mapa conocido: 1 salas exploradas", texto)

    def test_replay_hasta_despues_del_final_muestra_el_estado_final(self):
        """FR-025 (Historia 2, escenario 6, Apéndice B): un instante posterior
        al reloj final muestra el estado final e indica que la partida
        terminó antes, sin instanciar la vista."""
        cripta, _ = self.primera_cripta_y_salida()
        original = self.jugar(["esperar", "salir"], cripta)
        final = original.state.clock
        pedido = final + 1000

        juego, salida = self.reproducir(hasta=pedido)

        aviso = PARTIDA_TERMINO_ANTES
        self.assertIn(aviso, salida)
        instantes = [linea for linea in salida if linea.startswith("Instante ")]
        self.assertEqual(len(instantes), 1)
        self.assertTrue(instantes[0].startswith(f"Instante {final} "))
        self.assertLess(salida.index(aviso), salida.index(instantes[0]))
        self.assertEqual(juego.state.clock, final, "consultar no cambia la partida")

    def test_replay_hasta_el_instante_final_no_avisa(self):
        """FR-025, caso borde: el instante final exacto no es posterior al
        final, así que se muestra sin el aviso."""
        cripta, _ = self.primera_cripta_y_salida()
        original = self.jugar(["esperar", "salir"], cripta)
        final = original.state.clock

        _, salida = self.reproducir(hasta=final)

        self.assertNotIn(PARTIDA_TERMINO_ANTES, salida)
        instantes = [linea for linea in salida if linea.startswith("Instante ")]
        self.assertEqual(len(instantes), 1)
        self.assertTrue(instantes[0].startswith(f"Instante {final} "))

    def test_replay_hasta_un_instante_negativo_se_sigue_rechazando(self):
        """FR-009, FR-025: solo un instante posterior al final cambia; uno
        negativo se sigue rechazando con un mensaje."""
        cripta, _ = self.primera_cripta_y_salida()
        self.jugar(["esperar", "salir"], cripta)

        _, salida = self.reproducir(hasta=-1)

        self.assertFalse([linea for linea in salida if linea.startswith("Instante ")])
        self.assertIn("No existe el instante -1: el reloj empieza en 0.", salida)

    def test_replay_hasta_despues_de_moverse_con_una_copia_por_accion(self):
        """FR-014, FR-015: con una copia por acción, el resumen del instante
        final está en la sala a la que se movió el jugador."""
        cripta, direccion = self.primera_cripta_y_salida()
        original = self.jugar([f"mover {direccion}", "salir"], cripta)
        if original.is_over:
            self.skipTest("la partida terminó al moverse")

        juego, salida = self.reproducir(hasta=original.state.clock, copias_cada=1)

        lineas_de_sala = [linea for linea in salida if linea.startswith("  Sala: ")]
        self.assertEqual(len(lineas_de_sala), 1)
        self.assertTrue(lineas_de_sala[0].startswith(f"  Sala: {juego.player.room_id},"))
        self.assertIn(f"Mapa conocido: 2 salas exploradas", "\n".join(salida))


if __name__ == "__main__":
    unittest.main()
