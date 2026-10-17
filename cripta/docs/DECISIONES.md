# Documento de Decisiones de Diseño — CRIPTA

Acá vamos anotando por qué el programa está hecho como está. Cada sección cuenta un
problema concreto que tuvimos que resolver, qué opciones barajamos y con cuál nos
quedamos.

Las secciones que corresponden a un problema del §4 del enunciado llevan los seis
apartados que ese enunciado pide. Las otras documentan decisiones que no son un
problema del §4 pero que condicionan al resto del grupo, así que conviene tenerlas
escritas.

Cuando algo todavía no está medido lo decimos. No hay números inventados en este
documento.

---

## 4.1 Qué ocurre a continuación (agenda de eventos)

Estado: implementado, probado y medido.

### Problema

El juego no avanza por rondas. Lleva un reloj entero y una lista de cosas que van a
pasar, y en cada vuelta del bucle principal hay que sacar la que ocurre antes. Si
dos ocurren en el mismo instante, gana la que se programó primero.

Eso suena simple hasta que uno mira con qué frecuencia pasa.

Las cifras que siguen están **medidas**, no estimadas. Salen de correr partidas
completas con una agenda instrumentada, con `benchmark/scheduler_bench.py`. El detalle
de cada escenario está en el apartado de evidencia.

| Operación | Cuándo ocurre | Medido por partida |
| --- | --- | ---: |
| Sacar el evento más próximo | una vez por evento procesado | 11 081 con 5 enemigos, 189 310 con 500 |
| Meter un evento | cuando un actor actúa y programa su siguiente acción, o cuando arranca un efecto | 1.00 por cada extracción |
| Cancelar un evento | muere un actor, un antídoto corta el veneno, cambia una velocidad | 750 contra 189 310 eventos, una cada 252 |

Dos cosas saltan de esa tabla.

La primera fila es la que manda: en una partida con 500 enemigos se sacan casi 190 000
eventos. Lo que cueste sacar el mínimo es, en la práctica, lo que cuesta el juego
entero.

Y la segunda fila es la que condiciona la elección, porque **se inserta exactamente tan
seguido como se extrae**. La proporción medida es 1.00 en los tres escenarios, y tiene
sentido: cada actor que actúa programa de inmediato su siguiente acción. Eso descarta
cualquier estructura que abarate una de las dos operaciones encareciendo la otra.

Hay una exigencia extra que no se puede perder de vista: sacar el siguiente evento
no puede obligar a revisar todos los que están esperando. El enunciado lo dice con
todas las letras en §4.1.

### Alternativas consideradas

Miramos tres formas de guardar los eventos.

| Estructura | Insertar | Ver el mínimo | Sacar el mínimo |
| --- | --- | --- | --- |
| Lista sin ordenar | O(1) | O(n) | O(n) |
| Lista ordenada al insertar | O(n) | O(1) | O(1) |
| Montículo binario mínimo | O(log n) | O(1) | O(log n) |

La **lista sin ordenar** es la más fácil de escribir: se mete al final y listo. El
problema es sacar, porque hay que recorrer todo para encontrar el más chico. Eso
choca de frente con la restricción de §4.1 que acabamos de mencionar. Y como sacar
ocurre decenas de miles de veces sobre cientos de eventos, el trabajo total termina
siendo el producto de esas dos cantidades.

La **lista ordenada** arregla la extracción: el mínimo siempre está al frente. Pero
mueve el costo a la inserción, porque hay que buscarle el lugar y correr lo que
estaba después. En este juego eso no sirve de nada, porque insertamos casi tan
seguido como sacamos. Cada actor que actúa programa de inmediato su siguiente
acción. Así que el costo lineal vuelve a aparecer en cada vuelta del bucle, solo
que del otro lado.

### Decisión

Montículo binario mínimo, guardado adentro de una `list` de Python, en
`structures/event_queue.py`.

La comparación entre dos eventos está en un solo lugar, el método `_less()`: primero
compara `time`, y si empatan compara `sequence`. Todas las operaciones del montículo
usan ese mismo método, así que el orden es total y siempre el mismo. Eso último
importa más de lo que parece, porque el enunciado exige que dos partidas con la
misma semilla y las mismas acciones den el mismo resultado.

La agenda no ejecuta nada ni sabe qué hora es. Solo guarda eventos y los devuelve en
orden. Quien decide qué significa cada evento es el motor.

**Lo de cancelar.** Acá tomamos la decisión menos obvia de esta sección. Cuando hay
que cancelar un evento, no lo sacamos del montículo: le ponemos una marca y lo
dejamos donde está. Cuando ese evento llega a la raíz, el montículo lo tira sin
entregarlo.

¿Por qué no borrarlo de una vez? Porque encontrarlo cuesta O(n). Un montículo
garantiza que cada padre es menor que sus hijos, pero no te dice dónde está un
elemento concreto, así que para ubicarlo habría que revisar todo. Y el enunciado
pide justamente lo contrario: §2.10 exige poder cancelar un efecto, y §4.1 exige que
los eventos de un actor muerto no se ejecuten, en ambos casos sin recorrer los
eventos pendientes. Marcar y seguir resuelve las dos cosas en O(1).

Esto obliga a un acuerdo con el resto del modelo: quien programa un evento se queda
con la referencia al objeto. Como cada actor tiene a lo sumo una acción esperando,
alcanza con que cada actor guarde la suya. Al morir, cancelarla es inmediato. Lo
mismo vale para los efectos temporales y para los eventos de puerta. Afecta a
`model/actor.py` y a `model/effects.py`.

### Análisis de complejidad

Con `n` eventos guardados:

| Operación | Costo | Por qué |
| --- | --- | --- |
| `push` | O(log n) | el elemento nuevo sube como mucho la altura del árbol |
| `pop` | O(log n) | la raíz nueva baja como mucho esa misma altura |
| `peek` | O(1) amortizado | inmediato si la raíz sirve; cada raíz cancelada que descarta cuesta O(log n), pero un evento se descarta una sola vez en toda su vida |
| `cancel` | O(1) | pone una marca, no toca el montículo |
| `is_empty` | O(1) amortizado | igual que `peek` |

El espacio es O(n), con una salvedad: como los cancelados se quedan adentro hasta
llegar a la raíz, ese `n` puede ser mayor que la cantidad de eventos que de verdad
van a ejecutarse. El exceso está acotado por la cantidad de cancelaciones, que en
este juego son pocas comparadas con los eventos que se procesan.

La operación que domina el bucle es `pop`. Con varios cientos de eventos, el árbol
tiene unos nueve niveles de alto, así que cada extracción hace cerca de nueve
comparaciones en lugar de revisar los cientos de eventos que hay esperando.

### Evidencia empírica

Medimos con `benchmark/scheduler_bench.py`, en Python 3.14.6 sobre Windows 11. La
lista sin ordenar está implementada en ese mismo archivo, como `UnsortedEventList`,
solo para poder medirla. El motor no la usa.

La prueba imita lo que hace el juego de verdad: se llena la agenda con una cantidad
fija de eventos y después se repite muchas veces el patrón de sacar el más próximo y
meter el siguiente, de modo que el tamaño se mantiene parejo.

