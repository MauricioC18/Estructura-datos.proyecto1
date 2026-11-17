# Plan de implementación: Niebla de guerra y viaje automático «ir a»

**Carpeta**: `specs/003-niebla-ir-a` | **Rama**: `Parte_2-niebla-ir-a` | **Fecha**: 2026-11-16 | **Especificación**: [spec.md](./spec.md)

**Artefactos asociados**: [research.md](./research.md) · [data-model.md](./data-model.md) · [contracts/](./contracts/) · [quickstart.md](./quickstart.md)

## Resumen

La capacidad tiene dos partes que comparten un mismo dato: **lo que el jugador sabe del mapa**.

1. **El mapa conocido** es estado del juego. Lo frecuente es preguntarle cosas: en qué estado está una sala y qué recuerda el jugador de una puerta (§5.3). Lo raro es modificarlo: solo cambia cuando el jugador entra a una sala o cuando una puerta cambia con él presente. Por eso se diseña para consultas O(1) promedio y para que cada cambio deje una anotación barata de deshacer, igual que el rastro del jugador.
2. **«ir a»** es una búsqueda de costo mínimo sobre ese mapa conocido. **Reutiliza la búsqueda que ya escribió el cazador** (`structures/rutas_mas_baratas.py`), pasándole un proveedor de vecinas que solo ve salas exploradas y puertas que el jugador recuerda abiertas. No se escribe ninguna búsqueda nueva.

La decisión central del plan es **qué se guarda y qué se deduce**:

- Se **guarda**: qué salas exploró el jugador y qué recuerda de cada puerta que observó. Es lo único que no se puede reconstruir a partir del esqueleto.
- Se **deduce**: el nombre, las salidas y el costo de las salidas de una sala explorada. No cambian durante la partida y el jugador ya los conoce por estar explorada (FR-005), así que se leen del mapa de salas en el momento de mostrarlos. Si se copiaran, explorar costaría más y habría dos fuentes del mismo dato.
- Se **mantiene al día de forma incremental**: cuántas salidas de salas exploradas llevan a cada sala. Con eso, «¿está avistada?» es una consulta O(1) y explorar cuesta en proporción a lo revelado (FR-034).

## Contexto técnico

**Lenguaje**: Python 3.11 o superior. Las 945 pruebas actuales pasan; se corrieron sobre 3.11.3.

**Dependencias nuevas**: ninguna.

**Estructuras**: se reutilizan la `TablaHash` del grupo, el patrón de anotaciones inversas del historial reversible (`structures/history.py`) y la búsqueda de costo mínimo del cazador, que a su vez usa el montículo de la agenda de eventos. Se agrega **una** estructura nueva, el mapa conocido, que se arma enteramente con `TablaHash` y una `list` usada como pila. Ver «Alternativas consideradas».

**Persistencia**: el conocimiento entra en el archivo de partida. Este plan define **qué** se exporta y se importa (dos listas planas); el formato binario y la subida de versión son de Carlos y se coordinan con la línea de tiempo de Erick, que también cambia el formato.

**Pruebas**: `unittest`, desde `cripta/` con `python -m unittest discover -s tests -t .`.

**Rendimiento**: un paso de «ir a» debe calcularse en 5 ms o menos con el mapa conocido completo (FR-036). Según la aclaración del 2026-11-16, mientras no exista la cripta de referencia se mide sobre la cripta publicada más grande y sobre criptas sintéticas de al menos ese tamaño. **El tamaño de la cripta publicada más grande todavía no se conoce en este repositorio**: el paquete sin conexión solo trae `cripta-01`, de 6 salas. Hay que obtenerlo antes de fijar los tamaños de la medición; no se inventa.

**Alcance**: una estructura nueva, ganchos en el motor, el comando de mapa, el viaje en el controlador, la bitácora de reproducción, la vista, el guardado y el banco de mediciones.

## Revisión contra la constitución

