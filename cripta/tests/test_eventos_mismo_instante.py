"""Consultar un instante con varios eventos (specs/003-linea-de-tiempo).

Historia 1, escenarios 6 y 9, y el caso del Apéndice B «varios eventos
ocurren en el mismo instante t: historia <t> muestra el estado después de
todos ellos». Lo exige FR-002.

Dos guardianes de la misma velocidad atacan al jugador a la vez, cada 100
unidades, y el jugador, más lento, espera cada 142. Así hay instantes con
dos eventos que no coinciden con ninguna decisión del jugador.

Las pruebas no comparan contra valores escritos a mano: durante la partida
registran el estado real después de cada turno de enemigo, y exigen que el
resumen de cada instante coincida con el estado después del último evento
de ese instante.
"""
import unittest

from adapters.almacen_partida import reconstruir_desde_copia, tomar_copia_del_estado
from model.consulta_historia import consultar_instante
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from structures.history import History, ReversibleEventQueue
from structures.inventory import Inventory
from structures.linea_de_tiempo import LineaDeTiempo
from structures.trail import PlayerTrail
from tests.test_linea_de_tiempo import estado_del_resumen, estado_observable

ESPERAS = 30


def partida_con_ataques_simultaneos(copias_cada=10):
    mapa = RoomMap()

    for numero in (1, 2):
        sala = Room(numero, f"Sala {numero}")
        sala.content_loaded = True
        mapa.add(sala)

    puerta = Door(1, 2, closed=False, cost=100)
    mapa.room(1).add_exit(Exit("N", 2, puerta))
    mapa.room(2).add_exit(Exit("S", 1, puerta))

    estado = GameState(seed=7)
    historial = History(estado)
    jugador = Player("p-1", "Heroe", 10 ** 6, 6, 2, 70, 1)
    jugador.inventory = Inventory(10, history=historial)
    guardianes = [
        Enemy(f"e-{numero}", f"Guardian {numero}", 10 ** 6, 3, 1, 100, 1, Enemy.GUARDIAN)
        for numero in (1, 2)
    ]
    linea = LineaDeTiempo(copias_cada=copias_cada)

    juego = Game(
        estado,
        jugador,
        guardianes,
        room_map=mapa,
        trail=PlayerTrail(historial),
        history=historial,
        event_queue=ReversibleEventQueue(historial),
        timeline=linea,
        snapshot=tomar_copia_del_estado,
    )

    return juego, linea


def jugar_registrando_cada_turno(juego):
    """Espera ESPERAS veces y devuelve [(instante, estado real después del turno)]."""
    registro = []
    turno_original = Game._run_enemy_turn

    def turno_registrado(motor, enemigo):
        resultado = turno_original(motor, enemigo)
        if motor is juego:
            registro.append((motor.state.clock, estado_observable(motor)))
        return resultado

    Game._run_enemy_turn = turno_registrado
    try:
        for _ in range(ESPERAS):
            if not juego.wait().accepted:
                break
    finally:
        Game._run_enemy_turn = turno_original

    return registro


def instantes_con_varios_eventos(registro, linea, reloj):
    """[(instante, estado real tras su último evento, hay otro evento antes de
    la siguiente decisión del jugador)] para cada instante con dos o más
    eventos que no es una decisión del jugador."""
    decisiones = [accion.reloj for accion in linea.acciones()]
    resultado = []
    indice = 0

    while indice < len(registro):
        instante = registro[indice][0]
        fin = indice

        while fin + 1 < len(registro) and registro[fin + 1][0] == instante:
            fin += 1

        cuantos = fin - indice + 1

        if cuantos > 1 and instante <= reloj and instante not in decisiones:
            siguiente_decision = min(
                (decision for decision in decisiones if decision > instante),
                default=reloj + 1,
            )
            otro_antes = fin + 1 < len(registro) and registro[fin + 1][0] < siguiente_decision
            resultado.append((instante, registro[fin][1], otro_antes))

        indice = fin + 1

    return resultado


class VariosEventosEnElMismoInstanteTest(unittest.TestCase):

    def setUp(self):
        self.juego, self.linea = partida_con_ataques_simultaneos()
        registro = jugar_registrando_cada_turno(self.juego)
        self.instantes = instantes_con_varios_eventos(
            registro, self.linea, self.juego.state.clock
        )

    def comprobar(self, casos):
        for instante, real, _ in casos:
            with self.subTest(instante=instante):
                resumen = consultar_instante(self.juego, instante, reconstruir_desde_copia)
                # El reloj del resumen es el instante pedido; lo demás debe ser el estado real.
                self.assertEqual(estado_del_resumen(resumen)[1:], real[1:])

    def test_la_partida_tiene_los_dos_tipos_de_instante(self):
        """Control: sin esto, las dos pruebas siguientes no probarían nada."""
        self.assertTrue([caso for caso in self.instantes if not caso[2]])
        self.assertTrue([caso for caso in self.instantes if caso[2]])

    def test_varios_eventos_en_el_mismo_instante_cuentan_todos(self):
        """FR-002 (Historia 1, escenario 9, Apéndice B): con dos ataques en el
        mismo instante t, el estado de t es el de después de los dos. Instantes
        tras los que no hay otro evento antes de la siguiente decisión."""
        self.comprobar([caso for caso in self.instantes if not caso[2]])

    @unittest.expectedFailure
    def test_un_evento_posterior_al_instante_no_cuenta(self):
        """FR-002 (Historia 1, escenarios 6 y 9): si después de t y antes de la
        siguiente decisión del jugador hay otro evento, el estado de t no lo
        incluye.

        Falla: la consulta repite la última acción del jugador completa, con
        todos los eventos hasta su siguiente decisión, también los de tiempo
        mayor que t. Corregirlo es de la línea de tiempo
        (model/consulta_historia.py y model/game.py): repetir esa última
        acción deteniendo los eventos en t. Al corregirlo, quitar el decorador.
        """
        self.comprobar([caso for caso in self.instantes if caso[2]])


if __name__ == "__main__":
    unittest.main()
