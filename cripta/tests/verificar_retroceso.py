"""
Verificador del retroceso para las pruebas del motor.

Problema que resuelve
    Un cambio que el motor olvida anotar en el historial no lanza ninguna
    excepcion: simplemente no se deshace. Este modulo lo vuelve visible. Toma
    una "foto" de todo lo que §2.11 dice que debe revertirse, ejecuta una
    accion, usa el pergamino y compara. Si algo quedo distinto, la prueba
    falla y dice exactamente que campo fue.

Solo es para pruebas. El juego nunca copia el estado: la foto existe solo
dentro de la prueba, para comparar, y nunca se usa para restaurar nada. Por
eso no choca con la prohibicion de §2.11.

Uso, desde una prueba de Game:

    from tests.verificar_retroceso import assert_rewind_restores

    def test_atacar_se_revierte(self):
        assert_rewind_restores(self, game, lambda: game.attack("e-201"), trail=game.trail)

La accion se ejecuta y se revierte con game.rewind(), asi que el jugador
necesita al menos un pergamino en el inventario.

Que se compara
    Reloj; vida, sala, velocidad y equipo del jugador; vida, sala, velocidad,
    is_active y evento pendiente de cada enemigo; puertas, trampas y objetos
    del suelo de cada sala; orden real del inventario; eventos activos de la
    agenda con su time y sequence; efectos; antorcha; resultado; acciones del
    jugador y enemigos derrotados; y el rastro de cada sala, si se pasa.

Que no se compara, a proposito
    - Pergaminos de retroceso, en el suelo y en el inventario (§2.11). Su
      cantidad se verifica aparte: debe quedar en la de antes menos uno.
    - La bitacora en pantalla, que es presentacion.
    - El contador de secuencia y el generador aleatorio (DECISIONES.md).
    - events_processed, que es una medicion y no estado del juego.
    - El cursor del inventario, que no es estado del juego.
"""
from structures.inventory import is_rewind_scroll
from structures.sorting import sort


def _ids_without_scrolls(items):
    return [item.instance_id for item in items if not is_rewind_scroll(item)]


def _id_or_none(item):
    return None if item is None else item.instance_id


def _event_key(event):
    return (event.time, event.sequence)


def _event_view(event):
    if event is None:
        return None

    return (
        event.time,
        event.sequence,
        event.event_type,
        None if event.actor is None else event.actor.actor_id,
        None if event.target is None else event.target.actor_id,
        event.amount,
        event.room_id,
        event.direction,
        event.instance_id,
    )


def snapshot(game, trail=None):
    """Lista de (campo, valor) con lo que el retroceso debe restaurar."""
    fields = []
    player = game.player

    fields.append(("reloj", game.state.clock))
    fields.append(("resultado", game.result))
    fields.append(("antorcha encendida", game.torch_lit))
    fields.append(("acciones del jugador", game.player_actions))
    fields.append(("enemigos derrotados", game.enemies_defeated))

    fields.append(("jugador.vida", player.health))
    fields.append(("jugador.sala", player.room_id))
    fields.append(("jugador.velocidad", player.speed))
    fields.append(("jugador.arma", _id_or_none(player.equipped_weapon)))
    fields.append(("jugador.armadura", _id_or_none(player.equipped_armor)))
    fields.append(("jugador.evento pendiente", _event_view(player.scheduled_event)))

    if player.inventory is not None:
        fields.append(("inventario (orden real)", _ids_without_scrolls(player.inventory)))

    for enemy in game.enemies:
        name = f"enemigo {enemy.actor_id}"
        fields.append((f"{name}.vida", enemy.health))
        fields.append((f"{name}.sala", enemy.room_id))
        fields.append((f"{name}.velocidad", enemy.speed))
        fields.append((f"{name}.activo", enemy.is_active))
        fields.append((f"{name}.evento pendiente", _event_view(enemy.scheduled_event)))

    if game.room_map is not None:
        for room_id in game.room_map.room_ids():
            room = game.room_map.room(room_id)
            name = f"sala {room_id}"
            fields.append((f"{name}.suelo", _ids_without_scrolls(room.floor_items)))

            for exit_ in room.exits():
                fields.append((f"{name}.puerta {exit_.direction}.cerrada", exit_.door.closed))

            for trap in room.traps:
                fields.append((f"{name}.trampa {trap.instance_id}.armada", trap.armed))

            if trail is not None:
                fields.append((f"{name}.rastro", trail.time_at(room_id)))

    active = sort(game.events.active_events(), key=_event_key)
    fields.append(("agenda (eventos activos)", [_event_view(event) for event in active]))

    fields.append(
        (
            "efectos",
            [
                (effect.name, effect.target.actor_id, effect.ends_at, effect.cancelled)
                for effect in game.effects
            ],
        )
    )

    return fields


def differences(before, after):
    """Campos que cambiaron entre dos fotos, como texto legible."""
    found = []
    after_values = after

    if len(before) != len(after_values):
        found.append(
            f"cambio la cantidad de campos ({len(before)} antes, {len(after_values)} despues): "
            "aparecio o desaparecio una sala, un enemigo, una salida o una trampa"
        )

    for index in range(min(len(before), len(after_values))):
        name, old = before[index]
        other_name, new = after_values[index]

        if name != other_name:
            found.append(f"el campo {name} ahora es {other_name}")
        elif old != new:
            found.append(f"{name}: antes {old!r}, despues del retroceso {new!r}")

    return found


def assert_rewind_restores(testcase, game, action, trail=None):
    """Ejecuta action(), usa game.rewind() y exige que todo quede como antes."""
    inventory = game.player.inventory
    testcase.assertIsNotNone(inventory, "El jugador necesita un inventario.")
    testcase.assertGreater(inventory.scroll_count(), 0, "El jugador necesita un pergamino.")

    before = snapshot(game, trail)
    scrolls_before = inventory.scroll_count()

    result = action()
    testcase.assertTrue(result.accepted, f"La accion fue rechazada: {result.message}")

    rewind = game.rewind()
    testcase.assertTrue(rewind.accepted, f"El retroceso fue rechazado: {rewind.message}")

    found = differences(before, snapshot(game, trail))
    testcase.assertEqual(
        found,
        [],
        "El retroceso no restauro todo. Probablemente falta anotar en el historial:\n  "
        + "\n  ".join(found),
    )
    testcase.assertEqual(
        inventory.scroll_count(),
        scrolls_before - 1,
        "El pergamino usado debe quedar consumido (§2.11).",
    )