| Principio | Cómo lo cumple este plan |
| --- | --- |
| I. Estructuras propias, sin dependencias prohibidas | Las salas exploradas, los contadores de avistamiento y las puertas recordadas van en `TablaHash`, no en estructuras de la biblioteca estándar usadas como índice. El orden de exploración va en una `list` usada como pila contigua, que P1 §7 permite. La búsqueda de «ir a» reutiliza la del cazador y su montículo propio. No entra ninguna biblioteca de colas, grafos ni rutas. **Las claves de puerta son `int`**, porque `TablaHash` solo admite `int` y `str` (`structures/funciones_hash.py`) |
| II. Determinismo | El mapa conocido no usa azar. Cambia solo por acciones del jugador y por eventos de la agenda, que ya son deterministas. El recorrido de las salas exploradas usa el orden de exploración, que es una pila, y no el orden interno de la tabla. La búsqueda de «ir a» tiene el desempate de FR-024 aplicado aparte, igual que el cazador |
| III. Separación MVC | El mapa conocido vive en `structures/` y el modelo lo recibe desde afuera, igual que el rastro. Las reglas del viaje (siguiente paso, motivos de parada) viven en el modelo. El controlador solo orquesta los pasos, porque es el único que puede cargar contenido de salas. La vista recibe objetos de presentación y no toca el modelo. `--replay` sigue sin instanciar la vista |
| IV. Ningún dato de una cripta en el código | No se escribe ningún identificador de sala. La sala inicial sale de los datos de la cripta. Las criptas de medición son sintéticas y deterministas por semilla |
| V. Presupuesto de solicitudes | **No se agrega ninguna solicitud.** La antorcha revela nombre y salidas, que ya están en el esqueleto; no revela contenido (FR-010), así que no obliga a descargar nada. Un paso de «ir a» carga la sala destino por el mismo camino que un movimiento escrito a mano, con el mismo presupuesto |
| VI. Rendimiento respaldado con medición | Cada decisión de estructura tiene su alternativa descartada **medida** en `--bench`. Ver «Mediciones previstas» |
| VII. Especificación antes del código | La especificación se confirmó en `82bb5c3`, antes de este plan y antes de cualquier código |

**Resultado: pasa**, sin excepciones que justificar.

**Dónde habría sido fácil equivocarse.** Para «las salas exploradas» lo natural en Python es un conjunto, que §6.2 prohíbe en las mismas condiciones que `dict`. El plan usa `TablaHash` con valor `True`, igual que las «salas asentadas» de `rutas_mas_baratas.py`. Y para la clave de una puerta lo natural sería una tupla, que `TablaHash` no admite; se usa un entero (alternativa 4).

## Alternativas consideradas

Cada decisión tiene al menos dos alternativas y el motivo concreto del descarte. El detalle de la investigación está en [research.md](./research.md).

### 1. Dónde vive el conocimiento

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Una estructura propia, separada del mapa de salas** | Separa «lo que es» de «lo que el jugador sabe», que es literalmente lo que pide §3.3. Se exporta, se copia y se revierte sin tocar las salas. Copiarla para un punto de control cuesta lo que mide el conocimiento, no la cripta | Una búsqueda más por consulta, O(1) promedio | **Elegida** |
| Un atributo «explorada» en cada sala y otro «recordada» en cada puerta | Consulta directa, sin tabla | Mezcla el mapa real con el conocimiento, que §3.3 pide separar. Cambia el bloque de sala y de puerta del archivo de partida, que es de Carlos. Copiar el conocimiento para un punto de control obligaría a recorrer **todas** las salas de la cripta | Descartada |

### 2. Cómo se responde «¿está explorada?»

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **`TablaHash` con clave el id de sala** | O(1) promedio, independiente del tamaño del mapa conocido (FR-033) | Memoria de una entrada por sala explorada | **Elegida** |
| Una lista de ids explorados recorrida en cada consulta | Trivial | O(k) por consulta con *k* salas exploradas. Se consulta en cada vista, en cada paso de «ir a» y en cada vecina que la búsqueda examina: la búsqueda pasaría a ser O(k² log k) | Descartada, **se mide** |

