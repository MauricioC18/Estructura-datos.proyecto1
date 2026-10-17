"""
Contrato común de las fuentes de datos de CRIPTA (bloque 2).

Problema que resuelve
    §3.4 exige que --offline lea los datos desde disco "a través del mismo
    contrato lógico que usa el cliente de red", y §6 que el modelo no sepa
    si los datos vinieron de HTTP o de archivos. FuenteDatos es ese
    contrato: FuenteHttp y FuenteOffline lo implementan, y el resto del
    programa solo conoce FuenteDatos.

Qué devuelve cada método
    Exactamente el cuerpo JSON que devuelve el API, ya convertido por json
    en listas y diccionarios de Python, con la forma documentada en el
    Swagger. La fuente no interpreta los datos: convertirlos en objetos del
    modelo es trabajo del Traductor. §7 permite esos diccionarios solo para
    leer el JSON; nadie debe guardarlos como índice ni como caché.

Quién la usa
    Solo RepositorioCripta y sus gestores. El modelo nunca la importa.
    El controlador crea la fuente al iniciar (FuenteHttp o FuenteOffline,
    según --offline) y se la entrega al RepositorioCripta.

Presupuesto de solicitudes (§5.1)
    La cuenta vive en la fuente, porque es la única que sabe cuándo sale
    una solicitud real a la red. FuenteOffline nunca la incrementa (leer
    de disco no cuenta). Supuestos del grupo:
      - La cuenta de una partida empieza con reiniciar_conteo(), antes de
        listar las criptas, porque §5.1 incluye la lista en el conteo.
      - El presupuesto se conoce después de datos_generales(); las
        solicitudes hechas antes ya cuentan.
      - Toda solicitud enviada cuenta, aunque falle (tiempo agotado,
        HTTP 4xx o 5xx), y cada reintento tras HTTP 429 cuenta aparte.
      - Si no queda presupuesto, la fuente rechaza la solicitud sin
        enviarla (PresupuestoAgotado). Los gestores deben consultar
        solicitudes_restantes() antes, para planificar la precarga.

Ruta excluida a propósito
    GET /catalogo/<id> no forma parte del contrato: cuesta lo mismo que un
    lote de 10 fichas (§3.3), así que usarla solo desperdiciaría
    presupuesto.

Nota para la precarga en segundo plano (D1, opción b)
    Si más adelante una fuente se usa desde otro hilo, _consumir_solicitud
    debe protegerse con un candado (threading.Lock).
"""
from abc import ABC, abstractmethod

MAXIMO_POR_LOTE = 10  # límite del API para contenido y catálogo (Swagger)


class ErrorFuenteDatos(Exception):
    """Error al obtener datos, con la operación que falló (§3.1)."""

    def __init__(self, operacion, detalle, codigo_http=None):
        self.operacion = operacion
        self.detalle = detalle
        self.codigo_http = codigo_http
        mensaje = f"No se pudo {operacion}: {detalle}"
        if codigo_http is not None:
            mensaje += f" (HTTP {codigo_http})"
        super().__init__(mensaje)


class PresupuestoAgotado(ErrorFuenteDatos):
    """La partida ya hizo todas las solicitudes que permite su cripta."""

    def __init__(self, operacion, presupuesto):
        super().__init__(
            operacion,
            f"se agotó el presupuesto de {presupuesto} solicitudes de esta partida",
        )
        self.presupuesto = presupuesto


def validar_ids_salas(ids_salas):
    """Exige una lista de 1 a 10 enteros distintos.

    Se valida antes de enviar porque una solicitud que el API rechaza con
    HTTP 400 también gasta presupuesto.
    """
    _validar_lote(ids_salas, int, "salas")


def validar_ids_catalogo(ids):
    """Exige una lista de 1 a 10 textos distintos y no vacíos."""
    _validar_lote(ids, str, "ids de catálogo")


def validar_numero_de_pagina(pagina):
    """Exige un entero mayor o igual a 1 (las páginas del API empiezan en 1)."""
    if isinstance(pagina, bool) or not isinstance(pagina, int):
        raise TypeError(f"El número de página debe ser un entero: {pagina!r}")
    if pagina < 1:
        raise ValueError(f"Las páginas empiezan en 1: {pagina}")


def _validar_lote(elementos, tipo, nombre):
    if not isinstance(elementos, list):
        raise TypeError(f"Las {nombre} deben venir en una lista")
    if not 1 <= len(elementos) <= MAXIMO_POR_LOTE:
        raise ValueError(
            f"Se piden entre 1 y {MAXIMO_POR_LOTE} {nombre} por solicitud; "
            f"llegaron {len(elementos)}"
        )
    for posicion in range(len(elementos)):
        elemento = elementos[posicion]
        if isinstance(elemento, bool) or not isinstance(elemento, tipo):
            raise TypeError(f"Valor no válido en {nombre}: {elemento!r}")
        if tipo is str and elemento == "":
            raise ValueError(f"Hay un valor vacío en {nombre}")
        # Con 10 elementos como máximo basta comparar con los anteriores.
        for anterior in range(posicion):
            if elementos[anterior] == elemento:
                raise ValueError(f"Valor repetido en {nombre}: {elemento!r}")


