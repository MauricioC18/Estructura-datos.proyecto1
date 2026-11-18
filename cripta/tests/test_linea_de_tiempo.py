"""Pruebas de la linea de tiempo (seccion 3.6 y 5.5 de la segunda parte).

La estructura se prueba con bloques de bytes falsos, sin tocar el motor: no
reconstruye nada, solo guarda y localiza.
"""
import struct
import tempfile
import unittest
from pathlib import Path

from adapters.almacen_partida import (
    VERSION_DEL_FORMATO,
    AlmacenPartida,
    PartidaIncompatible,
    construir_juego_reversible,
    reconstruir_desde_copia,
    tomar_copia_del_estado,
)
from model.consulta_historia import (
    MAPA_CONOCIDO_NO_DISPONIBLE,
    PARTIDA_TERMINO_ANTES,
    ConsultaRechazada,
    consultar_accion,
    consultar_hasta,
    consultar_instante,
)
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.item import Item
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from model.trap import Trap
from structures.history import History, ReversibleEventQueue
from structures.inventory import Inventory
from structures.linea_de_tiempo import LineaDeTiempo
from structures.trail import PlayerTrail


def llenar(linea, cantidad, reloj_por_accion=100):
    """Registra acciones, pidiendo copias cuando la linea lo diga."""
    for numero in range(cantidad):
        if linea.hace_falta_copia():
            linea.guardar_copia(numero * reloj_por_accion, b"x" * 10)

        linea.registrar_accion("esperar", None, numero * reloj_por_accion)

    return linea


class LineaVaciaTest(unittest.TestCase):

    def test_una_linea_nueva_no_tiene_nada(self):
        linea = LineaDeTiempo(copias_cada=10)

        self.assertEqual(linea.cantidad_de_acciones(), 0)
        self.assertEqual(linea.cantidad_de_copias(), 0)

    def test_una_linea_vacia_pide_la_primera_copia(self):
        self.assertTrue(LineaDeTiempo(copias_cada=10).hace_falta_copia())

    def test_una_linea_vacia_no_encuentra_copia(self):
        self.assertIsNone(LineaDeTiempo(copias_cada=10).copia_para_accion(0))

    def test_recortar_una_linea_vacia_no_falla(self):
        self.assertFalse(LineaDeTiempo(copias_cada=10).recortar_ultima_accion())

    def test_rechaza_una_cantidad_entre_copias_invalida(self):
        for invalido in (0, -1, "10", 1.5, True):
            with self.subTest(copias_cada=invalido):
                with self.assertRaises(ValueError):
                    LineaDeTiempo(copias_cada=invalido)


class CopiasCadaKTest(unittest.TestCase):
    """FR-015: una copia completa cada K acciones, nunca mas seguido."""

    def test_con_k_de_diez_y_treinta_y_cinco_acciones_hay_cuatro_copias(self):
        linea = llenar(LineaDeTiempo(copias_cada=10), 35)

        self.assertEqual(linea.cantidad_de_acciones(), 35)
        self.assertEqual(linea.cantidad_de_copias(), 4)
        self.assertEqual(
            [copia.acciones for copia in linea.copias()], [0, 10, 20, 30]
        )

    def test_con_k_de_uno_hay_una_copia_por_accion(self):
        """La alternativa ingenua, la que sirve de referencia al medir."""
        linea = llenar(LineaDeTiempo(copias_cada=1), 12)

        self.assertEqual(linea.cantidad_de_copias(), 12)

    def test_con_k_mayor_que_la_partida_hay_una_sola_copia(self):
        linea = llenar(LineaDeTiempo(copias_cada=1000), 40)

        self.assertEqual(linea.cantidad_de_copias(), 1)
        self.assertEqual(linea.copias()[0].acciones, 0)

    def test_guardar_dos_copias_en_el_mismo_punto_deja_una(self):
        linea = LineaDeTiempo(copias_cada=10)
        linea.guardar_copia(0, b"primera")
        linea.guardar_copia(0, b"segunda")

        self.assertEqual(linea.cantidad_de_copias(), 1)
        self.assertEqual(linea.copias()[0].bloque, b"segunda")


class BusquedaDeLaCopiaTest(unittest.TestCase):
    """FR-018: localizar la copia sin examinarlas todas."""

    def setUp(self):
        self.linea = llenar(LineaDeTiempo(copias_cada=10), 35)

    def test_un_numero_de_accion_que_cae_justo_en_una_copia(self):
        self.assertEqual(self.linea.copia_para_accion(20).acciones, 20)

    def test_un_numero_de_accion_entre_dos_copias(self):
        self.assertEqual(self.linea.copia_para_accion(25).acciones, 20)

    def test_la_primera_accion_cae_en_la_copia_inicial(self):
        self.assertEqual(self.linea.copia_para_accion(0).acciones, 0)
        self.assertEqual(self.linea.copia_para_accion(3).acciones, 0)

    def test_un_numero_de_accion_despues_de_la_ultima_copia(self):
        self.assertEqual(self.linea.copia_para_accion(34).acciones, 30)

    def test_la_copia_elegida_nunca_esta_a_mas_de_k_acciones(self):
        """FR-016: ninguna consulta repite mas de K acciones."""
        for numero in range(self.linea.cantidad_de_acciones() + 1):
            copia = self.linea.copia_para_accion(numero)
            self.assertLessEqual(numero - copia.acciones, self.linea.copias_cada)


class TraducirUnInstanteTest(unittest.TestCase):
    """FR-002: cuentan los eventos de tiempo menor o igual que t, y si a t le
    corresponde una decision del jugador es el estado justo antes."""

    def setUp(self):
        self.linea = llenar(LineaDeTiempo(copias_cada=10), 10)

    def test_el_instante_cero_no_tiene_ninguna_accion_ocurrida(self):
        self.assertEqual(self.linea.accion_en_instante(0), 0)

    def test_un_instante_que_cae_sobre_una_accion_queda_justo_antes(self):
        """La accion anotada con reloj 500 todavia no ha ocurrido en 500."""
        self.assertEqual(self.linea.accion_en_instante(500), 5)

    def test_un_instante_entre_dos_acciones(self):
        self.assertEqual(self.linea.accion_en_instante(450), 5)

    def test_un_instante_posterior_a_todas_las_acciones(self):
        self.assertEqual(self.linea.accion_en_instante(10000), 10)

    def test_una_linea_sin_acciones_devuelve_cero(self):
        self.assertEqual(LineaDeTiempo().accion_en_instante(500), 0)