Con 20 000 ciclos de sacar e insertar, variando cuántos eventos hay esperando:

| Eventos esperando | Montículo | Lista sin ordenar | La lista tarda |
| ---: | ---: | ---: | ---: |
| 50 | 0.0560 s | 0.0661 s | 1.2 veces más |
| 100 | 0.0641 s | 0.1215 s | 1.9 veces más |
| 300 | 0.0781 s | 0.3438 s | 4.4 veces más |
| 1 000 | 0.0912 s | 1.1588 s | 12.7 veces más |
| 3 000 | 0.1032 s | 3.4197 s | 33.1 veces más |

Ninguna fila por separado dice gran cosa. Lo que importa es cómo cambia cada columna
al bajar por la tabla. Multiplicamos por 60 los eventos que esperan: el montículo
pasó de 0.0560 a 0.1032 segundos, ni siquiera el doble, que es el crecimiento
logarítmico que predice la teoría. La lista pasó de 0.0661 a 3.4197, unas 52 veces
más, que es el crecimiento lineal.

Y acá viene algo que conviene decir sin adornos: **con 50 eventos esperando, la
lista sin ordenar alcanzaba de sobra**. La diferencia era de una décima de segundo
en 20 000 ciclos. A esa escala la decisión no se justifica.

Se justifica a la escala que plantea el enunciado. §4.1 dice que en las pruebas
puede haber varios cientos de eventos simultáneos, y ahí la brecha ya es de 4.4
veces. Y §9 advierte que la cripta de la revisión puede tener más salas, más actores
y más efectos que las que usamos nosotros. En esa dirección la lista se degrada sin
techo mientras el montículo casi no se mueve.

En el escenario puntual que describe §4.1, con 300 eventos y 50 000 extracciones:
montículo 0.1290 s contra 0.8524 s de la lista, 6.6 veces.

### Frecuencia medida de las operaciones

§8 pide indicar con qué frecuencia medida se ejecuta cada operación, así que corrimos
partidas completas con una agenda instrumentada, `CountingEventQueue`, que es una
subclase de `EventQueue` y vive en el archivo de mediciones. Se hizo así, y no
poniéndole contadores a `EventQueue`, para no sumar trabajo en el camino que el juego
recorre decenas de miles de veces, que es justamente el que se está midiendo. `Game`
recibe la agenda desde fuera, de modo que la partida medida es idéntica a una normal
salvo por los contadores.

Se midieron cinco escenarios. Los dos primeros son estáticos, con el jugador esperando
en una sala; los dos del medio recorren una cripta de verdad, con movimiento, trampas y
puertas; el último es una partida de combate donde el jugador mata 500 enemigos.

| | Estático, 5 | Estático, 50 | Recorrido, 6 salas | Recorrido, 40 salas | Combate, 500 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Decisiones del jugador | 1 000 | 1 000 | 1 000 | 1 000 | 500 |
| Eventos procesados | 11 081 | 101 756 | 11 235 | 90 504 | 189 310 |
| Eventos por decisión | 11.1 | 101.8 | 11.2 | 90.5 | 378.6 |
| Inserciones | 11 092 | 101 857 | 11 247 | 90 607 | 190 010 |
| Extracciones | 11 081 | 101 756 | 11 235 | 90 504 | 189 310 |
| Inserciones por extracción | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Cancelaciones | 0 | 0 | 0 | 0 | 750 |
| Tamaño máximo de la agenda | 17 | 107 | 19 | 109 | 506 |

Cuatro conclusiones.

La cantidad de eventos por decisión del jugador crece en proporción directa con los
enemigos activos, porque cada uno programa una acción cada vez que actúa. Con 50
enemigos ya son 102 eventos entre dos decisiones, de modo que la estimación de "varios
cientos de eventos simultáneos" de §4.1 corresponde a una cripta con unas pocas decenas
de enemigos activos a la vez, que no es nada raro.

La proporción de 1.00 inserciones por extracción se mantiene en los cinco escenarios.
Esa es la medición que respalda el descarte de la lista ordenada: no sirve abaratar la
extracción si se paga en la inserción, porque ocurren la misma cantidad de veces.

Lo que manda es la cantidad de enemigos activos, no el tamaño de la cripta. Las
columnas tercera y cuarta recorren 6 y 40 salas, pero sus cifras son casi idénticas a
las de los escenarios estáticos con la misma cantidad de enemigos. Moverse, abrir
puertas y disparar trampas agrega eventos, pero son unos pocos por decisión; lo que
llena la agenda son los actores que programan su siguiente acción.

Las cancelaciones son raras. En los cuatro primeros escenarios no hay ninguna, porque
nadie muere. En el de combate, donde el jugador mata 500 enemigos y además corta 50
venenos con antídoto, hay 750 cancelaciones contra 189 310 eventos procesados: una cada
252. Eso respalda lo que se dice más abajo sobre el costo en memoria de la eliminación
diferida.

Cada configuración se corrió una sola vez. Los números sirven para comparar órdenes
de magnitud, no para discutir diferencias de centésimas.

### Límites conocidos

Si alguna vez se cancelaran muchísimos eventos y esos eventos quedaran enterrados en
el fondo del montículo, estaríamos ocupando memoria con cosas que nunca se van a
ejecutar. Hoy no pasa: en la partida con combate medimos 750 cancelaciones contra
189 310 eventos procesados, y de esas 700 se descartaron al llegar a la raíz, de modo
que en todo momento había a lo sumo unas pocas decenas de eventos muertos adentro. Si
el escenario cambiara, habría que reconstruir el montículo cada tanto o usar una
estructura que permita borrar por posición.

Ojo con `len()`: devuelve cuántos eventos hay guardados, incluidos los cancelados que
todavía no salieron. Los que sí respetan la idea de "eventos vivos" son `is_empty()`,
`peek()` y `pop()`. Para guardar la partida agregamos `active_events()`, que recorre
el montículo y devuelve los que no están cancelados; cuesta O(n), pero solo se llama
al guardar y nunca dentro del bucle. Si algún día hiciera falta ese número adentro
del bucle, habría que llevar un contador aparte.

Una cosa que la agenda no hace, y es a propósito: reprogramar. Cuando cambia la
velocidad de un actor (§2.3) no se le toca el `time` al evento que ya está adentro,
porque eso rompería el orden del montículo sin avisar. El motor tiene que cancelar
el viejo y meter uno nuevo con secuencia nueva.

### Pruebas

`tests/test_event_queue.py`, 18 pruebas, todas pasan en Python 3.14.6. Se corren con
`python -m unittest discover -s tests -t . -v` parado en `cripta/`.

Diez cubren el orden y la cancelación:

| Prueba | Qué comprueba |
| --- | --- |
| `test_order_by_time` | sale primero el de menor `time` |
| `test_order_by_sequence` | con tiempos iguales, gana el menor `sequence` |
| `test_peek_does_not_remove_event` | mirar no saca, y mirar dos veces da lo mismo |
| `test_cancel_event` | un evento cancelado no se entrega nunca |
| `test_empty_queue` | la agenda vacía devuelve `None` en vez de reventar |
| `test_cancel_event_in_the_middle` | cancelar uno que no está en la raíz no desordena a los demás |
| `test_cancel_all_events` | con todo cancelado, la agenda queda vacía |
| `test_push_already_cancelled_event` | meter uno ya cancelado no lo resucita |
| `test_total_order_with_many_events` | 500 eventos con tiempos repetidos salen en orden estricto |
| `test_interleaved_push_pop_keeps_order` | mezclar inserciones y extracciones no rompe el orden |

