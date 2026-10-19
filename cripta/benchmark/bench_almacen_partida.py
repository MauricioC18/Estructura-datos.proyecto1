"""
Benchmark del guardado binario de la partida (problema 4.10).

§4.10 pide comparar tamaño en disco y tiempo de carga contra guardar el mismo
estado en JSON. Se miden tres cosas, en criptas de tamaños distintos:

    1. Tamaño del archivo.
    2. Tiempo de cargar la partida completa.
    3. Tiempo de recuperar UNA sala. Es lo que §4.10 pide poder hacer sin leer
       el archivo completo, y es donde el formato propio se separa del JSON:
       el binario salta al bloque de esa sala por su índice, mientras el JSON
       tiene que leer y convertir todo el archivo para después quedarse con
       una sola sala.

La alternativa descartada que se mide es el JSON con el mismo estado. Se
escribe acá y no en el programa, igual que la lista sin ordenar de
benchmark/scheduler_bench.py, porque solo existe para comparar.

También se mide la otra alternativa que se descartó al diseñar el formato:
guardar solo los identificadores de los objetos, trampas y enemigos y pedirle
el resto al catálogo al cargar. Da un archivo más chico, y la medición dice
cuánto, para poder decir con números qué costó la decisión de que el archivo se
abra solo.

Nota: después de la primera lectura el sistema operativo guarda el archivo en
su propia memoria, así que esto mide el disco "caliente", que es el caso normal
mientras se juega.

Ejecutar desde la carpeta cripta/:  python -m benchmark.bench_almacen_partida
"""
import json
import struct
import tempfile
import time
from pathlib import Path

from adapters.almacen_partida import (
    AlmacenPartida,
    _empacar_bandera,
    _empacar_cantidad,
    _empacar_entero,
    _empacar_entero_opcional,
    _empacar_estado_aleatorio,
    _empacar_evento,
    _empacar_texto,
)
from benchmark.scheduler_bench import build_synthetic_crypt
from benchmark.utilidades_medicion import (
    Measurement,
    calentar_procesador,
    descripcion_del_equipo,
)
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.item import Item
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from model.trap import Trap
from structures.inventory import Inventory
from structures.trail import PlayerTrail

ESCENARIOS = (
    ("cripta chica", 6, 6),
    ("cripta mediana", 40, 50),
    ("cripta grande", 200, 300),
)

REPETICIONES = 7


# ----------------------------------------------------------------------
# La partida que se va a guardar
# ----------------------------------------------------------------------


def _objeto(numero):
    return Item(
        instance_id=f"i-{numero}",
        type_id="itm_pocion_menor",
        name=f"Pocion menor {numero}",
        item_class=Item.POTION,
        weight=1,
        value=5,
        heal=8,
    )


def construir_partida(room_count, enemy_count, decisiones=25):
    """Una partida jugada un rato, con enemigos, objetos en el suelo y rastro."""
    room_map = build_synthetic_crypt(room_count)

    for numero in range(1, room_count + 1):
        room_map.room(numero).floor_items.append(_objeto(f"{numero}-a"))

        if numero % 2 == 0:
            room_map.room(numero).floor_items.append(_objeto(f"{numero}-b"))

    enemies = []

    for numero in range(enemy_count):
        comportamiento = (
            Enemy.GUARDIAN if numero % 3 == 0
            else Enemy.WANDERER if numero % 3 == 1
            else Enemy.TRACKER
        )
        enemies.append(
            Enemy(
                actor_id=f"e-{numero:04d}",
                name=f"Enemigo {numero}",
                max_health=20,
                attack=4,
                defense=1,
                speed=90 + (numero % 7) * 10,
                room_id=1 + numero % room_count,
                behavior=comportamiento,
                drops=[_objeto(f"d-{numero}")],
                regeneration=2 if numero % 5 == 0 else 0,
            )
        )

    player = Player("p-1", "Heroe", 10000, 6, 2, 100, 1)
    player.inventory = Inventory(20)

    for numero in range(8):
        player.inventory.pick_up(_objeto(f"inv-{numero}"))

    game = Game(
        GameState(seed=2026),
        player,
        enemies,
        room_map=room_map,
        exit_room_id=room_count,
        trail=PlayerTrail(),
    )

    for _ in range(decisiones):
        game.wait()

    return game