class RecortarTest(unittest.TestCase):
    """FR-011 y FR-019: el pergamino recorta sin recorrer la historia."""

    def test_recortar_quita_una_accion(self):
        linea = llenar(LineaDeTiempo(copias_cada=10), 12)

        self.assertTrue(linea.recortar_ultima_accion())
        self.assertEqual(linea.cantidad_de_acciones(), 11)

    def test_recortar_quita_la_copia_que_quedo_en_el_futuro(self):
        linea = llenar(LineaDeTiempo(copias_cada=10), 11)
        self.assertEqual(linea.cantidad_de_copias(), 2)

        linea.recortar_ultima_accion()

        self.assertEqual(linea.cantidad_de_acciones(), 10)
        self.assertEqual(linea.cantidad_de_copias(), 2)

        linea.recortar_ultima_accion()

        self.assertEqual(linea.cantidad_de_acciones(), 9)
        self.assertEqual(linea.cantidad_de_copias(), 1)

    def test_recortar_nunca_quita_la_copia_inicial(self):
        linea = llenar(LineaDeTiempo(copias_cada=10), 3)

        for _ in range(5):
            linea.recortar_ultima_accion()

        self.assertEqual(linea.cantidad_de_acciones(), 0)
        self.assertEqual(linea.cantidad_de_copias(), 1)

    def test_varios_recortes_seguidos_dejan_la_linea_consistente(self):
        linea = llenar(LineaDeTiempo(copias_cada=5), 23)

        for _ in range(4):
            linea.recortar_ultima_accion()

        self.assertEqual(linea.cantidad_de_acciones(), 19)
        for copia in linea.copias():
            self.assertLessEqual(copia.acciones, 19)


class MemoriaTest(unittest.TestCase):
    """FR-017: la memoria crece con los cambios mas una copia cada K."""

    def test_el_desglose_suma_las_tres_listas(self):
        linea = llenar(LineaDeTiempo(copias_cada=10), 20)

        copias, acciones = linea.memoria_en_bytes()

        self.assertEqual(copias, 2 * 10)
        self.assertGreater(acciones, 0)

    def test_bajar_k_sube_la_memoria_de_las_copias(self):
        """Es el intercambio que la medicion tiene que cuantificar."""
        grande = llenar(LineaDeTiempo(copias_cada=50), 100)
        chica = llenar(LineaDeTiempo(copias_cada=1), 100)

        self.assertLess(
            grande.memoria_en_bytes()[0],
            chica.memoria_en_bytes()[0],
        )


# ----------------------------------------------------------------------
# Reconstruccion: la parte que de verdad responde consultas
# ----------------------------------------------------------------------

def construir_partida_con_linea(copias_cada=10, semilla=2026, salas=4,
                                objetos_extra=()):
    """Partida rica en azar, con linea de tiempo conectada.

    Hay combate, veneno, trampas, una puerta con cierre automatico y objetos
    en el suelo, para que el generador aleatorio trabaje de verdad: una
    divergencia del generador solo se ve si hay azar en juego.
    """
    cuartos = []

    for numero in range(1, salas + 1):
        cuarto = Room(numero, f"Sala {numero}")
        cuarto.content_loaded = True
        cuartos.append(cuarto)

    for indice in range(salas - 1):
        puerta = Door(
            indice + 1,
            indice + 2,
            closed=False,
            auto_close=250 if indice == 0 else None,
            cost=50 if indice % 2 == 0 else 150,
        )
        cuartos[indice].add_exit(Exit("N", indice + 2, puerta))
        cuartos[indice + 1].add_exit(Exit("S", indice + 1, puerta))

    cuartos[1].traps.append(Trap("t-1", "trp_dardos", "Dardos", 3, 200, 2))
    cuartos[0].floor_items.append(
        Item("i-daga", "itm_daga", "Daga", Item.WEAPON, 1, 2, attack_bonus=3)
    )
    cuartos[0].floor_items.append(
        Item("i-pocion", "itm_pocion", "Pocion", Item.POTION, 1, 2, heal=5)
    )

    mapa = RoomMap()

    for cuarto in cuartos:
        mapa.add(cuarto)

    estado = GameState(seed=semilla)
    historial = History(estado)

    jugador = Player("p-1", "Heroe", 500, 6, 2, 100, 1)
    jugador.inventory = Inventory(10, history=historial)

    for numero in range(3):
        jugador.inventory.pick_up(
            Item(f"i-perg-{numero}", "itm_pergamino", "Pergamino",
                 Item.REWIND_SCROLL, 1, 2)
        )

    for objeto in objetos_extra:
        jugador.inventory.pick_up(objeto)

    enemigos = [
        Enemy("e-1", "Rata", 30, 4, 1, 90, 2, Enemy.WANDERER),
        Enemy("e-2", "Centinela", 40, 5, 2, 110, 3, Enemy.GUARDIAN),
    ]

    linea = LineaDeTiempo(copias_cada=copias_cada)

    juego = Game(
        estado,
        jugador,
        enemigos,
        room_map=mapa,
        trail=PlayerTrail(historial),
        history=historial,
        event_queue=ReversibleEventQueue(historial),
        timeline=linea,
        snapshot=tomar_copia_del_estado,
    )

    return juego, linea


class MapaConocidoDoble:
    """Doble del mapa conocido, con el contrato acordado con Steven.

    Recibe los avisos del motor (jugador_entro, puerta_cambio) y responde
    salas_exploradas(). Sirve para probar que el motor avisa y que el resumen
    lee, sin depender del modulo real, que vive en otra rama.
    """

    disponible = True

    def __init__(self):
        self._exploradas = []
        self.puertas_observadas = 0

    def jugador_entro(self, room_id, torch_lit):
        if room_id not in self._exploradas:
            self._exploradas.append(room_id)

    def puerta_cambio(self, door, player_room_id):
        self.puertas_observadas += 1

    def salas_exploradas(self):
        return list(self._exploradas)


