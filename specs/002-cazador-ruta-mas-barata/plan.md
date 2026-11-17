# Plan de implementación: El cazador, un enemigo que persigue por la ruta más barata

**Carpeta**: `specs/002-cazador-ruta-mas-barata` | **Fecha**: 2026-11-16 | **Especificación**: [spec.md](./spec.md)

## Resumen

El cazador necesita, en cada turno, el costo mínimo desde su sala hasta la sala del jugador por salidas abiertas, y la vecina por la que empieza una ruta de ese costo. Es el primer problema de rutas ponderadas del proyecto.

La decisión central del plan es **desde dónde se busca**. La búsqueda se hace **desde la sala del jugador**, no desde la sala del cazador. Tres consecuencias, y las tres son la razón de la elección:

1. El desempate del enunciado está escrito como `costo(u, v) + dist(v, jugador) = d`. Buscar desde el jugador entrega `dist(v, jugador)` para todas las vecinas de golpe, que es exactamente lo que la fórmula pide. Buscando desde el cazador habría que reconstruir rutas para recuperar ese número.
2. El grafo no tiene dirección: el costo de una salida es el mismo en ambos sentidos (FR-003 de la capacidad 001) y una puerta abierta lo está para los dos lados. Así que la distancia desde el jugador **es** la distancia hasta el jugador.
3. Una sola búsqueda desde el jugador sirve para **todos** los cazadores activos. Si se buscara desde cada cazador, compartir trabajo sería imposible.

La segunda decisión es **qué invalida el cálculo**. Buscar desde el jugador hace que la respuesta dependa solo de dos cosas: la sala del jugador y el estado de las puertas. Ni el movimiento de un cazador, ni la muerte de otro actor, ni un cambio de velocidad pueden cambiarla. Eso reduce la invalidación que exige §5.2 a dos eventos observables y es lo que hace defendible reutilizar el cálculo sin romper FR-011.

## Contexto técnico

**Lenguaje**: Python 3.11 o superior; el desarrollo corre sobre 3.14.6.

**Dependencias nuevas**: ninguna.

**Estructuras**: se reutiliza el montículo binario mínimo de la agenda de eventos como cola de prioridad, y la `TablaHash` del grupo para distancias y salas asentadas. No se escribe ninguna estructura nueva. Ver «Alternativas consideradas».

**Persistencia**: el rango es un campo de la ficha de catálogo y se guarda con la caché del catálogo, que ya valida por versión. El **archivo binario de partida sí cambia**: guarda el comportamiento de cada enemigo y ahora tiene que guardar también su rango, así que sube la versión del formato. Ver «Qué se cambia».

**Pruebas**: `unittest`, desde `cripta/` con `python -m unittest discover -s tests -t .`. Hoy hay 882 pruebas y todas pasan.

**Rendimiento**: el ciclo completo de eventos entre dos decisiones del jugador debe seguir por debajo de 20 ms. La medición de la capacidad 001, sin cazadores, da 0.1897 ms, así que hay margen; la pregunta es cuánto se lo come la persecución.

**Alcance**: una estructura nueva de búsqueda, un comportamiento nuevo en el modelo, el traductor, el motor, el guardado binario y el banco de mediciones.

## Revisión contra la constitución

