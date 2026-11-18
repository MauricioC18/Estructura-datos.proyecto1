# Plan de implementación: Terreno, costo de tránsito de las salidas

**Carpeta**: `specs/001-terreno-costo-salidas` | **Fecha**: 2026-11-16 | **Especificación**: [spec.md](./spec.md)

## Resumen

El costo de atravesar una salida deja de ser el valor fijo 100 y pasa a ser un dato de la cripta. El cambio es pequeño en superficie pero toca cuatro capas: el modelo guarda el costo, el traductor lo lee del esqueleto, el motor lo usa al programar un movimiento y la vista lo muestra.

La decisión central del plan es **dónde vive el costo**. Se guarda en la puerta y no en la salida, porque la puerta ya es un único objeto compartido por las dos salas que conecta. Eso hace que FR-003, «el costo es el mismo en ambos sentidos», se cumpla por construcción en lugar de por una validación que haya que acordarse de escribir.

## Contexto técnico

**Lenguaje**: Python 3.11 o superior; el desarrollo corre sobre 3.14.6.

**Dependencias nuevas**: ninguna. Esta capacidad no agrega ni una.

**Persistencia**: el costo llega con el esqueleto de la cripta y se persiste con él, mediante la caché que ya existe y su validación por versión. El archivo binario de partida no cambia: el costo es dato de la cripta, no estado de la partida.

**Pruebas**: `unittest`, desde `cripta/` con `python -m unittest discover -s tests -t .`. Hoy hay 861 pruebas y todas pasan.

**Rendimiento**: el ciclo completo de eventos entre dos decisiones del jugador debe seguir por debajo de 20 ms. La medición actual, de la primera parte, da 0.1877 ms.

**Alcance**: cambio localizado. Cuatro archivos de producción y tres de pruebas, más las mediciones.

## Revisión contra la constitución

| Principio | Cómo lo cumple este plan |
| --- | --- |
| I. Estructuras propias, sin dependencias prohibidas | **No se agrega ninguna estructura de datos.** El costo es un entero dentro de un objeto que ya existe. No entra `dict`, `set`, `heapq`, `bisect`, `collections` ni ninguna biblioteca de grafos. El traductor ya usa la `TablaHash` propia del grupo para emparejar salidas |
| II. Determinismo | El costo es un dato leído de la cripta, no un valor aleatorio ni dependiente del orden de recorrido. Una cripta sin costos declarados produce partidas idénticas a las anteriores (FR-012, SC-003) |
| III. Separación MVC | El modelo guarda el costo y no sabe de dónde vino. El traductor, que es adaptador, lo lee del esqueleto. La vista lo muestra. Ninguna de las tres conoce a las otras dos |
| IV. Ningún dato de una cripta en el código | El único número que queda escrito es el **100 por omisión**, que es una regla del enunciado y no un dato de una cripta concreta. Queda como constante con nombre |
| V. Presupuesto de solicitudes | No se agrega ninguna solicitud. El costo viene en el esqueleto, que ya se descarga |
| VI. Rendimiento respaldado con medición | Se vuelve a correr la medición del ciclo de eventos con costos variables y se compara contra la cifra actual. Sin ese número no se declara que el cambio no cuesta |
| VII. Especificación antes del código | La especificación se confirmó en `beed3a1`, antes de este plan y antes de cualquier código |

**Resultado: pasa.** No hay nada que justificar como excepción.

## Alternativas consideradas

### Dónde guardar el costo

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **En la puerta (`Door`)** | La puerta ya es un único objeto compartido por las dos salas, así que el costo igual en ambos sentidos sale por construcción. El traductor ya tiene `_combinar` para cuando los dos lados declaran valores distintos, y ya lo usa para la llave y el cierre automático | Obliga a que toda salida tenga puerta, cosa que ya ocurre hoy | **Elegida** |
| En la salida (`Exit`) | Parece lo natural: el enunciado dice «cada salida puede declarar un costo» | Cada dirección tendría su propia copia y habría que validar a mano que coincidan. FR-003 pasaría a depender de que alguien se acuerde | Descartada |
| En una estructura aparte indexada por par de salas | Separa el dato nuevo del modelo viejo | Sería un índice, y §7 prohíbe `dict` para eso; habría que escribir una estructura entera para guardar un entero que ya tiene dónde vivir | Descartada |

El argumento decisivo es el mismo que ya se aplicó en la primera parte con la llave y el cierre automático: **lo que es propiedad de la conexión vive en la conexión**. El costo lo es.

### Cómo tratar un costo declarado distinto por cada lado

Se reutiliza `_combinar` del traductor, que ya resuelve exactamente este caso para la llave y el cierre automático: si un solo lado lo declara se usa tal cual, y si los dos declaran valores distintos se avisa y gana el de la sala de menor id. No se inventa una regla nueva para el costo.

### Cómo validar un costo inválido

El traductor ya tiene el camino de error de datos de cripta y la lista de avisos. Un costo que no sea entero mayor o igual que 1 entra por ahí, igual que cualquier otro campo malformado. No se sustituye por 100 en silencio, porque eso escondería el error (FR-011 y el caso borde correspondiente).

## Qué se cambia, archivo por archivo

### Modelo

- **`cripta/model/room.py`** — `Door` recibe un atributo de costo, con 100 por omisión mediante una constante con nombre. `Exit` expone el costo de su puerta, para que quien tenga una salida en la mano no tenga que saber que el dato está un nivel más abajo.

