# Persona 3: inventario, historial reversible, rastro, bitácora y ordenamiento

Esta rama agrega solo archivos nuevos. No modifica ningún archivo de otro integrante. Los nombres y la ubicación son los que fija `docs/ARQUITECTURA.md`.

| Archivo | Contenido |
| --- | --- |
| `structures/circular_log.py` | `CircularBuffer` y `CircularLog` (20 mensajes) |
| `structures/inventory.py` | `DoublyLinkedList` e `Inventory` |
| `structures/history.py` | `History`, `ReversibleEventQueue`, `use_rewind_scroll` |
| `structures/trail.py` | `PlayerTrail` |
| `structures/sorting.py` | `insertion_sort`, `merge_sort` y `sort` (selección automática) |
| `benchmark/persona3_bench.py` | `run()`, con el mismo contrato de `Measurement` |
| `tests/test_*.py` | 113 pruebas propias |
| `tests/verificar_retroceso.py` | `assert_rewind_restores`, para probar el retroceso del motor (sección 4) |

Esta rama se basa en `mauricio-logica-juego`, porque necesita `model/item.py`, `model/room.py` y `structures/tabla_hash.py`.

## 1. Bitácora: se conecta sin tocar el motor

`CircularLog` cumple el contrato de `Game`: tiene `append()` y se puede recorrer.

```python
game = Game(state, player, enemies, room_map, exit_room_id, message_log=CircularLog())
```

`visible_state().messages` deja de crecer sin límite. La prueba `test_plugs_into_game` lo comprueba con el motor real.

## 2. Inventario

`Player.inventory = Inventory(datos.inventario_max, history)`

`Game._player_has_key()` ya funciona con el inventario sin cambios, porque `Inventory` se puede recorrer y da objetos `Item`.

| Método | Devuelve | Para |
| --- | --- | --- |
| `is_full()` | `bool` | rechazar `recoger` sin consumir tiempo (Apéndice B) |
| `pick_up(item)` | `bool` | agrega al final del orden real y deja el cursor sobre el objeto recogido |
| `current()` | `Item` o `None` | el objeto que se está viendo |
| `next()`, `previous()`, `go_to_start()` | `bool` | navegación, costo 0 |
| `drop_current(player)` | `Item` o `None` | lo quita y, si estaba equipado, lo desequipa en `player` |
| `can_equip_current()` | `bool` | validar antes de cobrar el costo |
| `equip_current(player)` | `Item` sustituido o `None` | mueve al frente y actualiza `player.equipped_weapon` o `player.equipped_armor` |
| `sorted_view("peso" \| "valor" \| "nombre", reverse=False)` | `list` | vista para el comando `ver`; no altera el orden real |
| `scroll_count()`, `consume_scroll()` | | pergaminos |

**Cursor después de recoger.** El enunciado no define este caso, así que es una decisión de implementación. El cursor queda sobre el objeto recogido, para que `recoger` seguido de `equipar` o `usar` actúe sobre él sin un `sig` en medio. Un `recoger` rechazado no mueve el cursor. Esto cambia lo que muestra la vista, pero no afecta la reproducción: el replay ejecuta el mismo código y deja el cursor en el mismo lugar.

El equipo sigue viviendo en `Player`. El inventario solo lo actualiza, así que `effective_attack` y `effective_defense` no cambian.

`use_item()` no es parte de este módulo, porque aplica efectos que administra el motor. Para un objeto consumible, el motor puede llamar a `drop_current()` sin colocarlo en el suelo.

## 3. Rastro

```python
trail = PlayerTrail(history)
trail.mark(player.room_id, 0)                 # al iniciar (§2.9)
trail.mark(player.room_id, state.clock)       # en cada acción aceptada del jugador (Apéndice B)
exit_ = trail.freshest_exit(room, state.clock)  # turno del rastreador: Exit o None
```

