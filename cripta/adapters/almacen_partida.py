"""
Guardado binario de la partida (problema 4.10).

Problema que resuelve
    §4.10 pide guardar el estado de la partida en un archivo binario de
    formato propio, que al cargar permita recuperar una sala sin leer el
    archivo completo, que detecte la incompatibilidad con otra version del
    formato, y que se pueda comparar en tamano en disco y tiempo de carga
    contra guardar el mismo estado en JSON.

Como funciona
    Un solo archivo con cuatro partes, en este orden:

    encabezado     Firma "CRIPTAPA", version del formato, la posicion donde
                   empieza el indice y cuantas salas tiene. Mide siempre lo
                   mismo, asi que se lee sin buscar nada.
    bloque global  Lo que no pertenece a ninguna sala: las versiones de la
                   cripta y del catalogo, el reloj, el contador de secuencia,
                   el estado del generador aleatorio, el jugador con su
                   inventario, la agenda, el rastro, la antorcha, el
                   resultado y los dos contadores.
    bloques de     Uno por sala, con sus salidas y puertas, sus trampas, lo
    sala           que hay en el suelo y los enemigos que estan en ella.
    indice         Una entrada por sala, ORDENADAS POR ID DE SALA: el id, la
                   posicion donde empieza su bloque y cuantos bytes mide.

    Para leer una sala sola (leer_sala):
      1. se lee el encabezado, que mide siempre lo mismo, y se salta a la
         posicion del indice;
      2. busqueda binaria del id de sala en el indice, O(log n);
      3. se salta a la posicion de ese bloque y se leen solo sus bytes.
    Nunca se leen el bloque global ni los bloques de las otras salas.

    El indice va al final porque la posicion de cada bloque solo se conoce
    despues de armarlo. El encabezado guarda donde quedo, de modo que llegar
    al indice cuesta un salto y no recorrer el archivo.

Seguridad ante fallos
    El archivo se escribe primero en un temporal y despues se reemplaza de
    una sola vez (os.replace), igual que el indice de AlmacenFichas. Si el
    programa se cierra a medio guardar, el guardado anterior queda intacto y
    nunca queda un archivo a medias que parezca valido.

Versiones
    Si la firma o la version del formato no coinciden, cargar levanta
    PartidaIncompatible en vez de interpretar bytes que significan otra cosa.
    Si se le pasan las versiones vigentes de la cripta y del catalogo, se
    comparan tambien contra las que traia el archivo.

Por que el archivo guarda todo y no solo los identificadores
    Los objetos, las trampas y los enemigos los construye el traductor desde
    el catalogo, asi que el archivo podria guardar solo instance_id, type_id y
    lo que cambia, y pedirle el resto al catalogo al cargar. Seria bastante
    mas chico. No se hizo porque ataria la partida guardada a que el catalogo
    siga en la misma version: si cambia, el archivo quedaria inservible en vez
    de quedar simplemente viejo. Guardando todo, el archivo se abre solo.
    benchmark/bench_almacen_partida.py mide en bytes cuanto cuesta esa
    decision.

Por que un indice ordenado con busqueda binaria y no una tabla
    §7 prohibe usar dict como indice, y el indice se guarda en disco tal como
    se usa en memoria: listas paralelas ordenadas por id de sala, que se
    cargan sin reconstruir nada. Es el mismo criterio de AlmacenFichas.

Complejidad (n = salas, m = bytes del bloque de una sala)
    guardar: O(tamano del estado), una sola pasada
    cargar: O(tamano del archivo)
    leer_sala: O(log n) de busqueda mas O(m) de lectura, sin tocar el resto
    memoria al leer una sala: O(n) del indice mas O(m)

Limite conocido
    Guardar reescribe el archivo completo. No se guarda una sala suelta
    porque el reloj, la agenda y el inventario cambian en casi toda accion y
    habria que reescribir el bloque global de todos modos.
    No se guardan el historial del retroceso, que §2.11 deja fuera, la
    bitacora de mensajes ni events_processed, que son de la sesion y no del
    estado de la partida.
"""
import os
import struct
from pathlib import Path

from model.enemy import Enemy
from model.event import Event
from model.item import Item
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from model.trap import Trap
from structures.inventory import Inventory
from structures.sorting import sort
from structures.tabla_hash import TablaHash