Las otras ocho son de `active_events()` y de los campos que lleva cada evento:
que la lista deja afuera los cancelados, que volver a meter esos eventos en una
agenda nueva reconstruye el mismo orden de salida, y que cada tipo de evento carga
sus datos (el daño del veneno, la sala y la dirección de una puerta que se cierra, la
instancia de una trampa).

### Lo que queda abierto en esta sección

El enunciado dice en §2.4 que los enemigos que se activan en el mismo instante se
programan "en orden ascendente de su id de instancia". El detalle es que los ids
llegan como texto, del estilo `"e-201"`. Comparando como texto, `"e-10"` va antes que
`"e-9"`; comparando el número de atrás, al revés. Nosotros comparamos el texto
completo, porque no asume que el id tenga un número adentro, y §9 prohíbe depender
del formato de ids de una cripta en particular. Falta confirmarlo con el profesor,
aunque el riesgo es bajo: lo que el enunciado exige es que nuestro programa sea
reproducible consigo mismo, no que coincida con el de otro grupo.

`event_type` sigue siendo texto y no una enumeración. La bitácora de reproducción
(§4.11) es un archivo de texto y el valor se escribe tal cual, así que por ahora no
gana nada con ser otra cosa. Si llegamos a tener tantos tipos que equivocarse al
escribir uno sea un riesgo real, lo pasamos a constantes.

---

## El reloj virtual y la numeración de eventos

Estado: implementado y probado. No es un problema del §4, pero da soporte a 4.1 y
condiciona 4.6, así que va documentado.

El juego lleva un reloj entero y un número de secuencia que crece, que sirve para
desempatar eventos programados en el mismo instante. Había que decidir quién maneja
esos dos valores y, sobre todo, qué pasa con ellos cuando el jugador usa un pergamino
de retroceso.

### Un solo contador para toda la partida

El contador vive en `GameState.next_sequence()`. Arranca en cero y sube de a uno.

No lo pusimos en `EventQueue` porque programar un evento es una decisión del motor,
no de la estructura que lo guarda. Y descartamos tener un contador por actor, que a
primera vista parece más ordenado: si cada actor lleva el suyo, dos actores distintos
pueden generar el mismo número, y entonces el desempate de §2.3 no desempata nada. El
orden dejaría de ser total.

### El reloj sí se restaura al retroceder; el contador no

Esta nos costó entenderla, así que la escribimos con detalle.

El reloj se restaura, y no es opcional: §2.11 y §4.6 lo piden explícitamente. Pero
además hay una razón de fondo, que es que el valor del reloj significa algo por sí
solo. Se usa en cuentas cuando se programa algo (`reloj + intervalo`), se compara
contra la antigüedad del rastro para saber si todavía sirve (`reloj - rastro < 400`),
y se reporta en la tabla de puntajes al terminar. Si el reloj quedara adelantado
después de un retroceso, los eventos restaurados quedarían en el pasado y rastros
frescos parecerían vencidos.

Con el contador de secuencia pasa algo distinto, y es la parte interesante. Ese
número no se usa nunca en una cuenta ni como posición: lo único que se hace con él es
compararlo contra el de otro evento.

Pensemos en el ejemplo del enunciado. En `t=100` el jugador ataca con el contador en
50. Durante el intervalo se programan siete cosas, así que el contador llega a 57. En
`t=200` el jugador usa el pergamino.

Los eventos que el retroceso restaura son los que ya estaban esperando antes del
ataque, o sea que todos tienen número menor que 50. Los que se programaron durante el
intervalo son exactamente los que el retroceso descarta. Entonces, si el contador
vuelve a 50, los eventos nuevos reciben 50, 51, 52; y si se queda en 57, reciben 57,
58, 59. En los dos casos los nuevos son mayores que todos los restaurados, y entre
ellos conservan el mismo orden relativo. Las comparaciones dan idéntico resultado, así
que la partida es la misma. Con dos pergaminos seguidos el argumento se repite igual.

Llegamos a considerar guardar en el historial cuántos números se consumieron en el
intervalo, para restarlos al retroceder. Lo descartamos por dos motivos. No resuelve
ningún problema, según lo que acabamos de ver. Y es frágil: si con dos retrocesos
seguidos una resta se compone mal, el contador vuelve a emitir números ya usados y el
orden total se rompe sin que salte ninguna excepción.

Hay además una ventaja práctica en dejarlo subir siempre: cada evento de la partida
tiene un número único, así que al leer una bitácora depurando nunca aparecen dos
eventos distintos con el mismo número.

Esto le afecta a quien implemente `structures/history.py`: el historial tiene que
guardar el valor del reloj de cada acción del jugador, pero no el contador. Lo que sí
debe guardar es el `time` y el `sequence` de cada evento que toque, para poder
devolverlos a la agenda tal como estaban.

### Guardar una partida no es lo mismo que retroceder

Conviene aclararlo porque se presta a confusión, y de hecho ya se prestó dentro del
grupo.

Lo de arriba vale para el pergamino de retroceso. No vale para el guardado de §4.10.

Cuando uno retrocede, la partida sigue corriendo: los eventos restaurados conviven
con los nuevos y, como solo se comparan entre ellos, alcanza con que los nuevos sigan
siendo mayores. Cuando uno carga una partida guardada el programa arranca de cero y
tiene que seguir exactamente donde se quedó. Ahí sí hay que guardar y restaurar el
reloj, el contador, el estado interno del generador aleatorio y los eventos que
estaban esperando en la agenda.

Para eso están `GameState.restore(clock, sequence_counter, random_state)` y
`EventQueue.active_events()`. La prueba
`test_restore_in_the_middle_of_a_game_keeps_the_rolls_aligned` comprueba que los
valores aleatorios que salen después de cargar son los mismos que habrían salido si
no se hubiera guardado nunca.

### El reloj no se puede escribir desde afuera

`clock` es una propiedad de solo lectura. Hay exactamente dos métodos que lo mueven.

`advance_clock_to(time)` lo usa el motor cuando saca un evento. Acepta avanzar o
quedarse en el mismo instante, porque varios eventos pueden compartir tiempo, y
rechaza retroceder.

`rewind_clock_to(time)` lo usa únicamente el pergamino. Acepta ir para atrás y rechaza
adelantar.

Podríamos haber dejado `clock` como un atributo cualquiera, pero entonces cualquier
módulo podría moverlo hacia atrás por error y el juego seguiría andando con un reloj
incoherente, sin una sola señal de que algo anda mal. Con las guardas, un error de
reprogramación aparece como un `ValueError` que dice qué pasó, en vez de como una
partida silenciosamente equivocada.

Un detalle que vale aclarar: `rewind_clock_to()` no calcula a dónde volver. Lo recibe
del historial, que anotó el valor del reloj en el momento de la acción que se está
revirtiendo. Calcularlo restando el tiempo transcurrido necesitaría exactamente la
misma información y encima podría desincronizarse.