| Principio | Cómo lo cumple este plan |
| --- | --- |
| I. Estructuras propias, sin dependencias prohibidas | **No se escribe ninguna estructura nueva y no entra ninguna prohibida.** La cola de prioridad es el montículo que ya resuelve la agenda de eventos. Las distancias y las salas asentadas van en la `TablaHash` del grupo, no en `dict`; las salas asentadas tampoco van en `set`. No se usa `heapq`, `bisect`, `collections`, `networkx` ni ninguna biblioteca de rutas |
| II. Determinismo | El cálculo no usa azar. El montículo ordena por `(distancia, id de sala)`, así que su orden de expansión es total y reproducible, y el desempate del enunciado se aplica aparte sobre las vecinas, de modo que el resultado no depende del orden de expansión |
| III. Separación MVC | La búsqueda vive en `structures/` y no importa nada del modelo: recibe desde afuera una función que, dada una sala, devuelve sus vecinas abiertas con su costo. El modelo del cazador recibe la búsqueda como colaborador, igual que el rastreador recibe el rastro. La vista no cambia |
| IV. Ningún dato de una cripta en el código | El rango sale de la ficha de catálogo (FR-002, FR-014). No se escribe ningún identificador de sala, ningún rango ni ningún costo de ninguna cripta |
| V. Presupuesto de solicitudes | **No se agrega ninguna solicitud.** El esqueleto completo, con el costo de cada salida, ya se descarga al iniciar, y la decisión del cazador no lee contenido de salas (FR-012) |
| VI. Rendimiento respaldado con medición | Se miden las cuatro cosas que piden §5.1 y §5.2, incluidas las dos alternativas descartadas: cálculo por cazador y recalcular siempre desde cero. Sin esos números no se afirma que compartir el cálculo convenga |
| VII. Especificación antes del código | La especificación se confirmó en `7c43117`, antes de este plan y antes de cualquier código |

**Resultado: pasa.** No hay nada que justificar como excepción.

## Alternativas consideradas

### Dónde buscar: desde el cazador o desde el jugador

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Desde la sala del jugador** | Entrega `dist(v, jugador)` para toda vecina, que es el número literal del desempate del enunciado. Una sola búsqueda sirve a todos los cazadores activos. La respuesta solo depende de la sala del jugador y de las puertas, lo que reduce la invalidación a dos eventos | Hay que apoyarse en que el grafo no tiene dirección; si algún día una salida costara distinto en cada sentido, esta decisión se cae | **Elegida** |
| Desde la sala del cazador | Es la lectura literal de «el cazador busca al jugador» | Para aplicar el desempate hay que reconstruir rutas y recuperar la distancia de cada vecina. Y el trabajo no se comparte: *n* cazadores son *n* búsquedas | Descartada |

El supuesto del grafo sin dirección queda escrito aquí a propósito: es lo que habría que revisar primero si el enunciado cambiara.

### Qué cola de prioridad usa la búsqueda

| Alternativa | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **Reutilizar el montículo de la agenda (`EventQueue`)** | Ya está escrito, probado y defendido. Ordena por `(time, sequence)`; se le entrega `(distancia, id de sala)` y queda ordenando por distancia y desempatando por id, que es justo lo que hace falta. Cero estructura nueva, y la constitución prefiere reutilizar | El montículo no tiene «disminuir clave», así que hay que insertar de nuevo y descartar al sacar las salas ya asentadas. Es el mismo recurso de la cancelación perezosa que la agenda ya usa, así que no es ajeno al diseño | **Elegida** |
| Escribir un montículo nuevo para la búsqueda | Interfaz a medida, sin nombres heredados de la agenda | Sería un segundo montículo binario en el mismo repositorio haciendo lo mismo. La constitución pide justificar no reutilizar, y no hay con qué justificarlo | Descartada |
| Escoger el mínimo recorriendo una lista | No necesita ninguna estructura | O(V) por extracción, O(V²) en total. La cripta de la revisión es más grande que las de prueba y hay decenas de cazadores | Descartada |

El montículo no sabe qué ordena: ordena por un par. Que ese par sea «instante y número de secuencia» o «distancia e id de sala» es cosa de quien lo usa. Ese es el argumento de la reutilización y es el que hay que poder decir en la defensa.

### Un cálculo por cazador, uno compartido, o recalcular siempre

Las tres se implementan, porque §5.1 y §5.2 piden medir las alternativas, no solo nombrarlas. La que queda en el programa es la compartida; las otras dos quedan como modos del banco de mediciones.

| Alternativa | Qué hace | Qué se espera medir |
| --- | --- | --- |
| **Compartido con invalidación** (la del programa) | Una búsqueda desde la sala del jugador, cortada en el rango más grande entre los cazadores activos. Se invalida cuando el jugador cambia de sala o cuando una puerta se abre o se cierra | El ahorro cuando varios cazadores actúan entre dos cambios, y que el ahorro desaparece cuando las puertas cambian todo el tiempo |
| Uno por cazador | Una búsqueda por turno de cazador, cortada en el rango de ese cazador | Que gana cuando hay pocos cazadores y rangos muy distintos, porque corta antes |
| Recalcular siempre | Una búsqueda por turno, sin reutilizar nada | La referencia contra la que se mide el ahorro. Es también la definición de «decidir desde cero» de FR-011 |

