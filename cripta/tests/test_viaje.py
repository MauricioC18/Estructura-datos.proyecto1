"""Pruebas de las reglas del viaje «ir a» en el modelo (specs/003-niebla-ir-a).

Usan el motor real para mover al jugador, pero el mapa conocido se actualiza
a mano con jugador_entro, porque los avisos del motor todavía no existen. El
bucle completo del viaje (controlador y bitácora) se prueba aparte, cuando
exista. Cada prueba cita en su docstring los requisitos que comprueba.
"""
import unittest

from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.player import Player
from model.room import DEFAULT_EXIT_COST, Door, Exit, Room, RoomMap
from model.viaje import (
    CONTENIDO_NO_DISPONIBLE,
    DANO,
    ENEMIGOS,
    LLEGADA,
    ORDEN_DE_LOS_MOTIVOS,
    PARTIDA_TERMINADA,
    SIN_RUTA,
    hay_enemigos_vivos_en,
    motivos_de_parada,
    siguiente_paso,
    validar_orden,
)
from structures.mapa_conocido import MapaConocido


OPUESTA = (("N", "S"), ("S", "N"), ("E", "O"), ("O", "E"))


def opuesta(direccion):
    for una, otra in OPUESTA:
        if una == direccion:
            return otra
    raise ValueError(direccion)


def mapa_de_salas(*ids):
    room_map = RoomMap()
    for id_sala in ids:
        sala = Room(id_sala, f"Sala {id_sala}")
        sala.content_loaded = True
        room_map.add(sala)
    return room_map


def conectar(room_map, id_a, id_b, direccion, costo=DEFAULT_EXIT_COST, cerrada=False):
    puerta = Door(id_a, id_b, closed=cerrada, cost=costo)
    room_map.room(id_a).add_exit(Exit(direccion, id_b, puerta))
    room_map.room(id_b).add_exit(Exit(opuesta(direccion), id_a, puerta))
    return puerta


def jugador(sala=1, vida=100):
    return Player(
        actor_id="p-1", name="Heroe", max_health=vida, attack=6, defense=10,
        speed=100, room_id=sala,
    )


def guardian(sala, actor_id="e-1", ataque=1):
    return Enemy(
        actor_id=actor_id, name="Guardia", max_health=10, attack=ataque,
        defense=0, speed=100, room_id=sala, behavior=Enemy.GUARDIAN,
    )


def partida(room_map, enemigos=None, sala=1):
    return Game(GameState(seed=7), jugador(sala), enemigos, room_map=room_map)


def explorar(mapa, *ids):
    for id_sala in ids:
        mapa.jugador_entro(id_sala)


class TestValidarOrden(unittest.TestCase):
    """FR-022: qué órdenes se aceptan (Historia 4, escenario 1 y casos borde)."""

    def setUp(self):
        self.room_map = mapa_de_salas(1, 2, 3)
        conectar(self.room_map, 1, 2, "E")
        conectar(self.room_map, 2, 3, "E")
        self.game = partida(self.room_map)
        self.mapa = MapaConocido(self.room_map)
        explorar(self.mapa, 1)

    def test_hacia_una_sala_no_explorada_se_rechaza_sin_consumir_tiempo(self):
        """FR-022 (Apéndice B): se rechaza y el reloj no cambia."""
        reloj = self.game.state.clock

        resultado = validar_orden(self.game, self.mapa, 2)

        self.assertFalse(resultado.accepted)
        self.assertEqual(self.game.state.clock, reloj)
        self.assertEqual(self.game.player.room_id, 1)

    def test_un_id_inexistente_da_el_mismo_mensaje(self):
        """FR-022: no se revela si la sala existe."""
        no_explorada = validar_orden(self.game, self.mapa, 3).message
        inexistente = validar_orden(self.game, self.mapa, 999).message

        self.assertEqual(no_explorada.replace("3", "#"), inexistente.replace("999", "#"))

    def test_hacia_la_sala_actual_se_rechaza(self):
        """FR-022 (supuesto del grupo)."""
        self.assertFalse(validar_orden(self.game, self.mapa, 1).accepted)

    def test_hacia_una_sala_explorada_se_acepta(self):
        """FR-022."""
        explorar(self.mapa, 2)

        self.assertTrue(validar_orden(self.game, self.mapa, 2).accepted)

    def test_con_la_partida_terminada_se_rechaza(self):
        """FR-022: como cualquier acción, con la partida terminada no hay viaje."""
        explorar(self.mapa, 2)
        self.game.result = "derrota"

        self.assertFalse(validar_orden(self.game, self.mapa, 2).accepted)


