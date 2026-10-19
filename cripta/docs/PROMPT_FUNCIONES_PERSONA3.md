Estoy trabajando en el proyecto grupal "CRIPTA — Estructuras de Datos II — II Ciclo 2026": un juego de mazmorra dirigido por eventos, en Python 3.11 o superior, con arquitectura MVC. Somos cuatro integrantes y yo soy la Persona 3. Me toca:
- el inventario;
- el historial reversible con el pergamino de retroceso;
- el rastro del jugador;
- la bitácora de 20 mensajes;
- los algoritmos de ordenamiento;
- sus pruebas y sus mediciones.

El enunciado oficial es la fuente de verdad: no inventes requisitos. Si algo no está definido, dímelo antes de asumirlo y distingue entre requisito y decisión de implementación.

## Restricciones obligatorias

- No usar `dict` como índice, caché ni tabla de búsqueda. Para buscar por clave existe `structures/tabla_hash.py` (`TablaHash` con `insertar`, `obtener`, `contiene`, `eliminar`).
- No usar `sorted()` ni `list.sort()`.
- No usar `collections.deque` ni otra estructura de biblioteca en lugar de la que se evalúa.
- El retroceso no puede guardar copias completas del estado.
- El Modelo no depende de HTTP, archivos ni interfaz.
- Código simple y defendible ante el profesor:
  - identificadores en inglés y docstrings en español sin tildes;
  - un docstring de módulo que explique el problema, la estructura y la complejidad;
  - sin comentarios que expliquen lo obvio.
- No modificar archivos de otros integrantes.

## Interfaces existentes que debes usar (no las modifiques)

- `model/item.py`: `Item` es un dataclass con:
  - `instance_id`, `type_id`, `name`, `item_class`, `weight`, `value`, `attack_bonus`, `defense_bonus`;
  - las constantes `Item.WEAPON = "arma"`, `Item.ARMOR = "armadura"` e `Item.REWIND_SCROLL = "pergamino_retroceso"`.
- `model/player.py`: `Player` tiene `equipped_weapon`, `equipped_armor`, `inventory`, `effective_attack` y `effective_defense`. Los dos últimos suman `attack_bonus` y `defense_bonus` del equipo.
- `model/room.py`:
  - `Room.exits()` devuelve objetos `Exit(direction, destination, door)`;
  - `door.is_open` y `door.closed` dan el estado de la puerta;
  - los ids de sala son enteros.
- `model/game_state.py`: `GameState` tiene `clock` (solo lectura), `next_sequence()` y `rewind_clock_to(time)`.
- `model/event.py`: `Event` tiene `time`, `sequence`, `event_type`, `actor`, `cancelled` y otros campos opcionales. Las acciones de actores usan `event_type == "actor_action"`, y cada actor guarda su evento pendiente en `actor.scheduled_event`.
- `structures/event_queue.py`: `EventQueue` es un montículo binario mínimo por `(time, sequence)`, con `push`, `pop`, `peek`, `cancel(event)` (cancelación diferida), `active_events()` y el método interno `_remove_root()`, que también descarta los cancelados de la raíz.
- `benchmark/utilidades_medicion.py`: `Measurement(name, seconds, detail)`, `calentar_procesador()` y `descripcion_del_equipo()`.

## Lo que hay que implementar

### 1. `structures/circular_log.py` (§4.8)

**`CircularBuffer(capacity)`:**
- arreglo fijo, índice al más antiguo y contador;
- `append(x)` en O(1): si está lleno, sobrescribe el más antiguo y lo devuelve;
- `last()`, `pop_last()`, `clear()`, `is_empty()`, `is_full()`, `capacity`, `len()`;
- recorrido del más antiguo al más reciente;
- `ValueError` si la capacidad es menor que 1 e `IndexError` si está vacío.

**`CircularLog(capacity=20)`:**
- hereda de `CircularBuffer` y guarda los mensajes como `str`;
- debe servir como `message_log` de `Game`, que solo pide `append()` y poder recorrerla.

Requisitos: memoria constante y sin desplazar físicamente los 19 mensajes anteriores.

### 2. `structures/sorting.py` (§4.9)

**Funciones:** `insertion_sort`, `merge_sort` y `sort(data, key=identity, reverse=False, counter=None)`.
- Todas son estables, aceptan `reverse` y devuelven una lista nueva sin modificar la entrada.
- La clave se calcula una sola vez por elemento: se ordenan pares `(clave, elemento)`.
- `ComparisonCounter` cuenta comparaciones (`comparisons`) y anota en `algorithm` qué usó `sort`.