# ----------------------------------------------------------------------
# La alternativa descartada: el mismo estado en JSON
# ----------------------------------------------------------------------


def _objeto_a_json(item):
    return {
        "instance_id": item.instance_id,
        "type_id": item.type_id,
        "name": item.name,
        "item_class": item.item_class,
        "weight": item.weight,
        "value": item.value,
        "attack_bonus": item.attack_bonus,
        "defense_bonus": item.defense_bonus,
        "heal": item.heal,
        "speed_modifier": item.speed_modifier,
        "duration": item.duration,
        "opens": item.opens,
    }


def _objeto_desde_json(crudo):
    return Item(**crudo)


def guardar_en_json(juego, ruta, versiones=("", "", "")):
    """El mismo estado que guarda AlmacenPartida, en un solo archivo JSON."""
    id_cripta, version_cripta, version_catalogo = versiones
    state = juego.state

    salas = []

    for room_id in juego.room_map.room_ids():
        room = juego.room_map.room(room_id)
        salas.append({
            "room_id": room.room_id,
            "name": room.name,
            "content_loaded": room.content_loaded,
            "exits": [
                {
                    "direction": exit_.direction,
                    "destination": exit_.destination,
                    "door": {
                        "room_a": exit_.door.room_a,
                        "room_b": exit_.door.room_b,
                        "closed": exit_.door.closed,
                        "key_id": exit_.door.key_id,
                        "auto_close": exit_.door.auto_close,
                    },
                }
                for exit_ in room.exits()
            ],
            "traps": [
                {
                    "instance_id": trap.instance_id,
                    "type_id": trap.type_id,
                    "name": trap.name,
                    "damage": trap.damage,
                    "rearm_interval": trap.rearm_interval,
                    "room_id": trap.room_id,
                    "armed": trap.armed,
                }
                for trap in room.traps
            ],
            "floor_items": [_objeto_a_json(item) for item in room.floor_items],
            "enemies": [
                {
                    "actor_id": enemy.actor_id,
                    "name": enemy.name,
                    "max_health": enemy.max_health,
                    "health": enemy.health,
                    "attack": enemy.attack,
                    "defense": enemy.defense,
                    "speed": enemy.speed,
                    "room_id": enemy.room_id,
                    "is_active": enemy.is_active,
                    "behavior": enemy.behavior,
                    "regeneration": enemy.regeneration,
                    "drops": [_objeto_a_json(item) for item in enemy.drops],
                }
                for enemy in juego.enemies if enemy.room_id == room_id
            ],
        })

    version_aleatoria, claves, gauss = state.random_state()
    inventario = list(juego.player.inventory)

    contenido = {
        "id_cripta": id_cripta,
        "version_cripta": version_cripta,
        "version_catalogo": version_catalogo,
        "seed": state.seed,
        "clock": state.clock,
        "sequence_counter": state.sequence_counter,
        "random_state": [version_aleatoria, list(claves), gauss],
        "player": {
            "actor_id": juego.player.actor_id,
            "name": juego.player.name,
            "max_health": juego.player.max_health,
            "health": juego.player.health,
            "attack": juego.player.attack,
            "defense": juego.player.defense,
            "speed": juego.player.speed,
            "room_id": juego.player.room_id,
            "capacity": juego.player.inventory.capacity,
            "items": [_objeto_a_json(item) for item in inventario],
            "equipped_weapon": (
                None if juego.player.equipped_weapon is None
                else juego.player.equipped_weapon.instance_id
            ),
            "equipped_armor": (
                None if juego.player.equipped_armor is None
                else juego.player.equipped_armor.instance_id
            ),
        },
        "exit_room_id": juego.exit_room_id,
        "torch_lit": juego.torch_lit,
        "result": juego.result,
        "player_actions": juego.player_actions,
        "enemies_defeated": juego.enemies_defeated,
        "events": [
            {
                "time": event.time,
                "sequence": event.sequence,
                "event_type": event.event_type,
                "actor": None if event.actor is None else event.actor.actor_id,
                "target": None if event.target is None else event.target.actor_id,
                "amount": event.amount,
                "room_id": event.room_id,
                "direction": event.direction,
                "instance_id": event.instance_id,
            }
            for event in juego.events.active_events()
        ],
        "trail": [
            [room_id, juego.trail.time_at(room_id)]
            for room_id in juego.room_map.room_ids()
            if juego.trail.time_at(room_id) is not None
        ],
        "rooms": salas,
    }

    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(contenido, archivo)

    return ruta.stat().st_size


