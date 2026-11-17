"""
Mapa conocido: lo que el jugador sabe del mapa (niebla de guerra, §3.3).

Problema que resuelve
    El jugador ya no ve la cripta completa. Cada sala está, para él,
    explorada, avistada o desconocida, y de cada puerta recuerda el estado
    de la última vez que la observó, aunque haya cambiado después. Es estado
    del juego: se revierte con el pergamino, se guarda con la partida y lo
    usa el viaje automático «ir a» (§3.4).

Qué se guarda y qué se deduce
    Se guarda solo lo que no se puede reconstruir del esqueleto:
      - las salas exploradas;
      - el estado recordado de cada puerta observada.
    Se mantiene al día, para responder rápido:
      - por cada sala, cuántas salidas de salas exploradas llevan a ella.
        Una sala no explorada con ese contador mayor que cero está avistada.
    Se lee del mapa de salas cuando hace falta:
      - el nombre, las salidas y el costo de las salidas de una sala
        explorada, que no cambian durante la partida. El estado real de una
        puerta nunca se lee para mostrarlo: siempre el recordado.

Estructuras, todas propias o permitidas
    exploradas            TablaHash  id de sala -> True
    contadores            TablaHash  id de sala -> salidas que la avistan
    puertas recordadas    TablaHash  clave de puerta -> True (abierta) o
                                     False (cerrada); sin entrada, desconocida
    orden de exploración  list usada como pila
    No se usa dict como índice ni set (P1 §7, §6.2).

Clave de una puerta
    TablaHash solo admite claves int o str, así que no sirve una tupla. Se
    usa id de room_a * 4 + posición de la dirección por la que la puerta sale
    de room_a. Es única (una salida por dirección y sala), es la misma desde
    los dos lados y sobrevive a guardar y cargar porque no depende del objeto
    en memoria. Un texto con los ids de las dos salas no serviría: dos
    salidas distintas pueden unir las mismas dos salas.

Reversión
    Cada cambio anota en el historial reversible su operación inversa, con el
    mismo patrón que el rastro del jugador. Si nada cambia no se anota nada.
    El historial solo guarda anotaciones mientras hay una acción del jugador
    en curso y no se está deshaciendo, así que lo explorado al iniciar la
    partida no se puede revertir y deshacer no cuenta como observar.

Complejidad (k = salas exploradas)
    estado_de_sala, puerta_recordada: O(1) promedio, no dependen de k.
    jugador_entro: O(1); con la antorcha, como mucho 5 salas y 20 contadores.
    puerta_cambio: O(1).
    deshacer los cambios de una acción: O(cambios de esa acción).
    vecinas_conocidas: O(grado de la sala), a lo sumo 4.
    exportar, importar: O(k + puertas recordadas).
"""
from model.room import DIRECTIONS
from structures.history import CallbackChange
from structures.sorting import sort
from structures.tabla_hash import TablaHash

EXPLORADA = "explorada"
AVISTADA = "avistada"
DESCONOCIDA = "desconocida"

ABIERTA = "abierta"
CERRADA = "cerrada"