### Qué mueve el reloj y qué no

Esta tabla la armamos porque es fácil equivocarse.

| Situación | Qué le pasa al reloj | Dónde lo dice |
| --- | --- | --- |
| Se procesa un evento | salta al `time` de ese evento | §2.3 |
| Se espera una respuesta HTTP, incluido un 429 | nada | §2.4, §3.1 |
| Se usa un pergamino de retroceso | vuelve al instante guardado, sin consumir tiempo | §2.11 |
| Una acción inválida: inventario lleno, llave equivocada | nada | Apéndice B |
| Veneno, regeneración, cierre de puerta, rearme de trampa | nada; solo programan eventos más adelante | §2.10 |
| Cambio de velocidad | nada; recalcula cuándo ocurre un evento ya programado | §2.3 |
| Trampa al entrar a una sala | nada; se aplica en el instante actual | §2.10 |

Solo la primera fila mueve el reloj. Todo lo demás, a lo sumo, programa eventos.

### Los eventos apuntan al actor, no a su identificador

Al principio `Event` guardaba `actor_id` y `target_id` como texto. Lo cambiamos a
referencias directas al objeto `Actor`.

El motivo salió al escribir el bucle. El motor necesita el actor cada vez que procesa
un evento, y con solo el identificador habría que salir a buscarlo recorriendo la
lista de actores, O(n) por evento. Con decenas de miles de eventos eso se come el
presupuesto de 20 ms de §5.2. Lo normal sería armar un índice, pero §7 prohíbe usar
`dict` como tabla de búsqueda. Guardar la referencia no resuelve el problema: lo
elimina. El acceso es inmediato y no hace falta ninguna estructura extra.

El identificador no se pierde, queda disponible como `event.actor.actor_id`, que es
lo que se escribe al serializar. Al cargar una partida hay que resolver cada
identificador contra la lista de actores, pero eso ocurre una sola vez y lejos del
bucle principal.

La clase quedó plana, con campos opcionales según el tipo de evento, en lugar de
usar subclases. Esa forma la decidió el guardado binario de §4.10: `struct` empaqueta
registros de tamaño fijo, y una clase plana se empaqueta directo, mientras que una
jerarquía obligaría a inventar un formato con etiqueta de tipo.

### El azar

`GameState` guarda la instancia `random.Random(semilla)` que usa todo el modelo, y
guarda también la semilla, porque hace falta en el archivo de partida y en la cabecera
de la bitácora de reproducción. El generador global del módulo `random` no se usa en
ninguna parte, porque el enunciado lo prohíbe.

Queda una duda abierta. §2.11 dice que la reversión incluye "cualquier otro dato
modificado", y el estado interno del generador se modifica durante el intervalo que se
revierte. Nosotros no lo restauramos, por dos razones. Una práctica:
`random.Random.getstate()` devuelve cientos de enteros, y guardarlos por cada
intervalo se parece demasiado a la copia completa de estado que §2.11 prohíbe. Y una
de fondo: lo que §2.6 exige es que la misma semilla con la misma secuencia de acciones
dé la misma partida, y el uso del pergamino forma parte de esa secuencia, así que la
reproducción sigue siendo fiel. De todos modos conviene preguntarlo.

### Complejidad y pruebas

Todo acá es O(1) en tiempo y espacio constante.

`tests/test_game_state.py`, 20 pruebas, todas pasan. Cubren el reloj en cero y
cargado, el reloj de solo lectura, la numeración creciente, el avance hacia adelante y
al mismo instante, el rechazo de retroceder con `advance_clock_to()`, el retroceso
correcto y el rechazo de adelantar con `rewind_clock_to()`, el avance después de un
retroceso, que el contador no vuelve atrás, que la misma semilla da la misma secuencia
de valores y semillas distintas no, y que la semilla queda accesible.

---

## El bucle del motor

Estado: anda con esperar y atacar. Moverse, abrir puertas y todo lo de inventario
espera a que existan las salas y el inventario.

### Una acción del jugador es un ciclo completo de eventos

Cada método de acción de `Game` hace dos cosas: ejecuta la acción y después procesa
todos los eventos pendientes hasta que vuelva a tocarle decidir al jugador. El
controlador no toca el reloj ni la agenda.

La otra opción era darle el bucle al controlador, con un método que avanzara un evento
por llamada. La descartamos porque obligaría a la vista a entender cómo funciona el
reloj, que es justo lo que §6 pide evitar. Y hay una ventaja que no habíamos previsto:
§5.2 define el presupuesto de rendimiento sobre "un ciclo completo de eventos entre
dos decisiones consecutivas del jugador", y con esta forma ese ciclo es exactamente
una llamada. Se puede medir sin instrumentar nada.

### El actor se olvida de su evento apenas se ejecuta

Cada actor guarda la referencia a su acción pendiente. Cuando el motor saca ese evento
y lo ejecuta, pone la referencia en `None` antes de programar la siguiente.

Esto lo descubrimos escribiendo una prueba, y es el tipo de error que más miedo da.
Sin esa línea, el actor queda apuntando a un evento que ya se consumió. Si justo en
ese momento un efecto le cambiara la velocidad, `change_speed()` creería que tiene una
acción esperando, cancelaría un evento que ya no está en la agenda y programaría una
nueva. Al terminar el turno se programaría otra. El actor quedaría con dos acciones
pendientes y actuaría el doble de veces, sin lanzar ninguna excepción y sin que nada
se viera raro. Lo fija `test_the_player_has_no_pending_event_during_their_turn`.

### Los eventos de un muerto se filtran dos veces

Cuando un actor muere, el motor cancela su evento pendiente. Y además, el bucle
descarta cualquier evento cuyo actor ya no esté vivo, antes de ejecutarlo.

Parece redundante. No lo es. La cancelación cubre el caso normal, el de morir de un
golpe, pero un actor puede morir por un camino que no pase por el motor, por ejemplo
un pulso de veneno que lo deja en cero. El filtro del bucle garantiza la regla de §2.6
sin depender de que todas las causas de muerte se acuerden de cancelar.

Un evento descartado no mueve el reloj, porque no pasó nada.

### `GameState` lleva el tiempo, `Game` lleva la partida

`GameState` tiene el reloj, el contador y el generador aleatorio, que es justo lo que
hay que guardar para reanudar una partida. `Game` tiene los actores, la agenda, los
efectos y el resultado.

El corte quedó ahí por una razón concreta: `GameState.restore()` ya es la interfaz que
usa el guardado de §4.10, y meterle los actores adentro habría obligado a cambiarla de
nuevo después de habérsela pasado al resto del grupo.

### El ataque efectivo se resuelve por polimorfismo

`Actor` tiene `effective_attack` y `effective_defense`, que devuelven el valor base.
`Player` los sobrescribe sumando los bonos del arma y la armadura equipadas. Así la
fórmula de daño es una sola para todos y el motor nunca pregunta de qué tipo es el
actor que tiene enfrente.

El equipo se trata por duck typing: sirve cualquier objeto que tenga `attack_bonus` o
`defense_bonus`. Eso nos dejó probar el combate con equipo sin esperar al catálogo.

### El motor no sale a buscar el contenido de una sala