class FuenteDatos(ABC):
    """Contrato común de FuenteHttp y FuenteOffline.

    Cada método de datos corresponde a una ruta del API y devuelve su
    cuerpo JSON tal como lo describe el Swagger. Todos pueden lanzar
    ErrorFuenteDatos (o su subclase PresupuestoAgotado).
    """

    def __init__(self):
        self._realizadas = 0
        self._presupuesto = None

    # ------------------------------------------------------------------
    # Datos: una operación por ruta del API
    # ------------------------------------------------------------------

    @abstractmethod
    def listar_criptas(self):
        """GET /criptas

        Devuelve {"criptas": [{"id", "nombre", "salas", "dificultad"}, ...]}.
        """

    @abstractmethod
    def datos_generales(self, id_cripta):
        """GET /criptas/{id_cripta}

        Devuelve {"id", "version", "salas_total", "paginas",
        "salas_por_pagina", "sala_inicial", "sala_salida", "llave_salida",
        "presupuesto_solicitudes", "inventario_max",
        "jugador": {"vida_max", "ataque", "defensa", "velocidad"}}.
        """

    @abstractmethod
    def version_cripta(self, id_cripta):
        """GET /criptas/{id_cripta}/version

        Devuelve {"id", "version"}. Cuesta lo mismo que datos_generales(),
        que ya incluye la versión, así que solo conviene cuando no hacen
        falta los demás datos generales.
        """

    @abstractmethod
    def pagina_salas(self, id_cripta, pagina):
        """GET /criptas/{id_cripta}/salas?pagina={pagina}  (pagina empieza en 1)

        Devuelve {"pagina", "total_paginas", "salas": [...]}. Cada sala trae
        "id" y "nombre", y puede traer "salidas": {"N"|"S"|"E"|"O":
        {"sala", "cerrada"?, "llave"?, "cierre_automatico"?}}. Los campos
        marcados con ? pueden faltar o venir en null.
        """

    @abstractmethod
    def contenido(self, id_cripta, ids_salas):
        """GET /criptas/{id_cripta}/contenido?salas=...

        ids_salas: lista de 1 a 10 enteros distintos (validar_ids_salas).
        Devuelve {"contenido": [{"sala", "enemigos"?, "objetos"?,
        "trampas"?}, ...]}. El orden de las entradas no está garantizado:
        cada una se ubica por su campo "sala".
        """

    @abstractmethod
    def catalogo(self, ids):
        """GET /catalogo?ids=...

        ids: lista de 1 a 10 textos distintos (validar_ids_catalogo).
        Devuelve {"entidades": [...]}; el campo "clase" de cada ficha indica
        su tipo (enemigo, arma, armadura, pocion, antidoto, llave, antorcha,
        pergamino_retroceso o trampa). Cada ficha se ubica por su "id".
        """

    @abstractmethod
    def version_catalogo(self):
        """GET /catalogo/version

        Devuelve {"version"}.
        """

    def descripcion_del_origen(self):
        """Texto para el reporte final: de dónde vienen los datos."""
        return "fuente de datos"

    # ------------------------------------------------------------------
    # Presupuesto de solicitudes
    # ------------------------------------------------------------------

    def reiniciar_conteo(self):
        """Empieza la cuenta de una partida nueva, sin presupuesto conocido."""
        self._realizadas = 0
        self._presupuesto = None

    def establecer_presupuesto(self, maximo):
        """Fija el presupuesto_solicitudes de la cripta elegida."""
        if maximo < 0:
            raise ValueError("El presupuesto no puede ser negativo")
        self._presupuesto = maximo

    def solicitudes_realizadas(self):
        return self._realizadas

    def presupuesto(self):
        """El presupuesto de la partida, o None si todavía no se conoce."""
        return self._presupuesto

    def solicitudes_restantes(self):
        """Solicitudes que quedan, o None si todavía no hay presupuesto."""
        if self._presupuesto is None:
            return None
        return max(0, self._presupuesto - self._realizadas)

    def _consumir_solicitud(self, operacion):
        """Las fuentes de red lo llaman justo antes de cada envío,
        incluidos los reintentos tras HTTP 429. Si no queda presupuesto,
        lanza PresupuestoAgotado y la solicitud no se envía ni se cuenta.
        """
        if self._presupuesto is not None and self._realizadas >= self._presupuesto:
            raise PresupuestoAgotado(operacion, self._presupuesto)
        self._realizadas += 1
