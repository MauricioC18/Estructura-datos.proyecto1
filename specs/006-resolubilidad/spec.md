# Feature Specification: Verificación de resolubilidad

**Feature Branch**: `Parte_2-API-cache-persistencia`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Verificación de resolubilidad (§3.5 y §5.4 de cripta/docs/SegundoProyecto-EDII-2026.md, más los cuatro casos de resolubilidad del Apéndice B). Antes de iniciar una partida, el programa debe decidir, con el esqueleto y la ubicación de las llaves (spec 004), si desde sala_inicial se puede obtener llave_salida y llegar a sala_salida a través de una puerta que la requiera. Supuestos de la verificación: se puede atravesar toda salida abierta y toda salida cerrada cuya llave ya se obtuvo; las llaves no se gastan; todo enemigo se puede derrotar; una llave que suelta un enemigo se obtiene en la sala donde ese enemigo inicia; las trampas y el cierre automático no impiden el paso. Si es resoluble, el reporte da un orden de obtención de llaves en el que cada llave aparece después de las que hacen falta para alcanzarla, y ese orden tiene que salir siempre igual aunque haya varios válidos. Si no es resoluble, el reporte dice qué llaves no se pueden obtener, qué puertas cerradas de la frontera de la región alcanzable bloquean el avance y qué llave pide cada una, dónde está cada una de esas llaves, y, si una llave está detrás de puertas que solo ella abre, directamente o por una cadena de llaves, señala ese ciclo concreto. Hay que definir qué pasa cuando la ubicación de llaves no está disponible. Una cripta no resoluble no inicia salvo con --forzar; --verificar <cripta> hace solo la verificación y muestra el reporte, sin la vista del juego. El reporte se muestra al iniciar cada partida. El costo tiene que ser aproximadamente lineal en salas, salidas y llaves, sin repetir el recorrido completo por cada llave; la frontera y las dependencias salen del mismo recorrido, y la detección de ciclos es determinista. Tiene que tardar menos de 200 ms en la cripta publicada más grande, sin red, y --bench debe compararla contra la versión ingenua que repite el recorrido por cada llave, con criptas sintéticas de muchas llaves encadenadas generadas con semilla. Las banderas las conecta Steven (spec 005), así que el reporte tiene que exponer si la cripta es resoluble y sus líneas de texto. Carpeta: specs/006-resolubilidad."

## Clarifications

### Session 2026-11-17

Preguntas resueltas durante `/speckit.specify`:

- Q: ¿El orden de obtención incluye todas las llaves obtenibles o solo las necesarias para llegar a la salida? → A: Todas las llaves obtenibles (FR-006).
- Q: Cuando la cripta es resoluble pero alguna llave no es obtenible, ¿el reporte lo menciona? → A: Sí, como aviso al final del reporte (FR-008).
- Q: ¿Qué pasa cuando la ubicación de llaves no está disponible? → A: El reporte dice que no se pudo verificar, la partida inicia igual, y `--verificar` termina con un código de salida propio para ese caso (FR-018, FR-020).

### Session 2026-11-18

Preguntas resueltas durante `/speckit.clarify`:

- Q: ¿Con qué regla se elige el orden cuando hay varios válidos? → A: Por rondas: primero las llaves que se alcanzan sin abrir ninguna puerta cerrada, después las que se alcanzan con esas, y así; dentro de cada ronda, por id (FR-006, FR-007).
- Q: Si hay varias formas de explicar por qué una llave está bloqueada, ¿cuál se reporta? → A: Primero la que apunta a una llave sin ubicación; entre llaves con ubicación, la de menor id (FR-013, FR-014).
- Q: ¿El reporte explica cada llave que no se puede obtener? → A: Sí: una línea por llave no obtenible que dice de qué llave depende, o que no tiene ubicación, o que está en una zona sin acceso; los ciclos van aparte (FR-009, FR-012).
- Q: ¿`--replay` de una partida que se jugó con `--forzar` se detiene por la verificación? → A: No: la reproducción nunca se detiene por la verificación, porque la partida original ya se jugó (FR-016).
- Q: ¿Qué dice cada línea del orden de llaves? → A: La llave y dónde se obtiene, por ejemplo «1. itm_llave_bronce: sala 4» o «2. itm_llave_hierro: la suelta e-201, que inicia en la sala 7» (FR-006, FR-021).

## User Scenarios & Testing *(mandatory)*

