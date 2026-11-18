# Especificación: La línea de tiempo, consultar la partida en cualquier instante pasado

**Carpeta**: `specs/003-linea-de-tiempo`

**Creada**: 2026-11-16

**Estado**: Borrador

**Origen**: §3.6 del enunciado de la segunda parte (`cripta/docs/SegundoProyecto-EDII-2026.md`), el problema de estructuras de datos §5.5, y cuatro casos del Apéndice B bajo «Línea de tiempo». Se apoya en el pergamino de retroceso de P1 §2.11 y en el guardado binario de P1 §4.10, y no modifica ninguno de los dos.

**Qué la distingue del pergamino**: el pergamino **cambia** la partida y solo alcanza cinco acciones atrás. La línea de tiempo **no cambia nada** y alcanza hasta el instante 0. Son capacidades independientes: la primera es una jugada, la segunda es una consulta.

## Escenarios de uso y pruebas

### Historia 1 — El jugador puede mirar hacia atrás sin deshacer nada (Prioridad: P1)

En una partida larga el jugador pierde el hilo de lo que pasó: cuándo se envenenó, en qué sala dejó el martillo, cuánta vida tenía antes de aquella pelea. Hasta ahora la única forma de volver atrás era el pergamino, que además de mostrar **deshace**, solo llega cinco acciones y se consume.

La línea de tiempo le deja preguntar por cualquier instante de la partida y recibir una foto de cómo estaba todo en ese momento: el reloj, dónde estaba, cómo estaba de vida y de estadísticas, qué cargaba, qué efectos lo afectaban, qué enemigos había en su sala y con cuánta vida, y cuánto conocía del mapa. Preguntar no cuesta tiempo virtual, no cuenta como una acción y no toca la partida.

Puede preguntar de dos formas: por un instante del reloj, o por el número de una acción suya, que es como la gente recuerda lo que hizo («¿cómo estaba antes de mi décima jugada?»).

**Por qué esta prioridad**: es la capacidad. Todo lo demás la acota, la protege o la hace barata.

**Prueba independiente**: se juega una partida, se consulta un instante pasado y se comprueba que el resumen coincide con el estado que la partida tuvo de verdad en ese instante.

**Escenarios de aceptación**:

1. **Dado** una partida en curso con el reloj en 4000, **cuando** el jugador consulta el instante 1500, **entonces** recibe el estado que la partida tuvo en 1500, no el actual.
2. **Dado** el mismo instante consultado, **cuando** se compara el resumen con el estado real que hubo en 1500, **entonces** coincide en reloj, sala, vida, estadísticas, inventario, efectos activos y enemigos de esa sala con su vida.
3. **Dado** una partida con más de cinco acciones del jugador, **cuando** se consulta un instante anterior a las últimas cinco, **entonces** la consulta funciona: la línea no está limitada como el pergamino.
4. **Dado** un número de acción del jugador, **cuando** se consulta por ese número, **entonces** se recibe el estado justo **antes** de tomar esa acción.
5. **Dado** un instante al que le corresponde una decisión del jugador, **cuando** se consulta, **entonces** el estado es el de justo antes de tomarla, no el de después.
6. **Dado** un instante que cae entre dos eventos, **cuando** se consulta, **entonces** el estado incluye todos los eventos de tiempo menor o igual que el pedido y ninguno posterior.
7. **Dado** una consulta cualquiera, **cuando** termina, **entonces** el reloj, la vida, el inventario, la agenda de eventos y las acciones que quedan por revertir están exactamente como antes de consultar.
8. **Dado** el mismo instante, **cuando** se consulta dos veces, **entonces** el resumen es idéntico.
9. **Dado** varios eventos que ocurren en el mismo instante t, por ejemplo dos enemigos que atacan a la vez, **cuando** se consulta t, **entonces** el estado es el de después de todos ellos. *(Apéndice B)*

---

### Historia 2 — Preguntar por algo que no pasó se rechaza (Prioridad: P1)

No se puede consultar el futuro. Si el jugador pide un instante que todavía no llegó, o el número de una acción que no ha tomado, el programa se lo dice y no inventa nada.

**Por qué esta prioridad**: es un caso borde obligatorio y es lo que impide que la capacidad devuelva una respuesta sin sentido en vez de un error.

