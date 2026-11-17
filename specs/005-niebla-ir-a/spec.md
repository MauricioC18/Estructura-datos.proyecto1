# Especificación: Niebla de guerra y viaje automático «ir a»

**Carpeta**: `specs/005-niebla-ir-a`

**Creada**: 2026-11-16

**Estado**: Borrador

**Origen**: §3.3 y §3.4 del enunciado de la segunda parte (`cripta/docs/SegundoProyecto-EDII-2026.md`), el problema §5.3, el límite de «ir a» de §6.1, lo que §7.3 pide a la interfaz para esta capacidad y los seis casos del Apéndice B bajo «Niebla de guerra e ir a».

**Por qué va después de 001 y 002**: «ir a» minimiza la suma de los costos de las salidas, que especificó `specs/001-terreno-costo-salidas`, y desempata igual que el cazador de `specs/002-cazador-ruta-mas-barata`. Esta capacidad no cambia ninguna de las dos reglas: las aplica sobre lo que el jugador conoce en lugar de sobre la cripta completa.

**Fuera de alcance**: la verificación de resolubilidad, la línea de tiempo y sus puntos de control, el terreno y el cazador, y las banderas `--verificar`, `--forzar`, `--checkpoint-cada` y `--hasta`. Cada una vive en la especificación de su capacidad. De la línea de tiempo, esta especificación solo exige que el conocimiento del jugador se pueda recuperar tal como estaba en un instante pasado; la consulta en sí es de la otra especificación.

## Clarifications

### Session 2026-11-16

- Q: ¿Qué estado tienen las puertas de una vecina explorada por la antorcha que el jugador nunca observó? → A: Desconocido hasta que el jugador las observe. El viaje automático no las usa, porque no las recuerda abiertas.
- Q: ¿Cuándo observa el jugador una puerta: solo al entrar a una sala, o también cuando la puerta cambia mientras él está en una de sus dos salas? → A: En los dos casos: al entrar a una sala observa todas sus puertas, y mientras está en una de las dos salas que conecta una puerta, observa cada cambio de esa puerta en el instante en que ocurre.
- Q: ¿Cómo se muestra una sala avistada? → A: Como «hay algo en esa dirección», sin revelar su identificador ni su nombre.
- Q: Cuando un mismo paso cumple varios motivos de detención a la vez, ¿qué motivo se informa? → A: Todos los que se cumplieron, en un orden fijo: el orden en que FR-028 los enumera.
- Q: Si el jugador enciende la antorcha estando ya dentro de una sala, ¿se exploran en ese momento las vecinas de esa sala? → A: No. La antorcha solo explora vecinas al entrar a una sala; encenderla no explora nada hasta el siguiente movimiento.
- Q: Mientras no se publique la cripta de referencia, ¿contra qué se mide el límite de 5 ms por paso de «ir a»? → A: Contra la cripta publicada más grande y contra criptas sintéticas deterministas de al menos ese tamaño. Si se publica la cripta de referencia o se ajusta el límite, se actualiza esta especificación. *(Reemplazada por la última aclaración.)*
- Q: Si `ir a` recibe un identificador que no corresponde a ninguna sala, ¿se rechaza igual que una sala no explorada, sin revelar que no existe? → A: Sí. Mismo rechazo y mismo mensaje que una sala no explorada.
- Q: ¿«Una sala que contiene enemigos» incluye a los enemigos muertos? → A: No. Solo cuentan los enemigos vivos, estén activos o dormidos. Un enemigo muerto deja de actuar (P1 §2.6) y no detiene el viaje.
- Q: ¿La especificación debe fijar con qué criptas se mide FR-036? → A: No. El límite es el de §6.1, sobre el mapa conocido completo de la cripta de referencia. Con qué criptas se mide es una decisión del plan.
- Q: ¿Se acepta la orden `ir a` cuando la partida ya terminó? → A: No. Se rechaza sin consumir tiempo, igual que toda otra acción con la partida terminada (FR-038).

### Session 2026-11-17

- Q: Una salida puede existir en un solo sentido: la sala a la que lleva no declara la salida de vuelta. ¿Cómo la trata «ir a»? → A: La ruta solo puede atravesar cada salida en el sentido en que existe; una salida de un solo sentido no se puede recorrer al revés. Con esa restricción, la ruta sigue siendo la de menor costo (FR-023) y desempata igual (FR-024). Si existe una salida directa que el mapa recuerda abierta desde la sala del jugador hacia el destino, el viaje no puede declarar que no hay ruta conocida. *(Confirmado por el grupo: el servicio puede publicar salidas de un solo sentido.)*