FIRMA_DEL_ARCHIVO = b"CRIPTAPA"
VERSION_DEL_FORMATO = 1

# "<" = little-endian, sin relleno. B = 1 byte, H = 2, I = 4, i = 4 con signo,
# q = 8 con signo, Q = 8 sin signo, d = flotante de 8.
_FORMATO_ENCABEZADO = "<8sHQI"
_FORMATO_LARGO_DE_TEXTO = "<H"
_FORMATO_LARGO_DE_BLOQUE = "<I"
_FORMATO_ENTRADA_DEL_INDICE = "<iQI"
_FORMATO_CANTIDAD = "<I"
_FORMATO_ENTERO = "<q"
_FORMATO_ENTERO_OPCIONAL = "<Bq"
_FORMATO_BANDERA = "<B"
_FORMATO_FLOTANTE = "<d"

# Los formatos se compilan una sola vez: leer un bloque toca estos struct
# miles de veces y volver a interpretar la cadena de formato en cada campo era
# la mitad del tiempo de carga.
_ENCABEZADO = struct.Struct(_FORMATO_ENCABEZADO)
_LARGO_DE_TEXTO = struct.Struct(_FORMATO_LARGO_DE_TEXTO)
_LARGO_DE_BLOQUE = struct.Struct(_FORMATO_LARGO_DE_BLOQUE)
_ENTRADA_DEL_INDICE = struct.Struct(_FORMATO_ENTRADA_DEL_INDICE)
_CANTIDAD = struct.Struct(_FORMATO_CANTIDAD)
_ENTERO = struct.Struct(_FORMATO_ENTERO)
_ENTERO_OPCIONAL = struct.Struct(_FORMATO_ENTERO_OPCIONAL)
_BANDERA = struct.Struct(_FORMATO_BANDERA)
_FLOTANTE = struct.Struct(_FORMATO_FLOTANTE)

_TAMANO_DEL_ENCABEZADO = _ENCABEZADO.size

_SIN_VALOR = 0
_ES_TEXTO = 1
_ES_ENTERO = 2


class PartidaIncompatible(Exception):
    """El archivo no es de este formato o es de otra version (§4.10)."""

    def __init__(self, detalle):
        self.detalle = detalle
        super().__init__(f"La partida guardada no se puede cargar: {detalle}")


class ArchivoDePartidaDanado(Exception):
    """El archivo se corto o sus bytes no se pueden interpretar."""

    def __init__(self, detalle):
        self.detalle = detalle
        super().__init__(f"El archivo de partida esta danado: {detalle}")


class SalaGuardada:
    """Una sala leida del archivo, con lo que habia en ella."""

    def __init__(self, room, enemies):
        self.room = room
        self.enemies = enemies


class PartidaGuardada:
    """El estado completo leido del archivo, listo para Game.load()."""

    def __init__(self):
        self.id_cripta = ""
        self.version_cripta = ""
        self.version_catalogo = ""
        self.seed = 0
        self.clock = 0
        self.sequence_counter = 0
        self.random_state = None
        self.player = None
        self.enemies = []
        self.room_map = None
        self.exit_room_id = None
        self.trail_marks = []
        self.events = []
        self.torch_lit = False
        self.result = ""
        self.player_actions = 0
        self.enemies_defeated = 0


# ----------------------------------------------------------------------
# Escritura de valores sueltos
# ----------------------------------------------------------------------


def _empacar_texto(valor):
    crudo = ("" if valor is None else str(valor)).encode("utf-8")
    return _LARGO_DE_TEXTO.pack(len(crudo)) + crudo


def _empacar_entero(valor):
    return _ENTERO.pack(int(valor))


def _empacar_entero_opcional(valor):
    if valor is None:
        return _ENTERO_OPCIONAL.pack(_SIN_VALOR, 0)

    return _ENTERO_OPCIONAL.pack(_ES_ENTERO, int(valor))


def _empacar_bandera(valor):
    return _BANDERA.pack(1 if valor else 0)


def _empacar_texto_o_entero(valor):
    if valor is None:
        return _BANDERA.pack(_SIN_VALOR)

    if isinstance(valor, int) and not isinstance(valor, bool):
        return _BANDERA.pack(_ES_ENTERO) + _empacar_entero(valor)

    return _BANDERA.pack(_ES_TEXTO) + _empacar_texto(valor)


def _empacar_cantidad(valor):
    return _CANTIDAD.pack(int(valor))