`freshest_exit` devuelve el `Exit`, así que `Enemy.decide_action()` puede responder `(MOVE, exit_)` o `(WAIT, None)`, igual que el errante. Para eso, `decide_action` tiene que recibir el `trail` o el `Exit` ya calculado. Ese cambio le corresponde a la Persona 1.

**Acordado:** en `move()`, la sala destino se marca con el reloj del **instante en que se ejecuta la acción**, no al terminar su costo. Moverse en t=0 con costo 100 marca con 0. Lo dice §2.5 ("el jugador aparece en la sala destino al ejecutar la acción") y lo confirma el ejemplo de §2.13. `PlayerTrail.mark()` recibe el instante como parámetro, así que no cambia nada en este módulo.

## 4. Historial reversible

### Lo que ya se revierte solo

Para que la agenda de eventos se revierta sola, `Game` tiene que recibir la agenda reversible:

```python
history = History(state)
game = Game(..., event_queue=ReversibleEventQueue(history))
```

`ReversibleEventQueue` anota sus propias operaciones, sin tocar `EventQueue`:

- `push`, `pop` y `cancel`;
- los eventos cancelados que el montículo descarta por dentro;
- `actor.scheduled_event`.

El reloj se guarda al abrir cada intervalo y se devuelve con `GameState.rewind_clock_to()`. El contador de secuencia no se toca, como dice `DECISIONES.md`.

Las pruebas `TestReversibleQueueWithTheEngine` verifican con el `Game` real que después de deshacer quedan iguales:

- el reloj;
- los eventos activos de la agenda;
- `scheduled_event` de cada actor.

Lo verifican para estos casos: `wait()`, dos retrocesos seguidos, un cambio de velocidad y la cancelación por muerte.

### Lo que el motor debe anotar (Persona 1)

**Abrir el intervalo.** El motor llama a `history.begin_action()` en cada acción **aceptada** del jugador, después de validarla y antes de modificar nada. Las rechazadas no lo llaman.

**Anotar cada cambio.** Todo cambio de estado de `Game` hasta la siguiente decisión del jugador se anota. Para un atributo se reemplaza la asignación:

```python
self.history.assign(target, "health", target.health - damage)   # en vez de take_damage()
self.history.assign(enemy, "room_id", chosen_exit.destination)
self.history.assign(enemy, "is_active", True)
self.history.assign(door, "closed", False)
self.history.assign(trap, "armed", False)
self.history.assign(self, "result", VICTORY)
self.history.assign(self, "torch_lit", True)
self.history.assign(self, "player_actions", self.player_actions + 1)
self.history.assign(self, "enemies_defeated", self.enemies_defeated + 1)
self.history.assign(self, "effects", nueva_lista)   # en _forget_finished_effects
self.history.assign(effect, "cancelled", True)
self.history.assign(actor, "speed", actor.speed)    # antes de change_speed()
```

Para las listas:

```python
self.history.list_append(room.floor_items, item)   # soltar, y lo que suelta un enemigo
self.history.list_pop(room.floor_items, index)     # recoger
self.history.list_append(self.effects, effect)
```

`history.assign()` funciona con propiedades: `health` sigue recortándose en su setter.

**Excepción de §2.11.** Si el objeto que se recoge o se suelta es un pergamino de retroceso, su cambio en `floor_items` **no** se anota. `Inventory` ya hace lo mismo con su lado. Se puede usar `structures.inventory.is_rewind_scroll(item)`.

**El pergamino.**

```python
def rewind(self):
    if self.is_over:
        return self._game_already_ended()
    if not use_rewind_scroll(self.player.inventory, self.history):
        return ActionResult(False, "No tienes pergaminos o no hay acciones que revertir.")
    self._log("El tiempo retrocede.")
    return ActionResult(True, "El tiempo retrocede.")
```

No consume tiempo, no llama a `begin_action()` y no suma a `player_actions`.

### Cómo probar que no se escapa ningún cambio

