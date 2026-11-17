"""La sala actual se muestra según el conocimiento del jugador (specs/003-niebla-ir-a, T032, T035).

Cada prueba cita en su docstring los requisitos que comprueba.
"""
import io
import unittest

from controller.application import ExitView, room_view
from structures.mapa_conocido import ABIERTA, CERRADA
from model.enemy import Enemy
from tests.test_ir_a import conectar, guardian, mapa_de_salas
from tests.test_niebla import antorcha, partida_con_niebla
from view.console_view import ConsoleView


def salidas_por_direccion(vista):
    return [(salida.direction, salida) for salida in vista.exits]


def buscar(vista, direccion):
    for una, salida in salidas_por_direccion(vista):
        if una == direccion:
            return salida
    raise AssertionError(direccion)


class TestSalaActual(unittest.TestCase):

    def setUp(self):
        # 1 -E- 2 -E- 3, y 1 -S- 4 con la puerta cerrada.
        self.room_map = mapa_de_salas(1, 2, 3, 4)
        conectar(self.room_map, 1, 2, "E", costo=40)
        conectar(self.room_map, 2, 3, "E")
        conectar(self.room_map, 1, 4, "S", cerrada=True, llave="itm_llave")

    def test_destinos_avistados_sin_id_y_puertas_recordadas(self):
        """FR-005, FR-020: al empezar, las vecinas solo están avistadas y no
        muestran su id; cada puerta trae su estado recordado y su costo."""
        game, mapa = partida_con_niebla(self.room_map)

        vista = room_view(game, mapa)

        self.assertEqual(buscar(vista, "E"), ExitView("E", None, ABIERTA, 40))
        self.assertEqual(buscar(vista, "S"), ExitView("S", None, CERRADA, 100))

    def test_un_destino_explorado_muestra_su_id(self):
        """FR-005, FR-020: después de volver de la sala 2, esa salida ya
        muestra el id del destino."""
        game, mapa = partida_con_niebla(self.room_map)
        game.move("E")
        game.move("O")

        vista = room_view(game, mapa)

        self.assertEqual(buscar(vista, "E").destination, 2)
        self.assertIsNone(buscar(vista, "S").destination)

    def test_lo_que_se_muestra_no_sale_de_la_cripta_completa(self):
        """FR-012, FR-037: encender la antorcha no revela el id de la vecina;
        al entrar a la sala 2 con la antorcha, la sala 3 queda explorada sin
        que el jugador haya entrado, y su salida ya muestra el id."""
        game, mapa = partida_con_niebla(self.room_map, objetos=[antorcha()])
        game.use_item()

        vista_en_1 = room_view(game, mapa)
        self.assertIsNone(buscar(vista_en_1, "E").destination)

        game.move("E")
        vista_en_2 = room_view(game, mapa)

        self.assertEqual(buscar(vista_en_2, "E").destination, 3)
        self.assertEqual(buscar(vista_en_2, "O").destination, 1)

    def test_sin_mapa_conocido_se_muestra_el_estado_real(self):
        """Una partida sin niebla de guerra sigue mostrando sus salidas."""
        game, _ = partida_con_niebla(self.room_map, con_mapa=False)

        vista = room_view(game)

        self.assertEqual(buscar(vista, "E"), ExitView("E", 2, ABIERTA, 40))
        self.assertEqual(buscar(vista, "S"), ExitView("S", 4, CERRADA, 100))

    def test_la_consola_muestra_costos_estado_y_avistadas(self):
        """FR-020 (T035): la línea de salidas lleva el costo, la puerta
        cerrada y «hay algo en esa direccion» para un destino avistado."""
        game, mapa = partida_con_niebla(self.room_map)
        salida = io.StringIO()

        ConsoleView(output=salida).show_room(room_view(game, mapa))

        texto = salida.getvalue()
        self.assertIn("E->hay algo en esa direccion (costo 40)", texto)
        self.assertIn("S->hay algo en esa direccion (costo 100) (cerrada)", texto)
        self.assertNotIn("->2", texto)


class TestCazadorEnLaVista(unittest.TestCase):

    def test_el_cazador_se_distingue_con_el_motor_real(self):
        """FR-021: en la sala del jugador, el cazador lleva su marca y el
        guardián no, partiendo del estado visible que arma el motor."""
        room_map = mapa_de_salas(1, 2)
        conectar(room_map, 1, 2, "E")
        cazador = Enemy(
            actor_id="e-1", name="Sabueso", max_health=10, attack=1, defense=0,
            speed=100, room_id=1, behavior=Enemy.HUNTER, pursuit_range=300,
        )
        game, _ = partida_con_niebla(room_map, [cazador, guardian(1, "e-2")])
        salida = io.StringIO()

        ConsoleView(output=salida).show_state(game.visible_state())

        lineas = salida.getvalue().split("\n")
        del_cazador = [linea for linea in lineas if "e-1" in linea]
        del_guardian = [linea for linea in lineas if "e-2" in linea]
        self.assertEqual(len(del_cazador), 1)
        self.assertEqual(len(del_guardian), 1)
        self.assertIn("cazador", del_cazador[0])
        self.assertNotIn("cazador", del_guardian[0])


if __name__ == "__main__":
    unittest.main()