class TestSiguientePaso(unittest.TestCase):
    """Historia 4: la ruta usa solo lo que el jugador conoce."""

    def test_sigue_la_ruta_de_menor_costo_y_no_la_de_menos_salas(self):
        """FR-023 (Historia 4, escenario 2): directo a 4 cuesta 500; por 2 y 3, 150."""
        room_map = mapa_de_salas(1, 2, 3, 4)
        conectar(room_map, 1, 4, "N", costo=500)
        conectar(room_map, 1, 2, "E", costo=50)
        conectar(room_map, 2, 3, "E", costo=50)
        conectar(room_map, 3, 4, "S", costo=50)
        game = partida(room_map)
        mapa = MapaConocido(room_map)
        explorar(mapa, 1, 2, 3, 4)

        paso = siguiente_paso(game, mapa, 4)

        self.assertEqual(paso.direction, "E")
        self.assertEqual(paso.destination, 2)

    def test_desempate_hacia_la_vecina_de_menor_id(self):
        """FR-024 (Historia 4, escenario 3): por 3 (al N) y por 2 (al E) cuesta
        lo mismo; va a 2 aunque N se recorra primero."""
        room_map = mapa_de_salas(1, 2, 3, 4)
        conectar(room_map, 1, 3, "N")
        conectar(room_map, 1, 2, "E")
        conectar(room_map, 3, 4, "E")
        conectar(room_map, 2, 4, "N")
        game = partida(room_map)
        mapa = MapaConocido(room_map)
        explorar(mapa, 1, 2, 3, 4)

        self.assertEqual(siguiente_paso(game, mapa, 4).destination, 2)

    def test_no_usa_una_puerta_que_recuerda_cerrada(self):
        """FR-023, FR-027 (Historia 4, escenario 4): no abre puertas aunque
        haya llave; la única ruta pasa por una puerta cerrada, así que no hay paso."""
        room_map = mapa_de_salas(1, 2)
        conectar(room_map, 1, 2, "E", cerrada=True)
        game = partida(room_map)
        mapa = MapaConocido(room_map)
        explorar(mapa, 2, 1)

        self.assertIsNone(siguiente_paso(game, mapa, 2))

    def test_toma_el_desvio_si_la_corta_se_recuerda_cerrada(self):
        """FR-023, FR-027: con la puerta corta cerrada, va por la larga."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 3, "E", cerrada=True)
        conectar(room_map, 1, 2, "N")
        conectar(room_map, 2, 3, "O")
        game = partida(room_map)
        mapa = MapaConocido(room_map)
        explorar(mapa, 3, 2, 1)

        self.assertEqual(siguiente_paso(game, mapa, 3).destination, 2)

    def test_usa_el_recuerdo_y_no_la_realidad(self):
        """FR-012: la puerta 2-3 está abierta en realidad, pero el jugador la
        recuerda cerrada; no hay ruta conocida."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 2, "E")
        puerta_23 = conectar(room_map, 2, 3, "E", cerrada=True)
        game = partida(room_map)
        mapa = MapaConocido(room_map)
        explorar(mapa, 3, 2, 1)
        puerta_23.closed = False

        self.assertIsNone(siguiente_paso(game, mapa, 3))

    def test_no_pasa_por_salas_no_exploradas(self):
        """FR-023: 2 es avistada; aunque la ruta exista, no se conoce."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 2, "E")
        conectar(room_map, 2, 3, "E")
        game = partida(room_map)
        mapa = MapaConocido(room_map)
        mapa.importar([1, 3], [])
        explorar(mapa, 1)

        self.assertIsNone(siguiente_paso(game, mapa, 3))

    def test_el_calculo_no_modifica_nada(self):
        """FR-026: calcular el paso no mueve al jugador ni avanza el reloj."""
        room_map = mapa_de_salas(1, 2)
        conectar(room_map, 1, 2, "E")
        game = partida(room_map)
        mapa = MapaConocido(room_map)
        explorar(mapa, 2, 1)
        reloj = game.state.clock

        siguiente_paso(game, mapa, 2)

        self.assertEqual(game.state.clock, reloj)
        self.assertEqual(game.player.room_id, 1)

    def test_recalcula_con_el_recuerdo_corregido(self):
        """FR-006, FR-026, FR-028 (Apéndice B, a nivel de modelo): el mapa
        recuerda abierta la puerta 2-3, que en realidad está cerrada. Al llegar
        a 2 el jugador la observa, el siguiente cálculo ya no tiene ruta y el
        reloj queda donde lo dejó el paso. El aviso del motor se simula."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 2, "E")
        puerta_23 = conectar(room_map, 2, 3, "E")
        game = partida(room_map)
        mapa = MapaConocido(room_map)
        explorar(mapa, 3, 2, 1)
        puerta_23.closed = True

        paso = siguiente_paso(game, mapa, 3)
        self.assertEqual(paso.destination, 2)
        game.move(paso.direction)
        mapa.jugador_entro(game.player.room_id)
        reloj_tras_el_paso = game.state.clock

        self.assertIsNone(siguiente_paso(game, mapa, 3))
        motivos = motivos_de_parada(game, 3, game.player.health, False, sin_ruta=True)
        self.assertEqual(motivos, [SIN_RUTA])
        self.assertEqual(game.state.clock, reloj_tras_el_paso)


