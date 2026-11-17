"""Niebla de guerra con el motor real (specs/003-niebla-ir-a, T015 a T019 y T029).

A diferencia de test_mapa_conocido.py y de test_ir_a.py, aquí nadie llama a
jugador_entro ni a puerta_cambio a mano: el mapa conocido se le pasa a la
partida y el conocimiento sale de los avisos del motor. Las criptas son
sintéticas y pequeñas, armadas con los ayudantes de test_ir_a.py. Cada prueba
cita en su docstring los requisitos que comprueba.
"""
import unittest

from controller.game_controller import GameController
from model.game import Game
from model.game_state import GameState
from model.item import Item
from model.player import Player
from model.trap import Trap
from model.viaje import ENEMIGOS, LLEGADA, SIN_RUTA
from structures.history import History, ReversibleEventQueue
from structures.inventory import Inventory
from structures.mapa_conocido import ABIERTA, AVISTADA, CERRADA, DESCONOCIDA, EXPLORADA, MapaConocido
from structures.trail import PlayerTrail
from tests.test_ir_a import conectar, guardian, mapa_de_salas, pergamino


LLAVE = "itm_llave"
ESPERAS_MAXIMAS = 50


def llave():
    return Item("o-llave", LLAVE, "Llave", Item.KEY, 1, 1)


def antorcha(duracion=5000):
    return Item("o-antorcha", "itm_antorcha", "Antorcha", Item.TORCH, 1, 5, duration=duracion)


def partida_con_niebla(room_map, enemigos=None, objetos=(), vida=100, seed=11,
                       con_mapa=True):
    """Partida armada como build_game: el mapa conocido comparte el historial
    y se le pasa a Game, que es quien avisa. Con con_mapa=False, la misma
    partida sin niebla de guerra."""
    state = GameState(seed=seed)
    history = History(state)
    jugador = Player(
        actor_id="p-1", name="Heroe", max_health=vida, attack=6, defense=0,
        speed=100, room_id=1,
    )
    jugador.inventory = Inventory(10, history)

    for objeto in objetos:
        jugador.inventory.pick_up(objeto)

    seleccionar_antorcha(jugador.inventory)
    mapa =MapaConocido(room_map, history) if con_mapa else None
    game = Game(
        state,
        jugador,
        enemigos,
        room_map=room_map,
        trail=PlayerTrail(history),
        history=history,
        event_queue=ReversibleEventQueue(history),
        known_map=mapa,
    )
    return game, mapa


def seleccionar_antorcha(inventario):
    """Deja el cursor sobre la antorcha, si la hay, para que usar la encienda."""
    inventario.go_to_start()
    while inventario.current() is not None:
        if inventario.current().item_class == Item.TORCH:
            return
        if not inventario.next():
            return


def esperar_hasta(game, condicion):
    for _ in range(ESPERAS_MAXIMAS):
        if condicion():
            return
        game.wait()
    raise AssertionError("la condición no se cumplió esperando")


def pasillo_con_puerta_que_se_cierra(auto_close=1000):
    """1 -E- 2 -E- 3; la puerta entre 2 y 3 está cerrada con llave y se
    cierra sola auto_close unidades después de abrirla."""
    room_map = mapa_de_salas(1, 2, 3)
    conectar(room_map, 1, 2, "E")
    puerta = conectar(room_map, 2, 3, "E", cerrada=True, llave=LLAVE)
    puerta.auto_close = auto_close
    return room_map, puerta


def recuerdos_de_la_sala_actual(game, mapa):
    """(recordado, real) de cada puerta de la sala del jugador."""
    pares = []
    for salida in game.room_map.room(game.player.room_id).exits():
        real = ABIERTA if salida.door.is_open else CERRADA
        pares.append((mapa.puerta_recordada(salida.door), real))
    return pares