### 3. Cómo se responde «¿está avistada?»

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Contador por sala: cuántas salidas de salas exploradas llevan a ella** | Consulta O(1) promedio. Explorar una sala suma 1 a los destinos de sus salidas, como mucho 4: el costo es proporcional a las salas reveladas (FR-034). Revertir resta lo mismo, así que una sala avistada por dos exploradas no se «desavista» al revertir una sola | Una tabla más | **Elegida** |
| Recalcular todas las avistadas después de cada exploración | No hay que mantener nada | O(tamaño del mapa conocido) por exploración: incumple FR-034 | Descartada, **se mide** |
| Deducirla al consultar, mirando las salidas de la propia sala | Sin estado extra | Mira las salidas **de la sala consultada**, no las que llegan a ella. Con un paso de un solo sentido, que el traductor admite (`model/room.py:25-26`), da una respuesta falsa | Descartada |

### 4. Cómo se identifica una puerta en la memoria

`TablaHash` solo admite claves `int` o `str`, así que una tupla no sirve.

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **`int`: id de una sala de la puerta × 4 + índice de la dirección por la que sale de ella** (siempre el lado `room_a` de la puerta) | Única: cada salida es única por sala y dirección. Es la misma desde los dos lados porque siempre se calcula desde `room_a`. Es estable entre guardar y cargar, porque depende de ids y direcciones y no de la identidad del objeto en memoria. Es un `int`, que la función hash usa sin conversión | Hay que buscar en qué dirección sale la puerta de `room_a`: como mucho 4 comparaciones | **Elegida** |
| `str` con los ids de las dos salas, por ejemplo `"4-7"` | Legible | **No es única**: dos salidas distintas pueden unir las mismas dos salas (el caso que resolvió FR-008 de la capacidad 002). Además, convertir a texto en cada consulta cuesta más | Descartada |
| La identidad del objeto puerta en memoria | Sin cálculo | No es determinista ni sobrevive a guardar y cargar: después de cargar las puertas son objetos nuevos | Descartada |
| Una tupla | Es lo natural en Python | `TablaHash` la rechaza con `TypeError` | Imposible |

### 5. Cómo se revierte

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Anotar en el historial reversible la operación inversa de cada cambio** (`CallbackChange`), igual que `PlayerTrail.mark` (`structures/trail.py:47-53`) | Es el mecanismo que el pergamino ya usa. Se anota solo lo que cambió: una sala que ya estaba explorada o una puerta que ya se recordaba así no anotan nada. Revertir cuesta lo que costaron los cambios (FR-035). La línea de tiempo recibe los mismos cambios por el mismo camino | Cada cambio crea un objeto de anotación | **Elegida** |
| Copiar el conocimiento al empezar cada acción | Revertir es reemplazar | Es una copia de estado por acción, que P1 §2.11 prohíbe para el retroceso y §3.6 limita a una cada *K* acciones | Descartada |

### 6. «ir a» comparte la búsqueda con el cazador o se separa

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Reutilizar `RutasMasBaratas` con un proveedor de vecinas del mapa conocido** | Ya está escrita, probada y medida, y su desempate es exactamente el de FR-024, incluido el caso de dos salidas hacia la misma vecina. Fue diseñada para esto: recibe las vecinas desde afuera y nunca mira el modelo (su docstring lo dice, y el plan 002 lo anticipa). Se busca **desde el destino**, sin corte, y se pide el primer paso desde la sala del jugador: la misma geometría que el cazador, con el destino en lugar del jugador | Hereda el supuesto del cazador de que el grafo no tiene dirección (ver Riesgos) | **Elegida** |
| Escribir una búsqueda propia para «ir a» | Independiente del cazador | Sería una segunda búsqueda de costo mínimo con un segundo desempate que mantener idéntico al primero. La constitución pide justificar no reutilizar, y no hay con qué | Descartada |
| Recorrido en anchura por cantidad de salas | Más simple | Cuenta salas, no costo: con costos distintos da la ruta equivocada (§5.1 y Historia 4, escenario 2) | Descartada: es incorrecta, no solo más lenta |
| Compartir el **cálculo** del cazador, no solo el código | Ahorraría una búsqueda | Son grafos distintos: el cazador ve todas las puertas reales y el jugador solo las que recuerda (FR-009 de 002 y FR-012 de esta). Compartir el resultado sería un error de reglas | Descartada |