def cargar_desde_json(ruta):
    """Reconstruye los mismos objetos que AlmacenPartida.cargar()."""
    with open(ruta, encoding="utf-8") as archivo:
        contenido = json.load(archivo)

    room_map = RoomMap()
    enemies = []
    puertas = {}

    for cruda in contenido["rooms"]:
        room = Room(cruda["room_id"], cruda["name"])
        room.content_loaded = cruda["content_loaded"]

        for salida in cruda["exits"]:
            datos = salida["door"]
            clave = (min(datos["room_a"], datos["room_b"]),
                     max(datos["room_a"], datos["room_b"]))

            if clave not in puertas:
                puertas[clave] = Door(
                    datos["room_a"], datos["room_b"],
                    closed=datos["closed"], key_id=datos["key_id"],
                    auto_close=datos["auto_close"],
                )

            room.add_exit(
                Exit(salida["direction"], salida["destination"], puertas[clave])
            )

        for trampa in cruda["traps"]:
            room.traps.append(Trap(**trampa))

        for item in cruda["floor_items"]:
            room.floor_items.append(_objeto_desde_json(item))

        for enemigo in cruda["enemies"]:
            drops = [_objeto_desde_json(item) for item in enemigo["drops"]]
            enemy = Enemy(
                actor_id=enemigo["actor_id"],
                name=enemigo["name"],
                max_health=enemigo["max_health"],
                attack=enemigo["attack"],
                defense=enemigo["defense"],
                speed=enemigo["speed"],
                room_id=enemigo["room_id"],
                behavior=enemigo["behavior"],
                health=enemigo["health"],
                drops=drops,
                regeneration=enemigo["regeneration"],
            )
            enemy.is_active = enemigo["is_active"]
            enemies.append(enemy)

        room_map.add(room)

    crudo = contenido["player"]
    player = Player(
        crudo["actor_id"], crudo["name"], crudo["max_health"], crudo["attack"],
        crudo["defense"], crudo["speed"], crudo["room_id"], health=crudo["health"],
    )
    player.inventory = Inventory(crudo["capacity"])

    for item in crudo["items"]:
        player.inventory.pick_up(_objeto_desde_json(item))

    return room_map, enemies, player, contenido


def leer_una_sala_del_json(ruta, id_de_sala):
    """Para quedarse con una sala hay que leer y convertir todo el archivo."""
    with open(ruta, encoding="utf-8") as archivo:
        contenido = json.load(archivo)

    for cruda in contenido["rooms"]:
        if cruda["room_id"] == id_de_sala:
            return cruda

    return None


# ----------------------------------------------------------------------
# La otra alternativa descartada: guardar solo los identificadores
# ----------------------------------------------------------------------