**Cómo elige `sort`:**
1. Con n ≤ `SMALL_THRESHOLD` (32), usa inserción.
2. Si no, cuenta los "descensos" en una pasada. Si superan n × `NEARLY_SORTED_RATIO` (0.05), usa mezcla.
3. Si no, intenta inserción con un tope de `shift_budget(n) = n * n.bit_length()` desplazamientos. Si lo supera, termina con mezcla sobre lo que quedó.

El tercer paso protege contra datos "rotados" como `[5, 6, 7, 8, 9, 0, 1, 2, 3, 4]`: tienen un solo descenso, pero inserción los ordena en O(n²).

**Funciones auxiliares:** `choose_algorithm(size, descents)` y `algorithm_for(data, key, reverse)`.

**Constantes:** `INSERTION`, `MERGE` e `INSERTION_THEN_MERGE`.

### 3. `structures/history.py` (§2.11, §4.6)

**Clases de cambio:**
- `Change` es la base, con `undo()`.
- `AttributeChange(target, attribute, previous)` restaura un atributo con `setattr`, así que también funciona con propiedades.
- `CallbackChange(function, *args)` ejecuta la operación inversa.

**`History(state, max_actions=5)`:**
- `begin_action()`: abre un intervalo que guarda `state.clock`. Los intervalos van en un `CircularBuffer(5)`, así que el sexto descarta el más antiguo.
- `record(change)`: anota solo si hay un intervalo abierto y no se está deshaciendo.
- `assign(target, attribute, value)`: anota el valor anterior y después asigna.
- `list_append(items, x)` y `list_pop(items, index)`: hacen la operación y anotan su inversa.
- `undo()`: saca el último intervalo, aplica sus cambios en orden inverso y devuelve el reloj con `state.rewind_clock_to()`. Mientras deshace no anota nada. Devuelve `False` si no hay intervalos.
- También: `can_undo()`, `available_actions()`, `is_recording`, `is_undoing`, `recorded_changes()` y `clear()` (para cuando se carga una partida).
- No restaura el contador de secuencia ni el generador aleatorio.

**`ReversibleEventQueue(history)`**, subclase de `EventQueue` que anota sola la inversa de cada operación:

| Operación | Inversa anotada |
| --- | --- |
| `push(e)` | marcar `e` como cancelado y limpiar `scheduled_event` si apuntaba a `e` |
| `_remove_root()` (pop y descartes internos) | reinsertar `e` con su mismo `time` y `sequence`, y restaurar `actor.scheduled_event` si es una acción de actor no cancelada |
| `cancel(e)` | restaurar `e.cancelled` y `actor.scheduled_event` |

**`use_rewind_scroll(inventory, history)`:**
- si no hay pergamino o no hay nada que deshacer, devuelve `False` sin tocar nada;
- si no, primero deshace y después consume el pergamino, para que el consumo quede fuera del intervalo revertido.

### 4. `structures/inventory.py` (§2.7, §4.5)

**`DoublyLinkedList`:**
- lista doble con dos nodos centinela;
- nodos `_Node(item)` con `previous`, `next` y `linked`;
- operaciones: `append`, `push_front`, `insert_after`, `insert_before`, `remove`, `move_to_front`, `first`, `next_of`, `previous_of` y `nodes()`;
- recorrido en los dos sentidos;
- `ValueError` si se quita un nodo que no está en la lista o se inserta uno que ya está.

**`Inventory(capacity, history=None)`:**
- Recorrerlo devuelve los `Item` en el orden real, porque el motor busca llaves recorriendo `player.inventory`.
- `is_full()`; `pick_up(item)` agrega al final, deja el cursor sobre el objeto recogido y devuelve `False` si está lleno, sin mover el cursor.
- `current()`, `next()`, `previous()` y `go_to_start()`: el cursor es una referencia al nodo actual.
- `drop_current(player)`, en O(1) en cualquier posición:
  - devuelve el objeto quitado;
  - si estaba equipado, lo desequipa en `player`;
  - el cursor pasa al siguiente, o al anterior si se soltó el último.
- `can_equip_current()` y `equip_current(player)`:
  - mueve el objeto al frente;
  - actualiza `player.equipped_weapon` o `player.equipped_armor`;
  - devuelve el objeto sustituido, que queda en el inventario, o `None`;
  - lanza `ValueError` si no es arma ni armadura.
- `sorted_view("peso" | "valor" | "nombre", reverse=False)`: copia ordenada con `sort()`, sin alterar el orden real. El nombre se compara en minúsculas.
- `scroll_count()` y `consume_scroll()`. Los pergaminos ocupan espacio.

**Con `history`:**
- Cada cambio anota su inversa.
- Al deshacer un `soltar` o un `equipar`, el nodo vuelve a su posición junto a sus vecinos de antes. Si el vecino anterior ya no está, usa el siguiente, y si tampoco está, va al final. Al deshacer un soltar, el cursor vuelve al objeto restaurado.
- El equipo se cambia con `history.assign`.
- Los movimientos de pergaminos de retroceso **no** se anotan (§2.11).