class _Lector:
    """Recorre los bytes de un bloque de principio a fin."""

    def __init__(self, contenido, de_donde):
        self._contenido = contenido
        self._de_donde = de_donde
        self._posicion = 0

    def _tomar(self, compilado):
        siguiente = self._posicion + compilado.size

        if siguiente > len(self._contenido):
            raise ArchivoDePartidaDanado(
                f"el {self._de_donde} se corto antes de lo esperado"
            )

        valores = compilado.unpack_from(self._contenido, self._posicion)
        self._posicion = siguiente
        return valores

    def texto(self):
        largo = self._tomar(_LARGO_DE_TEXTO)[0]
        siguiente = self._posicion + largo

        if siguiente > len(self._contenido):
            raise ArchivoDePartidaDanado(
                f"el {self._de_donde} se corto en medio de un texto"
            )

        crudo = self._contenido[self._posicion:siguiente]
        self._posicion = siguiente

        try:
            return crudo.decode("utf-8")
        except UnicodeDecodeError:
            raise ArchivoDePartidaDanado(
                f"el {self._de_donde} tiene un texto que no es UTF-8"
            )

    def entero(self):
        return self._tomar(_ENTERO)[0]

    def entero_opcional(self):
        etiqueta, valor = self._tomar(_ENTERO_OPCIONAL)
        return None if etiqueta == _SIN_VALOR else valor

    def bandera(self):
        return self._tomar(_BANDERA)[0] == 1

    def texto_o_entero(self):
        etiqueta = self._tomar(_BANDERA)[0]

        if etiqueta == _SIN_VALOR:
            return None

        if etiqueta == _ES_ENTERO:
            return self.entero()

        return self.texto()

    def cantidad(self):
        return self._tomar(_CANTIDAD)[0]

    def flotante(self):
        return self._tomar(_FLOTANTE)[0]


# ----------------------------------------------------------------------
# Objetos, trampas y actores
# ----------------------------------------------------------------------


def _empacar_objeto(item):
    return b"".join([
        _empacar_texto(item.instance_id),
        _empacar_texto(item.type_id),
        _empacar_texto(item.name),
        _empacar_texto(item.item_class),
        _empacar_entero(item.weight),
        _empacar_entero(item.value),
        _empacar_entero(item.attack_bonus),
        _empacar_entero(item.defense_bonus),
        _empacar_entero(item.heal),
        _empacar_entero(item.speed_modifier),
        _empacar_entero(item.duration),
        _empacar_texto_o_entero(item.opens),
    ])


def _leer_objeto(lector):
    return Item(
        instance_id=lector.texto(),
        type_id=lector.texto(),
        name=lector.texto(),
        item_class=lector.texto(),
        weight=lector.entero(),
        value=lector.entero(),
        attack_bonus=lector.entero(),
        defense_bonus=lector.entero(),
        heal=lector.entero(),
        speed_modifier=lector.entero(),
        duration=lector.entero(),
        opens=lector.texto_o_entero(),
    )


def _empacar_lista_de_objetos(items):
    partes = [_empacar_cantidad(len(items))]

    for item in items:
        partes.append(_empacar_objeto(item))

    return b"".join(partes)


def _leer_lista_de_objetos(lector):
    cuantos = lector.cantidad()
    return [_leer_objeto(lector) for _ in range(cuantos)]


def _empacar_trampa(trap):
    return b"".join([
        _empacar_texto(trap.instance_id),
        _empacar_texto(trap.type_id),
        _empacar_texto(trap.name),
        _empacar_entero(trap.damage),
        _empacar_entero(trap.rearm_interval),
        _empacar_entero(trap.room_id),
        _empacar_bandera(trap.armed),
    ])


def _leer_trampa(lector):
    return Trap(
        instance_id=lector.texto(),
        type_id=lector.texto(),
        name=lector.texto(),
        damage=lector.entero(),
        rearm_interval=lector.entero(),
        room_id=lector.entero(),
        armed=lector.bandera(),
    )


def _empacar_enemigo(enemy):
    return b"".join([
        _empacar_texto(enemy.actor_id),
        _empacar_texto(enemy.name),
        _empacar_entero(enemy.max_health),
        _empacar_entero(enemy.health),
        _empacar_entero(enemy.attack),
        _empacar_entero(enemy.defense),
        _empacar_entero(enemy.speed),
        _empacar_entero(enemy.room_id),
        _empacar_bandera(enemy.is_active),
        _empacar_texto(enemy.behavior),
        _empacar_entero(enemy.regeneration),
        _empacar_lista_de_objetos(enemy.drops),
    ])


