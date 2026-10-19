"""
FuenteHttp: obtiene los datos del API real de CRIPTA (bloque 2).

Requisitos del enunciado que cumple
    - Encabezado X-Cripta-Client-Id en todas las solicitudes, con un UUID
      generado una sola vez por ejecución y reutilizado, incluso en los
      reintentos (sección inicial del enunciado).
    - Tiempo de espera explícito en cada solicitud.
    - HTTP 429: espera los segundos de "reintentar_en" y vuelve a intentar,
      sin que el programa se caiga. Cada reintento cuenta en el presupuesto
      (§3.1 y §5.1).
    - Cualquier otro código, un tiempo agotado o una falla de conexión se
      reportan con ErrorFuenteDatos, que incluye la operación que falló
      (§3.1). Nunca escapa una excepción de requests sin contexto.
    - La espera es tiempo real: esta clase no conoce el reloj virtual del
      juego, así que no puede alterarlo (§3.1).

Cómo se prueba sin red
    El constructor recibe la sesión HTTP y la función de espera. En las
    pruebas se le pasan versiones falsas: así no se usa la red ni se
    esperan de verdad los segundos de un 429.
"""
import time
import uuid
from urllib.parse import quote

import requests

from adapters.fuente_datos import (
    ErrorFuenteDatos,
    FuenteDatos,
    PresupuestoAgotado,
    validar_ids_catalogo,
    validar_ids_salas,
    validar_numero_de_pagina,
)

URL_BASE_DEL_API = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
SEGUNDOS_DE_ESPERA_POR_SOLICITUD = 10
MAXIMO_DE_REINTENTOS_POR_429 = 5
SEGUNDOS_DE_ESPERA_SI_EL_429_NO_LOS_INDICA = 5

# Se genera al importar el módulo, que ocurre una sola vez por ejecución.
# Así todas las instancias de FuenteHttp de esta ejecución comparten el
# mismo identificador, aunque se cree una nueva por partida.
IDENTIFICADOR_CLIENTE_DE_ESTA_EJECUCION = str(uuid.uuid4())

_DESCRIPCION_DE_CODIGOS_HTTP = (
    (400, "el API rechazó la solicitud por estar mal formada"),
    (404, "el recurso solicitado no existe"),
    (500, "el API tiene contenido publicado inválido"),
)


