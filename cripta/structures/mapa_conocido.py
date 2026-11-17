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
    TablaHash solo admite claves int o str, así que no sirve una tupla. La
    clave de una salida es id de la sala * 4 + posición de su dirección. Es
    única (una salida por dirección y sala) y sobrevive a guardar y cargar
    porque no depende del objeto en memoria. Un texto con los ids de las dos
    salas no serviría: dos salidas distintas pueden unir las mismas dos
    salas.

    El recuerdo de una puerta se guarda bajo la clave de cada uno de sus
    lados, con el mismo valor. Así el proveedor de vecinas, que recorre las
    salidas de una sala, consulta con la clave de la salida que tiene en la
    mano, sin buscar por qué dirección sale la puerta de la otra sala: esa
    búsqueda era la mitad del costo de un paso de «ir a» (plan, mejora a).
    Observar escribe los dos lados, pero observar es raro y consultar es
    frecuente. La exportación entrega un par por puerta, con la clave del
    lado room_a.

Reversión
    Cada cambio anota en el historial reversible su operación inversa, con el
    mismo patrón que el rastro del jugador. Si nada cambia no se anota nada.
    El historial solo guarda anotaciones mientras hay una acción del jugador
    en curso y no se está deshaciendo, así que lo explorado al iniciar la
    partida no se puede revertir y deshacer no cuenta como observar.

Complejidad (k = salas exploradas)
    estado_de_sala, puerta_recordada: O(1) promedio, no dependen de k.
    jugador_entro: O(1); con la antorcha, como mucho 5 salas y 20 contadores.
    puerta_cambio: O(1), escribe los dos lados de la puerta.
    deshacer los cambios de una acción: O(cambios de esa acción).
    vecinas_conocidas: O(grado de la sala), a lo sumo 4, sin buscar la
        dirección de ninguna puerta.
    entrantes_conocidas: O(salidas que entran a la sala). El índice de
        salidas entrantes se arma una vez, en O(V + E), y ocupa O(E): no es
        conocimiento, no se exporta ni se revierte.
    exportar, importar: O(k + puertas recordadas).
