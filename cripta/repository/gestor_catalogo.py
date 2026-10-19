"""
Gestor del catálogo: une memoria, disco y red (problemas 4.3 y 4.4).

Problema que resuelve
    Antes de mostrar o simular una entidad, su id de tipo debe resolverse a
    una ficha del catálogo (§4.3). Los ids se descubren en orden no
    controlado, se repiten entre salas y pueden reutilizarse entre criptas.
    Pedir cada id por separado no cabe en el presupuesto, y un id vigente no
    se debe pedir dos veces si ya está en memoria o en disco.

Dónde busca una ficha (de lo más barato a lo más caro)
    1. CacheCatalogo (memoria, LRU con tope --cache-size)
    2. AlmacenFichas (disco, validado por la versión del catálogo)
    3. El API, en lotes de hasta 10 ids

Cómo se usa
    iniciar(version)              una vez por partida: abre el disco con la
                                  versión del catálogo (si no se indica, la
                                  pide a la fuente: 1 solicitud).
    asegurar_fichas(ids)          antes de entrar a una sala o cuando un
                                  enemigo suelta objetos: deja esos ids
                                  disponibles, descargando lo que falte.
    anotar_ids_conocidos(ids)     registra ids descubiertos que todavía no
                                  hacen falta, para usarlos de relleno.
    obtener_ficha(id)             nunca usa la red: memoria y luego disco.
    estadisticas()                datos para el reporte final (§5.1).

Armado de los lotes (decisión D4)
    Primero van los ids que hacen falta ahora. Si el lote tiene espacio, se
    completa con ids conocidos que todavía no se descargaron, en el orden en
    que se descubrieron. Una solicitud con 10 ids cuesta lo mismo que con 1
    (§3.4), así que el relleno ahorra solicitudes futuras. El orden de
    descubrimiento es determinista, así que los lotes también lo son.

Lo que sueltan los enemigos
    Cuando llega la ficha de un enemigo, los ids de su campo "suelta" se
    anotan como conocidos y se descargan como relleno en el siguiente lote.

Aciertos y fallos para el reporte (§5.1)
    Acierto de caché: la ficha se obtuvo sin usar la red (memoria o disco).
    Fallo de caché: un id que hacía falta no estaba ni en memoria ni en
    disco y hubo que descargarlo.

Si falla el disco
    Si no se puede guardar en disco (por ejemplo, otro programa bloquea el
    archivo), el juego sigue: las fichas quedan en un respaldo en memoria
    que no se desaloja y el reporte lo avisa.

Complejidad
    obtener_ficha: O(1) promedio en memoria; si no, O(log n) en el índice
    del disco más la lectura de esa ficha.
    asegurar_fichas: por cada id, O(1) en memoria u O(log n) en disco. Armar
    un lote recorre los ids conocidos, O(p); es despreciable frente a los
    ~400 ms de la solicitud que se ahorra.
"""
from adapters.almacen_fichas import ErrorAlmacenDisco
from adapters.fuente_datos import MAXIMO_POR_LOTE, ErrorFuenteDatos
from structures.lista_sin_repetidos import ListaSinRepetidos
from structures.tabla_hash import TablaHash


class FichaNoDisponible(Exception):
    """Se pidió una ficha que no está disponible (o el API no la devolvió)."""

    def __init__(self, id_ficha, motivo):
        self.id_ficha = id_ficha
        self.motivo = motivo
        super().__init__(f"La ficha {id_ficha!r} no está disponible: {motivo}")


