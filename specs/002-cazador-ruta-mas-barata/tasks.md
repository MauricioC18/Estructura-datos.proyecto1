# Tareas: El cazador, un enemigo que persigue por la ruta más barata

**Especificación**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Cada tarea referencia los requisitos que atiende. No hay tareas sin requisito.

Las tareas marcadas con **[P]** pueden hacerse en paralelo con la anterior porque tocan archivos distintos. Las etiquetas **[H1]**–**[H5]** remiten a las historias de la especificación.

## Lista

### Fase 1 — Base, bloquea todo lo demás

- [x] T001 La búsqueda de costos mínimos, en `cripta/structures/rutas_mas_baratas.py`
- [x] T002 [P] Pruebas de la búsqueda, en `cripta/tests/test_rutas_mas_baratas.py`
- [x] T003 El comportamiento cazador y su rango, en `cripta/model/enemy.py`
- [x] T004 [P] El traductor lee el cazador y su rango, en `cripta/repository/traductor.py`
- [x] T005 [P] Pruebas del traductor, en `cripta/tests/test_traductor.py`
- [x] T006 El motor le pasa al cazador las vecinas abiertas, en `cripta/model/game.py`

### Fase 2 — Historia 1: persigue por donde le cuesta menos (P1)

- [x] T007 [H1] Pruebas de la persecución, en `cripta/tests/test_cazador.py`

### Fase 3 — Historia 2: dos rutas igual de baratas (P1)

- [x] T008 [P] [H2] Pruebas del desempate y del determinismo, en `cripta/tests/test_cazador.py`

### Fase 4 — Historia 3: el rango (P2)

- [x] T009 [P] [H3] Pruebas del rango y de la espera, en `cripta/tests/test_cazador.py`

### Fase 5 — Historia 4: la decisión se recalcula (P2)

- [x] T010 [H4] Invalidar el cálculo compartido, en `cripta/model/game.py`
- [x] T011 [H4] Prueba de equivalencia contra recalcular siempre, en `cripta/tests/test_cazador.py`

### Fase 6 — Historia 5: sigue siendo un enemigo como los otros (P3)

- [x] T012 [P] [H5] Pruebas de activación y de no regresión, en `cripta/tests/test_cazador.py`

### Fase 7 — Cierre

- [x] T013 El guardado binario guarda el rango y sube de versión, en `cripta/adapters/almacen_partida.py`
- [x] T014 El banco de mediciones de la persecución, en `cripta/benchmark/`
- [x] T015 Correr las cuatro mediciones y anotarlas en `specs/002-cazador-ruta-mas-barata/plan.md`
- [x] T016 No romper nada: la suite completa
- [ ] T017 Registrar las invocaciones de spec-kit de esta capacidad, en `cripta/PROMPTS_LLM.md`

---

## T001 — La búsqueda de costos mínimos

**Requisitos**: FR-004, FR-007, FR-008, FR-010, FR-017

**Archivo**: `cripta/structures/rutas_mas_baratas.py`

- Recibir desde afuera un proveedor de vecinas: dada una sala, devuelve las vecinas alcanzables con el costo de la salida que lleva a cada una, contando **solo** las salidas cuya puerta está abierta en ese instante. La estructura no importa nada del modelo.
- Buscar los costos mínimos **desde una sala de origen**, que será la del jugador, con un **corte**: dejar de expandir en cuanto la distancia pasa del corte.
- Usar como cola de prioridad el montículo de `cripta/structures/event_queue.py`, entregándole candidatas que ordenen por `(distancia, id de sala)`. Sin «disminuir clave»: insertar de nuevo y descartar al extraer las salas ya asentadas, igual que la agenda descarta eventos cancelados.
- Guardar distancias y salas asentadas en `TablaHash`. **Ni `dict` ni `set`.**
- Exponer el costo mínimo hasta una sala, o que quedó fuera del corte.
- Cuando una misma vecina aparece por **dos salidas abiertas distintas** con costos distintos, quedarse con la más barata (FR-008). Así la búsqueda no necesita saber nada del caso.
- Exponer el **primer paso** desde una sala hacia el origen: entre sus vecinas `v` con `costo(sala, v) + distancia(v) = d`, la de **menor id**. El desempate se aplica aquí, sobre las vecinas, **no** se deja al orden de expansión del montículo.