def _leer_enemigo(lector):
    actor_id = lector.texto()
    name = lector.texto()
    max_health = lector.entero()
    health = lector.entero()
    attack = lector.entero()
    defense = lector.entero()
    speed = lector.entero()
    room_id = lector.entero()
    is_active = lector.bandera()
    behavior = lector.texto()
    regeneration = lector.entero()
    drops = _leer_lista_de_objetos(lector)

    enemy = Enemy(
        actor_id=actor_id,
        name=name,
        max_health=max_health,
        attack=attack,
        defense=defense,
        speed=speed,
        room_id=room_id,
        behavior=behavior,
        health=health,
        drops=drops,
        regeneration=regeneration,
    )
    enemy.is_active = is_active
    return enemy


def _empacar_jugador(player):
    inventory = player.inventory
    items = [] if inventory is None else list(inventory)
    actual = None if inventory is None else inventory.current()
    posicion_del_cursor = -1

    for indice, item in enumerate(items):
        if item is actual:
            posicion_del_cursor = indice
            break

    partes = [
        _empacar_texto(player.actor_id),
        _empacar_texto(player.name),
        _empacar_entero(player.max_health),
        _empacar_entero(player.health),
        _empacar_entero(player.attack),
        _empacar_entero(player.defense),
        _empacar_entero(player.speed),
        _empacar_entero(player.room_id),
        _empacar_texto(
            "" if player.equipped_weapon is None else player.equipped_weapon.instance_id
        ),
        _empacar_texto(
            "" if player.equipped_armor is None else player.equipped_armor.instance_id
        ),
        _empacar_bandera(inventory is not None),
        _empacar_entero(0 if inventory is None else inventory.capacity),
        _empacar_entero(posicion_del_cursor),
        _empacar_lista_de_objetos(items),
    ]

    return b"".join(partes)


def _leer_jugador(lector, history=None):
    actor_id = lector.texto()
    name = lector.texto()
    max_health = lector.entero()
    health = lector.entero()
    attack = lector.entero()
    defense = lector.entero()
    speed = lector.entero()
    room_id = lector.entero()
    id_del_arma = lector.texto()
    id_de_la_armadura = lector.texto()
    tiene_inventario = lector.bandera()
    capacidad = lector.entero()
    posicion_del_cursor = lector.entero()
    items = _leer_lista_de_objetos(lector)

    player = Player(
        actor_id, name, max_health, attack, defense, speed, room_id, health=health
    )

    if tiene_inventario:
        inventory = Inventory(max(1, capacidad), history)

        for item in items:
            inventory.pick_up(item)

        inventory.go_to_start()

        for _ in range(max(0, posicion_del_cursor)):
            inventory.next()

        player.inventory = inventory

    for item in items:
        if id_del_arma and item.instance_id == id_del_arma:
            player.equipped_weapon = item

        if id_de_la_armadura and item.instance_id == id_de_la_armadura:
            player.equipped_armor = item

    return player


# ----------------------------------------------------------------------
# Bloque global
# ----------------------------------------------------------------------


def _empacar_estado_aleatorio(estado):
    if estado is None:
        return _empacar_bandera(False)

    version, claves, gauss = estado
    partes = [
        _empacar_bandera(True),
        _empacar_entero(version),
        _empacar_cantidad(len(claves)),
    ]

    for clave in claves:
        partes.append(_empacar_entero(clave))

    if gauss is None:
        partes.append(_empacar_bandera(False))
    else:
        partes.append(_empacar_bandera(True))
        partes.append(_FLOTANTE.pack(gauss))

    return b"".join(partes)


def _leer_estado_aleatorio(lector):
    if not lector.bandera():
        return None

    version = lector.entero()
    cuantas = lector.cantidad()
    claves = tuple(lector.entero() for _ in range(cuantas))
    gauss = lector.flotante() if lector.bandera() else None
    return (version, claves, gauss)


