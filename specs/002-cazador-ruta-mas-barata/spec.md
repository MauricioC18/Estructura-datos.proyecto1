# Especificación: El cazador, un enemigo que persigue por la ruta más barata

**Carpeta**: `specs/002-cazador-ruta-mas-barata`

**Creada**: 2026-11-16

**Estado**: Borrador

**Origen**: §3.2 del enunciado de la segunda parte (`cripta/docs/SegundoProyecto-EDII-2026.md`), los problemas §5.1 y §5.2, y los cinco primeros casos del Apéndice B bajo «Terreno y cazador». Agrega un cuarto comportamiento de enemigo a los tres de P1 §2.9.

**Por qué va después de 001**: el cazador decide sumando costos de salidas. Sin el costo de tránsito, que ya quedó especificado e implementado en `specs/001-terreno-costo-salidas`, «la ruta más barata» no significa nada distinto de «la ruta con menos salas». Esa capacidad era infraestructura; esta es la primera que la usa.

## Escenarios de uso y pruebas

### Historia 1 — El cazador encuentra al jugador por donde le cuesta menos (Prioridad: P1)

Los tres enemigos de la primera parte eran ciegos al mapa: el guardián no se movía, el errante escogía al azar y el rastreador solo miraba a sus vecinas buscando un rastro fresco. El cazador es el primero que entiende la cripta completa: en su turno calcula cuánto le cuesta, como mínimo, llegar hasta la sala donde está el jugador, y da un paso en esa dirección.

Lo que lo hace distinto del rastreador no es que sepa dónde está el jugador, sino que **cuenta costo y no salas**. Un pasadizo de tres salas baratas le sirve más que uno de dos salas caras, y por eso puede aparecer por donde el jugador no lo espera.

**Por qué esta prioridad**: es la capacidad. Todo lo demás de esta especificación la acota o la protege.

**Prueba independiente**: se coloca un cazador en una cripta con dos rutas hacia el jugador, una de menos salas y mayor costo y otra de más salas y menor costo, y se comprueba por cuál sale.

**Escenarios de aceptación**:

1. **Dado** un cazador que comparte sala con el jugador, **cuando** le toca su turno, **entonces** ataca, sin calcular ninguna ruta.
2. **Dado** un cazador que no comparte sala con el jugador y tiene al menos una ruta por salidas abiertas, **cuando** le toca su turno, **entonces** se mueve una sala, por una salida que empieza una ruta de costo mínimo.
3. **Dado** un cazador con una ruta de dos salas y costo total 500 y otra de cuatro salas y costo total 200, **cuando** le toca su turno, **entonces** toma la de costo 200. *(Apéndice B)*
4. **Dado** un cazador que atraviesa una salida en su turno, **cuando** se programa su siguiente turno, **entonces** el costo de la acción es el costo de esa salida, no un valor fijo.
5. **Dado** un cazador y el jugador en salas distintas, **cuando** el cazador calcula su ruta, **entonces** solo cuenta salidas cuya puerta está abierta en ese instante.

---

### Historia 2 — Dos rutas igual de baratas se resuelven siempre igual (Prioridad: P1)

Cuando varias salidas empiezan rutas del mismo costo mínimo, el cazador no escoge al azar ni según el orden en que su cálculo haya visitado las salas: va a la sala vecina de menor identificador. Esa regla hace que la partida sea reproducible y que dos implementaciones distintas del cálculo tengan que dar el mismo resultado.

**Por qué esta prioridad**: va junto con la Historia 1 porque sin ella la capacidad no es determinista, y el determinismo es condición del proyecto, no un extra.

**Prueba independiente**: se construye una cripta simétrica donde dos vecinas del cazador inician rutas del mismo costo y se comprueba que siempre toma la de menor identificador, en varias corridas.

**Escenarios de aceptación**:

1. **Dado** un cazador cuyas dos salas vecinas inician rutas de costo mínimo idéntico, **cuando** le toca su turno, **entonces** se mueve a la vecina de menor identificador. *(Apéndice B)*
2. **Dado** la misma cripta, la misma semilla y la misma secuencia de acciones, **cuando** se juega dos veces, **entonces** el cazador toma exactamente las mismas decisiones en los mismos instantes.
3. **Dado** una cripta donde existen muchas rutas distintas del mismo costo mínimo, **cuando** el cazador decide, **entonces** el desempate por menor identificador se cumple igual que cuando solo hay dos.

---

### Historia 3 — El rango dice hasta dónde le interesa perseguir (Prioridad: P2)

Un cazador no persigue al jugador por toda la cripta. Su ficha declara un rango, medido en las mismas unidades que el costo de las salidas, y si llegar al jugador le cuesta más que eso, se queda donde está. Lo mismo si no hay ninguna ruta abierta: espera.

