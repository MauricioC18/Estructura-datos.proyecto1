# Plan de implementación: La línea de tiempo

**Carpeta**: `specs/003-linea-de-tiempo` | **Fecha**: 2026-11-16 | **Especificación**: [spec.md](./spec.md)

## Resumen

La capacidad necesita responder, para cualquier instante pasado, cómo estaba la partida, sin tocar la partida y sin guardar una copia del mundo por acción.

La decisión central es **cómo se reconstruye**. El enunciado permite dos caminos: hacia adelante desde un punto de control, re-simulando, o hacia atrás desde el estado actual, invirtiendo cambios. **Se elige hacia adelante**, y la razón no es de gusto: el camino hacia atrás es **imposible** con el historial que ya existe, y la razón está en el código.

`structures/history.py` guarda cambios inversos, pero sus objetos de cambio guardan **referencias directas a los objetos vivos**: un cambio de atributo sabe «este jugador, este atributo, este valor anterior». Para acotar una consulta a *K* acciones hay que partir de un punto de control, y un punto de control reconstruido crea **objetos nuevos**. Los cambios inversos no se pueden aplicar a esos objetos nuevos, porque apuntan a los viejos. Aplicarlos sobre los objetos vivos obligaría a restaurar el estado vivo campo por campo, en el sitio, sin cambiar la identidad de ningún objeto, y a dejarlo todo como estaba al terminar la consulta. Eso es un segundo deserializador que muta en vez de construir, con la agenda de eventos y los efectos apuntando a los mismos actores. Es mucho más riesgoso que lo que resuelve.

Hacia adelante, en cambio, todo lo que hace falta ya está escrito: `adapters/almacen_partida.py` serializa el estado completo **incluido el estado del generador aleatorio**, y lo vuelve a leer construyendo objetos nuevos con `Game.load`, que no rehace el trabajo de inicio de partida. Un punto de control es ese mismo bloque de bytes, guardado en memoria en vez de en disco, y una consulta es: reconstruir el punto de control más cercano, repetir a lo sumo *K* acciones del jugador, y leer el resumen. **La partida viva no se toca en ningún momento**, así que FR-005 a FR-008 se cumplen por construcción y no por cuidado.

## Contexto técnico

**Lenguaje**: Python 3.11 o superior; el desarrollo corre sobre 3.14.6.

**Dependencias nuevas**: ninguna.

**Estructuras**: se reutiliza el serializador completo del guardado binario, la búsqueda binaria propia que ese módulo ya tiene, y la lista contigua para las copias y las acciones. No se escribe ninguna estructura de datos nueva; sí un módulo nuevo que las orquesta.

**Persistencia**: el archivo de partida tiene que llevar la línea completa, así que **el formato sube de la versión 2 a la 3**. Un archivo de la primera parte ya se rechaza por versión, que es lo que pide FR-021.

**Pruebas**: `unittest`, desde `cripta/` con `python -m unittest discover -s tests -t .`. Hoy hay 945 pruebas y todas pasan.

**Rendimiento**: el ciclo completo de eventos entre dos decisiones del jugador debe seguir por debajo de 20 ms. La última medición, con 50 cazadores activos, da 0.1854 ms.

**Alcance**: un módulo nuevo, un embudo en el motor, el guardado binario, el comando de consulta y las mediciones. Las dos banderas nuevas de línea de comandos las integra la Persona 4; este plan le deja la interfaz lista y lo dice explícitamente.

## Revisión contra la constitución

| Principio | Cómo lo cumple este plan |
| --- | --- |
| I. Estructuras propias, sin dependencias prohibidas | **No entra ninguna prohibida.** La búsqueda del punto de control más cercano es búsqueda binaria **propia**, la que `almacen_partida` ya tiene para su índice de salas; `bisect` está prohibido. Las copias y las acciones van en `list` como almacenamiento contiguo, que sí está permitido, no como índice. No se usa `dict` como índice ni `set` |
| II. Determinismo | La reconstrucción se apoya en que la partida es determinista por semilla. El punto de control guarda el estado del generador, así que repetir las acciones produce exactamente los mismos resultados. El único punto donde el determinismo se rompía está identificado y resuelto: ver «El agujero del pergamino» |
| III. Separación MVC | La línea vive en el modelo y no sabe de vista ni de comandos. El resumen es un dato, no texto formateado: la vista lo imprime. La consulta sin interacción no instancia la vista porque no la necesita |
| IV. Ningún dato de una cripta en el código | No se escribe ningún identificador ni cantidad de ninguna cripta. El único número propio es el valor por omisión de *K*, que es una decisión del grupo justificada con mediciones, no un dato de una cripta |
| V. Presupuesto de solicitudes | **No se agrega ninguna solicitud.** Reconstruir usa lo que ya está en memoria; el punto de control lleva la cripta reconstruida dentro |
| VI. Rendimiento respaldado con medición | Se miden memoria y tiempo de consulta para cuatro valores de *K*, incluida la alternativa ingenua de una copia por acción, y el valor por omisión se escoge con esos números |
| VII. Especificación antes del código | La especificación se confirmó en `9b2c660`, antes de este plan y antes de cualquier código |