## Escenarios de uso y pruebas

### Historia 1 — El jugador solo conoce lo que ha visto (Prioridad: P1)

Hasta ahora el jugador veía la cripta completa. Con la niebla de guerra conoce únicamente lo que ha explorado. Cada sala está, para él, en uno de tres estados: **explorada**, si entró a ella al menos una vez; **avistada**, si no la ha explorado pero es el destino de una salida de una sala explorada; o **desconocida**, si no es ninguna de las dos. La sala inicial está explorada desde el instante 0.

De una sala explorada sabe su nombre, sus salidas, el costo de cada salida y el estado de sus puertas según la última vez que las observó. De una avistada sabe solamente que detrás de esa salida hay algo. De una desconocida no sabe nada.

**Por qué esta prioridad**: es la regla que da sentido a todo lo demás. Sin ella, la vista sigue mostrando información que el jugador no debería tener y «ir a» no tiene sobre qué calcular.

**Prueba independiente**: se juega una cripta pequeña moviéndose por algunas salas y se comprueba, en cada instante, qué salas figuran como exploradas, avistadas y desconocidas.

**Escenarios de aceptación**:

1. **Dado** una partida recién iniciada, **cuando** el jugador todavía no ha actuado, **entonces** la sala inicial está explorada, los destinos de sus salidas están avistados y todas las demás salas son desconocidas.
2. **Dado** un jugador que entra por primera vez a una sala avistada, **cuando** se completa el movimiento, **entonces** esa sala pasa a explorada y los destinos de sus salidas que no estaban explorados pasan a avistados.
3. **Dado** una sala avistada, **cuando** el jugador consulta lo que sabe de ella, **entonces** solo sabe que hay algo en esa dirección, sin su nombre ni sus salidas.
4. **Dado** una sala que el jugador ya exploró, **cuando** vuelve a salir de ella, **entonces** sigue explorada.

---

### Historia 2 — El mapa recuerda las puertas como las vio por última vez (Prioridad: P1)

El jugador observa una puerta cuando está en cualquiera de las dos salas que conecta. Lo que su mapa guarda es el estado de esa última observación, aunque la puerta cambie después. Una puerta con cierre automático puede figurar abierta en el mapa y estar cerrada en realidad; el mapa solo se corrige cuando el jugador vuelve a observarla.

**Por qué esta prioridad**: es lo que hace que el mapa del jugador sea un conocimiento y no una copia de la realidad, y es la condición que «ir a» tiene que respetar.

**Prueba independiente**: se abre una puerta con cierre automático, el jugador se aleja, la puerta se cierra sola y se comprueba que el mapa la sigue mostrando abierta hasta que el jugador vuelve a una de sus dos salas.

**Escenarios de aceptación**:

1. **Dado** un jugador que entra a una sala, **cuando** se completa el movimiento, **entonces** el mapa registra el estado actual de todas las puertas de esa sala.
2. **Dado** una puerta que el jugador vio abierta y que se cerró cuando él ya no estaba en ninguna de sus dos salas, **cuando** el jugador consulta el mapa, **entonces** la puerta sigue figurando abierta.
3. **Dado** esa misma puerta, **cuando** el jugador entra a una de las dos salas que conecta, **entonces** el mapa pasa a mostrarla cerrada.
4. **Dado** un jugador que está en una de las dos salas que conecta una puerta, **cuando** esa puerta cambia de estado, **entonces** el mapa registra el estado nuevo en ese mismo instante.

---

### Historia 3 — La antorcha ilumina las salas vecinas (Prioridad: P2)

En la primera parte la antorcha se encendía y se apagaba sin ningún efecto. Ahora, mientras esté encendida, al entrar a una sala también quedan exploradas todas sus vecinas, a través de cualquier salida, abierta o cerrada. Iluminar una vecina revela su nombre y sus salidas, pero no su contenido: no se ven sus enemigos, sus objetos ni sus trampas, sus enemigos no se activan y sus trampas no se disparan.

**Por qué esta prioridad**: da valor a un objeto que hasta ahora no lo tenía, pero el resto de la capacidad funciona sin ella.

