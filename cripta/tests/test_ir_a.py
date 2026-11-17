"""Pruebas del viaje automático «ir a» de punta a punta (specs/003-niebla-ir-a).

Corren el bucle del controlador sobre el motor real. Como el motor todavía no
avisa al mapa conocido, el conocimiento se arma a mano antes del viaje; por eso
el caso de la puerta recordada abierta que en realidad está cerrada, que
necesita que el motor avise al entrar, queda para cuando existan esos avisos
(T029). Cada prueba cita en su docstring los requisitos que comprueba.
"""
import os
import tempfile
import unittest

from adapters.fuente_datos import ErrorFuenteDatos
from controller.game_controller import GameController
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.item import Item
from model.player import Player
from model.room import DEFAULT_EXIT_COST, Door, Exit, Room, RoomMap
from model.trap import Trap
from model.viaje import CONTENIDO_NO_DISPONIBLE, DANO, ENEMIGOS, LLEGADA, PARTIDA_TERMINADA, SIN_RUTA
from replay.replay import replay_commands
from replay.replay_log import ReplayHeader, ReplayLogWriter, read_replay_log
from structures.history import History, ReversibleEventQueue
from structures.inventory import Inventory
from structures.mapa_conocido import ABIERTA, MapaConocido
from structures.trail import PlayerTrail


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


def conectar(room_map, id_a, id_b, direccion, costo=DEFAULT_EXIT_COST, cerrada=False,
             llave=None):
    puerta = Door(id_a, id_b, closed=cerrada, key_id=llave, cost=costo)
    room_map.room(id_a).add_exit(Exit(direccion, id_b, puerta))
    room_map.room(id_b).add_exit(Exit(opuesta(direccion), id_a, puerta))
    return puerta


def guardian(sala, actor_id="e-1", ataque=3):
    return Enemy(
        actor_id=actor_id, name="Guardia", max_health=10, attack=ataque,
        defense=0, speed=100, room_id=sala, behavior=Enemy.GUARDIAN,
    )


def pergamino(numero=1):
    return Item(f"o-{numero}", "itm_pergamino", "Pergamino", Item.REWIND_SCROLL, 1, 1)


def armar_partida(room_map, enemigos=None, vida=100, sala_de_salida=None, seed=11):
    """Partida completa como la arma la aplicación: historial reversible,
    inventario, rastro y agenda reversible."""
    state = GameState(seed=seed)
    history = History(state)
    jugador = Player(
        actor_id="p-1", name="Heroe", max_health=vida, attack=6, defense=0,
        speed=100, room_id=1,
    )
    jugador.inventory = Inventory(10, history)
    game = Game(
        state,
        jugador,
        enemigos,
        room_map=room_map,
        exit_room_id=sala_de_salida,
        trail=PlayerTrail(history),
        history=history,
        event_queue=ReversibleEventQueue(history),
    )
    mapa = MapaConocido(room_map, history)
    return game, mapa


def explorar(mapa, *ids):
    """Simula que el jugador ya pasó por esas salas antes del viaje."""
    for id_sala in ids:
        mapa.jugador_entro(id_sala)


class BitacoraDePrueba:
    """Lo mismo que ReplayLogWriter guarda, pero en memoria."""

    def __init__(self):
        self.lineas = []

    def append(self, command):
        self.lineas.append(command.to_text())

    def comment(self, text):
        self.lineas.append(f"# {text}")


