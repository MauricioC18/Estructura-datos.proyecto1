# Arquitectura del proyecto CRIPTA

## 1. Objetivo

El objetivo de este documento es definir la organización inicial del proyecto, las responsabilidades de sus módulos y la forma en que se comunicarán entre sí.

La arquitectura se basa en el enunciado oficial del proyecto CRIPTA de Estructuras de Datos II, II Ciclo 2026.

Las interfaces y decisiones que todavía no se hayan confirmado por el grupo se consideran provisionales y deberán revisarse antes de implementar módulos que dependan de ellas.

## 2. Organización del proyecto

```text
cripta/
├── main.py
├── model/
│   ├── game.py
│   ├── game_state.py
│   ├── actor.py
│   ├── player.py
│   ├── enemy.py
│   ├── room.py
│   └── effects.py
├── structures/
│   ├── event_queue.py
│   ├── inventory.py
│   ├── cache.py
│   ├── history.py
│   ├── trail.py
│   ├── circular_log.py
│   └── sorting.py
├── adapters/
│   ├── data_source.py
│   ├── http_source.py
│   ├── offline_source.py
│   └── persistence.py
├── controller/
│   └── game_controller.py
├── view/
│   └── console_view.py
├── replay/
│   └── replay.py
├── benchmark/
│   └── benchmark.py
├── tests/
├── docs/
│   ├── ARQUITECTURA.md
│   ├── DECISIONES.md
│   └── proyecto_cripta.md
├── PROMPTS_LLM.md
├── README.md
└── requirements.txt
```

El archivo `.gitignore` se mantiene en la raíz del repositorio, un nivel por encima de `cripta/`, porque también debe cubrir los archivos de configuración de los editores.

`docs/proyecto_cripta.md` es el enunciado oficial del proyecto y es la referencia para resolver cualquier duda sobre las reglas del juego.

La estructura puede ampliarse si resulta necesario, pero los cambios deben comunicarse al grupo para evitar duplicaciones y conflictos.

## 3. Responsabilidades de los módulos

### Model

Contiene las reglas y el estado del juego. No debe depender directamente de solicitudes HTTP, archivos concretos ni de la interfaz.

* `game.py`: coordina el funcionamiento del motor, las acciones y el procesamiento de eventos.
* `game_state.py`: mantiene el estado actual de la partida y el reloj virtual.
* `actor.py`: define los atributos y comportamientos comunes de los actores.
* `player.py`: contiene el comportamiento y los datos específicos del jugador.
* `enemy.py`: contiene los comportamientos y características de los enemigos.
* `room.py`: representa las salas, sus conexiones y los elementos que contienen.
* `effects.py`: representa los efectos temporales y sus reglas.

### Structures

Contiene las estructuras de datos implementadas para resolver los requisitos del proyecto.

* `event_queue.py`: agenda y administra los eventos del juego.
* `inventory.py`: administra el inventario y sus operaciones.
* `cache.py`: administra la caché y su política de desalojo.
* `history.py`: registra los cambios necesarios para revertir acciones.
* `trail.py`: administra el rastro del jugador.
* `circular_log.py`: conserva los últimos 20 mensajes.
* `sorting.py`: contiene los algoritmos de ordenamiento evaluados.

Cada estructura debe respetar las restricciones del enunciado y justificar sus decisiones mediante complejidad y mediciones cuando corresponda.

### Adapters

Permite obtener y almacenar datos sin acoplar el modelo a una implementación concreta.

* `data_source.py`: define la interfaz común para consultar los datos.
* `http_source.py`: implementa el acceso a la API.
* `offline_source.py`: proporciona una fuente alternativa para el funcionamiento sin conexión.
* `persistence.py`: administra el almacenamiento persistente que le corresponda según los acuerdos del grupo.

El modelo debe utilizar interfaces comunes en lugar de depender directamente de HTTP o de archivos específicos.

### Controller

* `game_controller.py`: recibe las acciones solicitadas por el usuario y las transforma en operaciones del modelo.

### View

* `console_view.py`: presenta el estado del juego y permite interactuar mediante la consola.

La vista no debe implementar las reglas del juego ni modificar directamente las estructuras internas del modelo.

### Replay

* `replay.py`: reproduce una partida a partir de un registro de acciones y verifica la compatibilidad de los datos necesarios.

### Benchmark

* `benchmark.py`: ejecuta las mediciones requeridas para evaluar las estructuras y operaciones del proyecto.

### Main

