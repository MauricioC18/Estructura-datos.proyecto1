"""
Caché del catálogo en memoria con política LRU (problema 4.4).

Problema que resuelve
    Mantener en memoria como máximo --cache-size fichas (25 por defecto) y,
    al llegar al tope, liberar alguna. Averiguar si una ficha está en memoria
    es una de las operaciones más frecuentes del programa (§4.4).

Política: LRU ("least recently used", la usada hace más tiempo)
    Cuando hay que liberar, se libera la ficha que lleva más tiempo sin
    usarse: es la que menos probablemente se necesite pronto, porque el
    jugador vuelve a salas cercanas y vuelve a ver los mismos tipos de
    enemigos y objetos.
    Alternativas consideradas:
      - FIFO: libera la ficha que entró primero, aunque se use todo el tiempo.
      - LFU: libera la menos usada en total; necesita contadores y tarda en
        "olvidar" fichas que se usaron mucho al principio de la partida.

Estructuras
    - TablaHash (id de ficha -> nodo): dice en O(1) promedio si una ficha
      está en memoria y encuentra su nodo.
    - Lista doblemente enlazada de nodos ordenada por último uso: la más
      reciente al frente y la usada hace más tiempo al final. Como cada nodo
      conoce a su anterior y a su siguiente, sacarlo de su lugar y ponerlo al
      frente cuesta O(1), sin recorrer la lista.
    - Dos nodos centinela (vacíos) marcan el frente y el final. Gracias a
      ellos nunca hay casos especiales de lista vacía, primer nodo o último
      nodo al insertar o quitar.

Fichas en uso (§4.4)
    Una ficha referenciada por una instancia activa no se puede liberar. La
    caché no lleva esa cuenta: cuando necesita liberar, llama a la función
    consultar_ids_en_uso que le entrega el controlador y salta las fichas que
    esa función reporta. Se consulta solo al liberar, que es poco frecuente
    (decisión D5). La función debe devolver una TablaHash cuyas claves son
    los ids en uso.
    Si todas las fichas que se podrían liberar están en uso, la caché excede
    el tope temporalmente y lo registra en exceso_maximo_sobre_capacidad()
    (decisión D9). En la siguiente inserción vuelve a intentar bajar al tope.

Disco
    La caché no escribe en disco. Quien descarga una ficha la guarda en disco
    en ese momento, así que liberar una ficha de memoria nunca pierde datos:
    volver a necesitarla cuesta una lectura de disco, no una solicitud (§4.4).

Retroceso
    La caché es infraestructura, no estado del juego: el pergamino de
    retroceso no la modifica (§2.11).

Complejidad (n = fichas en memoria)
    obtener_ficha, contiene_ficha: O(1) promedio.
    agregar_ficha sin liberar: O(1) promedio.
    agregar_ficha con liberación: O(u + 1) más el costo de consultar_ids_en_uso,
        donde u es la cantidad de fichas en uso que hay que saltar desde el final.
    espacio: O(n).
"""
from structures.tabla_hash import TablaHash

CAPACIDAD_POR_DEFECTO = 25  # valor por defecto de --cache-size (§4.4)


class _NodoDeFicha:
    """Un elemento de la lista doblemente enlazada."""

    __slots__ = ("id_ficha", "ficha", "anterior", "siguiente")

    def __init__(self, id_ficha, ficha):
        self.id_ficha = id_ficha
        self.ficha = ficha
        self.anterior = None
        self.siguiente = None


