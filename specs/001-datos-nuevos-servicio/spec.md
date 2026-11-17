# Feature Specification: Datos nuevos del servicio

**Feature Branch**: `Parte_2-API-cache-persistencia`

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "Datos nuevos del servicio para la segunda parte de CRIPTA (§4.1, §4.2, §4.3 y Apéndice A de cripta/docs/SegundoProyecto-EDII-2026.md). El contrato del API ya está publicado en su versión 1.1.0 (copia en cripta/docs/contrato/openapi-1.1.0.json): agrega solo el campo costo en las salidas, el campo rango y el comportamiento cazador en las fichas de enemigo, y la consulta GET /criptas/<id>/llaves. Son la base de tres capacidades: el terreno y el cazador usan el costo de las salidas y el rango, y la verificación de resolubilidad usa la ubicación de las llaves. Esta especificación cubre solo obtener, validar y conservar esos datos; las reglas que los usan (lo que cuesta moverse, el turno del cazador y la verificación) van en sus propias especificaciones. Lo que necesito: 1. Costo de las salidas: cada salida del esqueleto puede traer "costo", un entero mayor o igual que 1. Si no lo trae o viene en null, vale 100. Es el mismo en los dos sentidos del paso, aunque el contrato describe cada salida por separado. 2. Cazador: una ficha de enemigo puede tener comportamiento "cazador" y un campo "rango", entero mayor o igual que 1 en unidades de costo. El contrato no obliga a que venga el rango, así que hay que definir qué pasa con un cazador sin rango. Un rango en un enemigo que no es cazador no tiene efecto. Hoy el programa detiene la partida cuando encuentra un comportamiento que no conoce; con las criptas nuevas eso no puede pasar. 3. Ubicación de llaves: GET /criptas/<id>/llaves devuelve cada llave con la sala donde está. Si trae "enemigo", la llave está en lo que suelta esa instancia y la sala es donde el enemigo inicia. Se consulta al iniciar la partida y cuenta dentro de presupuesto_solicitudes. Se guarda en disco junto con el resto de la cripta y vale mientras coincida la versión de la cripta; si ya está guardada para esa versión no se vuelve a pedir. En modo --offline se lee de disco y no cuenta. 4. Lo guardado por la primera parte se invalida con la validación de versión que ya existe, no borrando archivos a mano. 5. Los campos nuevos no deben producir el aviso de "campo desconocido" que el programa da cuando el contrato del API cambia; un campo que siga sin conocerse debe seguir avisándose. Cada caso debe quedar como escenario de aceptación con requisitos numerados. Carpeta de la especificación: specs/001-datos-nuevos-servicio."

## Clarifications

### Session 2026-11-16

Preguntas resueltas durante `/speckit.specify`:

- Q: ¿Qué costo se usa cuando solo una de las dos salidas de un paso declara costo, o cuando las dos declaran valores distintos? → A: El valor declarado vale para los dos sentidos. Si las dos declaran valores distintos, gana el de la sala de menor id y se registra un aviso (FR-003).
- Q: ¿Qué pasa con una ficha de cazador que no trae rango, o lo trae en null? → A: Es un dato inválido de la ficha: se informa con el id de la ficha y no se usa ningún valor en su lugar (FR-008).
- Q: ¿Qué pasa si el paquete offline no trae la ubicación de llaves? → A: Se informa que la ubicación de llaves no está disponible y la partida puede continuar. Qué hace la verificación de resolubilidad en ese caso lo define su propia especificación (FR-016).

## User Scenarios & Testing *(mandatory)*

Esta especificación no agrega reglas de juego. Garantiza que los datos nuevos que publica el servicio lleguen completos, validados y conservados, para que las capacidades que los usan puedan apoyarse en ellos: el terreno y el cazador (costo y rango), la niebla de guerra y «ir a» (costo), y la verificación de resolubilidad (ubicación de llaves).

### User Story 1 - Jugar una cripta nueva que tiene cazadores (Priority: P1)

Como jugador, quiero iniciar y jugar las criptas de la segunda parte aunque tengan enemigos con comportamiento cazador, sin que la partida se detenga por un dato que el programa no reconoce. Cada cazador debe llegar a la partida con su rango.