def _empacar_evento(event):
    return b"".join([
        _empacar_entero(event.time),
        _empacar_entero(event.sequence),
        _empacar_texto(event.event_type),
        _empacar_texto("" if event.actor is None else event.actor.actor_id),
        _empacar_texto("" if event.target is None else event.target.actor_id),
        _empacar_entero_opcional(event.amount),
        _empacar_entero_opcional(event.room_id),
        _empacar_texto(event.direction),
        _empacar_texto(event.instance_id),
    ])


def _leer_evento(lector):
    time = lector.entero()
    sequence = lector.entero()
    event_type = lector.texto()
    id_del_actor = lector.texto()
    id_del_objetivo = lector.texto()
    amount = lector.entero_opcional()
    room_id = lector.entero_opcional()
    direction = lector.texto()
    instance_id = lector.texto()

    event = Event(
        time,
        sequence,
        event_type,
        amount=amount,
        room_id=room_id,
        direction=direction or None,
        instance_id=instance_id or None,
    )
    return event, id_del_actor, id_del_objetivo


def _empacar_bloque_global(juego, versiones):
    id_cripta, version_cripta, version_catalogo = versiones
    state = juego.state
    eventos = juego.events.active_events()

    partes = [
        _empacar_texto(id_cripta),
        _empacar_texto(version_cripta),
        _empacar_texto(version_catalogo),
        _empacar_entero(state.seed),
        _empacar_entero(state.clock),
        _empacar_entero(state.sequence_counter),
        _empacar_estado_aleatorio(state.random_state()),
        _empacar_jugador(juego.player),
        _empacar_entero_opcional(juego.exit_room_id),
        _empacar_bandera(juego.torch_lit),
        _empacar_texto(juego.result),
        _empacar_entero(juego.player_actions),
        _empacar_entero(juego.enemies_defeated),
        _empacar_cantidad(len(eventos)),
    ]

    for event in eventos:
        partes.append(_empacar_evento(event))

    marcas = _marcas_del_rastro(juego)
    partes.append(_empacar_cantidad(len(marcas)))

    for room_id, time in marcas:
        partes.append(_empacar_entero(room_id))
        partes.append(_empacar_entero(time))

    return b"".join(partes)


def _marcas_del_rastro(juego):
    marcas = []

    if juego.trail is None or juego.room_map is None:
        return marcas

    for room_id in juego.room_map.room_ids():
        time = juego.trail.time_at(room_id)

        if time is not None:
            marcas.append((room_id, time))

    return marcas


# ----------------------------------------------------------------------
# Bloques de sala
# ----------------------------------------------------------------------


def _empacar_puerta(door):
    return b"".join([
        _empacar_entero(door.room_a),
        _empacar_entero(door.room_b),
        _empacar_bandera(door.closed),
        _empacar_texto_o_entero(door.key_id),
        _empacar_entero_opcional(door.auto_close),
    ])


def _leer_puerta(lector):
    room_a = lector.entero()
    room_b = lector.entero()
    closed = lector.bandera()
    key_id = lector.texto_o_entero()
    auto_close = lector.entero_opcional()
    return Door(room_a, room_b, closed=closed, key_id=key_id,
                auto_close=auto_close)


def _empacar_bloque_de_sala(room, enemies):
    salidas = room.exits()
    partes = [
        _empacar_entero(room.room_id),
        _empacar_texto(room.name),
        _empacar_bandera(room.content_loaded),
        _empacar_cantidad(len(salidas)),
    ]

    for exit_ in salidas:
        partes.append(_empacar_texto(exit_.direction))
        partes.append(_empacar_entero(exit_.destination))
        partes.append(_empacar_puerta(exit_.door))

    partes.append(_empacar_cantidad(len(room.traps)))

    for trap in room.traps:
        partes.append(_empacar_trampa(trap))

    partes.append(_empacar_lista_de_objetos(room.floor_items))
    partes.append(_empacar_cantidad(len(enemies)))

    for enemy in enemies:
        partes.append(_empacar_enemigo(enemy))

    return b"".join(partes)


