"""Pruebas de la vista del mapa conocido (specs/003-niebla-ir-a, Historia 7).

Arman la vista desde un mapa conocido llenado a mano y la imprimen con la
vista de consola. No pasan por el bucle de comandos, que todavía no tiene el
mapa conocido de la partida. Cada prueba cita los requisitos que comprueba.
"""
import io
import unittest

from controller.application import KnownExitView, KnownRoomView, known_map_view
from model.room import DEFAULT_EXIT_COST, Door, Exit, Room, RoomMap
from structures.mapa_conocido import ABIERTA, CERRADA, DESCONOCIDA, MapaConocido
from view.console_view import ConsoleView


OPUESTA = (("N", "S"), ("S", "N"), ("E", "O"), ("O", "E"))


def opuesta(direccion):
    for una, otra in OPUESTA:
        if una == direccion:
            return otra
    raise ValueError(direccion)


def conectar(room_map, id_a, id_b, direccion, costo=DEFAULT_EXIT_COST, cerrada=False):
    puerta = Door(id_a, id_b, closed=cerrada, cost=costo)
    room_map.room(id_a).add_exit(Exit(direccion, id_b, puerta))
    room_map.room(id_b).add_exit(Exit(opuesta(direccion), id_a, puerta))
    return puerta


def cripta_de_prueba():
    """3 -O- 1 -E- 2 (costo 40) y 1 -S- 4 (cerrada); 2 -E- 5."""
    room_map = RoomMap()
    for id_sala in (1, 2, 3, 4, 5):
        room_map.add(Room(id_sala, f"Sala {id_sala}"))
    conectar(room_map, 1, 2, "E", costo=40)
    conectar(room_map, 1, 3, "O")
    conectar(room_map, 1, 4, "S", cerrada=True)
    conectar(room_map, 2, 5, "E")
    return room_map


class TestVistaDelMapaConocido(unittest.TestCase):
    """known_map_view arma la vista solo con el conocimiento del jugador."""

    def setUp(self):
        self.room_map = cripta_de_prueba()
        self.mapa = MapaConocido(self.room_map)

    def test_salas_exploradas_ordenadas_por_id_con_sus_salidas(self):
        """FR-018 (Historia 7, escenario 1): id, nombre, dirección, costo,
        estado recordado y destino de cada salida."""
        self.mapa.jugador_entro(2)
        self.mapa.jugador_entro(1)

        vista = known_map_view(self.mapa, self.room_map)

        self.assertEqual([sala.room_id for sala in vista], [1, 2])
        self.assertEqual(vista[0].name, "Sala 1")
        self.assertEqual(
            vista[0].exits,
            [
                KnownExitView("S", 100, CERRADA, None),
                KnownExitView("E", 40, ABIERTA, 2),
                KnownExitView("O", 100, ABIERTA, None),
            ],
        )

    def test_una_avistada_no_muestra_su_id(self):
        """FR-005, FR-018 (Historia 7, escenario 2)."""
        self.mapa.jugador_entro(1)

        salidas = known_map_view(self.mapa, self.room_map)[0].exits
        destinos = [salida.destination for salida in salidas]

        self.assertEqual(destinos, [None, None, None])

    def test_una_desconocida_no_aparece(self):
        """FR-018 (Historia 7, escenario 5): la sala 5 es desconocida."""
        self.mapa.jugador_entro(1)

        vista = known_map_view(self.mapa, self.room_map)

        self.assertEqual([sala.room_id for sala in vista], [1])
        for sala in vista:
            for salida in sala.exits:
                self.assertNotEqual(salida.destination, 5)

    def test_muestra_el_recuerdo_y_no_la_realidad(self):
        """FR-007, FR-012: la puerta 1-4 se abrió lejos del jugador."""
        puerta_14 = self.room_map.room(1).exit_towards("S").door
        self.mapa.jugador_entro(1)
        self.mapa.jugador_entro(2)
        puerta_14.closed = False

        sala_1 = known_map_view(self.mapa, self.room_map)[0]

        self.assertEqual(sala_1.exits[0].door_state, CERRADA)

    def test_puertas_nunca_observadas_figuran_desconocidas(self):
        """FR-008: la puerta 2-5 de una sala explorada con antorcha."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        sala_2 = [sala for sala in known_map_view(self.mapa, self.room_map)
                  if sala.room_id == 2][0]

        salida_este = [salida for salida in sala_2.exits if salida.direction == "E"][0]
        self.assertEqual(salida_este, KnownExitView("E", 100, DESCONOCIDA, None))

    def test_sin_salas_exploradas_la_vista_esta_vacia(self):
        """FR-018: caso vacío."""
        self.assertEqual(known_map_view(self.mapa, self.room_map), [])

    def test_armar_la_vista_no_cambia_el_conocimiento(self):
        """FR-019: ver el mapa no modifica nada."""
        self.mapa.jugador_entro(1)
        antes = self.mapa.exportar()

        known_map_view(self.mapa, self.room_map)

        self.assertEqual(self.mapa.exportar(), antes)


class TestPresentacionDelMapa(unittest.TestCase):
    """ConsoleView.show_known_map imprime lo que arma known_map_view."""

    def mostrar(self, salas):
        salida = io.StringIO()
        ConsoleView(output=salida).show_known_map(salas)
        return salida.getvalue()

    def test_imprime_cada_sala_y_sus_salidas(self):
        """FR-018 (Historia 7, escenario 1)."""
        texto = self.mostrar([
            KnownRoomView(1, "Entrada", [
                KnownExitView("E", 40, ABIERTA, 2),
                KnownExitView("S", 100, CERRADA, None),
            ]),
        ])

        self.assertIn("Sala 1: Entrada", texto)
        self.assertIn("E -> 2 (costo 40) abierta", texto)

    def test_avistada_como_algo_en_esa_direccion(self):
        """FR-005 (Historia 7, escenario 2): sin id ni nombre."""
        texto = self.mostrar([
            KnownRoomView(1, "Entrada", [KnownExitView("S", 100, CERRADA, None)]),
        ])

        self.assertIn("S -> hay algo en esa direccion (costo 100) cerrada", texto)

    def test_sin_salas(self):
        """FR-018: caso vacío."""
        self.assertIn("Todavia no conoces ninguna sala", self.mostrar([]))


if __name__ == "__main__":
    unittest.main()