**Resultado: pasa, con una desviación declarada.** Ver «Desviación declarada» al final de las alternativas.

## Alternativas consideradas

### Cómo se reconstruye el estado de un instante

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Hacia adelante desde un punto de control, re-simulando** | Todo lo necesario ya existe y está probado: el serializador completo con el estado del generador, y el cargador que construye objetos nuevos sin rehacer el inicio de partida. La partida viva **no se toca**, así que «la consulta no altera nada» sale por construcción. La memoria por acción es minúscula: el nombre de la acción y su argumento | Depende de que la partida sea determinista, y hay un punto donde no lo era. Hay que registrar las acciones del jugador, lo que toca el motor en un embudo | **Elegida** |
| Hacia atrás desde el estado actual, invirtiendo cambios | Reutilizaría las anotaciones de cambios inversos que ya están repartidas por todo el motor, que es el activo más grande de la primera parte | **No es viable con el historial que existe.** Los cambios guardan referencias a los objetos vivos, así que no se pueden aplicar a un punto de control reconstruido, que crea objetos nuevos. Y sin punto de control la consulta cuesta toda la partida, lo que viola FR-016. Hacerlo viable pedía restaurar el estado vivo en el sitio, campo por campo, sin cambiar la identidad de ningún objeto, y devolverlo todo al final | Descartada |
| Una copia completa del estado por cada acción | La consulta es inmediata y no hay nada que reconstruir | Es exactamente lo que §5.5 prohíbe: la memoria crece como acciones por tamaño del estado. En una partida de 500 acciones son 500 copias de la cripta entera | Descartada, pero **se implementa como modo de medición**: es la referencia contra la que se mide el ahorro, y el principio VI pide medir la alternativa descartada |

El argumento decisivo es el de la segunda fila, y conviene decirlo así en la defensa: **el camino hacia atrás no se descartó por preferencia, se descartó porque el diseño de la primera parte lo impide**. Las anotaciones de cambios inversos sirven para deshacer sobre el mismo objeto, que es justo lo que el pergamino necesita, y no sirven para reconstruir sobre una copia, que es lo que la línea de tiempo necesita. Son dos problemas parecidos con respuestas distintas.

### El agujero del pergamino, y por qué casi rompe el diseño

Re-simular exige determinismo, y aquí había un agujero real. El pergamino, al revertir una acción, devuelve el reloj a su valor anterior pero **no devuelve el estado del generador aleatorio**: `History.undo` llama a `rewind_clock_to` y no toca el generador. Está así desde la primera parte y es una decisión deliberada, documentada junto a la del contador de secuencia.

Consecuencia: después de un pergamino, la partida viva sigue con un generador que ya consumió números, mientras que re-simular desde un punto de control anterior volvería a consumirlos desde donde estaban. Los dos estados se separan, y el resumen de cualquier instante posterior a un pergamino sería **falso**. FR-023 se rompería sin que ninguna partida corta lo notara.

Tres salidas, y la elegida es la pequeña:

| Salida | Costo | Decisión |
| --- | --- | --- |
| Anotar el estado del generador cada vez que se usa un pergamino | Un registro por pergamino usado, de unos 5 KB, mucho menos que una copia completa | **No alcanza.** Ver abajo | Descartada al implementar |
| **Forzar una copia completa cada vez que se usa un pergamino** | Captura todo lo que un pergamino deja fuera del alcance de la lista de acciones, no solo el generador | Una copia completa en vez de 5 KB, y una copia extra fuera de la cadencia de *K* | **Elegida** |
| Anotar el estado del generador en cada acción | Alinearía siempre, sin pensar. Pero el estado de un generador de Mersenne son 625 enteros: unos 5 KB por acción, 2.5 MB en 500 acciones, para un dato que casi nunca cambia de forma imprevisible | Descartada |
| Hacer que el pergamino revierta el generador | Sería lo más limpio conceptualmente, pero cambia el comportamiento de una capacidad ya entregada y evaluada de la primera parte, y rompería su determinismo documentado | Descartada |

