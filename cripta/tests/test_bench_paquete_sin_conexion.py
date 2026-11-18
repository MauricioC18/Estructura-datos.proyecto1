"""--bench con la carpeta de --offline (§5.3 y §6.1, specs/005-niebla-ir-a FR-036).

La fila de la cripta de referencia en --bench sale de las criptas del paquete
sin conexion. Estas pruebas comprueban que «python main.py --bench --offline
CARPETA» mide esa carpeta, que sin --offline se sigue usando la carpeta por
omision, y que la fila de criptas reales muestra el promedio por paso. No
dependen del id ni del tamaño de ninguna cripta.
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



class TestFilaDeCriptasReales(unittest.TestCase):

    def test_la_fila_muestra_el_promedio_por_paso(self):
        """FR-036: la fila de cada cripta real muestra primer paso y promedio por paso."""
        cripta = bench_mapa_conocido.cuadricula(3)
        tiempos = (0.001, 0.002, 0.003, 0.004, 7)

        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("cripta-de-prueba", cripta)]),                 mock.patch.object(bench_mapa_conocido, "medir_paso_de_ir_a",
                                  return_value=tiempos):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0].seconds, 0.001)
        self.assertIn("cripta-de-prueba", filas[0].name)
        self.assertIn(f"({len(cripta)} salas)", filas[0].name)
        self.assertIn("primer paso 1.0000 ms", filas[0].detail)
        self.assertIn("por paso en un viaje de 7 pasos 2.0000 ms", filas[0].detail)

    def test_la_fila_mide_de_verdad_cada_cripta_del_paquete(self):
        """FR-036: sin reemplazar la medición, cada cripta tiene su fila con el promedio por paso."""
        criptas = [("primera", bench_mapa_conocido.cuadricula(3)),
                   ("segunda", bench_mapa_conocido.cuadricula(4))]

        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=criptas):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertEqual(len(filas), 2)
        for fila, (id_cripta, cripta) in zip(filas, criptas):
            self.assertIn(f"mapa completo de {id_cripta} ({len(cripta)} salas)", fila.name)
            self.assertIn("por paso en un viaje de", fila.detail)

    def test_sin_ruta_entre_los_extremos_no_inventa_un_promedio(self):
        """§5.3: si el viaje entre los extremos no tiene pasos, la fila lo dice en vez de promediar."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("aislada", bench_mapa_conocido.cuadricula(3))]),                 mock.patch.object(bench_mapa_conocido, "medir_paso_de_ir_a",
                                  return_value=(0.001, 0.002, 0.003, 0.004, 0)):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertIn("por paso: sin ruta entre los extremos", filas[0].detail)
        self.assertNotIn("2.0000 ms", filas[0].detail)

    def test_sin_paquete_lo_dice_con_la_carpeta(self):
        """§5.3: sin paquete en la carpeta, la fila dice dónde se buscó."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion", return_value=[]):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertEqual(len(filas), 1)
        self.assertIsNone(filas[0].seconds)
        self.assertIn("otra_carpeta", filas[0].detail)


if __name__ == "__main__":
    unittest.main()