def tamano_solo_con_identificadores(juego, carpeta):
    """Cuánto mediría el archivo guardando solo lo que cambia.

    Los objetos, las trampas y los enemigos los construye el traductor desde
    el catálogo, así que el archivo podría guardar solo el identificador de la
    instancia, el de su ficha y lo que cambia durante la partida, y pedirle el
    resto al catálogo al cargar.

    Acá se arma ese formato mínimo de verdad, omitiendo los campos estáticos,
    no poniéndolos en cero: los enteros del formato son de ancho fijo, así que
    vaciarlos no ahorraría ni un byte. Se usan las mismas primitivas que el
    formato real y se le deja el mismo encabezado y el mismo índice, de modo
    que la diferencia de bytes sea solo la de los campos.

    Al enemigo se le agrega el id de su ficha, que hoy no guarda, porque esa
    alternativa lo necesitaría para reconstruirlo. Se usa uno del largo de los
    reales para que la comparación no quede a favor.
    """
    partes_globales = [
        _empacar_texto("cripta-01"),
        _empacar_texto("3"),
        _empacar_texto("7"),
        _empacar_entero(juego.state.seed),
        _empacar_entero(juego.state.clock),
        _empacar_entero(juego.state.sequence_counter),
        _empacar_estado_aleatorio(juego.state.random_state()),
        _empacar_texto(juego.player.actor_id),
        _empacar_entero(juego.player.health),
        _empacar_entero(juego.player.room_id),
        _empacar_entero(juego.player.speed),
        _empacar_entero(juego.player.inventory.capacity),
        _empacar_entero(0),
        _empacar_texto(""),
        _empacar_texto(""),
        _empacar_entero_opcional(juego.exit_room_id),
        _empacar_bandera(juego.torch_lit),
        _empacar_texto(juego.result),
        _empacar_entero(juego.player_actions),
        _empacar_entero(juego.enemies_defeated),
    ]

    inventario = list(juego.player.inventory)
    partes_globales.append(_empacar_cantidad(len(inventario)))

    for item in inventario:
        partes_globales.append(_empacar_texto(item.instance_id))
        partes_globales.append(_empacar_texto(item.type_id))

    eventos = juego.events.active_events()
    partes_globales.append(_empacar_cantidad(len(eventos)))

    for event in eventos:
        partes_globales.append(_empacar_evento(event))

    marcas = [
        (room_id, juego.trail.time_at(room_id))
        for room_id in juego.room_map.room_ids()
        if juego.trail.time_at(room_id) is not None
    ]
    partes_globales.append(_empacar_cantidad(len(marcas)))

    for room_id, momento in marcas:
        partes_globales.append(_empacar_entero(room_id))
        partes_globales.append(_empacar_entero(momento))

    bloque_global = b"".join(partes_globales)
    bloques = []

    for room_id in juego.room_map.room_ids():
        room = juego.room_map.room(room_id)
        partes = [
            _empacar_entero(room.room_id),
            _empacar_bandera(room.content_loaded),
            _empacar_cantidad(len(room.exits())),
        ]

        for exit_ in room.exits():
            partes.append(_empacar_texto(exit_.direction))
            partes.append(_empacar_entero(exit_.destination))
            partes.append(_empacar_entero(exit_.door.room_a))
            partes.append(_empacar_entero(exit_.door.room_b))
            partes.append(_empacar_bandera(exit_.door.closed))
            partes.append(_empacar_entero_opcional(exit_.door.auto_close))

        partes.append(_empacar_cantidad(len(room.traps)))

        for trap in room.traps:
            partes.append(_empacar_texto(trap.instance_id))
            partes.append(_empacar_texto(trap.type_id))
            partes.append(_empacar_bandera(trap.armed))

        partes.append(_empacar_cantidad(len(room.floor_items)))

        for item in room.floor_items:
            partes.append(_empacar_texto(item.instance_id))
            partes.append(_empacar_texto(item.type_id))

        enemigos = [
            enemy for enemy in juego.enemies if enemy.room_id == room_id
        ]
        partes.append(_empacar_cantidad(len(enemigos)))

        for enemy in enemigos:
            partes.append(_empacar_texto(enemy.actor_id))
            partes.append(_empacar_texto("ent_rata_gigante"))
            partes.append(_empacar_entero(enemy.health))
            partes.append(_empacar_entero(enemy.room_id))
            partes.append(_empacar_bandera(enemy.is_active))

        bloques.append(b"".join(partes))

    tamano_del_encabezado = struct.calcsize("<8sHQI")
    largo_de_bloque = struct.calcsize("<I")
    entrada_del_indice = struct.calcsize("<iQI")

    total = tamano_del_encabezado + largo_de_bloque + len(bloque_global)

    for bloque in bloques:
        total += largo_de_bloque + len(bloque)

    total += entrada_del_indice * len(bloques)

    return total