### Adaptador de datos

- **`cripta/repository/traductor.py`** — se agrega `costo` a `CAMPOS_DE_SALIDA`, para que deje de reportarse como campo desconocido. Se lee, se valida y se pasa a `Door`, combinando los dos lados con el mecanismo existente.

### Motor

- **`cripta/model/game.py`** — el movimiento del jugador y el del enemigo dejan de usar la constante fija y pasan a usar el costo de la salida que atraviesan. `MOVE_COST` se conserva como el valor por omisión, no como el costo de todo movimiento.

### Vista

- **`cripta/view/console_view.py`** — la línea de salidas de la sala actual muestra el costo de cada una.

**Lo que no se toca**: `Actor.interval_for()` ya recibe un costo y aplica `max(1, ...)`, así que FR-004 y FR-008 se cumplen sin cambiarlo. `Actor.change_speed()` ya reescala con la velocidad anterior, así que FR-009 tampoco necesita cambios. Esto conviene decirlo en la defensa: **dos de los requisitos ya estaban satisfechos por el diseño de la primera parte**, y las pruebas lo demuestran.

## Complejidad esperada

| Operación | Costo | Nota |
| --- | --- | --- |
| Consultar el costo de una salida | O(1) | Es leer un atributo |
| Programar un movimiento | O(1) añadido | Una lectura más antes del cálculo que ya se hacía |
| Armar el mapa desde el esqueleto | sin cambio, O(S + E) | Un campo más por salida, leído en la pasada que ya existe |

El cambio no altera ninguna complejidad. Era de esperar: no se agrega estructura, se agrega un dato.

## Mediciones previstas

1. **El ciclo de eventos con costos variables.** Se repite la medición de §5.2 sobre una cripta sintética con costos repartidos, y se compara contra los 0.1877 ms actuales. Lo que se quiere mostrar es que leer un atributo más no mueve la aguja.
2. **Comprobación de que nada cambió donde no debía.** Una cripta sin costos declarados, misma semilla y mismas acciones, tiene que dar exactamente el mismo resultado que antes (SC-003). Es la medición que respalda FR-012.

Las dos entran en `--bench` por el módulo del motor, que ya está registrado.

### Resultado de las mediciones

Hechas el 2026-11-16, en Python 3.14.6 sobre Windows 11, con 2 000 decisiones del jugador:

| Escenario | Por ciclo | Del límite de 20 ms |
| --- | ---: | ---: |
| Costos uniformes, la carga de la primera parte | 0.1912 ms | 0.96 % |
| Costos variables, la carga de esta capacidad | 0.1897 ms | 0.95 % |

La diferencia está dentro del ruido de la medición: el cambio **no cuesta nada medible**, que es lo que se esperaba de leer un atributo en lugar de una constante. Sirve además para responder §5.6 en lo que toca a esta capacidad: la agenda de eventos no se ve afectada por los costos variables.

La cripta sintética reparte costos de forma determinista por posición, no al azar, e incluye los extremos 1 y 400 para que la medición pase por el intervalo mínimo y por una salida cara.

La segunda medición prevista, la de que una cripta sin costos declarados produce el mismo resultado que antes, quedó como prueba automatizada en vez de como medición: `test_an_exit_without_cost_behaves_as_before` y las 861 pruebas de la primera parte, que siguen pasando sin tocar ninguna.

## Riesgos

- **El costo por omisión escrito en dos lugares.** Si el modelo asume 100 y el traductor también, pueden separarse. Se define una sola constante y el traductor la usa.
- **Que alguien lea el costo desde la salida equivocada.** Al moverse hay que tomar el costo de la salida que se atraviesa, no el de la sala destino. Un escenario de aceptación lo fija.
- **Las pruebas existentes que construyen salidas a mano.** Hay muchas en `tests/` que crean `Door(...)` sin costo. Por eso el valor por omisión no es negociable: sin él, se romperían todas de golpe.

## Trazabilidad

| Requisito | Dónde se implementa | Dónde se prueba |
| --- | --- | --- |
| FR-001, FR-002 | `model/room.py` | `tests/test_room.py` |
| FR-003 | `model/room.py` (la puerta compartida) y `repository/traductor.py` (`_combinar`) | `tests/test_room.py`, `tests/test_traductor.py` |
| FR-004, FR-005, FR-008 | `model/game.py`, apoyado en `model/actor.py` sin cambios | `tests/test_movement.py`, `tests/test_actor.py` |
| FR-006, FR-007 | se cumplen por omisión; se fijan con pruebas de no regresión | `tests/test_movement.py`, `tests/test_game.py` |
| FR-009 | `model/actor.py`, sin cambios | `tests/test_actor.py` |
| FR-010 | `view/console_view.py` | `tests/test_console_view.py` |
| FR-011 | `repository/traductor.py` | `tests/test_traductor.py` |
| FR-012 | ninguno: es la consecuencia del valor por omisión | `tests/test_movement.py` |

## Fases

**Fase 0 — Investigación.** Hecha y recogida en este plan: se revisó cómo el traductor empareja las salidas y combina los valores que los dos lados declaran, y se confirmó que la puerta es un único objeto compartido. No hace falta un `research.md` aparte para una capacidad de este tamaño.

**Fase 1 — Diseño.** El modelo de datos es un atributo entero en un objeto existente, descrito arriba. Tampoco amerita un `data-model.md` aparte.

**Fase 2 — Tareas.** Las genera `/speckit.tasks` en `tasks.md`.