La verificación responde una sola pregunta antes de jugar: ¿se puede ganar esta cripta? Para responderla solo usa el esqueleto (salas, salidas y puertas con su estado inicial) y la ubicación de llaves que obtiene la especificación 004. No usa el contenido de las salas ni el catálogo, no gasta solicitudes propias y no cambia nada de la partida.

Vocabulario de esta especificación:

- **Región alcanzable**: las salas a las que el jugador puede llegar desde `sala_inicial` bajo los supuestos de §3.5, con las llaves que puede obtener en el camino.
- **Llave obtenible**: una llave con al menos una ubicación dentro de la región alcanzable.
- **Puerta de la frontera**: una salida cerrada que va desde una sala de la región alcanzable a una sala que no lo es, porque pide una llave que no es obtenible.
- **Dependencia**: la llave L depende de la llave M cuando, para llegar a la sala donde está L desde la región alcanzable, hay que pasar por una puerta que pide M.
- **Ciclo de dependencias**: una cadena de dependencias que vuelve a la llave de partida, como «L depende de L» o «L depende de M y M depende de L».

### User Story 1 - Saber antes de jugar si la cripta se puede ganar (Priority: P1)

Como jugador, quiero que antes de la primera acción el programa me diga si la cripta se puede ganar y, si se puede, en qué orden conviene conseguir las llaves.

**Why this priority**: Es la razón de ser de la capacidad (§3.5) y la base de todo lo demás: el reporte de bloqueo, `--forzar` y `--verificar` dependen de esta decisión.

**Independent Test**: Verificar criptas pequeñas armadas a mano, con llaves en el suelo y en lo que suelta un enemigo, y comparar la decisión y el orden con los esperados.

**Acceptance Scenarios**:

1. **Dado** una cripta en la que, partiendo de `sala_inicial`, se obtiene `llave_salida` y se llega a `sala_salida` por una puerta que la pide, **Cuando** se verifica, **Entonces** es resoluble.
2. **Dado** una cripta en la que hay que obtener la llave de bronce para abrir la puerta detrás de la cual está `llave_salida`, **Cuando** se verifica, **Entonces** es resoluble y en el orden la llave de bronce aparece antes que `llave_salida`.
3. **Dado** una llave que está en lo que suelta un enemigo errante, **Cuando** se verifica, **Entonces** la verificación la ubica en la sala donde ese enemigo inicia, aunque el errante pueda moverse durante la partida, y la línea del orden dice «la suelta <enemigo>, que inicia en la sala <n>». *(Apéndice B)*
4. **Dado** una cripta con varios órdenes válidos de obtención de llaves, **Cuando** se verifica dos veces, **Entonces** las dos ejecuciones producen el mismo orden: por rondas y, dentro de cada ronda, por id. *(Apéndice B)*
5. **Dado** la misma cripta con sus páginas, sus salas, sus salidas o sus entradas de ubicación de llaves en otro orden, **Cuando** se verifica, **Entonces** el resultado y el orden son los mismos.
6. **Dado** una salida declarada solo desde la sala A hacia la sala B, **Cuando** se verifica, **Entonces** se puede pasar de A a B pero no de B a A.
7. **Dado** una cripta en la que se obtiene `llave_salida` pero ninguna puerta que la pida lleva a `sala_salida`, **Cuando** se verifica, **Entonces** no es resoluble, aunque `sala_salida` sea alcanzable por otro camino.
8. **Dado** una cripta resoluble con una llave en una zona a la que no se puede llegar, **Cuando** se verifica, **Entonces** es resoluble, esa llave no aparece en el orden y el reporte la menciona como aviso al final.

---

### User Story 2 - Entender por qué una cripta no se puede ganar (Priority: P1)

Como jugador, quiero que, si la cripta no se puede ganar, el reporte me diga qué llaves faltan, qué puertas bloquean, dónde están esas llaves y si hay llaves encerradas detrás de sus propias puertas.

**Why this priority**: §3.5 exige este reporte, y es lo que se muestra cuando la partida no inicia (Apéndice B).

**Independent Test**: Verificar criptas no resolubles armadas a mano y comparar cada parte del reporte con lo esperado.

**Acceptance Scenarios**:

1. **Dado** que `llave_salida` está detrás de la única puerta que ella misma abre, **Cuando** se verifica, **Entonces** no es resoluble y el reporte señala el ciclo: `llave_salida` depende de sí misma. *(Apéndice B)*
2. **Dado** que la llave A está detrás de una puerta que pide B, y B está detrás de una puerta que pide A, **Cuando** se verifica, **Entonces** el reporte señala el ciclo concreto A → B → A.
3. **Dado** una cripta no resoluble, **Cuando** se verifica, **Entonces** el reporte lista cada llave que no se puede obtener, incluidas las que pide alguna puerta y no aparecen en la ubicación de llaves.
4. **Dado** una cripta no resoluble, **Cuando** se verifica, **Entonces** el reporte lista cada puerta de la frontera con su sala de origen, su dirección, su sala de destino y la llave que pide.
5. **Dado** una puerta de la frontera, **Cuando** se arma el reporte, **Entonces** dice dónde está la llave que pide: la sala, y el enemigo si la suelta uno; o que esa llave no tiene ubicación.
6. **Dado** una llave bloqueada por una puerta cuya llave no aparece en ninguna parte, **Cuando** se verifica, **Entonces** el reporte dice que depende de esa llave sin ubicación y no lo presenta como un ciclo.
7. **Dado** una llave a la que se puede llegar por dos puertas bloqueadas que piden llaves distintas, **Cuando** se verifica dos veces, **Entonces** el reporte elige siempre la misma explicación.

---

### User Story 3 - No empezar una partida que no se puede ganar (Priority: P1)

Como jugador, quiero que el programa no me deje empezar una cripta imposible sin avisarme, pero que me deje forzarla si quiero, y poder verificar una cripta sin jugarla.

**Why this priority**: Es la consecuencia que el enunciado exige de la verificación, y el Apéndice B la evalúa directamente.

**Independent Test**: Iniciar una cripta no resoluble con y sin `--forzar`, y ejecutar `--verificar` sobre criptas resolubles y no resolubles.

**Acceptance Scenarios**:

1. **Dado** una cripta no resoluble, **Cuando** se intenta iniciar una partida sin `--forzar`, **Entonces** la partida no inicia y se muestra el reporte. *(Apéndice B)*
2. **Dado** una cripta no resoluble, **Cuando** se inicia con `--forzar`, **Entonces** se muestra el reporte y la partida inicia igual.
3. **Dado** una cripta resoluble, **Cuando** se inicia una partida, **Entonces** se muestra el reporte con el orden de llaves antes de la primera acción.
4. **Dado** `--verificar <cripta>`, **Cuando** se ejecuta, **Entonces** solo se verifica y se muestra el reporte, sin instanciar la vista del juego ni iniciar una partida, y el código de salida dice si la cripta es resoluble.
5. **Dado** una partida guardada, **Cuando** se carga, **Entonces** no se verifica de nuevo, porque la verificación ocurrió cuando esa partida empezó.
6. **Dado** un paquete offline sin ubicación de llaves, **Cuando** se inicia una partida, **Entonces** el reporte dice que no se pudo verificar y la partida inicia; con `--verificar`, el código de salida es 2.
7. **Dado** el log de una partida de una cripta no resoluble que se jugó con `--forzar`, **Cuando** se reproduce con `--replay`, **Entonces** la reproducción no se detiene por la verificación.

---

### User Story 4 - Una verificación rápida y medida (Priority: P2)

Como grupo, queremos demostrar con mediciones que la verificación no repite el recorrido completo por cada llave y que cumple el límite de tiempo de §6.1.

**Why this priority**: Es el problema de estructuras de datos de §5.4 y lo que se defiende en el Documento de Decisiones.

**Independent Test**: Ejecutar `--bench` y la verificación de la cripta publicada más grande, sin red.

**Acceptance Scenarios**:

1. **Dado** la cripta publicada más grande, **Cuando** se verifica localmente sin red, **Entonces** tarda menos de 200 ms.
2. **Dado** criptas sintéticas con muchas llaves encadenadas, generadas con una semilla, **Cuando** se ejecuta `--bench`, **Entonces** se reportan los tiempos de la verificación y de la alternativa ingenua que repite el recorrido por cada llave, para varios tamaños.
3. **Dado** cualquier cripta medida, **Cuando** se comparan las dos versiones, **Entonces** dan la misma decisión, el mismo orden y el mismo reporte.
4. **Dado** la misma semilla, **Cuando** se generan las criptas sintéticas dos veces, **Entonces** son idénticas.

---

### Edge Cases

