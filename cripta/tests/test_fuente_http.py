"""
Pruebas de FuenteHttp sin usar la red.

Se reemplaza la sesión de requests por SesionHttpFalsa, que devuelve
respuestas preparadas de antemano, y la espera real por EsperaFalsa, que
solo anota cuántos segundos se habrían esperado.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import unittest
import uuid

import requests

from adapters.fuente_datos import ErrorFuenteDatos, PresupuestoAgotado
from adapters.fuente_http import (
    IDENTIFICADOR_CLIENTE_DE_ESTA_EJECUCION,
    MAXIMO_DE_REINTENTOS_POR_429,
    SEGUNDOS_DE_ESPERA_SI_EL_429_NO_LOS_INDICA,
    FuenteHttp,
)

URL_DE_PRUEBA = "https://api.prueba/v1"


class RespuestaHttpFalsa:
    def __init__(self, codigo, cuerpo=None, cuerpo_no_es_json=False):
        self.status_code = codigo
        self._cuerpo = cuerpo
        self._cuerpo_no_es_json = cuerpo_no_es_json

    def json(self):
        if self._cuerpo_no_es_json:
            raise ValueError("el cuerpo no es JSON")
        return self._cuerpo


class SesionHttpFalsa:
    """Devuelve, en orden, las respuestas (o excepciones) preparadas."""

    def __init__(self, *respuestas):
        self._respuestas = list(respuestas)
        self.solicitudes_recibidas = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.solicitudes_recibidas.append(
            {"url": url, "params": params, "headers": headers, "timeout": timeout}
        )
        siguiente = self._respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


class EsperaFalsa:
    def __init__(self):
        self.segundos_esperados = []

    def __call__(self, segundos):
        self.segundos_esperados.append(segundos)


def crear_fuente(*respuestas):
    sesion = SesionHttpFalsa(*respuestas)
    espera = EsperaFalsa()
    fuente = FuenteHttp(URL_DE_PRUEBA, "id-de-prueba", sesion, espera)
    return fuente, sesion, espera


class PruebasSolicitudesCorrectas(unittest.TestCase):

    def test_listar_criptas_devuelve_el_json(self):
        cuerpo = {"criptas": [{"id": "cripta-01", "nombre": "Osario menor", "salas": 20, "dificultad": 1}]}
        fuente, sesion, _ = crear_fuente(RespuestaHttpFalsa(200, cuerpo))
        self.assertEqual(fuente.listar_criptas(), cuerpo)
        solicitud = sesion.solicitudes_recibidas[0]
        self.assertEqual(solicitud["url"], URL_DE_PRUEBA + "/criptas")
        self.assertEqual(fuente.solicitudes_realizadas(), 1)

    def test_encabezado_y_tiempo_de_espera_en_cada_solicitud(self):
        fuente, sesion, _ = crear_fuente(RespuestaHttpFalsa(200, {}), RespuestaHttpFalsa(200, {}))
        fuente.listar_criptas()
        fuente.version_catalogo()
        for solicitud in sesion.solicitudes_recibidas:
            self.assertEqual(solicitud["headers"], {"X-Cripta-Client-Id": "id-de-prueba"})
            self.assertIsNotNone(solicitud["timeout"])

    def test_rutas_y_parametros_de_cada_operacion(self):
        fuente, sesion, _ = crear_fuente(*[RespuestaHttpFalsa(200, {}) for _ in range(6)])
        fuente.datos_generales("cripta-01")
        fuente.version_cripta("cripta-01")
        fuente.pagina_salas("cripta-01", 2)
        fuente.contenido("cripta-01", [1, 2, 3])
        fuente.catalogo(["ent_rata_gigante", "itm_antorcha"])
        fuente.version_catalogo()
        recibidas = sesion.solicitudes_recibidas
        self.assertEqual(recibidas[0]["url"], URL_DE_PRUEBA + "/criptas/cripta-01")
        self.assertEqual(recibidas[1]["url"], URL_DE_PRUEBA + "/criptas/cripta-01/version")
        self.assertEqual(recibidas[2]["url"], URL_DE_PRUEBA + "/criptas/cripta-01/salas")
        self.assertEqual(recibidas[2]["params"], {"pagina": 2})
        self.assertEqual(recibidas[3]["url"], URL_DE_PRUEBA + "/criptas/cripta-01/contenido")
        self.assertEqual(recibidas[3]["params"], {"salas": "1,2,3"})
        self.assertEqual(recibidas[4]["url"], URL_DE_PRUEBA + "/catalogo")
        self.assertEqual(recibidas[4]["params"], {"ids": "ent_rata_gigante,itm_antorcha"})
        self.assertEqual(recibidas[5]["url"], URL_DE_PRUEBA + "/catalogo/version")
        self.assertEqual(fuente.solicitudes_realizadas(), 6)

    def test_id_con_caracteres_especiales_se_codifica(self):
        fuente, sesion, _ = crear_fuente(RespuestaHttpFalsa(200, {}))
        fuente.datos_generales("cripta 01/x")
        self.assertEqual(sesion.solicitudes_recibidas[0]["url"], URL_DE_PRUEBA + "/criptas/cripta%2001%2Fx")


class PruebasIdentificadorCliente(unittest.TestCase):

    def test_es_un_uuid_valido(self):
        uuid.UUID(IDENTIFICADOR_CLIENTE_DE_ESTA_EJECUCION)  # falla si no lo es

    def test_todas_las_instancias_comparten_el_identificador(self):
        primera = FuenteHttp(sesion_http=SesionHttpFalsa())
        segunda = FuenteHttp(sesion_http=SesionHttpFalsa())
        self.assertEqual(primera.identificador_cliente(), segunda.identificador_cliente())
        self.assertEqual(primera.identificador_cliente(), IDENTIFICADOR_CLIENTE_DE_ESTA_EJECUCION)


class PruebasValidacionAntesDeEnviar(unittest.TestCase):

    def test_lote_invalido_no_envia_ni_cuenta(self):
        fuente, sesion, _ = crear_fuente()
        with self.assertRaises(ValueError):
            fuente.contenido("cripta-01", [1, 1])
        with self.assertRaises(ValueError):
            fuente.catalogo([])
        self.assertEqual(sesion.solicitudes_recibidas, [])
        self.assertEqual(fuente.solicitudes_realizadas(), 0)

    def test_pagina_invalida_no_envia(self):
        fuente, sesion, _ = crear_fuente()
        with self.assertRaises(ValueError):
            fuente.pagina_salas("cripta-01", 0)
        with self.assertRaises(TypeError):
            fuente.pagina_salas("cripta-01", "1")
        self.assertEqual(sesion.solicitudes_recibidas, [])


class PruebasHttp429(unittest.TestCase):

    def test_espera_lo_indicado_y_reintenta(self):
        fuente, sesion, espera = crear_fuente(
            RespuestaHttpFalsa(429, {"error": "demasiadas solicitudes", "reintentar_en": 12}),
            RespuestaHttpFalsa(200, {"version": "cat-2026-08-01"}),
        )
        self.assertEqual(fuente.version_catalogo(), {"version": "cat-2026-08-01"})
        self.assertEqual(espera.segundos_esperados, [12])
        self.assertEqual(fuente.solicitudes_realizadas(), 2)  # el reintento cuenta (§5.1)
        # El reintento usa el mismo identificador de cliente.
        self.assertEqual(sesion.solicitudes_recibidas[0]["headers"], sesion.solicitudes_recibidas[1]["headers"])

    def test_sin_reintentar_en_usa_la_espera_por_defecto(self):
        fuente, _, espera = crear_fuente(
            RespuestaHttpFalsa(429, cuerpo_no_es_json=True),
            RespuestaHttpFalsa(200, {}),
        )
        fuente.listar_criptas()
        self.assertEqual(espera.segundos_esperados, [SEGUNDOS_DE_ESPERA_SI_EL_429_NO_LOS_INDICA])

    def test_se_rinde_despues_del_maximo_de_reintentos(self):
        respuestas = [RespuestaHttpFalsa(429, {"error": "x", "reintentar_en": 1})
                      for _ in range(MAXIMO_DE_REINTENTOS_POR_429 + 1)]
        fuente, _, espera = crear_fuente(*respuestas)
        with self.assertRaises(ErrorFuenteDatos) as contexto:
            fuente.listar_criptas()
        self.assertEqual(contexto.exception.codigo_http, 429)
        self.assertEqual(len(espera.segundos_esperados), MAXIMO_DE_REINTENTOS_POR_429)
        self.assertEqual(fuente.solicitudes_realizadas(), MAXIMO_DE_REINTENTOS_POR_429 + 1)

    def test_sin_presupuesto_no_espera_para_reintentar(self):
        fuente, sesion, espera = crear_fuente(
            RespuestaHttpFalsa(429, {"error": "x", "reintentar_en": 12}),
        )
        fuente.establecer_presupuesto(1)
        with self.assertRaises(PresupuestoAgotado):
            fuente.listar_criptas()
        self.assertEqual(espera.segundos_esperados, [])
        self.assertEqual(len(sesion.solicitudes_recibidas), 1)


class PruebasErroresHttp(unittest.TestCase):

    def test_404_incluye_operacion_codigo_y_mensaje_del_api(self):
        fuente, _, _ = crear_fuente(RespuestaHttpFalsa(404, {"error": "cripta no encontrada"}))
        with self.assertRaises(ErrorFuenteDatos) as contexto:
            fuente.datos_generales("cripta-99")
        error = contexto.exception
        self.assertEqual(error.codigo_http, 404)
        self.assertIn("cripta-99", str(error))
        self.assertIn("cripta no encontrada", str(error))
        self.assertEqual(fuente.solicitudes_realizadas(), 1)

    def test_400_y_500(self):
        for codigo in (400, 500, 503):
            fuente, _, _ = crear_fuente(RespuestaHttpFalsa(codigo, {"error": "falla"}))
            with self.assertRaises(ErrorFuenteDatos) as contexto:
                fuente.listar_criptas()
            self.assertEqual(contexto.exception.codigo_http, codigo)

    def test_error_sin_cuerpo_json(self):
        fuente, _, _ = crear_fuente(RespuestaHttpFalsa(500, cuerpo_no_es_json=True))
        with self.assertRaises(ErrorFuenteDatos):
            fuente.listar_criptas()

    def test_respuesta_200_que_no_es_json(self):
        fuente, _, _ = crear_fuente(RespuestaHttpFalsa(200, cuerpo_no_es_json=True))
        with self.assertRaises(ErrorFuenteDatos) as contexto:
            fuente.listar_criptas()
        self.assertIn("JSON", str(contexto.exception))

    def test_tiempo_agotado(self):
        fuente, _, _ = crear_fuente(requests.Timeout("lento"))
        with self.assertRaises(ErrorFuenteDatos) as contexto:
            fuente.listar_criptas()
        self.assertIn("no respondió", str(contexto.exception))
        self.assertEqual(fuente.solicitudes_realizadas(), 1)  # la solicitud salió y cuenta

    def test_sin_conexion(self):
        fuente, _, _ = crear_fuente(requests.ConnectionError("sin red"))
        with self.assertRaises(ErrorFuenteDatos) as contexto:
            fuente.listar_criptas()
        self.assertIn("conectar", str(contexto.exception))

    def test_otro_error_de_requests(self):
        fuente, _, _ = crear_fuente(requests.TooManyRedirects("redirecciones"))
        with self.assertRaises(ErrorFuenteDatos):
            fuente.listar_criptas()


class PruebasPresupuestoHttp(unittest.TestCase):

    def test_no_envia_al_agotar_el_presupuesto(self):
        fuente, sesion, _ = crear_fuente(RespuestaHttpFalsa(200, {}), RespuestaHttpFalsa(200, {}))
        fuente.establecer_presupuesto(1)
        fuente.listar_criptas()
        with self.assertRaises(PresupuestoAgotado):
            fuente.version_catalogo()
        self.assertEqual(len(sesion.solicitudes_recibidas), 1)


if __name__ == "__main__":
    unittest.main()