def _leer_bloque_de_sala(contenido, puertas_compartidas=None):
    lector = _Lector(contenido, "bloque de sala")
    room = Room(lector.entero(), lector.texto())
    room.content_loaded = lector.bandera()

    cuantas_salidas = lector.cantidad()

    for _ in range(cuantas_salidas):
        direction = lector.texto()
        destination = lector.entero()
        door = _leer_puerta(lector)

        if puertas_compartidas is not None:
            door = _puerta_unica(puertas_compartidas, door)

        room.add_exit(Exit(direction, destination, door))

    cuantas_trampas = lector.cantidad()

    for _ in range(cuantas_trampas):
        room.traps.append(_leer_trampa(lector))

    room.floor_items.extend(_leer_lista_de_objetos(lector))

    cuantos_enemigos = lector.cantidad()
    enemies = [_leer_enemigo(lector) for _ in range(cuantos_enemigos)]

    return SalaGuardada(room, enemies)


def _puerta_unica(puertas_compartidas, door):
    """Una puerta es el mismo objeto desde sus dos salas.

    Cada bloque de sala guarda los datos de sus puertas, asi que una sala se
    puede leer sola. Al cargar la cripta completa, la segunda vez que aparece
    una puerta se devuelve la que ya se creo.
    """
    menor = min(door.room_a, door.room_b)
    mayor = max(door.room_a, door.room_b)
    clave = f"{menor}-{mayor}"
    existente = puertas_compartidas.obtener(clave)

    if existente is not None:
        return existente

    puertas_compartidas.insertar(clave, door)
    return door


# ----------------------------------------------------------------------
# El almacen
# ----------------------------------------------------------------------