`move()` exige que el contenido de la sala destino ya esté en memoria y, si no lo está,
rechaza el movimiento sin consumir tiempo. Lo comprueba con `Room.content_loaded`.

El motor no puede pedirlo él mismo porque §6 dice que el modelo no conoce HTTP ni
archivos. Quien lo carga es el controlador, antes de llamar a `move()`, con
`RepositorioCripta.cargar_contenido_de_sala()`. Así se cumple la regla de §4.2 de que
el jugador nunca quede en una sala cuyo contenido no se conoce, sin que el modelo sepa
de dónde salieron los datos.

### La llave se reconoce por el id de su ficha, no por su campo `abre`

Esto lo encontramos probando contra los datos reales del API, y las pruebas unitarias
no lo habían detectado porque tenían adentro el mismo malentendido que el código.

La primera versión comparaba el campo `abre` de la llave contra la llave que pide la
puerta. Con los datos reales no coincide nunca: la llave negra trae
`abre: "puerta_salida"`, mientras que la puerta de la salida pide
`llave: "itm_llave_negra"`. Son dos cosas distintas, el nombre de una puerta y el id de
una ficha.

§2.7 lo dice sin ambigüedad: una llave "permite abrir puertas cuya llave coincide con
su id". O sea que hay que comparar contra el id de la ficha de la llave, que en el
modelo es `Item.type_id`. El campo `abre` queda como información descriptiva.

La prueba `test_the_key_matches_by_its_type_id_and_not_by_opens` construye la llave con
un `opens` que a propósito no coincide, igual que en los datos reales, para que el
error no pueda volver.

### Recorrer el inventario no pasa por el ciclo de eventos

`inventory_next()` e `inventory_previous()` cuestan 0, así que mueven el cursor y
devuelven sin programar nada ni procesar eventos.

No es un atajo, es obligatorio. Si pasaran por el camino normal de una acción, el
`max(1, costo * 100 // velocidad)` de §2.3 convertiría ese 0 en 1 y cada vez que el
jugador mirara su inventario el reloj avanzaría una unidad. Tampoco suman a
`player_actions`, porque §2.12 define una acción del jugador como la que consume tiempo
virtual.

Sí devuelven `accepted` en verdadero y por lo tanto quedan en la bitácora de
reproducción, que es lo que el grupo acordó: soltar, usar y equipar actúan sobre el
objeto que muestra el cursor, de modo que sin la navegación la reproducción elegiría
otro objeto.

### Usar un objeto aplica su efecto antes de correr el ciclo

`use_item()` aplica el efecto y recién después programa la siguiente acción del jugador.
Importa para la poción de velocidad: al aplicarse primero, la acción siguiente ya se
programa con la velocidad nueva.

El objeto se consume sin pasar por el suelo. `Inventory.drop_current()` lo quita del
inventario y el motor simplemente no lo coloca en ningún lado, que es lo que §2.7 pide
para los consumibles.

Las armas, las armaduras y las llaves no se pueden usar, y un pergamino de retroceso se
rechaza indicando que tiene su propia acción. Los tres rechazos no consumen tiempo.

### El cursor no se mueve al recoger

Vale dejarlo anotado porque sorprende y afecta a la vista. `Inventory.pick_up()` agrega
el objeto al final y solo mueve el cursor si el inventario estaba vacío. O sea que
recoger un arma y equiparla necesita una navegación en el medio.

Es una decisión de la Persona 3 y es defendible, porque el cursor es un concepto
separado del orden real. Pero conviene que la vista lo tenga en cuenta, y que el grupo
sepa que cada secuencia de recoger y equipar deja un comando más en la bitácora de
reproducción.

### Las acciones que dependen de otro integrante rechazan, no revientan

El controlador de la Persona 4 despacha los once comandos del enunciado, incluidos
`recoger`, `soltar`, `usar`, `equipar`, recorrer el inventario y el pergamino. Siete de
esos métodos no existían todavía en `Game`, porque dependían del inventario y del
historial reversible de la Persona 3, así que escribir "soltar" terminaba el programa
con `AttributeError`.

De esos siete, seis ya están implementados contra el inventario real. El único que
sigue devolviendo el rechazo provisional es `rewind()`, que espera a que el motor anote
sus cambios en el historial.

No era un error de su controlador: programó contra el contrato acordado. El hueco era
nuestro. Ahora esos siete métodos existen y devuelven un `ActionResult` rechazado que
dice qué falta, por ejemplo "Todavía no se puede soltar objetos: falta el inventario".

Es un rechazo distinto de los del Apéndice B: ahí la acción existe y el juego la
prohíbe, acá la acción es válida y el programa todavía no sabe hacerla. Se eligió
rechazar y no lanzar una excepción por dos razones. El enunciado pide que los errores
se reporten con contexto y no que terminen el programa, y una acción rechazada ya tiene
la semántica correcta para este caso: no consume tiempo, no cambia el estado, no
consulta el azar y no se registra en la bitácora de reproducción, de modo que una
partida reproducida no se ve afectada.

Cuando lleguen esas estructuras solo se reemplaza el cuerpo de cada método y la interfaz
no cambia.

### El enemigo decide, el motor ejecuta

`decide_action()` devuelve el par `(acción, salida)`, y la salida solo viene cuando la
acción es moverse. El enemigo recibe su sala y el generador aleatorio, pero no toca ni
el reloj ni la agenda: quien cambia la sala del enemigo y programa su siguiente acción
es el motor.

El errante filtra las salidas por `door.is_open` antes de elegir, porque §2.5 dice que
los enemigos no pueden abrir puertas cerradas. Si no queda ninguna abierta, espera con
costo 100, como fija el Apéndice B.

La elección sale de `GameState.random_generator`, el mismo generador con semilla que usa
el combate, de modo que el recorrido de un errante es reproducible.

Una prueba comprueba la regla **directamente sobre `decide_action()`**, con cien
elecciones sobre una sala que tiene una salida abierta y otra cerrada, y verifica que
nunca elige la cerrada. La versión anterior de esa prueba lo comprobaba jugando una
partida y pasaba por la razón equivocada: el errante se movía a la sala del jugador en
su primer turno y a partir de ahí atacaba en vez de moverse, así que nunca llegaba a
probar la puerta cerrada.

### El rastreador usa el rastro, no lo reimplementa

`PlayerTrail.freshest_exit(room, instante)` ya aplica las tres reglas de §2.9: examina
solo las vecinas por salidas abiertas, descarta los rastros de 400 unidades o más de
antigüedad, y desempata por la sala de menor id. El rastreador del motor no repite nada
de eso: pide la salida y responde `(MOVE, salida)` o `(WAIT, None)`.

`decide_action()` recibe ahora el rastro y el reloj, además de la sala y el generador.
La alternativa que ofrecía la Persona 3 era que el motor calculara la salida y se la
pasara ya resuelta. Se descartó porque obligaría al motor a preguntar de qué tipo es
cada enemigo antes de llamar a `decide_action()`, lo que duplicaría el reparto que ese
método ya hace. Con esta forma cada comportamiento recibe lo que necesita y decide solo:
el errante la sala y el generador, el rastreador el rastro y el reloj.

