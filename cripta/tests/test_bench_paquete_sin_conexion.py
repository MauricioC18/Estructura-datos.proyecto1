"""--bench con la carpeta de --offline (§5.3 y §6.1, specs/005-niebla-ir-a FR-036).

La fila de la cripta de referencia en --bench sale de las criptas del paquete
sin conexion. Estas pruebas comprueban que «python main.py --bench --offline
CARPETA» mide esa carpeta, que sin --offline se sigue usando la carpeta por
omision, que la fila de criptas reales muestra el promedio por paso y que
el viaje medido parte de la sala inicial de los datos de la cripta. No
dependen del id ni del tamaño de ninguna cripta.
"""
import json
import os
import shutil
import tempfile
import types
import unittest
from unittest import mock

from adapters.fuente_offline import FuenteOffline, RutasDatosOffline
from benchmark import bench_mapa_conocido, benchmark
from main import main
from model.room import DIRECTIONS, Door, Exit, Room, RoomMap

DATOS_OFFLINE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_offline")


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
            1, 9, bench_mapa_conocido.HACIA_LA_ULTIMA, 42)
        tiempos = (0.001, 0.002, 0.003, 0.004, 7, recorrido)

        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("cripta-de-prueba", cripta, 1)]), \
                mock.patch.object(bench_mapa_conocido, "medir_paso_de_ir_a",
                                  return_value=tiempos):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0].seconds, 0.001)
        self.assertIn("cripta-de-prueba", filas[0].name)
        self.assertIn(f"({len(cripta)} salas)", filas[0].name)
        self.assertIn("primer paso 1.0000 ms", filas[0].detail)
        self.assertIn("por paso en un viaje de 7 pasos 2.0000 ms", filas[0].detail)
        self.assertIn("de la sala inicial 1 a la 9, la ultima del esqueleto (costo 42)",
                      filas[0].detail)

    def test_la_fila_mide_de_verdad_cada_cripta_del_paquete(self):
        """FR-036: sin reemplazar la medición, cada cripta tiene su fila con el promedio por paso."""
        criptas = [("primera", bench_mapa_conocido.cuadricula(3), 1),
                   ("segunda", bench_mapa_conocido.cuadricula(4), 1)]

        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=criptas):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertEqual(len(filas), 2)
        for fila, (id_cripta, cripta, _) in zip(filas, criptas):
            self.assertIn(f"mapa completo de {id_cripta} ({len(cripta)} salas)", fila.name)
            self.assertIn("por paso en un viaje de", fila.detail)

    def test_la_partida_es_la_sala_inicial_de_los_datos(self):
        """FR-036: el viaje medido parte de la sala inicial de la cripta, no de la primera del esqueleto."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("inicial-en-medio", inicial_en_medio(), 3)]):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertIn("de la sala inicial 3 a la 4, la ultima del esqueleto (costo 9)",
                      filas[0].detail)
        self.assertIn("por paso en un viaje de 1 pasos", filas[0].detail)

    def test_sin_ruta_a_la_ultima_mide_hacia_la_mas_lejana(self):
        """FR-036: sin ruta a la última, la fila mide y dice el viaje hacia la sala más lejana."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("cortada", ultima_aislada(), 1)]):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertIn("sin ruta de la sala inicial a la 4, la ultima del esqueleto; "
                      "de la sala inicial 1 a la 3, la mas lejana alcanzable (costo 12)",
                      filas[0].detail)
        self.assertIn("por paso en un viaje de 2 pasos", filas[0].detail)

    def test_si_la_sala_inicial_es_la_ultima_mide_hacia_la_mas_lejana(self):
        """FR-036: si la sala inicial es la última del esqueleto, el viaje va a la más lejana."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("al-final", bench_mapa_conocido.cuadricula(3), 9)]):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertIn("la sala inicial es la ultima del esqueleto; de la sala inicial 9 a la ",
                      filas[0].detail)
        self.assertIn("la mas lejana alcanzable", filas[0].detail)

    def test_un_viaje_sin_pasos_no_inventa_un_promedio(self):
        """§5.3: si el viaje medido no tiene pasos, la fila lo dice en vez de promediar."""
        with mock.patch.object(bench_mapa_conocido, "criptas_sin_conexion",
                               return_value=[("aislada", sin_salidas(), 1)]):
            filas = bench_mapa_conocido.mediciones_de_criptas_reales("otra_carpeta")

        self.assertIn("sin ruta desde la sala inicial 1 a ninguna otra; medido hacia la 2",
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


def inicial_en_medio():
    """1-2 (1), 2-3 (1) y 3-4 (9). Desde la 1 a la 4 son 3 pasos y costo 11;
    desde la 3, que será la sala inicial, 1 paso y costo 9."""
    return mapa_de_salas(4, [(1, 2, 1, True), (2, 3, 1, True), (3, 4, 9, True)])


def recorrido_con_mapa_completo(room_map, partida=None):
    return bench_mapa_conocido.elegir_recorrido(
        bench_mapa_conocido.conocimiento_completo(room_map), room_map, partida)


class TestSalaInicialDelPaquete(unittest.TestCase):

    def test_la_sala_inicial_sale_de_los_datos_generales(self):
        """FR-036: con un paquete real cuya sala inicial no es la primera del esqueleto, la fila parte de ella."""
        with tempfile.TemporaryDirectory() as carpeta_temporal:
            carpeta = os.path.join(carpeta_temporal, "paquete")
            shutil.copytree(DATOS_OFFLINE, carpeta)
            fuente = FuenteOffline(carpeta)
            id_cripta = fuente.listar_criptas()["criptas"][0]["id"]
            generales = fuente.datos_generales(id_cripta)
            ids_del_esqueleto = [sala["id"] for sala in fuente.pagina_salas(id_cripta, 1)["salas"]]
            otra_inicial = ids_del_esqueleto[1]
            self.assertNotEqual(otra_inicial, ids_del_esqueleto[0])

            generales["sala_inicial"] = otra_inicial
            ruta = RutasDatosOffline(carpeta).datos_generales(id_cripta)
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(generales, archivo)

            criptas = bench_mapa_conocido.criptas_sin_conexion(carpeta)
            filas = bench_mapa_conocido.mediciones_de_criptas_reales(carpeta)

        self.assertEqual(criptas[0][2], otra_inicial)
        self.assertIn(f"de la sala inicial {otra_inicial} a la", filas[0].detail)


class TestElegirRecorrido(unittest.TestCase):

    def test_con_ruta_a_la_ultima_la_usa(self):
        """FR-036: si hay ruta de la sala de partida a la última, se mide ese viaje."""
        recorrido = recorrido_con_mapa_completo(bench_mapa_conocido.cuadricula(3))

        self.assertEqual(recorrido.motivo, bench_mapa_conocido.HACIA_LA_ULTIMA)
        self.assertEqual((recorrido.partida, recorrido.destino), (1, 9))

    def test_parte_de_la_sala_inicial_dada(self):
        """FR-036: con sala inicial, el viaje parte de ella y no de la primera del esqueleto."""
        recorrido = recorrido_con_mapa_completo(inicial_en_medio(), partida=3)

        self.assertEqual(recorrido.motivo, bench_mapa_conocido.HACIA_LA_ULTIMA)
        self.assertEqual((recorrido.partida, recorrido.destino, recorrido.costo), (3, 4, 9))

    def test_el_viaje_medido_parte_de_la_sala_inicial(self):
        """FR-036: el camino medido tiene los pasos desde la sala inicial, no desde la primera."""
        *_, largo, recorrido = bench_mapa_conocido.medir_paso_de_ir_a(
            inicial_en_medio(), con_alternativa_lineal=False, partida=3)

        self.assertEqual(recorrido.partida, 3)
        self.assertEqual(largo, 1)

    def test_una_sala_inicial_fuera_del_esqueleto_es_un_error(self):
        """§5.3: una sala inicial que no está en el esqueleto no se mide en silencio."""
        with self.assertRaises(ValueError):
            recorrido_con_mapa_completo(inicial_en_medio(), partida=99)

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

        self.assertEqual(recorrido.motivo, bench_mapa_conocido.HACIA_LA_ULTIMA)
        self.assertEqual(recorrido.partida, 1)
        self.assertGreater(largo, 0)


if __name__ == "__main__":
    unittest.main()
