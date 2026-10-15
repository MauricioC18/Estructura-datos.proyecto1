"""
Gestor del contenido de las salas, con precarga por BFS (problema 4.2).

Problema que resuelve
    Antes de confirmar que el jugador entra a una sala, su contenido
    (enemigos, objetos, trampas) debe estar en memoria (§2.5, §4.2). Pedirlo
    justo al cruzar la puerta costaría ~400 ms en cada movimiento. Una
    solicitud de contenido acepta hasta 10 salas y cuesta casi lo mismo con
    1 que con 10 (§3.4), y una sala ya pedida no se vuelve a pedir.

Cómo funciona
    precargar_alrededor_de(sala_actual)
        Se llama al iniciar la partida y después de cada acción del jugador.
        Si la sala actual o alguna vecina directa todavía no tiene contenido,
        recorre el mapa en anchura (BFS) desde la sala actual y pide en una
        sola solicitud las 10 salas más cercanas que falten.
    asegurar_contenido(id_sala)
        Se llama antes de confirmar una entrada. Si la precarga ya trajo la
        sala, no hace nada. Si no (por ejemplo, porque la precarga se detuvo
        por falta de presupuesto), pide un lote empezando por esa sala y lo
        cuenta como una "espera en la puerta".
    contenido_de_sala(id_sala)
        Devuelve la entrada de contenido tal como la mandó el API.

Por qué la precarga solo se activa si falta un vecino directo
    Así no se gasta presupuesto por adelantado sin necesidad. Y como cada
    lote se llena hasta 10 salas, una sola solicitud cubre varios pasos.

Si quedan pocas solicitudes
    Si quedan RESERVA_DE_SOLICITUDES o menos, la precarga se detiene: el
    contenido solo se pide cuando el jugador intenta entrar a una sala sin
    contenido (y después hará falta otra solicitud para sus fichas).

Determinismo (§2.4)
    Las solicitudes son síncronas (decisión D1, opción a): nunca queda una
    respuesta pendiente, y el contenido entra al modelo cuando el jugador
    entra a la sala (D2). El orden de llegada de las respuestas no puede
    cambiar la partida.

Relación con el catálogo
    Cada vez que llega contenido, los tipos de enemigos, objetos y trampas
    se anotan en el GestorCatalogo como ids conocidos, para que sirvan de
    relleno en sus lotes.

Persistencia (§4.4)
    El gestor no escribe en disco. Quien lo crea puede:
      - entregarle con incorporar_contenido_guardado() el contenido que ya
        estaba en disco (de la misma versión de la cripta), que nunca se
        vuelve a pedir;
      - pasarle una función guardar_contenido, que recibe la lista de
        entradas nuevas cada vez que se descarga un lote.

Complejidad
    tiene_contenido, contenido_de_sala: O(1) promedio (TablaHash).
    precargar_alrededor_de: revisar la sala y sus vecinas es O(salidas);
        armar un lote es un BFS que se detiene al juntar 10 salas, O(V + E)
        en el peor caso. Ocurre solo cuando hace falta pedir.
"""
from adapters.fuente_datos import MAXIMO_POR_LOTE, ErrorFuenteDatos
from structures.tabla_hash import TablaHash

RESERVA_DE_SOLICITUDES = 2  # una para contenido y otra para sus fichas


class ContenidoNoDisponible(Exception):
    """Se pidió el contenido de una sala que no está disponible."""

    def __init__(self, id_sala, motivo):
        self.id_sala = id_sala
        self.motivo = motivo
        super().__init__(f"El contenido de la sala {id_sala} no está disponible: {motivo}")


class EstadisticasContenido:
    def __init__(self):
        self.lotes_de_contenido = 0
        self.salas_descargadas = 0
        self.salas_recuperadas_de_disco = 0
        self.esperas_en_la_puerta = 0
        self.precargas_omitidas_por_presupuesto = 0


