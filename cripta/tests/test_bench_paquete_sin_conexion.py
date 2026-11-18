"""--bench con la carpeta de --offline (§5.3 y §6.1, specs/005-niebla-ir-a FR-036).

La fila de la cripta de referencia en --bench sale de las criptas del paquete
sin conexion. Estas pruebas comprueban que «python main.py --bench --offline
CARPETA» mide esa carpeta, que sin --offline se sigue usando la carpeta por
omision. No dependen del id ni del tamaño de ninguna cripta.
"""
import types
import unittest
from unittest import mock

from benchmark import bench_mapa_conocido, benchmark
from main import main


def suite_falsa(acepta_carpeta):
    """Un modulo de suite que anota con que argumentos se llamo su run()."""
    llamadas = []
    modulo = types.ModuleType("suite_falsa")

    def run(*argumentos):
        llamadas.append(argumentos)
        return []

    modulo.run = run
    if acepta_carpeta:
        modulo.USA_PAQUETE_SIN_CONEXION = True

    return modulo, llamadas


class TestMainPasaLaCarpeta(unittest.TestCase):

    def test_bench_con_offline_mide_esa_carpeta(self):
        """FR-036: --bench --offline CARPETA le pasa CARPETA al ejecutor."""
        with mock.patch("benchmark.benchmark.main") as ejecutor:
            self.assertEqual(main(["--bench", "--offline", "otra_carpeta"]), 0)

        ejecutor.assert_called_once_with(carpeta_sin_conexion="otra_carpeta")

    def test_bench_sin_offline_no_cambia_la_carpeta(self):
        """FR-036: sin --offline, el ejecutor no recibe carpeta y cada suite usa la suya."""
        with mock.patch("benchmark.benchmark.main") as ejecutor:
            self.assertEqual(main(["--bench"]), 0)

        ejecutor.assert_called_once_with(carpeta_sin_conexion=None)


class TestEjecutorPasaLaCarpeta(unittest.TestCase):

    def ejecutar(self, modulo, carpeta):
        lineas = []
        # La descripción del equipo se reemplaza primero: mock.patch resuelve sus
        # rutas con importlib.import_module, que la segunda reemplaza.
        with mock.patch("benchmark.benchmark.descripcion_del_equipo", return_value="equipo"), \
                mock.patch("benchmark.benchmark.importlib.import_module", return_value=modulo):
            benchmark.main(suites=(("Suite", "suite_falsa"),), output=lineas.append,
                           carpeta_sin_conexion=carpeta)
        return lineas

    def test_la_suite_que_mide_criptas_reales_recibe_la_carpeta(self):
        """FR-036: la suite que declara usar el paquete recibe la carpeta de --offline."""
        modulo, llamadas = suite_falsa(acepta_carpeta=True)

        lineas = self.ejecutar(modulo, "otra_carpeta")

        self.assertEqual(llamadas, [("otra_carpeta",)])
        self.assertIn("Paquete sin conexion: otra_carpeta", lineas)

    def test_sin_carpeta_la_suite_usa_la_suya(self):
        """FR-036: sin --offline, run() se llama sin argumentos, como antes."""
        modulo, llamadas = suite_falsa(acepta_carpeta=True)

        self.ejecutar(modulo, None)

        self.assertEqual(llamadas, [()])

    def test_las_demas_suites_no_reciben_la_carpeta(self):
        """§5.3: una suite que no mide criptas reales se llama igual que antes."""
        modulo, llamadas = suite_falsa(acepta_carpeta=False)

        self.ejecutar(modulo, "otra_carpeta")

        self.assertEqual(llamadas, [()])

    def test_la_suite_del_mapa_conocido_declara_usar_el_paquete(self):
        """FR-036: la medición de «ir a» con criptas reales es la que recibe la carpeta."""
        self.assertTrue(bench_mapa_conocido.USA_PAQUETE_SIN_CONEXION)
        self.assertIn(("Mapa conocido y viaje ir a", "benchmark.bench_mapa_conocido"),
                      benchmark.SUITES)


if __name__ == "__main__":
    unittest.main()