**Prueba independiente**: se enciende una antorcha, se entra a una sala con cuatro vecinas, una de ellas con enemigos dormidos y otra con una trampa armada, y se comprueba que las cuatro quedan exploradas sin que nada de eso se active.

**Escenarios de aceptación**:

1. **Dado** un jugador con la antorcha encendida, **cuando** entra a una sala, **entonces** todas las vecinas de esa sala quedan exploradas, tanto las que están detrás de salidas abiertas como las que están detrás de salidas cerradas. *(Apéndice B)*
2. **Dado** una vecina con enemigos dormidos y una trampa armada, **cuando** queda explorada por la antorcha, **entonces** sus enemigos siguen dormidos y su trampa sigue armada. *(Apéndice B)*
3. **Dado** una vecina explorada por la antorcha, **cuando** el jugador consulta el mapa, **entonces** conoce su nombre, sus salidas y el costo de cada una, y los destinos de esas salidas que no estaban explorados pasan a avistados.
4. **Dado** una vecina explorada por la antorcha cuyas puertas hacia otras salas el jugador nunca observó, **cuando** consulta el mapa, **entonces** esas puertas figuran con estado desconocido hasta que el jugador las observe.
5. **Dado** un jugador con la antorcha apagada, **cuando** entra a una sala, **entonces** solo esa sala pasa a explorada.
6. **Dado** un jugador dentro de una sala, **cuando** enciende la antorcha, **entonces** ninguna sala nueva pasa a explorada; las vecinas se exploran recién cuando entre a otra sala con la antorcha todavía encendida.

---

### Historia 4 — Viajar a una sala conocida sin escribir cada paso (Prioridad: P1)

El comando `ir a <sala>` lleva al jugador a una sala explorada mediante una secuencia de movimientos ordinarios. La ruta se calcula solo con lo que el jugador conoce: atraviesa únicamente salas exploradas y salidas que su mapa recuerda abiertas, minimiza la suma de los costos y, cuando varias vecinas empiezan rutas del mismo costo mínimo, da el primer paso hacia la de menor identificador, igual que el cazador.

Cada paso es una acción completa del jugador: cuesta lo que cuesta atravesar esa salida y entre un paso y el siguiente ocurren normalmente los eventos del reloj. Antes de cada paso la ruta se vuelve a calcular con lo que el jugador sabe en ese momento, de modo que si al llegar a una sala ve cerrada una puerta que recordaba abierta, el siguiente cálculo la evita. El viaje nunca abre puertas, aunque el jugador tenga la llave.

**Por qué esta prioridad**: es la mitad de la capacidad y la que el jugador usa directamente.

**Prueba independiente**: con varias salas exploradas, se pide `ir a` hacia una sala lejana y se comprueba que la secuencia de movimientos es la de menor costo, con el desempate correcto, y que el tiempo consumido es la suma de los intervalos de cada paso.

**Escenarios de aceptación**:

1. **Dado** una sala que el jugador no ha explorado, **cuando** escribe `ir a` hacia ella, **entonces** la orden se rechaza y no consume tiempo. *(Apéndice B)*
2. **Dado** dos rutas conocidas hacia el destino, una de menos salas y mayor costo y otra de más salas y menor costo, **cuando** el jugador viaja, **entonces** sigue la de menor costo.
3. **Dado** dos vecinas que empiezan rutas conocidas del mismo costo mínimo, **cuando** el jugador viaja, **entonces** el primer paso va a la de menor identificador.
4. **Dado** una ruta que mejoraría pasando por una puerta cerrada de la que el jugador tiene la llave, **cuando** viaja, **entonces** no abre la puerta y sigue por las salidas que recuerda abiertas.
5. **Dado** un viaje de varios pasos, **cuando** termina, **entonces** cada paso consumió el tiempo de un movimiento por esa salida y entre paso y paso se ejecutaron los eventos del reloj que correspondían.
6. **Dado** un viaje de varios pasos, **cuando** se revisa la bitácora de reproducción, **entonces** cada paso aparece como un movimiento individual y la orden `ir a` aparece además como comentario.
7. **Dado** tres salas exploradas unidas solo por salidas de un solo sentido, de la sala 1 a la 3, de la 3 a la 2 y de la 2 a la 1, todas de costo 1 y recordadas abiertas, con el jugador en la sala 1, **cuando** escribe `ir a 3`, **entonces** el viaje atraviesa la salida directa de la 1 a la 3 en un solo paso de costo 1, y no informa que no hay ruta conocida.
8. **Dado** un destino al que el jugador solo podría llegar recorriendo al revés una salida de un solo sentido, **cuando** escribe `ir a` hacia él, **entonces** esa salida no forma parte de la ruta: el viaje sigue otra ruta conocida que respete el sentido de las salidas, o, si no la hay, se detiene antes del primer paso informando que no hay ruta conocida, sin consumir tiempo.