class CacheCatalogo:
    """Fichas del catálogo en memoria, con tope y política LRU."""

    def __init__(self, capacidad_maxima=CAPACIDAD_POR_DEFECTO, consultar_ids_en_uso=None):
        if (isinstance(capacidad_maxima, bool) or not isinstance(capacidad_maxima, int)
                or capacidad_maxima < 1):
            raise ValueError("La capacidad de la caché debe ser un entero mayor o igual a 1")
        self._capacidad_maxima = capacidad_maxima
        # Sin función, se considera que ninguna ficha está en uso.
        self._consultar_ids_en_uso = consultar_ids_en_uso
        self._nodos_por_id = TablaHash()

        self._centinela_frente = _NodoDeFicha(None, None)
        self._centinela_final = _NodoDeFicha(None, None)
        self._centinela_frente.siguiente = self._centinela_final
        self._centinela_final.anterior = self._centinela_frente

        self._aciertos_en_memoria = 0
        self._fallos_en_memoria = 0
        self._cantidad_de_desalojos = 0
        self._exceso_maximo_sobre_capacidad = 0

    # ------------------------------------------------------------------
    # Operaciones principales
    # ------------------------------------------------------------------

    def obtener_ficha(self, id_ficha):
        """Devuelve la ficha y la marca como la más reciente, o None si no
        está en memoria. Cuenta un acierto o un fallo."""
        nodo = self._nodos_por_id.obtener(id_ficha)
        if nodo is None:
            self._fallos_en_memoria += 1
            return None
        self._aciertos_en_memoria += 1
        self._quitar_de_la_lista(nodo)
        self._insertar_al_frente(nodo)
        return nodo.ficha

    def contiene_ficha(self, id_ficha):
        """Indica si la ficha está en memoria, sin cambiar el orden de uso
        ni las estadísticas."""
        return self._nodos_por_id.contiene(id_ficha)

    def agregar_ficha(self, id_ficha, ficha):
        """Guarda la ficha como la más reciente. Si se supera el tope, libera
        las fichas usadas hace más tiempo que no estén en uso."""
        nodo_existente = self._nodos_por_id.obtener(id_ficha)
        if nodo_existente is not None:
            nodo_existente.ficha = ficha
            self._quitar_de_la_lista(nodo_existente)
            self._insertar_al_frente(nodo_existente)
            return
        nodo_nuevo = _NodoDeFicha(id_ficha, ficha)
        self._insertar_al_frente(nodo_nuevo)
        self._nodos_por_id.insertar(id_ficha, nodo_nuevo)
        if self._nodos_por_id.tamano() > self._capacidad_maxima:
            self._liberar_hasta_el_tope(nodo_nuevo)

    def vaciar(self):
        """Olvida todas las fichas (por ejemplo, si cambió la versión del
        catálogo). Las estadísticas se conservan."""
        self._nodos_por_id = TablaHash()
        self._centinela_frente.siguiente = self._centinela_final
        self._centinela_final.anterior = self._centinela_frente

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def cantidad_de_fichas(self):
        return self._nodos_por_id.tamano()

    def capacidad_maxima(self):
        return self._capacidad_maxima

    def ids_en_orden_de_uso(self):
        """Ids desde el más reciente hasta el usado hace más tiempo."""
        resultado = []
        nodo = self._centinela_frente.siguiente
        while nodo is not self._centinela_final:
            resultado.append(nodo.id_ficha)
            nodo = nodo.siguiente
        return resultado

    def aciertos_en_memoria(self):
        return self._aciertos_en_memoria

    def fallos_en_memoria(self):
        return self._fallos_en_memoria

    def cantidad_de_desalojos(self):
        return self._cantidad_de_desalojos

    def exceso_maximo_sobre_capacidad(self):
        """Cuántas fichas por encima del tope llegó a tener la caché porque
        todas las candidatas estaban en uso (0 si nunca pasó)."""
        return self._exceso_maximo_sobre_capacidad

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _insertar_al_frente(self, nodo):
        primero = self._centinela_frente.siguiente
        nodo.anterior = self._centinela_frente
        nodo.siguiente = primero
        self._centinela_frente.siguiente = nodo
        primero.anterior = nodo

    def _quitar_de_la_lista(self, nodo):
        nodo.anterior.siguiente = nodo.siguiente
        nodo.siguiente.anterior = nodo.anterior
        nodo.anterior = None
        nodo.siguiente = None

    def _liberar_hasta_el_tope(self, nodo_recien_agregado):
        """Recorre desde el final (lo usado hace más tiempo) y libera fichas
        que no estén en uso hasta volver al tope o quedarse sin candidatas.
        La ficha recién agregada nunca se libera: alguien acaba de pedirla."""
        ids_en_uso = None
        if self._consultar_ids_en_uso is not None:
            ids_en_uso = self._consultar_ids_en_uso()

        candidato = self._centinela_final.anterior
        while (self._nodos_por_id.tamano() > self._capacidad_maxima
               and candidato is not self._centinela_frente):
            siguiente_candidato = candidato.anterior
            esta_en_uso = ids_en_uso is not None and ids_en_uso.contiene(candidato.id_ficha)
            if candidato is not nodo_recien_agregado and not esta_en_uso:
                self._quitar_de_la_lista(candidato)
                self._nodos_por_id.eliminar(candidato.id_ficha)
                self._cantidad_de_desalojos += 1
            candidato = siguiente_candidato

        exceso = self._nodos_por_id.tamano() - self._capacidad_maxima
        if exceso > self._exceso_maximo_sobre_capacidad:
            self._exceso_maximo_sobre_capacidad = exceso
