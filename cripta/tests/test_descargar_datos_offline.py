"""
Pruebas de la herramienta de descarga, con el API simulado.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import tempfile
import unittest

from adapters.fuente_http import FuenteHttp
from adapters.fuente_offline import FuenteOffline, GuardadorDatosOffline
from tools.descargar_datos_offline import descargar_datos_offline
from tests.test_fuente_http import EsperaFalsa, RespuestaHttpFalsa, SesionHttpFalsa
from tests.test_fuente_offline import (
    CONTENIDO_1_2,
    DATOS_GENERALES,
    LISTA_CRIPTAS,
    PAGINA_1,
    VERSION_CATALOGO,
)

FICHA_ANTORCHA = {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha",
                  "peso": 1, "valor": 5, "duracion": 2000}
FICHA_RATA = {"id": "ent_rata_gigante", "clase": "enemigo", "nombre": "Rata gigante",
              "vida_max": 12, "ataque": 5, "defensa": 1, "velocidad": 150,
              "comportamiento": "rastreador", "suelta": ["itm_pocion_menor"]}
FICHA_DARDOS = {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos en la pared",
                "daño": 4, "rearme": 300}
FICHA_POCION = {"id": "itm_pocion_menor", "clase": "pocion", "nombre": "Poción menor",
                "peso": 1, "valor": 10, "cura": 8}


class PruebasDescarga(unittest.TestCase):

    def test_descarga_completa_incluye_lo_que_sueltan_los_enemigos(self):
        sesion = SesionHttpFalsa(
            RespuestaHttpFalsa(200, LISTA_CRIPTAS),
            RespuestaHttpFalsa(200, DATOS_GENERALES),
            RespuestaHttpFalsa(200, PAGINA_1),
            RespuestaHttpFalsa(200, CONTENIDO_1_2),
            RespuestaHttpFalsa(200, {"entidades": [FICHA_ANTORCHA, FICHA_RATA, FICHA_DARDOS]}),
            RespuestaHttpFalsa(200, {"entidades": [FICHA_POCION]}),  # lo que suelta la rata
            RespuestaHttpFalsa(200, VERSION_CATALOGO),
        )
        fuente = FuenteHttp("https://api.prueba/v1", "id", sesion, EsperaFalsa())
        with tempfile.TemporaryDirectory() as carpeta:
            resumen = descargar_datos_offline(
                fuente, GuardadorDatosOffline(carpeta), mostrar=lambda texto: None
            )
            self.assertEqual(resumen.criptas_descargadas, ["cripta-01"])
            self.assertEqual(resumen.fichas_descargadas, 4)
            self.assertEqual(resumen.solicitudes_realizadas, 7)
            self.assertEqual(resumen.lotes_de_catalogo_fallidos, [])

            # Las salas se pidieron en un solo lote y las fichas en el orden descubierto.
            self.assertEqual(sesion.solicitudes_recibidas[3]["params"], {"salas": "1,2"})
            self.assertEqual(sesion.solicitudes_recibidas[4]["params"],
                             {"ids": "itm_antorcha,ent_rata_gigante,trp_dardos"})
            self.assertEqual(sesion.solicitudes_recibidas[5]["params"], {"ids": "itm_pocion_menor"})

            # Todo lo descargado se puede leer con FuenteOffline.
            offline = FuenteOffline(carpeta)
            self.assertEqual(offline.contenido("cripta-01", [1, 2]), CONTENIDO_1_2)
            self.assertEqual(offline.catalogo(["itm_pocion_menor"])["entidades"], [FICHA_POCION])

    def test_un_lote_de_catalogo_fallido_no_detiene_la_descarga(self):
        sesion = SesionHttpFalsa(
            RespuestaHttpFalsa(200, LISTA_CRIPTAS),
            RespuestaHttpFalsa(200, DATOS_GENERALES),
            RespuestaHttpFalsa(200, PAGINA_1),
            RespuestaHttpFalsa(200, CONTENIDO_1_2),
            RespuestaHttpFalsa(404, {"error": "id desconocido"}),
            RespuestaHttpFalsa(200, VERSION_CATALOGO),
        )
        fuente = FuenteHttp("https://api.prueba/v1", "id", sesion, EsperaFalsa())
        with tempfile.TemporaryDirectory() as carpeta:
            resumen = descargar_datos_offline(
                fuente, GuardadorDatosOffline(carpeta), mostrar=lambda texto: None
            )
        self.assertEqual(len(resumen.lotes_de_catalogo_fallidos), 1)
        lote, mensaje = resumen.lotes_de_catalogo_fallidos[0]
        self.assertEqual(lote, ["itm_antorcha", "ent_rata_gigante", "trp_dardos"])
        self.assertIn("id desconocido", mensaje)


if __name__ == "__main__":
    unittest.main()
