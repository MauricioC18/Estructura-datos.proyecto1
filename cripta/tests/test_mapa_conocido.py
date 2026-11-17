"""Pruebas del mapa conocido (specs/003-niebla-ir-a).

Prueban la estructura sola, llamando a mano a los avisos que en la partida
dará el motor (jugador_entro, puerta_cambio). Cada prueba cita en su docstring
los requisitos que comprueba.
"""
import unittest

from model.game_state import GameState
from model.room import DEFAULT_EXIT_COST, Door, Exit, Room, RoomMap
from structures.history import History
from structures.mapa_conocido import (
    ABIERTA,
    AVISTADA,
    CERRADA,
    DESCONOCIDA,
    EXPLORADA,
    MapaConocido,
)


OPUESTA = (("N", "S"), ("S", "N"), ("E", "O"), ("O", "E"))


def opuesta(direccion):
    for una, otra in OPUESTA:
        if una == direccion:
            return otra
    raise ValueError(direccion)


def mapa_de_salas(*ids):
    room_map = RoomMap()
    for id_sala in ids:
        room_map.add(Room(id_sala, f"Sala {id_sala}"))
    return room_map


def conectar(room_map, id_a, id_b, direccion, cerrada=False, costo=DEFAULT_EXIT_COST):
    """Paso de doble sentido: una sola puerta compartida por las dos salidas."""
    puerta = Door(id_a, id_b, closed=cerrada, cost=costo)
    room_map.room(id_a).add_exit(Exit(direccion, id_b, puerta))
    room_map.room(id_b).add_exit(Exit(opuesta(direccion), id_a, puerta))
    return puerta


def puerta_entre(room_map, id_a, direccion):
    return room_map.room(id_a).exit_towards(direccion).door


def cruz():
    """Sala 1 al centro, con 2 al N, 3 al S (cerrada), 4 al E y 5 al O.
    Más allá: 2 -N- 6 y 4 -E- 7 (cerrada). 6 y 7 son las salas lejanas."""
    room_map = mapa_de_salas(1, 2, 3, 4, 5, 6, 7)
    conectar(room_map, 1, 2, "N")
    conectar(room_map, 1, 3, "S", cerrada=True)
    conectar(room_map, 1, 4, "E")
    conectar(room_map, 1, 5, "O")
    conectar(room_map, 2, 6, "N")
    conectar(room_map, 4, 7, "E", cerrada=True)
    return room_map


def historial():
    return History(GameState(seed=1))