**Prueba independiente**: se consulta un instante mayor que el reloj actual y se comprueba que la consulta se rechaza con un mensaje.

**Escenarios de aceptación**:

1. **Dado** una partida con el reloj en 4000, **cuando** el jugador consulta el instante 5000, **entonces** la consulta se rechaza con un mensaje que lo explica, y nada cambia. *(Apéndice B)*
2. **Dado** una partida con doce acciones tomadas, **cuando** el jugador consulta la acción número 20, **entonces** la consulta se rechaza.
3. **Dado** una consulta rechazada, **cuando** termina, **entonces** no consumió tiempo virtual ni contó como acción.
4. **Dado** el instante exacto del reloj actual, **cuando** se consulta, **entonces** **sí** se acepta: el presente es parte de la historia.
5. **Dado** el instante 0, **cuando** se consulta, **entonces** se acepta y devuelve el estado con que empezó la partida.

---

### Historia 3 — Lo que el pergamino borró deja de estar en la historia (Prioridad: P2)

Si el jugador usa un pergamino, la acción revertida no ocurrió: la línea de tiempo cuenta la historia de la partida **tal como quedó**, no todo lo que se intentó. Consultar aquella acción ya no es posible, porque ya no existe.

**Por qué esta prioridad**: es el otro caso borde obligatorio, y es donde las dos capacidades se tocan. Si la línea guardara lo revertido, mostraría una historia que contradice la partida.

**Prueba independiente**: se juega, se usa un pergamino y se comprueba que el instante revertido ya no se puede consultar y que el último consultable es el anterior a esa acción.

**Escenarios de aceptación**:

1. **Dado** una partida en la que el jugador acaba de usar un pergamino, **cuando** consulta la línea de tiempo, **entonces** no aparece la acción revertida ni nada de lo que ocurrió durante ella. *(Apéndice B)*
2. **Dado** esa misma partida, **cuando** el jugador consulta el instante en que estaba la acción revertida, **entonces** la consulta se rechaza, porque ese instante ya es futuro respecto del reloj.
3. **Dado** una partida con varios pergaminos usados seguidos, **cuando** se consulta, **entonces** la línea refleja solo las acciones que quedaron.
4. **Dado** un pergamino usado, **cuando** el jugador sigue jugando y toma acciones nuevas, **entonces** la línea continúa desde donde quedó y las acciones nuevas se pueden consultar.
5. **Dado** el pergamino, **cuando** se usa, **entonces** sigue limitado a cinco acciones: la línea de tiempo no amplía cuánto se puede deshacer.

---

### Historia 4 — Consultar sigue siendo barato en una partida larga (Prioridad: P2)

Una partida puede tener cientos de acciones. Consultar un instante del principio no puede costar recorrer toda la partida, ni el programa puede guardarse una copia completa del mundo por cada acción, porque la memoria se iría de las manos.

El programa guarda copias completas solo de vez en cuando, cada cierta cantidad de acciones del jugador, y entre una y otra guarda únicamente lo necesario para reconstruir. Así cualquier consulta queda a poca distancia de una copia, y la memoria crece con lo que de verdad pasó y no con el tamaño del mundo multiplicado por las acciones.

Cada cuántas acciones se guarda una copia es configurable, porque es un intercambio: más copias, consultas más rápidas y más memoria.

**Por qué esta prioridad**: sin esto la capacidad funciona en una partida de prueba y se cae en la cripta de la revisión, que es más grande. Y es lo que §5.5 evalúa.

**Prueba independiente**: se juegan dos partidas, una de 50 acciones y otra de 500, y se comprueba que consultar el instante inicial cuesta prácticamente lo mismo en las dos.

**Escenarios de aceptación**:

1. **Dado** una partida de 500 acciones, **cuando** se consulta cualquier instante, **entonces** la reconstrucción no pasa por más acciones del jugador que la cantidad configurada entre copias.
2. **Dado** una partida de 50 acciones y otra de 500, **cuando** se consulta el instante inicial en ambas, **entonces** las dos consultas cuestan prácticamente lo mismo.
3. **Dado** una partida de 500 acciones, **cuando** se mide la memoria de la línea, **entonces** no es 500 veces el tamaño del estado.
4. **Dado** un instante pedido, **cuando** el programa busca de qué copia partir, **entonces** esa búsqueda no recorre todas las copias una por una.
5. **Dado** un pergamino, **cuando** se usa y la línea se recorta, **entonces** recortar cuesta lo mismo en una partida de 50 acciones que en una de 500.