def estado_observable(juego):
    """Lo que un resumen debe poder reproducir."""
    sala = juego.player.room_id

    return (
        juego.state.clock,
        sala,
        juego.player.health,
        juego.player.effective_attack,
        juego.player.effective_defense,
        juego.player.speed,
        tuple((item.name, item.item_class) for item in juego.player.inventory),
        tuple(
            (efecto.name, efecto.ends_at)
            for efecto in juego.effects
            if not efecto.cancelled
        ),
        tuple(
            (enemigo.actor_id, enemigo.name, enemigo.health)
            for enemigo in juego.enemies
            if enemigo.room_id == sala and enemigo.is_alive
        ),
        juego.result,
    )


def estado_del_resumen(resumen):
    return (
        resumen.instante,
        resumen.sala,
        resumen.vida,
        resumen.ataque,
        resumen.defensa,
        resumen.velocidad,
        tuple(resumen.inventario),
        tuple(resumen.efectos),
        tuple(resumen.enemigos),
        resumen.resultado,
    )


def jugar_guardando_el_estado(juego, cuantas):
    """Juega y devuelve el estado real de antes de cada accion.

    El estado en el instante de una accion es el de justo antes de tomarla
    (FR-002), asi que se guarda antes de ejecutarla.
    """
    reales = []
    paso = 0

    while len(reales) < cuantas and not juego.is_over:
        antes = estado_observable(juego)
        resto = paso % 6

        if resto == 0:
            resultado = juego.move("N")
        elif resto == 2:
            resultado = juego.move("S")
        elif resto == 3:
            resultado = juego.pick_up(0)
        else:
            resultado = juego.wait()

        if not resultado.accepted:
            resultado = juego.wait()

            if not resultado.accepted:
                break

        reales.append(antes)
        paso += 1

    return reales


class ReconstruirUnInstanteTest(unittest.TestCase):
    """Historia 1: consultar un instante pasado."""

    def test_todos_los_instantes_coinciden_con_el_estado_real(self):
        """FR-023 y SC-001: la prueba de fondo de la capacidad.

        No compara contra valores escritos a mano: juega guardando el estado
        real de antes de cada accion y despues consulta TODAS las acciones,
        exigiendo que cada resumen coincida. Es la unica forma de ver una
        divergencia del generador aleatorio.
        """
        juego, linea = construir_partida_con_linea(copias_cada=10)
        reales = jugar_guardando_el_estado(juego, 40)

        self.assertGreaterEqual(len(reales), 20, "la partida quedo demasiado corta")

        for numero, real in enumerate(reales):
            with self.subTest(accion=numero):
                resumen = consultar_accion(juego, numero, reconstruir_desde_copia)
                self.assertEqual(estado_del_resumen(resumen), real)

    def test_consultar_por_instante_del_reloj_da_lo_mismo(self):
        """FR-003: las dos formas de preguntar coinciden."""
        juego, _ = construir_partida_con_linea(copias_cada=10)
        reales = jugar_guardando_el_estado(juego, 24)

        for numero, real in enumerate(reales):
            with self.subTest(accion=numero):
                resumen = consultar_instante(juego, real[0], reconstruir_desde_copia)
                self.assertEqual(estado_del_resumen(resumen), real)

    def test_el_instante_cero_da_el_estado_inicial(self):
        juego, _ = construir_partida_con_linea()
        inicial = estado_observable(juego)
        jugar_guardando_el_estado(juego, 15)

        resumen = consultar_instante(juego, 0, reconstruir_desde_copia)

        self.assertEqual(estado_del_resumen(resumen), inicial)

    def test_dos_consultas_del_mismo_instante_dan_lo_mismo(self):
        """FR-022."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 15)

        primera = consultar_accion(juego, 5, reconstruir_desde_copia)
        segunda = consultar_accion(juego, 5, reconstruir_desde_copia)

        self.assertEqual(estado_del_resumen(primera), estado_del_resumen(segunda))

    def test_el_resumen_trae_todo_lo_que_exige_el_enunciado(self):
        """FR-004."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 15)

        resumen = consultar_accion(juego, 7, reconstruir_desde_copia)

        self.assertIsNotNone(resumen.instante)
        self.assertIsNotNone(resumen.sala)
        self.assertIsNotNone(resumen.nombre_de_la_sala)
        self.assertIsNotNone(resumen.vida)
        self.assertIsNotNone(resumen.ataque)
        self.assertIsNotNone(resumen.defensa)
        self.assertIsNotNone(resumen.velocidad)
        self.assertIsInstance(resumen.inventario, list)
        self.assertIsInstance(resumen.efectos, list)
        self.assertIsInstance(resumen.enemigos, list)
        self.assertEqual(resumen.mapa_conocido, MAPA_CONOCIDO_NO_DISPONIBLE)

    def test_el_mapa_conocido_se_lee_de_quien_lo_tenga(self):
        """El dato es de la niebla de guerra, que la implementa otro.

        Se usa un doble que cumple el contrato acordado: recibe los avisos del
        motor y responde salas_exploradas(). Asi la prueba vale aunque el
        modulo real todavia no este en esta rama.
        """
        juego, _ = construir_partida_con_linea(objetos_extra=())
        jugar_guardando_el_estado(juego, 12)

        def reconstruir_con_mapa(bloque):
            reconstruido = reconstruir_desde_copia(bloque)
            reconstruido.known_map = MapaConocidoDoble()
            return reconstruido

        resumen = consultar_accion(juego, 6, reconstruir_con_mapa)

        self.assertIsInstance(resumen.mapa_conocido, tuple)
        self.assertIn(1, resumen.mapa_conocido)

    def test_sin_niebla_de_guerra_el_resumen_lo_dice_en_vez_de_fallar(self):
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 8)

        resumen = consultar_accion(juego, 3, reconstruir_desde_copia)

        self.assertEqual(resumen.mapa_conocido, MAPA_CONOCIDO_NO_DISPONIBLE)


