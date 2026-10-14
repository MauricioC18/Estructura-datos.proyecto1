"""
Pruebas de ListaSinRepetidos.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import unittest

from structures.lista_sin_repetidos import ListaSinRepetidos


class PruebasListaSinRepetidos(unittest.TestCase):

    def test_lista_nueva_vacia(self):
        lista = ListaSinRepetidos()
        self.assertEqual(lista.elementos, [])
        self.assertEqual(lista.cantidad(), 0)
        self.assertFalse(lista.contiene("a"))

    def test_conserva_el_orden_y_descarta_repetidos(self):
        lista = ListaSinRepetidos()
        resultados = [lista.agregar(elemento) for elemento in ("b", "a", "b", "c", "a")]
        self.assertEqual(lista.elementos, ["b", "a", "c"])
        self.assertEqual(resultados, [True, True, False, True, False])
        self.assertEqual(lista.cantidad(), 3)
        self.assertTrue(lista.contiene("c"))

    def test_muchos_elementos(self):
        lista = ListaSinRepetidos()
        for vuelta in range(3):
            for i in range(500):
                lista.agregar(f"itm_{i}")
        self.assertEqual(lista.cantidad(), 500)
        self.assertEqual(lista.elementos[0], "itm_0")
        self.assertEqual(lista.elementos[-1], "itm_499")


if __name__ == "__main__":
    unittest.main()