**La equivalencia no se da por supuesta.** La prueba que respalda FR-011 no compara contra lo que esperamos: corre la misma partida en modo compartido y en modo recalcular siempre y exige que las decisiones sean idénticas, turno por turno. Si alguna difiere, la invalidación está mal.

### Dos salidas abiertas hacia la misma vecina

El desempate del enunciado está escrito sobre vecinas, no sobre salidas, así que no dice qué hacer cuando dos salidas abiertas distintas llevan a la misma sala con costos distintos. La especificación lo resolvió: cuenta la más barata. En el plan eso significa que el proveedor de vecinas, cuando una sala aparece dos veces, se queda con el costo menor; así la búsqueda no necesita saber nada del caso.

### Corte por rango

La búsqueda deja de expandir en cuanto la distancia pasa del corte. Con el cálculo compartido el corte es el rango más grande entre los cazadores activos; cada cazador compara después su propia distancia contra su propio rango. Así un cazador de rango pequeño no paga por la región que solo le interesa a uno de rango grande, salvo que compartan el turno.

Esto es lo que respalda FR-017: el trabajo depende de la región dentro del corte, no de la cantidad de salas de la cripta.

**El precio de compartir, que FR-017 ahora obliga a medir.** Cuando varios cazadores de rangos distintos deciden en el mismo instante, el corte es el rango mayor, así que el de rango pequeño paga por una región que no le interesa. La medición 2 incluye por eso un caso de rangos muy desiguales, y el número que salga se reporta aunque deje mal al cálculo compartido.

### Si compartir implementación con «ir a»

El viaje automático «ir a» (§3.4), que es de Steven, también busca rutas de costo mínimo, pero sobre el mapa que el jugador conoce y no sobre el completo, y busca una ruta entera y no un paso. Este plan deja la búsqueda **parametrizada por quién provee las vecinas**, de modo que «ir a» pueda usar la misma estructura pasando el mapa conocido en lugar del real. Que la use o no es decisión de su plan; esta capacidad no la obliga.

## Qué se cambia, archivo por archivo

### Estructura nueva

- **`cripta/structures/rutas_mas_baratas.py`** (nuevo) — la búsqueda de costos mínimos. Recibe desde afuera una función que, dada una sala, devuelve sus vecinas con el costo de la salida que lleva a cada una, contando solo las abiertas. Expone el costo mínimo a cada sala dentro del corte y el primer paso con el desempate del enunciado ya aplicado. No importa nada del modelo.

### Modelo

- **`cripta/model/enemy.py`** — constante del cuarto comportamiento y el rango como atributo del enemigo. Decisión del cazador: si comparte sala ataca; si no, pregunta a la búsqueda por el primer paso dentro de su rango; si no hay, espera. El cazador recibe la búsqueda como colaborador, igual que el rastreador recibe el rastro, y no conoce el mapa.
- **`cripta/model/game.py`** — el motor construye el proveedor de vecinas abiertas sobre su mapa de salas y se lo pasa al enemigo en su turno. Invalida el cálculo compartido cuando el jugador cambia de sala y cuando una puerta se abre o se cierra, incluido el cierre automático.

### Adaptador de datos

- **`cripta/repository/traductor.py`** — se agrega el cuarto comportamiento a la tabla de traducción, `rango` a los campos permitidos de la ficha de enemigo, y la lectura y validación del rango. Un rango ausente o inválido en una ficha de cazador entra por el camino de error de datos de cripta que ya existe (FR-014). Un rango en la ficha de un enemigo que no es cazador se avisa y se ignora.

### Guardado binario

- **`cripta/adapters/almacen_partida.py`** — el bloque de cada enemigo guarda su comportamiento; ahora tiene que guardar también su rango, o un cazador cargado perseguiría con un rango inventado. Eso cambia el formato, así que **sube la versión del formato de 1 a 2**. Las partidas guardadas con la versión 1 se rechazan con el mensaje que el módulo ya da; no se intenta leerlas a medias.

