"""Pruebas de la busqueda de costos minimos (FR-004, FR-007, FR-008, FR-010, FR-017).

Los grafos se arman a mano, sin tocar el modelo: la busqueda solo necesita un
proveedor de vecinas, asi que se puede probar el algoritmo aparte del juego.
"""
import unittest

from structures.rutas_mas_baratas import RutasMasBaratas


def proveedor(aristas, cerradas=()):
    """Proveedor de vecinas sobre una lista de aristas sin direccion.

    aristas: tuplas (a, b, costo). cerradas: las que no se deben contar, para
    probar que una puerta cerrada no da paso (FR-010).
    """
    def vecinas_abiertas(id_sala):
        encontradas = []

        for posicion, (a, b, costo) in enumerate(aristas):
            if posicion in cerradas:
                continue
            if a == id_sala:
                encontradas.append((b, costo, (a, b, costo)))
            elif b == id_sala:
                encontradas.append((a, costo, (b, a, costo)))

        return encontradas

    return vecinas_abiertas


class RutasMasBaratasTest(unittest.TestCase):

    def test_una_sola_sala_queda_a_distancia_cero_y_sin_primer_paso(self):
        rutas = RutasMasBaratas(proveedor([]), origen=1)

        self.assertEqual(rutas.distancia_a(1), 0)
        self.assertIsNone(rutas.primer_paso_desde(1))

    def test_suma_el_costo_de_cada_arista_del_camino(self):
        """FR-004: el costo minimo es la suma de los costos recorridos."""
        rutas = RutasMasBaratas(
            proveedor([(1, 2, 70), (2, 3, 30)]),
            origen=1,
        )

        self.assertEqual(rutas.distancia_a(2), 70)
        self.assertEqual(rutas.distancia_a(3), 100)

    def test_mas_aristas_y_menor_costo_le_gana_a_menos_aristas_y_mayor_costo(self):
        """FR-004 y SC-001: cuenta el costo, no la cantidad de salas.

        Del 1 al 5 hay dos caminos: uno de dos aristas que cuesta 500 y uno de
        cuatro que cuesta 200.
        """
        aristas = [
            (1, 9, 250),
            (9, 5, 250),
            (1, 2, 50),
            (2, 3, 50),
            (3, 4, 50),
            (4, 5, 50),
        ]
        rutas = RutasMasBaratas(proveedor(aristas), origen=5)

        self.assertEqual(rutas.distancia_a(1), 200)
        self.assertEqual(rutas.primer_paso_desde(1), (1, 2, 50))

    def test_el_corte_deja_fuera_lo_que_pasa_del_presupuesto(self):
        """FR-017: no se expande mas alla del corte."""
        aristas = [(1, 2, 100), (2, 3, 100), (3, 4, 100)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=1, corte=200)

        self.assertEqual(rutas.distancia_a(3), 200)
        self.assertTrue(rutas.alcanza(3))
        self.assertIsNone(rutas.distancia_a(4))
        self.assertFalse(rutas.alcanza(4))

    def test_una_sala_justo_en_el_corte_queda_dentro(self):
        rutas = RutasMasBaratas(proveedor([(1, 2, 600)]), origen=1, corte=600)

        self.assertEqual(rutas.distancia_a(2), 600)

    def test_una_sala_un_paso_mas_alla_del_corte_queda_fuera(self):
        rutas = RutasMasBaratas(proveedor([(1, 2, 601)]), origen=1, corte=600)

        self.assertIsNone(rutas.distancia_a(2))

    def test_el_corte_no_esconde_el_primer_paso_de_una_sala_que_si_entro(self):
        """Si una sala entro, la vecina de su ruta optima esta mas cerca."""
        aristas = [(1, 2, 100), (2, 3, 100)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=1, corte=200)

        self.assertEqual(rutas.primer_paso_desde(3), (3, 2, 100))

    def test_desempata_por_la_vecina_de_menor_id(self):
        """FR-008 y SC-002: dos vecinas empatadas, gana la de menor id.

        Desde la sala 1 hay dos rutas de costo 200 hacia el origen 9: una por
        la sala 4 y otra por la sala 7.
        """
        aristas = [(1, 7, 100), (7, 9, 100), (1, 4, 100), (4, 9, 100)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=9)

        self.assertEqual(rutas.distancia_a(1), 200)
        self.assertEqual(rutas.primer_paso_desde(1), (1, 4, 100))

    def test_el_desempate_no_depende_del_orden_de_expansion(self):
        """FR-008: el id correcto no coincide con el orden del monticulo.

        La sala 2 se asienta antes que la 8, porque esta mas cerca del origen,
        pero las dos empiezan rutas de costo 300 desde la sala 1. Una
        implementacion que se quedara con la primera vecina asentada elegiria
        la 8; la regla del enunciado manda la 2.
        """
        aristas = [(1, 8, 100), (8, 5, 200), (1, 2, 250), (2, 5, 50)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=5)

        self.assertEqual(rutas.distancia_a(8), 200)
        self.assertEqual(rutas.distancia_a(2), 50)
        self.assertEqual(rutas.distancia_a(1), 300)
        self.assertEqual(rutas.primer_paso_desde(1), (1, 2, 250))

    def test_el_desempate_se_cumple_con_muchas_rutas_de_igual_costo(self):
        """FR-008: cuatro vecinas empatadas, gana la de menor id."""
        aristas = []
        for intermedia in (12, 3, 40, 7):
            aristas.append((1, intermedia, 100))
            aristas.append((intermedia, 99, 100))

        rutas = RutasMasBaratas(proveedor(aristas), origen=99)

        self.assertEqual(rutas.distancia_a(1), 200)
        self.assertEqual(rutas.primer_paso_desde(1), (1, 3, 100))

    def test_entre_dos_salidas_hacia_la_misma_vecina_cuenta_la_mas_barata(self):
        """FR-008: la vecina es la misma, asi que decide el costo."""
        aristas = [(1, 2, 400), (1, 2, 90), (2, 3, 10)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=3)

        self.assertEqual(rutas.distancia_a(1), 100)
        self.assertEqual(rutas.primer_paso_desde(1), (1, 2, 90))

    def test_una_arista_cerrada_no_da_paso(self):
        """FR-010: solo cuentan las salidas abiertas."""
        aristas = [(1, 2, 10), (1, 3, 500), (3, 2, 500)]
        rutas = RutasMasBaratas(proveedor(aristas, cerradas=(0,)), origen=2)

        self.assertEqual(rutas.distancia_a(1), 1000)
        self.assertEqual(rutas.primer_paso_desde(1), (1, 3, 500))

    def test_un_grafo_partido_en_dos_deja_el_otro_lado_sin_distancia(self):
        aristas = [(1, 2, 10), (8, 9, 10)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=1)

        self.assertEqual(rutas.distancia_a(2), 10)
        self.assertIsNone(rutas.distancia_a(8))
        self.assertIsNone(rutas.primer_paso_desde(8))

    def test_un_corte_de_cero_solo_alcanza_el_origen(self):
        rutas = RutasMasBaratas(proveedor([(1, 2, 1)]), origen=1, corte=0)

        self.assertEqual(rutas.distancia_a(1), 0)
        self.assertIsNone(rutas.distancia_a(2))

    def test_costos_de_uno_y_costos_muy_grandes(self):
        aristas = [(1, 2, 1), (2, 3, 10 ** 9)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=1)

        self.assertEqual(rutas.distancia_a(2), 1)
        self.assertEqual(rutas.distancia_a(3), 10 ** 9 + 1)

    def test_un_ciclo_no_deja_la_busqueda_dando_vueltas(self):
        aristas = [(1, 2, 10), (2, 3, 10), (3, 1, 10)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=1)

        self.assertEqual(rutas.distancia_a(2), 10)
        self.assertEqual(rutas.distancia_a(3), 10)

    def test_mejora_una_distancia_ya_tentativa(self):
        """El camino caro se descubre primero y luego aparece el barato."""
        aristas = [(1, 4, 500), (1, 2, 10), (2, 3, 10), (3, 4, 10)]
        rutas = RutasMasBaratas(proveedor(aristas), origen=1)

        self.assertEqual(rutas.distancia_a(4), 30)

    def test_rechaza_un_corte_que_no_es_entero_o_es_negativo(self):
        with self.assertRaises(ValueError):
            RutasMasBaratas(proveedor([]), origen=1, corte=-1)

        with self.assertRaises(ValueError):
            RutasMasBaratas(proveedor([]), origen=1, corte="600")

        with self.assertRaises(ValueError):
            RutasMasBaratas(proveedor([]), origen=1, corte=True)