---

### Historia 5 — El viaje se detiene cuando algo importa (Prioridad: P1)

Viajar no es un atajo para ignorar el peligro. El viaje se detiene cuando el jugador llega al destino, cuando entra a una sala que contiene enemigos vivos, activos o dormidos, cuando recibe daño, sea de un ataque, de un veneno o de una trampa, y cuando deja de existir una ruta conocida hacia el destino. La interfaz le dice al jugador por qué se detuvo.

**Por qué esta prioridad**: sin estas paradas, un solo comando podría llevar al jugador a la muerte sin darle oportunidad de decidir.

**Prueba independiente**: se preparan viajes que terminan por cada uno de los motivos y se comprueba que el jugador queda donde corresponde y que el motivo informado es el correcto.

**Escenarios de aceptación**:

1. **Dado** un mapa que recuerda abierta una puerta que en realidad está cerrada, **cuando** el viaje llega a una sala desde la que el jugador observa esa puerta, **entonces** el mapa se actualiza y la ruta se vuelve a calcular; si ya no queda ruta conocida, el viaje se detiene sin consumir tiempo adicional. *(Apéndice B)*
2. **Dado** un viaje cuya ruta pasa por una sala con enemigos dormidos, **cuando** el jugador entra a esa sala, **entonces** los enemigos se activan según las reglas de la primera parte (P1 §2.4) y el viaje se detiene. *(Apéndice B)*
3. **Dado** un viaje durante el cual un enemigo ataca al jugador, un veneno le hace daño o una trampa se dispara, **cuando** termina el paso en que eso ocurrió, **entonces** el viaje se detiene.
4. **Dado** un viaje que llega a su destino, **cuando** se completa el último paso, **entonces** el viaje se detiene e informa que llegó.
5. **Dado** un jugador que inició un viaje, **cuando** el viaje se detiene, **entonces** la interfaz informa el motivo.
6. **Dado** un viaje cuyo último paso llega al destino y ese destino contiene enemigos, **cuando** el viaje se detiene, **entonces** la interfaz informa los dos motivos, primero la llegada y después los enemigos.
7. **Dado** un viaje que se detuvo después de varios pasos, **cuando** el jugador usa un pergamino de retroceso, **entonces** se revierte únicamente el último paso y el viaje no continúa. *(Apéndice B)*

---

### Historia 6 — El conocimiento es parte de la partida (Prioridad: P2)

Lo que el jugador sabe del mapa no es un adorno de la interfaz: es estado del juego. Se guarda con la partida, el pergamino de retroceso lo revierte junto con todo lo demás y debe poder recuperarse tal como estaba en cualquier instante pasado.

**Por qué esta prioridad**: si el conocimiento no se revirtiera, un pergamino dejaría al jugador sabiendo cosas de una historia que ya no ocurrió; si no se guardara, cargar una partida le devolvería el mapa completo o lo dejaría a ciegas.

**Prueba independiente**: se entra a una sala con la antorcha encendida, se usa un pergamino y se compara el conocimiento con el que había antes de entrar.

**Escenarios de aceptación**:

1. **Dado** un jugador que entró a una sala con la antorcha encendida y exploró así varias vecinas, **cuando** usa un pergamino de retroceso, **entonces** la sala y las vecinas exploradas en esa entrada vuelven al estado que tenían antes. *(Apéndice B)*
2. **Dado** una acción revertida con un pergamino durante la cual el mapa actualizó el estado recordado de una puerta, **cuando** se completa el retroceso, **entonces** el mapa recuerda la puerta como la recordaba antes de esa acción.
3. **Dado** una partida guardada, **cuando** se carga, **entonces** el jugador conoce exactamente las mismas salas y recuerda las mismas puertas en el mismo estado que al guardarla.
4. **Dado** la misma cripta, la misma semilla y la misma secuencia de acciones, **cuando** se juega dos veces, **entonces** el conocimiento del jugador es el mismo en cada instante.