# ----------------------------------------------------------------------
# Frecuencia de las operaciones (§8.1)
# ----------------------------------------------------------------------


def contar_operaciones(juego):
    """Cuántas veces empaca cada cosa un guardado.

    Cada sala, salida, trampa, objeto, enemigo y evento se empaca exactamente
    una vez por guardado, así que contarlos en el estado da la frecuencia real
    de las operaciones del formato sin tener que instrumentar nada.
    """
    conteos = {
        "salas": 0,
        "salidas": 0,
        "trampas": 0,
        "objetos": 0,
        "enemigos": 0,
        "eventos": len(juego.events.active_events()),
        "marcas de rastro": 0,
    }

    for room_id in juego.room_map.room_ids():
        room = juego.room_map.room(room_id)
        conteos["salas"] += 1
        conteos["salidas"] += len(room.exits())
        conteos["trampas"] += len(room.traps)
        conteos["objetos"] += len(room.floor_items)

        if juego.trail.time_at(room_id) is not None:
            conteos["marcas de rastro"] += 1

    for enemy in juego.enemies:
        conteos["enemigos"] += 1
        conteos["objetos"] += len(enemy.drops)

    conteos["objetos"] += len(list(juego.player.inventory))
    return conteos


# ----------------------------------------------------------------------
# Medición
# ----------------------------------------------------------------------


def _segundos_por_llamada(operacion, repeticiones=REPETICIONES):
    mejor = None

    for _ in range(repeticiones):
        inicio = time.perf_counter()
        operacion()
        transcurrido = time.perf_counter() - inicio

        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    return mejor


def medir(room_count, enemy_count):
    with tempfile.TemporaryDirectory() as temporal:
        carpeta = Path(temporal)
        juego = construir_partida(room_count, enemy_count)

        ruta_binaria = carpeta / "partida.cripta"
        almacen = AlmacenPartida(ruta_binaria)
        bytes_binarios = almacen.guardar(juego, versiones=("cripta-01", "3", "7"))

        ruta_json = carpeta / "partida.json"
        bytes_json = guardar_en_json(
            juego, ruta_json, versiones=("cripta-01", "3", "7")
        )

        del_medio = 1 + room_count // 2

        resultado = {
            "salas": room_count,
            "enemigos": enemy_count,
            "bytes_binarios": bytes_binarios,
            "bytes_json": bytes_json,
            "carga_binaria": _segundos_por_llamada(lambda: almacen.cargar()),
            "carga_json": _segundos_por_llamada(
                lambda: cargar_desde_json(ruta_json)
            ),
            "una_sala_binaria": _segundos_por_llamada(
                lambda: almacen.leer_sala(del_medio)
            ),
            "una_sala_json": _segundos_por_llamada(
                lambda: leer_una_sala_del_json(ruta_json, del_medio)
            ),
        }

        resultado["operaciones"] = contar_operaciones(juego)
        resultado["bytes_solo_ids"] = tamano_solo_con_identificadores(juego, carpeta)
        return resultado


def medir_guardado(room_count, enemy_count):
    """Tiempo de escribir la partida, en binario y en JSON."""
    with tempfile.TemporaryDirectory() as temporal:
        carpeta = Path(temporal)
        juego = construir_partida(room_count, enemy_count)
        almacen = AlmacenPartida(carpeta / "partida.cripta")
        ruta_json = carpeta / "partida.json"
        versiones = ("cripta-01", "3", "7")

        return (
            _segundos_por_llamada(lambda: almacen.guardar(juego, versiones=versiones)),
            _segundos_por_llamada(
                lambda: guardar_en_json(juego, ruta_json, versiones=versiones)
            ),
        )