class TestMemoriaDePuertas(unittest.TestCase):
    """T015 — Historia 2."""

    def test_una_puerta_que_se_cierra_lejos_se_sigue_recordando_abierta(self):
        """FR-006, FR-007 (Historia 2, escenarios 2 y 3): la puerta se cierra
        sola con el jugador lejos; el mapa la sigue recordando abierta, y al
        volver a una de sus salas el recuerdo se corrige."""
        room_map, puerta = pasillo_con_puerta_que_se_cierra()
        game, mapa = partida_con_niebla(room_map, objetos=[llave()])

        self.assertTrue(game.move("E").accepted)
        self.assertTrue(game.open_door("E").accepted)
        self.assertEqual(mapa.puerta_recordada(puerta), ABIERTA)
        self.assertTrue(game.move("O").accepted)
        esperar_hasta(game, lambda: puerta.closed)

        self.assertEqual(mapa.puerta_recordada(puerta), ABIERTA)

        self.assertTrue(game.move("E").accepted)

        self.assertEqual(mapa.puerta_recordada(puerta), CERRADA)

    def test_un_cierre_con_el_jugador_presente_se_observa_al_instante(self):
        """FR-006 (Historia 2, escenario 4)."""
        room_map, puerta = pasillo_con_puerta_que_se_cierra(auto_close=300)
        game, mapa = partida_con_niebla(room_map, objetos=[llave()])
        game.move("E")
        game.open_door("E")

        esperar_hasta(game, lambda: puerta.closed)

        self.assertEqual(mapa.puerta_recordada(puerta), CERRADA)

    def test_en_cada_instante_las_puertas_de_la_sala_coinciden(self):
        """SC-002, FR-006: en una partida con cierres automáticos, después de
        cada acción el recuerdo de cada puerta de la sala del jugador coincide
        con su estado real."""
        room_map, _ = pasillo_con_puerta_que_se_cierra(auto_close=250)
        game, mapa = partida_con_niebla(room_map, objetos=[llave()])
        acciones = (
            lambda: game.move("E"), lambda: game.open_door("E"), game.wait,
            game.wait, game.wait, lambda: game.open_door("E"),
            lambda: game.move("E"), game.wait, game.wait, game.wait,
            lambda: game.move("O"), lambda: game.move("O"), game.wait,
        )

        for accion in acciones:
            accion()
            for recordado, real in recuerdos_de_la_sala_actual(game, mapa):
                self.assertEqual(recordado, real)


class TestAntorcha(unittest.TestCase):
    """T016 — Historia 3."""

    def setUp(self):
        self.room_map = mapa_de_salas(1, 2, 3)
        conectar(self.room_map, 1, 2, "E")
        self.puerta_2_3 = conectar(self.room_map, 2, 3, "E")
        self.trampa = Trap("t-1", "trp_dardos", "Dardos", 5, 300, 3)
        self.room_map.room(3).traps.append(self.trampa)
        self.dormido = guardian(3)

    def test_encender_la_antorcha_no_explora_nada(self):
        """FR-037 (Historia 3, escenario 6)."""
        game, mapa = partida_con_niebla(self.room_map, [self.dormido], [antorcha()])
        antes = mapa.exportar()

        self.assertTrue(game.use_item().accepted)

        self.assertTrue(game.torch_lit)
        self.assertEqual(mapa.exportar(), antes)
        self.assertEqual(mapa.estado_de_sala(2), AVISTADA)

    def test_explora_las_vecinas_sin_activar_enemigos_ni_trampas(self):
        """Apéndice B; FR-009, FR-010, FR-011 (Historia 3, escenarios 1 y 2):
        al entrar con la antorcha la vecina queda explorada, su enemigo sigue
        dormido y sin turno en la agenda, y su trampa sigue armada."""
        game, mapa = partida_con_niebla(self.room_map, [self.dormido], [antorcha()])
        game.use_item()

        self.assertTrue(game.move("E").accepted)

        self.assertEqual(mapa.estado_de_sala(3), EXPLORADA)
        self.assertFalse(self.dormido.is_active)
        self.assertIsNone(self.dormido.scheduled_event)
        self.assertTrue(self.trampa.armed)
        self.assertEqual(game.player.health, game.player.max_health)

    def test_la_antorcha_apagada_deja_de_explorar(self):
        """FR-009: con la antorcha ya apagada, entrar no explora vecinas."""
        game, mapa = partida_con_niebla(self.room_map, [self.dormido], [antorcha(duracion=200)])
        game.use_item()
        esperar_hasta(game, lambda: not game.torch_lit)

        game.move("E")

        self.assertEqual(mapa.estado_de_sala(3), AVISTADA)


