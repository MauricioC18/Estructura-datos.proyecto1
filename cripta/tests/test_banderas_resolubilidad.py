"""Banderas --verificar y --forzar, y el reporte al iniciar una partida.

Los requisitos son de specs/006-resolubilidad/spec.md (Historia 3); la
conexión es de specs/005-niebla-ir-a (tareas T054 a T056). Cada prueba cita
en su docstring el requisito de la especificación 006 que comprueba.

Usan dos paquetes sin conexión: datos_offline_p2, que trae la ubicación de
llaves, y datos_offline, que no la trae. La cripta se elige por el resultado
de su verificación, sin escribir ningún id ni tamaño.
"""
import io
import os
import tempfile
import unittest
from unittest import mock

import main
from adapters.fuente_offline import FuenteOffline
from controller import application
from controller.application import InUseIds, play, replay
from model.resolubilidad import CODIGO_NO_RESOLUBLE, CODIGO_RESOLUBLE, CODIGO_SIN_VERIFICAR
from repository.repositorio_cripta import RepositorioCripta
from view.console_view import ConsoleView


CARPETA_CRIPTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAQUETE_CON_LLAVES = os.path.join(CARPETA_CRIPTA, "datos_offline_p2")
PAQUETE_SIN_LLAVES = os.path.join(CARPETA_CRIPTA, "datos_offline")
ENCABEZADO_DEL_REPORTE = "Verificación de resolubilidad:"


class EntradaGuionada:
    def __init__(self, lineas):
        self.lineas = list(lineas)

    def __call__(self, prompt):
        if not self.lineas:
            raise EOFError
        return self.lineas.pop(0)


def argumentos_rechazados(lista):
    with mock.patch("sys.stderr", io.StringIO()):
        try:
            main.parse_arguments(lista)
        except SystemExit:
            return True
    return False


class TestArgumentos(unittest.TestCase):

    def test_por_omision_no_se_fuerza_ni_se_verifica(self):
        """006/FR-016: sin --forzar se exige la resolubilidad."""
        argumentos = main.parse_arguments([])

        self.assertFalse(argumentos.forzar)
        self.assertIsNone(argumentos.verificar)

    def test_las_banderas_se_leen(self):
        """006/FR-016 y 006/FR-018."""
        self.assertTrue(main.parse_arguments(["--forzar"]).forzar)
        self.assertEqual(main.parse_arguments(["--verificar", "x"]).verificar, "x")

    def test_forzar_solo_al_empezar_una_partida_nueva(self):
        """006/FR-016: --forzar no tiene sentido al reproducir, medir, cargar
        ni verificar."""
        for otras in (["--replay", "x.log"], ["--bench"], ["--cargar", "x"], ["--verificar", "x"]):
            with self.subTest(otras=otras):
                self.assertTrue(argumentos_rechazados(["--forzar", *otras]))

    def test_verificar_no_se_combina_con_otro_modo(self):
        """006/FR-018: --verificar solo verifica."""
        for otras in (["--replay", "x.log"], ["--bench"], ["--cargar", "x"]):
            with self.subTest(otras=otras):
                self.assertTrue(argumentos_rechazados(["--verificar", "x", *otras]))