---

### Historia 7 — Ver lo que se conoce (Prioridad: P2)

El jugador tiene un comando para ver su mapa conocido: las salas exploradas, sus salidas y las salas avistadas. La vista de la sala actual también se deriva solo de lo que el jugador sabe, y los cazadores se distinguen a simple vista de los demás enemigos.

**Por qué esta prioridad**: sin poder ver el mapa, el jugador no sabe a qué sala puede pedir `ir a`.

**Prueba independiente**: se exploran algunas salas, se pide el mapa y se compara lo mostrado con lo que el jugador debería conocer.

**Escenarios de aceptación**:

1. **Dado** un jugador que exploró varias salas, **cuando** pide ver el mapa, **entonces** ve cada sala explorada con su identificador, su nombre, sus salidas, el costo de cada salida y el estado recordado de cada puerta.
2. **Dado** una salida de una sala explorada que lleva a una sala avistada, **cuando** el jugador ve el mapa o la sala actual, **entonces** se muestra como «hay algo en esa dirección», sin su identificador ni su nombre.
3. **Dado** el comando para ver el mapa, **cuando** el jugador lo usa, **entonces** no consume tiempo, no se registra como acción y no cambia nada de la partida.
4. **Dado** una sala con un cazador y otros enemigos, **cuando** la vista muestra la sala, **entonces** el cazador se distingue de los demás.
5. **Dado** una sala desconocida, **cuando** el jugador ve el mapa, **entonces** esa sala no aparece de ninguna forma.

---

### Casos borde

- **`ir a` hacia la sala en la que ya está el jugador**: se rechaza sin consumir tiempo.
- **`ir a` con un identificador que no corresponde a ninguna sala de la cripta**: se rechaza igual que una sala no explorada, sin revelar si esa sala existe.
- **`ir a` hacia una sala explorada a la que no lleva ninguna ruta conocida**: el viaje se detiene antes del primer paso, informa que no hay ruta conocida y no consume tiempo.
- **Salidas de un solo sentido**: una salida puede existir solo desde una sala hacia otra, sin que la segunda declare la vuelta. La ruta solo la atraviesa en el sentido en que existe, y el costo de la ruta se cuenta con las salidas en ese sentido. Que la vuelta no exista no impide usar la ida: si hay una salida directa recordada abierta hacia el destino, el viaje no se declara sin ruta.
- **Iniciar un viaje desde una sala con enemigos**: se permite. Solo detiene el viaje **entrar** a una sala con enemigos, no partir de una.
- **Un enemigo entra a la sala del jugador a mitad del viaje sin hacerle daño**: no es un motivo de parada por sí solo; si lo ataca, el daño sí lo es.
- **El primer paso de cada cálculo atraviesa siempre una puerta de la sala actual**: como el jugador observa las puertas de la sala en la que está, el mapa nunca le hace intentar cruzar una puerta que en ese instante está cerrada sin haberla visto cerrada antes.
- **La sala siguiente no puede cargarse porque se agotó el presupuesto de solicitudes**: el viaje se detiene con su propio motivo y ese paso no consume tiempo.
- **La partida termina a mitad del viaje**, por la muerte del jugador o porque entra a la sala de salida: el viaje se detiene.
- **`ir a` con la partida ya terminada**: se rechaza sin consumir tiempo, como cualquier otra acción (FR-038).
- **El jugador usa un pergamino después de un viaje**: se revierte solo el último paso; el viaje no se reanuda.
- **La antorcha se apaga a mitad de un viaje**: las entradas posteriores ya no exploran vecinas; lo explorado hasta ese momento queda explorado.
- **Una vecina ya explorada vuelve a quedar al alcance de la antorcha**: sigue explorada; la antorcha no le quita ni le cambia nada.
- **Una salida cerrada con llave hacia una vecina**: la antorcha explora esa vecina igual, porque explora a través de cualquier salida.
- **Una sala desconocida a la que llega un enemigo**: el jugador no sabe nada de ella ni de lo que pasa ahí.

## Requisitos

### Requisitos funcionales

**Conocimiento del jugador**

