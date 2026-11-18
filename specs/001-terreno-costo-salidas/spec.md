# Especificación: Terreno, costo de tránsito de las salidas

**Carpeta**: `specs/001-terreno-costo-salidas`

**Creada**: 2026-11-16

**Estado**: Borrador

**Origen**: §3.1 del enunciado de la segunda parte (`cripta/docs/SegundoProyecto-EDII-2026.md`), y los dos últimos casos del Apéndice B bajo «Terreno y cazador». Modifica la regla de costo de movimiento de P1 §2.3.

**Por qué va sola y primero**: el costo de las salidas es infraestructura de la que dependen otras tres capacidades del proyecto: la ruta más barata del cazador, el viaje automático «ir a» y las mediciones con criptas de costo variable. Entregarla por separado desbloquea al resto del equipo en vez de que esperen al cazador completo.

## Escenarios de uso y pruebas

### Historia 1 — El terreno hace que unas rutas sean más lentas que otras (Prioridad: P1)

Hasta ahora todas las salidas tardaban lo mismo en atravesarse, así que la única diferencia entre dos caminos era cuántas salas tenían. A partir de esta capacidad, cada salida declara cuánto cuesta atravesarla, y un camino de tres salas baratas puede ser más rápido que uno de dos salas caras.

Esto vale para todos los que se mueven por la cripta, no solo para el jugador: un enemigo que persigue al jugador por un pasadizo costoso llega más tarde que uno que viene por uno barato.

**Por qué esta prioridad**: sin esto no existe el terreno. Es la regla que cambia, y todo lo demás de esta especificación la acompaña.

**Prueba independiente**: se juega una partida en una cripta donde una salida declara costo 50 y otra 200, y se comprueba que el reloj avanza distinto al atravesar cada una.

**Escenarios de aceptación**:

1. **Dado** un jugador de velocidad 100 en una sala con una salida de costo 50, **cuando** la atraviesa, **entonces** su siguiente decisión ocurre 50 unidades después.
2. **Dado** el mismo jugador frente a una salida de costo 200, **cuando** la atraviesa, **entonces** su siguiente decisión ocurre 200 unidades después.
3. **Dado** un enemigo que se mueve por una salida costosa, **cuando** ejecuta su movimiento, **entonces** su siguiente turno se programa según el costo de esa salida y no según un valor fijo.
4. **Dado** un actor que atraviesa una salida, **cuando** se calcula cuánto tarda, **entonces** el tiempo es el mayor entre 1 y la división entera de `costo_de_la_salida * 100` entre la velocidad del actor.
5. **Dado** un actor de velocidad muy alta, **cuando** atraviesa una salida de costo 1, **entonces** el tiempo que consume es al menos 1 unidad y el reloj avanza. *(Apéndice B)*

---

### Historia 2 — El jugador puede decidir con el costo a la vista (Prioridad: P2)

El jugador necesita saber cuánto le va a costar cada salida antes de escoger, porque esa es ahora la decisión táctica principal: huir por el camino corto y caro, o por el largo y barato.

**Por qué esta prioridad**: sin mostrar el costo, la regla existe pero el jugador juega a ciegas y la decisión deja de tener sentido.

**Prueba independiente**: se entra a una sala con salidas de costos distintos y se comprueba que la vista los muestra.

**Escenarios de aceptación**:

1. **Dado** un jugador en una sala con varias salidas, **cuando** mira el estado de la sala, **entonces** ve el costo de cada salida junto con su dirección y su destino.
2. **Dado** una salida que no declara costo, **cuando** el jugador mira la sala, **entonces** ve el costo que esa salida tiene en efecto.

---

### Historia 3 — Las criptas sin costos declarados siguen jugándose igual (Prioridad: P2)

Las criptas de la primera parte, y las salidas de la segunda que no declaren costo, deben comportarse exactamente como antes. Nadie debería tener que modificar datos existentes para que el juego siga funcionando.

**Por qué esta prioridad**: protege todo lo que ya funciona y es lo que permite entregar esta capacidad sin romper la base. Va junto con la Historia 2 porque ambas son condiciones para dar la capacidad por terminada.

**Prueba independiente**: se juega una cripta donde ninguna salida declara costo y se compara con el resultado anterior al cambio, con la misma semilla.

**Escenarios de aceptación**:

1. **Dado** una salida que no declara costo, **cuando** alguien la atraviesa, **entonces** se comporta como si declarara costo 100.
2. **Dado** una cripta en la que ninguna salida declara costo, **cuando** se juega con la misma semilla y las mismas acciones que antes de esta capacidad, **entonces** el resultado observable es idéntico.

---

### Historia 4 — Un cambio de velocidad en pleno movimiento respeta el progreso (Prioridad: P3)

Si un actor bebe una poción de velocidad mientras está atravesando una salida larga, lo que le falta del trayecto se reajusta en proporción, en vez de empezar de nuevo o completarse de golpe.

**Por qué esta prioridad**: es un caso borde obligatorio del Apéndice B, pero se apoya en una regla que ya existe desde la primera parte; es el que más fácil se rompe al cambiar el costo del movimiento.

**Prueba independiente**: se programa el movimiento de un actor por una salida costosa, se le cambia la velocidad a mitad de camino y se comprueba el instante reprogramado.

**Escenarios de aceptación**:

1. **Dado** un actor que atraviesa una salida costosa y tiene su llegada programada, **cuando** cambia su velocidad antes de llegar, **entonces** el tiempo que le falta se reescala según la regla de P1 §2.3 y nunca queda en menos de 1 unidad. *(Apéndice B)*
2. **Dado** ese mismo actor, **cuando** se reprograma su llegada, **entonces** el cálculo usa la velocidad que tenía antes del cambio para medir lo que le faltaba.