class ConPaquetes(unittest.TestCase):

    def setUp(self):
        if not os.path.isdir(PAQUETE_CON_LLAVES):
            self.skipTest("no está el paquete datos_offline_p2")
        self.directorio = tempfile.TemporaryDirectory()
        self.bitacoras = os.path.join(self.directorio.name, "partidas")
        self._caches = 0

    def tearDown(self):
        self.directorio.cleanup()

    def carpeta_de_cache(self):
        self._caches += 1
        return os.path.join(self.directorio.name, f"cache{self._caches}")

    def repositorio(self, paquete=PAQUETE_CON_LLAVES):
        in_use = InUseIds()
        repositorio = RepositorioCripta(
            FuenteOffline(paquete), self.carpeta_de_cache(), consultar_ids_en_uso=in_use
        )
        in_use.repository = repositorio
        return repositorio, in_use

    def cripta_con_codigo(self, codigo, paquete=PAQUETE_CON_LLAVES):
        """La primera cripta del paquete cuya verificación da ese código."""
        repositorio, _ = self.repositorio(paquete)
        for cripta in repositorio.listar_criptas():
            repositorio.empezar_conteo_de_partida()
            if repositorio.verificar_cripta(cripta["id"]).codigo_de_salida() == codigo:
                return cripta["id"]
        self.skipTest(f"el paquete no trae una cripta con código {codigo}")

    def verificar_por_linea_de_comandos(self, cripta, paquete=PAQUETE_CON_LLAVES):
        salida = io.StringIO()
        with mock.patch.object(ConsoleView, "__init__", side_effect=AssertionError("vista")), \
                mock.patch.object(application, "build_game", side_effect=AssertionError("motor")), \
                mock.patch("sys.stdout", salida):
            codigo = main.main(["--verificar", cripta, "--offline", paquete,
                                "--cache", self.carpeta_de_cache()])
        return codigo, salida.getvalue()

    def jugar(self, cripta, lineas, paquete=PAQUETE_CON_LLAVES, forzar=False, load_path=None):
        repositorio, in_use = self.repositorio(paquete)
        salida = io.StringIO()
        vista = ConsoleView(output=salida, read_line=EntradaGuionada(lineas))
        juego = play(repositorio, vista, 5, cripta, None, in_use, self.bitacoras,
                     load_path=load_path, forzar=forzar)
        return juego, salida.getvalue()

    def bitacoras_escritas(self):
        if not os.path.isdir(self.bitacoras):
            return []
        return sorted(os.listdir(self.bitacoras))


class TestVerificar(ConPaquetes):

    def test_una_cripta_resoluble_termina_con_0_sin_vista_ni_motor(self):
        """006/FR-018: --verificar solo verifica, muestra el reporte sin
        instanciar la vista ni iniciar una partida, y termina con 0."""
        cripta = self.cripta_con_codigo(CODIGO_RESOLUBLE)

        codigo, texto = self.verificar_por_linea_de_comandos(cripta)

        self.assertEqual(codigo, 0)
        self.assertIn(f"{ENCABEZADO_DEL_REPORTE} la cripta es resoluble.", texto)
        self.assertIn("Orden de obtención de llaves:", texto)
        self.assertEqual(self.bitacoras_escritas(), [])

    def test_una_cripta_no_resoluble_termina_con_1_y_muestra_el_reporte(self):
        """006/FR-018 y 006/FR-016: el código 1 dice que no es resoluble, y el
        reporte explica por qué."""
        cripta = self.cripta_con_codigo(CODIGO_NO_RESOLUBLE)

        codigo, texto = self.verificar_por_linea_de_comandos(cripta)

        self.assertEqual(codigo, 1)
        self.assertIn(f"{ENCABEZADO_DEL_REPORTE} la cripta no es resoluble.", texto)
        self.assertIn("Llaves que no se pueden obtener:", texto)

    def test_sin_ubicacion_de_llaves_termina_con_2(self):
        """006/FR-018 y 006/FR-020: si falta la ubicación de llaves, el código
        es 2 y el reporte dice que no se pudo verificar."""
        cripta = self.cripta_con_codigo(CODIGO_SIN_VERIFICAR, PAQUETE_SIN_LLAVES)

        codigo, texto = self.verificar_por_linea_de_comandos(cripta, PAQUETE_SIN_LLAVES)

        self.assertEqual(codigo, 2)
        self.assertIn(f"{ENCABEZADO_DEL_REPORTE} no se pudo verificar.", texto)

    def test_una_cripta_que_no_existe_no_se_confunde_con_un_resultado(self):
        """006/FR-018 reserva 0, 1 y 2 para los resultados de la verificación;
        un error de datos termina con 3 y lo dice."""
        codigo, texto = self.verificar_por_linea_de_comandos("no-existe")

        self.assertEqual(codigo, 3)
        self.assertIn("Error:", texto)