- **FR-001**: Para el jugador, cada sala de la cripta DEBE estar en exactamente uno de tres estados: explorada, avistada o desconocida.
- **FR-002**: La sala inicial DEBE estar explorada desde el instante 0.
- **FR-003**: Una sala DEBE pasar a explorada cuando el jugador entra a ella, sea con un movimiento escrito por el jugador o con un paso de un viaje, y DEBE seguir explorada mientras ninguna reversión deshaga esa entrada.
- **FR-004**: Una sala no explorada DEBE estar avistada si es destino de alguna salida de una sala explorada, y desconocida en caso contrario.
- **FR-005**: De una sala explorada, el jugador DEBE conocer su nombre, sus salidas, el costo de cada salida y el estado de cada una de sus puertas según la última observación. De una sala avistada DEBE conocer únicamente que hay algo detrás de esa salida, sin su identificador ni su nombre. De una sala desconocida NO DEBE conocer nada.
- **FR-006**: El jugador DEBE observar una puerta cuando está en cualquiera de las dos salas que conecta. Al entrar a una sala DEBE observar todas las puertas de esa sala, y mientras esté en una de las dos salas que conecta una puerta DEBE observar cada cambio de esa puerta en el instante en que ocurre.
- **FR-007**: El mapa del jugador DEBE recordar el estado de cada puerta tal como estaba en su última observación, aunque la puerta haya cambiado después.
- **FR-008**: Una puerta que el jugador nunca observó, como las de una vecina explorada por la antorcha que no la conectan con la sala del jugador, DEBE figurar en el mapa con estado desconocido hasta que el jugador la observe.

**Antorcha**

- **FR-009**: Mientras la antorcha esté encendida, al entrar a una sala DEBEN quedar exploradas, además de esa sala, todas sus vecinas, a través de cualquier salida, abierta o cerrada.
- **FR-010**: Explorar una vecina con la antorcha DEBE revelar su nombre, sus salidas y el costo de cada salida, y NO DEBE revelar su contenido, activar sus enemigos ni disparar sus trampas. NO DEBE contar como que el jugador entró a esa vecina.
- **FR-011**: Una sala explorada por la antorcha DEBE seguir explorada después de que la antorcha se apague.
- **FR-037**: Encender la antorcha NO DEBE explorar ninguna sala por sí mismo. La antorcha solo explora vecinas al entrar a una sala mientras está encendida.

**Separación entre el mapa y el conocimiento**

- **FR-012**: Todo lo que la interfaz muestra del mapa y todo lo que usa el viaje automático DEBE derivarse exclusivamente del conocimiento del jugador. Lo que el programa descargue o conserve para su propio funcionamiento NO DEBE contar como conocimiento del jugador.
- **FR-013**: El conocimiento del jugador NO DEBE afectar las decisiones de los enemigos ni ninguna otra regla del juego distinta de lo que se muestra y del viaje automático.

**El conocimiento como estado del juego**

- **FR-014**: El conocimiento del jugador DEBE guardarse con la partida, y cargar la partida DEBE restaurarlo idéntico: las mismas salas exploradas y el mismo estado recordado de cada puerta.
- **FR-015**: El pergamino de retroceso DEBE revertir todos los cambios de conocimiento ocurridos en el intervalo que revierte: las salas exploradas en ese intervalo, por entrada o por antorcha, vuelven a su estado anterior, y cada puerta recordada vuelve al estado que el mapa recordaba antes.
- **FR-016**: El conocimiento del jugador DEBE poder recuperarse tal como estaba en cualquier instante pasado de la historia vigente de la partida.
- **FR-017**: La misma cripta, la misma semilla y la misma secuencia de acciones DEBEN producir el mismo conocimiento del jugador en cada instante.

**Lo que ve el jugador**

- **FR-018**: La interfaz DEBE ofrecer un comando para ver el mapa conocido, que muestre cada sala explorada con su identificador y su nombre, y cada una de sus salidas con su dirección, su costo, el estado recordado de su puerta y su destino. El destino DEBE mostrarse como lo permite FR-005.
- **FR-019**: Ver el mapa conocido NO DEBE consumir tiempo virtual, NO DEBE registrarse como acción del jugador y NO DEBE modificar ningún estado de la partida.
- **FR-020**: La vista de la sala actual DEBE mostrar sus salidas según el conocimiento del jugador, con el mismo criterio de FR-005 para los destinos.
- **FR-021**: La vista DEBE distinguir a los cazadores de los demás enemigos.

**Viaje automático «ir a»**

