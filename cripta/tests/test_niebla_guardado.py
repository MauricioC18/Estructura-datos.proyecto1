"""Guardar y cargar el conocimiento del jugador (specs/003-niebla-ir-a, T040).

La partida se arma como en test_niebla.py, se guarda con el adaptador de
Carlos y se vuelve a armar con build_saved_game, que es lo que hace la
aplicación al cargar. Cada prueba cita en su docstring los requisitos que
comprueba.
"""
import os
import tempfile
import unittest

from adapters.almacen_partida import cargar_partida, guardar_partida
from controller.application import build_saved_game
from structures.mapa_conocido import ABIERTA, MapaConocido
from tests.test_ir_a import pergamino
from tests.test_niebla import (
    antorcha,
    esperar_hasta,
    llave,
    partida_con_niebla,
    pasillo_con_puerta_que_se_cierra,
    seleccionar_antorcha,
)


class TestGuardarYCargar(unittest.TestCase):
    """T040 — Historia 6, escenario 3."""

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.directorio.name, "partida.bin")

    def tearDown(self):
        self.directorio.cleanup()

    def partida_jugada(self):
        room_map, puerta = pasillo_con_puerta_que_se_cierra()
        game, mapa = partida_con_niebla(
            room_map, objetos=[llave(), antorcha(), pergamino()]
        )
        game.move("E")
        game.open_door("E")
        game.move("O")
        esperar_hasta(game, lambda: puerta.closed)
        return game, mapa, puerta

    def test_cargar_restaura_el_conocimiento_identico(self):
        """FR-014, SC-005: mismas salas exploradas, en el mismo orden, y el
        mismo recuerdo de cada puerta, incluida una recordada abierta que en
        realidad está cerrada."""
        game, mapa, _ = self.partida_jugada()
        guardar_partida(game, self.ruta)

        cargada = build_saved_game(cargar_partida(self.ruta))

        self.assertIsInstance(cargada.known_map, MapaConocido)
        self.assertEqual(cargada.known_map.exportar(), mapa.exportar())
        puerta_cargada = cargada.room_map.room(2).exit_towards("E").door
        self.assertTrue(puerta_cargada.closed)
        self.assertEqual(cargada.known_map.puerta_recordada(puerta_cargada), ABIERTA)
        for id_sala in (1, 2, 3):
            self.assertEqual(cargada.known_map.estado_de_sala(id_sala), mapa.estado_de_sala(id_sala))

    def test_lo_explorado_despues_de_cargar_se_revierte(self):
        """FR-014, FR-015: la partida cargada anota en su historial lo que el
        jugador explora desde ahí, y el pergamino lo revierte."""
        game, _, _ = self.partida_jugada()
        guardar_partida(game, self.ruta)
        cargada = build_saved_game(cargar_partida(self.ruta))
        mapa = cargada.known_map
        seleccionar_antorcha(cargada.player.inventory)
        self.assertTrue(cargada.use_item().accepted)
        antes = mapa.exportar()
        cargada.move("E")
        self.assertNotEqual(mapa.exportar(), antes)

        self.assertTrue(cargada.rewind().accepted)

        self.assertEqual(mapa.exportar(), antes)


if __name__ == "__main__":
    unittest.main()