### Mediciones

- **`cripta/benchmark/`** — un módulo nuevo para la persecución, con los cuatro escenarios de abajo y los tres modos de cálculo. Las criptas sintéticas son deterministas por semilla, como exige la constitución.

**Lo que no se toca**: el rastro, la lógica de guardián, errante y rastreador, el cálculo del intervalo, el combate y la vista. El cazador usa la espera y el ataque que ya existen con sus costos de siempre.

## Complejidad esperada

Sea *V* el total de salas, *E* el total de salidas, y *Vr* y *Er* las que quedan dentro del corte por rango.

| Operación | Costo | Nota |
| --- | --- | --- |
| Búsqueda desde el jugador con corte | O((Vr + Er) log Vr) | El log es el montículo. Con el corte, independiente de *V* |
| Primer paso de un cazador, cálculo vigente | O(grado de la sala) | Mira sus vecinas y aplica el desempate. En esta cripta el grado es a lo sumo 4 |
| Primer paso de un cazador, cálculo invalidado | O((Vr + Er) log Vr) | Paga la búsqueda |
| Turno de un cazador fuera de rango | O(1) después de la búsqueda | Su sala no quedó dentro del corte |
| *n* cazadores entre dos cambios | una búsqueda + O(n) | Frente a *n* búsquedas si no se comparte |
| Invalidar | O(1) | Marcar, no recorrer |
| Espacio | O(Vr) | Distancias y asentadas de la región dentro del corte |

La ganancia esperada del cálculo compartido es de *n* búsquedas a una. La pregunta que hay que medir es cada cuánto se invalida de verdad.

## Mediciones previstas

1. **Rango pequeño en cripta grande.** La misma decisión, con el mismo rango, en criptas de tamaño creciente. Lo que se quiere mostrar es que el tiempo deja de depender del tamaño de la cripta, que es FR-017 y SC-005.
2. **Decenas de cazadores.** Cantidad creciente de cazadores activos persiguiendo al mismo jugador, en modo compartido y en modo por cazador. Lo que se busca es el punto en que compartir empieza a ganar, y si existe un caso en que no gana.
3. **Puertas que cambian mucho y puertas que casi no cambian.** Dos criptas sintéticas, una con cierres automáticos frecuentes y otra casi sin ellos, las dos en modo compartido y en modo recalcular siempre. Es la medición que pide §5.2 y la que puede dejar sin argumento al cálculo compartido.
4. **El ciclo de eventos con cazadores.** La medición del ciclo completo entre dos decisiones del jugador, ahora con decenas de cazadores activos, contra los 0.1897 ms de la capacidad 001 y contra el límite de 20 ms (SC-006).

Las cuatro entran en `--bench`.

**Qué se reporta si el resultado no es el esperado**: si recalcular siempre resulta competitivo, se reporta tal cual y se discute quedarse con lo simple. La constitución pide un número incómodo documentado antes que uno favorable sin respaldo, y en esta capacidad el resultado honesto puede ser que la cripta de prueba es demasiado pequeña para que la diferencia importe.

### Resultado de las mediciones

Hechas el 2026-11-16, en Python 3.14.6 sobre Windows 11, con criptas sintéticas deterministas por semilla.

**1. El corte por rango (FR-017, SC-005).** Un cazador de rango 300, decidiendo en criptas de tamaño creciente:

| Cripta | Por decisión |
| --- | ---: |
| 60 salas | 0.0048 ms |
| 240 salas | 0.0048 ms |
| 600 salas | 0.0049 ms |
| 600 salas, sin corte efectivo | **1.5588 ms** |

Plano, como predecía el plan: cuadruplicar y decuplicar la cripta no mueve la cifra. La última fila es la que da sentido a las otras tres: sin el corte, la misma decisión en la misma cripta cuesta **320 veces más**. El rango no es solo una regla del juego, es lo que hace barata la decisión.