Para quien juega, esto significa que alejarse lo suficiente, o cerrar una puerta a tiempo, lo saca del radar del cazador.

**Por qué esta prioridad**: sin el rango el cazador funciona, pero persigue siempre y la cripta se vuelve injugable. Además es la condición que hace que su decisión pueda ser barata.

**Prueba independiente**: se pone al jugador a una distancia de costo mayor que el rango del cazador y se comprueba que el cazador espera en vez de moverse.

**Escenarios de aceptación**:

1. **Dado** un cazador sin ninguna ruta por salidas abiertas hacia el jugador, **cuando** le toca su turno, **entonces** espera, y la espera le cuesta 100. *(Apéndice B)*
2. **Dado** un cazador cuya ruta más barata hacia el jugador cuesta 700 y cuyo rango es 600, **cuando** le toca su turno, **entonces** espera, y la espera le cuesta 100. *(Apéndice B)*
3. **Dado** un cazador cuya ruta más barata cuesta exactamente lo que vale su rango, **cuando** le toca su turno, **entonces** se mueve: el rango es el costo máximo que acepta, no un costo que ya quede fuera.
4. **Dado** un cazador que espera por estar fuera de rango, **cuando** se programa su siguiente turno, **entonces** se calcula con el costo 100 de la espera y la velocidad del cazador, igual que la espera de cualquier actor.

---

### Historia 4 — Lo que decidió hace un turno no lo ata en el siguiente (Prioridad: P2)

La cripta cambia mientras el cazador se mueve: las puertas se abren y se cierran, el jugador camina, otros actores mueren. El cazador no sigue un plan trazado de antemano. En cada turno su decisión tiene que ser la misma que daría un cálculo hecho desde cero en ese instante.

El caso que más importa es el de una puerta que se cierra justo en la ruta que el cazador venía siguiendo. Si se queda con el cálculo viejo, da un paso hacia una puerta cerrada o sigue una ruta que ya no existe. Lo correcto es que, en su siguiente turno, decida como si nunca hubiera calculado nada.

**Por qué esta prioridad**: es un caso borde obligatorio y la propiedad que cualquier intento de ahorrar trabajo puede romper sin que se note en una partida corta.

**Prueba independiente**: se deja al cazador avanzar un paso, se cierra una puerta de su ruta, y se compara su siguiente decisión contra la de un cazador recién colocado en la misma sala con la cripta en ese mismo estado.

**Escenarios de aceptación**:

1. **Dado** un cazador que dio un paso hacia el jugador, **cuando** una puerta de su ruta se cierra antes de su siguiente turno, **entonces** en ese turno decide como si calculara desde cero. *(Apéndice B)*
2. **Dado** un cazador cuya única ruta queda cortada por una puerta que se cerró, **cuando** le toca su turno, **entonces** espera con costo 100.
3. **Dado** un cazador al que una puerta recién abierta le acorta el camino, **cuando** le toca su turno, **entonces** toma la ruta nueva y no la que era más barata antes.
4. **Dado** un cazador, **cuando** el jugador se mueve entre dos turnos del cazador, **entonces** el cazador persigue la sala donde el jugador está, no la que ocupaba cuando el cazador decidió la vez anterior.

---

### Historia 5 — El cazador sigue siendo un enemigo como los otros (Prioridad: P3)

Todo lo que valía para los enemigos de la primera parte vale para el cazador: duerme hasta que se activa, no abre puertas cerradas, ataca con sus propios valores, muere, suelta lo que tenga que soltar y aparece en la vista como cualquier otro. Lo único nuevo es cómo escoge a dónde moverse.

**Por qué esta prioridad**: no agrega capacidad, pero si no se cumple, el cazador rompe reglas ya entregadas y evaluadas.

**Prueba independiente**: se juega una cripta con un cazador dormido y se comprueba que no actúa hasta que se activa según las reglas de P1.

**Escenarios de aceptación**:

1. **Dado** un cazador que todavía no se ha activado, **cuando** pasa el tiempo, **entonces** no persigue al jugador ni consume turnos.
2. **Dado** un cazador junto a una puerta cerrada que sería parte del camino más barato si estuviera abierta, **cuando** le toca su turno, **entonces** no la abre y escoge entre las salidas abiertas.
3. **Dado** una cripta con enemigos de los cuatro comportamientos, **cuando** se juega, **entonces** guardián, errante y rastreador se comportan exactamente como antes de esta capacidad.
4. **Dado** una ficha de catálogo cuyo comportamiento es cazador, **cuando** se arma la cripta, **entonces** su rango se toma de la ficha y no de un valor escrito en el programa.

---

### Casos borde

