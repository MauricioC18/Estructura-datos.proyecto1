"""
Pruebas de AlmacenCripta (esqueleto y contenido en disco, por versión).

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import tempfile
import unittest
from pathlib import Path

from adapters.almacen_cripta import AlmacenCripta
from adapters.almacen_fichas import ErrorAlmacenDisco
from tests.datos_cripta_01 import CONTENIDO_CRIPTA_01, GENERALES_CRIPTA_01, SALAS_CRIPTA_01


class PruebasAlmacenCripta(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._carpeta_temporal.name) / "criptas"
        self.almacen = AlmacenCripta(self.carpeta)

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def test_primera_vez_no_hay_copia(self):
        self.assertFalse(self.almacen.preparar(GENERALES_CRIPTA_01))
        self.assertIsNone(self.almacen.leer_esqueleto("cripta-01"))
        self.assertEqual(self.almacen.leer_contenido_guardado("cripta-01", [1, 2]), [])

    def test_misma_version_conserva_la_copia(self):
        self.almacen.preparar(GENERALES_CRIPTA_01)
        self.almacen.guardar_esqueleto("cripta-01", SALAS_CRIPTA_01)
        self.almacen.guardar_contenido("cripta-01", CONTENIDO_CRIPTA_01)
        otra_ejecucion = AlmacenCripta(self.carpeta)
        self.assertTrue(otra_ejecucion.preparar(GENERALES_CRIPTA_01))
        self.assertEqual(otra_ejecucion.leer_esqueleto("cripta-01"), SALAS_CRIPTA_01)
        self.assertEqual(otra_ejecucion.leer_contenido_guardado("cripta-01", [1, 2, 3, 4, 5, 6]),
                         CONTENIDO_CRIPTA_01)

    def test_otra_version_borra_la_copia(self):
        self.almacen.preparar(GENERALES_CRIPTA_01)
        self.almacen.guardar_esqueleto("cripta-01", SALAS_CRIPTA_01)
        self.almacen.guardar_contenido("cripta-01", CONTENIDO_CRIPTA_01)
        nueva_version = dict(GENERALES_CRIPTA_01, version="otra-version")
        self.assertFalse(self.almacen.preparar(nueva_version))
        self.assertIsNone(self.almacen.leer_esqueleto("cripta-01"))
        self.assertEqual(self.almacen.leer_contenido_guardado("cripta-01", [1, 2, 3]), [])
        self.assertTrue(self.almacen.preparar(nueva_version))  # ahora la vigente es la nueva

    def test_contenido_en_el_orden_pedido_y_solo_lo_guardado(self):
        self.almacen.preparar(GENERALES_CRIPTA_01)
        self.almacen.guardar_contenido("cripta-01", CONTENIDO_CRIPTA_01[:3])
        entradas = self.almacen.leer_contenido_guardado("cripta-01", [3, 6, 1])
        self.assertEqual([entrada["sala"] for entrada in entradas], [3, 1])

    def test_archivos_danados_se_ignoran(self):
        self.almacen.preparar(GENERALES_CRIPTA_01)
        self.almacen.guardar_esqueleto("cripta-01", SALAS_CRIPTA_01)
        self.almacen.guardar_contenido("cripta-01", CONTENIDO_CRIPTA_01[:2])
        carpeta = self.carpeta / "cripta-01"
        (carpeta / "esqueleto.json").write_text("{ dañado", encoding="utf-8")
        (carpeta / "contenido" / "sala_1.json").write_text("no es json", encoding="utf-8")
        self.assertIsNone(self.almacen.leer_esqueleto("cripta-01"))
        entradas = self.almacen.leer_contenido_guardado("cripta-01", [1, 2])
        self.assertEqual([entrada["sala"] for entrada in entradas], [2])

    def test_conserva_tildes(self):
        self.almacen.preparar(GENERALES_CRIPTA_01)
        self.almacen.guardar_esqueleto("cripta-01", [{"id": 1, "nombre": "Galería del guardián"}])
        self.assertEqual(self.almacen.leer_esqueleto("cripta-01")[0]["nombre"], "Galería del guardián")

    def test_no_quedan_archivos_temporales(self):
        self.almacen.preparar(GENERALES_CRIPTA_01)
        self.almacen.guardar_esqueleto("cripta-01", SALAS_CRIPTA_01)
        self.almacen.guardar_contenido("cripta-01", CONTENIDO_CRIPTA_01)
        temporales = [ruta for ruta in self.carpeta.rglob("*.tmp")]
        self.assertEqual(temporales, [])

    def test_id_de_cripta_peligroso(self):
        with self.assertRaises(ValueError):
            self.almacen.preparar(dict(GENERALES_CRIPTA_01, id="../fuera"))

    def test_disco_que_no_se_puede_escribir(self):
        archivo = Path(self._carpeta_temporal.name) / "soy_un_archivo"
        archivo.write_text("x", encoding="utf-8")
        almacen = AlmacenCripta(archivo)  # la "carpeta" es en realidad un archivo
        with self.assertRaises(ErrorAlmacenDisco):
            almacen.preparar(GENERALES_CRIPTA_01)


if __name__ == "__main__":
    unittest.main()
