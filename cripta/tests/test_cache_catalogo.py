"""
Pruebas de CacheCatalogo (caché LRU del catálogo).

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import random
import unittest

from structures.cache_catalogo import CAPACIDAD_POR_DEFECTO, CacheCatalogo
from structures.tabla_hash import TablaHash


def tabla_de_ids(*ids):
    """Arma la TablaHash que devolvería consultar_ids_en_uso."""
    tabla = TablaHash()
    for id_ficha in ids:
        tabla.insertar(id_ficha, True)
    return tabla


class ConsultaDeUsoFalsa:
    """Simula la función del controlador y cuenta cuántas veces se llama."""

    def __init__(self, *ids):
        self.ids_en_uso = tabla_de_ids(*ids)
        self.veces_consultada = 0

    def __call__(self):
        self.veces_consultada += 1
        return self.ids_en_uso


class PruebasBasicas(unittest.TestCase):

    def test_capacidad_por_defecto_es_25(self):
        self.assertEqual(CacheCatalogo().capacidad_maxima(), 25)
        self.assertEqual(CAPACIDAD_POR_DEFECTO, 25)

    def test_capacidad_invalida(self):
        for capacidad in (0, -3, 2.5, "10", True):
            with self.assertRaises(ValueError):
                CacheCatalogo(capacidad)

    def test_cache_vacia(self):
        cache = CacheCatalogo(3)
        self.assertEqual(cache.cantidad_de_fichas(), 0)
        self.assertEqual(cache.ids_en_orden_de_uso(), [])
        self.assertIsNone(cache.obtener_ficha("ent_rata_gigante"))
        self.assertEqual(cache.fallos_en_memoria(), 1)
        self.assertEqual(cache.aciertos_en_memoria(), 0)

    def test_agregar_y_obtener(self):
        cache = CacheCatalogo(3)
        cache.agregar_ficha("ent_rata_gigante", "ficha rata")
        self.assertEqual(cache.obtener_ficha("ent_rata_gigante"), "ficha rata")
        self.assertEqual(cache.aciertos_en_memoria(), 1)
        self.assertEqual(cache.fallos_en_memoria(), 0)

    def test_contiene_no_cambia_orden_ni_estadisticas(self):
        cache = CacheCatalogo(3)
        cache.agregar_ficha("a", 1)
        cache.agregar_ficha("b", 2)
        self.assertTrue(cache.contiene_ficha("a"))
        self.assertFalse(cache.contiene_ficha("z"))
        self.assertEqual(cache.ids_en_orden_de_uso(), ["b", "a"])
        self.assertEqual(cache.aciertos_en_memoria() + cache.fallos_en_memoria(), 0)


class PruebasOrdenDeUso(unittest.TestCase):

    def test_lo_mas_reciente_queda_al_frente(self):
        cache = CacheCatalogo(5)
        for id_ficha in ("a", "b", "c"):
            cache.agregar_ficha(id_ficha, id_ficha)
        self.assertEqual(cache.ids_en_orden_de_uso(), ["c", "b", "a"])
        cache.obtener_ficha("a")
        self.assertEqual(cache.ids_en_orden_de_uso(), ["a", "c", "b"])

    def test_agregar_una_ficha_existente_la_actualiza_y_la_mueve(self):
        cache = CacheCatalogo(3)
        cache.agregar_ficha("a", "vieja")
        cache.agregar_ficha("b", 2)
        cache.agregar_ficha("a", "nueva")
        self.assertEqual(cache.ids_en_orden_de_uso(), ["a", "b"])
        self.assertEqual(cache.obtener_ficha("a"), "nueva")
        self.assertEqual(cache.cantidad_de_fichas(), 2)
        self.assertEqual(cache.cantidad_de_desalojos(), 0)

    def test_enlaces_coherentes_en_ambas_direcciones(self):
        cache = CacheCatalogo(4)
        for id_ficha in ("a", "b", "c", "d", "e"):
            cache.agregar_ficha(id_ficha, id_ficha)
        cache.obtener_ficha("c")
        # Prueba de caja blanca: recorrer la lista desde el final hacia el frente.
        desde_el_final = []
        nodo = cache._centinela_final.anterior
        while nodo is not cache._centinela_frente:
            desde_el_final.append(nodo.id_ficha)
            nodo = nodo.anterior
        self.assertEqual(desde_el_final, list(reversed(cache.ids_en_orden_de_uso())))


class PruebasDesalojo(unittest.TestCase):

    def test_libera_la_usada_hace_mas_tiempo(self):
        cache = CacheCatalogo(3)
        for id_ficha in ("a", "b", "c", "d"):
            cache.agregar_ficha(id_ficha, id_ficha)
        self.assertFalse(cache.contiene_ficha("a"))
        self.assertEqual(cache.ids_en_orden_de_uso(), ["d", "c", "b"])
        self.assertEqual(cache.cantidad_de_desalojos(), 1)

    def test_usar_una_ficha_la_protege_del_desalojo(self):
        cache = CacheCatalogo(3)
        for id_ficha in ("a", "b", "c"):
            cache.agregar_ficha(id_ficha, id_ficha)
        cache.obtener_ficha("a")
        cache.agregar_ficha("d", "d")
        self.assertTrue(cache.contiene_ficha("a"))
        self.assertFalse(cache.contiene_ficha("b"))

    def test_capacidad_uno(self):
        cache = CacheCatalogo(1)
        cache.agregar_ficha("a", 1)
        cache.agregar_ficha("b", 2)
        self.assertEqual(cache.ids_en_orden_de_uso(), ["b"])

    def test_vaciar(self):
        cache = CacheCatalogo(3)
        cache.agregar_ficha("a", 1)
        cache.obtener_ficha("a")
        cache.vaciar()
        self.assertEqual(cache.cantidad_de_fichas(), 0)
        self.assertEqual(cache.ids_en_orden_de_uso(), [])
        self.assertEqual(cache.aciertos_en_memoria(), 1)  # se conservan
        cache.agregar_ficha("b", 2)
        self.assertEqual(cache.ids_en_orden_de_uso(), ["b"])


class PruebasFichasEnUso(unittest.TestCase):

    def test_salta_las_fichas_en_uso(self):
        consulta = ConsultaDeUsoFalsa("a")
        cache = CacheCatalogo(2, consulta)
        cache.agregar_ficha("a", 1)
        cache.agregar_ficha("b", 2)
        cache.agregar_ficha("c", 3)  # "a" es la más vieja, pero está en uso
        self.assertTrue(cache.contiene_ficha("a"))
        self.assertFalse(cache.contiene_ficha("b"))
        self.assertEqual(cache.exceso_maximo_sobre_capacidad(), 0)

    def test_solo_consulta_el_uso_cuando_hay_que_liberar(self):
        consulta = ConsultaDeUsoFalsa()
        cache = CacheCatalogo(3, consulta)
        for id_ficha in ("a", "b", "c"):
            cache.agregar_ficha(id_ficha, id_ficha)
        cache.obtener_ficha("a")
        self.assertEqual(consulta.veces_consultada, 0)
        cache.agregar_ficha("d", "d")
        self.assertEqual(consulta.veces_consultada, 1)

    def test_todas_en_uso_excede_el_tope_temporalmente(self):
        consulta = ConsultaDeUsoFalsa("a", "b")
        cache = CacheCatalogo(2, consulta)
        cache.agregar_ficha("a", 1)
        cache.agregar_ficha("b", 2)
        cache.agregar_ficha("c", 3)
        self.assertEqual(cache.cantidad_de_fichas(), 3)
        self.assertEqual(cache.exceso_maximo_sobre_capacidad(), 1)
        self.assertEqual(cache.cantidad_de_desalojos(), 0)

        # Cuando dejan de estar en uso, la siguiente inserción vuelve al tope.
        consulta.ids_en_uso = tabla_de_ids()
        cache.agregar_ficha("d", 4)
        self.assertEqual(cache.cantidad_de_fichas(), 2)
        self.assertEqual(cache.ids_en_orden_de_uso(), ["d", "c"])
        self.assertEqual(cache.cantidad_de_desalojos(), 2)
        self.assertEqual(cache.exceso_maximo_sobre_capacidad(), 1)  # el máximo se recuerda

    def test_la_ficha_recien_agregada_nunca_se_libera(self):
        consulta = ConsultaDeUsoFalsa("a")
        cache = CacheCatalogo(1, consulta)
        cache.agregar_ficha("a", 1)
        cache.agregar_ficha("b", 2)  # "a" está en uso y "b" se acaba de pedir
        self.assertTrue(cache.contiene_ficha("a"))
        self.assertTrue(cache.contiene_ficha("b"))
        self.assertEqual(cache.exceso_maximo_sobre_capacidad(), 1)


class PruebaContraModeloDeReferencia(unittest.TestCase):
    """Compara la caché con un LRU trivial hecho con una list de Python,
    a lo largo de miles de operaciones aleatorias (con semilla fija)."""

    def test_miles_de_operaciones_aleatorias(self):
        azar = random.Random(2026)
        capacidad = 5
        cache = CacheCatalogo(capacidad)
        modelo = []  # ids desde el más reciente al más viejo
        ids_posibles = [f"ficha_{i}" for i in range(12)]
        for _ in range(5_000):
            id_ficha = azar.choice(ids_posibles)
            if azar.random() < 0.5:
                encontrada = cache.obtener_ficha(id_ficha)
                if id_ficha in modelo:
                    self.assertEqual(encontrada, id_ficha)
                    modelo.remove(id_ficha)
                    modelo.insert(0, id_ficha)
                else:
                    self.assertIsNone(encontrada)
            else:
                cache.agregar_ficha(id_ficha, id_ficha)
                if id_ficha in modelo:
                    modelo.remove(id_ficha)
                modelo.insert(0, id_ficha)
                if len(modelo) > capacidad:
                    modelo.pop()
            self.assertEqual(cache.ids_en_orden_de_uso(), modelo)


if __name__ == "__main__":
    unittest.main()