- **Un cazador y el jugador en regiones incomunicadas** de la cripta: no existe ruta, así que espera, por grande que sea su rango.
- **El jugador y el cazador en la misma sala con rango 0**: compartir sala tiene prioridad sobre todo lo demás, así que ataca. El rango solo limita la persecución.
- **Rango 0 y el jugador en otra sala**: cualquier ruta cuesta al menos 1, así que nunca persigue; se queda esperando. Es una ficha válida, no un error.
- **Rango enorme**, mayor que el costo de cruzar la cripta entera: persigue siempre que exista ruta. No hay tope.
- **Varios cazadores en la misma sala**: cada uno decide por su cuenta en su propio turno y todos llegan al mismo resultado, porque la regla de desempate no depende de quién pregunta.
- **Una ficha de cazador sin el campo de rango, o con un rango que no es entero mayor o igual que 0**: es un dato inválido de la cripta y se reporta como tal, sin inventar un valor por omisión que oculte el error.
- **El cazador llega a la sala del jugador en su movimiento**: ese turno fue un movimiento; atacar es decisión del turno siguiente, cuando ya comparte sala.
- **El jugador muere o la partida termina** mientras un cazador tiene turno programado: se aplica lo mismo que a cualquier enemigo con turno programado, sin regla nueva.
- **Dos salidas abiertas distintas que llevan a la misma sala vecina con costos distintos**: cuenta la más barata, tanto para el costo mínimo como para el paso que el cazador atraviesa. La vecina es la misma, así que el desempate por identificador no decide nada aquí.
- **Una salida de costo muy alto como único camino**: la ruta existe y cuesta mucho; si ese costo supera el rango, el cazador espera aunque el jugador esté en la sala de al lado.

## Requisitos

### Requisitos funcionales

- **FR-001**: El juego DEBE reconocer un cuarto comportamiento de enemigo, el cazador, junto a guardián, errante y rastreador.
- **FR-002**: La ficha de catálogo de un cazador DEBE aportar su rango, un entero mayor o igual que 0, expresado en las mismas unidades que el costo de las salidas.
- **FR-003**: Un cazador que comparte sala con el jugador DEBE atacar, sin considerar rutas ni rango.
- **FR-004**: Un cazador que no comparte sala con el jugador DEBE considerar el costo mínimo de llegar desde su sala hasta la sala actual del jugador, sumando el costo de cada salida recorrida y contando únicamente salidas cuya puerta está abierta en ese instante.
- **FR-005**: Cuando no existe ninguna ruta así, el cazador DEBE esperar, y la espera DEBE costar 100.
- **FR-006**: Cuando ese costo mínimo es mayor que el rango del cazador, el cazador DEBE esperar, y la espera DEBE costar 100.
- **FR-007**: Cuando ese costo mínimo existe y no supera el rango, el cazador DEBE moverse una sala por una salida que empiece una ruta de ese costo mínimo, y el costo de esa acción DEBE ser el costo de la salida que atraviesa.
- **FR-008**: Entre las salas vecinas que empiezan una ruta de costo mínimo, el cazador DEBE moverse a la de menor identificador. Cuando dos salidas abiertas distintas llevan a esa misma vecina con costos distintos, DEBE atravesar la más barata de las dos. Este criterio DEBE cumplirse siempre, incluso cuando hay muchas rutas de igual costo, y DEBE valer sea cual sea la forma en que se calcule la ruta.
- **FR-009**: El cazador DEBE decidir con el esqueleto completo de la cripta y el estado actual de todas las puertas. Lo que el jugador conoce o desconoce del mapa NO DEBE afectar su decisión.
- **FR-010**: Un cazador NO DEBE abrir puertas cerradas, igual que cualquier otro enemigo.
- **FR-011**: La decisión de un cazador en cada turno DEBE ser idéntica a la que se obtendría calculando la ruta desde cero en ese instante, considerando que entre dos de sus turnos pueden haber ocurrido aperturas y cierres de puertas, movimientos del jugador, cambios de sala de otros actores y cambios de velocidad.
- **FR-012**: La decisión de un cazador NO DEBE depender de si el contenido de alguna sala ya fue descargado, ni provocar ninguna solicitud nueva al servicio.
- **FR-013**: Los comportamientos guardián, errante y rastreador DEBEN conservar exactamente su lógica de decisión. El cazador NO DEBE usar el rastro del jugador.
- **FR-014**: Una ficha de cazador sin rango, o con un rango que no sea un entero mayor o igual que 0, DEBE reportarse como dato inválido de la cripta, sin sustituirlo por un valor por omisión.
- **FR-015**: Un cazador DEBE activarse con las mismas reglas que cualquier otro enemigo, y mientras no esté activo NO DEBE perseguir ni consumir turnos.
- **FR-016**: La misma cripta, la misma semilla y la misma secuencia de acciones DEBEN producir las mismas decisiones del cazador en los mismos instantes.