class TestEnemigosAlEntrar(unittest.TestCase):
    """FR-028 (b): enemigos vivos, activos o dormidos, en la sala a la que se entra."""

    def test_cuenta_los_dormidos(self):
        """FR-028 (b)."""
        room_map = mapa_de_salas(1, 2)
        dormido = guardian(2)
        game = partida(room_map, [dormido])

        self.assertFalse(dormido.is_active)
        self.assertTrue(hay_enemigos_vivos_en(game, 2))

    def test_no_cuenta_los_muertos(self):
        """FR-028 (b): un muerto no detiene el viaje."""
        room_map = mapa_de_salas(1, 2)
        muerto = guardian(2)
        muerto.health = 0
        game = partida(room_map, [muerto])

        self.assertFalse(hay_enemigos_vivos_en(game, 2))

    def test_sala_vacia(self):
        """FR-028 (b)."""
        game = partida(mapa_de_salas(1, 2))

        self.assertFalse(hay_enemigos_vivos_en(game, 2))

    def test_entrar_a_una_sala_con_dormidos_los_activa_y_detiene(self):
        """FR-025, FR-028 (b) (Historia 5, escenario 2, Apéndice B): el paso es
        un movimiento ordinario, así que los activa según P1 §2.4."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 2, "E")
        conectar(room_map, 2, 3, "E")
        dormido = guardian(2)
        game = partida(room_map, [dormido])
        mapa = MapaConocido(room_map)
        explorar(mapa, 3, 2, 1)

        paso = siguiente_paso(game, mapa, 3)
        enemigos = hay_enemigos_vivos_en(game, paso.destination)
        vida = game.player.health
        game.move(paso.direction)

        self.assertTrue(dormido.is_active)
        self.assertIn(ENEMIGOS, motivos_de_parada(game, 3, vida, enemigos))


class TestMotivosDeParada(unittest.TestCase):
    """FR-028, FR-029, FR-030: por qué se detiene el viaje y en qué orden."""

    def setUp(self):
        self.room_map = mapa_de_salas(1, 2, 3)
        conectar(self.room_map, 1, 2, "E")
        conectar(self.room_map, 2, 3, "E")
        self.game = partida(self.room_map)

    def test_sin_motivos_el_viaje_sigue(self):
        """FR-028: a mitad de camino, sin daño ni enemigos, la lista está vacía."""
        self.game.move("E")

        self.assertEqual(motivos_de_parada(self.game, 3, self.game.player.health, False), [])

    def test_llegada(self):
        """FR-028 (a) (Historia 5, escenario 4)."""
        self.game.move("E")

        self.assertEqual(motivos_de_parada(self.game, 2, self.game.player.health, False),
                         [LLEGADA])

    def test_dano(self):
        """FR-028 (c) (Historia 5, escenario 3): cualquier pérdida de vida."""
        vida = self.game.player.health
        self.game.move("E")
        self.game.player.health = vida - 1

        self.assertEqual(motivos_de_parada(self.game, 3, vida, False), [DANO])

    def test_partida_terminada(self):
        """FR-028 (e)."""
        self.game.result = "derrota"

        self.assertIn(PARTIDA_TERMINADA,
                      motivos_de_parada(self.game, 3, self.game.player.health, False))

    def test_contenido_no_disponible_no_cuenta_llegada(self):
        """FR-028 (f): el paso no se dio."""
        motivos = motivos_de_parada(self.game, 1, self.game.player.health, True,
                                    contenido_no_disponible=True)

        self.assertEqual(motivos, [CONTENIDO_NO_DISPONIBLE])

    def test_varios_motivos_en_el_orden_de_fr_028(self):
        """FR-029 (Historia 5, escenario 6): llega a un destino con enemigos
        y recibe daño: se informan todos, en orden."""
        vida = self.game.player.health
        self.game.move("E")
        self.game.player.health = vida - 3

        motivos = motivos_de_parada(self.game, 2, vida, True)

        self.assertEqual(motivos, [LLEGADA, ENEMIGOS, DANO])

    def test_un_enemigo_que_llega_sin_atacar_no_es_motivo(self):
        """FR-028 (b), caso borde: los enemigos se toman de la sala al entrar,
        no del estado después del ciclo."""
        self.game.move("E")
        self.game.enemies.append(guardian(2))

        self.assertEqual(motivos_de_parada(self.game, 3, self.game.player.health, False), [])

    def test_partir_de_una_sala_con_enemigos_no_es_motivo(self):
        """FR-030: lo que importa es la sala a la que se entra."""
        self.game.enemies.append(guardian(1))
        enemigos = hay_enemigos_vivos_en(self.game, 2)
        self.game.move("E")

        self.assertEqual(motivos_de_parada(self.game, 3, self.game.player.health, enemigos), [])

    def test_el_orden_es_el_de_fr_028(self):
        """FR-029."""
        self.assertEqual(
            ORDEN_DE_LOS_MOTIVOS,
            (LLEGADA, ENEMIGOS, DANO, SIN_RUTA, PARTIDA_TERMINADA, CONTENIDO_NO_DISPONIBLE),
        )


if __name__ == "__main__":
    unittest.main()