### 5. `structures/trail.py` (§2.9, §4.7)

**`PlayerTrail(history=None)`:** guarda id de sala → instante en una `TablaHash`. `TRAIL_LIFETIME = 400`.
- `mark(room_id, time)`: si hay historial, anota el valor anterior, o que la sala no tenía entrada.
- `time_at(room_id)` e `is_fresh(room_id, now)`, con la condición `now - time < 400`.
- `freshest_exit(room, now)`:
  - recorre `room.exits()` e ignora las puertas cerradas y los rastros caducados;
  - devuelve el `Exit` con el instante más alto, o el de menor id de sala si hay empate;
  - devuelve `None` si no hay ninguno.

La caducidad se detecta al consultar; no se eliminan rastros. El costo es O(salidas). El motor marca la sala con el reloj del instante en que se ejecuta cada acción aceptada, y también al iniciar la partida.

## Pruebas (`unittest`, desde `cripta/` con `python -m unittest discover -s tests -t .`)

Para cada módulo, cubre:
- casos normales;
- vacíos;
- límites, como capacidad exacta, 20 y 21 mensajes, frescura en 399 y en 400, n = 32 y 33;
- errores;
- el máximo de 5 retrocesos.

Además, estos casos del Apéndice B y de §2.11:
- recoger con el inventario lleno;
- empate de rastros, que gana la sala de menor id;
- recoger o soltar un pergamino dentro del intervalo revertido;
- dos pergaminos seguidos;
- el ejemplo del enunciado: ataque en t=100, veneno, ataque de la rata, rearme de una trampa y pergamino en t=200. Después del retroceso deben volver la vida de los dos, la trampa, el reloj y el rastro.

Para el ordenamiento, prueba también:
- estabilidad, incluso después de cambiar de inserción a mezcla;
- que datos rotados de 2048 elementos terminen con `INSERTION_THEN_MERGE`;
- que los casi ordenados se queden con inserción.

Incluye además `tests/verificar_retroceso.py`, un ayudante solo para pruebas:
- `snapshot(game, trail)` devuelve una lista de pares (campo, valor) con el reloj, el resultado, la antorcha, los contadores, la vida, sala, velocidad, equipo y evento pendiente de cada actor, puertas, trampas y suelo de cada sala, orden real del inventario, eventos activos de la agenda y efectos;
- deja fuera los pergaminos, la bitácora, el contador de secuencia y el cursor;
- `differences(antes, despues)` devuelve los campos que cambiaron;
- `assert_rewind_restores(testcase, game, action, trail)` falla nombrando el campo exacto que no se restauró.

## Mediciones (`benchmark/persona3_bench.py`, función `run()` que devuelve `Measurement`)

Mide estas operaciones, incluyendo siempre la alternativa descartada:
- la bitácora frente a `list` + `pop(0)`;
- soltar al inicio, en medio y al final con n = 10, 100, 1000 y 10 000, frente a `list.pop(i)`;
- recorrer el inventario y las vistas ordenadas;
- los tres ordenamientos con datos aleatorios, casi ordenados (1 % de intercambios), invertidos, rotados y cadenas largas con prefijo común, para n de 4 a 4096, reportando comparaciones y qué usó `sort`;
- el rastro con 1, 10, 100 y 1000 rastreadores;
- el historial con 1, 10, 100 y 1000 cambios por acción;
- `ReversibleEventQueue` frente a `EventQueue` (300 eventos, 20 000 extracciones).

Agrega también:
- `benchmark/persona3_frecuencias.py`: cuenta cuántas veces se ejecuta cada operación por decisión del jugador, con el motor real y versiones con contadores del historial, el rastro y la bitácora;
- `benchmark/persona3_corridas.py`: corre todo 3 veces y guarda las corridas y las medianas en `docs/mediciones/persona3/`.

**No inventes cifras.** Reporta lo que salga, aunque la alternativa descartada resulte más rápida a tamaños pequeños; en ese caso, la justificación es el requisito.

## Cómo trabajar

Ve por etapas: análisis, diseño, interfaces, implementación, pruebas, integración, benchmark y documentación. Empieza con el análisis y el diseño de cada estructura:
- qué problema resuelve;
- qué operaciones necesita;
- al menos dos alternativas y por qué se descartan;
- complejidad temporal y espacial;
- qué medición lo demostraría.

Explícame en palabras sencillas lo que sea complicado y espera mi confirmación antes de generar el código completo. Todo lo que generes es una propuesta que yo voy a revisar y que debo poder defender ante el profesor.