class EstadisticasCatalogo:
    """Fotografía de los contadores del gestor, para el reporte final."""

    def __init__(self):
        self.version_catalogo = None
        self.aciertos_en_memoria = 0
        self.recuperaciones_desde_disco = 0
        self.fichas_que_hubo_que_descargar = 0
        self.fichas_descargadas = 0
        self.lotes_de_catalogo_descargados = 0
        self.desalojos_de_memoria = 0
        self.exceso_maximo_sobre_capacidad = 0
        self.fallos_al_guardar_en_disco = 0
        self.avisos = []

    def aciertos_de_cache(self):
        """Fichas obtenidas sin usar la red (memoria o disco)."""
        return self.aciertos_en_memoria + self.recuperaciones_desde_disco

    def fallos_de_cache(self):
        """Fichas necesarias que hubo que descargar."""
        return self.fichas_que_hubo_que_descargar


class GestorCatalogo:
    """Entrega fichas del catálogo buscando en memoria, disco y red."""

    def __init__(self, fuente, almacen, cache):
        self._fuente = fuente
        self._almacen = almacen
        self._cache = cache
        self._version_catalogo = None
        self._ids_conocidos = ListaSinRepetidos()
        # Respaldo solo para fichas que no se pudieron guardar en disco.
        self._fichas_sin_disco = TablaHash()

        self._aciertos_en_respaldo = 0
        self._recuperaciones_desde_disco = 0
        self._fichas_que_hubo_que_descargar = 0
        self._fichas_descargadas = 0
        self._lotes_descargados = 0
        self._fallos_al_guardar_en_disco = 0
        self._avisos = []

    # ------------------------------------------------------------------
    # Inicio
    # ------------------------------------------------------------------

    def iniciar(self, version_vigente=None):
        """Abre el almacén en disco con la versión vigente del catálogo.
        Si no se indica la versión, la pide a la fuente (1 solicitud)."""
        version = version_vigente
        if version is None:
            version = self._fuente.version_catalogo()["version"]
        if self._version_catalogo is not None and version != self._version_catalogo:
            # Lo que haya en memoria es de otra versión: ya no sirve.
            self._cache.vaciar()
            self._fichas_sin_disco = TablaHash()
        self._version_catalogo = version
        try:
            self._almacen.abrir(version)
        except ErrorAlmacenDisco as error:
            self._avisos.append(f"Se juega sin caché en disco: {error}")
        motivo = self._almacen.motivo_del_ultimo_descarte()
        if motivo:
            self._avisos.append(f"Caché en disco reiniciada: {motivo}")

    def version_catalogo(self):
        return self._version_catalogo

    # ------------------------------------------------------------------
    # Operaciones principales
    # ------------------------------------------------------------------

    def anotar_ids_conocidos(self, ids):
        """Recuerda ids descubiertos para usarlos de relleno en los lotes."""
        self._exigir_iniciado()
        for id_ficha in ids:
            _validar_id_de_ficha(id_ficha)
            if not self._esta_disponible(id_ficha):
                self._ids_conocidos.agregar(id_ficha)

    def asegurar_fichas(self, ids):
        """Deja disponibles (en memoria o en disco) todas las fichas pedidas,
        descargando en lotes las que falten.

        Puede lanzar PresupuestoAgotado o ErrorFuenteDatos (desde la fuente)
        y FichaNoDisponible si el API no devuelve un id pedido.
        """
        self._exigir_iniciado()
        necesarias = ListaSinRepetidos()
        for id_ficha in ids:
            _validar_id_de_ficha(id_ficha)
            if not self._esta_disponible(id_ficha):
                necesarias.agregar(id_ficha)
                self._ids_conocidos.agregar(id_ficha)
        self._fichas_que_hubo_que_descargar += necesarias.cantidad()

        while True:
            faltantes = [id_ficha for id_ficha in necesarias.elementos
                         if not self._esta_disponible(id_ficha)]
            if not faltantes:
                return
            necesarias_en_este_lote = faltantes[:MAXIMO_POR_LOTE]
            lote = list(necesarias_en_este_lote)
            self._completar_lote_con_conocidos(lote)
            self._descargar_lote(lote)
            for id_ficha in necesarias_en_este_lote:
                if not self._esta_disponible(id_ficha):
                    raise FichaNoDisponible(id_ficha, "el API no la devolvió")

    def obtener_ficha(self, id_ficha):
        """Devuelve la ficha desde memoria o disco. Nunca usa la red: antes
        hay que haber llamado a asegurar_fichas con ese id."""
        self._exigir_iniciado()
        ficha = self._cache.obtener_ficha(id_ficha)
        if ficha is not None:
            return ficha

        ficha = self._fichas_sin_disco.obtener(id_ficha)
        if ficha is not None:
            self._aciertos_en_respaldo += 1
        else:
            ficha = self._almacen.leer_ficha(id_ficha)
            if ficha is None:
                raise FichaNoDisponible(
                    id_ficha, "no está en memoria ni en disco; falta llamar a asegurar_fichas"
                )
            self._recuperaciones_desde_disco += 1
        self._cache.agregar_ficha(id_ficha, ficha)
        return ficha

    def estadisticas(self):
        resultado = EstadisticasCatalogo()
        resultado.version_catalogo = self._version_catalogo
        resultado.aciertos_en_memoria = self._cache.aciertos_en_memoria() + self._aciertos_en_respaldo
        resultado.recuperaciones_desde_disco = self._recuperaciones_desde_disco
        resultado.fichas_que_hubo_que_descargar = self._fichas_que_hubo_que_descargar
        resultado.fichas_descargadas = self._fichas_descargadas
        resultado.lotes_de_catalogo_descargados = self._lotes_descargados
        resultado.desalojos_de_memoria = self._cache.cantidad_de_desalojos()
        resultado.exceso_maximo_sobre_capacidad = self._cache.exceso_maximo_sobre_capacidad()
        resultado.fallos_al_guardar_en_disco = self._fallos_al_guardar_en_disco
        resultado.avisos = list(self._avisos)
        return resultado

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _esta_disponible(self, id_ficha):
        return (self._cache.contiene_ficha(id_ficha)
                or self._fichas_sin_disco.contiene(id_ficha)
                or self._almacen.contiene_ficha(id_ficha))

    def _completar_lote_con_conocidos(self, lote):
        """Agrega al lote ids conocidos pendientes hasta llegar a 10."""
        for id_ficha in self._ids_conocidos.elementos:
            if len(lote) >= MAXIMO_POR_LOTE:
                return
            if id_ficha not in lote and not self._esta_disponible(id_ficha):
                lote.append(id_ficha)

    def _descargar_lote(self, lote):
        respuesta = self._fuente.catalogo(lote)
        fichas = respuesta.get("entidades") if isinstance(respuesta, dict) else None
        if not isinstance(fichas, list):
            raise ErrorFuenteDatos("descargar fichas del catálogo", "la respuesta no trae 'entidades'")
        for ficha in fichas:
            if not isinstance(ficha, dict) or not isinstance(ficha.get("id"), str) or not ficha["id"]:
                raise ErrorFuenteDatos("descargar fichas del catálogo", "el API devolvió una ficha sin id")
        self._lotes_descargados += 1

        try:
            self._almacen.guardar_fichas(fichas)
        except ErrorAlmacenDisco as error:
            self._fallos_al_guardar_en_disco += 1
            self._avisos.append(f"Fichas guardadas solo en memoria: {error}")
            for ficha in fichas:
                self._fichas_sin_disco.insertar(ficha["id"], ficha)

        for ficha in fichas:
            self._fichas_descargadas += 1
            self._cache.agregar_ficha(ficha["id"], ficha)
            if ficha.get("clase") == "enemigo":
                self.anotar_ids_conocidos(ficha.get("suelta") or [])

    def _exigir_iniciado(self):
        if self._version_catalogo is None:
            raise RuntimeError("Primero hay que llamar a iniciar()")


def _validar_id_de_ficha(id_ficha):
    if not isinstance(id_ficha, str) or not id_ficha:
        raise ValueError(f"Un id de ficha debe ser un texto no vacío: {id_ficha!r}")