class ConsultarNoAlteraNadaTest(unittest.TestCase):
    """FR-005 a FR-008 y SC-003."""

    def test_cien_consultas_no_cambian_la_partida(self):
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 20)

        antes = estado_observable(juego)
        acciones_antes = juego.player_actions
        eventos_antes = len(juego.events.active_events())

        for _ in range(100):
            consultar_accion(juego, 5, reconstruir_desde_copia)

        self.assertEqual(estado_observable(juego), antes)
        self.assertEqual(juego.player_actions, acciones_antes)
        self.assertEqual(len(juego.events.active_events()), eventos_antes)

    def test_consultar_no_consume_tiempo_virtual(self):
        """FR-005."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 12)
        reloj = juego.state.clock

        consultar_accion(juego, 4, reconstruir_desde_copia)

        self.assertEqual(juego.state.clock, reloj)

    def test_consultar_no_cuenta_como_accion(self):
        """FR-006."""
        juego, linea = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 12)
        cuantas = linea.cantidad_de_acciones()

        consultar_accion(juego, 4, reconstruir_desde_copia)

        self.assertEqual(linea.cantidad_de_acciones(), cuantas)

    def test_consultar_no_toca_el_historial_del_pergamino(self):
        """FR-008: la linea de tiempo y el pergamino son independientes."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 12)
        disponibles = juego.history.available_actions()

        for _ in range(10):
            consultar_accion(juego, 3, reconstruir_desde_copia)

        self.assertEqual(juego.history.available_actions(), disponibles)

    def test_consultar_no_reconstruye_sobre_los_objetos_vivos(self):
        """La consulta trabaja sobre objetos nuevos, no sobre los de la partida."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 12)
        jugador_vivo = juego.player

        consultar_accion(juego, 3, reconstruir_desde_copia)

        self.assertIs(juego.player, jugador_vivo)


class ObjetoQueSeEstaViendoTest(unittest.TestCase):
    """El caso que el plan senala como el mas facil de arruinar.

    Soltar, usar y equipar actuan sobre el objeto que el cursor muestra, y el
    cursor lo mueven comandos que NO consumen tiempo y por lo tanto no son
    acciones. Si la linea guardara la posicion en vez del identificador del
    objeto, repetir la accion soltaria otro objeto.
    """

    def _partida_con_objetos(self, extra=()):
        """Los objetos entran ANTES de construir la partida.

        Si se agregaran despues, quedarian fuera de la copia inicial y la
        reconstruccion no podria conocerlos: seria un defecto de la prueba y
        no del programa.
        """
        gemas = [
            Item(f"i-obj-{numero}", "itm_gema", f"Gema {numero}",
                 Item.ARMOR, 1, 2, defense_bonus=1)
            for numero in range(3)
        ]
        juego, linea = construir_partida_con_linea(
            copias_cada=5, objetos_extra=gemas + list(extra)
        )

        return juego, linea, juego.player.inventory

    def test_soltar_despues_de_mover_el_cursor_se_repite_bien(self):
        juego, _, inventario = self._partida_con_objetos()

        inventario.go_to_start()
        inventario.next()
        inventario.next()
        objetivo = inventario.current().instance_id

        antes = estado_observable(juego)
        self.assertTrue(juego.drop().accepted)
        numero = juego.timeline.cantidad_de_acciones() - 1

        resumen = consultar_accion(juego, numero, reconstruir_desde_copia)
        self.assertEqual(estado_del_resumen(resumen), antes)

        despues = estado_observable(juego)
        siguiente = consultar_accion(
            juego, numero + 1, reconstruir_desde_copia
        )
        self.assertEqual(estado_del_resumen(siguiente), despues)
        self.assertNotIn(objetivo, [nombre for nombre, _ in siguiente.inventario])

    def test_equipar_despues_de_mover_el_cursor_se_repite_bien(self):
        juego, _, inventario = self._partida_con_objetos()

        inventario.go_to_start()
        inventario.next()
        inventario.next()
        inventario.next()

        self.assertTrue(juego.equip_item().accepted)
        despues = estado_observable(juego)
        numero = juego.timeline.cantidad_de_acciones()

        resumen = consultar_accion(juego, numero, reconstruir_desde_copia)

        self.assertEqual(estado_del_resumen(resumen), despues)

    def test_usar_despues_de_mover_el_cursor_se_repite_bien(self):
        cura = Item("i-cura", "itm_pocion", "Pocion", Item.POTION, 1, 2, heal=7)
        juego, _, inventario = self._partida_con_objetos(extra=[cura])

        inventario.go_to_start()
        for _ in range(20):
            actual = inventario.current()
            if actual is not None and actual.instance_id == "i-cura":
                break
            if not inventario.next():
                break

        self.assertTrue(juego.use_item().accepted)
        despues = estado_observable(juego)
        numero = juego.timeline.cantidad_de_acciones()

        resumen = consultar_accion(juego, numero, reconstruir_desde_copia)

        self.assertEqual(estado_del_resumen(resumen), despues)


class ConsultasImposiblesTest(unittest.TestCase):
    """Historia 2: preguntar por algo que no paso."""

    def setUp(self):
        self.juego, self.linea = construir_partida_con_linea()
        jugar_guardando_el_estado(self.juego, 12)

    def test_un_instante_posterior_al_reloj_se_rechaza(self):
        """Apendice B y SC-004."""
        with self.assertRaises(ConsultaRechazada) as error:
            consultar_instante(
                self.juego, self.juego.state.clock + 1, reconstruir_desde_copia
            )

        self.assertIn("futuro", str(error.exception))

    def test_el_instante_exacto_del_reloj_si_se_acepta(self):
        """El enunciado solo prohibe el instante POSTERIOR."""
        resumen = consultar_instante(
            self.juego, self.juego.state.clock, reconstruir_desde_copia
        )

        self.assertEqual(resumen.instante, self.juego.state.clock)

    def test_un_instante_negativo_se_rechaza(self):
        with self.assertRaises(ConsultaRechazada):
            consultar_instante(self.juego, -1, reconstruir_desde_copia)

    def test_un_instante_que_no_es_entero_se_rechaza(self):
        for invalido in ("500", 1.5, None, True):
            with self.subTest(instante=invalido):
                with self.assertRaises(ConsultaRechazada):
                    consultar_instante(self.juego, invalido, reconstruir_desde_copia)

    def test_una_accion_que_no_se_ha_tomado_se_rechaza(self):
        """FR-010."""
        with self.assertRaises(ConsultaRechazada) as error:
            consultar_accion(
                self.juego,
                self.linea.cantidad_de_acciones() + 5,
                reconstruir_desde_copia,
            )

        self.assertIn("ha tomado", str(error.exception))

    def test_una_accion_negativa_se_rechaza(self):
        with self.assertRaises(ConsultaRechazada):
            consultar_accion(self.juego, -1, reconstruir_desde_copia)

    def test_una_consulta_rechazada_no_consume_tiempo_ni_cuenta(self):
        """FR-009: nada cambia."""
        reloj = self.juego.state.clock
        acciones = self.linea.cantidad_de_acciones()

        with self.assertRaises(ConsultaRechazada):
            consultar_instante(self.juego, reloj + 1000, reconstruir_desde_copia)

        self.assertEqual(self.juego.state.clock, reloj)
        self.assertEqual(self.linea.cantidad_de_acciones(), acciones)

    def test_una_partida_sin_linea_lo_dice(self):
        juego = Game(
            GameState(seed=1),
            Player("p-1", "Heroe", 100, 6, 2, 100, 1),
            room_map=None,
            start=False,
        )

        with self.assertRaises(ConsultaRechazada) as error:
            consultar_instante(juego, 0, reconstruir_desde_copia)

        self.assertIn("linea de tiempo", str(error.exception))


class PergaminoYLineaTest(unittest.TestCase):
    """Historia 3: lo que el pergamino borro deja de estar en la historia."""

    def test_la_accion_revertida_deja_de_estar_en_la_linea(self):
        """Apendice B."""
        juego, linea = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 12)
        cuantas = linea.cantidad_de_acciones()

        self.assertTrue(juego.rewind().accepted)

        self.assertEqual(linea.cantidad_de_acciones(), cuantas - 1)

    def test_el_instante_revertido_ya_no_se_puede_consultar(self):
        """SC-005: ese instante paso a ser futuro respecto del reloj."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 12)
        reloj_antes = juego.state.clock

        juego.rewind()

        self.assertLess(juego.state.clock, reloj_antes)

        with self.assertRaises(ConsultaRechazada):
            consultar_instante(juego, reloj_antes, reconstruir_desde_copia)

    def test_un_pergamino_fuerza_una_copia_completa(self):
        """Un pergamino deja la partida donde la lista de acciones no llega.

        No basta con anotar el estado del generador, que era la idea del plan:
        el pergamino tambien consume un pergamino del inventario, y ese
        consumo no es una accion del jugador. Hace falta una copia completa.
        """
        juego, linea = construir_partida_con_linea(copias_cada=50)
        jugar_guardando_el_estado(juego, 12)

        self.assertEqual(linea.cantidad_de_copias(), 1)

        self.assertTrue(juego.rewind().accepted)

        self.assertEqual(linea.cantidad_de_copias(), 2)
        self.assertEqual(
            linea.copias()[-1].acciones, linea.cantidad_de_acciones()
        )

    def test_los_instantes_posteriores_a_un_pergamino_siguen_coincidiendo(self):
        """La prueba que justifica el anclaje del generador.

        Sin el anclaje, repetir las acciones desde una copia anterior
        consumiria numeros distintos de los que consumio la partida viva y
        esta prueba tiene que fallar.
        """
        juego, linea = construir_partida_con_linea(copias_cada=10)
        jugar_guardando_el_estado(juego, 15)

        self.assertTrue(juego.rewind().accepted)

        reales = []

        for _ in range(12):
            if juego.is_over:
                break
            reales.append((linea.cantidad_de_acciones(), estado_observable(juego)))
            if not juego.wait().accepted:
                break

        self.assertGreaterEqual(len(reales), 6)

        for numero, real in reales:
            with self.subTest(accion=numero):
                resumen = consultar_accion(juego, numero, reconstruir_desde_copia)
                self.assertEqual(estado_del_resumen(resumen), real)

    def test_varios_pergaminos_seguidos_dejan_la_linea_consistente(self):
        juego, linea = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 15)
        cuantas = linea.cantidad_de_acciones()
        usados = 0

        for _ in range(3):
            if juego.rewind().accepted:
                usados += 1

        self.assertGreater(usados, 0)
        self.assertEqual(linea.cantidad_de_acciones(), cuantas - usados)

        for copia in linea.copias():
            self.assertLessEqual(copia.acciones, linea.cantidad_de_acciones())

    def test_la_linea_llega_mas_atras_que_el_pergamino(self):
        """FR-013: el pergamino alcanza cinco acciones; la linea, el inicio."""
        juego, linea = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 20)

        self.assertGreater(linea.cantidad_de_acciones(), 5)
        self.assertEqual(juego.history.max_actions, 5)

        resumen = consultar_accion(juego, 1, reconstruir_desde_copia)

        self.assertIsNotNone(resumen.vida)