Un cambio sin anotar no lanza ninguna excepción: simplemente no se deshace. Para detectarlo está `tests/verificar_retroceso.py`:

```python
from tests.verificar_retroceso import assert_rewind_restores

def test_atacar_se_revierte(self):
    assert_rewind_restores(self, game, lambda: game.attack("e-201"), trail=game.trail)
```

Toma una foto de todo lo que §2.11 pide revertir, ejecuta la acción, llama a `game.rewind()` y compara. Si algo quedó distinto, la prueba falla y dice el campo exacto, por ejemplo `sala 2.trampa t-1.armada: antes True, despues del retroceso False`. También verifica que el pergamino quede consumido.

La foto existe solo dentro de la prueba y nunca se usa para restaurar nada, así que no choca con la prohibición de §2.11.

Compara:
- reloj, resultado, antorcha, `player_actions` y `enemies_defeated`;
- vida, sala, velocidad, equipo y evento pendiente del jugador y de cada enemigo, más `is_active` de los enemigos;
- puertas, trampas y suelo de cada sala;
- el orden real del inventario;
- los eventos activos de la agenda con su `time` y `sequence`;
- los efectos;
- el rastro, si se pasa `trail`.

No compara, a propósito: pergaminos, bitácora en pantalla, contador de secuencia, generador aleatorio, `events_processed` ni el cursor.

Conviene una prueba por cada acción y por cada evento que el motor procesa: esperar, atacar con y sin muerte, moverse con trampa, moverse hacia la salida, abrir con cierre automático, recoger, soltar, usar cada tipo de objeto y equipar. Con el motor de la rama `mauricio-logica-juego` sin anotar nada, el verificador ya encuentra que `wait()` deja `player_actions` en 1 después de deshacer. La agenda y el reloj sí vuelven, por `ReversibleEventQueue`.

### Decisiones tomadas en este módulo

- La bitácora en pantalla no se revierte: es presentación, no estado del juego.
- El generador aleatorio no se restaura. Así lo acordó el grupo en `ARQUITECTURA.md`.
- El cursor del inventario no se restaura, salvo al deshacer un `soltar`, donde vuelve al objeto restaurado.

### Casos que el enunciado no define

Si se recoge un pergamino después de soltar otro objeto y luego se retrocede dos veces, el inventario puede quedar con un objeto más que `inventario_max`. Esto pasa porque el pergamino no se devuelve (§2.11) y el objeto soltado sí. Falta decidir qué hacer en ese caso.

## 5. Ordenamiento

```python
from structures.sorting import sort
ordenados = sort(enemies, key=lambda enemy: enemy.actor_id)
```

Con esto se puede reemplazar `Game._by_ascending_id()`, como pide su propio docstring. Es estable y no modifica la entrada.

`SMALL_THRESHOLD` y `NEARLY_SORTED_RATIO` son provisionales y se calibran con el benchmark.

## 6. Vista (Persona 4)

`VisibleState` todavía no incluye el inventario. Para el comando `ver`:

- el objeto actual sale de `player.inventory.current()`;
- el orden real, de recorrer `player.inventory`;
- una vista ordenada, de `sorted_view(criterio)`.

Las vistas ordenadas no van al log de replay porque no cambian el estado. Así lo dice `ARQUITECTURA.md`.

## 7. Benchmark

```
python -m benchmark.persona3_bench
```

Mide:

- la bitácora, contra la alternativa descartada `list.pop(0)`;
- soltar por posición con n = 10 a 10 000, contra `list.pop(i)`;
- recorrer el inventario y sus vistas;
- los dos algoritmos y la selección automática, con datos aleatorios, casi ordenados, invertidos, rotados y con comparaciones costosas;
- el rastro con 1 a 1000 rastreadores;
- el historial con 1 a 1000 cambios por acción;
- el costo de la agenda reversible frente a `EventQueue`.

Las cifras para el Documento de Decisiones deben salir de la máquina del grupo.