### 7. Recalcular la ruta en cada paso o reutilizarla durante el viaje

FR-026 exige recalcular «con el conocimiento vigente». Como la búsqueda va desde el destino, que no cambia durante el viaje, el resultado solo cambia si cambia el conocimiento.

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Recalcular desde cero antes de cada paso** | Cumple FR-026 literalmente; no hay invalidación que pueda fallar | Una búsqueda por paso | **Elegida**, mientras la medición dé menos de 5 ms |
| Reutilizar la búsqueda del viaje mientras el conocimiento no cambie (un contador de versión del conocimiento que se incrementa con cada exploración o cambio de puerta recordada) | Una búsqueda por viaje en lugar de una por paso: el jugador solo atraviesa salas ya exploradas, así que el conocimiento casi nunca cambia a mitad del viaje | Una invalidación más que mantener correcta, en una operación que el jugador pide a mano y no ocurre en el ciclo de eventos | Descartada, **se mide** contra la elegida. Si la elegida pasara de 5 ms, se cambia y se documenta |

### 8. Dónde viven las reglas del viaje

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Reglas en el modelo (siguiente paso, aceptar la orden, motivos de parada) y el bucle de pasos en el controlador** | El modelo no puede cargar contenido de salas (§6 de P1; `ARQUITECTURA.md` «El controlador carga el contenido antes de mover»). Cada paso pasa por el mismo camino que un `mover` escrito a mano, así que carga el contenido, se registra en la bitácora y precarga igual. Las reglas siguen en el modelo, que es lo que exige MVC | Dos lugares en vez de uno | **Elegida** |
| Todo el viaje dentro del modelo | Un solo lugar | El modelo tendría que pedir contenido de salas, que no puede, o asumir que ya está cargado, que no es cierto | Descartada |
| Todo en el controlador | Un solo lugar | Pondría reglas del juego (cuándo se detiene, qué ruta) fuera del modelo | Descartada |

## Complejidad esperada

Sea *k* el número de salas exploradas, *d* el número de puertas recordadas, *r* el número de salas que revela una entrada (1 sin antorcha, hasta 5 con antorcha) y *c* el número de cambios de conocimiento de una acción. El grado de una sala es a lo sumo 4.

| Operación | Tiempo | Espacio | Nota |
| --- | --- | --- | --- |
| Estado de una sala (explorada, avistada o desconocida) | O(1) promedio | — | Dos búsquedas en `TablaHash`. **No depende de *k*** (FR-033) |
| Estado recordado de una puerta | O(1) promedio | — | Calcular la clave mira como mucho 4 salidas; luego una búsqueda (FR-033) |
| Entrar a una sala sin antorcha | O(1) | O(1) | Marcar 1 sala, sumar a ≤ 4 contadores, observar ≤ 4 puertas |
| Entrar con la antorcha | O(r) = O(1) | O(r) | ≤ 5 salas marcadas y ≤ 20 contadores. **Proporcional a lo revelado, no a *k*** (FR-034) |
| Observar un cambio de puerta | O(1) | O(1) | Comprobar que el jugador está en una de las dos salas y actualizar una entrada |
| Anotar los cambios de una acción | O(c) | O(c) | Una anotación por cambio real |
| Revertir una acción con el pergamino | O(c) | — | Aplica las anotaciones al revés (FR-035) |
| Un paso de «ir a» | O((k + e) log k) | O(k) | Búsqueda desde el destino sobre el subgrafo conocido (*e* ≤ 4*k* salidas), más O(4) para el primer paso con desempate |
| Validar la orden `ir a` | O(1) promedio | — | ¿Está explorada? ¿Es la sala actual? |
| Ver el mapa conocido | O(k log k) | O(k) | Recorre las exploradas y las ordena por id para mostrarlas, con el ordenamiento propio del proyecto. Es un comando que el jugador pide, no ocurre en el ciclo de eventos |
| Exportar o copiar el conocimiento | O(k + d) | O(k + d) | Para el archivo de partida y para los puntos de control |
| Importar | O(k + d) | O(k + d) | Los contadores de avistamiento se rehacen sumando las salidas de cada explorada |
| Memoria total | — | O(k + d + avistadas) | Nunca proporcional a la cripta completa ni a la longitud de la partida |

