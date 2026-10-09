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
| `is_empty()` | `bool` | `True` si no queda ningún evento activo |
| `len(queue)` | `int` | eventos almacenados, incluidos los cancelados aún no descartados |

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
| `advance_clock_to(time)` | — | mueve el reloj; acepta el mismo instante y rechaza retroceder |
| `rewind_clock_to(time)` | — | devuelve el reloj a un instante anterior; rechaza adelantar |
| `random_generator` | `random.Random` | generador de azar del modelo, creado con la semilla |
| `seed` | — | semilla de la partida, para el guardado y la cabecera del replay |

Acuerdos que esta interfaz impone al resto del proyecto:

* `next_sequence()` es la **única** fuente de números de secuencia. Ningún módulo debe mantener su propio contador, porque el desempate de eventos dejaría de ser un orden total.
* `rewind_clock_to()` lo usa exclusivamente el pergamino de retroceso. No calcula el instante de destino: lo recibe del historial reversible.
* El historial reversible (`structures/history.py`) debe registrar el valor del reloj de cada acción del jugador, pero **no** el contador de secuencia. Sí debe registrar el `time` y el `sequence` de cada evento afectado.
* Todo el azar del modelo pasa por `random_generator`. No se usa el generador global del módulo `random`.

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