**Corrección hecha al implementar.** La idea del anclaje de 5 KB se implementó y la prueba de equivalencia la tumbó: un pergamino, además de no revertir el generador, **consume un pergamino del inventario**, y ese consumo no es una acción del jugador, así que no está en la lista que la re-simulación repite. El anclaje alineaba el azar y dejaba el inventario mal.

La respuesta correcta es más simple de explicar: **un pergamino es un punto donde el estado vivo no se puede derivar de la lista de acciones, así que la línea se re-ancla con una copia completa.** Es corrección, no optimización, y por eso se paga la copia. El mecanismo del anclaje se retiró del código en vez de dejarlo sin uso.

**Esto es lo que hay que poder contar en la defensa**: el diseño elegido obligó a buscar dónde el programa no era determinista, y apareció un punto que la primera parte había dejado así a propósito. No es un defecto de la primera parte: es que la línea de tiempo le pide algo que el pergamino no necesitaba. Y la primera respuesta que se nos ocurrió era insuficiente; lo descubrió una prueba, no un razonamiento.

### Qué se registra por cada acción del jugador

Lo mínimo para repetirla: su nombre y su argumento. El argumento depende de la acción, y hay un caso que no es obvio.

Soltar, usar y equipar actúan sobre **el objeto que el jugador está viendo**, y el cursor del inventario lo mueven los comandos «siguiente» y «anterior», que **no consumen tiempo** y por lo tanto no son acciones. Si se registrara solo «soltar», al repetirla el cursor estaría en otra parte y se soltaría otro objeto.

Por eso para esas tres se registra **el identificador del objeto**, no la posición ni el cursor. Al repetir, se pone el cursor sobre ese objeto por identificador y se ejecuta. Queda bien aunque el inventario haya cambiado de orden por cualquier motivo.

Se comprobó además que mostrar el inventario ordenado **no** reordena el inventario: devuelve una lista nueva. Si lo hubiera reordenado en el sitio, sería otro estado que registrar.

### Dónde se registra

En `_finish_player_action`, que es el **único** embudo por el que pasa toda acción del jugador aceptada que consume tiempo. Las ocho acciones llegan ahí, siete por `_player_acts` y moverse directamente. Registrar en el embudo, y no en cada comando del controlador, mantiene la línea en el modelo y hace que funcione igual con vista, sin vista y en reproducción.

Las acciones **rechazadas** no llegan al embudo, así que no entran en la línea, que es lo correcto: no ocurrieron.

### Cómo se encuentra el punto de control del que partir

Las copias se guardan en una lista contigua, en orden creciente de número de acción, porque se crean en ese orden. Encontrar la última copia en o antes de un número de acción es **búsqueda binaria**, la misma que `almacen_partida` ya tiene para su índice de salas; `bisect` está prohibido. Eso es O(log n) y responde a FR-018, que pide no examinar todas las copias.

Para una consulta por instante del reloj hay un paso previo: traducir el instante al número de acción. Las acciones también están en orden creciente de reloj, así que es otra búsqueda binaria sobre la misma lista.

### Cómo se recorta la línea cuando se usa un pergamino

El pergamino quita **una** acción. Recortar es quitar el último registro de acción y, si la última copia correspondía justamente a esa acción, quitarla también. Es trabajo constante, no un recorrido: eso responde a FR-019 y SC-008.

### Desviación declarada

El enunciado permite «no más de una copia completa cada *K* acciones del jugador». Este plan cumple eso durante el juego normal, pero **fuerza una copia extra cada vez que se usa un pergamino**, que puede caer dentro de las *K* acciones de la anterior.

Se declara en vez de esconderlo, con su justificación: sin esa copia el programa informaría una historia **falsa**, y §3.6 exige que el estado consultado sea el real. Entre correcto y dentro del presupuesto de memoria, manda correcto. La cantidad de copias extra está acotada por los pergaminos que la cripta contenga, porque cada uso consume uno, y la medición de memoria las reporta aparte para que se vea cuánto pesan.

## Qué se cambia, archivo por archivo

### Estructura nueva

- **`cripta/structures/linea_de_tiempo.py`** (nuevo) — la línea. Guarda la lista de acciones registradas, la lista de copias completas con su número de acción y su reloj, y los anclajes del generador. Expone: registrar una acción, recortar por pergamino, localizar de qué copia partir para un instante o para un número de acción (búsqueda binaria propia), y cuánta memoria ocupa. **No reconstruye**: no sabe nada del motor.