---

### Casos borde

- Una salida declara un costo menor que 1 o un valor que no es entero: se trata como un dato inválido de la cripta y se reporta como tal, sin inventar un valor por defecto que oculte el error. El valor **vacío** no entra en este caso: el contrato lo admite y significa «sin costo propio», así que vale 100.
- Una salida declara un costo muy grande: el movimiento tarda mucho, pero el reloj sigue avanzando y la partida sigue siendo jugable; no hay tope.
- Un actor de velocidad muy alta frente a una salida de costo 1: el tiempo consumido se recorta a 1 para que el reloj siempre avance.
- Las dos salas que conecta una salida declaran costos distintos para ella: es una contradicción en los datos y debe reportarse, no resolverse en silencio escogiendo uno de los dos.
- Abrir una puerta de una salida costosa sigue costando lo que cuesta abrir una puerta; el costo de la salida solo aplica a atravesarla.

## Requisitos

### Requisitos funcionales

- **FR-001**: Cada salida de una sala DEBE tener un costo de tránsito, expresado como un entero mayor o igual que 1.
- **FR-002**: Una salida que no declara costo DEBE comportarse como si declarara 100. Declarar el campo **vacío** cuenta como no declararlo: el contrato del servicio 1.1.0 admite el valor nulo y significa que esa salida no tiene costo propio.
- **FR-003**: El costo de una salida DEBE ser el mismo en los dos sentidos.
- **FR-004**: Moverse a través de una salida DEBE consumir, en unidades de tiempo virtual, el mayor entre 1 y la división entera de `costo_de_la_salida * 100` entre la velocidad del actor. Es la misma fórmula de P1 §2.3, con el costo de la salida en lugar del valor fijo 100.
- **FR-005**: FR-004 DEBE aplicarse a todos los actores: al jugador y a todos los enemigos, sea cual sea su comportamiento.
- **FR-006**: El costo de atacar, esperar, recoger, soltar, usar, equipar y abrir puertas NO DEBE cambiar.
- **FR-007**: Los comportamientos de enemigo existentes (guardián, errante y rastreador) DEBEN conservar exactamente su lógica de decisión; lo único que cambia es cuánto tarda el movimiento que escogen.
- **FR-008**: El tiempo que consume un movimiento NUNCA DEBE ser menor que 1, de modo que el reloj virtual siempre avance.
- **FR-009**: Cuando cambia la velocidad de un actor que tiene un movimiento programado, el tiempo restante DEBE reescalarse según la regla de P1 §2.3, calculando con la velocidad anterior.
- **FR-010**: La vista DEBE mostrar el costo de cada salida de la sala en que está el jugador.
- **FR-011**: Un costo declarado que no sea un entero mayor o igual que 1 DEBE reportarse como dato inválido de la cripta, sin sustituirlo por un valor por defecto.
- **FR-012**: Una partida en una cripta donde ninguna salida declara costo DEBE producir el mismo resultado observable que antes de esta capacidad, con la misma semilla y las mismas acciones.

### Entidades

- **Salida**: la conexión entre dos salas en una dirección. Ahora tiene, además de su dirección, su sala destino y su puerta, un **costo de tránsito**: cuánto trabajo cuesta atravesarla. Es un atributo de la conexión, no de ninguna de las dos salas, y por eso vale igual en ambos sentidos.

## Criterios de éxito

- **SC-001**: Atravesar una salida de costo 50 deja al jugador listo para decidir en la mitad del tiempo virtual que atravesar una de costo 100, con la misma velocidad.
- **SC-002**: En una cripta con costos variados, un camino con más salas pero menor costo total lleva al jugador a su destino en menos tiempo virtual que uno con menos salas y mayor costo.
- **SC-003**: Jugar una cripta sin costos declarados, con la misma semilla y la misma secuencia de acciones, produce exactamente el mismo resultado que antes de esta capacidad: mismo reloj final, misma vida, mismos mensajes.
- **SC-004**: Ningún movimiento, por rápido que sea el actor o por barata que sea la salida, deja el reloj virtual sin avanzar.
- **SC-005**: El ciclo completo de eventos entre dos decisiones del jugador sigue resolviéndose en menos de 20 ms en la cripta de referencia.
- **SC-006**: Un jugador que entra a una sala puede decir, solo con lo que la vista le muestra, cuál de sus salidas es la más barata.

## Supuestos

- El costo de una salida es un dato de la cripta y llega con el esqueleto, igual que la dirección y la sala destino. Esta capacidad no define cómo se obtiene ese dato, solo qué significa.
- Un costo inválido se trata con el mismo criterio que el proyecto ya aplica a los datos malformados de una cripta: se reporta como error de datos y no se adivina un valor.
- El costo afecta únicamente al tiempo que consume el movimiento. No afecta al daño, ni a la activación de enemigos, ni a las trampas, ni al cierre automático de puertas.
- La fórmula del intervalo es la de la primera parte y no se modifica; lo único que cambia es qué número entra como costo.
- Que el jugador conozca o no el costo de una salida que todavía no ha explorado es asunto de la capacidad de niebla de guerra (§3.3), no de esta.
- Cómo se usa el costo para calcular rutas de costo mínimo es asunto de las capacidades del cazador (§3.2) y del viaje automático (§3.4). Esta capacidad solo establece que el costo existe y cuánto tarda atravesar una salida.
