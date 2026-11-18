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
from model.room import DIRECTIONS, Door, Exit, Room, RoomMap


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
        recorrido = bench_mapa_conocido.RecorridoMedido(
            1, 9, bench_mapa_conocido.ENTRE_EXTREMOS, 42)
        tiempos = (0.001, 0.002, 0.003, 0.004, 7, recorrido)

        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("cripta-de-prueba", cripta)]), \
                mock.patch.object(bench_mapa_conocido, "medir_paso_de_ir_a",
                                  return_value=tiempos):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0].seconds, 0.001)
        self.assertIn("cripta-de-prueba", filas[0].name)
        self.assertIn(f"({len(cripta)} salas)", filas[0].name)
        self.assertIn("primer paso 1.0000 ms", filas[0].detail)
        self.assertIn("por paso en un viaje de 7 pasos 2.0000 ms", filas[0].detail)
        self.assertIn("de la sala 1 a la 9 (extremos, costo 42)", filas[0].detail)

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

    def test_sin_ruta_entre_los_extremos_mide_hacia_la_mas_lejana(self):
        """FR-036: sin ruta entre los extremos, la fila mide y dice el viaje hacia la sala más lejana."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("cortada", ultima_aislada())]):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertIn("sin ruta entre los extremos; de la sala 1 a la 3, "
                      "la mas lejana alcanzable (costo 12)", filas[0].detail)
        self.assertIn("por paso en un viaje de 2 pasos", filas[0].detail)

    def test_un_viaje_sin_pasos_no_inventa_un_promedio(self):
        """§5.3: si el viaje medido no tiene pasos, la fila lo dice en vez de promediar."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("aislada", sin_salidas())]):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertIn("sin ruta desde la sala 1 a ninguna otra; medido hacia la 2",
                      filas[0].detail)
        self.assertIn("por paso: el viaje no dio pasos", filas[0].detail)

    def test_sin_paquete_lo_dice_con_la_carpeta(self):
        """§5.3: sin paquete en la carpeta, la fila dice dónde se buscó."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion", return_value=[]):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertEqual(len(filas), 1)
        self.assertIsNone(filas[0].seconds)
        self.assertIn("otra_carpeta", filas[0].detail)


def mapa_de_salas(cantidad, uniones):
    """cantidad salas y uniones (origen, destino, costo, con_vuelta)."""
    room_map = RoomMap()
    for numero in range(1, cantidad + 1):
        room_map.add(Room(numero, f"Sala {numero}"))
    for origen, destino, costo, con_vuelta in uniones:
        puerta = Door(origen, destino, cost=costo)
        sala = room_map.room(origen)
        sala.add_exit(Exit(direccion_libre(sala), destino, puerta))
        if con_vuelta:
            sala = room_map.room(destino)
            sala.add_exit(Exit(direccion_libre(sala), origen, puerta))
    return room_map


def direccion_libre(sala):
    usadas = [salida.direction for salida in sala.exits()]
    return next(direccion for direccion in DIRECTIONS if direccion not in usadas)


def ultima_aislada():
    """1-2 (5) y 2-3 (7); la sala 4, la última, no tiene salidas."""
    return mapa_de_salas(4, [(1, 2, 5, True), (2, 3, 7, True)])


def sin_salidas():
    return mapa_de_salas(2, [])


def recorrido_con_mapa_completo(room_map):
    return bench_mapa_conocido.elegir_recorrido(
        bench_mapa_conocido.conocimiento_completo(room_map), room_map)


class TestElegirRecorrido(unittest.TestCase):

    def test_con_ruta_entre_los_extremos_los_usa(self):
        """FR-036: si hay ruta de la primera sala a la última, se mide ese viaje."""
        recorrido = recorrido_con_mapa_completo(bench_mapa_conocido.cuadricula(3))

        self.assertEqual(recorrido.motivo, bench_mapa_conocido.ENTRE_EXTREMOS)
        self.assertEqual((recorrido.partida, recorrido.destino), (1, 9))

    def test_sin_ruta_va_a_la_mas_lejana_por_costo(self):
        """FR-036: sin ruta a la última, el destino es la alcanzable de mayor costo mínimo."""
        recorrido = recorrido_con_mapa_completo(ultima_aislada())

        self.assertEqual(recorrido.motivo, bench_mapa_conocido.HACIA_LA_MAS_LEJANA)
        self.assertEqual((recorrido.partida, recorrido.destino, recorrido.costo), (1, 3, 12))

    def test_la_mas_lejana_es_por_costo_y_no_por_salas(self):
        """FR-036: una sala a un paso caro queda más lejos que otra a dos pasos baratos."""
        room_map = mapa_de_salas(5, [(1, 2, 1, True), (2, 3, 1, True), (1, 4, 50, True)])

        recorrido = recorrido_con_mapa_completo(room_map)

        self.assertEqual((recorrido.destino, recorrido.costo), (4, 50))

    def test_empate_gana_la_de_menor_id(self):
        """§5.3: dos salas igual de lejanas: gana la de menor id, para repetir la medición."""
        room_map = mapa_de_salas(4, [(1, 3, 5, True), (1, 2, 5, True)])

        self.assertEqual(recorrido_con_mapa_completo(room_map).destino, 2)

    def test_respeta_las_salidas_de_un_solo_sentido(self):
        """FR-036: una sala que solo tiene salida HACIA la primera no cuenta como alcanzable."""
        room_map = mapa_de_salas(4, [(1, 2, 3, True), (3, 1, 100, False)])

        recorrido = recorrido_con_mapa_completo(room_map)

        self.assertEqual((recorrido.destino, recorrido.costo), (2, 3))

    def test_sin_salas_alcanzables_lo_dice(self):
        """§5.3: si desde la primera sala no se alcanza ninguna, el motivo lo dice."""
        recorrido = recorrido_con_mapa_completo(sin_salidas())

        self.assertEqual(recorrido.motivo, bench_mapa_conocido.SIN_ALCANZABLES)
        self.assertIsNone(recorrido.costo)

    def test_las_cuadriculas_sinteticas_siguen_midiendo_entre_extremos(self):
        """§5.3: las filas sintéticas no cambian: siempre hay ruta entre los extremos."""
        *_, largo, recorrido = bench_mapa_conocido.medir_paso_de_ir_a(
            bench_mapa_conocido.cuadricula(3), con_alternativa_lineal=False)

        self.assertEqual(recorrido.motivo, bench_mapa_conocido.ENTRE_EXTREMOS)
        self.assertGreater(largo, 0)


if __name__ == "__main__":
    unittest.main()
