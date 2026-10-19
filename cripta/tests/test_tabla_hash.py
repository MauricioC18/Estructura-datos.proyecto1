"""
Pruebas de TablaHash y de las funciones hash.

La misma batería de pruebas de la tabla se ejecuta dos veces: con crc32
(la función elegida) y con FNV-1a (la alternativa descartada).

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import unittest

from structures.funciones_hash import hash_crc32, hash_fnv1a
from structures.tabla_hash import TablaHash


class PruebasFuncionesHash(unittest.TestCase):
    """Valores de referencia publicados para cada algoritmo: si coinciden,
    el resultado es el mismo en cualquier ejecución y computadora."""

    def test_crc32_valores_de_referencia(self):
        self.assertEqual(hash_crc32(""), 0)
        self.assertEqual(hash_crc32("a"), 0xE8B7BE43)
        self.assertEqual(hash_crc32("123456789"), 0xCBF43926)

    def test_fnv1a_valores_de_referencia(self):
        self.assertEqual(hash_fnv1a(""), 0xCBF29CE484222325)
        self.assertEqual(hash_fnv1a("a"), 0xAF63DC4C8601EC8C)
        self.assertEqual(hash_fnv1a("foobar"), 0x85944171F73967E8)

    def test_enteros_usan_el_mismo_numero(self):
        for funcion in (hash_crc32, hash_fnv1a):
            self.assertEqual(funcion(0), 0)
            self.assertEqual(funcion(42), 42)

    def test_misma_clave_mismo_resultado(self):
        for funcion in (hash_crc32, hash_fnv1a):
            self.assertEqual(funcion("guardián"), funcion("guardián"))

    def test_textos_distintos_resultados_distintos(self):
        for funcion in (hash_crc32, hash_fnv1a):
            self.assertNotEqual(funcion("ent_rata_gigante"), funcion("ent_rata_gigantf"))

    def test_tipos_no_soportados(self):
        for funcion in (hash_crc32, hash_fnv1a):
            for clave in (1.5, None, [1, 2], (1, 2)):
                with self.assertRaises(TypeError):
                    funcion(clave)


class PruebasTablaHash(unittest.TestCase):
    """Pruebas de la tabla usando crc32 (función por defecto)."""

    funcion_hash = staticmethod(hash_crc32)

    def crear_tabla(self, capacidad_inicial=8):
        return TablaHash(capacidad_inicial, self.funcion_hash)

    # --- tabla vacía -------------------------------------------------

    def test_tabla_nueva_esta_vacia(self):
        tabla = self.crear_tabla()
        self.assertTrue(tabla.esta_vacia())
        self.assertEqual(tabla.tamano(), 0)
        self.assertEqual(tabla.claves(), [])
        self.assertIsNone(tabla.obtener("ent_rata_gigante"))
        self.assertFalse(tabla.contiene("ent_rata_gigante"))

    def test_eliminar_en_tabla_vacia(self):
        self.assertFalse(self.crear_tabla().eliminar("cualquiera"))

    # --- casos normales ----------------------------------------------

    def test_insertar_y_obtener(self):
        tabla = self.crear_tabla()
        tabla.insertar("ent_rata_gigante", "ficha rata")
        tabla.insertar("itm_antorcha", "ficha antorcha")
        self.assertEqual(tabla.obtener("ent_rata_gigante"), "ficha rata")
        self.assertEqual(tabla.obtener("itm_antorcha"), "ficha antorcha")
        self.assertEqual(tabla.tamano(), 2)
        self.assertFalse(tabla.esta_vacia())

    def test_insertar_clave_existente_reemplaza_el_valor(self):
        tabla = self.crear_tabla()
        tabla.insertar("e-201", 12)
        tabla.insertar("e-201", 7)
        self.assertEqual(tabla.obtener("e-201"), 7)
        self.assertEqual(tabla.tamano(), 1)

    def test_obtener_inexistente_devuelve_valor_por_defecto(self):
        tabla = self.crear_tabla()
        tabla.insertar("a", 1)
        self.assertIsNone(tabla.obtener("b"))
        self.assertEqual(tabla.obtener("b", -1), -1)

    def test_valor_none_se_distingue_con_contiene(self):
        tabla = self.crear_tabla()
        tabla.insertar("sala_sin_datos", None)
        self.assertIsNone(tabla.obtener("sala_sin_datos"))
        self.assertTrue(tabla.contiene("sala_sin_datos"))

    def test_eliminar_existente(self):
        tabla = self.crear_tabla()
        tabla.insertar("a", 1)
        tabla.insertar("b", 2)
        self.assertTrue(tabla.eliminar("a"))
        self.assertFalse(tabla.contiene("a"))
        self.assertEqual(tabla.obtener("b"), 2)
        self.assertEqual(tabla.tamano(), 1)

    def test_eliminar_dos_veces(self):
        tabla = self.crear_tabla()
        tabla.insertar("a", 1)
        self.assertTrue(tabla.eliminar("a"))
        self.assertFalse(tabla.eliminar("a"))
        self.assertTrue(tabla.esta_vacia())

    def test_eliminar_y_volver_a_insertar(self):
        tabla = self.crear_tabla()
        tabla.insertar("a", 1)
        tabla.eliminar("a")
        tabla.insertar("a", 2)
        self.assertEqual(tabla.obtener("a"), 2)
        self.assertEqual(tabla.tamano(), 1)

    # --- tipos de clave ----------------------------------------------

    def test_entero_y_texto_son_claves_distintas(self):
        tabla = self.crear_tabla()
        tabla.insertar(1, "sala 1")
        tabla.insertar("1", "texto 1")
        self.assertEqual(tabla.obtener(1), "sala 1")
        self.assertEqual(tabla.obtener("1"), "texto 1")
        self.assertEqual(tabla.tamano(), 2)

    def test_claves_con_tildes_y_enie(self):
        tabla = self.crear_tabla()
        tabla.insertar("guardián", "comportamiento")
        tabla.insertar("daño", 4)
        self.assertEqual(tabla.obtener("guardián"), "comportamiento")
        self.assertEqual(tabla.obtener("daño"), 4)
        self.assertFalse(tabla.contiene("guardian"))  # sin tilde es otra clave

    def test_clave_de_tipo_no_soportado(self):
        tabla = self.crear_tabla()
        with self.assertRaises(TypeError):
            tabla.insertar(3.5, "x")
        with self.assertRaises(TypeError):
            tabla.obtener(None)

    # --- capacidad y redimensionamiento ------------------------------

    def test_capacidad_se_redondea_a_potencia_de_2(self):
        self.assertEqual(self.crear_tabla(1).capacidad(), 1)
        self.assertEqual(self.crear_tabla(10).capacidad(), 16)
        self.assertEqual(self.crear_tabla(16).capacidad(), 16)

    def test_capacidad_inicial_invalida(self):
        with self.assertRaises(ValueError):
            self.crear_tabla(0)

    def test_redimensiona_solo_al_superar_factor_de_carga(self):
        tabla = self.crear_tabla(8)
        for i in range(6):  # 6 / 8 = 0,75: todavía no supera el límite
            tabla.insertar(i, i)
        self.assertEqual(tabla.capacidad(), 8)
        tabla.insertar(6, 6)  # 7 / 8 > 0,75: se duplica
        self.assertEqual(tabla.capacidad(), 16)
        for i in range(7):
            self.assertEqual(tabla.obtener(i), i)

    def test_reemplazar_valor_no_provoca_redimensionamiento(self):
        tabla = self.crear_tabla(8)
        for i in range(6):
            tabla.insertar(i, i)
        for _ in range(20):
            tabla.insertar(0, "nuevo")
        self.assertEqual(tabla.capacidad(), 8)
        self.assertEqual(tabla.tamano(), 6)

    def test_capacidad_minima_con_muchas_claves(self):
        tabla = self.crear_tabla(1)
        for i in range(100):
            tabla.insertar(f"k{i}", i)
        for i in range(100):
            self.assertEqual(tabla.obtener(f"k{i}"), i)

    # --- volumen (máximo exigido y más) ------------------------------

    def test_diez_mil_claves(self):
        tabla = self.crear_tabla()
        cantidad = 10_000
        for i in range(cantidad):
            tabla.insertar(f"ent_tipo_{i:05d}", i)
        self.assertEqual(tabla.tamano(), cantidad)
        self.assertLessEqual(tabla.tamano() * 4, tabla.capacidad() * 3)
        for i in range(cantidad):
            self.assertEqual(tabla.obtener(f"ent_tipo_{i:05d}"), i)
        self.assertFalse(tabla.contiene("ent_tipo_99999"))

    def test_eliminar_la_mitad_de_muchas_claves(self):
        tabla = self.crear_tabla()
        for i in range(2_000):
            tabla.insertar(i, str(i))
        for i in range(0, 2_000, 2):
            self.assertTrue(tabla.eliminar(i))
        self.assertEqual(tabla.tamano(), 1_000)
        for i in range(2_000):
            self.assertEqual(tabla.contiene(i), i % 2 == 1)

    def test_claves_devuelve_todas_sin_repetir(self):
        tabla = self.crear_tabla()
        esperadas = [f"itm_{i}" for i in range(50)]
        for clave in esperadas:
            tabla.insertar(clave, True)
        obtenidas = tabla.claves()
        self.assertEqual(len(obtenidas), 50)
        for clave in esperadas:
            self.assertIn(clave, obtenidas)

    # --- determinismo y colisiones -----------------------------------

    def test_mismas_operaciones_mismo_orden_de_claves(self):
        primera = self.crear_tabla()
        segunda = self.crear_tabla()
        for tabla in (primera, segunda):
            for i in range(300):
                tabla.insertar(f"e-{i}", i)
            for i in range(0, 300, 3):
                tabla.eliminar(f"e-{i}")
        self.assertEqual(primera.claves(), segunda.claves())

    def test_distribucion_sin_cubetas_sobrecargadas(self):
        tabla = self.crear_tabla()
        for i in range(1_000):
            tabla.insertar(f"ent_tipo_{i:05d}", i)
        # Con factor de carga <= 0,75 y una buena función hash, ninguna
        # cubeta debería acumular muchas entradas. Como la función es
        # determinista, este resultado es siempre el mismo.
        self.assertLessEqual(tabla.longitud_maxima_cubeta(), 8)


class PruebasTablaHashConFNV(PruebasTablaHash):
    """Repite todas las pruebas de la tabla usando FNV-1a."""

    funcion_hash = staticmethod(hash_fnv1a)


if __name__ == "__main__":
    unittest.main()