### Requisitos de rendimiento

- **FR-017**: El costo de la decisión de un cazador DEBE crecer con el tamaño de la región que queda dentro de su rango, y no con el tamaño de la cripta completa. Cuando varios cazadores de rangos distintos deciden en el mismo instante, el trabajo compartido entre ellos PUEDE abarcar la región del rango mayor; ese sobrecosto DEBE quedar medido y reportado, no supuesto.
- **FR-018**: El programa DEBE seguir resolviendo el ciclo completo de eventos entre dos decisiones del jugador en menos de 20 ms con al menos 50 cazadores activos a la vez, que es lo que este proyecto toma como «decenas de cazadores».

### Entidades

- **Cazador**: un enemigo que, además de lo que tiene cualquier enemigo, trae un **rango**: el costo máximo de ruta que acepta recorrer para perseguir al jugador.
- **Costo mínimo hasta el jugador**: para una sala y un instante dados, lo que menos cuesta llegar desde esa sala a la sala del jugador usando solo salidas abiertas. No es un dato de la cripta: es una respuesta que cambia cada vez que cambian las puertas o la sala del jugador.

## Criterios de éxito

- **SC-001**: En una cripta con una ruta de menos salas y mayor costo y otra de más salas y menor costo, el cazador toma siempre la de menor costo.
- **SC-002**: En una cripta donde dos o más vecinas inician rutas del mismo costo mínimo, repetir la partida con la misma semilla produce siempre el mismo movimiento, hacia la vecina de menor identificador.
- **SC-003**: Un cazador cuyo jugador está fuera de su rango, o incomunicado de él, no se mueve ni una sala durante toda la partida.
- **SC-004**: Después de que una puerta se abre o se cierra, la decisión del cazador coincide con la de un cálculo hecho desde cero en ese instante, en todos los turnos comprobados.
- **SC-005**: Al multiplicar por diez el tamaño de la cripta sin cambiar el rango del cazador, el tiempo de su decisión no se multiplica por diez.
- **SC-006**: Con al menos 50 cazadores activos persiguiendo al mismo jugador, el ciclo completo de eventos entre dos decisiones del jugador sigue resolviéndose en menos de 20 ms.
- **SC-007**: Está medido, con una cripta donde las puertas cambian con frecuencia y otra donde casi nunca cambian, cuánto trabajo ahorra reutilizar cálculos frente a calcular siempre desde cero, y en qué condiciones deja de convenir.
- **SC-008**: Está medido si conviene un cálculo por cazador o un cálculo compartido entre todos los cazadores activos, y está documentada la condición que hace cambiar la respuesta.
- **SC-009**: Las 882 pruebas anteriores a esta capacidad siguen pasando sin modificarlas, con una sola excepción prevista: las que fijan la versión del formato del archivo de partida, porque guardar el rango de un cazador cambia ese formato. Cualquier otra prueba que falle es un defecto, no una prueba desactualizada.

## Supuestos

- El rango de un cazador es un dato de la cripta y llega en su ficha de catálogo, igual que su vida, su ataque y su velocidad. Esta especificación no define cómo se obtiene ese dato, solo qué significa.
- Un rango inválido o ausente se trata con el mismo criterio que el proyecto ya aplica a los datos malformados de una cripta, y que la capacidad 001 aplicó al costo de las salidas: se reporta como error de datos y no se adivina un valor.
- El rango es el costo máximo aceptado, de modo que una ruta que cuesta exactamente el rango sí se recorre. El enunciado dice que el cazador espera cuando el costo es **mayor** que el rango.
- Que el jugador haya explorado o no las salas por donde pasa el cazador no cambia nada: la niebla de guerra es del jugador y no del enemigo. Qué ve el jugador del cazador es asunto de la capacidad de niebla de guerra (§3.3), no de esta.
- El esqueleto de la cripta ya se descarga completo al iniciar y ya incluye el costo de cada salida, así que esta capacidad no agrega ninguna solicitud al servicio.
- Reutilizar cálculos entre turnos está permitido mientras no cambie ninguna decisión. Es una decisión del `plan.md`, no una regla del juego, y FR-011 es la condición que cualquier reutilización tiene que respetar.
- Cómo se calcula la ruta y con qué estructuras es asunto del `plan.md`. Esta especificación solo establece qué ruta es la correcta y cómo se desempata.
- El viaje automático «ir a» del jugador (§3.4) también calcula rutas de costo mínimo, pero sobre el mapa que el jugador conoce y no sobre el completo. Si conviene compartir implementación con esta capacidad es decisión del `plan.md` de ambas; las reglas son distintas y se especifican por separado.