**Verificable cuando**: en un grafo armado a mano, las distancias coinciden con las calculadas a mano; una ruta de más aristas y menor peso gana sobre una de menos aristas y mayor peso; las salas más allá del corte quedan sin distancia; con dos vecinas empatadas, el primer paso es la de menor id; una arista cerrada no se cuenta.

---

## T002 — Pruebas de la búsqueda [P]

**Requisitos**: FR-004, FR-007, FR-008, FR-010, FR-017

**Archivo**: `cripta/tests/test_rutas_mas_baratas.py`

Cubrir, con proveedores de vecinas escritos a mano y sin tocar el modelo:

- Grafo de un solo nodo, y origen igual a destino: distancia 0 y sin primer paso.
- Más aristas y menor peso gana (SC-001).
- Corte: una sala justo en el corte queda dentro; una un paso más allá, fuera.
- Desempate con dos y con varias vecinas empatadas, en una topología donde el orden de expansión y el id dan respuestas distintas, para que una implementación que confíe en el montículo falle.
- Aristas cerradas no se cuentan, y el grafo partido en dos deja el otro lado sin distancia.
- Pesos de 1 y pesos muy grandes, sin desbordes ni ceros.
- Dos aristas abiertas distintas hacia el mismo vecino con pesos distintos: cuenta la más barata, en la distancia y en el primer paso (FR-008).

**Depende de**: T001

---

## T003 — El comportamiento cazador y su rango

**Requisitos**: FR-001, FR-002, FR-003, FR-005, FR-006, FR-007, FR-013, FR-015

**Archivo**: `cripta/model/enemy.py`

- Agregar la constante del cuarto comportamiento, junto a guardián, errante y rastreador.
- Agregar el rango como atributo del enemigo, con un valor neutro para los que no son cazadores, y rechazar un rango que no sea entero mayor o igual que 0.
- Decidir: si comparte sala con el jugador, atacar (ya lo hace la regla común y tiene prioridad); si no, pedir el primer paso a la búsqueda que recibe como colaborador y moverse por él; si no hay primer paso, o la distancia pasa de su rango, esperar.
- El cazador **no** recibe el mapa ni lo conoce: recibe la búsqueda ya hecha, igual que el rastreador recibe el rastro.
- **No tocar** `_wander` ni `_track`, ni la regla de compartir sala.
- El colaborador de búsqueda entra en la firma de la decisión **al final y con valor por omisión**: hay diez llamadas directas a esa firma en `tests/test_movement.py`, varias posicionales, y ninguna debe romperse.

**Verificable cuando**: un cazador que comparte sala ataca; uno con primer paso disponible se mueve por él; uno sin primer paso espera; uno cuya distancia pasa de su rango espera; uno con distancia igual a su rango se mueve; un rango inválido se rechaza al construir.

**Depende de**: T001

---

## T004 — El traductor lee el cazador y su rango [P]

**Requisitos**: FR-001, FR-002, FR-014

**Archivo**: `cripta/repository/traductor.py`

- Agregar el cazador a la tabla que traduce el comportamiento del API al del modelo, con el texto que usa el enunciado.
- Agregar `rango` a los campos permitidos de la ficha de enemigo, para que deje de avisarse como campo desconocido.
- Leer el rango de la ficha y pasarlo al enemigo.
- Una ficha de cazador **sin** rango, o con un rango que no sea entero mayor o igual que 0, entra por el camino de error de datos de cripta que ya existe. **No se sustituye por un valor por omisión.**
- Una ficha que **no** es de cazador y declara rango: se avisa y se ignora.

**Verificable cuando**: una ficha con comportamiento de cazador y rango 600 produce un cazador de rango 600; una de cazador sin rango se reporta como error de datos; una de cazador con rango -1 o con texto se reporta como error; `rango` ya no aparece en la lista de avisos por campo desconocido; una ficha de errante con rango produce un aviso y un errante.

**Depende de**: T003

---

## T005 — Pruebas del traductor [P]