class CostoDeLaConsultaTest(unittest.TestCase):
    """Historia 4: consultar sigue siendo barato en una partida larga."""

    def test_ninguna_consulta_repite_mas_de_k_acciones(self):
        """FR-016: se cuenta cuantas repite, no se estima."""
        juego, linea = construir_partida_con_linea(copias_cada=10)
        jugar_guardando_el_estado(juego, 35)

        for numero in range(linea.cantidad_de_acciones() + 1):
            with self.subTest(accion=numero):
                resumen = consultar_accion(juego, numero, reconstruir_desde_copia)
                self.assertLessEqual(resumen.acciones_repetidas, 10)

    def test_con_una_copia_por_accion_no_se_repite_ninguna(self):
        juego, linea = construir_partida_con_linea(copias_cada=1)
        jugar_guardando_el_estado(juego, 12)

        for numero in range(linea.cantidad_de_acciones() + 1):
            resumen = consultar_accion(juego, numero, reconstruir_desde_copia)
            self.assertEqual(resumen.acciones_repetidas, 0)

    def test_con_una_sola_copia_las_consultas_siguen_siendo_correctas(self):
        """K mayor que el total: solo existe la copia inicial."""
        juego, linea = construir_partida_con_linea(copias_cada=10000)
        reales = jugar_guardando_el_estado(juego, 20)

        self.assertEqual(linea.cantidad_de_copias(), 1)

        for numero, real in enumerate(reales):
            with self.subTest(accion=numero):
                resumen = consultar_accion(juego, numero, reconstruir_desde_copia)
                self.assertEqual(estado_del_resumen(resumen), real)