### Modelo

- **`cripta/model/game.py`** — el embudo de acción del jugador registra en la línea el nombre de la acción y su argumento, y cada cierta cantidad de acciones pide una copia completa. El pergamino recorta la línea y anota el estado del generador. La línea se recibe **desde afuera**, como la bitácora y el historial, de modo que una partida sin línea sigue funcionando igual.

### Reconstrucción

- **`cripta/model/consulta_historia.py`** (nuevo) — responde una consulta. Reconstruye el punto de control más cercano en objetos nuevos, repite a lo sumo *K* acciones, aplica los anclajes del generador que cruce, y devuelve el resumen. Es quien conoce al motor y al serializador; la línea no.

### Adaptador de persistencia

- **`cripta/adapters/almacen_partida.py`** — se separa el armado del contenido en bytes de su escritura en disco, para que un punto de control sea el mismo bloque **en memoria**; hoy `guardar` construye el contenido completo y lo escribe de una vez, así que el corte es pequeño. Se agrega la línea al archivo y **la versión del formato sube de 2 a 3**.

### Vista y controlador

- **`cripta/controller/commands.py`** y **`cripta/view/console_view.py`** — el comando de consulta y la impresión del resumen. El resumen que produce el modelo es un dato; la vista decide cómo se ve.

### Mediciones

- **`cripta/benchmark/bench_linea_de_tiempo.py`** (nuevo) — memoria y tiempo de consulta para cuatro valores de *K*, incluida la copia por acción.

**Lo que no se toca**: el pergamino y su límite de cinco acciones, el historial reversible, la agenda, el combate, y la lógica de los cuatro comportamientos de enemigo.

**Lo que queda para la Persona 4**, con la interfaz ya lista: las banderas `--checkpoint-cada K` y `--replay ... --hasta t`. El modelo expondrá la consulta y el resumen; conectar las banderas es integración.

## Complejidad esperada

Sea *A* la cantidad de acciones del jugador, *C* la de copias (*A/K*), y *E* el tamaño del estado.

| Operación | Costo | Nota |
| --- | --- | --- |
| Registrar una acción | O(1) | Agregar a una lista contigua |
| Tomar una copia completa | O(E) | Una cada *K* acciones |
| Localizar la copia de la que partir | O(log C) | Búsqueda binaria propia |
| Traducir un instante a número de acción | O(log A) | Búsqueda binaria sobre la misma lista |
| Responder una consulta | O(E + K · coste de una acción) | Reconstruir la copia y repetir a lo sumo *K* acciones |
| Recortar por pergamino | O(1) | Quita una acción y a lo sumo una copia |
| Memoria | O(A + (A/K) · E + pergaminos · 5 KB) | Frente a O(A · E) de la alternativa ingenua |

Lo que importa de esta tabla: **el costo de una consulta no tiene ninguna *A***. Por eso SC-002 pide que consultar en una partida de 500 acciones cueste lo mismo que en una de 50.

## Mediciones previstas

1. **Memoria y tiempo de consulta para cuatro valores de *K***: 1, 10, 50 y 200. *K* = 1 es la alternativa ingenua, una copia por acción, y es la referencia. Lo que se busca es la rodilla de la curva, donde bajar más *K* ya casi no acelera la consulta pero sigue costando memoria.
2. **El costo de una consulta frente al largo de la partida**: consultar el instante inicial en partidas de 50, 200 y 500 acciones, con *K* fijo. Debe quedar plano (SC-002).
3. **El recorte por pergamino frente al largo de la partida** (SC-008). Debe quedar plano.
4. **El ciclo de eventos con la línea activa**, contra los 0.1854 ms actuales y el límite de 20 ms (FR-024, SC-009).

Para la memoria se mide el tamaño real en bytes de lo que la línea guarda, no una estimación: las copias son bloques de bytes, así que se pueden sumar.

**Qué se reporta si el resultado no es el esperado**: si *K* = 1 resulta aceptable en memoria para las criptas de esta escala, se reporta tal cual y se discute si la complejidad del diseño se justifica. La constitución pide el número incómodo antes que el favorable sin respaldo. Lo que **no** cambia con las mediciones es que §5.5 prohíbe la copia por acción, así que el diseño se mantiene aunque la medición fuera indulgente; lo que las mediciones deciden es el valor por omisión de *K*.

## Riesgos

