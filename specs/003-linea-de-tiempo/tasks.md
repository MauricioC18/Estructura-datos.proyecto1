# Tareas: La línea de tiempo

**Especificación**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Cada tarea referencia los requisitos que atiende. No hay tareas sin requisito.

Las tareas marcadas con **[P]** pueden hacerse en paralelo con la anterior porque tocan archivos distintos. Las etiquetas **[H1]**–**[H6]** remiten a las historias de la especificación.

## Lista

### Fase 1 — Base, bloquea todo lo demás

- [x] T001 La línea: acciones, copias, anclajes y búsqueda binaria, en `cripta/structures/linea_de_tiempo.py`
- [x] T002 [P] Pruebas de la línea, en `cripta/tests/test_linea_de_tiempo.py`
- [x] T003 Separar el armado del contenido de su escritura, en `cripta/adapters/almacen_partida.py`
- [x] T004 El motor registra cada acción del jugador y pide copias, en `cripta/model/game.py`

### Fase 2 — Historia 1: consultar un instante pasado (P1)

- [x] T005 [H1] La reconstrucción y el resumen, en `cripta/model/consulta_historia.py`
- [x] T006 [H1] Prueba de equivalencia contra el estado real de todos los instantes, en `cripta/tests/test_linea_de_tiempo.py`
- [x] T007 [P] [H1] Pruebas de que consultar no altera nada, en `cripta/tests/test_linea_de_tiempo.py`
- [x] T008 [P] [H1] Pruebas de las acciones que actúan sobre el objeto que se ve, en `cripta/tests/test_linea_de_tiempo.py`

### Fase 3 — Historia 2: preguntar por algo que no pasó (P1)

- [x] T009 [P] [H2] Rechazo de consultas imposibles, en `cripta/model/consulta_historia.py` y sus pruebas

### Fase 4 — Historia 3: el pergamino recorta la línea (P2)

- [x] T010 [H3] El recorte y el anclaje del generador, en `cripta/model/game.py`
- [x] T011 [H3] Pruebas del recorte y de la re-simulación después de un pergamino, en `cripta/tests/test_linea_de_tiempo.py`

### Fase 5 — Historia 4: consultar sigue siendo barato (P2)

- [x] T012 [H4] Pruebas del límite de K acciones y de la búsqueda binaria, en `cripta/tests/test_linea_de_tiempo.py`

### Fase 6 — Historia 5: la historia sobrevive a guardar y cargar (P3)

- [x] T013 [H5] La línea en el archivo de partida y la versión 3, en `cripta/adapters/almacen_partida.py`
- [x] T014 [P] [H5] Pruebas de ida y vuelta de la línea, en `cripta/tests/test_almacen_partida.py`

### Fase 7 — Cierre

- [x] T015 El comando de consulta y la impresión del resumen, en `cripta/controller/commands.py` y `cripta/view/console_view.py`
- [x] T016 El banco de mediciones de la línea, en `cripta/benchmark/bench_linea_de_tiempo.py`
- [x] T017 Correr las mediciones, escoger el valor por omisión de K y anotarlo en `specs/003-linea-de-tiempo/plan.md`
- [x] T018 No romper nada: la suite completa
- [x] T019 Dejarle la interfaz lista a la Persona 4 para las dos banderas nuevas
- [x] T020 Registrar las invocaciones de spec-kit de esta capacidad, en `cripta/PROMPTS_LLM.md`

### Fase 8 — Historia 6: consultar una partida registrada sin jugarla (P3)

- [x] T021 [H6] `--replay --hasta` con un instante posterior al final muestra el estado final y avisa, en `cripta/controller/application.py` y `cripta/tests/test_banderas_linea_de_tiempo.py`

### Fase 9 — Pendientes de la auditoría de cierre

- [x] T022 [H1] Prueba del escenario 9 (varios eventos en el mismo instante, Apéndice B), en `cripta/tests/test_eventos_mismo_instante.py` — FR-002
- [ ] T023 [H1] La consulta de un instante entre dos decisiones del jugador no debe incluir eventos posteriores al instante: repetir la última acción deteniendo los eventos en *t*, en `cripta/model/consulta_historia.py` y `cripta/model/game.py`; al hacerlo, quitar el fallo esperado de `test_un_evento_posterior_al_instante_no_cuenta` — FR-002
- [x] T024 Medir la consulta con 5 000 acciones y *K* por omisión, y la alternativa sin puntos de control, en `cripta/benchmark/bench_linea_de_tiempo.py`; resultados en `cripta/docs/DECISIONES.md` §5.5 — FR-016, FR-017, §6.1 y §6.3