La firma quedó en cinco parámetros. Es su forma final, porque los tres comportamientos
de §2.8 ya están completos y no hay un cuarto.

### El rastro se marca en el instante de la acción, no al terminar su costo

Esta era una pregunta que la Persona 3 dejó abierta para el grupo: al moverse, ¿con qué
reloj se marca la sala destino?

Se marca con el reloj del instante en que se ejecuta la acción, antes de correr el ciclo
de eventos. Si el jugador se mueve en el instante 0 con una acción de costo 100, la sala
destino recibe 0 y no 100.

El enunciado lo define sin ambigüedad aunque no lo diga en §2.9. §2.5 dice que "el
jugador aparece en la sala destino al ejecutar la acción", y el ejemplo de §2.13 lo
confirma: el jugador se mueve al norte en el instante 0 y la rata, al actuar en el 66,
ya comparte sala con él. El costo de 100 define cuándo el jugador vuelve a actuar, no
cuándo llega.

Marcarlo después tendría además una consecuencia concreta: un rastreador que actuara
entre las dos decisiones del jugador vería el rastro más fresco de lo que corresponde.

La marca vive en `_finish_player_action()`, que es por donde pasan todas las acciones
aceptadas. Así se cumple de una sola vez lo que pide el Apéndice B, que el rastro de la
sala actual se refresque en cada acción del jugador y no solo al moverse. Las acciones
rechazadas no pasan por ahí, de modo que no lo tocan.

### La partida termina en el instante en que se gana o se pierde

Cuando el jugador entra a la sala de salida, o cuando una trampa lo mata al entrar, la
acción se ejecuta y se cuenta, pero el reloj no avanza el costo de esa acción ni se
procesan los eventos que venían después.

Es una interpretación declarada. El enunciado no dice qué pasa con el tiempo de la
acción que termina la partida. Hacer avanzar el reloj otras 100 unidades obligaría a
procesar los turnos de enemigos posteriores a una partida ya ganada, lo que no tiene
sentido y hasta podría matar al jugador después de haber ganado. El tiempo final que
§2.12 pide para la tabla de puntajes es entonces el instante en que se entró a la sala
de salida.

### Una partida terminada no acepta más acciones

Otro hallazgo de la revisión. Después de que el jugador moría, `wait()` y `attack()`
seguían aceptándose: sumaban a `player_actions`, metían eventos en la agenda y
devolvían `accepted` en verdadero. El reloj no avanzaba, porque el bucle revisa el
resultado antes de procesar, así que desde afuera no se notaba nada hasta que la tabla
de puntajes de §2.12 reportaba más acciones de las que el jugador ejecutó.

Ahora `Game` expone `is_over` y cada acción pública lo revisa antes de hacer nada. Si la
partida terminó, devuelve un `ActionResult` rechazado y no toca ningún estado.

Las acciones que falten deben seguir ese mismo patrón: revisar `is_over` como primera
línea, antes de validar cualquier otra cosa.

### Los contadores de la partida

`Game` lleva tres contadores: `player_actions`, `enemies_defeated` y
`events_processed`.

Los dos primeros los pide §2.12, que exige registrar en la tabla de puntajes las
acciones ejecutadas por el jugador y los enemigos derrotados. El tercero sirve para las
mediciones de frecuencia.

Una aclaración sobre `player_actions`, porque el enunciado es preciso con el término:
"acción del jugador" es una acción que consume tiempo virtual. Por eso el contador
sube únicamente cuando la acción se acepta. Una acción rechazada no cuenta, y el
pergamino de retroceso tampoco, porque §2.11 dice expresamente que no se registra como
acción del jugador.

### Orden de activación de enemigos

§2.4 pide activarlos en orden ascendente de identificador. Como son texto, los
comparamos como texto completo, según lo ya discutido en la sección 4.1.

El orden lo arma `structures/sorting.py`, el módulo de la Persona 3, que mide el
desorden de los datos y escoge entre inserción y mezcla. Antes había acá una inserción
escrita a mano, provisional mientras ese módulo no existiera. Usarlo no solo quita
código repetido: la activación de enemigos pasa a ser uno de los contextos reales de
ordenamiento que §4.9 pide, y el algoritmo lo escoge el programa y no nosotros.

### Límites conocidos

La bitácora de mensajes ya es el `CircularLog` de la Persona 3, y es lo que `Game` usa
por omisión cuando no le pasan otra. Antes era una `list` que crecía sin parar, lo que
incumplía §4.8. Se puso como valor por omisión y no como algo que haya que conectar,
para que el comportamiento correcto sea el que sale sin hacer nada.

Un efecto secundario que vale anotar: `messages` dejó de ser una lista, así que el
código que la lea debe recorrerla y no usar métodos de lista. Cuatro pruebas nuestras
asumían lo contrario y hubo que corregirlas para que respetaran el contrato que
nosotros mismos habíamos documentado.

Los tres comportamientos de §2.8 están completos.

Los nombres de `behavior` ya están verificados. Eran una apuesta, porque el enunciado
solo confirma `"rastreador"` en su ejemplo de catálogo, pero al integrar el bloque 2 se
comprobó contra el API real que el servicio envía `"guardián"` con tilde. El Traductor
convierte el texto del API a las constantes de `Enemy` antes de que lleguen al modelo,
así que `decide_action()` compara contra `Enemy.GUARDIAN` sin problema y no hubo que
cambiar nada.

**La regeneración queda implementada pero el API no puede activarla.** Esto salió de
una duda nuestra: el motor implementa la regla de §2.10 y la activa sola cuando
`enemy.regeneration` es mayor que cero, pero el Traductor nunca llena ese campo, así que
siempre llega en cero. Parecía un hueco que la cripta de la revisión podía destapar.

La Persona 2 lo verificó contra el contrato del servicio (`/openapi.json`, versión 1.0.0,
15 de octubre de 2026): el esquema de enemigo solo admite `id`, `nombre`, `clase`,
`vida_max`, `ataque`, `defensa`, `velocidad`, `comportamiento` y `suelta`, el de
colocación solo `instancia`, `tipo` y `vida`, los dos son cerrados y la palabra
"regenera" no aparece en todo el documento. Como la cripta de la revisión sale del mismo
servicio, tampoco puede declararla.

La implementación se mantiene porque §2.10 la exige y está probada. Y el Traductor
quedó avisando cualquier campo que no reconozca, una vez por campo, de modo que si el
contrato cambiara no se perdería en silencio.

Los objetos que suelta un enemigo al morir ya se colocan en el suelo de la sala donde
murió, como pide §2.6. Se verificó contra los datos reales: las dos ratas gigantes de
la sala 2 de `cripta-01` dejan su poción menor junto a la daga que ya estaba ahí.

### Complejidad

| Operación | Costo |
| --- | --- |
| Procesar un evento | O(log n), por sacarlo de la agenda |
| Buscar el enemigo al que se ataca | O(e) sobre los enemigos, una vez por acción del jugador y no por evento |
| Programar la acción de un actor | O(log n) |
| Cancelar la acción de un actor | O(1) |

### Evidencia empírica

Medido con `benchmark/scheduler_bench.py` en Python 3.14.6 sobre Windows 11.

§5.2 da 20 ms para resolver un ciclo completo de eventos entre dos decisiones del
jugador, sin contar red ni dibujado en pantalla.