---

### Historia 5 — La historia sobrevive a guardar y cargar (Prioridad: P3)

Si el jugador guarda la partida y vuelve mañana, su historia sigue ahí: puede consultar cualquier instante desde el inicio, no solo desde que cargó.

Y un archivo guardado con la primera parte, que no tiene línea de tiempo, se reconoce como incompatible en vez de cargarse a medias.

**Por qué esta prioridad**: no agrega capacidad nueva, pero sin esto la línea se pierde en cada sesión y la promesa de «desde el inicio» deja de ser cierta.

**Prueba independiente**: se juega, se guarda, se carga en otra sesión y se consulta un instante anterior al guardado.

**Escenarios de aceptación**:

1. **Dado** una partida guardada después de 40 acciones, **cuando** se carga y se consulta el instante de la acción 10, **entonces** el resumen es el mismo que habría dado antes de guardar.
2. **Dado** una partida cargada, **cuando** el jugador sigue jugando, **entonces** la línea continúa sin cortes y cubre tanto lo anterior al guardado como lo nuevo.
3. **Dado** un archivo guardado por la primera parte, **cuando** se intenta cargar, **entonces** se reconoce como incompatible y se dice por qué, sin leerlo a medias.

---

### Historia 6 — Consultar una partida registrada sin jugarla (Prioridad: P3)

Quien revisa una partida ya jugada no quiere volver a jugarla: quiere reproducir su bitácora y ver cómo estaba todo en un instante, con el mismo resumen que da la consulta en partida. Si pide un instante al que la partida nunca llegó, porque terminó antes, lo útil es ver cómo quedó al final y saber que terminó antes, no un rechazo: la partida ya no puede avanzar, así que ese instante nunca va a existir.

**Por qué esta prioridad**: es un caso borde obligatorio, pero se apoya en una consulta que ya existe (FR-014).

**Prueba independiente**: se juega una partida corta, se reproduce su bitácora hasta un instante mayor que el reloj final y se comprueba que se muestra el resumen del estado final con un aviso de que la partida terminó antes.

**Escenarios de aceptación**:

1. **Dado** la bitácora de una partida cuyo reloj quedó en 4000 al terminar, **cuando** se reproduce hasta el instante 5000, **entonces** se muestra el resumen del estado final, el del instante 4000, y se indica que la partida terminó antes del instante pedido. *(Apéndice B)*

---

### Casos borde

- **El instante 0 y el instante exacto del reloj actual**: los dos son consultables. El primero da el estado inicial; el segundo, el presente.
- **Un instante que cae exactamente sobre un evento**: ese evento cuenta como ejecutado, porque el estado en el instante t incluye todos los eventos de tiempo menor o igual que t.
- **Una consulta antes de la primera acción del jugador**: válida, y devuelve el estado inicial.
- **Una copia completa por cada acción**: es el extremo configurable; vuelve las consultas inmediatas y la memoria la peor posible. Debe seguir funcionando, y sirve de referencia para medir.
- **La cantidad entre copias mayor que el total de acciones de la partida**: existe una sola copia, la inicial, y las consultas reconstruyen desde ahí. Debe seguir funcionando.
- **Varios pergaminos usados seguidos**: la línea se recorta una vez por cada uno y queda consistente.
- **Una consulta en una partida ya terminada**: válida; la historia no deja de existir porque la partida acabó.
- **El mapa conocido todavía no existe en el programa**: el resumen debe poder construirse igual y decir que ese dato no está disponible, en vez de fallar. Cuando la niebla de guerra exista, el mismo resumen lo incluye sin que cambie el resto.
- **Una consulta con un instante negativo o con un texto que no es un número**: se rechaza con un mensaje, como cualquier dato mal escrito.
- **Reproducir una bitácora hasta exactamente el instante en que terminó la partida**: no es posterior al final, así que se muestra el resumen de ese instante sin el aviso de que la partida terminó antes. Esto no cambia la consulta en partida: ahí un instante posterior al reloj sigue rechazándose (FR-009), porque la partida todavía puede llegar a él.