**Esta medición hubo que corregirla.** La primera versión salió plana también *sin* corte, y el motivo no era bueno: la cripta sintética de la primera parte nace con una puerta cerrada de cada tres, así que la región alcanzable desde la sala del jugador es de dos o tres salas por grande que sea la cripta. No se estaba midiendo el corte por rango sino el bloqueo por puertas. Se agregó al generador la opción de no cerrar ninguna puerta y se volvió a medir. Queda anotado porque es exactamente el tipo de medición que parece confirmar la hipótesis sin haberla probado.

**2. Compartir el cálculo frente a uno por cazador (SC-008).** Cincuenta cazadores persiguiendo al mismo jugador en una cripta de 60 salas:

| Escenario | Compartido | Uno por cazador | Veces |
| --- | ---: | ---: | ---: |
| Rangos iguales (300) | 0.0120 ms | 0.2377 ms | 19.8× |
| Rangos desiguales (300 y sin tope) | 0.2025 ms | 3.8722 ms | 19.1× |

Compartir gana por un orden de magnitud en los dos casos, que es lo que se esperaba: cincuenta búsquedas pasan a ser una.

**El sobrecosto que FR-017 obliga a reportar está en la primera columna.** Con rangos desiguales, el cálculo compartido cuesta 0.2025 ms contra 0.0120 ms con rangos iguales: **diecisiete veces más**, porque el corte es el rango mayor y los cuarenta y nueve cazadores de rango pequeño pagan por la región del que no tiene tope. El dato es real y hay que decirlo. Lo que lo deja aceptable es que la alternativa, un cálculo por cazador, cuesta 3.8722 ms en ese mismo escenario: compartir con sobrecosto sigue siendo diecinueve veces más barato que no compartir.

**3. Puertas que cambian mucho y puertas que casi nunca cambian (SC-007).** Diez cazadores sin tope de rango, 300 decisiones del jugador:

| Cripta | Modo | Tiempo | Búsquedas |
| --- | --- | ---: | ---: |
| Puertas que cambian mucho | compartido | 0.0187 s | 297 |
| Puertas que cambian mucho | recalcular siempre | 0.0557 s | 3902 |
| Puertas que casi no cambian | compartido | 0.0557 s | 247 |
| Puertas que casi no cambian | recalcular siempre | 0.6047 s | 4120 |

**La columna de búsquedas desmiente la mitad de lo que el plan esperaba, y es el hallazgo de esta capacidad.** El plan suponía que el ahorro vendría de reutilizar el cálculo entre turnos cuando las puertas están quietas. No es así: 297 búsquedas en 300 decisiones significa que el cálculo se invalida **casi en cada decisión del jugador**, y con las puertas quietas también, 247 de 300. La razón es que el jugador se mueve, y moverse invalida.

Entonces el ahorro real no es la reutilización entre turnos: es **compartir una búsqueda entre los diez cazadores del mismo instante**. De 3902 búsquedas a 297 es casi exactamente dividir por el número de cazadores, no por la quietud de las puertas.

Eso cambia cuál es la justificación de la decisión, y conviene decirlo así en la defensa: lo que vale no es la caché, es buscar desde el jugador en vez de desde cada cazador. Si el cálculo se hiciera desde cada cazador, compartirlo sería imposible y este ahorro no existiría.

De paso explica la fila tercera: con las puertas quietas el modo compartido cuesta *más* (0.0557 s contra 0.0187 s) aunque haga *menos* búsquedas, porque con las puertas abiertas la región alcanzable es toda la cripta y cada búsqueda es mucho más cara.

**4. El ciclo de eventos con cazadores (FR-018, SC-006).**

| Escenario | Por ciclo | Del límite de 20 ms |
| --- | ---: | ---: |
| Sin cazadores (capacidad 001) | 0.1897 ms | 0.95 % |
| Con 50 cazadores activos | 0.1854 ms | 0.93 % |

Cincuenta cazadores persiguiendo al jugador no mueven la aguja del ciclo completo: la diferencia está dentro del ruido de la medición. Con el cálculo compartido, la persecución de cincuenta enemigos cuesta 0.012 ms por instante, frente a los 0.185 ms que cuesta el ciclo entero. SC-006 se cumple con dos órdenes de magnitud de margen.

## Riesgos