class TestReversion(unittest.TestCase):
    """T017 — Historia 6."""

    def setUp(self):
        self.room_map = mapa_de_salas(1, 2, 3)
        conectar(self.room_map, 1, 2, "E")
        self.puerta_2_3 = conectar(self.room_map, 2, 3, "E")

    def test_el_pergamino_revierte_una_entrada_con_antorcha(self):
        """Apéndice B; FR-015 (Historia 6, escenario 1): las salas exploradas
        en la entrada revertida vuelven a su estado anterior."""
        game, mapa = partida_con_niebla(self.room_map, objetos=[antorcha(), pergamino()])
        game.use_item()
        antes = mapa.exportar()
        game.move("E")
        self.assertEqual(mapa.estado_de_sala(3), EXPLORADA)

        self.assertTrue(game.rewind().accepted)

        self.assertEqual(game.player.room_id, 1)
        self.assertEqual(mapa.exportar(), antes)
        self.assertEqual(mapa.estado_de_sala(2), AVISTADA)
        self.assertEqual(mapa.estado_de_sala(3), DESCONOCIDA)

    def test_el_recuerdo_de_una_puerta_vuelve_al_anterior(self):
        """FR-015 (Historia 6, escenario 2): una puerta observada durante la
        acción revertida vuelve a como se recordaba antes, y deshacer no
        cuenta como observar."""
        game, mapa = partida_con_niebla(self.room_map, objetos=[pergamino()])
        self.assertEqual(mapa.puerta_recordada(self.puerta_2_3), DESCONOCIDA)
        game.move("E")
        self.assertEqual(mapa.puerta_recordada(self.puerta_2_3), ABIERTA)

        game.rewind()

        self.assertEqual(mapa.puerta_recordada(self.puerta_2_3), DESCONOCIDA)


def jugar(acciones, con_mapa=True, seed=7):
    """Juega una partida con combate y devuelve la partida, el mapa y el
    conocimiento exportado después de cada acción."""
    room_map = mapa_de_salas(1, 2, 3)
    conectar(room_map, 1, 2, "E")
    conectar(room_map, 2, 3, "E", costo=150)
    enemigos = [guardian(2, "e-1", ataque=4), guardian(3, "e-2", ataque=2)]
    game, mapa = partida_con_niebla(room_map, enemigos, [antorcha()], seed=seed,
                                    con_mapa=con_mapa)
    instantes = []

    for accion in acciones:
        accion(game)
        if mapa is not None:
            instantes.append(mapa.exportar())

    return game, instantes


ACCIONES = (
    lambda g: g.use_item(), lambda g: g.move("E"), lambda g: g.attack("e-1"),
    lambda g: g.attack("e-1"), lambda g: g.wait(), lambda g: g.move("E"),
    lambda g: g.attack("e-2"), lambda g: g.move("O"), lambda g: g.wait(),
)


class TestDeterminismo(unittest.TestCase):
    """T018."""

    def test_misma_semilla_y_acciones_dan_el_mismo_conocimiento(self):
        """FR-017 (Historia 6, escenario 4): en cada instante."""
        _, primera = jugar(ACCIONES)
        _, segunda = jugar(ACCIONES)

        self.assertEqual(primera, segunda)


class TestNoInterferencia(unittest.TestCase):
    """T019."""

    def test_con_y_sin_mapa_la_partida_es_la_misma(self):
        """FR-013: el mapa conocido no cambia las decisiones de los enemigos,
        el reloj ni el resultado."""
        con, _ = jugar(ACCIONES, con_mapa=True)
        sin, _ = jugar(ACCIONES, con_mapa=False)

        self.assertEqual(con.state.clock, sin.state.clock)
        self.assertEqual(con.result, sin.result)
        self.assertEqual(con.player.health, sin.player.health)
        self.assertEqual(list(con.messages), list(sin.messages))
        self.assertEqual(
            [(e.room_id, e.health, e.is_active) for e in con.enemies],
            [(e.room_id, e.health, e.is_active) for e in sin.enemies],
        )