## Cómo se revierte la exploración

El mapa conocido recibe el historial reversible desde afuera, igual que el rastro. Cada cambio anota su inversa con `history.record(...)`, y el historial solo la guarda mientras hay un intervalo abierto. Eso da tres propiedades sin escribir nada especial:

- **La exploración inicial no se puede revertir.** La sala inicial se marca antes de la primera acción, cuando todavía no hay intervalo abierto, así que no queda anotada. Es lo correcto: FR-002 dice que está explorada desde el instante 0.
- **Revertir no observa puertas.** El pergamino devuelve `closed` de cada puerta con su propia anotación y el historial ignora anotaciones nuevas mientras deshace (`History.is_recording`). Así revertir no cuenta como «la puerta cambió con el jugador presente».
- **La línea de tiempo recibe lo mismo.** Si Erick reconstruye hacia atrás invirtiendo cambios, los del conocimiento ya están en la misma secuencia de anotaciones.

**Qué se anota**, y esto responde la pregunta de §8 sobre la antorcha:

| Cambio | Anotación | Cuándo no se anota nada |
| --- | --- | --- |
| Una sala pasa a explorada | «deshacer exploración de esta sala»: quitarla de exploradas, sacarla de la pila del orden y restar 1 a los destinos de sus salidas | Si ya estaba explorada |
| Cambia lo que se recuerda de una puerta | El valor recordado anterior, o «no se recordaba» si nunca se había observado | Si el valor observado es igual al recordado |

**Entrar con la antorcha encendida a una sala con cuatro vecinas nuevas** deja como mucho cinco anotaciones de exploración (la sala y sus cuatro vecinas) y una por cada puerta de la sala cuyo recuerdo cambió. Nada más. Revertir esa entrada quita exactamente esas salas y deja las vecinas que ya estaban exploradas como estaban (Historia 6, escenario 1).

**El orden de exploración se revierte como una pila.** Las anotaciones se deshacen en orden inverso, así que la última sala explorada es siempre la primera en desexplorarse. Sacar de la pila es sacar el último elemento de la `list`, O(1), sin desplazar nada.

**El pergamino durante un viaje** no necesita nada propio. Cada paso es una acción completa que abre su propio intervalo en el historial (`Game.move` llama a `history.begin_action`). El viaje no es estado del juego: es un bucle del controlador que ya terminó cuando el jugador puede escribir `retroceder`. El pergamino revierte el último intervalo, que es el último paso con todo lo que exploró y observó, y no hay ningún viaje guardado que pueda reanudarse (FR-032).

## Cómo se exporta e importa el conocimiento

Este plan define el **contenido**; el formato binario es de Carlos.

- **Exportar** devuelve dos listas planas de enteros y booleanos:
  1. los ids de las salas exploradas, **en orden de exploración**;
  2. pares (clave de puerta, recordada abierta) por cada puerta recordada, en orden creciente de clave.
- **Importar** recibe esas dos listas y el mapa de salas, marca las exploradas en ese orden, rehace los contadores de avistamiento sumando las salidas de cada explorada y carga las puertas recordadas. **No anota nada en el historial**, porque cargar no es una acción del jugador.
- **No se exportan** los contadores de avistamiento: se deducen de las exploradas. Guardarlos sería guardar dos veces el mismo dato con riesgo de que no coincidan.

La misma exportación sirve como **copia para un punto de control** de la línea de tiempo, si Erick reconstruye hacia adelante.

## Qué se cambia, archivo por archivo

### Estructura nueva (mía)

- **`cripta/structures/mapa_conocido.py`** (nuevo): salas exploradas, contadores de avistamiento, puertas recordadas y orden de exploración. Expone las consultas, la entrada a una sala, la observación de una puerta, el proveedor de vecinas conocidas para la búsqueda, y exportar e importar. Recibe el mapa de salas y el historial desde afuera, con duck typing, y no importa el motor. Interfaz en [contracts/interfaz-mapa-conocido.md](./contracts/interfaz-mapa-conocido.md).