---

## T001 — La línea: acciones, copias, anclajes y búsqueda binaria

**Requisitos**: FR-003, FR-011, FR-015, FR-017, FR-018, FR-019

**Archivo**: `cripta/structures/linea_de_tiempo.py`

- Guardar tres listas contiguas: las acciones registradas (nombre, argumento, reloj al que ocurrieron), las copias completas (número de acción, reloj, bloque de bytes) y los anclajes del generador (número de acción, estado).
- Registrar una acción en O(1).
- Guardar una copia completa, con la regla de **no más de una cada K acciones**.
- Localizar la última copia en o antes de un número de acción, con **búsqueda binaria propia**. `bisect` está prohibido.
- Traducir un instante del reloj al número de acción correspondiente, también con búsqueda binaria, respetando FR-002: cuentan todos los eventos de tiempo menor o igual que el pedido, y si al instante le corresponde una decisión del jugador es el estado justo antes de tomarla.
- Recortar: quitar la última acción y, si la última copia era de esa acción, quitarla también. **Trabajo constante, no un recorrido.**
- Informar cuánta memoria ocupa, separando lo que pesan las copias, las acciones y los anclajes, para que la medición pueda reportarlo desglosado.
- **No reconstruye nada**: esta estructura no conoce el motor.

**Verificable cuando**: con K=10 y 35 acciones hay 4 copias; la búsqueda binaria encuentra la copia correcta para cualquier número de acción, incluidos los extremos; recortar quita una acción y a lo sumo una copia; una línea vacía responde sin fallar.

---

## T002 — Pruebas de la línea [P]

**Requisitos**: FR-003, FR-015, FR-017, FR-018, FR-019

**Archivo**: `cripta/tests/test_linea_de_tiempo.py`

Cubrir, sin tocar el motor, con bloques de bytes falsos:

- Línea vacía: ninguna copia, ninguna acción.
- La regla de una copia cada K, para K=1, K=10 y K mayor que el total.
- La búsqueda binaria: número de acción exacto de una copia, entre dos copias, antes de la primera, después de la última.
- La traducción de un instante del reloj al número de acción, incluidos un instante que cae sobre una acción y uno entre dos.
- Recortar: con y sin copia en la última acción, y varias veces seguidas.
- El desglose de memoria suma lo que ocupan las tres listas.

**Depende de**: T001

---

## T003 — Separar el armado del contenido de su escritura

**Requisitos**: FR-016, FR-020

**Archivo**: `cripta/adapters/almacen_partida.py`

Hoy `guardar` construye el contenido completo en memoria y después lo escribe de una vez. Hay que separar las dos cosas, para que un punto de control sea ese mismo bloque de bytes **sin pasar por disco**, y poder volver a leerlo desde memoria.

Es refactor: **no cambia ningún comportamiento** y las pruebas del guardado deben seguir pasando sin tocarlas.

**Verificable cuando**: armar el contenido y escribirlo produce el mismo archivo que antes; leer desde un bloque en memoria da la misma partida que leer desde el archivo; las pruebas del guardado pasan sin modificarse.

---

## T004 — El motor registra cada acción del jugador y pide copias

**Requisitos**: FR-003, FR-015, FR-016

**Archivo**: `cripta/model/game.py`

- En `_finish_player_action`, que es el **único** embudo de toda acción aceptada que consume tiempo, registrar en la línea el nombre de la acción y su argumento.
- Para soltar, usar y equipar, el argumento es **el identificador del objeto**, no su posición ni el cursor: el cursor lo mueven comandos que no son acciones, así que la posición no se puede repetir.
- Cada K acciones, pedir una copia completa del estado.
- La línea se recibe **desde afuera**, como la bitácora y el historial. Una partida sin línea debe seguir funcionando exactamente igual.
- Las acciones **rechazadas** no llegan al embudo y por lo tanto no entran en la línea.

**Verificable cuando**: una partida de 25 acciones con K=10 deja 25 acciones y 3 copias en la línea; una acción rechazada no agrega nada; una partida construida sin línea se juega igual que antes.