class TestViajeConElMotor(unittest.TestCase):
    """T029 y los demás casos del Apéndice B, con el conocimiento que
    producen los avisos del motor y no uno armado a mano."""

    def test_no_explorada_se_rechaza(self):
        """Apéndice B; FR-022: una sala solo avistada no es destino."""
        room_map = mapa_de_salas(1, 2)
        conectar(room_map, 1, 2, "E")
        game, mapa = partida_con_niebla(room_map)
        reloj = game.state.clock

        resultado = GameController(game).travel(2)

        self.assertFalse(resultado.accepted)
        self.assertEqual(game.state.clock, reloj)
        self.assertEqual(mapa.estado_de_sala(2), AVISTADA)

    def test_puerta_recordada_abierta_que_esta_cerrada(self):
        """Apéndice B; FR-006, FR-026, FR-028 (Historia 5, escenario 1): al
        llegar a la sala desde la que se ve la puerta, el recuerdo se corrige,
        la ruta se recalcula y, sin otra ruta, el viaje se detiene sin_ruta con
        el reloj donde lo dejó el último paso."""
        room_map, puerta = pasillo_con_puerta_que_se_cierra()
        game, mapa = partida_con_niebla(room_map, objetos=[llave()])
        game.move("E")
        game.open_door("E")
        game.move("E")
        game.move("O")
        game.move("O")
        esperar_hasta(game, lambda: puerta.closed)
        self.assertEqual(mapa.puerta_recordada(puerta), ABIERTA)
        controller = GameController(game)
        relojes = []
        original = controller.execute

        def anotar(command):
            resultado = original(command)
            relojes.append(game.state.clock)
            return resultado

        controller.execute = anotar

        resultado = controller.travel(3)

        self.assertEqual(resultado.steps, 1)
        self.assertEqual(resultado.reasons, [SIN_RUTA])
        self.assertEqual(game.player.room_id, 2)
        self.assertEqual(mapa.puerta_recordada(puerta), CERRADA)
        self.assertTrue(puerta.closed)
        self.assertEqual(game.state.clock, relojes[-1])

    def test_entrar_a_una_sala_con_enemigos_dormidos(self):
        """Apéndice B; FR-028 (b): la sala, explorada con la antorcha, tiene
        un enemigo dormido; al entrar se activa y el viaje se detiene."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 2, "E")
        conectar(room_map, 2, 3, "E")
        dormido = guardian(3)
        game, mapa = partida_con_niebla(room_map, [dormido], [antorcha()])
        game.use_item()
        game.move("E")
        game.move("O")
        self.assertEqual(mapa.estado_de_sala(3), EXPLORADA)
        self.assertFalse(dormido.is_active)

        resultado = GameController(game).travel(3)

        self.assertTrue(dormido.is_active)
        self.assertIn(ENEMIGOS, resultado.reasons)
        self.assertIn(LLEGADA, resultado.reasons)

    def test_pergamino_durante_un_viaje(self):
        """Apéndice B; FR-015, FR-032 (Historia 5, escenario 7): el pergamino
        revierte solo el último paso, con su conocimiento, y el viaje no sigue."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 2, "E")
        conectar(room_map, 2, 3, "E")
        game, mapa = partida_con_niebla(room_map, objetos=[pergamino()])
        game.move("E")
        game.move("E")
        game.move("O")
        game.move("O")
        antes_del_viaje = mapa.exportar()
        resultado = GameController(game).travel(3)
        self.assertEqual(resultado.steps, 2)
        acciones = game.player_actions

        self.assertTrue(game.rewind().accepted)

        self.assertEqual(game.player.room_id, 2)
        self.assertEqual(game.player_actions, acciones - 1)
        self.assertEqual(mapa.exportar(), antes_del_viaje)


if __name__ == "__main__":
    unittest.main()
