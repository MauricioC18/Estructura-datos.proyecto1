# Tareas: Terreno, costo de tránsito de las salidas

**Especificación**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Cada tarea referencia los requisitos que atiende. No hay tareas sin requisito.

Las tareas marcadas con **[P]** pueden hacerse en paralelo con la anterior porque tocan archivos distintos.

---

## T001 — El costo vive en la puerta

**Requisitos**: FR-001, FR-002, FR-003

**Archivo**: `cripta/model/room.py`

- Agregar a `Door` un atributo de costo de tránsito.
- Definir el valor por omisión como una constante con nombre, en un solo lugar.
- Exponer el costo desde `Exit`, para que quien tenga una salida no tenga que saber que el dato está en la puerta.
- Rechazar un costo que no sea entero mayor o igual que 1, con un mensaje que diga qué se recibió.

**Verificable cuando**: construir una puerta sin costo da 100; construir una con costo 250 da 250; las dos salidas que comparten una puerta informan el mismo costo; un costo de 0 o negativo se rechaza.

---

## T002 — Pruebas del costo en el modelo

**Requisitos**: FR-001, FR-002, FR-003

**Archivo**: `cripta/tests/test_room.py`

Cubrir: valor por omisión, costo declarado, igualdad en ambos sentidos desde el objeto compartido, y rechazo de valores inválidos.

**Depende de**: T001

---

## T003 — El traductor lee el costo del esqueleto

**Requisitos**: FR-001, FR-002, FR-003, FR-011

**Archivo**: `cripta/repository/traductor.py`

- Agregar `costo` a `CAMPOS_DE_SALIDA`, para que deje de avisarse como campo desconocido.
- Leerlo de cada salida y pasarlo a la puerta.
- Cuando los dos lados declaran costos distintos, resolverlo con `_combinar`, el mismo mecanismo que ya se usa para la llave y el cierre automático.
- Un costo malformado entra por el camino de error de datos de cripta que ya existe. **No se sustituye por 100 en silencio.**

**Verificable cuando**: una salida con `"costo": 250` produce una puerta de costo 250; una sin el campo produce 100; dos lados con costos distintos producen un aviso; un costo inválido se reporta como error de datos.

**Depende de**: T001

---

## T004 — Pruebas del traductor [P]

**Requisitos**: FR-001, FR-002, FR-003, FR-011

**Archivo**: `cripta/tests/test_traductor.py`

Cubrir los cuatro casos de T003, más que el campo `costo` ya no aparezca en la lista de avisos por campo desconocido.

**Depende de**: T003

---

## T005 — Moverse cuesta lo que cuesta la salida

**Requisitos**: FR-004, FR-005, FR-006, FR-007, FR-008, FR-012

**Archivo**: `cripta/model/game.py`

- En el movimiento del jugador, usar el costo de la salida que atraviesa en lugar de la constante fija.
- Hacer lo mismo en el movimiento del enemigo, para que valga para todos los actores.
- No tocar el costo de atacar, esperar, recoger, soltar, usar, equipar ni abrir puertas.
- No tocar la lógica de decisión de guardián, errante ni rastreador.

`Actor.interval_for()` ya aplica el mínimo de 1, así que FR-008 se cumple sin cambiarlo.

**Verificable cuando**: atravesar una salida de costo 50 adelanta el reloj 50 con velocidad 100; una de costo 200 lo adelanta 200; un enemigo que se mueve por una salida costosa se reprograma según ese costo; abrir una puerta sigue costando lo mismo que antes.

**Depende de**: T001

---

## T006 — Pruebas del movimiento con costo

**Requisitos**: FR-004, FR-005, FR-006, FR-007, FR-008, FR-012

**Archivo**: `cripta/tests/test_movement.py`

Cubrir, además de lo anterior:

- **Escenario obligatorio del Apéndice B**: un actor de velocidad muy alta atraviesa una salida de costo 1 y el intervalo resultante es al menos 1, de modo que el reloj avanza.
- Un camino de más salas y menor costo total lleva al jugador a su destino en menos tiempo virtual que uno de menos salas y mayor costo (SC-002).
- Una cripta sin costos declarados, con la misma semilla, produce el mismo resultado que antes del cambio (FR-012, SC-003).

Las pruebas citan en su nombre o en su docstring el requisito que ejercitan.

**Depende de**: T005

---

## T007 — Fijar el reescalado de velocidad con salidas costosas [P]

**Requisitos**: FR-009

**Archivo**: `cripta/tests/test_actor.py`

**Escenario obligatorio del Apéndice B**: cambiar la velocidad de un actor que tiene programada la llegada por una salida costosa reescala el tiempo restante según P1 §2.3, calculando con la velocidad anterior.

`Actor.change_speed()` ya hace esto. La tarea es **demostrarlo con una salida costosa**, no implementarlo: el requisito existía y el diseño de la primera parte ya lo satisface.

**Depende de**: T005

---

## T008 — La vista muestra el costo de cada salida [P]

**Requisitos**: FR-010

**Archivos**: `cripta/view/console_view.py`, `cripta/tests/test_console_view.py`

Mostrar el costo junto a la dirección y el destino de cada salida de la sala actual, de forma que el jugador pueda decir cuál es la más barata solo con lo que ve (SC-006).

**Depende de**: T001

---

## T009 — Medir el ciclo de eventos con costos variables

**Requisitos**: SC-005

**Archivo**: `cripta/benchmark/scheduler_bench.py`

Que la cripta sintética del banco reparta costos en vez de dejarlos todos en 100, y volver a medir el ciclo completo entre dos decisiones del jugador. Comparar contra los 0.1877 ms actuales.

El principio VI de la constitución no permite decir que el cambio no cuesta sin el número que lo respalde.

**Depende de**: T005

---

## T010 — No romper nada

**Requisitos**: FR-006, FR-007, FR-012

Correr la suite completa. Las 861 pruebas de la primera parte deben seguir pasando, más las nuevas.

Una prueba vieja que falle por el valor por omisión es una señal de que T001 quedó mal, no de que la prueba esté desactualizada.

**Depende de**: todas las anteriores

---

## Orden sugerido

```
T001 ──┬── T002
       ├── T003 ── T004
       ├── T005 ──┬── T006
       │          ├── T007
       │          └── T009
       └── T008
                      └── T010
```

T001 desbloquea todo lo demás, así que va primero y sola.

## Qué desbloquea esta capacidad para el resto del equipo

Cuando T005 esté confirmada, dos compañeros pueden avanzar sobre costos reales:

- **Steven**, el viaje automático «ir a», que minimiza suma de costos (§3.4).
- **Carlos**, la ruta más barata del cazador (§3.2), que es la siguiente especificación.