- **La divergencia por el generador aleatorio es el riesgo grande.** Ya está identificada y resuelta con los anclajes, pero cualquier otra fuente de no determinismo produciría resúmenes falsos sin que nada se vea raro. Por eso la prueba central no compara contra valores escritos a mano: juega una partida larga guardando el estado real en cada acción, y después consulta **todos** los instantes y exige que cada resumen coincida con lo que de verdad hubo. Es la técnica que en la capacidad del cazador destapó dos errores propios.
- **Las acciones que actúan sobre «el objeto que se está viendo»** son el caso fácil de arruinar, porque el cursor lo mueven comandos que no son acciones. Se registra el identificador del objeto, no la posición, y hay prueba de soltar, usar y equipar después de mover el cursor.
- **Repetir una acción podría tener efectos que no deberían repetirse**, por ejemplo escribir en la bitácora de reproducción o contar solicitudes al servicio. La reconstrucción trabaja sobre un motor armado sin bitácora y sin repositorio, de modo que repetir no puede escribir nada ni pedir nada.
- **Una copia completa guarda la cripta entera**, incluido el esqueleto, que no cambia nunca. Es desperdicio: lo que de verdad hace falta es el estado mutable. Se mide cuánto pesa y se deja anotado como la optimización evidente; no se hace ahora porque reutilizar el serializador completo, que ya está probado, vale más que ahorrar bytes en una cripta de este tamaño.
- **El cambio de versión del formato a 3** invalida los guardados de la capacidad anterior, no solo los de la primera parte. Hay que decirlo al grupo.
- **Defecto encontrado al implementar, ajeno a esta capacidad.** La prueba de equivalencia destapó que el archivo de partida **nunca guardó el costo de las salidas**: la capacidad 001 lo agregó al modelo y no al guardado, así que guardar y cargar devolvía todas las salidas a costo 100 en silencio. No había prueba que lo cubriera porque el costo se agregó después del guardado. Se corrigió aquí, y es el argumento más fuerte a favor de esta capacidad: reconstruir el pasado obliga a que el estado se serialice **completo**, y eso delata cualquier campo que falte.

## Trazabilidad

| Requisito | Dónde se implementa | Dónde se prueba |
| --- | --- | --- |
| FR-001, FR-002, FR-023 | `model/consulta_historia.py` | `tests/test_linea_de_tiempo.py`, prueba de todos los instantes |
| FR-003 | `structures/linea_de_tiempo.py`, `model/consulta_historia.py` | `tests/test_linea_de_tiempo.py` |
| FR-004 | `model/consulta_historia.py` | `tests/test_linea_de_tiempo.py` |
| FR-005 a FR-008 | se cumplen por construcción: la consulta trabaja sobre objetos nuevos | `tests/test_linea_de_tiempo.py` |
| FR-009, FR-010 | `model/consulta_historia.py` | `tests/test_linea_de_tiempo.py` |
| FR-011, FR-019 | `structures/linea_de_tiempo.py`, `model/game.py` | `tests/test_linea_de_tiempo.py` |
| FR-012, FR-013 | ninguno: el pergamino no se toca | `tests/test_linea_de_tiempo.py`, y las pruebas del pergamino que ya existen |
| FR-014 | `model/consulta_historia.py` (no instancia la vista) | `tests/test_linea_de_tiempo.py` |
| FR-015, FR-016 | `model/game.py`, `structures/linea_de_tiempo.py` | `tests/test_linea_de_tiempo.py` |
| FR-017 | `structures/linea_de_tiempo.py` | medición 1 |
| FR-018 | `structures/linea_de_tiempo.py` (búsqueda binaria propia) | `tests/test_linea_de_tiempo.py` |
| FR-020, FR-021 | `adapters/almacen_partida.py` | `tests/test_almacen_partida.py` |
| FR-022 | consecuencia de II | `tests/test_linea_de_tiempo.py` |
| FR-024 | el diseño completo | medición 4 |

## Fases

**Fase 0 — Investigación.** Hecha y recogida en este plan. Se revisó: que los objetos de cambio del historial guardan referencias a los objetos vivos, lo que descarta el camino hacia atrás; que el serializador ya guarda el estado del generador y que el cargador construye objetos nuevos sin rehacer el inicio de partida; que `_finish_player_action` es el único embudo de las acciones del jugador; que mostrar el inventario ordenado no lo reordena; y que el pergamino **no** revierte el generador, que era el agujero del diseño. No hace falta un `research.md` aparte.

**Fase 1 — Diseño.** El modelo de datos son tres listas contiguas —acciones, copias y anclajes del generador— y está descrito arriba. No amerita un `data-model.md` aparte.

**Fase 2 — Tareas.** Las genera `/speckit.tasks` en `tasks.md`.