class FuenteHttp(FuenteDatos):
    """Fuente de datos que consulta el API por HTTP."""

    def __init__(
        self,
        url_base=URL_BASE_DEL_API,
        identificador_cliente=IDENTIFICADOR_CLIENTE_DE_ESTA_EJECUCION,
        sesion_http=None,
        funcion_de_espera=time.sleep,
        segundos_de_espera_por_solicitud=SEGUNDOS_DE_ESPERA_POR_SOLICITUD,
    ):
        super().__init__()
        self._url_base = url_base.rstrip("/")
        self._identificador_cliente = identificador_cliente
        # Una sesión reutiliza la conexión con el servidor entre solicitudes.
        self._sesion_http = sesion_http if sesion_http is not None else requests.Session()
        self._esperar = funcion_de_espera
        self._segundos_de_espera_por_solicitud = segundos_de_espera_por_solicitud
        self._encabezados = {"X-Cripta-Client-Id": identificador_cliente}

    def identificador_cliente(self):
        return self._identificador_cliente

    def descripcion_del_origen(self):
        return f"API en red ({self._url_base})"

    # ------------------------------------------------------------------
    # Operaciones del contrato FuenteDatos
    # ------------------------------------------------------------------

    def listar_criptas(self):
        return self._pedir_json("listar las criptas", "/criptas")

    def datos_generales(self, id_cripta):
        return self._pedir_json(
            f"obtener los datos generales de {id_cripta}",
            f"/criptas/{_segmento_de_ruta(id_cripta)}",
        )

    def version_cripta(self, id_cripta):
        return self._pedir_json(
            f"obtener la versión de {id_cripta}",
            f"/criptas/{_segmento_de_ruta(id_cripta)}/version",
        )

    def pagina_salas(self, id_cripta, pagina):
        validar_numero_de_pagina(pagina)
        return self._pedir_json(
            f"descargar la página {pagina} de salas de {id_cripta}",
            f"/criptas/{_segmento_de_ruta(id_cripta)}/salas",
            {"pagina": pagina},
        )

    def contenido(self, id_cripta, ids_salas):
        validar_ids_salas(ids_salas)
        texto_de_salas = ",".join(str(id_sala) for id_sala in ids_salas)
        return self._pedir_json(
            f"descargar el contenido de las salas {texto_de_salas} de {id_cripta}",
            f"/criptas/{_segmento_de_ruta(id_cripta)}/contenido",
            {"salas": texto_de_salas},
        )

    def catalogo(self, ids):
        validar_ids_catalogo(ids)
        texto_de_ids = ",".join(ids)
        return self._pedir_json(
            f"descargar las fichas {texto_de_ids} del catálogo",
            "/catalogo",
            {"ids": texto_de_ids},
        )

    def version_catalogo(self):
        return self._pedir_json("obtener la versión del catálogo", "/catalogo/version")

    # ------------------------------------------------------------------
    # Envío de solicitudes
    # ------------------------------------------------------------------

    def _pedir_json(self, operacion, ruta, parametros=None):
        """Envía GET hasta obtener una respuesta útil y devuelve su JSON.

        Solo se reintenta después de HTTP 429. Cualquier otro problema se
        reporta de inmediato con ErrorFuenteDatos.
        """
        reintentos_hechos = 0
        while True:
            self._consumir_solicitud(operacion)  # cuenta, o lanza PresupuestoAgotado
            respuesta = self._enviar_get(operacion, ruta, parametros)

            if respuesta.status_code == 200:
                return _leer_json_de_respuesta(operacion, respuesta)

            if respuesta.status_code != 429:
                raise ErrorFuenteDatos(
                    operacion, _describir_error_http(respuesta), respuesta.status_code
                )

            if reintentos_hechos >= MAXIMO_DE_REINTENTOS_POR_429:
                raise ErrorFuenteDatos(
                    operacion,
                    f"el API siguió limitando la frecuencia después de "
                    f"{reintentos_hechos} reintentos",
                    429,
                )
            # Si ya no queda presupuesto, no tiene sentido esperar.
            if self.solicitudes_restantes() == 0:
                raise PresupuestoAgotado(operacion, self.presupuesto())
            self._esperar(_segundos_para_reintentar(respuesta))
            reintentos_hechos += 1

    def _enviar_get(self, operacion, ruta, parametros):
        segundos = self._segundos_de_espera_por_solicitud
        try:
            return self._sesion_http.get(
                self._url_base + ruta,
                params=parametros,
                headers=self._encabezados,
                timeout=segundos,
            )
        except requests.Timeout as error:
            raise ErrorFuenteDatos(
                operacion, f"el servidor no respondió en {segundos} segundos"
            ) from error
        except requests.ConnectionError as error:
            raise ErrorFuenteDatos(
                operacion, "no se pudo conectar con el servidor; revise la conexión a internet"
            ) from error
        except requests.RequestException as error:
            raise ErrorFuenteDatos(operacion, f"falló la solicitud ({error})") from error


# ----------------------------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------------------------

def _segmento_de_ruta(texto):
    """Codifica un id para usarlo dentro de la URL (por ejemplo, espacios)."""
    return quote(str(texto), safe="")


def _leer_json_de_respuesta(operacion, respuesta):
    try:
        return respuesta.json()
    except ValueError as error:  # requests lanza una subclase de ValueError
        raise ErrorFuenteDatos(operacion, "la respuesta no es JSON válido", 200) from error


def _mensaje_del_servidor(respuesta):
    """El campo "error" del cuerpo, si el API lo envió."""
    try:
        cuerpo = respuesta.json()
    except ValueError:
        return None
    if isinstance(cuerpo, dict) and isinstance(cuerpo.get("error"), str):
        return cuerpo["error"]
    return None


def _describir_error_http(respuesta):
    descripcion = "el API respondió con un código inesperado"
    for codigo, texto in _DESCRIPCION_DE_CODIGOS_HTTP:
        if respuesta.status_code == codigo:
            descripcion = texto
    mensaje_del_servidor = _mensaje_del_servidor(respuesta)
    if mensaje_del_servidor:
        descripcion += f" ({mensaje_del_servidor})"
    return descripcion


def _segundos_para_reintentar(respuesta):
    """Lee "reintentar_en" del cuerpo del 429; si falta, usa un valor por defecto."""
    try:
        cuerpo = respuesta.json()
    except ValueError:
        return SEGUNDOS_DE_ESPERA_SI_EL_429_NO_LOS_INDICA
    if isinstance(cuerpo, dict):
        segundos = cuerpo.get("reintentar_en")
        if isinstance(segundos, int) and not isinstance(segundos, bool) and segundos >= 1:
            return segundos
    return SEGUNDOS_DE_ESPERA_SI_EL_429_NO_LOS_INDICA
