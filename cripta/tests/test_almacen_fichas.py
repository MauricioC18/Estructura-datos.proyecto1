"""
Pruebas de AlmacenFichas (fichas del catálogo en disco).

Cada prueba trabaja en una carpeta temporal que se borra al terminar. Las
fichas de ejemplo son las reales de cripta-01.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import json
import struct
import tempfile
import unittest
from pathlib import Path

from adapters.almacen_fichas import FIRMA_DEL_INDICE, AlmacenFichas

VERSION = "be68d322d2f5"
OTRA_VERSION = "000000000000"

RATA = {"id": "ent_rata_gigante", "nombre": "Rata gigante", "clase": "enemigo", "vida_max": 12,
        "ataque": 5, "defensa": 1, "velocidad": 150, "comportamiento": "rastreador",
        "suelta": ["itm_pocion_menor"]}
GUARDIAN = {"id": "ent_guardian_oseo", "nombre": "Guardián óseo", "clase": "enemigo",
            "vida_max": 20, "ataque": 7, "defensa": 3, "velocidad": 90,
            "comportamiento": "guardián"}
DARDOS = {"id": "trp_dardos", "nombre": "Dardos en la pared", "clase": "trampa",
          "daño": 4, "rearme": 300}
ANTORCHA = {"id": "itm_antorcha", "nombre": "Antorcha", "clase": "antorcha",
            "peso": 1, "valor": 5, "duracion": 2000}


class PruebasAlmacenFichas(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._carpeta_temporal.name) / "cache"

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def abrir_almacen(self, version=VERSION):
        almacen = AlmacenFichas(self.carpeta)
        almacen.abrir(version)
        return almacen

    # --- almacén vacío y uso básico ----------------------------------

    def test_almacen_nuevo_esta_vacio(self):
        almacen = self.abrir_almacen()
        self.assertEqual(almacen.cantidad_de_fichas(), 0)
        self.assertFalse(almacen.contiene_ficha("ent_rata_gigante"))
        self.assertIsNone(almacen.leer_ficha("ent_rata_gigante"))
        self.assertIsNone(almacen.motivo_del_ultimo_descarte())

    def test_hay_que_abrir_antes_de_usar(self):
        almacen = AlmacenFichas(self.carpeta)
        with self.assertRaises(RuntimeError):
            almacen.leer_ficha("ent_rata_gigante")
        with self.assertRaises(RuntimeError):
            almacen.guardar_fichas([RATA])

    def test_version_invalida(self):
        for version in ("", None, 5):
            with self.assertRaises(ValueError):
                AlmacenFichas(self.carpeta).abrir(version)

    def test_guardar_y_leer(self):
        almacen = self.abrir_almacen()
        almacen.guardar_fichas([RATA, DARDOS])
        self.assertEqual(almacen.leer_ficha("ent_rata_gigante"), RATA)
        self.assertEqual(almacen.leer_ficha("trp_dardos"), DARDOS)
        self.assertEqual(almacen.cantidad_de_fichas(), 2)

    def test_conserva_tildes_y_enie(self):
        almacen = self.abrir_almacen()
        almacen.guardar_fichas([GUARDIAN, DARDOS])
        self.assertEqual(almacen.leer_ficha("ent_guardian_oseo")["nombre"], "Guardián óseo")
        self.assertEqual(almacen.leer_ficha("trp_dardos")["daño"], 4)

    def test_guardar_lista_vacia_no_hace_nada(self):
        almacen = self.abrir_almacen()
        almacen.guardar_fichas([])
        self.assertEqual(almacen.cantidad_de_fichas(), 0)

    def test_ficha_sin_id(self):
        almacen = self.abrir_almacen()
        for ficha_invalida in ({"nombre": "sin id"}, {"id": ""}, {"id": 7}, "no es ficha"):
            with self.assertRaises(ValueError):
                almacen.guardar_fichas([ficha_invalida])
        self.assertEqual(almacen.cantidad_de_fichas(), 0)

    # --- índice ordenado ---------------------------------------------

    def test_indice_queda_ordenado_aunque_se_guarde_desordenado(self):
        almacen = self.abrir_almacen()
        almacen.guardar_fichas([DARDOS, RATA])
        almacen.guardar_fichas([ANTORCHA, GUARDIAN])
        self.assertEqual(
            almacen.ids_ordenados(),
            ["ent_guardian_oseo", "ent_rata_gigante", "itm_antorcha", "trp_dardos"],
        )

    def test_mil_fichas(self):
        almacen = self.abrir_almacen()
        fichas = [{"id": f"itm_{(i * 7919) % 1000:04d}", "valor": i} for i in range(1000)]
        for inicio in range(0, 1000, 10):  # en lotes de 10, como el API
            almacen.guardar_fichas(fichas[inicio:inicio + 10])
        self.assertEqual(almacen.cantidad_de_fichas(), 1000)
        ids = almacen.ids_ordenados()
        for posicion in range(1, len(ids)):
            self.assertLess(ids[posicion - 1], ids[posicion])
        for ficha in fichas:
            self.assertEqual(almacen.leer_ficha(ficha["id"]), ficha)
        self.assertFalse(almacen.contiene_ficha("itm_9999"))
        self.assertFalse(almacen.contiene_ficha("aaa"))  # antes del primero
        self.assertFalse(almacen.contiene_ficha("zzz"))  # después del último

    def test_volver_a_guardar_reemplaza_la_ficha(self):
        almacen = self.abrir_almacen()
        almacen.guardar_fichas([RATA])
        rata_nueva = dict(RATA, ataque=99)
        almacen.guardar_fichas([rata_nueva])
        self.assertEqual(almacen.leer_ficha("ent_rata_gigante")["ataque"], 99)
        self.assertEqual(almacen.cantidad_de_fichas(), 1)

    # --- persistencia entre ejecuciones (§4.4) ------------------------

    def test_sobrevive_al_cierre_del_programa(self):
        self.abrir_almacen().guardar_fichas([RATA, DARDOS, GUARDIAN])
        otra_ejecucion = self.abrir_almacen()
        self.assertEqual(otra_ejecucion.cantidad_de_fichas(), 3)
        self.assertEqual(otra_ejecucion.leer_ficha("ent_guardian_oseo"), GUARDIAN)
        self.assertIsNone(otra_ejecucion.motivo_del_ultimo_descarte())

    def test_otra_version_del_catalogo_descarta_todo(self):
        self.abrir_almacen().guardar_fichas([RATA, DARDOS])
        almacen = self.abrir_almacen(OTRA_VERSION)
        self.assertEqual(almacen.cantidad_de_fichas(), 0)
        self.assertIsNone(almacen.leer_ficha("ent_rata_gigante"))
        self.assertIn("versión del catálogo", almacen.motivo_del_ultimo_descarte())
        self.assertEqual((self.carpeta / "fichas.datos").stat().st_size, 0)
        # Y lo que se guarde ahora queda con la versión nueva.
        almacen.guardar_fichas([ANTORCHA])
        self.assertEqual(self.abrir_almacen(OTRA_VERSION).cantidad_de_fichas(), 1)

    # --- lectura parcial y daños -------------------------------------

    def test_lee_solo_los_bytes_de_la_ficha_pedida(self):
        almacen = self.abrir_almacen()
        almacen.guardar_fichas([RATA, DARDOS])
        # Se dañan a propósito los bytes de DARDOS (la segunda ficha guardada).
        ruta_datos = self.carpeta / "fichas.datos"
        contenido = bytearray(ruta_datos.read_bytes())
        largo_dardos = len(json.dumps(DARDOS, ensure_ascii=False).encode("utf-8"))
        inicio_dardos = len(contenido) - largo_dardos
        contenido[inicio_dardos:] = b"x" * largo_dardos
        ruta_datos.write_bytes(bytes(contenido))
        # La rata se sigue leyendo bien porque nunca se leen los bytes de los dardos.
        self.assertEqual(almacen.leer_ficha("ent_rata_gigante"), RATA)
        self.assertIsNone(almacen.leer_ficha("trp_dardos"))

    def test_datos_recortados_devuelven_none(self):
        almacen = self.abrir_almacen()
        almacen.guardar_fichas([RATA])
        ruta_datos = self.carpeta / "fichas.datos"
        ruta_datos.write_bytes(ruta_datos.read_bytes()[:10])
        self.assertIsNone(almacen.leer_ficha("ent_rata_gigante"))

    def test_indice_danado_se_descarta(self):
        self.abrir_almacen().guardar_fichas([RATA])
        (self.carpeta / "fichas.indice").write_bytes(b"esto no es un indice")
        almacen = self.abrir_almacen()
        self.assertEqual(almacen.cantidad_de_fichas(), 0)
        self.assertIn("dañado", almacen.motivo_del_ultimo_descarte())

    def test_indice_recortado_se_descarta(self):
        self.abrir_almacen().guardar_fichas([RATA, DARDOS])
        ruta_indice = self.carpeta / "fichas.indice"
        ruta_indice.write_bytes(ruta_indice.read_bytes()[:-5])
        self.assertEqual(self.abrir_almacen().cantidad_de_fichas(), 0)

    def test_otra_version_del_formato_se_descarta(self):
        self.abrir_almacen().guardar_fichas([RATA])
        ruta_indice = self.carpeta / "fichas.indice"
        contenido = bytearray(ruta_indice.read_bytes())
        contenido[8:10] = struct.pack("<H", 99)  # justo después de la firma
        ruta_indice.write_bytes(bytes(contenido))
        almacen = self.abrir_almacen()
        self.assertEqual(almacen.cantidad_de_fichas(), 0)
        self.assertIn("formato 99", almacen.motivo_del_ultimo_descarte())

    def test_el_indice_empieza_con_la_firma(self):
        self.abrir_almacen().guardar_fichas([RATA])
        self.assertTrue((self.carpeta / "fichas.indice").read_bytes().startswith(FIRMA_DEL_INDICE))

    def test_no_queda_archivo_temporal(self):
        self.abrir_almacen().guardar_fichas([RATA])
        self.assertFalse((self.carpeta / "fichas.indice.tmp").exists())


if __name__ == "__main__":
    unittest.main()