**Depende de**: T001, T003

---

## T005 — La reconstrucción y el resumen [H1]

**Requisitos**: FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-008, FR-014, FR-016, FR-022, FR-023

**Archivo**: `cripta/model/consulta_historia.py`

- Reconstruir la copia más cercana **en objetos nuevos**, por el camino de carga que ya existe y que no rehace el trabajo de inicio de partida.
- Repetir a lo sumo K acciones del jugador sobre ese motor reconstruido, aplicando los anclajes del generador que se cruce.
- Para soltar, usar y equipar, poner el cursor sobre el objeto por su identificador antes de ejecutar.
- Armar el motor reconstruido **sin bitácora y sin repositorio**, para que repetir no pueda escribir en la bitácora ni provocar ninguna solicitud.
- Devolver el resumen como **dato, no como texto**: reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida, y el mapa conocido.
- El mapa conocido se obtiene de quien lo tenga. Mientras la niebla de guerra no exista, el resumen informa que ese dato no está disponible y se construye igual.
- **No instancia la vista** y **no toca la partida viva**: FR-005 a FR-008 salen por construcción.

**Verificable cuando**: el resumen de un instante coincide con el estado real de ese instante; dos consultas del mismo instante dan lo mismo; después de consultar, la partida viva está idéntica.

**Depende de**: T004

---

## T006 — Prueba de equivalencia contra el estado real [H1]

**Requisitos**: FR-001, FR-002, FR-023

**Archivo**: `cripta/tests/test_linea_de_tiempo.py`

**La prueba central de la capacidad.** No compara contra valores escritos a mano: juega una partida larga guardando en cada acción el estado real observable, y después consulta **todos** los instantes y exige que cada resumen coincida con lo que de verdad hubo.

Es la técnica que en la capacidad del cazador destapó dos errores propios, y aquí es la única forma de detectar una divergencia del generador aleatorio, que no se ve de ninguna otra manera.

Incluir: una partida con combate, con veneno, con cambios de velocidad, con puertas que se cierran solas y con objetos recogidos y soltados, para que haya azar de verdad en juego.

**Depende de**: T005

---

## T007 — Pruebas de que consultar no altera nada [P] [H1]

**Requisitos**: FR-005, FR-006, FR-007, FR-008

**Archivo**: `cripta/tests/test_linea_de_tiempo.py`

Después de cien consultas seguidas: el reloj, la vida, el inventario, la agenda de eventos, los efectos activos, el contador de acciones del jugador y **las acciones que quedan por revertir con el pergamino** son exactamente los de antes (SC-003).

Comprobar además que una consulta no agrega nada a la bitácora de reproducción.

**Depende de**: T005

---

## T008 — Pruebas de las acciones que actúan sobre el objeto que se ve [P] [H1]

**Requisitos**: FR-023

**Archivo**: `cripta/tests/test_linea_de_tiempo.py`

El caso que el plan señala como el más fácil de arruinar. Jugar moviendo el cursor del inventario con los comandos que **no** son acciones y después soltar, usar y equipar; luego consultar y exigir que el resumen refleje el objeto correcto.

Una implementación que registrara la posición en vez del identificador del objeto tiene que fallar aquí.

**Depende de**: T005

---

## T009 — Rechazo de consultas imposibles [P] [H2]

**Requisitos**: FR-009, FR-010

**Archivos**: `cripta/model/consulta_historia.py`, `cripta/tests/test_linea_de_tiempo.py`

- **Escenario obligatorio del Apéndice B**: un instante posterior al reloj actual se rechaza con un mensaje que lo explica.
- Un número de acción que el jugador no ha tomado se rechaza.
- Un instante negativo o un valor que no es entero se rechaza.
- El instante **exacto** del reloj actual **sí** se acepta: el enunciado solo prohíbe el posterior.
- El instante 0 se acepta y da el estado inicial.
- Una consulta rechazada no consume tiempo ni cuenta como acción.

**Depende de**: T005

---

## T010 — El recorte y el anclaje del generador [H3]

**Requisitos**: FR-011, FR-012, FR-019

**Archivo**: `cripta/model/game.py`