class ControladorQueAnota(GameController):
    """Anota, justo antes de cada paso, por qué puerta sale y cómo la recordaba."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cruces = []

    def execute(self, command):
        sala = self.game.room_map.room(self.game.player.room_id)
        puerta = sala.exit_towards(command.argument).door
        self.cruces.append((puerta, self.known_map.puerta_recordada(puerta), puerta.closed))
        return super().execute(command)


class RepositorioSinContenido:
    """Un repositorio cuya carga de contenido falla, como al agotar el presupuesto."""

    def cargar_contenido_de_sala(self, sala):
        raise ErrorFuenteDatos("cargar el contenido de la sala", "se agotó el presupuesto")

    def despues_de_accion(self, id_sala):
        pass


def ruta_mas_barata_contra_mas_corta():
    """Directo de 1 a 4 cuesta 500; por 2 y 3 cuesta 150."""
    room_map = mapa_de_salas(1, 2, 3, 4)
    conectar(room_map, 1, 4, "N", costo=500)
    conectar(room_map, 1, 2, "E", costo=50)
    conectar(room_map, 2, 3, "E", costo=50)
    conectar(room_map, 3, 4, "S", costo=50)
    return room_map


def pasillo(*costos):
    """Salas 1, 2, ... en línea hacia el este, con los costos dados."""
    room_map = mapa_de_salas(*range(1, len(costos) + 2))
    for indice in range(len(costos)):
        conectar(room_map, indice + 1, indice + 2, "E", costo=costos[indice])
    return room_map


class TestOrden(unittest.TestCase):
    """Historia 4, escenario 1, y los rechazos de FR-022 y FR-038."""

    def setUp(self):
        self.room_map = pasillo(100, 100)
        self.game, self.mapa = armar_partida(self.room_map)
        self.bitacora = BitacoraDePrueba()
        self.controller = GameController(self.game, self.bitacora, known_map=self.mapa)
        explorar(self.mapa, 1)

    def test_hacia_una_sala_no_explorada_se_rechaza_sin_tiempo_ni_bitacora(self):
        """FR-022 (Apéndice B): se rechaza, no consume tiempo y no se registra."""
        reloj = self.game.state.clock

        resultado = self.controller.travel(2)

        self.assertFalse(resultado.accepted)
        self.assertEqual(self.game.state.clock, reloj)
        self.assertEqual(self.game.player.room_id, 1)
        self.assertEqual(self.bitacora.lineas, [])

    def test_un_id_inexistente_da_el_mismo_mensaje(self):
        """FR-022: no se revela si la sala existe."""
        no_explorada = self.controller.travel(3).message
        inexistente = self.controller.travel(999).message

        self.assertEqual(no_explorada.replace("3", "#"), inexistente.replace("999", "#"))

    def test_hacia_la_sala_actual_se_rechaza(self):
        """FR-022."""
        self.assertFalse(self.controller.travel(1).accepted)
        self.assertEqual(self.bitacora.lineas, [])

    def test_con_la_partida_terminada_se_rechaza(self):
        """FR-038."""
        explorar(self.mapa, 2)
        self.game.result = "derrota"

        self.assertFalse(self.controller.travel(2).accepted)
        self.assertEqual(self.bitacora.lineas, [])

    def test_sin_mapa_conocido_no_hay_viaje(self):
        """FR-012: el viaje solo usa el conocimiento del jugador; sin él no viaja."""
        controller = GameController(self.game)

        resultado = controller.travel(2)

        self.assertFalse(resultado.accepted)
        self.assertEqual(self.game.player.room_id, 1)


class TestRuta(unittest.TestCase):
    """Historia 4: el viaje sigue la ruta conocida de menor costo."""

    def test_sigue_la_de_menor_costo_y_no_la_de_menos_salas(self):
        """FR-023 (Historia 4, escenario 2)."""
        room_map = ruta_mas_barata_contra_mas_corta()
        game, mapa = armar_partida(room_map)
        bitacora = BitacoraDePrueba()
        explorar(mapa, 1, 2, 3, 4)

        resultado = GameController(game, bitacora, known_map=mapa).travel(4)

        self.assertEqual(bitacora.lineas, ["# ir a 4", "mover E", "mover E", "mover S"])
        self.assertEqual(resultado.steps, 3)
        self.assertEqual(resultado.reasons, [LLEGADA])
        self.assertEqual(game.player.room_id, 4)

    def test_desempate_hacia_la_vecina_de_menor_id(self):
        """FR-024 (Historia 4, escenario 3): por 3 (al N) y por 2 (al E) cuesta
        lo mismo; el primer paso va a 2."""
        room_map = mapa_de_salas(1, 2, 3, 4)
        conectar(room_map, 1, 3, "N")
        conectar(room_map, 1, 2, "E")
        conectar(room_map, 3, 4, "E")
        conectar(room_map, 2, 4, "N")
        game, mapa = armar_partida(room_map)
        bitacora = BitacoraDePrueba()
        explorar(mapa, 1, 2, 3, 4)

        GameController(game, bitacora, known_map=mapa).travel(4)

        self.assertEqual(bitacora.lineas[1], "mover E")

    def test_no_abre_una_puerta_aunque_tenga_la_llave(self):
        """FR-027 (Historia 4, escenario 4)."""
        room_map = mapa_de_salas(1, 2)
        puerta = conectar(room_map, 1, 2, "E", cerrada=True, llave="itm_llave")
        game, mapa = armar_partida(room_map)
        game.player.inventory.pick_up(Item("o-1", "itm_llave", "Llave", Item.KEY, 1, 1))
        explorar(mapa, 2, 1)
        reloj = game.state.clock

        resultado = GameController(game, known_map=mapa).travel(2)

        self.assertEqual(resultado.reasons, [SIN_RUTA])
        self.assertEqual(resultado.steps, 0)
        self.assertTrue(puerta.closed)
        self.assertEqual(game.state.clock, reloj)

    def test_cada_paso_consume_su_intervalo_y_corren_los_eventos(self):
        """FR-025, FR-030 (Historia 4, escenario 5): con velocidad 100, dos
        pasos de costo 50 y 250 dejan el reloj en 300. El guardián de la sala
        de partida sigue tomando turnos entre paso y paso, y partir de su sala
        no detiene el viaje."""
        room_map = pasillo(50, 250)
        quieto = guardian(1)
        game, mapa = armar_partida(room_map, [quieto])
        explorar(mapa, 1, 2, 3)
        procesados = game.events_processed

        resultado = GameController(game, known_map=mapa).travel(3)

        self.assertEqual(resultado.reasons, [LLEGADA])
        self.assertEqual(game.state.clock, 300)
        self.assertGreater(game.events_processed - procesados, resultado.steps)
        self.assertEqual(game.player_actions, 2)

    def test_nunca_cruza_una_puerta_que_no_recordaba_abierta(self):
        """SC-008, FR-023, FR-027: en un viaje de varios pasos, cada puerta
        cruzada se recordaba abierta justo antes del paso y ninguna puerta
        pasó de cerrada a abierta por el viaje."""
        room_map = ruta_mas_barata_contra_mas_corta()
        cerrada = conectar(room_map, 1, 4, "O", costo=1, cerrada=True)
        game, mapa = armar_partida(room_map)
        explorar(mapa, 1, 2, 3, 4)
        controller = ControladorQueAnota(game, known_map=mapa)

        controller.travel(4)

        self.assertEqual(len(controller.cruces), 3)
        for puerta, recordada, estaba_cerrada in controller.cruces:
            self.assertEqual(recordada, ABIERTA)
            self.assertFalse(estaba_cerrada)
        self.assertTrue(cerrada.closed)


class TestBitacora(unittest.TestCase):
    """Historia 4, escenario 6: la bitácora del viaje."""

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.directorio.name, "partida.log")

    def tearDown(self):
        self.directorio.cleanup()

    def test_pasos_como_movimientos_y_la_orden_como_comentario(self):
        """FR-031, SC-003: la bitácora real tiene el comentario y un mover por
        paso, y reproducirla da la misma partida."""
        room_map = ruta_mas_barata_contra_mas_corta()
        game, mapa = armar_partida(room_map)
        explorar(mapa, 1, 2, 3, 4)
        cabecera = ReplayHeader("cripta-de-prueba", "v1", "c1", 11)

        with ReplayLogWriter(self.ruta, cabecera) as log:
            GameController(game, log, known_map=mapa).travel(4)

        with open(self.ruta, encoding="utf-8") as archivo:
            texto = archivo.read()
        self.assertIn("\n# ir a 4\nmover E\nmover E\nmover S\n", texto)

        log = read_replay_log(self.ruta)
        copia, _ = armar_partida(ruta_mas_barata_contra_mas_corta())
        replay_commands(GameController(copia), log.commands)

        self.assertEqual(copia.player.room_id, game.player.room_id)
        self.assertEqual(copia.state.clock, game.state.clock)
        self.assertEqual(copia.player_actions, game.player_actions)


class TestParadas(unittest.TestCase):
    """Historia 5: el viaje se detiene cuando algo importa."""

    def test_entra_a_una_sala_con_enemigos_dormidos(self):
        """FR-025, FR-028 (b) (Historia 5, escenario 2, Apéndice B): se activan
        según P1 §2.4 y el viaje se detiene."""
        room_map = pasillo(100, 100)
        dormido = guardian(2)
        game, mapa = armar_partida(room_map, [dormido])
        explorar(mapa, 1, 2, 3)

        resultado = GameController(game, known_map=mapa).travel(3)

        self.assertEqual(resultado.steps, 1)
        self.assertIn(ENEMIGOS, resultado.reasons)
        self.assertTrue(dormido.is_active)
        self.assertEqual(game.player.room_id, 2)

    def test_pergamino_despues_de_un_viaje_revierte_solo_el_ultimo_paso(self):
        """FR-032 (Historia 5, escenario 7, Apéndice B): vuelve a la sala y al
        reloj de antes del último paso, y no hay ningún paso más."""
        room_map = pasillo(100, 100)
        game, mapa = armar_partida(room_map)
        game.player.inventory.pick_up(pergamino())
        explorar(mapa, 1, 2, 3)
        controller = GameController(game, known_map=mapa)

        resultado = controller.travel(3)
        self.assertEqual((resultado.steps, game.player.room_id, game.state.clock), (2, 3, 200))

        self.assertTrue(game.rewind().accepted)

        self.assertEqual(game.player.room_id, 2)
        self.assertEqual(game.state.clock, 100)
        self.assertEqual(game.player_actions, 1)

    def test_llegada(self):
        """FR-028 (a) (Historia 5, escenario 4)."""
        room_map = pasillo(100)
        game, mapa = armar_partida(room_map)
        explorar(mapa, 1, 2)

        resultado = GameController(game, known_map=mapa).travel(2)

        self.assertEqual(resultado.reasons, [LLEGADA])

    def test_dano_por_veneno(self):
        """FR-028 (c) (Historia 5, escenario 3): el pulso de veneno de t=80 cae
        durante el primer paso."""
        room_map = pasillo(100, 100, 100)
        game, mapa = armar_partida(room_map)
        explorar(mapa, 1, 2, 3, 4)
        game.apply_poison(game.player, 1)

        resultado = GameController(game, known_map=mapa).travel(4)

        self.assertEqual(resultado.steps, 1)
        self.assertEqual(resultado.reasons, [DANO])

    def test_dano_por_trampa(self):
        """FR-028 (c) (Historia 5, escenario 3)."""
        room_map = pasillo(100, 100)
        room_map.room(2).traps.append(Trap("t-1", "trp_dardos", "Dardos", 2, 300, 2))
        game, mapa = armar_partida(room_map)
        explorar(mapa, 1, 2, 3)

        resultado = GameController(game, known_map=mapa).travel(3)

        self.assertEqual((resultado.steps, resultado.reasons), (1, [DANO]))

    def test_llegada_con_enemigos_y_ataque_informa_todo_en_orden(self):
        """FR-028, FR-029 (Historia 5, escenarios 3, 5 y 6): el destino tiene un
        guardián que se activa al entrar y ataca antes de la siguiente
        decisión del jugador."""
        room_map = pasillo(100)
        game, mapa = armar_partida(room_map, [guardian(2)])
        explorar(mapa, 1, 2)

        resultado = GameController(game, known_map=mapa).travel(2)

        self.assertEqual(resultado.reasons, [LLEGADA, ENEMIGOS, DANO])

    def test_la_partida_termina_a_mitad_del_viaje(self):
        """FR-028 (c) y (e): una trampa mata al jugador en el primer paso."""
        room_map = pasillo(100, 100)
        room_map.room(2).traps.append(Trap("t-1", "trp_pinchos", "Pinchos", 1000, 300, 2))
        game, mapa = armar_partida(room_map, vida=5)
        explorar(mapa, 1, 2, 3)

        resultado = GameController(game, known_map=mapa).travel(3)

        self.assertEqual(resultado.reasons, [DANO, PARTIDA_TERMINADA])
        self.assertTrue(game.is_over)

    def test_victoria_a_mitad_del_viaje(self):
        """FR-025, FR-028 (e): el paso es un movimiento ordinario, así que
        entrar a la sala de salida gana la partida y detiene el viaje."""
        room_map = pasillo(100, 100)
        game, mapa = armar_partida(room_map, sala_de_salida=2)
        explorar(mapa, 1, 2, 3)

        resultado = GameController(game, known_map=mapa).travel(3)

        self.assertEqual(resultado.steps, 1)
        self.assertEqual(resultado.reasons, [PARTIDA_TERMINADA])

    def test_contenido_no_disponible_no_consume_tiempo(self):
        """FR-028 (f) (supuesto del grupo): sin presupuesto para cargar la sala
        siguiente, el viaje se detiene sin mover ni consumir tiempo."""
        room_map = pasillo(100)
        game, mapa = armar_partida(room_map)
        explorar(mapa, 1, 2)
        reloj = game.state.clock

        resultado = GameController(
            game, repository=RepositorioSinContenido(), known_map=mapa
        ).travel(2)

        self.assertEqual(resultado.reasons, [CONTENIDO_NO_DISPONIBLE])
        self.assertEqual(resultado.steps, 0)
        self.assertIn("presupuesto", resultado.message)
        self.assertEqual(game.state.clock, reloj)
        self.assertEqual(game.player.room_id, 1)


class TestPresentacion(unittest.TestCase):
    """Historia 5, escenario 5: la interfaz informa por qué se detuvo."""

    def mostrar(self, resultado, destino):
        import io
        from view.console_view import ConsoleView

        salida = io.StringIO()
        ConsoleView(output=salida).show_travel_result(resultado, destino)
        return salida.getvalue()

    def test_muestra_todos_los_motivos_en_orden(self):
        """FR-029."""
        from controller.game_controller import TravelResult

        texto = self.mostrar(TravelResult(True, "", 2, [LLEGADA, ENEMIGOS, DANO]), 7)

        self.assertLess(texto.index("Llegaste a la sala 7"), texto.index("Hay enemigos"))
        self.assertLess(texto.index("Hay enemigos"), texto.index("Recibiste"))

    def test_muestra_el_rechazo(self):
        """FR-022."""
        from controller.game_controller import TravelResult

        texto = self.mostrar(TravelResult(False, "La sala 9 no esta en tu mapa."), 9)

        self.assertIn("La sala 9 no esta en tu mapa.", texto)

    def test_muestra_el_error_de_carga(self):
        """FR-028 (f), FR-029."""
        from controller.game_controller import TravelResult

        texto = self.mostrar(
            TravelResult(True, "sin presupuesto", 0, [CONTENIDO_NO_DISPONIBLE]), 2
        )

        self.assertIn("sin presupuesto", texto)


if __name__ == "__main__":
    unittest.main()