**Requisitos**: FR-001, FR-002, FR-014

**Archivo**: `cripta/tests/test_traductor.py`

Cubrir los cinco casos de T004.

**Depende de**: T004

---

## T006 — El motor le pasa al cazador las vecinas abiertas

**Requisitos**: FR-004, FR-007, FR-009, FR-012

**Archivo**: `cripta/model/game.py`

- Armar el proveedor de vecinas abiertas sobre el mapa de salas real del motor: para una sala, sus salidas con puerta abierta y el costo de cada una.
- Hacer la búsqueda desde la sala **del jugador**, con el corte en el rango más grande entre los cazadores activos, y pasarla al enemigo en su turno.
- El movimiento del cazador cuesta el costo de la salida que atraviesa, que es el camino que ya existe para el movimiento de cualquier enemigo; la espera cuesta lo que ya cuesta esperar.
- La búsqueda **no** consulta si el contenido de una sala fue descargado ni provoca ninguna solicitud.

**Verificable cuando**: un cazador en una partida real se mueve hacia el jugador; su siguiente turno se programa con el costo de la salida que atravesó; una partida con un cazador no hace ninguna solicitud más que una partida igual sin cazador.

**Depende de**: T001, T003

---

## T007 — Pruebas de la persecución [H1]

**Requisitos**: FR-003, FR-004, FR-007, FR-009, FR-010, FR-012

**Archivo**: `cripta/tests/test_cazador.py`

Cubrir, en partidas reales con el motor:

- Un cazador que comparte sala con el jugador ataca y no se mueve.
- **Escenario obligatorio del Apéndice B**: con una ruta de dos salas y costo 500 y otra de cuatro salas y costo 200, el cazador toma la de 200 (SC-001).
- El costo del turno es el costo de la salida atravesada, no un valor fijo.
- Una salida cerrada no se cuenta aunque sea el camino más corto.
- El cazador decide igual tenga o no el jugador explorada esa parte del mapa, y sin provocar solicitudes.
- **Caso borde**: el cazador que **entra** a la sala del jugador en su movimiento no ataca ese turno; ataca en el siguiente, cuando ya comparte sala.
- **Caso borde**: la partida termina mientras un cazador tiene turno programado, sin que aparezca ninguna regla nueva.

Las pruebas citan en su nombre o en su docstring el requisito que ejercitan.

**Depende de**: T006

---

## T008 — Pruebas del desempate y del determinismo [P] [H2]

**Requisitos**: FR-008, FR-016

**Archivo**: `cripta/tests/test_cazador.py`

- **Escenario obligatorio del Apéndice B**: dos vecinas inician rutas de costo mínimo idéntico y el cazador va a la de menor id (SC-002).
- Una cripta donde hay muchas rutas distintas del mismo costo mínimo: el desempate se cumple igual.
- La misma cripta y la misma semilla, jugadas dos veces, dan las mismas decisiones del cazador en los mismos instantes.
- **Caso borde**: varios cazadores en la misma sala deciden todos lo mismo, porque el desempate no depende de quién pregunta.
- La cripta de estas pruebas se construye para que el id de la vecina correcta **no** coincida con el orden en que el montículo expandiría las salas.

**Depende de**: T006

---

## T009 — Pruebas del rango y de la espera [P] [H3]

**Requisitos**: FR-005, FR-006

**Archivo**: `cripta/tests/test_cazador.py`

- **Escenario obligatorio del Apéndice B**: sin ruta abierta hacia el jugador, el cazador espera y la espera le cuesta 100.
- **Escenario obligatorio del Apéndice B**: con ruta más barata de 700 y rango 600, espera y la espera le cuesta 100.
- Con ruta más barata igual al rango, se mueve: el rango es el costo máximo aceptado.
- Rango 0 con el jugador en otra sala: espera siempre. Rango 0 compartiendo sala: ataca.
- El siguiente turno de un cazador que espera se programa con el costo 100 y su velocidad (SC-003).

**Depende de**: T006

---

## T010 — Invalidar el cálculo compartido [H4]

**Requisitos**: FR-011

**Archivo**: `cripta/model/game.py`