- **FR-022**: El jugador DEBE poder ordenar `ir a <sala>`, donde `<sala>` es el identificador numérico de una sala. La orden DEBE aceptarse solo si la sala está explorada y no es la sala actual del jugador; en cualquier otro caso DEBE rechazarse sin consumir tiempo y sin registrarse como acción. Un identificador que no corresponde a ninguna sala DEBE rechazarse con el mismo mensaje que una sala no explorada, sin revelar que no existe.
- **FR-038**: Con la partida terminada, la orden `ir a` DEBE rechazarse sin consumir tiempo, sin registrarse como acción y sin mover al jugador, igual que toda otra acción del jugador.
- **FR-023**: La ruta DEBE atravesar únicamente salas exploradas y únicamente salidas cuya puerta el mapa del jugador recuerda abierta, y DEBE minimizar la suma de los costos de las salidas recorridas.
- **FR-024**: Entre las salas vecinas que empiezan una ruta conocida de costo mínimo, el primer paso DEBE ir a la de menor identificador. Cuando dos salidas distintas que el mapa recuerda abiertas llevan a esa misma vecina con costos distintos, DEBE atravesar la más barata de las dos. Es el mismo criterio que FR-008 de `specs/002-cazador-ruta-mas-barata`.
- **FR-025**: Cada paso DEBE ser un movimiento ordinario y una acción completa del jugador, sujeto a todas las reglas de un movimiento escrito a mano: su costo, la disponibilidad del contenido de la sala destino, la activación de enemigos, las trampas, el rastro y la victoria. Entre un paso y el siguiente DEBEN ejecutarse normalmente los eventos del reloj.
- **FR-026**: La ruta DEBE recalcularse antes de cada paso con el conocimiento vigente en ese instante.
- **FR-027**: El viaje NO DEBE abrir puertas, aunque el jugador tenga la llave.
- **FR-028**: El viaje DEBE detenerse cuando ocurra cualquiera de estas condiciones:
  - (a) el jugador llega al destino;
  - (b) el jugador entra a una sala que contiene enemigos vivos, activos o dormidos;
  - (c) el jugador recibe daño de cualquier origen, sea un ataque, un veneno o una trampa;
  - (d) no existe una ruta conocida hacia el destino, en cuyo caso NO DEBE consumir tiempo adicional;
  - (e) la partida termina;
  - (f) el contenido de la sala siguiente no puede obtenerse, en cuyo caso ese paso NO DEBE consumir tiempo.
- **FR-029**: La interfaz DEBE informar al jugador el motivo por el que se detuvo el viaje. Si en el mismo paso se cumplen varios motivos, DEBE informarlos todos, en el orden en que FR-028 los enumera.
- **FR-030**: Partir de una sala que contiene enemigos NO DEBE impedir ni detener el viaje.
- **FR-031**: En la bitácora de reproducción, cada paso DEBE registrarse como un movimiento individual, igual que uno escrito a mano, y la orden `ir a` DEBE registrarse además como comentario. Reproducir esa bitácora DEBE producir la misma partida.
- **FR-032**: El pergamino de retroceso usado después de un viaje DEBE revertir únicamente el último paso, porque cada paso es una acción del jugador, y el viaje NO DEBE reanudarse.

### Requisitos de rendimiento

- **FR-033**: Consultar si una sala está explorada, avistada o desconocida, y consultar el estado recordado de una puerta, NO DEBE costar más a medida que crece el mapa conocido.
- **FR-034**: Explorar salas nuevas DEBE costar en proporción a la cantidad de salas reveladas, y no al tamaño del mapa conocido.
- **FR-035**: Registrar y revertir los cambios de conocimiento de una acción DEBE costar en proporción a esos cambios, y no al tamaño del mapa conocido.
- **FR-036**: Calcular un paso de «ir a» con el mapa conocido completo de la cripta de referencia DEBE tomar 5 ms o menos en el equipo local, sin contar red ni la presentación en pantalla.

### Entidades