class TestTresEstados(unittest.TestCase):
    """Historia 1: el jugador solo conoce lo que ha visto."""

    def setUp(self):
        self.room_map = mapa_de_salas(1, 2, 3, 4)
        conectar(self.room_map, 1, 2, "E")
        conectar(self.room_map, 2, 3, "E")
        conectar(self.room_map, 1, 4, "N")
        self.mapa = MapaConocido(self.room_map)

    def test_sin_explorar_nada_todo_es_desconocido(self):
        """FR-001: cada sala está en uno de tres estados; vacío, todas desconocidas."""
        for id_sala in (1, 2, 3, 4):
            self.assertEqual(self.mapa.estado_de_sala(id_sala), DESCONOCIDA)
        self.assertEqual(self.mapa.salas_exploradas(), [])

    def test_al_iniciar_la_sala_inicial_esta_explorada(self):
        """FR-002, FR-004 (Historia 1, escenario 1): la sala inicial explorada,
        los destinos de sus salidas avistados, el resto desconocido."""
        self.mapa.jugador_entro(1)

        self.assertEqual(self.mapa.estado_de_sala(1), EXPLORADA)
        self.assertEqual(self.mapa.estado_de_sala(2), AVISTADA)
        self.assertEqual(self.mapa.estado_de_sala(4), AVISTADA)
        self.assertEqual(self.mapa.estado_de_sala(3), DESCONOCIDA)

    def test_entrar_a_una_avistada_la_explora(self):
        """FR-003, FR-004 (Historia 1, escenario 2): la sala pasa a explorada y
        los destinos de sus salidas que no estaban explorados, a avistados."""
        self.mapa.jugador_entro(1)
        self.mapa.jugador_entro(2)

        self.assertEqual(self.mapa.estado_de_sala(2), EXPLORADA)
        self.assertEqual(self.mapa.estado_de_sala(3), AVISTADA)
        self.assertEqual(self.mapa.estado_de_sala(1), EXPLORADA)

    def test_una_avistada_no_es_explorada(self):
        """FR-005 (Historia 1, escenario 3): de una avistada no se conoce nada
        más que su existencia; no figura entre las exploradas."""
        self.mapa.jugador_entro(1)

        self.assertNotIn(2, self.mapa.salas_exploradas())
        self.assertFalse(self.mapa.esta_explorada(2))

    def test_salir_de_una_sala_no_la_desexplora(self):
        """FR-003 (Historia 1, escenario 4)."""
        self.mapa.jugador_entro(1)
        self.mapa.jugador_entro(2)
        self.mapa.jugador_entro(1)

        self.assertEqual(self.mapa.estado_de_sala(2), EXPLORADA)

    def test_las_exploradas_salen_en_orden_de_exploracion(self):
        """FR-017: el orden de exploración es determinista."""
        self.mapa.jugador_entro(1)
        self.mapa.jugador_entro(4)
        self.mapa.jugador_entro(1)
        self.mapa.jugador_entro(2)

        self.assertEqual(self.mapa.salas_exploradas(), [1, 4, 2])
        self.assertEqual(self.mapa.cantidad_de_exploradas(), 3)

    def test_avistada_por_dos_exploradas(self):
        """FR-004: una sala a la que llevan salidas de dos exploradas está avistada."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 3, "E")
        conectar(room_map, 2, 3, "N")
        conectar(room_map, 1, 2, "O")
        mapa = MapaConocido(room_map)

        mapa.jugador_entro(1)
        mapa.jugador_entro(2)

        self.assertEqual(mapa.estado_de_sala(3), AVISTADA)

    def test_un_paso_de_un_solo_sentido_no_avista_su_origen(self):
        """FR-004: avistada es destino de una salida de una explorada. Si la
        sala 6 tiene una salida hacia 1 sin vuelta, explorar 1 no avista 6."""
        room_map = mapa_de_salas(1, 6)
        puerta = Door(6, 1)
        room_map.room(6).add_exit(Exit("S", 1, puerta))
        mapa = MapaConocido(room_map)

        mapa.jugador_entro(1)

        self.assertEqual(mapa.estado_de_sala(6), DESCONOCIDA)

    def test_sala_inexistente_es_desconocida(self):
        """FR-001, FR-005: una sala que no existe no se conoce."""
        self.mapa.jugador_entro(1)

        self.assertEqual(self.mapa.estado_de_sala(999), DESCONOCIDA)


class TestMemoriaDePuertas(unittest.TestCase):
    """Historia 2: el mapa recuerda las puertas como las vio por última vez."""

    def setUp(self):
        self.room_map = mapa_de_salas(1, 2, 3)
        self.puerta_12 = conectar(self.room_map, 1, 2, "E")
        self.puerta_23 = conectar(self.room_map, 2, 3, "E", cerrada=True)
        self.mapa = MapaConocido(self.room_map)

    def test_al_entrar_observa_todas_las_puertas_de_la_sala(self):
        """FR-006 (Historia 2, escenario 1)."""
        self.mapa.jugador_entro(2)

        self.assertEqual(self.mapa.puerta_recordada(self.puerta_12), ABIERTA)
        self.assertEqual(self.mapa.puerta_recordada(self.puerta_23), CERRADA)

    def test_una_puerta_nunca_observada_es_desconocida(self):
        """FR-008."""
        self.mapa.jugador_entro(1)

        self.assertEqual(self.mapa.puerta_recordada(self.puerta_23), DESCONOCIDA)

    def test_cambio_lejos_del_jugador_no_se_observa(self):
        """FR-007 (Historia 2, escenario 2): la puerta cambia cuando el jugador
        no está en ninguna de sus dos salas; el mapa la sigue recordando abierta."""
        self.puerta_23.closed = False
        self.mapa.jugador_entro(2)
        self.mapa.jugador_entro(1)

        self.puerta_23.closed = True
        self.mapa.puerta_cambio(self.puerta_23, 1)

        self.assertEqual(self.mapa.puerta_recordada(self.puerta_23), ABIERTA)

    def test_volver_a_una_de_sus_salas_corrige_el_recuerdo(self):
        """FR-006, FR-007 (Historia 2, escenario 3)."""
        self.puerta_23.closed = False
        self.mapa.jugador_entro(2)
        self.mapa.jugador_entro(1)
        self.puerta_23.closed = True

        self.mapa.jugador_entro(2)

        self.assertEqual(self.mapa.puerta_recordada(self.puerta_23), CERRADA)

    def test_cambio_con_el_jugador_en_room_a_se_observa(self):
        """FR-006 (Historia 2, escenario 4)."""
        self.mapa.jugador_entro(2)
        self.puerta_23.closed = False

        self.mapa.puerta_cambio(self.puerta_23, 2)

        self.assertEqual(self.mapa.puerta_recordada(self.puerta_23), ABIERTA)

    def test_cambio_con_el_jugador_en_room_b_se_observa(self):
        """FR-006: cualquiera de las dos salas que conecta la puerta."""
        self.mapa.jugador_entro(3)
        self.puerta_23.closed = False

        self.mapa.puerta_cambio(self.puerta_23, 3)

        self.assertEqual(self.mapa.puerta_recordada(self.puerta_23), ABIERTA)

    def test_cambio_con_el_jugador_en_una_tercera_sala_no_se_observa(self):
        """FR-006, FR-007."""
        self.mapa.jugador_entro(2)
        self.mapa.jugador_entro(1)
        self.puerta_23.closed = False

        self.mapa.puerta_cambio(self.puerta_23, 1)

        self.assertEqual(self.mapa.puerta_recordada(self.puerta_23), CERRADA)

    def test_la_memoria_es_la_misma_desde_los_dos_lados(self):
        """FR-007: una sola puerta, un solo recuerdo, la mire desde donde la mire."""
        self.mapa.jugador_entro(1)
        clave_desde_1 = self.mapa.clave_de_puerta(self.puerta_12)
        self.mapa.jugador_entro(2)

        self.assertEqual(self.mapa.clave_de_puerta(self.puerta_12), clave_desde_1)
        self.assertEqual(self.mapa.puerta_recordada(self.puerta_12), ABIERTA)

    def test_dos_salidas_entre_las_mismas_salas_tienen_claves_distintas(self):
        """FR-007: dos puertas que unen las mismas dos salas se recuerdan por separado."""
        room_map = mapa_de_salas(1, 2)
        una = conectar(room_map, 1, 2, "E")
        otra = conectar(room_map, 1, 2, "N", cerrada=True)
        mapa = MapaConocido(room_map)

        mapa.jugador_entro(1)

        self.assertNotEqual(mapa.clave_de_puerta(una), mapa.clave_de_puerta(otra))
        self.assertEqual(mapa.puerta_recordada(una), ABIERTA)
        self.assertEqual(mapa.puerta_recordada(otra), CERRADA)

    def test_la_clave_de_una_puerta_es_un_entero(self):
        """FR-033: la tabla de puertas usa claves enteras."""
        self.assertIsInstance(self.mapa.clave_de_puerta(self.puerta_12), int)


class TestAntorcha(unittest.TestCase):
    """Historia 3: la antorcha ilumina las salas vecinas."""

    def setUp(self):
        self.room_map = cruz()
        self.mapa = MapaConocido(self.room_map)

    def test_explora_las_vecinas_por_salidas_abiertas_y_cerradas(self):
        """FR-009 (Historia 3, escenario 1, Apéndice B)."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        for id_sala in (1, 2, 3, 4, 5):
            self.assertEqual(self.mapa.estado_de_sala(id_sala), EXPLORADA)

    def test_los_destinos_de_las_vecinas_quedan_avistados(self):
        """FR-010 (Historia 3, escenario 3): se revelan nombre y salidas."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        self.assertEqual(self.mapa.estado_de_sala(6), AVISTADA)
        self.assertEqual(self.mapa.estado_de_sala(7), AVISTADA)

    def test_las_puertas_lejanas_de_las_vecinas_quedan_desconocidas(self):
        """FR-008 (Historia 3, escenario 4)."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        self.assertEqual(
            self.mapa.puerta_recordada(puerta_entre(self.room_map, 2, "N")), DESCONOCIDA
        )
        self.assertEqual(
            self.mapa.puerta_recordada(puerta_entre(self.room_map, 4, "E")), DESCONOCIDA
        )

    def test_las_puertas_de_la_sala_del_jugador_si_se_observan(self):
        """FR-006, FR-009: la puerta cerrada hacia 3 está en la sala del jugador."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        self.assertEqual(
            self.mapa.puerta_recordada(puerta_entre(self.room_map, 1, "S")), CERRADA
        )

    def test_sin_antorcha_solo_se_explora_la_sala(self):
        """FR-009 (Historia 3, escenario 5)."""
        self.mapa.jugador_entro(1)

        self.assertEqual(self.mapa.salas_exploradas(), [1])
        self.assertEqual(self.mapa.estado_de_sala(2), AVISTADA)

    def test_una_vecina_ya_explorada_no_cambia(self):
        """FR-009, FR-011: la antorcha no le quita ni le cambia nada."""
        self.mapa.jugador_entro(2)
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        self.assertEqual(self.mapa.salas_exploradas(), [2, 1, 3, 4, 5])

    def test_lo_explorado_con_antorcha_sigue_explorado_sin_ella(self):
        """FR-011: después de que la antorcha se apaga."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)
        self.mapa.jugador_entro(2, antorcha_encendida=False)

        self.assertEqual(self.mapa.estado_de_sala(5), EXPLORADA)

    def test_la_antorcha_no_cuenta_como_entrar(self):
        """FR-010: explorar con la antorcha no observa las puertas de la vecina,
        que es lo que sí haría entrar."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        self.assertEqual(
            self.mapa.puerta_recordada(puerta_entre(self.room_map, 2, "N")), DESCONOCIDA
        )
        self.mapa.jugador_entro(2)
        self.assertEqual(
            self.mapa.puerta_recordada(puerta_entre(self.room_map, 2, "N")), ABIERTA
        )


class TestReversion(unittest.TestCase):
    """Historia 6: el conocimiento se revierte con el pergamino."""

    def setUp(self):
        self.room_map = cruz()
        self.history = historial()
        self.mapa = MapaConocido(self.room_map, self.history)

    def test_lo_explorado_al_iniciar_no_se_puede_deshacer(self):
        """FR-002: sin intervalo abierto no se anota nada."""
        self.mapa.jugador_entro(1)
        self.history.begin_action()
        self.history.undo()

        self.assertEqual(self.mapa.estado_de_sala(1), EXPLORADA)
        self.assertEqual(self.history.recorded_changes(), 0)

    def test_deshacer_una_entrada_con_antorcha(self):
        """FR-015 (Historia 6, escenario 1, Apéndice B): la sala y las vecinas
        exploradas en esa entrada vuelven a su estado anterior."""
        self.mapa.jugador_entro(5)
        antes = [self.mapa.estado_de_sala(id_sala) for id_sala in range(1, 8)]

        self.history.begin_action()
        self.mapa.jugador_entro(1, antorcha_encendida=True)
        self.history.undo()

        despues = [self.mapa.estado_de_sala(id_sala) for id_sala in range(1, 8)]
        self.assertEqual(despues, antes)
        self.assertEqual(self.mapa.salas_exploradas(), [5])

    def test_deshacer_devuelve_el_recuerdo_de_una_puerta(self):
        """FR-015 (Historia 6, escenario 2)."""
        puerta_13 = puerta_entre(self.room_map, 1, "S")
        self.mapa.jugador_entro(1)

        self.history.begin_action()
        puerta_13.closed = False
        self.mapa.puerta_cambio(puerta_13, 1)
        self.assertEqual(self.mapa.puerta_recordada(puerta_13), ABIERTA)
        self.history.undo()

        self.assertEqual(self.mapa.puerta_recordada(puerta_13), CERRADA)

    def test_deshacer_borra_una_puerta_que_no_se_recordaba(self):
        """FR-015, FR-008: vuelve a desconocida."""
        puerta_26 = puerta_entre(self.room_map, 2, "N")
        self.mapa.jugador_entro(1)

        self.history.begin_action()
        self.mapa.jugador_entro(2)
        self.history.undo()

        self.assertEqual(self.mapa.puerta_recordada(puerta_26), DESCONOCIDA)

    def test_avistada_por_dos_sigue_avistada_al_deshacer_una(self):
        """FR-015: la sala 3 está avistada por 1 y por 2; deshacer la
        exploración de 2 no la desavista."""
        room_map = mapa_de_salas(1, 2, 3)
        conectar(room_map, 1, 3, "E")
        conectar(room_map, 2, 3, "N")
        conectar(room_map, 1, 2, "O")
        history = historial()
        mapa = MapaConocido(room_map, history)
        mapa.jugador_entro(1)

        history.begin_action()
        mapa.jugador_entro(2)
        history.undo()

        self.assertEqual(mapa.estado_de_sala(3), AVISTADA)
        self.assertEqual(mapa.estado_de_sala(2), AVISTADA)

    def test_deshacer_dos_acciones_seguidas(self):
        """FR-015: cada pergamino revierte su propio intervalo."""
        self.mapa.jugador_entro(1)
        self.history.begin_action()
        self.mapa.jugador_entro(2)
        self.history.begin_action()
        self.mapa.jugador_entro(6)

        self.history.undo()
        self.assertEqual(self.mapa.salas_exploradas(), [1, 2])
        self.history.undo()
        self.assertEqual(self.mapa.salas_exploradas(), [1])
        self.assertEqual(self.mapa.estado_de_sala(6), DESCONOCIDA)

    def test_una_entrada_con_antorcha_deja_pocas_anotaciones(self):
        """FR-035: una anotación por sala nueva y una por puerta cuyo recuerdo
        cambió. La sala 1 y sus cuatro vecinas son nuevas y sus cuatro puertas
        no se recordaban: nueve anotaciones."""
        self.history.begin_action()
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        self.assertEqual(self.history.recorded_changes(), 9)

    def test_volver_a_una_sala_conocida_no_anota_nada(self):
        """FR-035: si nada cambia, nada se anota."""
        self.mapa.jugador_entro(1)
        self.history.begin_action()
        self.mapa.jugador_entro(1)

        self.assertEqual(self.history.recorded_changes(), 0)

    def test_deshacer_no_cuenta_como_observar(self):
        """FR-015: mientras el historial deshace, nada se anota de nuevo."""
        puerta_13 = puerta_entre(self.room_map, 1, "S")
        self.mapa.jugador_entro(1)
        self.history.begin_action()
        self.history.assign(puerta_13, "closed", False)
        self.mapa.puerta_cambio(puerta_13, 1)

        self.history.undo()

        self.assertTrue(puerta_13.closed)
        self.assertEqual(self.mapa.puerta_recordada(puerta_13), CERRADA)
        self.assertEqual(self.history.recorded_changes(), 0)


class TestVecinasConocidas(unittest.TestCase):
    """Historia 4: el viaje solo usa lo que el jugador conoce."""

    def setUp(self):
        self.room_map = mapa_de_salas(1, 2, 3, 4)
        conectar(self.room_map, 1, 2, "E", costo=30)
        conectar(self.room_map, 1, 3, "S", cerrada=True)
        conectar(self.room_map, 1, 4, "N")
        self.mapa = MapaConocido(self.room_map)

    def test_solo_salidas_a_salas_exploradas(self):
        """FR-012, FR-023: 4 está avistada y 3 también; solo 2 está explorada.
        Devuelve id, costo de la salida y la salida misma."""
        self.mapa.jugador_entro(1)
        self.mapa.jugador_entro(2)
        self.mapa.jugador_entro(1)

        vecinas = self.mapa.vecinas_conocidas(1)

        self.assertEqual([(id_sala, costo) for id_sala, costo, _ in vecinas], [(2, 30)])
        self.assertIs(vecinas[0][2], self.room_map.room(1).exit_towards("E"))

    def test_con_antorcha_las_vecinas_por_puertas_abiertas(self):
        """FR-012, FR-023: con todo explorado, salen 4 y 2 en orden N, S, E, O;
        3 no, porque su puerta se recuerda cerrada."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        vecinas = [(id_sala, costo) for id_sala, costo, _ in self.mapa.vecinas_conocidas(1)]

        self.assertEqual(vecinas, [(4, 100), (2, 30)])

    def test_una_puerta_desconocida_no_se_usa_aunque_este_abierta(self):
        """FR-012, FR-023: las salas están exploradas pero el jugador nunca
        observó la puerta 2-5, que en realidad está abierta."""
        room_map = mapa_de_salas(1, 2, 5)
        conectar(room_map, 1, 2, "E")
        conectar(room_map, 2, 5, "E")
        mapa = MapaConocido(room_map)

        mapa.importar([1, 2, 5], [])

        self.assertEqual(mapa.vecinas_conocidas(2), [])

    def test_la_salida_cerrada_que_se_recuerda_cerrada_no_se_usa(self):
        """FR-027: no se pasa por puertas cerradas aunque haya llave."""
        self.mapa.jugador_entro(1, antorcha_encendida=True)

        destinos = [id_sala for id_sala, _, _ in self.mapa.vecinas_conocidas(1)]

        self.assertNotIn(3, destinos)

    def test_una_sala_no_explorada_no_tiene_vecinas_conocidas(self):
        """FR-012."""
        self.assertEqual(self.mapa.vecinas_conocidas(1), [])