## Requisitos

### Requisitos funcionales

- **FR-001**: El programa DEBE poder informar el estado que la partida tuvo en cualquier instante entre 0 y el reloj actual, sea cual sea la cantidad de acciones transcurridas.
- **FR-002**: El estado en el instante *t* DEBE ser el estado después de ejecutar todos los eventos de tiempo menor o igual que *t*. Si a *t* le corresponde una decisión del jugador, DEBE ser el estado justo antes de tomarla.
- **FR-003**: La consulta DEBE aceptarse de dos formas: por un instante del reloj, y por el número de una acción del jugador, en cuyo caso devuelve el estado justo antes de esa acción.
- **FR-004**: El resumen de un instante DEBE incluir al menos: el reloj, la sala del jugador, su vida y sus estadísticas, su inventario, los efectos activos, los enemigos de esa sala con su vida, y el mapa conocido en ese momento.
- **FR-005**: Una consulta NO DEBE consumir tiempo virtual.
- **FR-006**: Una consulta NO DEBE registrarse como una acción del jugador ni aparecer en la bitácora de reproducción.
- **FR-007**: Una consulta NO DEBE alterar ningún estado de la partida: ni el reloj, ni los actores, ni las puertas, ni los objetos, ni la agenda de eventos, ni los efectos.
- **FR-008**: Una consulta NO DEBE alterar el historial del pergamino de retroceso ni cuántas acciones quedan por revertir.
- **FR-009**: Una consulta de un instante posterior al reloj actual DEBE rechazarse con un mensaje que lo explique.
- **FR-010**: Una consulta del número de una acción que el jugador no ha tomado DEBE rechazarse con un mensaje que lo explique.
- **FR-011**: Las acciones revertidas con un pergamino DEBEN dejar de existir en la línea de tiempo, junto con todo lo ocurrido durante ellas.
- **FR-012**: El pergamino de retroceso DEBE seguir limitado a cinco acciones. La línea de tiempo NO DEBE ampliar ese límite ni permitir deshacer más.
- **FR-013**: La línea de tiempo DEBE cubrir desde el instante 0, también más allá de las cinco acciones que el pergamino alcanza.
- **FR-014**: El mismo resumen DEBE poder producirse sin interacción, reproduciendo una bitácora de partida hasta un instante dado, sin instanciar la vista.
- **FR-015**: La cantidad de acciones del jugador entre dos copias completas del estado DEBE ser configurable, y DEBE tener un valor por omisión.
- **FR-016**: Responder una consulta NO DEBE requerir aplicar ni deshacer los cambios de más acciones del jugador que esa cantidad configurada.
- **FR-017**: La memoria que ocupa la línea DEBE crecer con la cantidad de cambios ocurridos, más una copia completa cada esa cantidad de acciones. NO DEBE crecer como la cantidad de acciones multiplicada por el tamaño del estado.
- **FR-018**: Localizar de qué copia conviene partir para un instante pedido NO DEBE requerir examinar todas las copias.
- **FR-019**: Recortar la línea cuando se usa un pergamino NO DEBE requerir recorrer toda la historia de la partida.
- **FR-020**: Guardar y cargar la partida DEBE conservar la línea completa, de modo que después de cargar se pueda consultar cualquier instante desde el inicio.
- **FR-021**: Un archivo guardado por la primera parte, que no contiene línea de tiempo, DEBE detectarse como incompatible y rechazarse con un mensaje, sin leerse a medias.
- **FR-022**: Dos consultas del mismo instante DEBEN producir resúmenes idénticos.
- **FR-023**: El resumen de un instante DEBE coincidir con el estado que la partida tuvo de verdad en ese instante.
- **FR-025**: Al reproducir una bitácora hasta un instante posterior al reloj con que terminó la partida reproducida, el programa DEBE mostrar el resumen del estado final y DEBE indicar que la partida terminó antes del instante pedido, en vez de rechazar la consulta. La consulta en partida no cambia: FR-009 sigue vigente.

### Requisitos de rendimiento