### Modelo

- **`cripta/model/viaje.py`** (nuevo, mío): las reglas del viaje sobre el estado de la partida, sin efectos. Valida la orden (FR-022), calcula el siguiente paso reutilizando `RutasMasBaratas` (FR-023, FR-024, FR-026) y decide los motivos de parada después de un paso (FR-028), en el orden de FR-028. No carga contenido ni mueve al jugador.
- **`cripta/model/game.py`** (de Carlos; **lo que necesito de él**). Ganchos pequeños, sin cambiar ninguna regla existente:
  1. Recibir el mapa conocido como colaborador opcional en el constructor y en `Game.load`, con un objeto nulo cuando no hay, igual que `_NoHistory` (`game.py:48`).
  2. «El jugador entró a la sala X», con el estado de la antorcha: en `_begin_new_game` (`game.py:159`), antes de activar enemigos, y en `move` (`game.py:304-307`), justo después de cambiar la sala del jugador y antes de activar enemigos y disparar trampas.
  3. «Una puerta cambió»: en `open_door` (`game.py:354`) y en `_close_door` (`game.py:1050`), justo después de cambiar `closed`.
  4. Que `EnemyView` (`game.py:77-82`) traiga si el enemigo es cazador, para FR-021. Si Carlos prefiere no tocarlo, la aplicación lo deduce buscando el enemigo por su id; es peor porque duplica el filtro de `visible_state`.
- **Lo que no se toca del motor**: el combate, la agenda, la activación de enemigos, las trampas, el rastro, el cazador y el costo del movimiento. Un paso de «ir a» es un `move` normal.

### Controlador, reproducción y vista (míos)

- **`cripta/controller/commands.py`**: dos comandos nuevos, `mapa` e `ir a <sala>`. Ninguno es una «acción del modelo» que se registre tal cual en la bitácora: `mapa` no cambia nada (FR-019) y `ir a` se registra como sus pasos (FR-031). Se agregan a la ayuda.
- **`cripta/controller/game_controller.py`**: el bucle del viaje. Valida con el modelo; escribe el comentario en la bitácora; y mientras no haya motivo de parada, pide el siguiente paso, lo ejecuta con `execute(Command(MOVE, dirección))` (el mismo camino que un `mover` escrito a mano: carga contenido, registra y precarga) y pide los motivos de parada. Devuelve los motivos para que la vista los muestre (FR-029).
- **`cripta/replay/replay_log.py`**: un método para escribir un comentario en la bitácora. **La lectura ya ignora las líneas que empiezan con `#`**, así que reproducir no cambia (FR-031, SC-003).
- **`cripta/controller/application.py`**: armar la vista del mapa conocido; que `room_view` (`application.py:172`) muestre las salidas según el conocimiento, con los destinos avistados como «hay algo en esa dirección» y sin id (FR-020); atender `mapa` e `ir a` en el bucle de comandos.
- **`cripta/view/console_view.py`**: mostrar el mapa conocido, los motivos de parada del viaje y una marca de cazador en la lista de enemigos.

### Guardado (de Carlos; **lo que necesito de él**)

- **`cripta/adapters/almacen_partida.py`**: guardar en el bloque global las dos listas de la exportación y, al cargar, importarlas. Que `construir_juego` y `construir_juego_reversible` (`almacen_partida.py:1055`, `:1126`) armen el mapa conocido con el historial, igual que hoy arman el rastro. **Sube la versión del formato** (hoy 2, `almacen_partida.py:94`). La subida tiene que acordarse con Erick para que sea una sola, porque la línea de tiempo también cambia el formato.

### Mediciones (mías)

- **`cripta/benchmark/bench_mapa_conocido.py`** (nuevo) y una línea en `SUITES` de `cripta/benchmark/benchmark.py`.

### Lo que necesito de los demás