class MapaConocido:
    """Conocimiento del jugador sobre el mapa.

    room_map es el mapa de salas de la partida; de él se leen las salidas de
    las salas exploradas. history es el historial reversible, o None para no
    anotar nada, igual que el rastro.
    """

    def __init__(self, room_map, history=None):
        self._room_map = room_map
        self._history = history
        self._exploradas = TablaHash()
        self._contadores = TablaHash()
        self._puertas = TablaHash()
        self._orden = []

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def estado_de_sala(self, id_sala):
        """EXPLORADA, AVISTADA o DESCONOCIDA (§3.3)."""
        if self._exploradas.contiene(id_sala):
            return EXPLORADA

        if self._contadores.obtener(id_sala, 0) > 0:
            return AVISTADA

        return DESCONOCIDA

    def esta_explorada(self, id_sala):
        return self._exploradas.contiene(id_sala)

    def puerta_recordada(self, puerta):
        """ABIERTA, CERRADA o DESCONOCIDA si el jugador nunca la observó."""
        recordada = self._puertas.obtener(self.clave_de_puerta(puerta))

        if recordada is None:
            return DESCONOCIDA

        return ABIERTA if recordada else CERRADA

    def salas_exploradas(self):
        """Ids de las salas exploradas, en el orden en que se exploraron."""
        return list(self._orden)

    def cantidad_de_exploradas(self):
        return len(self._orden)

    def clave_de_puerta(self, puerta):
        """id de room_a * 4 + posición de la dirección de la salida en room_a."""
        sala = self._room_map.room(puerta.room_a)

        for indice in range(len(DIRECTIONS)):
            salida = sala.exit_towards(DIRECTIONS[indice])

            if salida is not None and salida.door is puerta:
                return puerta.room_a * len(DIRECTIONS) + indice

        raise ValueError(
            f"La puerta entre {puerta.room_a} y {puerta.room_b} no sale de la "
            f"sala {puerta.room_a}."
        )

    def vecinas_conocidas(self, id_sala):
        """Vecinas por las que el jugador sabe que puede pasar: (id, costo, salida).

        Solo salidas hacia salas exploradas cuya puerta se recuerda abierta.
        Es el proveedor de vecinas que recibe la búsqueda de costo mínimo,
        con la misma forma que las vecinas abiertas que usa el cazador.
        """
        if not self._exploradas.contiene(id_sala):
            return []

        vecinas = []

        for salida in self._room_map.room(id_sala).exits():
            if not self._exploradas.contiene(salida.destination):
                continue

            if self._puertas.obtener(self.clave_de_puerta(salida.door)) is True:
                vecinas.append((salida.destination, salida.cost, salida))

        return vecinas

    # ------------------------------------------------------------------
    # Avisos del motor
    # ------------------------------------------------------------------

    def jugador_entro(self, id_sala, antorcha_encendida=False):
        """El jugador entró a id_sala (o empezó la partida en ella).

        Explora la sala y observa todas sus puertas. Con la antorcha
        encendida explora además cada vecina, por cualquier salida, abierta o
        cerrada, sin observar las puertas de esas vecinas: el jugador no está
        en ellas. Enemigos, objetos y trampas no son asunto de esta
        estructura, así que nada de eso se toca.
        """
        sala = self._room_map.room(id_sala)
        self._explorar(id_sala)

        for salida in sala.exits():
            self._observar(salida.door)

        if antorcha_encendida:
            for salida in sala.exits():
                self._explorar(salida.destination)

    def puerta_cambio(self, puerta, sala_del_jugador):
        """Una puerta cambió de estado. Se observa si el jugador está en una
        de las dos salas que conecta (aclaración del 2026-11-16)."""
        if puerta.connects(sala_del_jugador):
            self._observar(puerta)

    # ------------------------------------------------------------------
    # Exportar e importar
    # ------------------------------------------------------------------

    def exportar(self):
        """(exploradas, puertas) como listas planas.

        exploradas: ids en orden de exploración.
        puertas: pares (clave, abierta) en orden creciente de clave.
        Los contadores no se exportan: se rehacen al importar.
        """
        pares = []

        for clave in self._puertas.claves():
            pares.append((clave, self._puertas.obtener(clave)))

        return list(self._orden), sort(pares, key=_primer_valor)

    def importar(self, exploradas, puertas):
        """Deja el conocimiento como estaba al exportar. No anota nada."""
        self._exploradas = TablaHash()
        self._contadores = TablaHash()
        self._puertas = TablaHash()
        self._orden = []

        for id_sala in exploradas:
            if self._exploradas.contiene(id_sala):
                raise ValueError(f"La sala {id_sala} aparece dos veces.")

            self._marcar_explorada(id_sala)

        for clave, abierta in puertas:
            self._puertas.insertar(clave, bool(abierta))

    # ------------------------------------------------------------------
    # Cambios con su inversa
    # ------------------------------------------------------------------

    def _explorar(self, id_sala):
        if self._exploradas.contiene(id_sala):
            return

        self._marcar_explorada(id_sala)
        self._anotar(CallbackChange(self._deshacer_exploracion, id_sala))

    def _marcar_explorada(self, id_sala):
        self._exploradas.insertar(id_sala, True)
        self._orden.append(id_sala)

        for salida in self._room_map.room(id_sala).exits():
            destino = salida.destination
            self._contadores.insertar(destino, self._contadores.obtener(destino, 0) + 1)

    def _deshacer_exploracion(self, id_sala):
        """Inversa de _explorar. Las anotaciones se deshacen en orden inverso,
        así que la sala es siempre la última de la pila."""
        if not self._orden or self._orden[-1] != id_sala:
            raise RuntimeError(
                f"Se esperaba deshacer la exploración de {id_sala} y la última "
                "explorada es otra."
            )

        self._orden.pop()
        self._exploradas.eliminar(id_sala)

        for salida in self._room_map.room(id_sala).exits():
            destino = salida.destination
            restante = self._contadores.obtener(destino, 0) - 1

            if restante > 0:
                self._contadores.insertar(destino, restante)
            else:
                self._contadores.eliminar(destino)

    def _observar(self, puerta):
        clave = self.clave_de_puerta(puerta)
        anterior = self._puertas.obtener(clave)
        actual = puerta.is_open

        if anterior is not None and anterior == actual:
            return

        self._puertas.insertar(clave, actual)
        self._anotar(CallbackChange(self._restaurar_puerta, clave, anterior))

    def _restaurar_puerta(self, clave, anterior):
        if anterior is None:
            self._puertas.eliminar(clave)
        else:
            self._puertas.insertar(clave, anterior)

    def _anotar(self, cambio):
        if self._history is not None:
            self._history.record(cambio)


def _primer_valor(par):
    return par[0]