"""
from model.room import DIRECTIONS, direction_index
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
        self._version = 0
        self._entrantes = None

    # ------------------------------------------------------------------
    # Consultas

    def usar_historial(self, history):
        """Anota los cambios siguientes en history.

        Al cargar una partida, el historial lo arma quien la carga y existe
        recién cuando la partida ya está armada; por eso no se puede pasar al
        construir el mapa. Lo ya importado no se anota: no es reversible.
        """
        self._history = history

    @property
    def version(self):
        """Sube con cada cambio del conocimiento: una exploración, un cambio
        de puerta recordada, una reversión o una importación. Quien guarde un
        cálculo hecho sobre el mapa conocido lo reutiliza solo si la versión
        no cambió (mejora c del plan, FR-026)."""
        return self._version
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

            clave = id_sala * len(DIRECTIONS) + direction_index(salida.direction)

            if self._puertas.obtener(clave) is True:
                vecinas.append((salida.destination, salida.cost, salida))

        return vecinas

    def entrantes_conocidas(self, id_sala):
        """Salidas que el jugador sabe que llevan a id_sala: (id_origen, costo, salida).

        Es el proveedor que expande la búsqueda de «ir a» cuando hay salidas
        de un solo sentido: la búsqueda va desde el destino y necesita las
        salidas que ENTRAN a cada sala (plan, alternativa 9). Cuenta una
        salida si las dos salas están exploradas y su puerta se recuerda
        abierta, con la clave del lado de la sala de origen; es el mismo
        criterio que vecinas_conocidas, mirado desde la otra punta.

        El índice de salidas entrantes depende solo de la topología, que no
        cambia, así que se arma una vez y no se toca al explorar ni al
        revertir: lo que cambia se filtra al consultar.
        """
        if not self._exploradas.contiene(id_sala):
            return []

        if self._entrantes is None:
            self._armar_entrantes()

        entrantes = []

        for origen, posicion, salida in self._entrantes.obtener(id_sala, []):
            if not self._exploradas.contiene(origen):
                continue

            if self._puertas.obtener(origen * len(DIRECTIONS) + posicion) is True:
                entrantes.append((origen, salida.cost, salida))

        return entrantes

    def _armar_entrantes(self):
        """Índice id de sala -> [(id_origen, posición de la dirección, salida)].

        O(V + E) una sola vez, recorriendo las salidas de cada sala del mapa.
        """
        self._entrantes = TablaHash()

        for id_origen in self._room_map.room_ids():
            for salida in self._room_map.room(id_origen).exits():
                destino = salida.destination
                lista = self._entrantes.obtener(destino)

                if lista is None:
                    lista = []
                    self._entrantes.insertar(destino, lista)

                lista.append((id_origen, direction_index(salida.direction), salida))

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
            if self._salida_de_la_clave(clave).door.room_a == clave // len(DIRECTIONS):
                pares.append((clave, self._puertas.obtener(clave)))

        return list(self._orden), sort(pares, key=_primer_valor)

    def importar(self, exploradas, puertas):
        """Deja el conocimiento como estaba al exportar. No anota nada."""
        self._version += 1
        self._exploradas = TablaHash()
        self._contadores = TablaHash()
        self._puertas = TablaHash()
        self._orden = []

        for id_sala in exploradas:
            if self._exploradas.contiene(id_sala):
                raise ValueError(f"La sala {id_sala} aparece dos veces.")

            self._marcar_explorada(id_sala)

        for clave, abierta in puertas:
            for lado in self._claves_de_los_lados(self._salida_de_la_clave(clave).door):
                self._puertas.insertar(lado, bool(abierta))

    # ------------------------------------------------------------------
    # Cambios con su inversa
    # ------------------------------------------------------------------

    def _explorar(self, id_sala):
        if self._exploradas.contiene(id_sala):
            return

        self._marcar_explorada(id_sala)
        self._anotar(CallbackChange(self._deshacer_exploracion, id_sala))

    def _marcar_explorada(self, id_sala):
        self._version += 1
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

        self._version += 1
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
        claves = self._claves_de_los_lados(puerta)
        anterior = self._puertas.obtener(claves[0])
        actual = puerta.is_open

        if anterior is not None and anterior == actual:
            return

        self._version += 1

        for clave in claves:
            self._puertas.insertar(clave, actual)

        self._anotar(CallbackChange(self._restaurar_puerta, claves, anterior))

    def _restaurar_puerta(self, claves, anterior):
        self._version += 1

        for clave in claves:
            if anterior is None:
                self._puertas.eliminar(clave)
            else:
                self._puertas.insertar(clave, anterior)

    def _claves_de_los_lados(self, puerta):
        """La clave del lado room_a y, si la puerta tiene salida de vuelta, la
        del lado room_b. Un paso de un solo sentido tiene una sola."""
        claves = [self.clave_de_puerta(puerta)]
        sala_b = self._room_map.room(puerta.room_b)

        for indice in range(len(DIRECTIONS)):
            salida = sala_b.exit_towards(DIRECTIONS[indice])

            if salida is not None and salida.door is puerta:
                claves.append(puerta.room_b * len(DIRECTIONS) + indice)
                break

        return claves

    def _salida_de_la_clave(self, clave):
        id_sala = clave // len(DIRECTIONS)
        salida = self._room_map.room(id_sala).exit_towards(DIRECTIONS[clave % len(DIRECTIONS)])

        if salida is None:
            raise ValueError(f"La clave de puerta {clave} no corresponde a ninguna salida.")

        return salida

    def _anotar(self, cambio):
        if self._history is not None:
            self._history.record(cambio)


def _primer_valor(par):
    return par[0]