| Quién | Qué | Estado |
| --- | --- | --- |
| Carlos | Ganchos de entrada a sala y cambio de puerta en `game.py`, y el mapa conocido como colaborador | **Falta** |
| Carlos | Cazador distinguible en `EnemyView` | **Falta** (hay alternativa sin él) |
| Carlos | Bloque del conocimiento en el archivo de partida y armado en `construir_juego*` | **Falta** |
| Carlos | `RutasMasBaratas` reutilizable con otro proveedor de vecinas | **Existe** (`structures/rutas_mas_baratas.py`) |
| Carlos | Confirmar si las criptas pueden tener pasos de un solo sentido (ver Riesgos) | **Falta**: afecta también al cazador |
| Erick | Si reconstruye hacia atrás, que use las mismas anotaciones del historial, sin el límite de 5 intervalos del pergamino. Si reconstruye hacia adelante, que el punto de control incluya la exportación del conocimiento | **Falta decidirlo**: es su plan |
| Erick | Una sola subida de versión del formato junto con Carlos | **Falta** |
| Mauricio | Nada para esta capacidad. La consulta de llaves y la verificación son de su especificación | — |

### Lo que otros necesitan de mí

- **Erick**: exportar y copiar el conocimiento para el resumen de `historia` («el mapa conocido en ese momento», §3.6) y para los puntos de control.
- **Carlos**: la interfaz del mapa conocido (dos avisos y exportar/importar), fijada en [contracts/interfaz-mapa-conocido.md](./contracts/interfaz-mapa-conocido.md).

## Mediciones previstas

Todas entran en `--bench` por una suite nueva, con criptas sintéticas deterministas por semilla. **Los tamaños se fijan cuando se conozca la cripta publicada más grande**; hasta entonces se miden tres tamaños crecientes de mapa conocido para ver la tendencia. No se escribe ningún número antes de medirlo.

| # | Qué se mide | Elegida | Alternativa descartada, medida directamente | Qué debería mostrar | Requisito |
| --- | --- | --- | --- | --- | --- |
| 1 | Consultar el estado de una sala | Tabla de exploradas y contadores | Lista de exploradas recorrida en cada consulta | Que la elegida queda plana al crecer el mapa conocido y la lista crece linealmente | FR-033, SC-007 |
| 2 | Consultar una puerta recordada | Tabla con clave entera | Clave de texto `"a-b"` (solo tiempo; su problema de unicidad es de corrección y se prueba aparte) | El costo de la clave de texto frente a la entera | FR-033 |
| 3 | Explorar *k* salas nuevas | Contadores incrementales | Recalcular todas las avistadas después de cada exploración | Que la elegida es proporcional a *k* y la alternativa crece con el mapa conocido | FR-034, SC-007 |
| 4 | Anotar y revertir una entrada con antorcha | Anotaciones inversas | Copiar el conocimiento antes de la acción | Que revertir no depende del tamaño del mapa conocido | FR-035 |
| 5 | Un paso de «ir a» con el mapa conocido completo | Recalcular en cada paso con `RutasMasBaratas` | (a) reutilizar la búsqueda del viaje mientras el conocimiento no cambie; (b) búsqueda con selección lineal del mínimo, sin montículo, escrita solo dentro de la medición | Si la elegida cumple los 5 ms; cuánto ahorra (a); cuánto aporta el montículo frente a (b) | FR-036, SC-006 |

Si la medición 5 da más de 5 ms, se cambia a la alternativa (a), se documenta el antes y el después y se corrige este plan.

## Riesgos