- `llave_salida` está en `sala_inicial`: es obtenible desde el principio.
- La cripta no tiene ninguna puerta cerrada: es resoluble si alguna puerta que pide `llave_salida` lleva a `sala_salida`; si no hay ninguna, no lo es.
- La ubicación de llaves viene vacía: ninguna llave es obtenible.
- Una puerta pide una llave que no aparece en la ubicación de llaves: esa llave no es obtenible y figura en el reporte como llave sin ubicación.
- La misma llave tiene varias ubicaciones: basta alcanzar una.
- Una llave está en una zona sin ninguna salida que llegue a ella: no es obtenible, no depende de ninguna llave y no forma ciclo.
- Una puerta cerrada que no pide ninguna llave: no se puede atravesar; si está en la frontera, el reporte la muestra sin llave.
- Dos puertas distintas llevan a `sala_salida` y solo una pide `llave_salida`: basta con alcanzar esa.
- Una puerta abierta con cierre automático, o una sala con trampas: no bloquean.

## Requirements *(mandatory)*

### Functional Requirements

**Qué se verifica**

- **FR-001**: Antes de iniciar una partida nueva, y al ejecutar `--verificar`, el programa MUST verificar la resolubilidad de la cripta usando solo el esqueleto y la ubicación de llaves (especificación 004), sin pedir contenido de salas ni fichas del catálogo.
- **FR-002**: La verificación MUST considerar atravesable toda salida abierta y toda salida cerrada cuya llave ya se obtuvo; las llaves no se consumen; todo enemigo se puede derrotar; las trampas y los cierres automáticos no bloquean.
- **FR-003**: Una llave MUST considerarse obtenida en cuanto la región alcanzable incluye la sala de cualquiera de sus ubicaciones. Una llave que suelta un enemigo MUST ubicarse en la sala donde ese enemigo inicia.
- **FR-004**: La verificación MUST respetar el sentido de las salidas: una salida solo se atraviesa desde la sala que la declara.
- **FR-005**: Una cripta MUST considerarse resoluble si y solo si `llave_salida` es obtenible y alguna sala de la región alcanzable tiene una salida hacia `sala_salida` cuya puerta pide `llave_salida`.

**Si es resoluble**

- **FR-006**: El reporte MUST dar un orden de obtención que incluya todas las llaves obtenibles, cada una una sola vez, en el que cada llave aparece después de todas las llaves necesarias para alcanzarla. El orden va por rondas: primero las llaves que se alcanzan sin abrir ninguna puerta cerrada; después, las que se alcanzan con las de rondas anteriores; y así. Cada línea dice la llave y dónde se obtiene: la sala o, si la suelta un enemigo, ese enemigo y la sala donde inicia.
- **FR-007**: El orden MUST ser determinista: dentro de cada ronda, las llaves van por id, y la misma cripta produce siempre el mismo orden, sin importar el orden en que lleguen las páginas, las salas, las salidas o las entradas de la ubicación de llaves.
- **FR-008**: Cuando la cripta es resoluble pero alguna llave no es obtenible, el reporte MUST mencionarla como aviso al final, después del orden.

**Si no es resoluble**

- **FR-009**: El reporte MUST listar las llaves que no se pueden obtener, incluidas las que pide alguna puerta y no aparecen en la ubicación de llaves. Cada una va en una línea que dice de qué llave depende, o que no tiene ubicación, o que está en una zona a la que no lleva ninguna salida.
- **FR-010**: El reporte MUST listar las puertas de la frontera, cada una con su sala de origen, su dirección, su sala de destino y la llave que pide (o que no pide ninguna).
- **FR-011**: Para cada llave que pide una puerta de la frontera, el reporte MUST decir dónde está: la sala y, si la suelta un enemigo, ese enemigo; o que la llave no tiene ubicación.
- **FR-012**: Si una llave está detrás de puertas que solo ella abre, directamente o mediante una cadena de llaves, el reporte MUST señalar el ciclo concreto, como la secuencia de llaves que vuelve a la primera.
- **FR-013**: Una llave cuya sala solo se alcanza pasando por una puerta que pide una llave sin ubicación MUST reportarse como dependiente de esa llave, no como parte de un ciclo.
- **FR-014**: Cuando hay varias formas de explicar el bloqueo de una llave, el reporte MUST elegir siempre la misma: primero la que apunta a una llave sin ubicación y, entre llaves con ubicación, la de menor id.
- **FR-015**: Las listas del reporte MUST salir en un orden determinista.

**Consecuencias en la partida**