def proveedor_dirigido(aristas):
    """Proveedor de un grafo DIRIGIDO: devuelve (entrantes, salientes).

    entrantes(v) da las aristas que llegan a v, que es por donde se expande
    la busqueda desde el origen; salientes(u) da las que salen de u, que es
    por donde se da el primer paso.
    """
    def entrantes(id_sala):
        return [
            (a, costo, (a, b, costo))
            for a, b, costo in aristas
            if b == id_sala
        ]

    def salientes(id_sala):
        return [
            (b, costo, (a, b, costo))
            for a, b, costo in aristas
            if a == id_sala
        ]

    return entrantes, salientes


class ParadaAnticipadaConSalidasDirigidasTest(unittest.TestCase):
    """parar_en y salidas_de se pueden usar juntos.

    El argumento de la parada anticipada no depende de por donde se expanda la
    busqueda: solo usa que Dijkstra asienta en orden no decreciente de
    distancia y que todo costo es al menos 1.
    """

    def test_el_primer_paso_es_el_mismo_con_parada_y_sin_ella(self):
        aristas = [(1, 4, 50), (4, 9, 50), (9, 7, 1), (7, 1, 1)]
        entrantes, salientes = proveedor_dirigido(aristas)

        completa = RutasMasBaratas(entrantes, 9, salidas_de=salientes)
        con_parada = RutasMasBaratas(
            entrantes, 9, parar_en=1, salidas_de=salientes
        )

        self.assertEqual(completa.distancia_a(1), 100)
        self.assertEqual(con_parada.distancia_a(1), 100)
        self.assertEqual(
            completa.primer_paso_desde(1), con_parada.primer_paso_desde(1)
        )
        self.assertEqual(con_parada.primer_paso_desde(1), (1, 4, 50))

    def test_el_desempate_se_cumple_con_parada_y_salidas_dirigidas(self):
        aristas = [(1, 7, 100), (7, 9, 100), (1, 4, 100), (4, 9, 100)]
        entrantes, salientes = proveedor_dirigido(aristas)

        rutas = RutasMasBaratas(entrantes, 9, parar_en=1, salidas_de=salientes)

        self.assertEqual(rutas.primer_paso_desde(1), (1, 4, 100))

    def test_una_sala_no_asentada_se_rechaza_en_vez_de_mentir(self):
        aristas = [(1, 2, 10), (2, 9, 10), (3, 9, 500)]
        entrantes, salientes = proveedor_dirigido(aristas)

        rutas = RutasMasBaratas(entrantes, 9, parar_en=2, salidas_de=salientes)

        self.assertTrue(rutas.se_detuvo())
        self.assertTrue(rutas.esta_asentada(2))

        with self.assertRaises(ValueError):
            rutas.primer_paso_desde(3)

        with self.assertRaises(ValueError):
            rutas.distancia_a(3)

    def test_si_la_sala_nunca_se_alcanza_la_busqueda_termina_entera(self):
        aristas = [(1, 2, 10), (2, 9, 10)]
        entrantes, salientes = proveedor_dirigido(aristas)

        rutas = RutasMasBaratas(entrantes, 9, parar_en=77, salidas_de=salientes)

        self.assertFalse(rutas.se_detuvo())
        self.assertEqual(rutas.distancia_a(1), 20)


if __name__ == "__main__":
    unittest.main()