- **Pasos de un solo sentido.** El traductor los admite: si una salida no tiene vuelta, la puerta solo aparece en la sala que la declara (`model/room.py:25-26`, `repository/traductor.py:183-206`). La búsqueda va desde el destino y expande por las salidas de cada sala, así que con un paso de un solo sentido calcularía una distancia por un camino que en realidad no se puede recorrer en ese sentido. **El cazador ya depende del mismo supuesto** (plan 002, «El supuesto del grafo sin dirección»). En `cripta-01` las 10 salidas tienen vuelta; no se sabe si alguna cripta publicada tiene un paso de un solo sentido. Si existen, la corrección es la misma para las dos capacidades: expandir por las salidas que **llegan** a cada sala y elegir el primer paso por las que **salen**. Se coordina con Carlos antes de implementar.
- **Una puerta que cambia y no avisa.** Si algún camino del motor cambia `closed` sin pasar por el gancho, el mapa queda desactualizado aunque el jugador esté presente, y FR-006 se rompe en silencio. Hoy solo hay dos lugares que cambian puertas (`open_door` y `_close_door`); el retroceso las cambia también pero no debe observar. La prueba de SC-002 compara, en cada instante, el recuerdo contra la realidad de las puertas de la sala del jugador.
- **Detectar el daño.** FR-028 (c) se comprueba comparando la vida del jugador antes y después del paso. Durante el ciclo de eventos la vida del jugador solo baja (veneno, ataques, trampas); las curaciones son acciones del jugador y no ocurren a mitad de un paso. Si alguna regla futura curara al jugador dentro del ciclo, un daño y una curación iguales se cancelarían y no se detectarían; entonces habría que pedirle al motor un contador de daño recibido.
- **La vista cambia y rompe pruebas existentes.** `room_view` hoy muestra el id de todos los destinos. Con FR-020 los destinos avistados dejan de mostrar su id, y las pruebas de la vista que lo fijan cambian. Es una de las dos excepciones que SC-009 admite.
- **Dependencia de tres archivos ajenos.** Los ganchos de `game.py` y el bloque del guardado son de Carlos. Si no llegan a tiempo, la capacidad se prueba con el mapa conocido armado a mano en las pruebas, pero la partida real no la tendrá.

## Trazabilidad

| Requisito | Dónde se implementa | Dónde se prueba |
| --- | --- | --- |
| FR-001 a FR-005 | `structures/mapa_conocido.py` | `tests/test_mapa_conocido.py` |
| FR-006, FR-007, FR-008 | `structures/mapa_conocido.py`, ganchos de `model/game.py` | `tests/test_mapa_conocido.py`, `tests/test_niebla.py` |
| FR-009, FR-010, FR-011, FR-037 | `structures/mapa_conocido.py`, gancho de entrada en `model/game.py` | `tests/test_niebla.py` |
| FR-012, FR-013 | `structures/mapa_conocido.py` (proveedor de vecinas conocidas), `controller/application.py` | `tests/test_niebla.py`, `tests/test_ir_a.py`, `tests/test_console_view.py` |
| FR-014 | `structures/mapa_conocido.py` (exportar e importar), `adapters/almacen_partida.py` | `tests/test_niebla.py`, `tests/test_almacen_partida.py` |
| FR-015, FR-035 | anotaciones en `structures/mapa_conocido.py` | `tests/test_niebla.py` |
| FR-016 | exportar o anotaciones, según el plan de Erick | prueba de la línea de tiempo (especificación de Erick) |
| FR-017 | consecuencia del principio II | `tests/test_niebla.py` (dos corridas idénticas) |
| FR-018, FR-019 | `controller/commands.py`, `controller/application.py`, `view/console_view.py` | `tests/test_commands.py`, `tests/test_console_view.py` |
| FR-020, FR-021 | `controller/application.py`, `view/console_view.py` | `tests/test_console_view.py` |
| FR-022 a FR-030 | `model/viaje.py`, `controller/game_controller.py` | `tests/test_ir_a.py` |
| FR-031 | `controller/game_controller.py`, `replay/replay_log.py` | `tests/test_ir_a.py`, `tests/test_replay_log.py` |
| FR-032 | ninguno propio: cada paso es una acción del historial | `tests/test_ir_a.py` |
| FR-033, FR-034, FR-036 | el diseño completo | mediciones 1, 3 y 5 |

## Fases

**Fase 0 — Investigación.** Hecha. Ver [research.md](./research.md).

**Fase 1 — Diseño.** Hecha. Ver [data-model.md](./data-model.md), [contracts/](./contracts/) y [quickstart.md](./quickstart.md).

**Revisión contra la constitución después del diseño.** Sigue pasando. El diseño no agregó ninguna estructura más allá de la decidida, ninguna solicitud de red y ningún dato de cripta. Las claves de las tres tablas son `int`.

**Fase 2 — Tareas.** Las genera `/speckit-tasks` en `tasks.md`. No se ejecuta en esta sesión.