- **FR-016**: Si la cripta no es resoluble, la partida MUST no iniciar salvo que se use `--forzar`, y el reporte MUST mostrarse en los dos casos. Una reproducción con `--replay` nunca se detiene por la verificación.
- **FR-017**: El reporte MUST mostrarse al iniciar cada partida nueva, antes de la primera acción, también cuando la cripta es resoluble.
- **FR-018**: `--verificar <cripta>` MUST ejecutar solo la verificación, mostrar el reporte sin instanciar la vista del juego, no iniciar ninguna partida y terminar con código de salida 0 si la cripta es resoluble, 1 si no lo es y 2 si no se pudo verificar (FR-020).
- **FR-019**: Al cargar una partida guardada, la verificación MUST no ejecutarse, porque la ubicación de llaves no se obtiene en ese inicio (especificación 004, FR-011).
- **FR-020**: Cuando la ubicación de llaves no está disponible (especificación 004, FR-016), el reporte MUST decir que no se pudo verificar y por qué, y la partida MUST iniciar igual, sin necesidad de `--forzar`.
- **FR-021**: El reporte MUST exponer, sin que quien lo use sepa cómo se calculó, si la cripta es resoluble y sus líneas de texto listas para mostrar, para que la vista y las banderas de la especificación 005 lo usen.
- **FR-022**: La verificación MUST no gastar solicitudes además de las de la especificación 004 y MUST no cambiar el estado de la partida.

**Costo y mediciones (§5.4 y §6.1)**

- **FR-023**: El costo de la verificación MUST crecer aproximadamente en proporción a la cantidad de salas, salidas y llaves: ninguna sala ni salida se vuelve a examinar por cada llave nueva que se obtiene.
- **FR-024**: La región alcanzable, la frontera, las dependencias y los ciclos MUST salir del mismo recorrido, sin recorridos completos adicionales por cada llave.
- **FR-025**: La detección de ciclos MUST ser determinista y reportar el ciclo concreto.
- **FR-026**: La verificación de la cripta publicada más grande MUST tardar menos de 200 ms, medida localmente sin red.
- **FR-027**: `--bench` MUST comparar la verificación con la alternativa ingenua que repite el recorrido completo cada vez que se obtiene una llave, en criptas sintéticas con muchas llaves encadenadas generadas con una semilla, para varios tamaños.
- **FR-028**: La verificación y la alternativa ingenua MUST dar la misma decisión, el mismo orden y el mismo reporte en todas las criptas medidas.

### Key Entities *(include if feature involves data)*

- **Esqueleto**: las salas con sus salidas; cada salida tiene sentido, sala de destino y puerta con estado inicial (abierta o cerrada) y llave requerida opcional.
- **Ubicación de llave**: dónde se obtiene una llave: sala y, opcionalmente, el enemigo que la suelta (especificación 004).
- **Reporte de resolubilidad**: la decisión (resoluble o no), el orden de llaves o la explicación del bloqueo (llaves no obtenibles, puertas de la frontera, ubicaciones, dependencias y ciclos), y sus líneas de texto.
- **Cripta sintética**: una cripta generada con semilla para medir, con muchas llaves encadenadas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los cuatro casos de resolubilidad del Apéndice B tienen una prueba automatizada que pasa y cita su requisito.
- **SC-002**: La verificación de la cripta publicada más grande tarda menos de 200 ms en la máquina de cualquier integrante, sin red.
- **SC-003**: En las criptas sintéticas, el tiempo de la verificación crece aproximadamente en proporción al tamaño de la cripta, mientras que el de la alternativa ingenua crece claramente más rápido a medida que aumentan las llaves encadenadas.
- **SC-004**: La verificación y la alternativa ingenua coinciden en el 100 % de las criptas medidas.
- **SC-005**: Iniciar una partida verificada no hace ninguna solicitud además de las de la especificación 004.

## Assumptions

- La ubicación de llaves y el esqueleto los obtiene la especificación 004; esta especificación no hace solicitudes propias.
- Mostrar el reporte en la vista y conectar las banderas `--verificar` y `--forzar` lo hace la especificación 005, usando lo que expone el reporte (FR-021). Los requisitos de las banderas viven en esta especificación.
- El juego se gana entrando a `sala_salida` después de abrir con `llave_salida` la puerta que permite acceder a ella (P1 §2.12); por eso FR-005 exige una puerta que pida `llave_salida`.
- Todas las criptas publicadas a la fecha usan pasos en los dos sentidos, pero el contrato permite salidas de un solo sentido, y la revisión usará una cripta nueva.
- Con salidas de un solo sentido, la verificación considera que una llave obtenida sirve en toda la región alcanzable, aunque el jugador no siempre pueda volver a la puerta que esa llave abre. Resolverlo exactamente exigiría seguir la combinación de sala y llaves del jugador, que crece exponencialmente con el número de llaves. Es un límite conocido y se documenta en la sección 5.4 de DECISIONES.
- Las mediciones se hacen con la cripta publicada más grande y con criptas sintéticas; ningún dato de una cripta concreta queda escrito en el código.