class TestExportarImportar(unittest.TestCase):
    """Historia 6, escenario 3: el conocimiento se guarda y se carga."""

    def test_ida_y_vuelta(self):
        """FR-014: el conocimiento importado es idéntico al exportado."""
        room_map = cruz()
        original = MapaConocido(room_map)
        original.jugador_entro(1, antorcha_encendida=True)
        original.jugador_entro(2)
        puerta_13 = puerta_entre(room_map, 1, "S")
        exploradas, puertas = original.exportar()

        copia = MapaConocido(room_map)
        copia.importar(exploradas, puertas)

        self.assertEqual(copia.salas_exploradas(), original.salas_exploradas())
        for id_sala in range(1, 8):
            self.assertEqual(copia.estado_de_sala(id_sala), original.estado_de_sala(id_sala))
        for id_sala in range(1, 8):
            for salida in room_map.room(id_sala).exits():
                self.assertEqual(
                    copia.puerta_recordada(salida.door),
                    original.puerta_recordada(salida.door),
                )
        self.assertEqual(copia.puerta_recordada(puerta_13), CERRADA)

    def test_exporta_listas_planas_ordenadas(self):
        """FR-014: exploradas en orden de exploración; puertas por clave creciente."""
        room_map = cruz()
        mapa = MapaConocido(room_map)
        mapa.jugador_entro(4)
        mapa.jugador_entro(1)

        exploradas, puertas = mapa.exportar()

        self.assertEqual(exploradas, [4, 1])
        claves = [clave for clave, _ in puertas]
        self.assertEqual(claves, sorted(claves))
        for clave, abierta in puertas:
            self.assertIsInstance(clave, int)
            self.assertIsInstance(abierta, bool)

    def test_exportar_vacio(self):
        """FR-014: sin conocimiento, dos listas vacías."""
        self.assertEqual(MapaConocido(cruz()).exportar(), ([], []))

    def test_importar_no_anota_nada(self):
        """FR-014: cargar no es una acción del jugador."""
        room_map = cruz()
        history = historial()
        mapa = MapaConocido(room_map, history)
        history.begin_action()

        mapa.importar([1, 2], [])

        self.assertEqual(history.recorded_changes(), 0)

    def test_importar_reemplaza_lo_que_habia(self):
        """FR-014."""
        room_map = cruz()
        mapa = MapaConocido(room_map)
        mapa.jugador_entro(5)

        mapa.importar([1], [])

        self.assertEqual(mapa.salas_exploradas(), [1])
        self.assertEqual(mapa.estado_de_sala(5), AVISTADA)

    def test_importar_rechaza_una_sala_repetida(self):
        """FR-014: unos datos con la misma sala dos veces están dañados."""
        with self.assertRaises(ValueError):
            MapaConocido(cruz()).importar([1, 1], [])

    def test_despues_de_importar_se_puede_deshacer_lo_nuevo(self):
        """FR-014, FR-015: lo importado es la base; lo explorado después se revierte."""
        room_map = cruz()
        history = historial()
        mapa = MapaConocido(room_map, history)
        mapa.importar([1], [])

        history.begin_action()
        mapa.jugador_entro(2)
        history.undo()

        self.assertEqual(mapa.salas_exploradas(), [1])



