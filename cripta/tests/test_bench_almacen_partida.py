"""
Pruebas del benchmark del guardado binario (§4.10).

Lo que hay que defender acá no son los tiempos, que cambian de máquina en
máquina, sino que la comparación sea justa: el JSON con el que se compara
tiene que guardar el mismo estado que el archivo binario y reconstruir los
mismos objetos. Si guardara menos, el binario saldría grande por nada.
"""
import tempfile
import unittest
from pathlib import Path

from adapters.almacen_partida import AlmacenPartida
from benchmark.bench_almacen_partida import (
    cargar_desde_json,
    construir_partida,
    guardar_en_json,
    leer_una_sala_del_json,
    medir,
    run,
    tamano_solo_con_identificadores,
)


class PruebasBenchAlmacenPartida(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._carpeta_temporal.name)
        self.juego = construir_partida(6, 6, decisiones=10)

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def test_el_json_guarda_el_mismo_estado_que_el_binario(self):
        ruta = self.carpeta / "partida.json"
        guardar_en_json(self.juego, ruta, versiones=("cripta-01", "3", "7"))

        room_map, enemies, player, contenido = cargar_desde_json(ruta)
        binario = AlmacenPartida(self.carpeta / "partida.cripta")
        binario.guardar(self.juego, versiones=("cripta-01", "3", "7"))
        partida = binario.cargar()

        self.assertEqual(contenido["clock"], partida.clock)
        self.assertEqual(contenido["sequence_counter"], partida.sequence_counter)
        self.assertEqual(len(contenido["events"]), len(partida.events))
        self.assertEqual(player.health, partida.player.health)
        self.assertEqual(player.room_id, partida.player.room_id)
        self.assertEqual(
            [item.instance_id for item in player.inventory],
            [item.instance_id for item in partida.player.inventory],
        )
        self.assertEqual(len(enemies), len(partida.enemies))
        self.assertEqual(
            list(room_map.room_ids()), list(partida.room_map.room_ids())
        )

    def test_el_json_reconstruye_las_salas_con_su_contenido(self):
        ruta = self.carpeta / "partida.json"
        guardar_en_json(self.juego, ruta)

        room_map, _, _, _ = cargar_desde_json(ruta)
        original = self.juego.room_map.room(2)
        cargada = room_map.room(2)

        self.assertEqual(cargada.name, original.name)
        self.assertEqual(len(cargada.traps), len(original.traps))
        self.assertEqual(len(cargada.floor_items), len(original.floor_items))
        self.assertEqual(len(cargada.exits()), len(original.exits()))

    def test_leer_una_sala_del_json_devuelve_esa_sala(self):
        ruta = self.carpeta / "partida.json"
        guardar_en_json(self.juego, ruta)

        self.assertEqual(leer_una_sala_del_json(ruta, 3)["room_id"], 3)
        self.assertIsNone(leer_una_sala_del_json(ruta, 99))

    def test_la_alternativa_de_solo_identificadores_pesa_menos(self):
        completo = AlmacenPartida(self.carpeta / "partida.cripta").guardar(self.juego)
        solo_ids = tamano_solo_con_identificadores(self.juego, self.carpeta)

        self.assertLess(solo_ids, completo)

    def test_la_medicion_corre_y_devuelve_las_cuatro_comparaciones(self):
        resultado = medir(6, 6)

        for clave in (
            "bytes_binarios",
            "bytes_json",
            "carga_binaria",
            "carga_json",
            "una_sala_binaria",
            "una_sala_json",
            "bytes_solo_ids",
        ):
            self.assertIn(clave, resultado)
            self.assertGreater(resultado[clave], 0)

    def test_el_binario_pesa_menos_que_el_json(self):
        """La razón por la que se eligió el formato propio."""
        resultado = medir(40, 50)

        self.assertLess(resultado["bytes_binarios"], resultado["bytes_json"])

    def test_recuperar_una_sala_no_crece_con_la_cripta(self):
        """Lo que pide §4.10: el JSON crece con el archivo, el binario no.

        Se compara la razón, no los tiempos sueltos, porque los tiempos
        dependen de la máquina.
        """
        chica = medir(6, 6)
        grande = medir(200, 150)

        crecimiento_binario = (
            grande["una_sala_binaria"] / chica["una_sala_binaria"]
        )
        crecimiento_json = grande["una_sala_json"] / chica["una_sala_json"]

        self.assertLess(crecimiento_binario, crecimiento_json)

    def test_run_entrega_las_mediciones_que_pide_el_bench(self):
        """--bench (§5.3) tiene que medir guardar y cargar."""
        mediciones = run()
        nombres = [medicion.name for medicion in mediciones]

        for operacion in ("Guardar", "Cargar completa", "Recuperar una sala"):
            with self.subTest(operacion=operacion):
                self.assertTrue(
                    any(nombre.startswith(operacion) for nombre in nombres)
                )

        for medicion in mediciones:
            if medicion.seconds is not None:
                self.assertGreater(medicion.seconds, 0)


if __name__ == "__main__":
    unittest.main()