- Reutilizar la búsqueda entre turnos de cazador mientras siga siendo válida.
- Invalidarla cuando el **jugador cambia de sala** y cuando **una puerta se abre o se cierra**, incluido el **cierre automático**, que lo dispara la agenda y no una acción del jugador.
- **No** invalidar por el movimiento de un cazador, la muerte de un actor ni un cambio de velocidad: ninguno de los tres cambia la sala del jugador ni el estado de las puertas, así que ninguno puede cambiar la respuesta. Esto se justifica en el plan y es lo que la prueba T011 tiene que confirmar.
- Dejar un modo de **recalcular siempre**, sin reutilizar nada, alcanzable desde las pruebas y desde el banco de mediciones. Ese modo es la definición de «decidir desde cero» de FR-011.

**Verificable cuando**: cerrar una puerta de la ruta cambia la decisión del siguiente turno; abrir una puerta que acorta el camino también; mover al jugador también; mover otro cazador no provoca una búsqueda nueva.

**Depende de**: T006

---

## T011 — Prueba de equivalencia contra recalcular siempre [H4]

**Requisitos**: FR-011

**Archivo**: `cripta/tests/test_cazador.py`

**Escenario obligatorio del Apéndice B**: una puerta de la ruta del cazador se cierra entre dos de sus turnos y en el siguiente turno decide como si calculara desde cero.

La prueba central **no compara contra valores escritos a mano**: corre la misma partida, con la misma semilla y las mismas acciones, en modo compartido y en modo recalcular siempre, y exige que las decisiones de los cazadores sean idénticas turno por turno (SC-004). Incluir al menos una partida con cierres automáticos frecuentes, porque es el evento que más fácil se olvida invalidar.

Cubrir además: la única ruta cortada por una puerta que se cerró deja al cazador esperando; una puerta recién abierta le hace tomar la ruta nueva; el jugador que se mueve entre dos turnos del cazador hace que persiga la sala nueva.

**Depende de**: T010

---

## T012 — Pruebas de activación y de no regresión [P] [H5]

**Requisitos**: FR-013, FR-015

**Archivo**: `cripta/tests/test_cazador.py`

Las tareas preveían `tests/test_enemy.py`, que no existe: los tres comportamientos de la primera parte se prueban en `tests/test_movement.py`. Estas pruebas quedaron junto a las demás del cazador, y las de los otros tres comportamientos siguen donde estaban.

- Un cazador que todavía no se ha activado no persigue ni consume turnos.
- Un cazador no abre una puerta cerrada, aunque fuera el camino más barato si estuviera abierta.
- Guardián, errante y rastreador conservan su lógica de decisión: las pruebas que ya existen para los tres siguen pasando sin modificarlas, y el cazador no usa el rastro.

**Depende de**: T003

---

## T013 — El guardado binario guarda el rango y sube de versión

**Requisitos**: FR-002, FR-016

**Archivos**: `cripta/adapters/almacen_partida.py`, `cripta/tests/test_almacen_partida.py`

El bloque de cada enemigo ya guarda su comportamiento; tiene que guardar también su rango, o un cazador cargado perseguiría con un rango inventado y la partida cargada no sería la misma que la guardada.

- Agregar el rango al bloque de enemigo, al escribir y al leer.
- **Subir la versión del formato de 1 a 2.** Un archivo de la versión 1 se rechaza con el mensaje que el módulo ya da; no se intenta leerlo a medias.

**Verificable cuando**: guardar y cargar una partida con un cazador devuelve el mismo rango; un archivo de la versión 1 se rechaza con un mensaje que nombra las dos versiones; la partida cargada toma las mismas decisiones que la original.

**Depende de**: T003

---

## T014 — El banco de mediciones de la persecución

**Requisitos**: FR-017, FR-018

**Archivo**: `cripta/benchmark/`

Un módulo nuevo, registrado en `--bench`, con criptas sintéticas deterministas por semilla y los tres modos de cálculo del plan: compartido con invalidación, uno por cazador y recalcular siempre.

Los cuatro escenarios:

1. Rango fijo y pequeño en criptas de tamaño creciente (FR-017, SC-005).
2. Cantidad creciente de cazadores activos persiguiendo al mismo jugador, en modo compartido y en modo por cazador (SC-008). Incluir un caso de **rangos muy desiguales**, donde el corte compartido es el rango mayor, para medir lo que paga el cazador de rango pequeño: FR-017 ahora obliga a reportar ese sobrecosto.
3. Una cripta con cierres automáticos frecuentes y otra casi sin ellos, en modo compartido y en modo recalcular siempre (SC-007).
4. El ciclo completo de eventos entre dos decisiones del jugador con **al menos 50 cazadores activos** (FR-018, SC-006).

El principio VI de la constitución no permite afirmar que compartir el cálculo convenga sin los números que lo respalden, y pide medir las alternativas descartadas. Por eso los tres modos se implementan, no solo el elegido.

**Depende de**: T010

---

## T015 — Correr las mediciones y anotarlas

**Requisitos**: FR-017, FR-018

**Archivo**: `specs/002-cazador-ruta-mas-barata/plan.md`

Correr los cuatro escenarios y anotar los números en el plan, con la máquina, la versión de Python y la fecha, igual que en la capacidad 001.

**Si el resultado contradice lo que el plan esperaba, se escribe tal cual.** Si recalcular siempre resulta competitivo en la escala de estas criptas, eso es el hallazgo y hay que decirlo, no esconderlo.

**Depende de**: T014

---

## T017 — Registrar las invocaciones de spec-kit

**Requisitos**: ninguno del juego; lo exige la constitución

**Archivo**: `cripta/PROMPTS_LLM.md`

La constitución, en «Cómo se trabaja», obliga a registrar cada invocación de un comando de spec-kit con texto propio, con fecha, herramienta, el texto enviado y para qué se usó la respuesta. Esta capacidad invocó `specify`, `plan`, `tasks`, `analyze` e `implement`, y la revisión de consistencia dejó además correcciones a la especificación que conviene anotar.

Las entradas de la capacidad 001 están en 2.25 y 2.26; estas continúan esa numeración.

**Verificable cuando**: cada invocación de spec-kit de esta capacidad tiene su entrada, con el texto enviado y el uso que se le dio, y ninguna queda con un marcador por rellenar.

**Depende de**: T016

---

## T016 — No romper nada

**Requisitos**: FR-013, FR-016

Correr la suite completa. Las 882 pruebas anteriores deben seguir pasando, más las nuevas.

Una prueba vieja que falle por el rango nuevo es señal de que T003 quedó mal, no de que la prueba esté desactualizada. La única excepción prevista son las pruebas del guardado binario que fijen la versión 1 del formato: esas sí cambian, por T013. Es la excepción que SC-009 admite, y ninguna otra.

**Depende de**: todas las anteriores

---

## Orden sugerido

```
T001 ──┬── T002
       ├── T003 ──┬── T004 ── T005
       │          ├── T012
       │          └── T013
       └── T006 ──┬── T007
                  ├── T008
                  ├── T009
                  └── T010 ──┬── T011
                             └── T014 ── T015
                                            └── T016 ── T017
```

T001 y T003 desbloquean todo lo demás. T001 se puede probar entera sin el modelo, así que conviene dejarla firme antes de tocar el motor: es donde está el algoritmo y donde un error se diagnostica más fácil.

## Lo mínimo que ya sirve

Con la Fase 1 y la Historia 1 (T001–T007) el cazador ya persigue por la ruta más barata y los dos casos del Apéndice B sobre costo quedan cubiertos. Las Historias 2 y 3 son condición para entregar: sin el desempate no hay determinismo y sin el rango la cripta no se puede jugar.

## Qué desbloquea esta capacidad para el resto del equipo

- **Steven**, el viaje automático «ir a» (§3.4): la búsqueda de T001 queda parametrizada por quién provee las vecinas, así que puede usarla pasándole el mapa conocido del jugador en lugar del mapa real. Si le conviene compartirla o separarla es decisión de su plan, y el plan de esta capacidad explica por qué queda abierta esa puerta.
- **Mauricio A.**, el traductor: el campo `rango` de la ficha de catálogo queda leído y validado por T004, así que no tiene que agregarlo él.