- **La invalidación incompleta es el riesgo grande de esta capacidad.** Un evento que cambia el grafo y no invalida produce una decisión distinta de la del cálculo desde cero, y FR-011 se rompe sin que ninguna partida se vea rara. Por eso la prueba de equivalencia compara contra el modo recalcular siempre en vez de contra valores esperados escritos a mano.
- **El cierre automático de puertas es el caso fácil de olvidar**, porque no lo dispara ninguna acción del jugador sino la agenda de eventos. Se invalida en el mismo lugar donde se abre y se cierra cualquier puerta, no en el lugar donde el jugador abre una.
- **El desempate puede salir bien por casualidad.** Si el desempate se dejara al orden de expansión del montículo, muchas criptas darían el resultado correcto igual. Se aplica aparte, sobre las vecinas de la sala del cazador, y la prueba usa una cripta simétrica construida para que el orden de expansión y el id den respuestas distintas.
- **El cambio de versión del formato binario invalida los guardados de la primera parte**, y obliga a tocar las pruebas que fijan esa versión. Es la única excepción que SC-009 admite. Es lo correcto según §4.3 del enunciado, pero hay que decirlo al grupo para que nadie crea que su archivo se corrompió.
- **La firma de la decisión del enemigo ya tiene diez llamadas directas en las pruebas**, varias posicionales. El colaborador de búsqueda va al final y con valor por omisión, para que ninguna de esas llamadas se rompa y el guardián, el errante y el rastreador sigan decidiendo igual.
- **El rango como atributo de todos los enemigos**, y no solo de los cazadores, abarata el modelo pero deja un campo sin sentido en los otros tres. Se le da un valor neutro y el traductor avisa si una ficha que no es de cazador lo declara.

## Trazabilidad

| Requisito | Dónde se implementa | Dónde se prueba |
| --- | --- | --- |
| FR-001, FR-002 | `model/enemy.py`, `repository/traductor.py` | `tests/test_enemy.py`, `tests/test_traductor.py` |
| FR-003 | `model/enemy.py` | `tests/test_enemy.py` |
| FR-004, FR-007 | `structures/rutas_mas_baratas.py`, `model/enemy.py` | `tests/test_rutas_mas_baratas.py`, `tests/test_cazador.py` |
| FR-005, FR-006 | `model/enemy.py` | `tests/test_cazador.py` |
| FR-008 | `structures/rutas_mas_baratas.py` | `tests/test_rutas_mas_baratas.py`, `tests/test_cazador.py` |
| FR-009, FR-012 | `model/game.py` (el proveedor de vecinas se arma sobre el mapa real) | `tests/test_cazador.py` |
| FR-010 | `structures/rutas_mas_baratas.py` (solo salidas abiertas) | `tests/test_rutas_mas_baratas.py`, `tests/test_cazador.py` |
| FR-011 | `model/game.py` (invalidación) | `tests/test_cazador.py`, comparación contra el modo recalcular siempre |
| FR-013 | ninguno: es no regresión | `tests/test_enemy.py`, las 882 pruebas anteriores |
| FR-014 | `repository/traductor.py` | `tests/test_traductor.py` |
| FR-015 | ninguno: el cazador usa la activación que ya existe | `tests/test_cazador.py` |
| FR-016 | consecuencia de II; ningún código propio | `tests/test_cazador.py` |
| FR-017 | `structures/rutas_mas_baratas.py` (corte por rango) | medición 1 |
| FR-018 | el diseño completo | medición 4 |

## Fases

**Fase 0 — Investigación.** Hecha y recogida en este plan. Se revisó el montículo de la agenda para confirmar que ordena por un par y que se le puede entregar `(distancia, id)`; se revisó cómo el motor resuelve el turno de un enemigo y qué colaboradores le pasa; se revisó el bloque de enemigo del guardado binario y se encontró que el rango obliga a subir la versión del formato. No hace falta un `research.md` aparte.

**Fase 1 — Diseño.** El modelo de datos son dos tablas de la región dentro del corte, distancias y salas asentadas, más un rango entero en el enemigo. Está descrito arriba y no amerita un `data-model.md` aparte.

**Fase 2 — Tareas.** Las genera `/speckit.tasks` en `tasks.md`.
