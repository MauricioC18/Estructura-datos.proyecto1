"""
Pruebas de GrafoSalas y del recorrido en anchura (BFS).

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import unittest

from structures.grafo_salas import GrafoSalas, construir_grafo_desde_esqueleto
from tests.datos_cripta_01 import SALAS_CRIPTA_01, salas_de_cuadricula


def distancia_en_cuadricula(id_a, id_b, ancho):
    fila_a, columna_a = divmod(id_a - 1, ancho)
    fila_b, columna_b = divmod(id_b - 1, ancho)
    return abs(fila_a - fila_b) + abs(columna_a - columna_b)


class PruebasGrafoSalas(unittest.TestCase):

    def setUp(self):
        self.grafo = construir_grafo_desde_esqueleto(SALAS_CRIPTA_01)

    def test_construccion_desde_el_esqueleto_real(self):
        self.assertEqual(self.grafo.cantidad_de_salas(), 6)
        self.assertEqual(self.grafo.ids_de_salas(), [1, 2, 3, 4, 5, 6])

    def test_vecinos_en_orden_n_s_e_o(self):
        # La sala 2 declara S→1, N→3, E→5; el grafo las ordena N, S, E, O.
        self.assertEqual(self.grafo.vecinos(2), [3, 1, 5])
        self.assertEqual(self.grafo.vecinos(1), [2])

    def test_incluye_salidas_cerradas(self):
        self.assertIn(5, self.grafo.vecinos(2))  # cerrada con llave de bronce
        self.assertIn(6, self.grafo.vecinos(4))  # cerrada con llave negra

    def test_sala_desconocida(self):
        with self.assertRaises(ValueError):
            self.grafo.vecinos(99)
        with self.assertRaises(ValueError):
            self.grafo.salas_en_orden_de_distancia(99, 10)

    def test_sala_repetida_o_id_invalido(self):
        grafo = GrafoSalas()
        grafo.agregar_sala(1, [])
        with self.assertRaises(ValueError):
            grafo.agregar_sala(1, [])
        with self.assertRaises(ValueError):
            grafo.agregar_sala("2", [])

    def test_sala_sin_salidas(self):
        grafo = construir_grafo_desde_esqueleto([{"id": 7, "nombre": "Aislada"}])
        self.assertEqual(grafo.vecinos(7), [])
        self.assertEqual(grafo.salas_en_orden_de_distancia(7, 10), [7])


class PruebasRecorridoEnAnchura(unittest.TestCase):

    def setUp(self):
        self.grafo = construir_grafo_desde_esqueleto(SALAS_CRIPTA_01)

    def test_orden_por_distancia_en_cripta_01(self):
        # Distancias desde 1: 2 a 1 paso; 3 y 5 a 2; 4 a 3; 6 a 4.
        self.assertEqual(self.grafo.salas_en_orden_de_distancia(1, 10), [1, 2, 3, 5, 4, 6])

    def test_limite_de_cantidad(self):
        self.assertEqual(self.grafo.salas_en_orden_de_distancia(1, 3), [1, 2, 3])

    def test_filtro_no_corta_el_recorrido(self):
        # Excluir la sala 2 no impide llegar a las que están detrás de ella.
        resultado = self.grafo.salas_en_orden_de_distancia(1, 10, lambda sala: sala != 2)
        self.assertEqual(resultado, [1, 3, 5, 4, 6])

    def test_filtro_que_excluye_todo(self):
        self.assertEqual(self.grafo.salas_en_orden_de_distancia(1, 10, lambda sala: False), [])

    def test_salida_hacia_sala_inexistente_se_ignora(self):
        grafo = construir_grafo_desde_esqueleto([
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2}, "S": {"sala": 99}}},
            {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1}}},
        ])
        self.assertEqual(grafo.salas_en_orden_de_distancia(1, 10), [1, 2])

    def test_cuadricula_grande_en_orden_de_distancia(self):
        ancho = 20
        grafo = construir_grafo_desde_esqueleto(salas_de_cuadricula(ancho, 20))
        origen = 7 * ancho + 8  # una sala del interior
        resultado = grafo.salas_en_orden_de_distancia(origen, 40)
        self.assertEqual(len(resultado), 40)
        self.assertEqual(resultado[0], origen)
        distancias = [distancia_en_cuadricula(origen, sala, ancho) for sala in resultado]
        for posicion in range(1, len(distancias)):
            self.assertLessEqual(distancias[posicion - 1], distancias[posicion])
        self.assertEqual(len(set(resultado)), 40)  # sin repetidas

    def test_es_determinista(self):
        grafo = construir_grafo_desde_esqueleto(salas_de_cuadricula(15, 15))
        self.assertEqual(grafo.salas_en_orden_de_distancia(100, 30),
                         grafo.salas_en_orden_de_distancia(100, 30))


if __name__ == "__main__":
    unittest.main()
