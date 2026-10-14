# Documento de Decisiones de Diseño — CRIPTA

Este documento contiene una sección por cada problema de §4 del enunciado.
Las secciones marcadas como pendientes aún no tienen evidencia empírica.

---

## 4.1 Qué ocurre a continuación (agenda de eventos)

**Estado:** implementado y probado con pruebas unitarias. Evidencia empírica pendiente (`--bench`).

### 1. Problema

El bucle principal del juego debe, en cada paso, obtener el evento pendiente con
menor `tiempo_siguiente` y, en caso de empate, con menor número de secuencia.

Las operaciones que el programa ejecuta realmente sobre esta estructura son:

| Operación | Cuándo ocurre | Frecuencia esperada |
| --- | --- | --- |
| Obtener y retirar el mínimo | una vez por evento procesado | decenas de miles por partida |
| Insertar un evento | al programar la siguiente acción de un actor, un pulso de efecto o un cierre de puerta | aproximadamente una por evento procesado |
| Cancelar un evento | muerte de un actor, antídoto que cancela veneno, reprogramación por cambio de velocidad | poco frecuente |

El enunciado indica que puede haber varios cientos de eventos simultáneos y que
la selección del mínimo se ejecutará decenas de miles de veces, por lo que el
costo de esa operación domina el comportamiento del bucle principal.

La frecuencia medida real se agregará cuando esté disponible el modo `--bench`.

### 2. Alternativas consideradas

| Estructura | Insertar | Consultar mínimo | Extraer mínimo |
| --- | --- | --- | --- |
| Lista sin ordenar | O(1) | O(n) | O(n) |
| Lista ordenada por inserción | O(n) | O(1) | O(1) |
| Montículo binario mínimo | O(log n) | O(1) | O(log n) |