* `main.py`: es el punto de entrada del programa. Interpreta las opciones de ejecución y conecta los componentes necesarios, sin concentrar las reglas del juego en este archivo.

## 4. Distribución de responsabilidades

| Integrante | Responsabilidad principal                                                      |
| ---------- | ------------------------------------------------------------------------------ |
| Persona 1  | Motor del juego, agenda de eventos, reloj virtual, actores, combate y enemigos |
| Persona 2  | API, fuentes de datos, precarga, catálogo, caché y persistencia relacionada    |
| Persona 3  | Inventario, historial reversible, rewind, rastro, bitácora y ordenamientos     |
| Persona 4  | MVC, interfaz, replay, benchmark e integración                                 |

La distribución identifica responsables principales, pero no significa que cada módulo se desarrollará de forma aislada. Las interfaces compartidas deben acordarse entre todos.

Cada integrante es responsable de implementar y probar su parte, documentar sus decisiones y colaborar en la integración.

## 5. Comunicación entre módulos

El flujo general previsto es:

1. `main.py` configura el modo de ejecución.
2. El controlador recibe la acción solicitada por el usuario.
3. El modelo valida la acción y aplica las reglas correspondientes.
4. La agenda de eventos determina qué evento debe procesarse a continuación.
5. El modelo actualiza el estado de la partida.
6. La vista muestra el resultado.

La fuente de datos proporciona la información necesaria al modelo mediante una interfaz. La implementación concreta puede utilizar la API o funcionar sin conexión.

El sistema de replay debe poder reproducir acciones sin requerir interacción del usuario. El benchmark debe poder ejecutarse sin depender de la interfaz interactiva.

## 6. Agenda de eventos y reloj virtual

La agenda de eventos debe seleccionar el siguiente evento según estos criterios:

1. Menor tiempo de ejecución.
2. Menor número de secuencia cuando dos eventos tengan el mismo tiempo.

El número de secuencia permite resolver los empates de manera determinista.

Las acciones y eventos deben respetar los costos, intervalos y reglas temporales definidos en el enunciado.

Cuando una acción modifica la velocidad de un actor, su próximo evento debe reprogramarse respetando las reglas de tiempo restantes y asignando un nuevo número de secuencia cuando corresponda.

La estructura elegida para la agenda debe permitir seleccionar el siguiente evento eficientemente, sin recorrer todos los eventos en cada selección.

### Interfaz de `EventQueue` (implementada)

La agenda es un montículo binario mínimo. La justificación completa está en el Documento de Decisiones, sección 4.1.

| Operación | Devuelve | Comportamiento |
| --- | --- | --- |
| `push(event)` | — | agrega un evento |
| `peek()` | `Event` o `None` | siguiente evento activo, sin retirarlo |
| `pop()` | `Event` o `None` | retira y devuelve el siguiente evento activo |
| `cancel(event)` | — | marca el evento como cancelado |
| `active_events()` | `list` | eventos no cancelados, para guardar la agenda en disco |
| `is_empty()` | `bool` | `True` si no queda ningún evento activo |
| `len(queue)` | `int` | eventos almacenados, incluidos los cancelados aún no descartados |

### Interfaz de `Event` (implementada)

| Campo | Para qué |
| --- | --- |
| `time`, `sequence` | prioridad en la agenda |
| `event_type` | tipo que el motor interpreta |
| `actor`, `target` | **referencias al objeto `Actor`**, no identificadores |
| `amount` | daño del veneno, cantidad de regeneración, modificador de velocidad |
| `room_id`, `direction` | cierre automático de una puerta |
| `room_id`, `instance_id` | rearme de una trampa |
| `cancelled` | marca de cancelación diferida |

`Event` guarda la **referencia** al actor y no su identificador, porque el motor necesita el actor cada vez que procesa un evento y buscarlo por identificador costaría O(n) por evento. El identificador sigue disponible como `event.actor.actor_id`, que es lo que se escribe al serializar. Al cargar una partida hay que resolver cada identificador contra la lista de actores, pero eso ocurre una sola vez y no en el bucle principal.

La clase es plana, con campos opcionales, en lugar de usar subclases por tipo de evento o un objeto de datos anidado. La razón es que el guardado binario de §4.10 empaqueta registros de forma fija con `struct`, y una clase plana se empaqueta directamente; una jerarquía obligaría a inventar un formato con etiqueta de tipo.

Acuerdos que esta interfaz impone al resto del modelo:

* La cancelación se hace **por referencia al objeto `Event`**, no por identificador. Quien programa un evento debe conservar esa referencia: cada actor guarda la referencia a su acción pendiente y cada efecto temporal a su próximo pulso. Así cancelar al morir un actor o al aplicar un antídoto cuesta O(1) y no requiere recorrer los eventos pendientes.
* **Nunca debe modificarse el `time` ni el `sequence` de un evento que ya está en la agenda**, porque rompería la propiedad de orden del montículo. Una reprogramación por cambio de velocidad (§2.3 del enunciado) se hace cancelando el evento anterior e insertando uno nuevo con un número de secuencia nuevo.
* Los identificadores de `Event` son de tipo texto, porque el servicio entrega los ids de instancia en ese formato (`"e-201"`, `"t-17"`). Los ids de sala sí son enteros.

### Interfaz de `GameState` (implementada)

Mantiene el estado temporal de la partida. La justificación está en el Documento de Decisiones, sección "Reloj virtual y numeración de eventos".

| Miembro | Devuelve | Comportamiento |
| --- | --- | --- |
| `clock` | `int` | reloj virtual, de solo lectura |
| `next_sequence()` | `int` | siguiente número de secuencia; única fuente de la partida |
| `sequence_counter` | `int` | número que recibirá el próximo evento, para guardarlo en disco |
| `random_state()` | tupla | estado interno del generador, para guardarlo en disco |
| `restore(clock, sequence_counter, random_state)` | — | devuelve el estado temporal al guardado en un archivo de partida |
| `advance_clock_to(time)` | — | mueve el reloj; acepta el mismo instante y rechaza retroceder |
| `rewind_clock_to(time)` | — | devuelve el reloj a un instante anterior; rechaza adelantar |
| `random_generator` | `random.Random` | generador de azar del modelo, creado con la semilla |
| `seed` | — | semilla de la partida, para el guardado y la cabecera del replay |

Acuerdos que esta interfaz impone al resto del proyecto:

* `next_sequence()` es la **única** fuente de números de secuencia. Ningún módulo debe mantener su propio contador, porque el desempate de eventos dejaría de ser un orden total.
* `rewind_clock_to()` lo usa exclusivamente el pergamino de retroceso. No calcula el instante de destino: lo recibe del historial reversible.
* El historial reversible (`structures/history.py`) debe registrar el valor del reloj de cada acción del jugador, pero **no** el contador de secuencia. Sí debe registrar el `time` y el `sequence` de cada evento afectado.
* Todo el azar del modelo pasa por `random_generator`. No se usa el generador global del módulo `random`.
* `restore()` es para **cargar una partida guardada**, no para el pergamino de retroceso. Son dos casos distintos: el retroceso devuelve el reloj pero no necesita el contador de secuencia ni el estado del generador, mientras que cargar una partida debe continuar exactamente donde se quedó y sí los necesita. Quien implemente el guardado de §4.10 debe persistir los tres valores junto con los eventos activos de la agenda.

### Interfaz de `Actor` (implementada)

Atributos y comportamiento comunes del jugador y de los enemigos. `Player` y `Enemy` heredarán de esta clase.

| Miembro | Devuelve | Comportamiento |
| --- | --- | --- |
| `actor_id`, `name`, `room_id` | — | identificación y sala actual |
| `health` | `int` | vida; el setter recorta siempre al rango `[0, max_health]` |
| `max_health`, `attack`, `defense` | `int` | estadísticas |
| `speed` | `int` | velocidad; el setter rechaza valores menores o iguales a cero |
| `is_alive` | `bool` | `True` mientras la vida sea mayor que cero |
| `scheduled_event` | `Event` o `None` | referencia al evento pendiente del actor |
| `interval_for(cost)` | `int` | `max(1, cost * 100 // speed)` |
| `next_time_after(current_time, cost)` | `int` | `current_time` más el intervalo |
| `change_speed(current_time, new_speed)` | `int` o `None` | cambia la velocidad y devuelve el instante reprogramado |
| `take_damage(amount)`, `heal(amount)` | — | modifican la vida respetando el recorte del setter |

Acuerdos que esta interfaz impone al resto del modelo:

* La tabla de costos de las acciones **no** vive en `Actor`. Es una propiedad de cada acción y la administra el motor; `Actor` solo convierte un costo en un intervalo según su velocidad.
* `change_speed()` **no** modifica el evento pendiente ni la agenda. Devuelve el instante nuevo, y el motor debe cancelar el evento anterior e insertar uno nuevo con un número de secuencia nuevo.
* El motor es responsable de mantener `scheduled_event` al día cada vez que programa o cancela la acción de un actor. De esa referencia depende poder cancelar en O(1) los eventos de un actor muerto.
* La vida nunca necesita recortarse desde fuera: cualquier asignación a `health` ya queda dentro del rango válido.