**Why this priority**: Hoy, en cuanto el programa necesita la ficha de un cazador, informa un comportamiento desconocido y no puede seguir con esa acción, así que las criptas publicadas no se pueden jugar. Mientras eso pase, nadie del grupo puede probar su capacidad con ellas.

**Independent Test**: Se inicia una cripta cuyo contenido incluye un cazador y se entra a su sala: la partida continúa y el cazador tiene el rango declarado en su ficha.

**Acceptance Scenarios**:

1. **Dado** una cripta con un enemigo cuya ficha declara comportamiento cazador y rango 600, **Cuando** el jugador entra a la sala de ese enemigo, **Entonces** la partida continúa y ese enemigo es un cazador con rango 600.
2. **Dado** una ficha de guardián, de errante o de rastreador, **Cuando** se carga un enemigo de ese tipo, **Entonces** conserva el comportamiento que tenía en la primera parte.
3. **Dado** una ficha de enemigo que no es cazador y declara un rango, **Cuando** se carga un enemigo de ese tipo, **Entonces** el rango no tiene ningún efecto y no aparece ningún aviso.
4. **Dado** una ficha de cazador sin rango (ausente o en null), **Cuando** se carga un enemigo de ese tipo, **Entonces** se informa como dato inválido de la ficha, con su id, y no se usa ningún rango en su lugar.
5. **Dado** una ficha con un comportamiento distinto de los cuatro conocidos, **Cuando** se carga un enemigo de ese tipo, **Entonces** se informa como dato inválido de la cripta, nombrando la ficha y el valor recibido.

---

### User Story 2 - Cada salida tiene su costo de movimiento (Priority: P1)

Como jugador, quiero que cada salida tenga el costo que declara la cripta, igual en los dos sentidos, para que moverse, la persecución del cazador y los viajes automáticos usen el terreno real.

**Why this priority**: El costo de las salidas es la base del terreno, del cazador y de «ir a». Sin él, esas tres capacidades no se pueden probar con datos reales.

**Independent Test**: Se carga un esqueleto con salidas con y sin costo, y se consulta el costo de cada salida en ambos sentidos.

**Acceptance Scenarios**:

1. **Dado** una salida que declara costo 250, **Cuando** se carga el esqueleto, **Entonces** el costo de esa salida es 250.
2. **Dado** una salida que no declara costo, o que lo declara en null, **Cuando** se carga el esqueleto, **Entonces** su costo es 100.
3. **Dado** un paso entre dos salas cuyas dos salidas declaran el mismo costo, **Cuando** se carga el esqueleto, **Entonces** el costo es el mismo en ambos sentidos.
4. **Dado** un paso entre dos salas en el que solo una de las dos salidas declara costo 250, **Cuando** se carga el esqueleto, **Entonces** el costo es 250 en ambos sentidos.
5. **Dado** un paso entre las salas 3 y 8 en el que la salida de la sala 3 declara costo 120 y la de la sala 8 declara costo 200, **Cuando** se carga el esqueleto, **Entonces** el costo es 120 en ambos sentidos y se registra un aviso que nombra las dos salas y el valor usado.
6. **Dado** una salida con costo 0, negativo, decimal o que no es un número, **Cuando** se carga el esqueleto, **Entonces** se informa como dato inválido de la cripta, indicando la sala, la dirección y el valor, y la partida no inicia.
7. **Dado** un esqueleto cargado, **Cuando** todavía no se ha descargado el contenido de ninguna sala, **Entonces** el costo de todas las salidas ya está disponible.

---

### User Story 3 - La ubicación de las llaves está disponible antes de jugar (Priority: P2)

Como jugador, quiero que antes de la primera acción el programa conozca dónde se puede obtener cada llave de la cripta, para que la verificación de resolubilidad pueda decirme si la cripta se puede ganar. Esa consulta debe respetar el presupuesto de solicitudes y no repetirse si ya se tiene para la versión vigente de la cripta.

**Why this priority**: La verificación de resolubilidad depende por completo de este dato, pero ninguna otra capacidad lo necesita para empezar a probar.

**Independent Test**: Se inicia una partida dos veces en la misma cripta: la primera hace la consulta y la guarda; la segunda la lee del disco sin consultar.

**Acceptance Scenarios**:

1. **Dado** una cripta sin copia guardada de la ubicación de llaves, **Cuando** se inicia la partida, **Entonces** se hace exactamente una consulta de ubicación de llaves, cuenta como una solicitud en el presupuesto y aparece en el reporte de solicitudes.
2. **Dado** una entrada con llave y sala, sin enemigo, **Cuando** se obtiene la ubicación de llaves, **Entonces** esa llave está en el suelo de esa sala.
3. **Dado** una entrada con llave, sala y enemigo, **Cuando** se obtiene la ubicación de llaves, **Entonces** esa llave está en lo que suelta esa instancia de enemigo, y la sala es donde esa instancia inicia.
4. **Dado** una partida anterior en la misma cripta y la misma versión, **Cuando** se inicia una nueva partida, **Entonces** la ubicación de llaves se toma del disco y no se hace la consulta.
5. **Dado** una copia guardada para una versión anterior de la cripta, **Cuando** se inicia una partida con la versión nueva, **Entonces** la copia anterior no se usa y se consulta la ubicación vigente.
6. **Dado** el modo offline, **Cuando** se inicia una partida, **Entonces** la ubicación de llaves se lee del paquete de datos y no cuenta en el presupuesto.
7. **Dado** un paquete offline que no trae la ubicación de llaves, **Cuando** se inicia una partida, **Entonces** se informa que la ubicación de llaves no está disponible, la partida puede continuar y ese estado se distingue de una lista de llaves vacía.
8. **Dado** una respuesta con una entrada sin llave o sin sala, o con una sala que no existe en el esqueleto, **Cuando** se obtiene la ubicación de llaves, **Entonces** se informa como dato inválido de la cripta y la partida no inicia.
9. **Dado** que la consulta de ubicación de llaves falla o ya no queda presupuesto, **Cuando** se inicia la partida, **Entonces** se informa el error con la operación que falló y la partida no inicia.

---

### User Story 4 - Lo guardado por la primera parte no se mezcla con las criptas nuevas (Priority: P3)

Como grupo, queremos que los datos guardados en disco durante la primera parte dejen de usarse automáticamente cuando el servicio publica versiones nuevas, y que el aviso de cambios en el contrato siga funcionando para lo que de verdad no conocemos.

**Why this priority**: La validación de versión ya existe; solo hay que confirmar que cubre los datos nuevos y que los avisos no se llenan de falsas alarmas.

**Independent Test**: Se deja en disco una copia de la primera parte, se inicia la misma cripta con otra versión y se revisa qué datos se usaron y qué avisos aparecieron.

**Acceptance Scenarios**:

1. **Dado** esqueleto, contenido o fichas guardados para una versión distinta de la vigente, **Cuando** se inicia una partida, **Entonces** no se usa ninguno de esos datos y se obtienen los vigentes, sin que nadie borre archivos a mano.
2. **Dado** una cripta que declara costo en sus salidas y rango en sus cazadores, **Cuando** se juega, **Entonces** no aparece ningún aviso de campo desconocido por costo ni por rango.
3. **Dado** una salida o una ficha con un campo que el contrato no declara, **Cuando** se carga, **Entonces** aparece el aviso de campo desconocido, una sola vez por campo y por tipo de dato.

---

### Edge Cases

- Un paso de un solo sentido (sin salida de vuelta) tiene el costo de la única salida que lo declara.
- Una cripta cuyas salidas no declaran costo en ninguna parte: todas cuestan 100 y la cripta se juega igual que en la primera parte.
- La misma llave aparece en varias entradas de la ubicación de llaves: se conservan todas sus ubicaciones.
- La lista de ubicación de llaves viene vacía: es un dato válido; qué significa para la partida lo decide la verificación de resolubilidad.
- Una llave está en la sala inicial: es una ubicación válida.
- Una entrada de la ubicación de llaves trae campos además de llave, sala y enemigo: el contrato lo permite, así que se ignoran sin aviso.
- La copia en disco de la ubicación de llaves está dañada o incompleta: se trata como si no existiera y se vuelve a obtener.
- Una entrada nombra una instancia de enemigo cuyo contenido todavía no se ha descargado: se acepta tal como viene; no se exige descargar contenido para comprobarla.
- Un cazador con rango 1: es un valor válido; lo que implica para su comportamiento lo define la especificación del cazador.

## Requirements *(mandatory)*

### Functional Requirements

**Costo de las salidas**