def run():
    """Mediciones para el ejecutor de --bench (benchmark/benchmark.py)."""
    measurements = []

    for nombre, room_count, enemy_count in ESCENARIOS:
        datos = medir(room_count, enemy_count)
        guardado_binario, guardado_json = medir_guardado(room_count, enemy_count)
        escenario = f"{room_count} salas, {enemy_count} enemigos"

        measurements.append(Measurement(
            f"Tamano ({nombre})", None,
            f"binario {_kilobytes(datos['bytes_binarios'])}, "
            f"JSON {_kilobytes(datos['bytes_json'])} [descartado], "
            f"solo ids {_kilobytes(datos['bytes_solo_ids'])} [descartado]",
        ))

        for operacion, binario, json_ in (
            ("Guardar", guardado_binario, guardado_json),
            ("Cargar completa", datos["carga_binaria"], datos["carga_json"]),
            ("Recuperar una sala", datos["una_sala_binaria"], datos["una_sala_json"]),
        ):
            measurements.append(Measurement(
                f"{operacion}: binario ({nombre})", binario, escenario,
            ))
            measurements.append(Measurement(
                f"{operacion}: JSON [descartado] ({nombre})", json_,
                f"{json_ / binario:.2f}x el binario",
            ))

    return measurements


def _milisegundos(segundos):
    return f"{segundos * 1000:.3f} ms"


def _kilobytes(cuantos):
    return f"{cuantos / 1024:.1f} KB"


def main():
    print("Guardado binario de la partida (problema 4.10)")
    print(descripcion_del_equipo())
    print()
    calentar_procesador()

    resultados = []

    for nombre, room_count, enemy_count in ESCENARIOS:
        print(f"Midiendo {nombre}: {room_count} salas, {enemy_count} enemigos...")
        resultados.append((nombre, medir(room_count, enemy_count)))

    print()
    print("Frecuencia de las operaciones por guardado")
    columnas = ("salas", "salidas", "trampas", "objetos", "enemigos", "eventos",
                "marcas de rastro")
    encabezado = f"{'escenario':<18}" + "".join(f"{nombre:>18}" for nombre in columnas)
    print(encabezado)

    for nombre, datos in resultados:
        fila = f"{nombre:<18}" + "".join(
            f"{datos['operaciones'][columna]:>18}" for columna in columnas
        )
        print(fila)

    print()
    print("Tamaño en disco")
    print(f"{'escenario':<18}{'binario':>12}{'JSON':>12}{'JSON/binario':>15}")

    for nombre, datos in resultados:
        razon = datos["bytes_json"] / datos["bytes_binarios"]
        print(f"{nombre:<18}{_kilobytes(datos['bytes_binarios']):>12}"
              f"{_kilobytes(datos['bytes_json']):>12}{razon:>14.2f}x")

    print()
    print("Tiempo de cargar la partida completa")
    print(f"{'escenario':<18}{'binario':>12}{'JSON':>12}{'JSON/binario':>15}")

    for nombre, datos in resultados:
        razon = datos["carga_json"] / datos["carga_binaria"]
        print(f"{nombre:<18}{_milisegundos(datos['carga_binaria']):>12}"
              f"{_milisegundos(datos['carga_json']):>12}{razon:>14.2f}x")

    print()
    print("Tiempo de recuperar UNA sala (lo que pide §4.10)")
    print(f"{'escenario':<18}{'binario':>12}{'JSON':>12}{'JSON/binario':>15}")

    for nombre, datos in resultados:
        razon = datos["una_sala_json"] / datos["una_sala_binaria"]
        print(f"{nombre:<18}{_milisegundos(datos['una_sala_binaria']):>12}"
              f"{_milisegundos(datos['una_sala_json']):>12}{razon:>14.2f}x")

    print()
    print("Alternativa descartada: guardar solo los identificadores")
    print(f"{'escenario':<18}{'completo':>12}{'solo ids':>12}{'ahorro':>12}")

    for nombre, datos in resultados:
        ahorro = 1 - datos["bytes_solo_ids"] / datos["bytes_binarios"]
        print(f"{nombre:<18}{_kilobytes(datos['bytes_binarios']):>12}"
              f"{_kilobytes(datos['bytes_solo_ids']):>12}{ahorro * 100:>11.1f}%")


if __name__ == "__main__":
    main()