class TestRecuerdoPorLado(unittest.TestCase):
    """Mejora (a) del plan: el recuerdo se guarda bajo la clave de cada lado."""

    def test_observada_desde_room_b_sirve_desde_room_a(self):
        """FR-007, FR-023: una sola puerta, el mismo recuerdo desde los dos lados."""
        room_map = mapa_de_salas(1, 2)
        puerta = conectar(room_map, 1, 2, "E")
        mapa = MapaConocido(room_map)
        mapa.importar([1, 2], [])

        mapa.puerta_cambio(puerta, 2)

        self.assertEqual([v for v, _, _ in mapa.vecinas_conocidas(1)], [2])
        self.assertEqual([v for v, _, _ in mapa.vecinas_conocidas(2)], [1])
        self.assertEqual(mapa.puerta_recordada(puerta), ABIERTA)

    def test_un_cambio_actualiza_los_dos_lados(self):
        """FR-006, FR-007: al cerrarse con el jugador presente, ninguno de los
        dos lados la ofrece como vecina."""
        room_map = mapa_de_salas(1, 2)
        puerta = conectar(room_map, 1, 2, "E")
        mapa = MapaConocido(room_map)
        mapa.jugador_entro(1)
        mapa.jugador_entro(2)

        puerta.closed = True
        mapa.puerta_cambio(puerta, 2)

        self.assertEqual(mapa.vecinas_conocidas(1), [])
        self.assertEqual(mapa.vecinas_conocidas(2), [])

    def test_deshacer_restaura_los_dos_lados(self):
        """FR-015: la inversa devuelve las dos entradas."""
        room_map = mapa_de_salas(1, 2)
        puerta = conectar(room_map, 1, 2, "E")
        history = historial()
        mapa = MapaConocido(room_map, history)
        mapa.jugador_entro(1)
        mapa.jugador_entro(2)

        history.begin_action()
        puerta.closed = True
        mapa.puerta_cambio(puerta, 1)
        history.undo()

        self.assertEqual([v for v, _, _ in mapa.vecinas_conocidas(1)], [2])
        self.assertEqual([v for v, _, _ in mapa.vecinas_conocidas(2)], [1])

    def test_un_paso_de_un_solo_sentido_tiene_una_sola_entrada(self):
        """FR-007, FR-014: sin salida de vuelta, un solo lado que recordar."""
        room_map = mapa_de_salas(1, 6)
        puerta = Door(6, 1)
        room_map.room(6).add_exit(Exit("S", 1, puerta))
        mapa = MapaConocido(room_map)

        mapa.jugador_entro(6)

        self.assertEqual(mapa.puerta_recordada(puerta), ABIERTA)
        self.assertEqual(len(mapa.exportar()[1]), 1)

    def test_exportar_da_un_par_por_puerta(self):
        """FR-014: aunque se guarden dos lados, se exporta una vez cada puerta."""
        room_map = cruz()
        mapa = MapaConocido(room_map)
        mapa.jugador_entro(1)

        exploradas, puertas = mapa.exportar()

        self.assertEqual(len(puertas), 4)
        for clave, _ in puertas:
            self.assertEqual(clave // 4, 1)

    def test_importar_una_clave_que_no_es_de_ninguna_salida(self):
        """FR-014: datos dañados se rechazan."""
        with self.assertRaises(ValueError):
            MapaConocido(cruz()).importar([1], [(1 * 4 + 3 + 400, True)])


if __name__ == "__main__":
    unittest.main()