### Interfaz de `Game` (implementada en parte)

**Lo que ya funciona:** `wait()`, `attack(enemy_id)`, `visible_state()`, `change_actor_speed(actor, new_speed)` y el bucle de eventos completo, con el combate de §2.6 y el azar reproducible. El resto de los métodos de la tabla siguen pendientes de las salas y del inventario.

`Game` se construye con un `GameState`, el `Player` y la lista de enemigos, y ya dentro del constructor programa la primera acción del jugador en el instante 0, activa los enemigos de la sala inicial según §2.4 y deja la partida esperando la primera decisión.

`GameState` guarda el estado temporal —reloj, contador de secuencia y generador aleatorio—, que es lo que hay que persistir para reanudar una partida. `Game` guarda los actores, la agenda y el resultado.


`model/game.py` es el único punto por el que el controlador habla con el modelo. La vista nunca toca las estructuras internas.

**Cada llamada a una acción hace dos cosas:** ejecuta la acción del jugador y después procesa todos los eventos pendientes hasta que vuelva a tocarle decidir al jugador. El controlador no administra el reloj ni la agenda. Esto corresponde al "ciclo completo de eventos entre dos decisiones consecutivas del jugador" que §5.2 del enunciado exige resolver en menos de 20 ms.

| Método | Costo | Depende de |
| --- | --- | --- |
| `wait()` | 100 | nada |
| `attack(enemy_id)` | 100 | nada |
| `move(direction)` | 100 | salas |
| `open_door(direction)` | 50 | salas |
| `pick_up(floor_index)` | 25 | inventario |
| `drop()` | 25 | inventario |
| `use_item()` | 50 | inventario |
| `equip_item()` | 50 | inventario |
| `inventory_next()`, `inventory_previous()` | 0 | inventario |
| `rewind()` | 0 | historial reversible |

`drop()`, `use_item()` y `equip_item()` actúan sobre el objeto que el cursor del inventario está mostrando, porque §4.5 pide poder soltar el objeto que se está viendo. Por eso no reciben índice y por eso la navegación del inventario es parte de la interfaz.

`rewind()` no consume tiempo virtual y no cuenta como acción del jugador (§2.11).

**Resultado de una acción.** Toda acción devuelve un `ActionResult` con `accepted` y `message`. Una acción rechazada no consume tiempo virtual, no modifica el estado y no consulta el generador aleatorio. Los casos de rechazo están en el Apéndice B del enunciado: recoger con el inventario lleno, abrir una puerta sin la llave correcta, moverse hacia una salida que no existe o está cerrada, atacar a un enemigo que no está en la sala.

**Estado visible.** `visible_state()` devuelve una vista de solo lectura con lo que §10.2 exige mostrar: sala actual, salidas y su estado, enemigos con su id de instancia, objetos del suelo, estadísticas del jugador, efectos activos, resultado de la partida y los últimos 20 mensajes.

Se devuelve como una clase `@dataclass`, no como un `dict`. No es que un `dict` de presentación incumpla §7, que prohíbe usarlo como índice o tabla de búsqueda, pero una clase con campos nombrados evita tener que explicarlo en la defensa y sigue el estilo de los ejemplos del curso.

**Estado visible, campos actuales.** `VisibleState` trae por ahora `clock`, `result`, `player_name`, `health`, `max_health`, `attack`, `defense`, `speed`, `room_id`, `enemies` y `messages`. Cada enemigo se entrega como un `EnemyView` con `actor_id`, `name`, `health` y `max_health`, y solo aparecen los que están vivos en la sala del jugador. Faltan las salidas, los objetos del suelo y los efectos activos, que dependen de las salas y del inventario.

`messages` es hoy una `list` que crece sin límite. §4.8 exige memoria constante y que agregar un mensaje no desplace los 19 anteriores, de modo que debe sustituirse por `structures/circular_log.py` cuando exista.

### Interfaces de `Player` y `Enemy` (implementadas)

Ambas heredan de `Actor`.

`Player` agrega `equipped_weapon`, `equipped_armor` e `inventory`, y sobrescribe `effective_attack` y `effective_defense` sumando los bonos del equipo (§2.7). El arma y la armadura se tratan por duck typing: basta con que el objeto tenga `attack_bonus` o `defense_bonus`, así que el catálogo puede entregar lo que quiera mientras respete esos nombres. `inventory` se asigna desde fuera, para que la estructura de inventario encaje sin modificar `Player`.

