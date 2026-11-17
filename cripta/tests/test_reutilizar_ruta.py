"""Reutilizar la búsqueda durante el viaje (mejora c del plan, specs/005-niebla-ir-a).

FR-026 exige que cada paso se decida con el conocimiento vigente. Reutilizar
la búsqueda del paso anterior solo es válido si da exactamente la misma
decisión que recalcular. Estas pruebas lo comprueban sobre los mismos 300
mapas sintéticos de las pruebas de la parada anticipada, y comprueban que un
cambio del conocimiento a mitad del viaje obliga a buscar de nuevo.
"""
import unittest

from model.room import Door, Exit, Room, RoomMap
from model.viaje import RutaDelViaje, siguiente_paso
from structures.history import History
from model.game_state import GameState
from structures.mapa_conocido import MapaConocido
from tests.test_parada_anticipada import SEMILLAS, mapa_aleatorio


class _Jugador:
    def __init__(self, room_id):
        self.room_id = room_id


class _Partida:
    def __init__(self, room_id):
        self.player = _Jugador(room_id)


def conocimiento_completo(room_map, ids):
    mapa = MapaConocido(room_map)
    for id_sala in ids:
        mapa.jugador_entro(id_sala)
    return mapa


class TestReutilizarEsIgualQueRecalcular(unittest.TestCase):

    def test_en_300_mapas_el_viaje_es_el_mismo(self):
        """FR-026: paso a paso, la salida con la búsqueda reutilizada es la
        misma que recalculando desde cero."""
        pasos = 0
        for semilla in SEMILLAS:
            room_map, ids = mapa_aleatorio(semilla)
            mapa = conocimiento_completo(room_map, ids)
            destino = ids[0]
            for origen in ids[1:6]:
                partida = _Partida(origen)
                ruta = RutaDelViaje()
                for _ in range(len(ids)):
                    reutilizada = siguiente_paso(partida, mapa, destino, ruta)
                    recalculada = siguiente_paso(partida, mapa, destino)
                    self.assertIs(reutilizada, recalculada,
                                  f"semilla {semilla}, sala {partida.player.room_id}")
                    if reutilizada is None:
                        break
                    partida.player.room_id = reutilizada.destination
                    pasos += 1
        self.assertGreater(pasos, 1000)


class TestUnCambioObligaABuscarDeNuevo(unittest.TestCase):

    def setUp(self):
        """1 -E- 2 -E- 3 por 100 cada una; desvío 2 -N- 4 -E- 5 -S- 3, más caro."""
        self.room_map = RoomMap()
        for id_sala in (1, 2, 3, 4, 5):
            self.room_map.add(Room(id_sala, f"Sala {id_sala}"))
        self.puerta_23 = self._unir(2, 3, "E", "O", 100)
        self._unir(1, 2, "E", "O", 100)
        self._unir(2, 4, "N", "S", 100)
        self._unir(4, 5, "E", "O", 100)
        self._unir(5, 3, "S", "N", 100)
        self.mapa = conocimiento_completo(self.room_map, (1, 2, 3, 4, 5))

    def _unir(self, a, b, ida, vuelta, costo):
        puerta = Door(a, b, cost=costo)
        self.room_map.room(a).add_exit(Exit(ida, b, puerta))
        self.room_map.room(b).add_exit(Exit(vuelta, a, puerta))
        return puerta

    def test_una_puerta_que_se_cierra_a_mitad_del_viaje(self):
        """FR-006, FR-026: después del primer paso, la puerta 2-3 se cierra
        con el jugador presente. El siguiente paso ya no puede ser el de la
        búsqueda guardada: va por el desvío."""
        partida = _Partida(1)
        ruta = RutaDelViaje()
        primero = siguiente_paso(partida, self.mapa, 3, ruta)
        self.assertEqual(primero.destination, 2)
        partida.player.room_id = 2

        self.puerta_23.closed = True
        self.mapa.puerta_cambio(self.puerta_23, 2)

        segundo = siguiente_paso(partida, self.mapa, 3, ruta)

        self.assertEqual(segundo.destination, 4)
        self.assertIs(segundo, siguiente_paso(partida, self.mapa, 3))

    def test_otro_destino_no_reutiliza(self):
        """FR-026: la búsqueda guardada es de un destino."""
        partida = _Partida(1)
        ruta = RutaDelViaje()
        siguiente_paso(partida, self.mapa, 3, ruta)

        self.assertIs(siguiente_paso(partida, self.mapa, 5, ruta),
                      siguiente_paso(partida, self.mapa, 5))


class TestVersionDelConocimiento(unittest.TestCase):
    """FR-026: la versión sube con cada cambio y solo con un cambio."""

    def setUp(self):
        self.room_map = RoomMap()
        for id_sala in (1, 2):
            self.room_map.add(Room(id_sala, f"Sala {id_sala}"))
        self.puerta = Door(1, 2)
        self.room_map.room(1).add_exit(Exit("E", 2, self.puerta))
        self.room_map.room(2).add_exit(Exit("O", 1, self.puerta))
        self.history = History(GameState(seed=1))
        self.mapa = MapaConocido(self.room_map, self.history)

    def test_sube_al_explorar_y_al_cambiar_una_puerta(self):
        antes = self.mapa.version
        self.mapa.jugador_entro(1)
        despues_de_explorar = self.mapa.version
        self.puerta.closed = True
        self.mapa.puerta_cambio(self.puerta, 1)

        self.assertGreater(despues_de_explorar, antes)
        self.assertGreater(self.mapa.version, despues_de_explorar)

    def test_no_sube_si_nada_cambia(self):
        self.mapa.jugador_entro(1)
        antes = self.mapa.version

        self.mapa.jugador_entro(1)
        self.mapa.puerta_cambio(self.puerta, 1)

        self.assertEqual(self.mapa.version, antes)

    def test_sube_al_revertir_y_al_importar(self):
        self.mapa.jugador_entro(1)
        self.history.begin_action()
        self.mapa.jugador_entro(2)
        antes = self.mapa.version

        self.history.undo()
        despues_de_revertir = self.mapa.version
        self.mapa.importar([1], [])

        self.assertGreater(despues_de_revertir, antes)
        self.assertGreater(self.mapa.version, despues_de_revertir)


if __name__ == "__main__":
    unittest.main()