- **FR-024**: El ciclo completo de eventos entre dos decisiones del jugador DEBE seguir resolviéndose en menos de 20 ms con la línea de tiempo activa.

### Entidades

- **Instante consultable**: un valor del reloj entre 0 y el reloj actual. No todos corresponden a una decisión del jugador: entre dos decisiones ocurren turnos de enemigos, efectos y cierres de puertas.
- **Resumen de un instante**: la foto del estado en ese instante, con los datos que enumera FR-004. Es de solo lectura y no se puede volver a jugar desde él.
- **Copia completa del estado**: una foto guardada de todo el estado mutable de la partida, tomada cada cierta cantidad de acciones del jugador, que sirve de punto de partida para reconstruir instantes cercanos.
- **Cantidad entre copias**: cuántas acciones del jugador pasan entre dos copias completas. Es el intercambio entre memoria y velocidad de consulta, y es configurable.

## Criterios de éxito

- **SC-001**: En una partida de 500 acciones del jugador, consultar cualquier instante anterior devuelve un resumen que coincide con el estado real que la partida tuvo en ese instante.
- **SC-002**: Consultar el instante inicial en una partida de 500 acciones cuesta prácticamente lo mismo que en una de 50: el costo de una consulta no crece con el largo de la partida.
- **SC-003**: Después de cien consultas seguidas, el reloj, la vida, el inventario, la agenda de eventos y las acciones que quedan por revertir son exactamente los mismos que antes de la primera consulta.
- **SC-004**: Una consulta de un instante posterior al reloj actual se rechaza con un mensaje y sin consumir tiempo virtual, en el 100 % de los casos probados.
- **SC-005**: Después de usar un pergamino, el instante de la acción revertida ya no es consultable y el último consultable es el anterior a esa acción.
- **SC-006**: Están medidos la memoria que ocupa la línea y el tiempo de una consulta para al menos tres valores de la cantidad entre copias, y el valor por omisión está justificado con esos números.
- **SC-007**: En una partida de 500 acciones, la memoria de la línea es una fracción pequeña de lo que ocuparían 500 copias completas del estado.
- **SC-008**: Recortar la línea al usar un pergamino cuesta prácticamente lo mismo en una partida de 50 acciones que en una de 500.
- **SC-009**: El ciclo completo de eventos entre dos decisiones del jugador sigue resolviéndose en menos de 20 ms con la línea activa.
- **SC-010**: Las 945 pruebas anteriores a esta capacidad siguen pasando sin modificarlas, con la excepción de las que fijan la versión del formato del archivo de partida, porque guardar la línea cambia ese formato.

## Supuestos

- **El mapa conocido del jugador es de otra capacidad.** La niebla de guerra (§3.3) la desarrolla otro integrante y todavía no existe en el programa. Esta especificación exige que el resumen incluya el mapa conocido del instante, y deja la representación de ese dato a quien lo implemente: el resumen lo obtiene de quien lo tenga. Mientras no exista, el resumen se construye igual e informa que ese dato no está disponible; cuando exista, lo incluye sin que cambie nada más.
- **Las banderas de línea de comandos las integra otro integrante.** Esta especificación define qué debe responder el programa cuando se le pide un instante y cuando se le pide reproducir una bitácora hasta un instante; cómo se escriben esas opciones en la terminal es de la integración.
- El valor por omisión de la cantidad entre copias lo fija el plan con mediciones, como exige §3.6. Esta especificación solo exige que exista, que sea configurable y que esté justificado.
- La línea describe la partida **tal como quedó**: lo revertido con un pergamino no es parte de la historia. Es lo que el enunciado fija y es lo que hace que la línea no pueda contradecir a la partida.
- Que el estado en un instante se reconstruya reconstruyendo hacia adelante desde una copia, o hacia atrás invirtiendo cambios, es decisión del plan. El enunciado permite las dos. Esta especificación solo exige que el resultado sea el estado real y que no haya que pasar por más acciones que la cantidad configurada.
- La partida es determinista por semilla desde la primera parte, y de eso depende que dos consultas del mismo instante den lo mismo.
- Una consulta es de solo lectura en el sentido fuerte: no es un punto desde el que se pueda seguir jugando. Volver a jugar desde el pasado sigue siendo cosa del pergamino, con su límite de cinco acciones.