- **FR-001**: El programa MUST asignar a cada salida del esqueleto un costo de movimiento: el valor de su campo `costo` cuando viene, o 100 cuando falta o viene en null.
- **FR-002**: El costo MUST ser un entero mayor o igual que 1. Cualquier otro valor es un dato inválido de la cripta: se informa indicando la sala, la dirección y el valor recibido, y la partida no inicia.
- **FR-003**: Un paso entre dos salas MUST tener el mismo costo en ambos sentidos. Si solo una de sus dos salidas declara costo, ese valor MUST usarse en ambos sentidos. Si las dos declaran valores distintos, MUST usarse el de la salida de la sala de menor id y registrarse un aviso que nombre las dos salas y el valor usado.
- **FR-004**: En un paso de un solo sentido, el costo MUST ser el de la única salida que lo declara.
- **FR-005**: El costo de todas las salidas MUST estar disponible en cuanto se carga el esqueleto, sin depender de que se haya descargado el contenido de ninguna sala.

**Cazador y rango**

- **FR-006**: El programa MUST reconocer el comportamiento `cazador` en una ficha de enemigo, además de guardián, errante y rastreador. Una cripta con cazadores MUST poder iniciarse y jugarse sin detenerse por ese comportamiento.
- **FR-007**: Cada cazador MUST tener el rango de su ficha, un entero mayor o igual que 1 expresado en unidades de costo. Un rango presente con otro valor MUST tratarse como dato inválido de la ficha, informando su id y el valor recibido.
- **FR-008**: Cuando la ficha de un cazador no trae rango, o lo trae en null, MUST tratarse como dato inválido de la ficha, informando su id. No se usa ningún rango en su lugar.
- **FR-009**: Un rango presente en la ficha de un enemigo que no es cazador MUST ignorarse: no cambia su comportamiento ni produce avisos.
- **FR-010**: Un comportamiento distinto de los cuatro conocidos MUST seguir informándose como dato inválido, nombrando la ficha y el valor recibido.

**Ubicación de llaves**

- **FR-011**: Al iniciar una partida, el programa MUST obtener la ubicación de llaves de la cripta: por cada entrada, el id de la llave, la sala y, si la trae, la instancia de enemigo.
- **FR-012**: Una entrada con instancia de enemigo MUST interpretarse como una llave que está en lo que suelta esa instancia, con la sala igual a la sala donde esa instancia inicia. Una entrada sin enemigo MUST interpretarse como una llave en el suelo de esa sala.
- **FR-013**: La consulta de ubicación de llaves MUST contar como una solicitud dentro de `presupuesto_solicitudes`, igual que sus reintentos después de un HTTP 429, y MUST aparecer en el reporte de solicitudes de la partida.
- **FR-014**: La ubicación de llaves MUST guardarse en disco junto con los demás datos de la cripta, asociada a su versión. Mientras la versión coincida, una partida nueva MUST usar la copia guardada sin consultar al servicio.
- **FR-015**: En modo offline, la ubicación de llaves MUST leerse del paquete de datos sin hacer solicitudes y sin contar en el presupuesto.
- **FR-016**: Cuando el paquete offline no trae la ubicación de llaves, el programa MUST informar que ese dato no está disponible y la partida MUST poder continuar. Ese estado MUST distinguirse de una lista de llaves vacía. Lo que hace la verificación de resolubilidad sin ese dato lo define su propia especificación.
- **FR-017**: Una entrada sin llave o sin sala, con valores del tipo equivocado, o con una sala que no existe en el esqueleto, MUST informarse como dato inválido de la cripta, y la partida no inicia.
- **FR-018**: Si una misma llave aparece en varias entradas, MUST conservarse cada una de sus ubicaciones.
- **FR-019**: La ubicación de llaves de una misma versión de cripta MUST ser idéntica, entrada por entrada y en el mismo orden, sin importar si se obtuvo del servicio, de la copia en disco o del paquete offline.
- **FR-020**: Si la consulta falla, se agota el tiempo de espera o ya no queda presupuesto, MUST informarse el error con la operación que falló, y la partida no inicia.
- **FR-021**: Una copia en disco dañada o incompleta de la ubicación de llaves MUST tratarse como ausente.

**Versiones y avisos**