class GestorContenido:
    """Mantiene en memoria el contenido de las salas y lo precarga por BFS."""

    def __init__(self, fuente, id_cripta, grafo, gestor_catalogo=None, guardar_contenido=None):
        self._fuente = fuente
        self._id_cripta = id_cripta
        self._grafo = grafo
        self._gestor_catalogo = gestor_catalogo
        self._guardar_contenido = guardar_contenido
        self._contenido_por_sala = TablaHash()
        self._estadisticas = EstadisticasContenido()

    def incorporar_contenido_guardado(self, entradas):
        """Agrega contenido leído del disco (misma versión de la cripta).
        Esas salas ya no se pedirán al API."""
        for entrada in entradas:
            id_sala = entrada.get("sala") if isinstance(entrada, dict) else None
            if isinstance(id_sala, bool) or not isinstance(id_sala, int):
                continue  # un archivo dañado no impide jugar: esa sala se volverá a pedir
            if self.tiene_contenido(id_sala) or not self._grafo.contiene_sala(id_sala):
                continue
            self._contenido_por_sala.insertar(id_sala, entrada)
            self._estadisticas.salas_recuperadas_de_disco += 1
            if self._gestor_catalogo is not None:
                self._gestor_catalogo.anotar_ids_conocidos(tipos_de_la_sala(entrada))

    # ------------------------------------------------------------------
    # Operaciones principales
    # ------------------------------------------------------------------

    def precargar_alrededor_de(self, sala_actual):
        """Pide contenido si falta en la sala actual o en una vecina directa.
        Devuelve True si hizo una solicitud."""
        if self._sala_y_vecinas_tienen_contenido(sala_actual):
            return False
        restantes = self._fuente.solicitudes_restantes()
        if restantes is not None and restantes <= RESERVA_DE_SOLICITUDES:
            self._estadisticas.precargas_omitidas_por_presupuesto += 1
            return False
        self._descargar_lote_desde(sala_actual)
        return True

    def asegurar_contenido(self, id_sala):
        """Garantiza el contenido de una sala antes de entrar a ella.
        Puede lanzar PresupuestoAgotado o ErrorFuenteDatos (de la fuente) y
        ContenidoNoDisponible si el API no devuelve esa sala."""
        if self.tiene_contenido(id_sala):
            return
        self._estadisticas.esperas_en_la_puerta += 1
        self._descargar_lote_desde(id_sala)
        if not self.tiene_contenido(id_sala):
            raise ContenidoNoDisponible(id_sala, "el API no devolvió su contenido")

    def tiene_contenido(self, id_sala):
        return self._contenido_por_sala.contiene(id_sala)

    def contenido_de_sala(self, id_sala):
        """La entrada de contenido de la sala, tal como la mandó el API."""
        entrada = self._contenido_por_sala.obtener(id_sala)
        if entrada is None:
            raise ContenidoNoDisponible(id_sala, "falta llamar a asegurar_contenido")
        return entrada

    def estadisticas(self):
        copia = EstadisticasContenido()
        copia.lotes_de_contenido = self._estadisticas.lotes_de_contenido
        copia.salas_descargadas = self._estadisticas.salas_descargadas
        copia.salas_recuperadas_de_disco = self._estadisticas.salas_recuperadas_de_disco
        copia.esperas_en_la_puerta = self._estadisticas.esperas_en_la_puerta
        copia.precargas_omitidas_por_presupuesto = (
            self._estadisticas.precargas_omitidas_por_presupuesto)
        return copia

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _sala_y_vecinas_tienen_contenido(self, sala):
        if not self.tiene_contenido(sala):
            return False
        for vecina in self._grafo.vecinos(sala):
            if self._grafo.contiene_sala(vecina) and not self.tiene_contenido(vecina):
                return False
        return True

    def _elegir_salas_para_lote(self, origen):
        """Las 10 salas sin contenido más cercanas a origen (BFS)."""
        return self._grafo.salas_en_orden_de_distancia(
            origen, MAXIMO_POR_LOTE, lambda sala: not self.tiene_contenido(sala)
        )

    def _descargar_lote_desde(self, origen):
        lote = self._elegir_salas_para_lote(origen)
        if not lote:
            return
        respuesta = self._fuente.contenido(self._id_cripta, lote)
        entradas = respuesta.get("contenido") if isinstance(respuesta, dict) else None
        if not isinstance(entradas, list):
            raise ErrorFuenteDatos("descargar contenido de salas", "la respuesta no trae 'contenido'")
        self._estadisticas.lotes_de_contenido += 1

        entradas_nuevas = []
        for entrada in entradas:
            id_sala = entrada.get("sala") if isinstance(entrada, dict) else None
            if isinstance(id_sala, bool) or not isinstance(id_sala, int):
                raise ErrorFuenteDatos("descargar contenido de salas",
                                       "el API devolvió contenido sin número de sala")
            if self.tiene_contenido(id_sala):
                continue
            self._contenido_por_sala.insertar(id_sala, entrada)
            self._estadisticas.salas_descargadas += 1
            entradas_nuevas.append(entrada)
            if self._gestor_catalogo is not None:
                self._gestor_catalogo.anotar_ids_conocidos(tipos_de_la_sala(entrada))
        if entradas_nuevas and self._guardar_contenido is not None:
            self._guardar_contenido(entradas_nuevas)


def tipos_de_la_sala(entrada):
    """Ids de catálogo que aparecen en una entrada de contenido, en orden:
    enemigos, objetos y trampas. Las listas pueden faltar en el JSON."""
    tipos = []
    for enemigo in entrada.get("enemigos") or []:
        tipos.append(enemigo["tipo"])
    for id_objeto in entrada.get("objetos") or []:
        tipos.append(id_objeto)
    for trampa in entrada.get("trampas") or []:
        tipos.append(trampa["tipo"])
    return tipos


def descargar_salas_del_esqueleto(fuente, id_cripta, paginas_declaradas):
    """Descarga todas las páginas del esqueleto y devuelve sus salas juntas.
    Si una página informa otro total de páginas, se sigue ese total."""
    salas = []
    pagina = 1
    total_paginas = paginas_declaradas
    while pagina <= total_paginas:
        respuesta = fuente.pagina_salas(id_cripta, pagina)
        total_paginas = respuesta["total_paginas"]
        for sala in respuesta["salas"]:
            salas.append(sala)
        pagina += 1
    return salas