class LaLineaSobreviveAlArchivoTest(unittest.TestCase):
    """Historia 5: guardar y cargar conserva la linea completa."""

    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.ruta = Path(self._carpeta.name) / "guardados" / "partida.cripta"

    def tearDown(self):
        self._carpeta.cleanup()

    def guardar_y_cargar(self, juego):
        AlmacenPartida(self.ruta).guardar(juego, versiones=("c", "1", "1"))

        return construir_juego_reversible(AlmacenPartida(self.ruta).cargar())

    def test_la_linea_viaja_completa(self):
        """FR-020."""
        juego, linea = construir_partida_con_linea(copias_cada=5)
        jugar_guardando_el_estado(juego, 18)

        cargado = self.guardar_y_cargar(juego)

        self.assertIsNotNone(cargado.timeline)
        self.assertEqual(
            cargado.timeline.cantidad_de_acciones(), linea.cantidad_de_acciones()
        )
        self.assertEqual(
            cargado.timeline.cantidad_de_copias(), linea.cantidad_de_copias()
        )
        self.assertEqual(cargado.timeline.copias_cada, linea.copias_cada)

    def test_consultar_despues_de_cargar_da_el_mismo_resumen(self):
        """FR-020: la promesa de «desde el inicio» sigue siendo cierta."""
        juego, _ = construir_partida_con_linea(copias_cada=5)
        reales = jugar_guardando_el_estado(juego, 18)

        cargado = self.guardar_y_cargar(juego)

        for numero, real in enumerate(reales):
            with self.subTest(accion=numero):
                antes = consultar_accion(juego, numero, reconstruir_desde_copia)
                despues = consultar_accion(cargado, numero, reconstruir_desde_copia)
                self.assertEqual(estado_del_resumen(antes), real)
                self.assertEqual(estado_del_resumen(despues), real)

    def test_la_linea_continua_al_seguir_jugando(self):
        """La partida cargada sigue registrando sin cortes."""
        juego, _ = construir_partida_con_linea(copias_cada=5)
        jugar_guardando_el_estado(juego, 12)

        cargado = self.guardar_y_cargar(juego)
        antes = cargado.timeline.cantidad_de_acciones()

        nuevas = jugar_guardando_el_estado(cargado, 6)

        self.assertGreater(cargado.timeline.cantidad_de_acciones(), antes)

        for desplazamiento, real in enumerate(nuevas):
            numero = antes + desplazamiento
            with self.subTest(accion=numero):
                resumen = consultar_accion(cargado, numero, reconstruir_desde_copia)
                self.assertEqual(estado_del_resumen(resumen), real)

    def test_las_copias_del_archivo_no_llevan_la_linea_dentro(self):
        """Si la llevaran, cada copia contendria las anteriores.

        El tamano creceria de forma exponencial con la cantidad de copias.
        """
        juego, linea = construir_partida_con_linea(copias_cada=2)
        jugar_guardando_el_estado(juego, 16)

        self.assertGreater(linea.cantidad_de_copias(), 5)

        tamanos = [len(copia.bloque) for copia in linea.copias()]

        self.assertLess(max(tamanos), 2 * min(tamanos))

    def test_un_archivo_de_una_version_anterior_se_rechaza(self):
        """FR-021: no se lee a medias."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 6)
        AlmacenPartida(self.ruta).guardar(juego, versiones=("c", "1", "1"))

        crudo = bytearray(self.ruta.read_bytes())
        crudo[8:10] = struct.pack("<H", VERSION_DEL_FORMATO - 1)
        self.ruta.write_bytes(bytes(crudo))

        with self.assertRaises(PartidaIncompatible) as error:
            AlmacenPartida(self.ruta).cargar()

        self.assertIn(str(VERSION_DEL_FORMATO), str(error.exception))


class ComandoYVistaTest(unittest.TestCase):
    """T015: el comando de consulta y la impresion del resumen."""

    def test_el_comando_acepta_las_dos_formas(self):
        """FR-003."""
        from controller.commands import HISTORY, parse_command

        por_instante = parse_command("historia 1500")
        self.assertEqual(por_instante.name, HISTORY)
        self.assertEqual(por_instante.argument, 1500)

        por_accion = parse_command("historia #10")
        self.assertEqual(por_accion.name, HISTORY)
        self.assertEqual(por_accion.argument, "#10")

    def test_el_comando_no_es_una_accion_del_juego(self):
        """FR-006: no entra en la bitacora de reproduccion."""
        from controller.commands import is_game_action, parse_command

        self.assertFalse(is_game_action(parse_command("historia 100")))

    def test_un_comando_mal_escrito_da_un_error_legible(self):
        from controller.commands import CommandError, parse_command

        for texto in ("historia", "historia xx", "historia #a", "historia 1 2"):
            with self.subTest(texto=texto):
                with self.assertRaises(CommandError):
                    parse_command(texto)

    def test_la_vista_imprime_el_resumen(self):
        """La vista decide como se ve; el modelo, que va adentro."""
        from view.console_view import ConsoleView

        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 12)
        resumen = consultar_accion(juego, 4, reconstruir_desde_copia)

        lineas = []
        vista = ConsoleView()
        vista._print = lineas.append

        vista.show_history(resumen)

        texto = chr(10).join(lineas)
        self.assertIn("Instante", texto)
        self.assertIn("Sala", texto)
        self.assertIn("Vida", texto)
        self.assertIn("Inventario", texto)
        self.assertIn("Efectos", texto)
        self.assertIn("Mapa conocido", texto)


class AvisosDelMotorAlMapaConocidoTest(unittest.TestCase):
    """Los avisos que la niebla de guerra necesita del motor.

    El modulo real es de Steven y vive en otra rama; aca se comprueba que el
    motor avisa en los momentos acordados, con un doble.
    """

    def _partida_con_mapa(self):
        doble = MapaConocidoDoble()
        juego, linea = construir_partida_con_linea()
        juego.known_map = doble
        doble.jugador_entro(juego.player.room_id, juego.torch_lit)

        return juego, doble

    def test_el_motor_avisa_cuando_el_jugador_entra_a_una_sala(self):
        juego, doble = self._partida_con_mapa()

        self.assertEqual(doble.salas_exploradas(), [1])

        self.assertTrue(juego.move("N").accepted)

        self.assertEqual(doble.salas_exploradas(), [1, 2])

    def test_una_partida_sin_niebla_no_falla_con_los_avisos(self):
        """El objeto nulo ignora los avisos, igual que _NoHistory."""
        juego, _ = construir_partida_con_linea()

        self.assertFalse(juego.known_map.disponible)
        self.assertTrue(juego.move("N").accepted)

    def test_la_vista_de_enemigos_dice_si_es_cazador(self):
        """Lo que Steven pidio para pintar el cazador distinto."""
        from model.enemy import Enemy

        juego, _ = construir_partida_con_linea()
        juego.enemies[0].behavior = Enemy.HUNTER
        juego.enemies[0].pursuit_range = 600
        juego.enemies[0].room_id = juego.player.room_id
        juego.enemies[1].room_id = juego.player.room_id

        vistos = {
            enemigo.actor_id: enemigo.is_hunter
            for enemigo in juego.visible_state().enemies
        }

        self.assertTrue(vistos["e-1"])
        self.assertFalse(vistos["e-2"])


class ContenidoPerezosoTest(unittest.TestCase):
    """El contenido de cada sala se descarga cuando el jugador va a entrar.

    En una partida real lo carga el controlador justo antes del movimiento, no
    el modelo. Si un punto de control se tomo cuando esa sala todavia no
    estaba cargada, repetir el movimiento al reconstruir lo rechaza y el
    resumen se queda en la sala anterior, sin dar ningun error.

    Las demas pruebas de este archivo no lo detectaban porque su cripta marca
    todas las salas como cargadas desde el inicio, que es mas permisivo que la
    realidad.
    """

    def partida_perezosa(self, copias_cada):
        """Como una partida real: solo la sala inicial viene cargada."""
        juego, linea = construir_partida_con_linea(copias_cada=copias_cada)

        for room_id in juego.room_map.room_ids():
            if room_id != juego.player.room_id:
                juego.room_map.room(room_id).content_loaded = False

        return juego, linea

    def caminar_cargando(self, juego, pasos):
        """Camina como el controlador: carga el contenido y despues mueve."""
        reales = []
        direccion = "N"

        for _ in range(pasos):
            if juego.is_over:
                break

            antes = estado_observable(juego)
            sala = juego.room_map.room(juego.player.room_id)
            salida = sala.exit_towards(direccion)

            if salida is not None:
                destino = juego.room_map.room(salida.destination)

                if not destino.content_loaded:
                    destino.content_loaded = True
                    juego.contenido_disponible(destino)
                    antes = estado_observable(juego)

                if juego.move(direccion).accepted:
                    reales.append((linea_actual(juego) - 1, antes))
                    continue

            direccion = "S" if direccion == "N" else "N"

            if juego.wait().accepted:
                reales.append((linea_actual(juego) - 1, antes))

        return reales

    def test_los_instantes_coinciden_con_carga_perezosa(self):
        """FR-023 con el contenido descargandose durante la partida."""
        juego, _ = self.partida_perezosa(copias_cada=10)
        reales = self.caminar_cargando(juego, 20)

        self.assertGreaterEqual(len(reales), 10)

        for numero, real in reales:
            with self.subTest(accion=numero):
                resumen = consultar_accion(juego, numero, reconstruir_desde_copia)
                self.assertEqual(estado_del_resumen(resumen), real)

    def test_cargar_contenido_fuerza_un_punto_de_control(self):
        """Es informacion nueva que la lista de acciones no puede reproducir."""
        juego, linea = self.partida_perezosa(copias_cada=10 ** 6)

        self.assertEqual(linea.cantidad_de_copias(), 1)

        self.caminar_cargando(juego, 6)

        self.assertGreater(linea.cantidad_de_copias(), 1)

    def test_avisar_sin_linea_de_tiempo_no_falla(self):
        juego, _ = construir_partida_con_linea()
        juego.timeline = None

        juego.contenido_disponible(juego.room_map.room(2))


def linea_actual(juego):
    return juego.timeline.cantidad_de_acciones()


class CasosDelApendiceBTest(unittest.TestCase):
    """Los dos casos del Apendice B que faltaban (FR-025 y FR-026)."""

    def test_varios_eventos_en_el_mismo_instante_cuentan_todos(self):
        """FR-026 y Apendice B: el estado es el posterior a todos ellos.

        Se busca un instante en el que el reloj haya procesado mas de un
        evento y se comprueba que el resumen refleja el estado despues de
        todos, no despues de algunos.
        """
        juego, linea = construir_partida_con_linea(copias_cada=10)
        reales = jugar_guardando_el_estado(juego, 25)

        instantes = [real[0] for real in reales]
        repetidos = [t for t in instantes if instantes.count(t) > 1]

        self.assertEqual(repetidos, [], "dos acciones no pueden compartir reloj")

        # Cada consulta tiene que coincidir con el estado real, y ese estado
        # real ya incluye todos los eventos que el motor proceso en ese
        # instante antes de devolverle el turno al jugador.
        for numero, real in enumerate(reales):
            with self.subTest(accion=numero):
                resumen = consultar_instante(juego, real[0], reconstruir_desde_copia)
                self.assertEqual(estado_del_resumen(resumen), real)

    def test_un_instante_con_eventos_y_decision_del_jugador(self):
        """FR-002 manda sobre FR-026 cuando coinciden: la decision no se toma."""
        juego, _ = construir_partida_con_linea(copias_cada=10)
        reales = jugar_guardando_el_estado(juego, 15)

        numero = len(reales) - 1
        instante = reales[numero][0]

        por_instante = consultar_instante(juego, instante, reconstruir_desde_copia)
        por_accion = consultar_accion(juego, numero, reconstruir_desde_copia)

        self.assertEqual(
            estado_del_resumen(por_instante), estado_del_resumen(por_accion)
        )
        self.assertEqual(por_instante.acciones_del_jugador, numero)

    def test_reproducir_hasta_despues_del_final_da_el_estado_final(self):
        """FR-025 y Apendice B: no se rechaza, se avisa."""
        juego, _ = construir_partida_con_linea(copias_cada=10)
        jugar_guardando_el_estado(juego, 15)
        final = estado_observable(juego)

        resumen = consultar_hasta(
            juego, juego.state.clock + 10 ** 6, reconstruir_desde_copia
        )

        self.assertEqual(estado_del_resumen(resumen), final)
        self.assertEqual(resumen.aviso, PARTIDA_TERMINO_ANTES)

    def test_reproducir_hasta_un_instante_valido_no_avisa_nada(self):
        juego, _ = construir_partida_con_linea(copias_cada=10)
        reales = jugar_guardando_el_estado(juego, 15)

        resumen = consultar_hasta(juego, reales[5][0], reconstruir_desde_copia)

        self.assertEqual(estado_del_resumen(resumen), reales[5])
        self.assertIsNone(resumen.aviso)

    def test_reproducir_hasta_el_instante_exacto_del_final_no_avisa(self):
        juego, _ = construir_partida_con_linea(copias_cada=10)
        jugar_guardando_el_estado(juego, 12)

        resumen = consultar_hasta(juego, juego.state.clock, reconstruir_desde_copia)

        self.assertIsNone(resumen.aviso)

    def test_reproducir_hasta_un_instante_invalido_si_se_rechaza(self):
        """FR-025 solo cambia el caso del futuro, no el de un dato malo."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 8)

        for invalido in (-1, "500", 1.5, None):
            with self.subTest(instante=invalido):
                with self.assertRaises(ConsultaRechazada):
                    consultar_hasta(juego, invalido, reconstruir_desde_copia)

    def test_en_partida_el_futuro_sigue_rechazandose(self):
        """FR-009 no cambia: las dos consultas son distintas a proposito."""
        juego, _ = construir_partida_con_linea()
        jugar_guardando_el_estado(juego, 8)

        with self.assertRaises(ConsultaRechazada):
            consultar_instante(
                juego, juego.state.clock + 1, reconstruir_desde_copia
            )