class AlmacenPartida:
    """Una partida guardada en un archivo binario de formato propio (§4.10)."""

    def __init__(self, ruta):
        self._ruta = Path(ruta)

    @property
    def ruta(self):
        return self._ruta

    def existe(self):
        return self._ruta.is_file()

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    def guardar(self, juego, versiones=("", "", "")):
        """Escribe el estado completo de la partida.

        versiones es (id_cripta, version_cripta, version_catalogo), que se
        guardan para poder avisar al cargar si la cripta cambio.
        """
        bloque_global = _empacar_bloque_global(juego, versiones)
        bloques, ids_de_sala = self._armar_bloques_de_sala(juego)

        posicion = _TAMANO_DEL_ENCABEZADO
        posicion += _LARGO_DE_BLOQUE.size + len(bloque_global)

        entradas = []
        cuerpo = []

        for id_de_sala, bloque in zip(ids_de_sala, bloques):
            cuerpo.append(_LARGO_DE_BLOQUE.pack(len(bloque)))
            cuerpo.append(bloque)
            posicion += _LARGO_DE_BLOQUE.size
            entradas.append((id_de_sala, posicion, len(bloque)))
            posicion += len(bloque)

        indice = []

        for id_de_sala, donde, cuanto in sort(entradas, key=_primer_valor):
            indice.append(
                _ENTRADA_DEL_INDICE.pack(id_de_sala, donde, cuanto)
            )

        encabezado = _ENCABEZADO.pack(
            FIRMA_DEL_ARCHIVO,
            VERSION_DEL_FORMATO,
            posicion,
            len(entradas),
        )

        contenido = b"".join(
            [encabezado, _LARGO_DE_BLOQUE.pack(len(bloque_global)),
             bloque_global]
            + cuerpo
            + indice
        )

        self._escribir_de_una_vez(contenido)
        return len(contenido)

    def _armar_bloques_de_sala(self, juego):
        bloques = []
        ids_de_sala = []

        if juego.room_map is None:
            return bloques, ids_de_sala

        for room_id in juego.room_map.room_ids():
            room = juego.room_map.room(room_id)
            bloques.append(_empacar_bloque_de_sala(room, _enemigos_en(juego, room_id)))
            ids_de_sala.append(room_id)

        return bloques, ids_de_sala

    def _escribir_de_una_vez(self, contenido):
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self._ruta.with_suffix(self._ruta.suffix + ".tmp")

        with open(temporal, "wb") as archivo:
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())

        os.replace(temporal, self._ruta)

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def leer_encabezado(self):
        """(version del formato, posicion del indice, cantidad de salas)."""
        with open(self._ruta, "rb") as archivo:
            crudo = archivo.read(_TAMANO_DEL_ENCABEZADO)

        if len(crudo) < _TAMANO_DEL_ENCABEZADO:
            raise ArchivoDePartidaDanado("el encabezado esta incompleto")

        firma, version, posicion_del_indice, cuantas_salas = _ENCABEZADO.unpack(
            crudo
        )

        if firma != FIRMA_DEL_ARCHIVO:
            raise PartidaIncompatible(
                "el archivo no es una partida de CRIPTA "
                f"(firma {firma!r} en vez de {FIRMA_DEL_ARCHIVO!r})"
            )

        if version != VERSION_DEL_FORMATO:
            raise PartidaIncompatible(
                f"el archivo es del formato version {version} y el programa "
                f"usa la {VERSION_DEL_FORMATO}"
            )

        return version, posicion_del_indice, cuantas_salas

    def ids_de_salas(self):
        """Los ids de sala guardados, en orden, leyendo solo el indice."""
        _, posicion_del_indice, cuantas_salas = self.leer_encabezado()
        return [entrada[0] for entrada in self._leer_indice(posicion_del_indice,
                                                            cuantas_salas)]

    def leer_sala(self, id_de_sala):
        """Una sala sin leer el archivo completo (§4.10).

        Lee el encabezado, salta al indice, busca el id con busqueda binaria y
        lee unicamente los bytes de ese bloque. Devuelve None si esa sala no
        esta guardada.
        """
        _, posicion_del_indice, cuantas_salas = self.leer_encabezado()
        entradas = self._leer_indice(posicion_del_indice, cuantas_salas)
        encontrado, donde = _buscar_en_indice(entradas, id_de_sala)

        if not encontrado:
            return None

        _, posicion, longitud = entradas[donde]

        with open(self._ruta, "rb") as archivo:
            archivo.seek(posicion)
            contenido = archivo.read(longitud)

        if len(contenido) != longitud:
            raise ArchivoDePartidaDanado(
                f"el bloque de la sala {id_de_sala} quedo incompleto"
            )

        return _leer_bloque_de_sala(contenido)

    def cargar(self, versiones_vigentes=None, history=None):
        """Lee todo el archivo y devuelve una PartidaGuardada.

        Si se pasan versiones_vigentes como (version_cripta, version_catalogo)
        y no coinciden con las del archivo, levanta PartidaIncompatible.
        """
        version_del_formato, posicion_del_indice, cuantas_salas = (
            self.leer_encabezado()
        )

        with open(self._ruta, "rb") as archivo:
            archivo.seek(_TAMANO_DEL_ENCABEZADO)
            crudo = archivo.read(_LARGO_DE_BLOQUE.size)

            if len(crudo) < _LARGO_DE_BLOQUE.size:
                raise ArchivoDePartidaDanado("falta el largo del bloque global")

            largo = _LARGO_DE_BLOQUE.unpack(crudo)[0]
            bloque_global = archivo.read(largo)

            if len(bloque_global) != largo:
                raise ArchivoDePartidaDanado("el bloque global quedo incompleto")

            entradas = self._leer_indice(posicion_del_indice, cuantas_salas, archivo)
            bloques = []

            for _, posicion, longitud in entradas:
                archivo.seek(posicion)
                contenido = archivo.read(longitud)

                if len(contenido) != longitud:
                    raise ArchivoDePartidaDanado("un bloque de sala quedo incompleto")

                bloques.append(contenido)

        partida = self._interpretar(bloque_global, bloques, history)

        if versiones_vigentes is not None:
            _comprobar_versiones(partida, versiones_vigentes)

        return partida

    def _interpretar(self, bloque_global, bloques, history):
        partida = PartidaGuardada()
        lector = _Lector(bloque_global, "bloque global")

        partida.id_cripta = lector.texto()
        partida.version_cripta = lector.texto()
        partida.version_catalogo = lector.texto()
        partida.seed = lector.entero()
        partida.clock = lector.entero()
        partida.sequence_counter = lector.entero()
        partida.random_state = _leer_estado_aleatorio(lector)
        partida.player = _leer_jugador(lector, history)
        partida.exit_room_id = lector.entero_opcional()
        partida.torch_lit = lector.bandera()
        partida.result = lector.texto()
        partida.player_actions = lector.entero()
        partida.enemies_defeated = lector.entero()

        cuantos_eventos = lector.cantidad()
        eventos_sin_actor = [_leer_evento(lector) for _ in range(cuantos_eventos)]

        cuantas_marcas = lector.cantidad()
        partida.trail_marks = [
            (lector.entero(), lector.entero()) for _ in range(cuantas_marcas)
        ]

        puertas_compartidas = TablaHash()
        room_map = RoomMap()
        enemies = []

        for contenido in bloques:
            guardada = _leer_bloque_de_sala(contenido, puertas_compartidas)
            room_map.add(guardada.room)
            enemies.extend(guardada.enemies)

        partida.room_map = room_map
        partida.enemies = enemies
        partida.events = _reapuntar_eventos(
            eventos_sin_actor, partida.player, enemies
        )
        return partida

    def _leer_indice(self, posicion_del_indice, cuantas_salas, archivo=None):
        tamano = _ENTRADA_DEL_INDICE.size

        if archivo is None:
            with open(self._ruta, "rb") as abierto:
                abierto.seek(posicion_del_indice)
                crudo = abierto.read(tamano * cuantas_salas)
        else:
            archivo.seek(posicion_del_indice)
            crudo = archivo.read(tamano * cuantas_salas)

        if len(crudo) != tamano * cuantas_salas:
            raise ArchivoDePartidaDanado("el indice de salas esta incompleto")

        entradas = []

        for numero in range(cuantas_salas):
            entradas.append(
                _ENTRADA_DEL_INDICE.unpack_from(crudo, numero * tamano)
            )

        return entradas


