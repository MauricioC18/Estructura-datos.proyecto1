"""
Pruebas de FuenteOffline y GuardadorDatosOffline.

Cada prueba trabaja en una carpeta temporal que se borra al terminar.
La prueba más importante es la de "mismo contrato": lo que devuelve
FuenteOffline debe ser idéntico a lo que devolvió FuenteHttp.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import tempfile
import unittest
from pathlib import Path

from adapters.fuente_datos import ErrorFuenteDatos
from adapters.fuente_http import FuenteHttp
from adapters.fuente_offline import (
    FuenteOffline,
    GuardadorDatosOffline,
    RutasDatosOffline,
    nombre_de_archivo_seguro,
)
from tests.test_fuente_http import EsperaFalsa, RespuestaHttpFalsa, SesionHttpFalsa

LISTA_CRIPTAS = {"criptas": [{"id": "cripta-01", "nombre": "Osario menor", "salas": 20, "dificultad": 1}]}
DATOS_GENERALES = {
    "id": "cripta-01", "version": "a3f91c", "salas_total": 20, "paginas": 1,
    "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 19,
    "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 9, "inventario_max": 10,
    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100},
}
PAGINA_1 = {
    "pagina": 1, "total_paginas": 1,
    "salas": [
        {"id": 1, "nombre": "Entrada derruida", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo de las urnas", "salidas": {"S": {"sala": 1}}},
    ],
}
CONTENIDO_1_2 = {
    "contenido": [
        {"sala": 1, "enemigos": [], "objetos": ["itm_antorcha"], "trampas": []},
        {"sala": 2, "enemigos": [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": 12}],
         "objetos": [], "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}]},
    ]
}
CATALOGO = {
    "entidades": [
        {"id": "ent_rata_gigante", "clase": "enemigo", "nombre": "Rata gigante", "vida_max": 12,
         "ataque": 5, "defensa": 1, "velocidad": 150, "comportamiento": "guardián", "suelta": None},
        {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos en la pared", "daño": 4, "rearme": 300},
    ]
}
VERSION_CATALOGO = {"version": "cat-2026-08-01"}


class PruebasFuenteOffline(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta = self._carpeta_temporal.name
        guardador = GuardadorDatosOffline(self.carpeta)
        guardador.guardar_lista_criptas(LISTA_CRIPTAS)
        guardador.guardar_datos_generales(DATOS_GENERALES)
        guardador.guardar_pagina_salas("cripta-01", PAGINA_1)
        guardador.guardar_contenido("cripta-01", CONTENIDO_1_2)
        guardador.guardar_catalogo(CATALOGO)
        guardador.guardar_version_catalogo(VERSION_CATALOGO)
        self.fuente = FuenteOffline(self.carpeta)

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    # --- lectura normal ----------------------------------------------

    def test_lee_lo_que_se_guardo(self):
        self.assertEqual(self.fuente.listar_criptas(), LISTA_CRIPTAS)
        self.assertEqual(self.fuente.datos_generales("cripta-01"), DATOS_GENERALES)
        self.assertEqual(self.fuente.pagina_salas("cripta-01", 1), PAGINA_1)
        self.assertEqual(self.fuente.contenido("cripta-01", [1, 2]), CONTENIDO_1_2)
        self.assertEqual(self.fuente.catalogo(["ent_rata_gigante", "trp_dardos"]), CATALOGO)
        self.assertEqual(self.fuente.version_catalogo(), VERSION_CATALOGO)

    def test_version_de_cripta_sale_de_los_datos_generales(self):
        self.assertEqual(self.fuente.version_cripta("cripta-01"), {"id": "cripta-01", "version": "a3f91c"})

    def test_arma_los_lotes_en_el_orden_pedido(self):
        respuesta = self.fuente.contenido("cripta-01", [2, 1])
        self.assertEqual([entrada["sala"] for entrada in respuesta["contenido"]], [2, 1])
        respuesta = self.fuente.catalogo(["trp_dardos"])
        self.assertEqual(len(respuesta["entidades"]), 1)

    def test_conserva_tildes_y_enie(self):
        rata = self.fuente.catalogo(["ent_rata_gigante"])["entidades"][0]
        self.assertEqual(rata["comportamiento"], "guardián")
        dardos = self.fuente.catalogo(["trp_dardos"])["entidades"][0]
        self.assertEqual(dardos["daño"], 4)

    def test_un_archivo_por_sala_y_por_ficha(self):
        rutas = RutasDatosOffline(self.carpeta)
        self.assertTrue(rutas.contenido_de_sala("cripta-01", 1).is_file())
        self.assertTrue(rutas.contenido_de_sala("cripta-01", 2).is_file())
        self.assertTrue(rutas.ficha_catalogo("trp_dardos").is_file())

    # --- presupuesto -------------------------------------------------

    def test_leer_de_disco_no_cuenta_como_solicitud(self):
        self.fuente.establecer_presupuesto(0)
        for _ in range(20):
            self.fuente.listar_criptas()
            self.fuente.contenido("cripta-01", [1, 2])
        self.assertEqual(self.fuente.solicitudes_realizadas(), 0)

    # --- errores -----------------------------------------------------

    def test_carpeta_inexistente(self):
        with self.assertRaises(ErrorFuenteDatos):
            FuenteOffline(Path(self.carpeta) / "no_existe")

    def test_sala_que_no_esta_guardada(self):
        with self.assertRaises(ErrorFuenteDatos) as contexto:
            self.fuente.contenido("cripta-01", [1, 7])
        self.assertIn("sala 7", str(contexto.exception))

    def test_cripta_y_ficha_que_no_estan_guardadas(self):
        with self.assertRaises(ErrorFuenteDatos):
            self.fuente.datos_generales("cripta-02")
        with self.assertRaises(ErrorFuenteDatos):
            self.fuente.catalogo(["itm_no_existe"])
        with self.assertRaises(ErrorFuenteDatos):
            self.fuente.pagina_salas("cripta-01", 2)

    def test_archivo_danado(self):
        ruta = RutasDatosOffline(self.carpeta).version_catalogo()
        ruta.write_text("{ esto no es json", encoding="utf-8")
        with self.assertRaises(ErrorFuenteDatos) as contexto:
            self.fuente.version_catalogo()
        self.assertIn("JSON", str(contexto.exception))

    def test_ids_que_intentan_salir_de_la_carpeta(self):
        for id_peligroso in ("../cripta-01", "a/b", "a\\b", "..", "x:y"):
            with self.assertRaises(ErrorFuenteDatos):
                self.fuente.datos_generales(id_peligroso)

    def test_lotes_invalidos(self):
        with self.assertRaises(ValueError):
            self.fuente.contenido("cripta-01", [])
        with self.assertRaises(ValueError):
            self.fuente.catalogo(["trp_dardos", "trp_dardos"])
        with self.assertRaises(ValueError):
            self.fuente.pagina_salas("cripta-01", 0)


class PruebasNombreDeArchivoSeguro(unittest.TestCase):

    def test_ids_reales_pasan_sin_cambios(self):
        for texto in ("cripta-01", "ent_rata_gigante", "itm_llave_negra"):
            self.assertEqual(nombre_de_archivo_seguro(texto), texto)

    def test_ids_rechazados(self):
        for texto in ("", ".", "..", "a/b", "a\\b", "a?b", " espacio", "linea\nnueva"):
            with self.assertRaises(ValueError):
                nombre_de_archivo_seguro(texto)


class PruebasMismoContrato(unittest.TestCase):
    """Lo que devuelve FuenteOffline debe ser idéntico a lo de FuenteHttp (§3.4)."""

    def test_offline_devuelve_lo_mismo_que_http(self):
        sesion = SesionHttpFalsa(
            RespuestaHttpFalsa(200, LISTA_CRIPTAS),
            RespuestaHttpFalsa(200, DATOS_GENERALES),
            RespuestaHttpFalsa(200, PAGINA_1),
            RespuestaHttpFalsa(200, CONTENIDO_1_2),
            RespuestaHttpFalsa(200, CATALOGO),
            RespuestaHttpFalsa(200, VERSION_CATALOGO),
        )
        fuente_http = FuenteHttp("https://api.prueba/v1", "id", sesion, EsperaFalsa())
        desde_http = [
            fuente_http.listar_criptas(),
            fuente_http.datos_generales("cripta-01"),
            fuente_http.pagina_salas("cripta-01", 1),
            fuente_http.contenido("cripta-01", [1, 2]),
            fuente_http.catalogo(["ent_rata_gigante", "trp_dardos"]),
            fuente_http.version_catalogo(),
        ]
        with tempfile.TemporaryDirectory() as carpeta:
            guardador = GuardadorDatosOffline(carpeta)
            guardador.guardar_lista_criptas(desde_http[0])
            guardador.guardar_datos_generales(desde_http[1])
            guardador.guardar_pagina_salas("cripta-01", desde_http[2])
            guardador.guardar_contenido("cripta-01", desde_http[3])
            guardador.guardar_catalogo(desde_http[4])
            guardador.guardar_version_catalogo(desde_http[5])

            fuente_offline = FuenteOffline(carpeta)
            desde_disco = [
                fuente_offline.listar_criptas(),
                fuente_offline.datos_generales("cripta-01"),
                fuente_offline.pagina_salas("cripta-01", 1),
                fuente_offline.contenido("cripta-01", [1, 2]),
                fuente_offline.catalogo(["ent_rata_gigante", "trp_dardos"]),
                fuente_offline.version_catalogo(),
            ]
        self.assertEqual(desde_http, desde_disco)
        self.assertEqual(fuente_http.solicitudes_realizadas(), 6)
        self.assertEqual(fuente_offline.solicitudes_realizadas(), 0)


if __name__ == "__main__":
    unittest.main()