class InstanteEnMedioDeUnTramoTest(unittest.TestCase):
    """T023: un instante entre dos decisiones no puede traer el futuro.

    Lo reporto Steven. El tramo entre dos decisiones del jugador NO es
    indivisible: se puede consultar por la mitad, y los eventos que ocurren
    despues del instante pedido no deben aparecer.

    Las demas pruebas no lo detectaban porque consultaban instantes que
    coinciden con una decision del jugador, que es el caso facil.
    """

    def partida_con_enemigo_lento(self):
        """El enemigo ataca entre dos decisiones del jugador, no en ellas."""
        cuartos = []

        for numero in (1, 2):
            cuarto = Room(numero, f"Sala {numero}")
            cuarto.content_loaded = True
            cuartos.append(cuarto)

        puerta = Door(1, 2, closed=False, cost=100)
        cuartos[0].add_exit(Exit("N", 2, puerta))
        cuartos[1].add_exit(Exit("S", 1, puerta))

        mapa = RoomMap()

        for cuarto in cuartos:
            mapa.add(cuarto)

        estado = GameState(seed=2026)
        historial = History(estado)
        jugador = Player("p-1", "Heroe", 10 ** 6, 6, 0, 100, 1)
        jugador.inventory = Inventory(10, history=historial)

        # Velocidad 150: actua cada 66 unidades, asi que casi siempre golpea
        # en medio de un tramo del jugador y no en sus limites.
        enemigo = Enemy("e-1", "Rata", 500, 5, 1, 150, 1, Enemy.GUARDIAN)
        linea = LineaDeTiempo(copias_cada=5)

        juego = Game(
            estado,
            jugador,
            [enemigo],
            room_map=mapa,
            trail=PlayerTrail(historial),
            history=historial,
            event_queue=ReversibleEventQueue(historial),
            timeline=linea,
            snapshot=tomar_copia_del_estado,
        )

        return juego, linea

    def decisiones(self, juego, cuantas):
        """(reloj, vida) en cada decision del jugador."""
        tomadas = []

        for _ in range(cuantas):
            tomadas.append((juego.state.clock, juego.player.health))
            juego.wait()

        return tomadas

    def test_un_instante_en_medio_no_trae_los_eventos_posteriores(self):
        """El caso exacto que reporto Steven.

        El jugador decide cada 100 y el enemigo pega cada 66, asi que entre
        dos decisiones hay golpes. Un instante anterior al primer golpe del
        tramo tiene que dar la vida de la decision, no la de la siguiente.
        """
        juego, _ = self.partida_con_enemigo_lento()
        tomadas = self.decisiones(juego, 6)

        reloj, vida = tomadas[0]
        reloj_siguiente, vida_siguiente = tomadas[1]

        self.assertNotEqual(
            vida, vida_siguiente,
            "sin golpes entre las dos decisiones la prueba no compara nada",
        )

        a_la_mitad = reloj + (reloj_siguiente - reloj) // 3
        resumen = consultar_instante(juego, a_la_mitad, reconstruir_desde_copia)

        self.assertEqual(resumen.vida, vida)

    def test_cada_instante_intermedio_da_una_vida_que_no_decrece(self):
        """Recorre el tramo completo: la vida solo puede bajar al avanzar."""
        juego, _ = self.partida_con_enemigo_lento()
        tomadas = self.decisiones(juego, 6)

        anterior = None

        for instante in range(0, tomadas[-1][0] + 1, 10):
            resumen = consultar_instante(juego, instante, reconstruir_desde_copia)

            if anterior is not None:
                self.assertLessEqual(
                    resumen.vida, anterior,
                    f"la vida subio al avanzar hasta el instante {instante}",
                )

            anterior = resumen.vida

    def test_el_instante_de_una_decision_coincide_con_esa_decision(self):
        """Lo que ya funcionaba tiene que seguir funcionando."""
        juego, _ = self.partida_con_enemigo_lento()

        for reloj, vida in self.decisiones(juego, 6):
            with self.subTest(reloj=reloj):
                resumen = consultar_instante(juego, reloj, reconstruir_desde_copia)
                self.assertEqual(resumen.vida, vida)

    def test_el_tope_se_quita_despues_de_consultar(self):
        """El motor reconstruido es de usar y tirar, pero el tope no puede
        quedar puesto en el que se devuelve."""
        juego, _ = self.partida_con_enemigo_lento()

        for _ in range(8):
            juego.wait()

        consultar_instante(juego, 150, reconstruir_desde_copia)

        self.assertIsNone(juego._event_limit)


if __name__ == "__main__":
    unittest.main()