def _primer_valor(entrada):
    return entrada[0]


def _enemigos_en(juego, room_id):
    enemigos = []

    for enemy in juego.enemies:
        if enemy.room_id == room_id:
            enemigos.append(enemy)

    return enemigos


def _buscar_en_indice(entradas, id_de_sala):
    """Busqueda binaria sobre el indice ordenado. (encontrado, posicion)."""
    izquierda = 0
    derecha = len(entradas)

    while izquierda < derecha:
        medio = (izquierda + derecha) // 2

        if entradas[medio][0] < id_de_sala:
            izquierda = medio + 1
        else:
            derecha = medio

    encontrado = (izquierda < len(entradas)
                  and entradas[izquierda][0] == id_de_sala)
    return encontrado, izquierda


def _reapuntar_eventos(eventos_sin_actor, player, enemies):
    """Devuelve los eventos con las referencias a los actores ya puestas.

    El archivo guarda el identificador del actor, no el objeto. Para
    encontrarlo se usa una TablaHash, porque §7 prohibe usar dict como indice.
    """
    actores = TablaHash()

    if player is not None:
        actores.insertar(player.actor_id, player)

    for enemy in enemies:
        actores.insertar(enemy.actor_id, enemy)

    eventos = []

    for event, id_del_actor, id_del_objetivo in eventos_sin_actor:
        if id_del_actor:
            event.actor = actores.obtener(id_del_actor)

        if id_del_objetivo:
            event.target = actores.obtener(id_del_objetivo)

        eventos.append(event)

    return eventos


def _comprobar_versiones(partida, versiones_vigentes):
    version_cripta, version_catalogo = versiones_vigentes

    if partida.version_cripta and partida.version_cripta != version_cripta:
        raise PartidaIncompatible(
            f"la partida se guardo con la cripta version {partida.version_cripta} "
            f"y la vigente es la {version_cripta}"
        )

    if partida.version_catalogo and partida.version_catalogo != version_catalogo:
        raise PartidaIncompatible(
            f"la partida se guardo con el catalogo version "
            f"{partida.version_catalogo} y el vigente es el {version_catalogo}"
        )


def construir_juego(partida, trail=None, history=None, event_queue=None,
                    message_log=None):
    """Arma el Game de una partida leida del archivo.

    Se usa Game.load() y no el constructor normal: el constructor hace el
    trabajo de inicio de partida (programa la primera accion del jugador en el
    instante 0 y activa los enemigos de la sala inicial), asi que una partida
    cargada con el constructor quedaria mal sin dar ningun error.
    """
    from model.game import Game
    from model.game_state import GameState
    from structures.trail import PlayerTrail

    state = GameState(seed=partida.seed)
    state.restore(partida.clock, partida.sequence_counter, partida.random_state)

    if trail is None:
        trail = PlayerTrail(history)

    for room_id, time in partida.trail_marks:
        trail.mark(room_id, time)

    return Game.load(
        state,
        partida.player,
        partida.enemies,
        partida.room_map,
        partida.exit_room_id,
        trail,
        history=history,
        event_queue=event_queue,
        message_log=message_log,
        events=partida.events,
        torch_lit=partida.torch_lit,
        result=partida.result,
        player_actions=partida.player_actions,
        enemies_defeated=partida.enemies_defeated,
    )