**Lista sin ordenar.** Se descartó porque extraer el mínimo obliga a examinar
todos los eventos pendientes, lo que el enunciado prohíbe explícitamente en §4.1
("obtener el siguiente evento no puede requerir examinar todos los eventos
programados"). Con varios cientos de eventos y decenas de miles de extracciones,
el trabajo total crece como el producto de ambas cantidades.

**Lista ordenada.** Extraer el mínimo es inmediato, pero insertar obliga a
desplazar elementos para mantener el orden. En este juego se inserta
aproximadamente una vez por cada extracción —cada actor que actúa programa su
siguiente acción—, así que el costo lineal de la inserción reaparece en cada
paso del bucle y no se amortiza.

### 3. Decisión

Montículo binario mínimo implementado sobre una `list` como almacenamiento
contiguo, en `structures/event_queue.py`.

El criterio de comparación está centralizado en `_less()`: primero `time`
ascendente y, cuando los tiempos son iguales, `sequence` ascendente. Todas las
operaciones del montículo usan ese mismo criterio, de modo que el orden es total
y determinista.

La agenda no ejecuta acciones ni administra el reloj virtual. Su única
responsabilidad es almacenar eventos y devolverlos en el orden correcto.

**Cancelación por marcado (eliminación diferida).** `cancel(evento)` marca el
evento como cancelado en O(1) y no lo retira de inmediato. El montículo descarta
los eventos cancelados cuando llegan a la raíz, en `_discard_cancelled_roots()`.

La razón es que §2.10 y §4.1 exigen poder cancelar efectos y detener los eventos
futuros de un actor muerto *sin recorrer todos los eventos pendientes*. Buscar un
evento concreto dentro de un montículo cuesta O(n), porque el montículo solo
ordena padres respecto a hijos y no permite localizar un elemento por su
contenido. El marcado evita esa búsqueda por completo.

Para que el marcado sea viable hace falta un acuerdo con el modelo: **quien
programa un evento conserva la referencia al objeto `Event`**. Como un actor
tiene a lo sumo una acción pendiente a la vez, basta con que cada actor guarde
la referencia a su evento programado; al morir, cancelarlo cuesta O(1). El mismo
acuerdo aplica a los efectos temporales y a los eventos de cierre de puerta.
Esta dependencia afecta a `model/actor.py` y `model/effects.py`.

### 4. Análisis de complejidad

Sea `n` la cantidad de eventos almacenados.

| Operación | Costo | Nota |
| --- | --- | --- |
| `push` | O(log n) | el nuevo elemento asciende como máximo la altura del árbol |
| `peek` | O(1) amortizado | O(1) si la raíz está activa; cada raíz cancelada que descarta cuesta O(log n), pero cada evento se descarta una sola vez en toda su vida |
| `pop` | O(log n) | |
| `cancel` | O(1) | solo marca el campo, sin tocar el montículo |
| `is_empty` | O(1) amortizado | mismo razonamiento que `peek` |

El espacio es O(n). Con la eliminación diferida, `n` incluye los eventos
cancelados que todavía no han llegado a la raíz, por lo que el montículo puede
ser mayor que la cantidad de eventos activos. El sobrecosto está acotado por la
cantidad de cancelaciones, que en este juego es poco frecuente frente al número
de eventos procesados.

La operación dominante del bucle principal es `pop`, con costo O(log n). Con
varios cientos de eventos simultáneos, la altura del árbol es de alrededor de 9
niveles, de modo que cada selección realiza unas pocas comparaciones en lugar de
examinar los cientos de eventos pendientes.

### 5. Evidencia empírica

**Pendiente.** Aún no se ha implementado el modo `--bench`, por lo que no existen
mediciones propias. El enunciado exige que al menos una sección mida directamente
la alternativa descartada; para esta sección se medirá la lista sin ordenar frente
al montículo, con varios cientos de eventos simultáneos y decenas de miles de
extracciones.

Lo único verificado hasta ahora son las pruebas unitarias de
`tests/test_event_queue.py`, que comprueban corrección, no rendimiento.

### 6. Límites conocidos

* **Memoria con muchas cancelaciones.** Si un escenario cancelara eventos de forma
  masiva y esos eventos quedaran en posiciones profundas del montículo, el montículo
  retendría memoria de eventos que nunca se ejecutarán. Si las mediciones mostraran
  que esto ocurre, habría que considerar una reconstrucción periódica del montículo
  o una estructura que permita eliminar por posición.
* **`__len__` no cuenta eventos activos.** Devuelve los eventos almacenados,
  incluidos los cancelados que aún no se descartaron. `is_empty()`, `peek()` y
  `pop()` sí respetan la semántica de eventos activos. Para guardar la partida
  existe `active_events()`, que recorre el montículo y devuelve los no
  cancelados; cuesta O(n) y solo se llama al guardar, no en el bucle principal.
  Si alguna vez hiciera falta el número de eventos activos dentro del bucle,
  habría que mantener un contador explícito.
* **La reprogramación no es una operación de la agenda.** Un cambio de velocidad
  (§2.3) no modifica el evento que ya está en el montículo, porque alterar su
  `time` rompería la propiedad de orden. El motor debe cancelar el evento anterior
  e insertar uno nuevo con un número de secuencia nuevo.

### 7. Pruebas realizadas

`tests/test_event_queue.py`, 18 pruebas, todas pasan (Python 3.14.6). Las diez
primeras cubren el orden y la cancelación:

| Prueba | Qué comprueba |
| --- | --- |
| `test_order_by_time` | el menor `time` sale primero |
| `test_order_by_sequence` | con tiempos iguales, desempata el menor `sequence` |
| `test_peek_does_not_remove_event` | `peek()` es idempotente y no retira |
| `test_cancel_event` | un evento cancelado nunca se entrega |
| `test_empty_queue` | `peek()` y `pop()` devuelven `None` en una agenda vacía |
| `test_cancel_event_in_the_middle` | cancelar un evento que no está en la raíz no altera el orden de los demás |
| `test_cancel_all_events` | con todo cancelado, la agenda queda vacía |
| `test_push_already_cancelled_event` | insertar un evento ya cancelado no lo hace ejecutable |
| `test_total_order_with_many_events` | 500 eventos con tiempos repetidos salen en orden total estricto por `(time, sequence)` |
| `test_interleaved_push_pop_keeps_order` | intercalar inserciones y extracciones mantiene el orden |

Comando: `python -m unittest discover -s tests -t . -v` desde `cripta/`.

Las ocho restantes cubren `active_events()` y los campos de carga de `Event`:
que la lista excluye los cancelados, que volver a insertar esos eventos en una
agenda nueva reconstruye el mismo orden de extracción, y que cada tipo de evento
transporta sus datos (daño del veneno, sala y dirección del cierre de puerta,
instancia de la trampa).

### 8. Decisiones abiertas de esta sección

* **Orden de activación de enemigos simultáneos.** §2.4 indica que los enemigos
  activados en el mismo instante se programan "en orden ascendente de su id de
  instancia", pero los ids llegan como texto (`"e-201"`). Se propone orden
  lexicográfico sobre el id completo, porque es determinista y no asume que el id
  contenga un número extraíble —§9 prohíbe depender del formato de ids de una
  cripta concreta. Pendiente de confirmar.
* **`event_type` como texto o enumeración.** Se mantiene como texto por ahora,
  porque la bitácora de reproducción (§4.11) es un archivo de texto y el valor se
  escribe tal cual. Si la cantidad de tipos crece lo suficiente para que los
  errores de escritura sean un riesgo real, se pasará a constantes.
* **Quién asigna los números de secuencia.** Resuelto: `GameState.next_sequence()`.
  Ver la sección "Reloj virtual y numeración de eventos" más abajo.

---

## Reloj virtual y numeración de eventos

**Estado:** implementado y probado con pruebas unitarias. No corresponde a un
problema de §4; da soporte a §4.1 y condiciona §4.6.

### 1. Problema

El juego mantiene un reloj virtual entero y necesita un número de secuencia
creciente para desempatar eventos programados en el mismo instante (§2.3). Hay
que decidir quién administra esos dos valores y cómo se comportan cuando el
jugador usa un pergamino de retroceso (§2.11).

### 2. Decisión: una única fuente de números de secuencia

El contador vive en `GameState.next_sequence()`, arranca en 0 y se incrementa en
cada llamada. No lo administra `EventQueue`, porque programar un evento es una
decisión del motor y no de la estructura que lo almacena.

Se descartó mantener un contador por actor: dos actores podrían generar el mismo
número y el desempate de §2.3 quedaría sin resolver, con lo que el orden dejaría
de ser total.

### 3. Decisión: el reloj se restaura al retroceder, el contador no

Esta es la decisión menos evidente de esta sección.

El reloj **sí** se restaura, porque el enunciado lo exige en §2.11 y en §4.6, y
porque su valor tiene significado absoluto: se usa en aritmética al programar
(`reloj + intervalo`, §2.3), se compara contra la antigüedad del rastro
(`reloj - rastro < 400`, §2.9) y se reporta en la tabla de puntajes (§2.12). Un
reloj adelantado haría que los eventos restaurados quedaran en el pasado y que
rastros frescos parecieran caducados.

El contador de secuencia **no** necesita restaurarse. La razón es que `sequence`
solo se usa para comparar un evento contra otro, nunca en aritmética ni como
índice. Los eventos que el retroceso restaura son los que ya estaban pendientes
antes de la acción revertida, de modo que todos tienen un número menor que el
valor del contador en ese momento; los eventos programados durante el intervalo
revertido son precisamente los que el retroceso descarta. Por lo tanto, los
eventos nuevos reciben números mayores que todos los restaurados, tanto si el
contador se restaura como si no. El orden que producen las comparaciones es
idéntico en ambos casos, y la partida observable también. El mismo argumento se
aplica a dos retrocesos consecutivos (Apéndice B).

Se consideró guardar en el historial cuántos números se consumieron durante el
intervalo para restarlos al retroceder. Se descartó porque no resuelve ningún
problema real y es más frágil: si una resta se compone mal con dos retrocesos
seguidos, el contador reutilizaría números ya emitidos y el orden total se
rompería sin producir ninguna excepción.

No restaurar el contador tiene además una ventaja práctica: cada evento de la
partida conserva un número de secuencia único, lo que evita ambigüedades al leer
una bitácora durante la depuración.

**Consecuencia para `structures/history.py` (persona 3):** el historial debe
registrar el valor del reloj de cada acción del jugador, pero no el contador de
secuencia. Sí debe registrar el `time` y el `sequence` propios de cada evento
afectado, para poder devolverlos a la agenda tal como estaban.

### 4. Decisión: el reloj es de solo lectura

`clock` se expone como propiedad sin asignación directa. Solo dos métodos lo
mueven:

| Método | Quién lo usa | Regla |
| --- | --- | --- |
| `advance_clock_to(time)` | el motor, al extraer un evento | acepta avanzar o quedarse en el mismo instante; rechaza retroceder |
| `rewind_clock_to(time)` | únicamente el pergamino de retroceso | acepta retroceder o quedarse; rechaza adelantar |

Quedarse en el mismo instante debe permitirse porque varios eventos comparten
tiempo. El retroceso es la única operación del juego que mueve el reloj hacia
atrás (§2.11), y separarla en su propio método hace explícito quién la invoca.

La alternativa era dejar `clock` como atributo público. Se descartó porque
cualquier módulo podría moverlo hacia atrás por error y el juego seguiría
ejecutándose con un reloj incoherente sin producir ningún aviso. Con las guardas,
un error de reprogramación aparece como `ValueError` con contexto en lugar de
como una partida silenciosamente incorrecta.

`rewind_clock_to()` no calcula el instante de destino: lo recibe del historial,
que anotó el valor del reloj en el momento de la acción revertida. Calcularlo
restando el tiempo transcurrido requeriría la misma información y podría
desincronizarse.

### 5. Qué mueve el reloj y qué no

| Situación | Efecto sobre el reloj | Referencia |
| --- | --- | --- |
| Procesar un evento | salta al `time` de ese evento | §2.3 |
| Esperar una respuesta HTTP, incluido un 429 | ninguno | §2.4, §3.1 |
| Usar un pergamino de retroceso | lo devuelve al instante registrado; no consume tiempo | §2.11 |
| Acción inválida: inventario lleno, llave incorrecta | ninguno | Apéndice B |
| Veneno, regeneración, cierre de puerta, rearme de trampa | ninguno; solo programan eventos en `reloj + intervalo` | §2.10 |
| Cambio de velocidad | ninguno; recalcula el tiempo de un evento programado | §2.3 |
| Trampa al entrar a una sala | ninguno; se aplica en el instante actual | §2.10 |

### 5b. Cargar una partida no es lo mismo que retroceder

El apartado 3 concluye que el contador de secuencia no necesita restaurarse al
usar un pergamino de retroceso. Eso **no** se extiende al guardado de §4.10.

El retroceso deja la partida en marcha: los eventos restaurados conviven con los
nuevos y, como solo se comparan entre sí, basta con que los nuevos sigan siendo
mayores. Cargar una partida es distinto, porque el programa arranca de cero y
debe continuar exactamente donde se quedó. Por eso el archivo de guardado sí debe
conservar y restaurar el reloj, el contador de secuencia, el estado interno del
generador aleatorio y los eventos activos de la agenda.

`GameState.restore(clock, sequence_counter, random_state)` cubre los tres
primeros y `EventQueue.active_events()` entrega los eventos a persistir. Está
cubierto por `test_restore_in_the_middle_of_a_game_keeps_the_rolls_aligned`, que
comprueba que los valores aleatorios posteriores a una carga coinciden con los
que habría producido la partida sin guardar.

### 5c. Los eventos apuntan al actor, no a su identificador

`Event` guardaba `actor_id` y `target_id` como texto. Se cambió a referencias
directas al objeto `Actor`.

El motor necesita el actor cada vez que procesa un evento. Con solo el
identificador habría que buscarlo, lo que cuesta O(n) por evento recorriendo la
lista de actores; con decenas de miles de eventos eso compite contra el
presupuesto de 20 ms de §5.2. La alternativa habitual sería un índice, pero §7
prohíbe `dict` como tabla de búsqueda. La referencia directa elimina el problema
en lugar de resolverlo: el acceso es O(1) y no hace falta ninguna estructura
adicional.

El identificador sigue disponible como `event.actor.actor_id`, que es lo que se
escribe al serializar. Al cargar hay que resolver cada identificador contra la
lista de actores, pero eso ocurre una sola vez y fuera del bucle principal.

La clase se mantuvo plana, con campos opcionales por tipo de evento, en lugar de
usar subclases o un objeto de datos anidado. El motivo es el guardado binario de
§4.10: `struct` empaqueta registros de forma fija, y una clase plana se empaqueta
directamente, mientras que una jerarquía obligaría a un formato con etiqueta de
tipo.

### 6. Azar reproducible

`GameState` contiene la instancia `random.Random(semilla)` que usa todo el
modelo, y conserva la semilla porque hace falta en el archivo de guardado y en
la cabecera de la bitácora de reproducción (§2.6, §4.11). No se usa el generador
global del módulo `random`, que el enunciado prohíbe.

**Decisión abierta:** §2.11 dice que la reversión incluye "cualquier otro dato
modificado", y el estado interno del generador aleatorio se modifica durante el
intervalo revertido. No se restaura, porque `random.Random.getstate()` devuelve
cientos de enteros y guardarlos por intervalo se aproximaría a una copia de
estado, que §2.11 prohíbe. El requisito de §2.6 se mantiene igual: misma
semilla y misma secuencia de acciones del jugador producen la misma partida,
porque el uso del pergamino forma parte de esa secuencia de acciones. Conviene
confirmarlo con el profesor.

### 7. Complejidad

Todas las operaciones son O(1) en tiempo y el estado temporal ocupa espacio
constante.

### 8. Evidencia empírica

**Pendiente.** Estas operaciones son O(1) y no se espera que aparezcan en el
perfil de rendimiento, pero el presupuesto de §5.2 se medirá sobre el ciclo
completo de eventos cuando exista `--bench`.

### 9. Pruebas realizadas

`tests/test_game_state.py`, 20 pruebas, todas pasan (Python 3.14.6). Cubren:
reloj inicial en 0 y con valor cargado, reloj de solo lectura, numeración
creciente desde 0, avance hacia adelante y al mismo instante, rechazo de
retroceso en `advance_clock_to()`, retroceso correcto y rechazo de adelanto en
`rewind_clock_to()`, avance posterior a un retroceso, continuidad del contador
tras un retroceso, reproducibilidad del azar con la misma semilla, divergencia
con semillas distintas y disponibilidad de la semilla.

Total del proyecto: 87 pruebas, todas pasan.
Comando: `python -m unittest discover -s tests -t . -v` desde `cripta/`.

---

## El bucle del motor

**Estado:** implementado y probado para esperar y atacar. Moverse, abrir puertas
y las acciones de inventario esperan a que existan las salas y el inventario.

### 1. Decisión: una acción del jugador equivale a un ciclo completo de eventos

Cada método de acción de `Game` ejecuta la acción y después procesa todos los
eventos pendientes hasta que vuelva a tocarle decidir al jugador. El controlador
no administra el reloj ni la agenda.

La alternativa era exponer el bucle al controlador, con un método que avanzara un
evento por llamada. Se descartó porque obligaría a la vista a conocer el
funcionamiento del reloj, y porque §5.2 define el presupuesto de rendimiento
precisamente sobre "un ciclo completo de eventos entre dos decisiones consecutivas
del jugador". Con esta forma, ese ciclo es exactamente una llamada y se puede
medir sin instrumentar nada.

### 2. Decisión: el actor olvida su evento en cuanto se ejecuta

Cada actor guarda en `scheduled_event` la referencia a su acción pendiente. Al
sacar un evento de la agenda y ejecutarlo, el motor pone esa referencia en `None`
antes de programar la siguiente.

Sin eso, un actor seguiría apuntando a un evento ya consumido. Si en ese momento
un efecto le cambiara la velocidad, `change_speed()` creería que tiene una acción
pendiente, cancelaría un evento que ya no está en la agenda y programaría una
acción nueva. Al terminar su turno se programaría otra, de modo que el actor
quedaría con dos acciones pendientes y actuaría el doble de veces, sin que nada
produjera un error. Está cubierto por
`test_the_player_has_no_pending_event_during_their_turn`.

### 3. Decisión: los eventos de un actor muerto se filtran por dos caminos

Al morir un actor, el motor cancela su evento pendiente. Además, el bucle descarta
cualquier evento cuyo actor ya no esté vivo antes de ejecutarlo.

Parece redundante y no lo es: la cancelación cubre el caso normal, pero un actor
puede morir por una vía que no pase por el motor, como un pulso de veneno que lo
deja en cero. El filtro del bucle garantiza la regla de §2.6 —un actor muerto deja
de ejecutar eventos futuros— sin depender de que todas las causas de muerte
recuerden cancelar.

Un evento descartado no adelanta el reloj, porque no ocurrió nada.

### 4. Decisión: `GameState` guarda el tiempo, `Game` guarda la partida

`GameState` mantiene el reloj, el contador de secuencia y el generador aleatorio,
que es exactamente lo que hay que guardar y restaurar para reanudar una partida.
`Game` mantiene los actores, la agenda y el resultado.

El corte está puesto ahí porque `GameState.restore()` ya es la interfaz que usa el
guardado de §4.10, y mezclar los actores dentro habría obligado a cambiarla otra
vez.

### 5. Decisión: el ataque efectivo se resuelve por polimorfismo

`Actor` expone `effective_attack` y `effective_defense` devolviendo el valor base,
y `Player` los sobrescribe sumando los bonos del arma y la armadura equipadas
(§2.7). Así la fórmula de daño es la misma para todos y el motor no pregunta de
qué tipo es cada actor.

El equipo se trata por duck typing: cualquier objeto con `attack_bonus` o
`defense_bonus` sirve. Eso permite probar el combate con equipo sin depender del
catálogo.

### 6. Orden de activación de enemigos simultáneos

§2.4 exige activarlos en orden ascendente de identificador de instancia. Como los
identificadores son texto, se comparan como texto completo, según lo ya razonado
en la sección 4.1. El orden se arma con una inserción simple, porque §4.9 prohíbe
`sorted()` y `list.sort()` y el módulo de ordenamiento del proyecto todavía no
existe. Debe reemplazarse por ese módulo cuando esté disponible.

### 7. Límites conocidos

* **La bitácora de mensajes es una `list` que crece.** §4.8 exige memoria constante
  y que agregar un mensaje no desplace los 19 anteriores. Esa estructura
  corresponde a `structures/circular_log.py` y todavía no existe, así que la lista
  es provisional y debe sustituirse.
* **El errante y el rastreador esperan.** Sin salas no pueden examinar salidas ni
  rastros. Esperar es lo que §2.8 indica cuando no hay ninguna opción disponible,
  de modo que el comportamiento actual no es incorrecto, pero está incompleto.
* **Los valores de `behavior`.** El enunciado solo confirma `"rastreador"` en su
  ejemplo de catálogo. Los nombres del guardián y del errante deben verificarse
  contra el servicio real.
* **Los objetos que suelta un enemigo al morir** (§2.6) no se colocan en ningún
  lado, porque no existe el suelo de la sala.

### 8. Complejidad

| Operación | Costo |
| --- | --- |
| Procesar un evento | O(log n) por la extracción de la agenda |
| Buscar el enemigo objetivo de un ataque | O(e) sobre los enemigos, una vez por acción del jugador y no por evento |
| Programar la acción de un actor | O(log n) |
| Cancelar la acción de un actor | O(1) |

### 9. Evidencia empírica

**Pendiente.** El presupuesto de 20 ms de §5.2 se medirá sobre este bucle cuando
exista `--bench`.

### 10. Pruebas realizadas

`tests/test_game.py`, 26 pruebas, todas pasan (Python 3.14.6), en siete grupos:
bucle, combate, acciones rechazadas, determinismo, activación de enemigos, cambio
de velocidad y estado visible.

Los tiempos se verifican contra el ejemplo de §2.13: un enemigo de velocidad 150
activado en 0 queda programado para 66 y actúa una vez antes de la siguiente
decisión del jugador; uno de velocidad 250 actúa dos veces. También se comprueba
que una acción rechazada no mueve el reloj ni consulta el generador aleatorio, y
que dos partidas con la misma semilla y las mismas acciones producen los mismos
mensajes.

Total del proyecto: 87 pruebas, todas pasan.

---

## Actores, intervalos y cambios de velocidad

**Estado:** implementado y probado con pruebas unitarias. No corresponde a un
problema de §4; implementa las reglas de §2.2 y §2.3.

### 1. Decisión: el `max(1, ...)` del intervalo es un requisito de terminación

El intervalo de una acción es `max(1, costo * 100 // velocidad)` (§2.3). La
división entera puede dar 0 cuando la velocidad es mucho mayor que el costo: con
velocidad 10000 y una acción de costo 25, `2500 // 10000` es 0.

Sin el `max(1, ...)`, ese actor quedaría programado para el mismo instante en que
está actuando y volvería a actuar en ese instante indefinidamente, de modo que el
reloj virtual no avanzaría nunca y el bucle principal no terminaría. El
`max(1, ...)` garantiza que toda acción adelante el reloj al menos una unidad.

Está cubierto por `test_interval_is_never_zero`.

### 2. Decisión: el límite de vida vive en el setter

`health` se expone como propiedad y su setter recorta el valor al rango
`[0, max_health]`.

El enunciado pide ese límite en dos lugares distintos del Apéndice B: la
regeneración de un enemigo y la poción de curación. La alternativa era escribir
el recorte en cada operación que modifica la vida, lo que repetiría la regla y
dejaría abierta la posibilidad de olvidarla en una tercera operación futura, como
un efecto nuevo. Con el recorte en el setter, la regla se cumple una sola vez y
es imposible saltarla.

La diferencia con el estilo de validación habitual es que aquí no se lanza
`ValueError`: recortar es la regla del juego, no un error del programa. Donde sí
se valida con `ValueError` es en `speed`, porque una velocidad de 0 haría fallar
la división del intervalo, y en `max_health` y `actor_id`.

### 3. Decisión: el actor calcula el reescalado, el motor reprograma

`change_speed(current_time, new_speed)` aplica la fórmula de §2.3
(`restante_nuevo = max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)`),
devuelve el instante reprogramado y recién entonces reemplaza la velocidad.

Se resolvió en un único método porque la fórmula necesita las dos velocidades a
la vez. Si el cambio de velocidad y el cálculo fueran dos pasos separados, bastaría
invertir el orden para que el resultado quedara mal sin producir ningún error
visible. `test_rescale_uses_the_previous_speed_not_the_new_one` detecta
precisamente esa inversión.

El método **no modifica** el evento pendiente ni toca la agenda. Devuelve el
instante y el motor cancela el evento anterior e inserta uno nuevo con un número
de secuencia nuevo, como exige §2.3 y como requiere la agenda para no romper su
propiedad de orden.

### 4. Decisión: los costos de las acciones no viven en el actor

`Actor` solo convierte un costo en un intervalo según su velocidad. La tabla de
costos de §2.3 es una propiedad de cada acción, no del actor, así que vive en el
motor.

### 5. Referencia al evento pendiente

Cada actor guarda en `scheduled_event` la referencia a su evento programado. Como
un actor tiene a lo sumo una acción pendiente a la vez, eso permite cancelarlo en
O(1) cuando muere, sin recorrer la agenda, que es lo que exige §4.1.

### 6. Complejidad

Todas las operaciones son O(1) en tiempo y espacio.

### 7. Pruebas realizadas

`tests/test_actor.py`, 23 pruebas, todas pasan (Python 3.14.6), agrupadas en
cuatro casos: intervalos, vida, validación y cambio de velocidad.

Los intervalos se verifican contra los números del propio enunciado: velocidad
150 con costo 100 da 66 (§2.4 y §2.13), y la secuencia del jugador de §2.13
—moverse en 0, recoger en 100, equipar en 125— produce 100, 125 y 175.

Total del proyecto: 87 pruebas, todas pasan.