class TestReporteAlIniciar(ConPaquetes):

    def test_apendice_b_no_resoluble_sin_forzar_no_inicia_y_muestra_el_reporte(self):
        """006/FR-016 (Historia 3, escenario 1, Apéndice B): una cripta no
        resoluble sin --forzar no inicia, se muestra el reporte y no se abre
        bitácora."""
        cripta = self.cripta_con_codigo(CODIGO_NO_RESOLUBLE)

        juego, texto = self.jugar(cripta, ["esperar", "salir"])

        self.assertIsNone(juego)
        self.assertIn(f"{ENCABEZADO_DEL_REPORTE} la cripta no es resoluble.", texto)
        self.assertIn("Llaves que no se pueden obtener:", texto)
        self.assertIn("--forzar", texto)
        self.assertNotIn("Bitacora:", texto)
        self.assertEqual(self.bitacoras_escritas(), [])

    def test_no_resoluble_con_forzar_muestra_el_reporte_e_inicia(self):
        """006/FR-016 (Historia 3, escenario 2): con --forzar se muestra el
        reporte y la partida inicia igual."""
        cripta = self.cripta_con_codigo(CODIGO_NO_RESOLUBLE)

        juego, texto = self.jugar(cripta, ["esperar", "salir"], forzar=True)

        self.assertIsNotNone(juego)
        self.assertGreater(juego.state.clock, 0)
        self.assertIn(f"{ENCABEZADO_DEL_REPORTE} la cripta no es resoluble.", texto)
        self.assertLess(texto.index(ENCABEZADO_DEL_REPORTE), texto.index("Escriba ayuda"))
        self.assertEqual(len(self.bitacoras_escritas()), 1)

    def test_resoluble_muestra_el_orden_antes_de_la_primera_accion(self):
        """006/FR-017 (Historia 3, escenario 3): una cripta resoluble muestra
        el reporte con el orden de llaves antes de la primera acción."""
        cripta = self.cripta_con_codigo(CODIGO_RESOLUBLE)

        juego, texto = self.jugar(cripta, ["esperar", "salir"])

        self.assertIsNotNone(juego)
        self.assertIn(f"{ENCABEZADO_DEL_REPORTE} la cripta es resoluble.", texto)
        self.assertLess(texto.index("Orden de obtención de llaves:"), texto.index("Escriba ayuda"))

    def test_sin_ubicacion_de_llaves_inicia_y_lo_dice(self):
        """006/FR-020 (Historia 3, escenario 6): sin ubicación de llaves la
        partida inicia sin --forzar y el reporte dice que no se pudo verificar."""
        cripta = self.cripta_con_codigo(CODIGO_SIN_VERIFICAR, PAQUETE_SIN_LLAVES)

        juego, texto = self.jugar(cripta, ["esperar", "salir"], paquete=PAQUETE_SIN_LLAVES)

        self.assertIsNotNone(juego)
        self.assertIn(f"{ENCABEZADO_DEL_REPORTE} no se pudo verificar.", texto)

    def test_una_partida_cargada_no_se_verifica(self):
        """006/FR-019 (Historia 3, escenario 5): al cargar una partida guardada
        no se verifica de nuevo, aunque la cripta no sea resoluble y no se
        use --forzar."""
        cripta = self.cripta_con_codigo(CODIGO_NO_RESOLUBLE)
        archivo = os.path.join(self.directorio.name, "guardada.cripta")
        self.jugar(cripta, ["esperar", f"guardar {archivo}", "salir"], forzar=True)

        juego, texto = self.jugar(cripta, ["salir"], load_path=archivo)

        self.assertIsNotNone(juego)
        self.assertNotIn(ENCABEZADO_DEL_REPORTE, texto)

    def test_replay_de_una_partida_forzada_no_se_detiene(self):
        """006/FR-016 (Historia 3, escenario 7): la reproducción de una
        partida jugada con --forzar no se detiene por la verificación."""
        cripta = self.cripta_con_codigo(CODIGO_NO_RESOLUBLE)
        original, _ = self.jugar(cripta, ["esperar", "esperar", "salir"], forzar=True)
        repositorio, in_use = self.repositorio()
        bitacora = os.path.join(self.bitacoras, self.bitacoras_escritas()[0])

        reproducida = replay(repositorio, bitacora, lambda texto: None, in_use, verbose=False)

        self.assertIsNotNone(reproducida)
        self.assertEqual(reproducida.state.clock, original.state.clock)


if __name__ == "__main__":
    unittest.main()
