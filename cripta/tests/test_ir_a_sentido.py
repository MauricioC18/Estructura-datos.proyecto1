"""«ir a» respeta el sentido de las salidas (specs/003-niebla-ir-a, T049).

Escenarios 7 y 8 de la Historia 4 y la aclaración del 2026-11-17: una salida
puede existir en un solo sentido, y la ruta solo puede atravesarla en ese
sentido. El conocimiento sale de los avisos del motor real: el jugador recorre
las salas antes de pedir el viaje. Cada prueba cita en su docstring los
requisitos que comprueba.
"""
import unittest

from controller.game_controller import GameController
from model.room import Door, Exit
from model.viaje import LLEGADA, SIN_RUTA
from tests.test_ir_a import conectar, mapa_de_salas
from tests.test_niebla import partida_con_niebla


def salida_de_un_sentido(room_map, id_a, id_b, direccion, costo=1):
    """Una salida de id_a a id_b sin vuelta: la sala id_b no la declara."""
    puerta = Door(id_a, id_b, cost=costo)
    room_map.room(id_a).add_exit(Exit(direccion, id_b, puerta))
    return puerta


class TestSentidoDeLasSalidas(unittest.TestCase):

    def test_usa_la_salida_directa_de_un_solo_sentido(self):
        """FR-023, FR-024 (Historia 4, escenario 7): con 1→3, 3→2 y 2→1, todas
        de un solo sentido y de costo 1, desde la sala 1 «ir a 3» da un solo
        paso de costo 1 por la salida directa, y no informa que no hay ruta."""
        room_map = mapa_de_salas(1, 2, 3)
        salida_de_un_sentido(room_map, 1, 3, "E")
        salida_de_un_sentido(room_map, 3, 2, "S")
        salida_de_un_sentido(room_map, 2, 1, "O")
        game, _ = partida_con_niebla(room_map)
        for direccion in ("E", "S", "O"):
            self.assertTrue(game.move(direccion).accepted)
        self.assertEqual(game.player.room_id, 1)
        reloj = game.state.clock

        resultado = GameController(game).travel(3)

        self.assertTrue(resultado.accepted)
        self.assertEqual(resultado.steps, 1)
        self.assertEqual(resultado.reasons, [LLEGADA])
        self.assertEqual(game.player.room_id, 3)
        self.assertEqual(game.state.clock - reloj, 1)

    def test_no_recorre_una_salida_al_reves(self):
        """FR-023 (Historia 4, escenario 8): la salida 3→1 no tiene vuelta, así
        que no sirve para ir de 1 a 3; el viaje sigue la ruta conocida que
        respeta el sentido, 1→2→3, y llega en dos pasos."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 2, "E", costo=1)
        conectar(room_map, 2, 3, "E", costo=1)
        salida_de_un_sentido(room_map, 3, 1, "S")
        game, _ = partida_con_niebla(room_map)
        for direccion in ("E", "E", "S"):
            self.assertTrue(game.move(direccion).accepted)
        self.assertEqual(game.player.room_id, 1)

        resultado = GameController(game).travel(3)

        self.assertTrue(resultado.accepted)
        self.assertEqual(resultado.steps, 2)
        self.assertEqual(resultado.reasons, [LLEGADA])
        self.assertEqual(game.player.room_id, 3)

    def test_sin_ruta_que_respete_el_sentido_no_viaja(self):
        """FR-023, FR-028 (Historia 4, escenario 8): si la única conexión es
        una salida de un solo sentido en contra, no hay ruta conocida, el
        viaje no da ningún paso y no consume tiempo."""
        room_map = mapa_de_salas(1, 2)
        salida_de_un_sentido(room_map, 1, 2, "E")
        game, mapa = partida_con_niebla(room_map)
        self.assertTrue(game.move("E").accepted)
        self.assertTrue(mapa.esta_explorada(1))
        reloj = game.state.clock

        resultado = GameController(game).travel(1)

        self.assertTrue(resultado.accepted)
        self.assertEqual(resultado.steps, 0)
        self.assertEqual(resultado.reasons, [SIN_RUTA])
        self.assertEqual(game.player.room_id, 2)
        self.assertEqual(game.state.clock, reloj)


if __name__ == "__main__":
    unittest.main()