- **FR-022**: Los datos guardados en disco para una versión de cripta distinta de la vigente (esqueleto, contenido y ubicación de llaves) MUST invalidarse mediante la validación de versión que ya usa el programa al iniciar una partida, sin borrar archivos a mano. Las fichas guardadas MUST usarse solo mientras coincida la versión global del catálogo.
- **FR-023**: Los campos `costo` de las salidas y `rango` de las fichas de enemigo MUST considerarse parte del contrato conocido: su presencia no produce el aviso de campo desconocido.
- **FR-024**: Cualquier otro campo que no declare el contrato de una salida, una ficha o una colocación MUST seguir produciendo el aviso de campo desconocido, una sola vez por campo y por tipo de dato. Los campos adicionales en las entradas de ubicación de llaves no producen aviso, porque el contrato los permite.

### Key Entities *(include if feature involves data)*

- **Paso entre salas**: conecta dos salas en una dirección de cada lado. Tiene estado inicial (abierto o cerrado), una llave requerida opcional, un cierre automático opcional y, desde ahora, un costo de movimiento igual en ambos sentidos.
- **Ficha de enemigo**: define estadísticas, lo que suelta y su comportamiento, que es uno de cuatro: guardián, errante, rastreador o cazador. Solo el cazador usa rango.
- **Ubicación de llave**: indica dónde se puede obtener una llave: el id de la llave, la sala y, opcionalmente, la instancia de enemigo que la suelta. Pertenece a una cripta y es válida solo para una versión de esa cripta.
- **Versión de la cripta y versión del catálogo**: determinan si los datos guardados en disco todavía sirven. La versión de la cripta gobierna esqueleto, contenido y ubicación de llaves; la del catálogo gobierna las fichas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Toda cripta publicada por el servicio en su contrato 1.1.0 se puede iniciar, y el jugador puede entrar a cualquiera de sus salas sin que la partida se detenga por un comportamiento o un campo desconocido.
- **SC-002**: Sin copia en disco vigente, iniciar una partida hace exactamente una consulta de ubicación de llaves; con copia vigente, ninguna. En modo offline, ninguna solicitud.
- **SC-003**: Al jugar las criptas publicadas no aparece ningún aviso de campo desconocido por costo ni por rango; un campo no declarado en datos de prueba sí produce el aviso.
- **SC-004**: El costo de cualquier salida y el rango de cualquier cazador coinciden con lo que declara el servicio, o con 100 cuando la salida no declara costo, en el 100 % de los casos de prueba.
- **SC-005**: Todas las pruebas automatizadas de la primera parte siguen pasando.

## Assumptions

- El contrato HTTP del servicio en su versión 1.1.0, copiado en `cripta/docs/contrato/openapi-1.1.0.json`, es la referencia para los nombres, los tipos y los campos obligatorios de los datos nuevos.
- Las reglas que usan estos datos se especifican en otras capacidades: lo que cuesta moverse y el turno del cazador (§3.1 y §3.2), la niebla de guerra, «ir a» y mostrar los costos en la vista (§3.3, §3.4 y §7.3), y la verificación de resolubilidad (§3.5).
- Un dato inválido se trata igual que en la primera parte: se informa con un mensaje que identifica el dato. Si se detecta al iniciar la partida, la partida no inicia; si se detecta durante la partida (por ejemplo, la ficha de un cazador, que se obtiene cuando hace falta), la acción que lo necesitaba no se realiza. No se adivinan valores que la cripta no declara, salvo el costo 100 que fija el enunciado.
- La ubicación de llaves se obtiene al iniciar cualquier partida y al ejecutar solo la verificación, porque la verificación de resolubilidad se hace antes de jugar. Si hace falta también al cargar una partida guardada lo decide la especificación de resolubilidad.
- No se comprueba al iniciar que la instancia de enemigo de una ubicación de llave exista en el contenido de su sala, porque el contenido se descarga por partes durante el juego y exigirlo gastaría solicitudes.
- Las reglas de puertas de la primera parte no cambian: estado inicial, llave requerida y cierre automático se combinan como hasta ahora.
- Las criptas publicadas al 16 de noviembre de 2026 declaran el costo en ambos lados de cada paso, siempre con el mismo valor, y solo los cazadores declaran rango. La especificación cubre también los casos que esas criptas no presentan, porque la revisión usará una cripta nueva.