- Al usar un pergamino, recortar la línea: la acción revertida deja de existir.
- **Anotar el estado del generador aleatorio** en ese punto. Es el agujero que el plan identificó: el pergamino devuelve el reloj pero no el generador, así que sin este anclaje la re-simulación divergiría de la partida viva y los resúmenes posteriores serían falsos.
- Un anclaje por pergamino usado, **no por acción**: el estado de un generador son unos 5 KB.
- El pergamino sigue limitado a cinco acciones. La línea **no** amplía ese límite.

**Verificable cuando**: después de un pergamino la línea tiene una acción menos; el instante revertido ya no es consultable; hay exactamente un anclaje por pergamino usado.

**Depende de**: T004

---

## T011 — Pruebas del recorte y de la re-simulación tras un pergamino [H3]

**Requisitos**: FR-011, FR-012, FR-013, FR-019

**Archivo**: `cripta/tests/test_linea_de_tiempo.py`

- **Escenario obligatorio del Apéndice B**: consultar después de un pergamino no muestra la acción revertida.
- **La prueba que justifica el anclaje**: jugar, usar un pergamino, seguir jugando, y consultar instantes **posteriores** al pergamino exigiendo que coincidan con el estado real. Sin el anclaje del generador esta prueba tiene que fallar.
- Varios pergaminos seguidos dejan la línea consistente.
- Después de un pergamino, las acciones nuevas se registran y se pueden consultar.
- La línea cubre más allá de las cinco acciones del pergamino (FR-013).

**Depende de**: T010

---

## T012 — Pruebas del límite de K acciones y de la búsqueda binaria [H4]

**Requisitos**: FR-016, FR-018

**Archivo**: `cripta/tests/test_linea_de_tiempo.py`

- Responder cualquier consulta repite **a lo sumo K** acciones del jugador. Se comprueba contando cuántas repite, no estimando.
- La localización de la copia no examina todas las copias.
- Con K mayor que el total de acciones hay una sola copia y las consultas siguen siendo correctas.
- Con K=1 las consultas no repiten ninguna acción.

**Depende de**: T005

---

## T013 — La línea en el archivo de partida y la versión 3 [H5]

**Requisitos**: FR-020, FR-021

**Archivo**: `cripta/adapters/almacen_partida.py`

- Guardar la línea completa en el archivo: acciones, copias y anclajes.
- Leerla al cargar, de modo que después de cargar se pueda consultar cualquier instante desde el inicio.
- **Subir la versión del formato de 2 a 3.** Un archivo de la primera parte, y también uno de la capacidad anterior, se rechazan por versión con el mensaje que el módulo ya da.

**Verificable cuando**: guardar y cargar conserva la línea; una consulta después de cargar da el mismo resumen que antes de guardar; un archivo de versión 2 se rechaza nombrando las dos versiones.

**Depende de**: T004, T005

---

## T014 — Pruebas de ida y vuelta de la línea [P] [H5]

**Requisitos**: FR-020, FR-021

**Archivo**: `cripta/tests/test_almacen_partida.py`

Cubrir los tres casos de T013, más que seguir jugando después de cargar deje la línea sin cortes.

**Depende de**: T013

---

## T015 — El comando de consulta y la impresión del resumen

**Requisitos**: FR-003, FR-004

**Archivos**: `cripta/controller/commands.py`, `cripta/view/console_view.py`

- El comando de consulta, en sus dos formas: por instante del reloj y por número de acción del jugador.
- El comando **no** es una acción del juego, así que no entra en la bitácora de reproducción ni consume tiempo.
- La vista imprime el resumen que el modelo devolvió como dato. La vista no decide qué va en el resumen; el modelo no decide cómo se ve.
- Agregarlo a la lista de ayuda.

**Verificable cuando**: el comando se interpreta en las dos formas; un texto mal escrito da un error legible; el comando no aparece en la bitácora.

**Depende de**: T005

---

## T016 — El banco de mediciones de la línea

**Requisitos**: FR-017, FR-024

**Archivo**: `cripta/benchmark/bench_linea_de_tiempo.py`

Registrado en `--bench`, con criptas sintéticas deterministas por semilla:

1. Memoria y tiempo de consulta para **K = 1, 10, 50 y 200**. K=1 es la alternativa ingenua, una copia por acción, y es la referencia contra la que se mide el ahorro. La memoria se reporta **desglosada**: copias, acciones y anclajes.
2. El costo de una consulta en partidas de 50, 200 y 500 acciones, con K fijo. Debe quedar plano (SC-002).
3. El recorte por pergamino en partidas de 50 y 500 acciones. Debe quedar plano (SC-008).
4. El ciclo de eventos con la línea activa, contra los 0.1854 ms actuales y el límite de 20 ms.