La primera versión de esta medición era floja: el jugador solo esperaba, los enemigos
eran guardianes que no se movían y no había ni salas ni trampas ni puertas. Daba
0.1705 ms por ciclo, pero no probaba casi nada de lo que el motor hace.

El escenario actual recorre una cripta de verdad. El jugador camina de punta a punta y
vuelve, cada sala tiene una trampa que se rearma, una de cada tres puertas está cerrada
y se cierra sola después de abrirla, y los enemigos son errantes que se reparten por la
cripta mientras el jugador la recorre. Además hay un veneno y una antorcha corriendo, y
todos los enemigos tienen regeneración.

Que el escenario ejercita lo que dice está comprobado: en la corrida de la cripta
pequeña hubo 833 entradas a salas con sus 833 activaciones de trampa, 167 aperturas de
puerta y 167 cierres automáticos.

| | 6 salas, 5 errantes | 40 salas, 50 errantes |
| --- | ---: | ---: |
| Decisiones del jugador | 1 000 | 1 000 |
| Eventos por decisión | 11.2 | 90.5 |
| Tamaño máximo de la agenda | 19 | 109 |
| **Tiempo por ciclo** | **0.0357 ms** | **0.3302 ms** |
| Lo que permite §5.2 | 20 ms | 20 ms |

En el caso grande usamos el 1.7 % del presupuesto. El margen sigue siendo enorme, pero
conviene notar que el ciclo se volvió casi diez veces más caro al pasar de 5 a 50
enemigos, y que el costo crece con la cantidad de enemigos activos y no con el tamaño
de la cripta: lo que pesa es cuántos actores programan eventos, no cuántas salas hay.

Falta una sola cosa por medir: la decisión de un rastreador, que es la más cara de §2.8
porque examina las salas vecinas y consulta el rastro. Cuando exista hay que repetir
esta medición.

### Pruebas

`tests/test_game.py`, 31 pruebas, todas pasan. Están agrupadas en bucle, combate,
acciones rechazadas, determinismo, activación de enemigos, cambio de velocidad, estado
visible y contadores.

Los tiempos se verifican contra el ejemplo de §2.13 del enunciado: un enemigo de
velocidad 150 activado en cero queda programado para 66 y alcanza a actuar una vez
antes de la siguiente decisión del jugador; uno de velocidad 250 actúa dos veces.
También comprobamos que una acción rechazada no mueve el reloj ni consulta el
generador aleatorio, y que dos partidas con la misma semilla y las mismas acciones
producen exactamente los mismos mensajes.

---

## Efectos temporales

Estado: los seis efectos de §2.10 están implementados y probados, incluidas las
trampas y el cierre automático de puertas.

### El veneno programa todos sus pulsos de una vez

§2.10 fija el veneno en un pulso cada 80 unidades durante 400. Los dos números son
constantes, así que apenas se aplica ya se saben los cinco instantes en que va a hacer
daño: 80, 160, 240, 320 y 400. El motor los programa todos juntos.

Lo primero que intentamos fue lo obvio: que cada pulso programara el siguiente. El
problema aparece al preguntarse si queda otro pulso, porque para eso el evento tendría
que saber cuándo termina el efecto, y ese dato no cabe adentro del evento. Habría que
tener un objeto de efecto con estado propio y, peor, una forma de encontrarlo cada vez
que se procesa un pulso. Programarlos todos de una vez borra las dos necesidades: cada
pulso solo aplica el daño que trae el evento.

De paso, el antídoto se vuelve trivial. §2.10 dice que cancelar un efecto impide sus
activaciones futuras, y acá esas activaciones son unos eventos concretos que ya
tenemos identificados. Cancelarlas es marcarlos.

El costo son cinco entradas en el montículo en vez de una. Frente a los varios cientos
de eventos simultáneos que menciona §4.1, y con inserción en O(log n), no mueve la
aguja.

Una interpretación que declaramos: el pulso del instante 400 sí se aplica. El
enunciado dice que el veneno "dura 400 unidades desde su aplicación" y no aclara qué
pasa con la activación que cae justo en el borde. Decidimos incluirla, así que un
veneno completo hace cinco pulsos. Queda fijado en
`test_poison_lasts_four_hundred_units_and_no_more`.

### La regeneración no se registra como efecto cancelable

La regeneración no tiene duración. §2.10 dice que el enemigo recupera la cantidad
indicada cada 200 unidades y nada más. Como no se sabe cuándo termina, no se puede
programar por adelantado, así que acá sí cada pulso programa el siguiente.

No la guardamos en la lista de efectos activos porque nada la cancela: se detiene sola
cuando el enemigo muere, gracias al filtro del bucle. Y tampoco se muestra en pantalla,
porque es una característica de los enemigos y no un efecto sobre el jugador.

Cada pulso reprograma el siguiente leyendo la cantidad del propio evento, sin mirar
ningún estado externo. Que la vida no pase del máximo lo garantiza el setter de
`health`, como ya se explicó más abajo.

### El cambio de velocidad lo aplica el motor

§2.10 pide reajustar la próxima acción tanto al empezar el efecto como al terminarlo.
Ese reajuste cancela un evento e inserta otro, que es trabajo de la agenda, así que no
puede vivir adentro de un objeto de efecto sin que el modelo de efectos pase a depender
del motor, cosa que generaría una dependencia circular.

`apply_speed_change()` cambia la velocidad llamando a `change_actor_speed()`, que ya
hace el reescalado de §2.3, y programa un evento de fin que lleva la velocidad anterior
en el campo `amount`. Cuando ese evento se dispara, el motor vuelve a llamar a
`change_actor_speed()` con ese valor. El reajuste del final usa exactamente el mismo
camino que el del comienzo, que es la mejor garantía de que los dos hagan lo mismo.

### Un efecto de velocidad reemplaza al anterior

Esto salió de una revisión, no del diseño inicial, y vale contarlo porque el error era
invisible.

La primera versión permitía encimar efectos. Una poción subía al jugador de 100 a 200 y
anotaba "restaurar a 100". Una segunda lo subía de 200 a 300 y anotaba "restaurar a
200". Cuando terminaba la primera lo bajaba a 100, aunque la segunda siguiera activa, y
cuando terminaba la segunda lo subía a 200. El jugador quedaba en 200 de forma
permanente, sin ningún efecto activo, y sin que nada lanzara una excepción.

Ahora aplicar un efecto de velocidad termina primero el anterior sobre ese mismo actor:
le devuelve la velocidad original y cancela su evento de fin. Recién entonces aplica el
nuevo, de modo que lo que el nuevo anota restaurar es siempre la velocidad base.

Devolver la velocidad y volver a cambiarla no descuadra el reescalado. Si al actor le
faltaba `r` unidades y pasa de la velocidad `v` a la original `o` y de ahí a la nueva
`n`, el resultado es `r * v / o * o / n`, que es lo mismo que un único reescalado de
`v` a `n`.

Esta es una interpretación declarada: el enunciado no dice qué pasa con dos efectos de
velocidad simultáneos. Elegimos reemplazar porque es lo que §2.7 establece para efectos
del mismo tipo, cuando dice que equipar otra arma sustituye a la anterior.