- **Conocimiento del jugador**: lo que el jugador sabe del mapa en un instante: qué salas exploró y qué estado recuerda de cada puerta que observó. Es estado del juego, no de la interfaz.
- **Estado de una sala para el jugador**: explorada, avistada o desconocida. Las avistadas y las desconocidas se deducen de las exploradas y de las salidas de estas.
- **Puerta recordada**: el estado de una puerta tal como el jugador la vio por última vez: abierta, cerrada o desconocida si nunca la observó. Puede no coincidir con el estado real.
- **Viaje**: una orden `ir a` en curso. Tiene un destino, avanza de a un paso y termina con un motivo de detención.
- **Motivo de detención**: por qué terminó un viaje: llegada, sala con enemigos, daño recibido, sin ruta conocida, partida terminada o contenido no disponible.

## Criterios de éxito

- **SC-001**: Cada uno de los seis casos del Apéndice B bajo «Niebla de guerra e ir a» tiene al menos una prueba automatizada que lo ejercita y cita el requisito que comprueba.
- **SC-002**: En partidas con puertas que se abren y se cierran solas, el mapa del jugador nunca muestra para una puerta un estado distinto del que tenía en la última observación del jugador, en todos los instantes comprobados.
- **SC-003**: Reproducir la bitácora de una partida que usó `ir a` produce exactamente la misma partida, con el mismo conocimiento del jugador al final.
- **SC-004**: Después de cada pergamino de retroceso, el conocimiento del jugador es idéntico al que tenía antes de la acción revertida, incluidas las entradas con la antorcha encendida.
- **SC-005**: Guardar y cargar una partida deja al jugador con exactamente el mismo conocimiento.
- **SC-006**: Un paso de «ir a» con el mapa conocido completo de la cripta de referencia se calcula en 5 ms o menos, según una medición del modo de mediciones del programa.
- **SC-007**: Está medido que, al multiplicar el tamaño del mapa conocido, el costo de consultar el estado de una sala o de una puerta no crece en la misma proporción, y que explorar *k* salas nuevas cuesta en proporción a *k*.
- **SC-008**: Ningún viaje atraviesa una salida cuya puerta el jugador no recordaba abierta, ni abre una puerta.
- **SC-009**: Las 945 pruebas anteriores a esta capacidad siguen pasando sin modificarlas, con dos excepciones previstas: las que fijan la versión del formato del archivo de partida, porque guardar el conocimiento cambia ese formato, y las que fijan cómo la vista muestra las salidas hacia salas que el jugador no ha explorado. Cualquier otra prueba que falle es un defecto, no una prueba desactualizada.

## Supuestos

- `<sala>` en `ir a <sala>` es el identificador numérico de la sala. *(Supuesto del grupo.)*
- `ir a` hacia la sala actual se rechaza sin consumir tiempo. *(Supuesto del grupo.)*
- Se puede iniciar un viaje desde una sala con enemigos; el viaje se detiene solo al **entrar** a una sala con enemigos. *(Supuesto del grupo.)*
- Si el presupuesto de solicitudes de red impide cargar la sala siguiente, el viaje se detiene con motivo propio y sin consumir tiempo. *(Supuesto del grupo.)* Es el mismo trato que la primera parte ya da a un movimiento escrito a mano cuyo contenido no puede obtenerse.
- Pergamino durante un viaje: como `ir a` es una sola orden, el jugador no puede intercalar el pergamino entre dos pasos. «Durante un viaje» se entiende así: el viaje se detiene, el pergamino revierte el último paso y el viaje no se reanuda solo. *(Supuesto del grupo.)*
- «Recibir daño» incluye cualquier pérdida de vida del jugador mientras viaja: ataques, veneno y trampas. *(Supuesto del grupo.)*
- La orden `ir a` en sí no consume tiempo; consume tiempo cada paso, como un movimiento.
- Cómo se distingue visualmente a un cazador es decisión de la interfaz; esta especificación solo exige que se distinga.
- La cripta de referencia de §6.1 ya está publicada. Cómo se mide FR-036 es una decisión del `plan.md`. Si el profesor ajusta el límite (§6.1 lo anuncia como enmienda de una «§2.7» que el enunciado no contiene), se actualiza esta especificación.
- Cómo se almacena el conocimiento, cómo se calcula la ruta y si se comparte el cálculo con el cazador son asuntos del `plan.md` (§5.3 pide justificar esto último allí). Esta especificación solo fija qué conoce el jugador, qué ruta es la correcta y cuándo se detiene el viaje.
- Cómo se guarda el conocimiento en el archivo de partida y cómo se recupera por instante para la línea de tiempo se coordina con las capacidades de guardado y de línea de tiempo; esta especificación solo exige que ambas cosas sean posibles y fieles.