El principio VI no permite escoger el valor por omisión de K sin los números que lo respalden, y pide medir la alternativa descartada: por eso K=1 se mide.

**Depende de**: T005

---

## T017 — Correr las mediciones y escoger K

**Requisitos**: FR-015, FR-017

**Archivo**: `specs/003-linea-de-tiempo/plan.md`

Correr los cuatro escenarios, anotar los números con la máquina, la versión de Python y la fecha, **escoger el valor por omisión de K y justificarlo con esos números**, como exige §3.6.

Si el resultado contradice lo que el plan esperaba, se escribe tal cual.

**Depende de**: T016

---

## T018 — No romper nada

**Requisitos**: FR-012

Correr la suite completa. Las 945 pruebas anteriores deben seguir pasando, más las nuevas.

La única excepción prevista son las pruebas del guardado que fijan la versión del formato, por T013, que es la excepción que SC-010 admite. Si en T003 se rompe alguna prueba del guardado, el refactor quedó mal: T003 no cambia ningún comportamiento.

**Depende de**: todas las anteriores

---

## T019 — Dejarle la interfaz lista a la Persona 4

**Requisitos**: FR-014, FR-015

**Archivo**: una nota en `cripta/docs/`

Las dos banderas nuevas son de la Persona 4: `--checkpoint-cada K` y `--replay ... --hasta t`. Esta tarea no las implementa: deja escrito qué llamar, qué devuelve y qué no hay que hacer, para que conectarlas sea trabajo mecánico y no haya que leer este plan completo.

Incluir el aviso de que el formato del archivo de partida subió a la versión 3.

**Depende de**: T005

---

## T020 — Registrar las invocaciones de spec-kit

**Requisitos**: ninguno del juego; lo exige la constitución

**Archivo**: `cripta/PROMPTS_LLM.md`

Las entradas de las capacidades anteriores van de 2.25 a 2.29; estas continúan la numeración.

**Depende de**: T018

---

## T021 — `--replay --hasta` después del final [H6]

**Requisitos**: FR-025 (Historia 6, escenario 1, Apéndice B), FR-009 sin cambios

**Archivos**: `cripta/controller/application.py`, `cripta/tests/test_banderas_linea_de_tiempo.py`

Agregada después del cierre, cuando una auditoría encontró que este caso del Apéndice B no tenía escenario y que el programa rechazaba el instante. La especificación se corrigió primero, en un commit aparte. La bandera es de la integración, así que el arreglo vive en `replay()` y no toca la línea, la consulta ni el archivo de partida: si el instante pedido es posterior al reloj final, avisa y consulta el reloj final, que ya es consultable. El instante final exacto se muestra sin aviso y un instante negativo se sigue rechazando.

**Depende de**: T019

---

## Orden sugerido

```
T001 ──┬── T002
       └── T004 ──┬── T005 ──┬── T006
T003 ──────┘      │          ├── T007
                  │          ├── T008
                  │          ├── T009
                  │          ├── T012
                  │          ├── T015
                  │          ├── T016 ── T017
                  │          ├── T019
                  │          └── T013 ── T014
                  └── T010 ── T011
                                 └── T018 ── T020
```

T001 y T003 son independientes entre sí y los dos desbloquean T004. T005 desbloquea casi todo lo demás.

## Lo mínimo que ya sirve

Con T001 a T007 la capacidad ya responde consultas correctas y comprobadas, sin alterar la partida. Las Historias 2 y 3 son condición para entregar: sin el rechazo de lo imposible y sin el recorte por pergamino, los dos casos obligatorios del Apéndice B quedan sin cubrir.

## Qué le toca al resto del equipo

- **Persona 4**: las dos banderas nuevas, con la interfaz que deja T019. También el aviso de la versión 3 del formato de partida, que invalida los guardados anteriores.
- **Steven**: cuando exista la niebla de guerra, el resumen debe incluir el mapa conocido del instante. Esta capacidad lo deja previsto y lo reporta como no disponible mientras no exista; conectarlo será agregar una lectura, no rediseñar nada.