### Cómo se reparten los eventos de efecto

El bucle mira `event_type` y reparte con una cadena de `if`/`elif`. Sin tabla de
despacho, porque §7 prohíbe `dict` como tabla de búsqueda y porque con cinco tipos una
cadena de condiciones se lee mejor que cualquier alternativa y no hay que explicarla.

### Límites conocidos

Las trampas y el cierre de puertas dependen de las salas y no están.

La antorcha solo se enciende y se apaga. Lo que ilumina es asunto de la vista; el
modelo se limita a informar si está prendida.

Y si a un mismo actor le cae un segundo veneno, los efectos se acumulan: se programan
los pulsos de los dos y el antídoto cancela ambos. El enunciado no dice qué debería
pasar ahí, así que esto es una interpretación nuestra y no una regla verificada.

Queda una asimetría a propósito: dos venenos se acumulan, pero dos efectos de velocidad
se reemplazan. La razón es que acumular veneno solo hace más daño, que es un resultado
plausible y sin consecuencias más allá del propio efecto, mientras que acumular
velocidad corrompía la velocidad base del actor de forma permanente, como se explica
arriba. Donde el enunciado no decide, elegimos la interpretación que no deja el estado
del juego en un valor incorrecto.

### Complejidad

| Operación | Costo |
| --- | --- |
| Aplicar veneno | O(p log n), con p igual a 5 pulsos |
| Cancelar veneno con un antídoto | O(e + p) sobre los efectos activos |
| Un pulso de veneno o de regeneración | O(log n) |
| Empezar o terminar un cambio de velocidad | O(log n) |

### Pruebas

`tests/test_effects.py`, 33 pruebas, todas pasan.

Cubren los casos del Apéndice B que tienen que ver con efectos: que un antídoto
aplicado antes del siguiente pulso evita todo el daño posterior, que la vida regenerada
nunca supera el máximo, y que la regeneración se corta cuando el enemigo muere.

Además comprobamos que el veneno hace exactamente cinco pulsos y ni uno más, que la
velocidad vuelve a su valor anterior cuando termina el efecto, que terminar el efecto
reprograma la acción pendiente con una secuencia nueva, y que una partida con varios
efectos encima sigue siendo reproducible con la misma semilla.

Van ahí también las dos pruebas de la bitácora inyectada, que comprueban que `Game` usa
la estructura que le pasan y que funciona con cualquier cosa que tenga `append()` y se
pueda recorrer, incluida una con límite de capacidad.

Las nueve últimas son las que fijan los dos errores que encontró la revisión: que un
segundo y un tercer efecto de velocidad no dejen al actor con una velocidad permanente
equivocada, y que una partida terminada rechace las acciones sin contarlas ni programar
eventos.

---

## Actores, intervalos y cambios de velocidad

Estado: implementado y probado. No es un problema del §4; implementa las reglas de §2.2
y §2.3.

### El `max(1, ...)` del intervalo no es un adorno

El intervalo de una acción es `max(1, costo * 100 // velocidad)`. Esa división es
entera, y puede dar cero cuando la velocidad es mucho más grande que el costo: con
velocidad 10000 y una acción de costo 25, `2500 // 10000` da 0.

Sin el `max(1, ...)`, ese actor quedaría programado para el mismo instante en que está
actuando. Volvería a actuar en ese instante. Y otra vez. El reloj no avanzaría nunca y
el bucle principal no terminaría. El mínimo de 1 garantiza que toda acción empuje el
reloj por lo menos una unidad.

Lo fija `test_interval_is_never_zero`.

### El límite de vida vive en el setter

`health` es una propiedad y su setter recorta el valor al rango `[0, max_health]`.

El enunciado pide ese límite en dos lugares distintos del Apéndice B: la regeneración
de un enemigo y la poción de curación. Podríamos haber escrito el recorte en cada
operación que toca la vida, pero eso repite la regla y deja la puerta abierta a
olvidarla en una tercera operación futura, como un efecto nuevo que todavía no
existe. Poniéndola en el setter, la regla se escribe una vez y no hay forma de
saltársela.

Acá no lanzamos `ValueError`, a diferencia del resto de las validaciones, porque
recortar es una regla del juego y no un error del programa. Donde sí lanzamos es en
`speed`, porque una velocidad de cero haría fallar la división del intervalo, y en
`max_health` y `actor_id`.

### El actor calcula el reescalado, el motor reprograma

`change_speed(current_time, new_speed)` aplica la fórmula de §2.3, devuelve el
instante reprogramado y recién después reemplaza la velocidad.

Lo resolvimos en un solo método porque la fórmula necesita las dos velocidades al
mismo tiempo, la vieja y la nueva. Si cambiar la velocidad y calcular fueran dos pasos
separados, bastaría invertir el orden para que el resultado saliera mal sin que nada
avisara. `test_rescale_uses_the_previous_speed_not_the_new_one` existe justamente para
detectar esa inversión.

El método no toca el evento pendiente ni la agenda. Devuelve el instante, y el motor se
encarga de cancelar el viejo y meter uno nuevo con secuencia nueva, como exige §2.3 y
como necesita el montículo para no romperse.

### Los costos de las acciones no viven en el actor

`Actor` solo sabe convertir un costo en un intervalo según su velocidad. La tabla de
costos de §2.3 es una propiedad de cada acción, no del actor, así que vive en el motor.

### La referencia al evento pendiente

Cada actor guarda en `scheduled_event` la referencia a su acción programada. Como un
actor tiene a lo sumo una pendiente a la vez, eso permite cancelarla en O(1) cuando
muere, sin recorrer la agenda. Es lo que hace posible cumplir §4.1.

### Complejidad y pruebas

Todo acá es O(1) en tiempo y espacio.

`tests/test_actor.py`, 23 pruebas, todas pasan, agrupadas en intervalos, vida,
validación y cambio de velocidad.

Los intervalos los verificamos contra los números del propio enunciado: velocidad 150
con costo 100 da 66, que es el ejemplo de §2.4 y §2.13, y la secuencia del jugador de
§2.13, moverse en 0, recoger en 100 y equipar en 125, produce 100, 125 y 175.

---

## Resumen del estado de las pruebas

| Archivo | Pruebas |
| --- | ---: |
| `tests/test_event_queue.py` | 18 |
| `tests/test_game_state.py` | 20 |
| `tests/test_actor.py` | 23 |
| `tests/test_game.py` | 36 |
| `tests/test_effects.py` | 33 |
| `tests/test_movement.py` | 61 |
| `tests/test_inventory_actions.py` | 32 |
| **Total del motor** | **223** |

Con las del bloque 2 integradas, el proyecto tiene 618 pruebas y todas pasan en
Python 3.14.6. Se corren con `python -m unittest discover -s tests -t . -v` desde
`cripta/`, con las dependencias de `requirements.txt` instaladas.

El motor se probó además contra los datos reales de `cripta-01`: se recorre la cripta
desde la sala inicial hasta la de salida, disparando la trampa de la sala 2, abriendo
con la llave negra la puerta de la salida y terminando en victoria con el reloj en 350
y cero solicitudes de red.

Las mediciones se corren con `python -m benchmark.scheduler_bench` desde la misma
carpeta.