`Enemy` agrega `behavior`, `drops`, `regeneration` e `is_active`, y expone `decide_action(player)`, que devuelve `Enemy.ATTACK` o `Enemy.WAIT` según §2.8. Compartir sala con el jugador tiene prioridad sobre el comportamiento. El guardián está completo; el errante y el rastreador esperan hasta que existan las salas y el rastro.

Los valores de `behavior` son los que entrega el catálogo. El enunciado solo confirma `"rastreador"` en su ejemplo, así que los nombres del guardián y del errante deben verificarse contra el servicio real antes de confiar en ellos.

### Qué registra la bitácora de reproducción

| Pregunta | Respuesta | Fundamento |
| --- | --- | --- |
| ¿Se registra el uso del pergamino? | Sí | §2.11 dice que no se registra "como acción del jugador **en el historial**", y ahí historial es el historial reversible de §4.6, no la bitácora de §4.11. Si la bitácora no lo registrara, reproducirla no daría la misma partida, y §4.11 exige reproducción fiel |
| ¿Se registra la navegación del inventario? | Sí | `drop()`, `use_item()` y `equip_item()` actúan sobre el objeto que muestra el cursor, así que sin la navegación la reproducción elegiría otro objeto. Las vistas ordenadas de §4.5 no se registran, porque no alteran el orden real ni el estado |
| ¿Se registran las acciones rechazadas? | No | No consumen tiempo, no cambian el estado y no consultan el generador aleatorio, de modo que omitirlas no cambia la partida reproducida |
| ¿El retroceso restaura el estado del generador aleatorio? | No | Ver el apartado correspondiente del Documento de Decisiones. §2.6 exige que misma semilla y misma secuencia de acciones den la misma partida, y el uso del pergamino forma parte de esa secuencia, así que la reproducción sigue siendo fiel. Guardar el estado interno del generador en cada intervalo se acercaría a una copia de estado, que §2.11 prohíbe |
| ¿Cómo se despachan los comandos sin `dict`? | Con `if`/`elif` | Es la opción que no hay que justificar en la defensa |

**Importante: cargar una partida guardada es un caso distinto del retroceso.** Para continuar exactamente donde se quedó, el archivo de guardado sí debe conservar y restaurar el contador de secuencia y el estado del generador aleatorio, además de los eventos pendientes de la agenda. Que el retroceso no los necesite no significa que el guardado tampoco.

## 7. Reglas de implementación

* No utilizar `dict` como índice, caché o tabla de búsqueda para resolver los problemas evaluados.
* No utilizar `sorted()` ni `list.sort()` en los algoritmos de ordenamiento evaluados.
* No utilizar copias completas del estado para implementar el rewind.
* Mantener las reglas del juego separadas de la interfaz y del acceso a datos.
* No introducir dependencias entre módulos sin comunicarlas al grupo.
* No inventar mediciones de rendimiento: deben obtenerse mediante pruebas reales.
* Registrar los prompts utilizados con herramientas de IA en `PROMPTS_LLM.md`, según las instrucciones del proyecto.
* Mantener el código claro y evitar comentarios que no aporten información necesaria.

## 8. Pruebas

Cada módulo debe contar con pruebas para sus operaciones principales.

Se deben considerar:

* Casos normales.
* Estructuras vacías.
* Límites de capacidad.
* Empates y orden de ejecución.
* Errores y entradas inválidas.
* Casos especiales definidos en el enunciado.
* Integración con otros módulos.

Las pruebas de integración deben comprobar que los módulos se comunican correctamente y respetan las reglas del juego.

## 9. Decisiones pendientes

Las siguientes decisiones deben confirmarse entre los integrantes antes de implementar módulos que dependan de ellas:

* Interfaces definitivas del modelo.
* Representación de salas, conexiones y contenido.
* Forma de notificar los cambios de estado.
* Estructura interna de la caché.
* Formato y responsabilidades del almacenamiento persistente.
* Información exacta que debe registrar el historial reversible.
* Formato del registro de replay.
* Convenciones de nombres y manejo de errores.

Cada decisión importante debe justificarse en el Documento de Decisiones, incluyendo alternativas, complejidad y evidencia experimental cuando corresponda.

## 10. Mantenimiento de la arquitectura

Este documento debe actualizarse cuando el grupo acuerde cambios relevantes en las interfaces o responsabilidades.

Antes de modificar una interfaz utilizada por otro módulo, se debe comunicar el cambio y coordinar su integración.
