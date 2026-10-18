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

Las secciones están en el orden de los problemas del §4 del enunciado. Después vienen
las decisiones que no corresponden a un problema del §4 pero que condicionan al resto
del grupo, y al final el estado de las pruebas.

Las secciones 4.2, 4.3, 4.4 y 4.10 todavía no están escritas. Cada una dice de quién es
y qué le falta.

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
| Eventos procesados | 11 081 | 101 756 | 13 081 | 90 504 | 189 310 |
| Eventos por decisión | 11.1 | 101.8 | 13.1 | 90.5 | 378.6 |
| Inserciones | 11 092 | 101 857 | 13 095 | 90 607 | 190 010 |
| Extracciones | 11 081 | 101 756 | 13 081 | 90 504 | 189 310 |
| Inserciones por extracción | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Cancelaciones | 0 | 0 | 0 | 0 | 750 |
| Tamaño máximo de la agenda | 17 | 107 | 21 | 109 | 506 |

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

---

## 4.2 Traer el contenido antes de que haga falta (precarga)

Estado: implementado, probado y medido.

### Problema

Antes de confirmar que el jugador entra a una sala, su contenido (enemigos, objetos y
trampas) tiene que estar en memoria (§2.5). Si lo pedimos justo al cruzar la puerta, el
jugador espera unos 400 ms en cada movimiento (§3.4). Pero cada solicitud gasta
presupuesto, y el presupuesto es por partida: cripta-01 tiene 9 solicitudes para todo,
incluida la lista de criptas y el catálogo.

Lo que juega a favor: el esqueleto se descarga completo al empezar, así que conocemos el
mapa entero, y una solicitud de contenido cuesta lo mismo con 1 sala que con 10 (§3.4).
El problema es decidir **cuándo** pedir y **qué salas** meter en cada lote.

Las cifras que siguen están **medidas** con `benchmark/bench_frecuencia_bloque2.py`, que
recorre la cripta como lo hace el controlador y cuenta cada operación. Son conteos con
semilla fija, así que dan lo mismo en cualquier computadora. La salida completa está en
`docs/mediciones/bloque2/frecuencias_2026-10-18.txt`.

| Operación | Cuándo ocurre | cripta-01 real (20 acciones) | Cripta sintética de 900 salas (300 acciones) |
| --- | --- | ---: | ---: |
| Revisar si hace falta precargar | al empezar y después de cada acción | 21 | 301 |
| Armar y pedir un lote con BFS | cuando a la sala actual o a una vecina le falta contenido | 1 (6 salas) | 33 (330 salas) |
| Esperar en una puerta | se entra a una sala que la precarga no trajo | 0 | 0 |

La revisión ocurre en cada acción y casi nunca hace nada: en cripta-01 hubo 21 revisiones
y un solo lote. Por eso la revisión tiene que ser barata, y el BFS, que es lo caro, puede
costar más porque ocurre pocas veces.

### Alternativas consideradas

Comparamos tres estrategias sobre el mismo recorrido del jugador. Las tres están
implementadas en `benchmark/bench_precarga_contenido.py`.

**Sin precarga.** Pedir cada sala cuando el jugador intenta entrar. Es lo más simple y
nunca descarga una sala de más, pero hace esperar en todas las puertas y gasta una
solicitud por sala visitada. En cripta-01 serían 6 solicitudes solo de contenido, de 9
que hay para toda la partida.

**Solo vecinos directos.** Cuando el jugador llega a una sala, pedir esa sala y sus
vecinas sin contenido (a lo sumo 5 por lote). Elimina las esperas, pero desperdicia el
lote: como cada sala tiene como mucho 4 salidas, nunca llena las 10 posiciones que
permite el API, así que vuelve a pedir apenas el jugador da un par de pasos.

**Precarga en segundo plano.** Pedir con hilos mientras el jugador piensa. La descartamos
sin implementarla: el orden en que llegan las respuestas no puede cambiar la partida
(§2.4) y la reproducción tiene que ser fiel (§4.11). Con solicitudes síncronas nunca hay
una respuesta pendiente y ese problema desaparece (decisión D1). `adapters/fuente_datos.py`
deja anotado qué habría que cambiar si algún día se hiciera.

### Decisión

**Precarga por BFS con lotes llenos**, en `repository/gestor_contenido.py`, sobre el grafo
de `structures/grafo_salas.py`.

- **Cuándo:** al empezar la partida y después de cada acción, `despues_de_accion()`
  revisa la sala actual y sus vecinas directas. Si todas tienen contenido, no hace nada.
- **Qué:** si a alguna le falta, recorre el mapa en anchura (BFS) desde la sala del
  jugador y junta las 10 salas más cercanas que todavía no tienen contenido. Se piden en
  una sola solicitud.
- **Antes de entrar:** `cargar_contenido_de_sala()` verifica que la sala destino esté
  cargada. Si la precarga no la trajo, la pide ahí mismo y lo cuenta como una "espera en
  la puerta" en el reporte.
- **Reserva:** si quedan 2 solicitudes o menos, la precarga se detiene (supuesto S3). Esas
  últimas quedan para entrar a una sala a la que el jugador de verdad se mueve.
- **Determinismo:** las solicitudes son síncronas y el contenido entra al modelo cuando el
  jugador entra a la sala (D2). Como `--replay` pasa por el mismo controlador, reproducir
  un log pide las mismas salas en el mismo orden.

El grafo es una lista de adyacencia sobre `TablaHash`, con los vecinos siempre en el orden
N, S, E, O. Incluye las salidas cerradas, porque el jugador puede abrirlas. La cola del
BFS es una `list` con un índice que marca el frente: sacar de la cola es avanzar el
índice, sin desplazar elementos.

El contenido descargado también se guarda en disco por versión de la cripta
(`adapters/almacen_cripta.py`). Eso se cuenta en la sección 4.4.

### Análisis de complejidad

Con V salas y E salidas (E ≤ 4V):

| Operación | Costo | Frecuencia |
| --- | --- | --- |
| Revisar si hace falta precargar | O(1) promedio por sala, a lo sumo 5 salas | una por acción |
| Comprobar que la sala destino esté cargada | O(1) | uno por movimiento |
| BFS para armar un lote | O(V + E) en el peor caso, pero se detiene al juntar 10 salas | solo cuando falta contenido cerca |
| Sacar de la cola del BFS | O(1) | una por sala visitada por el BFS |

En la práctica el BFS se detiene enseguida, porque las salas sin contenido están cerca
del borde de lo ya descargado. El costo que importa no es de CPU: una solicitud son unos
400 ms, mucho más que recorrer cualquier cripta en memoria.

### Evidencia empírica

**Mismo recorrido, tres estrategias** (`python -m benchmark.bench_precarga_contenido`).
Cuenta solicitudes y esperas, no tiempo, así que el resultado es exacto y se repite igual
en cualquier computadora. Coincide con la tercera corrida oficial del 13 de octubre
(`docs/mediciones/bloque2/medianas_2026-10-13.md`).

| Escenario | BFS (decisión) | Solo vecinos directos | Sin precarga |
| --- | --- | --- | --- |
| cripta-01 real, recorrido completo | 1 solicitud, 0 esperas | 4 solicitudes, 0 esperas | 6 solicitudes, 6 esperas |
| Cuadrícula 10×10, 300 pasos al azar | 10, 0 esperas | 57, 0 esperas | 81, 81 esperas |
| Cuadrícula 20×20, 300 pasos al azar | 31, 0 esperas | 117, 0 esperas | 130, 130 esperas |
| Cuadrícula 30×30, 300 pasos al azar | 33, 0 esperas | 125, 0 esperas | 135, 135 esperas |

El BFS gasta entre 3,8 y 5,7 veces menos solicitudes que pedir solo los vecinos, y
ninguna estrategia con precarga hace esperar al jugador. Sin precarga, el jugador espera
en cada sala nueva que visita.

**Contra el API real** (14 de octubre, `docs/mediciones/bloque2/presupuesto_api_real_2026-10-14.md`):
recorriendo cripta-01 con `tools.simular_partida_bloque2`, todo el contenido de la cripta llegó en
**un solo lote** de 6 salas, y hubo 0 esperas en la puerta. La partida completa usó 7 de
las 9 solicitudes.

### Límites conocidos

- **Descarga salas que el jugador nunca visita.** En la cuadrícula de 20×20 se descargaron
  310 salas para 130 visitadas. No cuesta presupuesto, porque se cuentan solicitudes y no
  salas, pero ocupa memoria con contenido que tal vez no se use.
- **No sabe hacia dónde va el jugador.** El BFS trata igual todas las direcciones, incluidas
  las puertas cerradas con llave. En una cripta con muchas puertas cerradas puede traer
  salas a las que el jugador tarda en llegar.
- **Si el presupuesto se agota, el jugador puede quedar encerrado.** Con 2 solicitudes o
  menos la precarga se detiene, y si después se gastan esas últimas, entrar a una sala sin
  contenido se rechaza sin consumir tiempo (S1). El juego no se cae, pero esa sala queda
  inaccesible. Con cripta-01 sobran 2 solicitudes, y no sabemos el presupuesto de la cripta
  de la revisión.
- **Las mediciones grandes son sintéticas.** Las cuadrículas tienen todas las puertas
  abiertas y salas de hasta 4 salidas. Una cripta real con pasillos largos haría que el BFS
  llegue más lejos para juntar 10 salas, sin cambiar la cantidad de solicitudes.

### Pruebas

`tests/test_grafo_salas.py` (13 pruebas) cubre el BFS: orden por distancia en cripta-01 y
en una cuadrícula grande, vecinos en orden N, S, E, O, salidas cerradas incluidas y que el
recorrido sea determinista. `tests/test_gestor_contenido.py`
(17) cubre la precarga, la reserva de solicitudes, las esperas en la puerta y el contenido
recuperado de disco. `tests/test_repositorio_cripta.py` (26) verifica el presupuesto real
de cripta-01 de punta a punta: 7 solicitudes en frío, con 1 lote de contenido.

---

## 4.3 Resolución de referencias del catálogo

Estado: implementado, probado y medido.

### Problema

Antes de mostrar o simular un enemigo, un objeto o una trampa, su id de tipo tiene que
convertirse en una ficha del catálogo (§4.3). Esos ids aparecen en el contenido de cada
sala, en un orden que no controlamos, y se repiten mucho: dos ratas de la misma sala son
el mismo `ent_rata_gigante`. Además, un enemigo puede soltar objetos cuyas fichas tampoco
tenemos todavía.

Pedir cada id por separado no entra en el presupuesto, y un id que ya está en memoria o en
disco no se debe volver a pedir.

Medido con `benchmark/bench_frecuencia_bloque2.py`, en arranque en frío:

| Operación | Cuándo ocurre | cripta-01 real (20 acciones) | Cripta sintética de 900 salas (300 acciones) |
| --- | --- | ---: | ---: |
| Consultar si una ficha ya está (memoria o disco) | al preparar cada sala y en la precarga de fichas | 57 (2,9 por acción) | 4 853 (16,2 por acción) |
| Ficha que hacía falta y no estaba (fallo) | primera vez que se necesita un tipo | 2 | 20 |
| Pedir un lote al catálogo | cuando falta alguna ficha | 2 lotes, 11 fichas | 11 lotes, 60 fichas |

Lo que muestra la tabla: preguntar "¿esta ficha ya está?" es lo que más se repite, y pedir
fichas al API casi no ocurre. En cripta-01 hicieron falta 11 fichas, pero solo 2 fueron
fallos: las otras 9 ya habían llegado de relleno en un lote anterior, como se explica en
la decisión.

### Alternativas consideradas

Implementamos las tres estrategias sobre el mismo `GestorCatalogo`, y las medimos en el
mismo recorrido (`CatalogoUnaFichaPorSolicitud` y `CatalogoLotesSinRelleno`, en
`benchmark/bench_frecuencia_bloque2.py`).

**Una ficha por solicitud** (lo que haría `GET /catalogo/<id>`). Es lo más directo. Pero
§3.4 dice que una solicitud con 10 ids cuesta lo mismo que con 1, así que cada solicitud
de una sola ficha desperdicia nueve lugares. En cripta-01, con su presupuesto real de 9,
el jugador **no logra salir de la sala inicial**: se gasta el presupuesto antes de tener
las fichas de la sala 2.

**Lotes de 10 solo con lo necesario.** Junta en un lote los ids que hacen falta en ese
momento. Mejora mucho, pero en cripta-01 cada sala pide pocas fichas nuevas, y los lotes
salen casi vacíos: el presupuesto se agota a mitad de la partida y 7 de los 20 movimientos
se rechazan.

Para saber si un id ya está disponible también comparamos estructuras: tabla hash, lista
ordenada con búsqueda binaria y búsqueda lineal. Esa comparación está en la sección 4.4,
porque es la misma búsqueda que usa la caché.

### Decisión

**Lotes de 10 rellenos con ids conocidos** (decisión D4), en `repository/gestor_catalogo.py`.

- Para cada id busca primero en memoria (`CacheCatalogo`), después en disco
  (`AlmacenFichas`) y solo al final en el API. `obtener_ficha()` nunca usa la red; antes de
  usar una ficha hay que llamar a `asegurar_fichas()`.
- **Ids conocidos.** Cada vez que llega contenido, sus tipos se anotan como conocidos en una
  `ListaSinRepetidos` (`structures/lista_sin_repetidos.py`): una `list` en orden de llegada
  más una `TablaHash` para descartar repetidos en O(1). Lo mismo con el campo `suelta` de
  cada enemigo que llega.
- **Armado del lote.** Primero van los ids que hacen falta ahora. Si queda espacio, el lote
  se completa con ids conocidos que todavía no se descargaron, en el orden en que se
  descubrieron. Una solicitud con 10 ids cuesta lo mismo que con 1, así que el relleno
  adelanta fichas que se van a necesitar después sin gastar nada extra.
- **Determinismo.** El orden de descubrimiento depende solo del orden en que se pidió el
  contenido, que es síncrono. Por eso los lotes son siempre los mismos, también al
  reproducir.
- **Objetos que suelta un enemigo.** Se aseguran antes de entrar a la sala, nunca a mitad
  de un combate, y normalmente ya llegaron con la precarga.
- **Respuestas incompletas.** Si el API no devuelve un id pedido, se informa con
  `FichaNoDisponible`.

### Análisis de complejidad

Con k ids pedidos, n fichas guardadas en disco y p ids conocidos:

| Operación | Costo | Frecuencia |
| --- | --- | --- |
| Consultar si una ficha está | O(1) promedio en memoria; si no está, O(log n) en el índice del disco | la más frecuente: 2,9 a 16,2 por acción |
| Anotar un id conocido | O(1) promedio (`ListaSinRepetidos`) | una vez por tipo en cada lote de contenido |
| `asegurar_fichas(k ids)` sin descargar | O(k) consultas | una por sala preparada y en cada precarga |
| Armar un lote | O(p) para recorrer los conocidos | solo cuando hay que descargar |
| Descargar un lote | una solicitud de red (~400 ms) | 2 por partida en cripta-01 |

Recorrer los ids conocidos para armar un lote es lineal, pero ocurre pocas veces (11 lotes
en 300 acciones en la cripta sintética), y es despreciable frente a los 400 ms de la
solicitud que se ahorra.

### Evidencia empírica

**Las tres estrategias en el mismo recorrido** (`python -m benchmark.bench_frecuencia_bloque2`,
salida completa en `docs/mediciones/bloque2/frecuencias_2026-10-18.txt`):

| Escenario | Lotes con relleno (decisión) | Lotes sin relleno | Una ficha por solicitud |
| --- | --- | --- | --- |
| cripta-01 real, presupuesto 9, 20 pasos | 2 solicitudes de catálogo, 7 en total, 20 movimientos | 4 de catálogo, 9 en total, presupuesto agotado: 7 movimientos rechazados | 4 de catálogo, 9 en total: no sale de la sala inicial |
| Sintética 30×30, 60 tipos, 300 pasos | 11 de catálogo, 65 en total | 29 de catálogo, 83 en total | 60 de catálogo, 114 en total |

En la cripta sintética, que tiene presupuesto ilimitado, el relleno gasta 2,6 veces menos
solicitudes de catálogo que los lotes sin relleno y 5,5 veces menos que pedir de a una. En
cripta-01 la diferencia es más grave: con el presupuesto real, solo la decisión permite
terminar el recorrido.

**Contra el API real** (14 de octubre, medido dos veces: antes y después de integrar el
Traductor): las 11 fichas de cripta-01 llegaron en 2 lotes con solo 2 fallos de caché, y la
partida usó 7 de 9 solicitudes.

### Límites conocidos

- **El relleno puede traer fichas que no se usen.** Solo rellena con ids que aparecieron
  en contenido ya descargado, así que es probable que se usen, pero no seguro: el jugador
  puede no llegar nunca a esa sala. El costo es memoria y disco, no presupuesto.
- **Depende de la precarga de contenido.** El relleno solo puede adelantar ids que ya se
  conocen. Si la precarga se detiene por presupuesto, los lotes de catálogo vuelven a salir
  más vacíos.
- **Una cripta con muchos tipos no entra en un presupuesto chico.** Con 10 fichas por
  solicitud, un catálogo de t tipos necesita al menos t/10 solicitudes. Si la cripta de la
  revisión tuviera muchos más tipos que solicitudes disponibles, la caché en disco de una
  partida anterior sería la única forma de completarla.
- **Lo que suelta un enemigo se conoce tarde.** Se sabe recién cuando llega la ficha del
  enemigo. Si no queda presupuesto para un lote más, esa ficha se pide al entrar a la sala.

### Pruebas

`tests/test_gestor_catalogo.py` (21 pruebas) cubre que lo ya disponible no se vuelva a
pedir, los ids repetidos, el relleno con ids conocidos (también lo que suelta un enemigo),
que cripta-01 quepa en dos lotes, que los lotes sean deterministas, la recuperación desde
disco con una caché chica y el id que el API no devuelve.
`tests/test_lista_sin_repetidos.py` (3) cubre el orden de llegada sin repetidos.
`tests/test_bench_frecuencia_bloque2.py` (7) fija los conteos de esta sección: si cambia
el comportamiento del catálogo, la prueba falla y hay que actualizar estas cifras.

---

## 4.4 Reutilización y caché persistente

Estado: implementado, probado y medido.

### Problema

En memoria caben como mucho `--cache-size` fichas (25 por defecto). Al llegar al tope hay
que liberar alguna, pero nunca una que esté en uso: la de un enemigo vivo, un objeto del
inventario, o un objeto o una trampa de la sala actual (§4.4). Una ficha liberada tiene que
seguir en disco, de modo que volver a necesitarla cueste una lectura de disco y no una
solicitud. Y la caché tiene que sobrevivir al cierre del programa, validada por la versión
del catálogo. Lo mismo vale, por versión de la cripta, para el esqueleto y el contenido.

Medido con `benchmark/bench_frecuencia_bloque2.py`, en arranque en frío:

| Operación | cripta-01, caché 25 | cripta-01, caché 5 | Sintética, caché 25 | Sintética, caché 5 |
| --- | ---: | ---: | ---: | ---: |
| Acciones del jugador | 20 | 20 | 300 | 300 |
| Búsquedas en memoria (¿está esta ficha?) | 57 | 57 | 4 853 | 4 853 |
| Lecturas de una ficha (aciertos en memoria) | 16 (16) | 16 (6) | 389 (258) | 389 (195) |
| Inserciones en memoria | 11 | 21 | 191 | 254 |
| Fichas liberadas | 0 | 16 | 160 | 223 |
| Lecturas de disco | 0 | 10 | 131 | 194 |
| Solicitudes de red | 7 | 7 | 65 | 65 |

Tres cosas salen de esa tabla:

- **Se busca muchísimo más de lo que se inserta**: con la caché por defecto, 5 veces más en
  cripta-01 y 25 veces más en la cripta sintética. Lo que cueste buscar es lo que cuesta la caché.
- **Liberar memoria nunca cuesta red.** Con caché de 5 en cripta-01 se liberaron 16 fichas y
  se leyeron 10 del disco, y la partida siguió usando las mismas 7 solicitudes.
- Con caché de 25 en la cripta sintética, la caché llegó a tener 6 fichas más que el tope
  porque todas las candidatas estaban en uso. Eso se explica en la decisión.

### Alternativas consideradas

**Para buscar por id** comparamos cinco opciones (`benchmark/bench_tabla_hash.py`):

| Estructura | Búsqueda | Por qué no |
| --- | --- | --- |
| `dict` de Python | O(1) | §7 lo prohíbe como caché o tabla de búsqueda; está medido solo como referencia |
| Búsqueda lineal en una `list` | O(n) | con 10 000 claves es más de 400 veces más lenta que la tabla |
| `list` ordenada + búsqueda binaria | O(log n) | más lenta que la tabla desde 25 claves, y cada inserción desplaza elementos |
| Tabla hash propia con FNV-1a | O(1) | unas 5 veces más lenta que con crc32: calcula el hash en Python |
| **Tabla hash propia con crc32** | O(1) | decisión |

**Para decidir qué liberar** consideramos FIFO (libera la que entró primero, aunque se use
todo el tiempo), LFU (la menos usada en total, que necesita contadores y tarda en olvidar
fichas muy usadas al principio) y LRU (la usada hace más tiempo). Elegimos LRU porque el
jugador vuelve a salas cercanas y ve otra vez los mismos tipos. **No medimos FIFO ni LFU**:
la decisión entre políticas es razonada, no medida.

**Para llevar el orden de uso del LRU** comparamos una lista doblemente enlazada contra una
`list` de Python en la que la ficha usada se mueve al final (`benchmark/bench_cache_catalogo.py`).

**Para guardar en disco** comparamos tres formatos (`benchmark/bench_almacen_fichas.py`): un
solo JSON con todas las fichas, un archivo JSON por ficha, y nuestro almacén con un índice
binario ordenado.

**Para saber qué fichas están en uso** consideramos llevar un contador de referencias en cada
ficha, que habría que actualizar cada vez que un enemigo muere, un objeto se recoge o el
jugador cambia de sala. En cambio, la caché le pregunta al modelo qué está en uso solo
cuando necesita liberar, que es mucho menos frecuente (decisión D5).

### Decisión

**Memoria: `CacheCatalogo`** (`structures/cache_catalogo.py`). Una `TablaHash` de id a nodo
dice en O(1) promedio si la ficha está, y una lista doblemente enlazada con dos nodos
centinela lleva el orden de uso: la más reciente al frente y la usada hace más tiempo al
final. Mover un nodo al frente no recorre nada, porque cada nodo conoce a su anterior y a su
siguiente.

- **Al liberar**, la caché llama a `consultar_ids_en_uso`, que arma el controlador con
  `RepositorioCripta.ids_en_uso(...)`: enemigos vivos y lo que sueltan, inventario, y suelo y
  trampas de la sala actual. Recorre desde el final y salta las fichas en uso.
- **Tope flexible** (D9): si todas las candidatas están en uso, la caché excede el tope por
  un momento, lo registra, y en la siguiente inserción vuelve a intentar bajar.
- **La caché no entra en el retroceso** (§2.11): es infraestructura, no estado del juego.

**La tabla hash** (`structures/tabla_hash.py`) usa encadenamiento, capacidad en potencias de
2 y se duplica cuando pasa de 0,75 entradas por cubeta. La función hash es crc32
(`structures/funciones_hash.py`): es determinista entre ejecuciones, a diferencia de `hash()`
de Python, que cambia el resultado para los textos en cada ejecución. Es la misma tabla que
usa todo el proyecto en lugar de `dict`.

**Disco: `AlmacenFichas`** (`adapters/almacen_fichas.py`, decisión D6). Dos archivos:
`fichas.datos`, con las fichas una tras otra en JSON, y `fichas.indice`, binario con
`struct`: firma, versión del formato, versión del catálogo y una entrada por ficha
**ordenada por id** con su posición y su tamaño. Para leer una ficha, una búsqueda binaria en
el índice y luego se leen solo sus bytes. Al guardar, el índice se escribe en un temporal y se
reemplaza de una vez (`os.replace`), así un cierre a medio guardar nunca deja un índice que
apunte a datos incompletos. Si la versión del catálogo no coincide, todo se descarta.

**Esqueleto y contenido: `AlmacenCripta`** (`adapters/almacen_cripta.py`). Un archivo por sala
dentro de la carpeta de cada cripta, validados por la versión de la cripta. Con eso, una
segunda partida en la misma cripta no vuelve a pedir páginas ni contenido.

Si el disco falla, el juego sigue sin persistencia y el reporte final lo avisa (S8).

### Análisis de complejidad

Con n fichas en memoria, N fichas en disco y u fichas en uso que hay que saltar:

| Operación | Costo | Frecuencia medida |
| --- | --- | --- |
| ¿Está en memoria? (`contiene_ficha`) | O(1) promedio | la más frecuente: 57 en 20 acciones, 4 853 en 300 |
| Obtener de memoria y moverla al frente | O(1) promedio | 16 en 20 acciones, 389 en 300 |
| Insertar sin liberar | O(1) promedio | entre 11 y 254 inserciones por partida |
| Insertar liberando | O(u + 1) más lo que cueste `consultar_ids_en_uso` | entre 0 y 223 fichas liberadas por partida |
| Buscar en el índice del disco | O(log N) | 26 a 2 351 por partida |
| Leer una ficha del disco | O(log N) más leer sus bytes | 0 a 194 por partida |
| Guardar un lote de k fichas | O(k·N) por las inserciones ordenadas, más reescribir el índice O(N) | una vez por lote descargado |
| Abrir el almacén | O(N) | una vez por partida |

Lo que domina es la primera fila, y es O(1). Liberar es lo único que puede costar más, porque
pregunta qué está en uso. Con la caché por defecto no ocurrió nunca en cripta-01; en la cripta
sintética se liberaron 160 fichas en 191 inserciones, pero aun así se buscó 25 veces más de lo
que se insertó.

### Evidencia empírica

Mediana de 3 corridas en la computadora de Mauricio (Python 3.13.14 en Windows), 13 de
octubre. Cada benchmark calienta el procesador antes de medir. Detalle y rangos en
`docs/mediciones/bloque2/medianas_2026-10-13.md`.

**Buscar por id**, nanosegundos por búsqueda con acierto:

| Claves | TablaHash crc32 (decisión) | TablaHash FNV-1a | Lista ordenada + binaria | Lineal | `dict` (referencia) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 25 | 163 | 800 | 226 | 283 | 13 |
| 100 | 163 | 831 | 329 | 894 | 14 |
| 1 000 | 179 | 826 | 575 | 8 543 | 18 |
| 10 000 | 190 | 872 | 800 | 80 495 | 21 |

La tabla con crc32 es casi plana: con 400 veces más claves pasa de 163 a 190 ns. Le gana a
todas las alternativas permitidas en todos los tamaños, también con 25 claves, que es el tope
por defecto. Las búsquedas con fallo dan lo mismo (154 a 175 ns).

**Orden de uso del LRU**, caché llena, nanosegundos por operación:

| Capacidad | Obtener: lista doble (decisión) | Obtener: `list` | Insertar liberando: lista doble | Insertar liberando: `list` |
| ---: | ---: | ---: | ---: | ---: |
| 25 | 291 | 331 | 996 | 670 |
| 100 | 291 | 535 | 1 003 | 692 |
| 1 000 | 303 | 3 214 | 1 047 | 829 |
| 5 000 | 315 | 20 968 | 1 069 | 1 387 |

Obtener es plano con la lista doble; con la `list` crece con la cantidad de fichas y con 5 000
es 67 veces más lento.

**Recuperar una ficha liberada**, microsegundos por lectura:

| Fichas | AlmacenFichas (decisión) | Un JSON por ficha | Un solo JSON |
| ---: | ---: | ---: | ---: |
| 25 | 31,5 | 44,4 | 58,3 |
| 100 | 31,6 | 44,8 | 116,3 |
| 1 000 | 32,0 | 45,5 | 778,2 |

El almacén no depende de la cantidad de fichas; un solo JSON es 24 veces más lento con 1 000.
Un archivo por ficha se acerca, pero con 1 000 fichas son 1 000 archivos. La búsqueda binaria
en el índice cuesta entre 0,29 y 0,60 µs, apenas el 1 o 2 % de la lectura: lo que cuesta es ir
al disco. Aun así, leer del disco es unas 12 700 veces más rápido que una solicitud de ~400 ms.

**Persistencia contra el API real** (14 de octubre, `docs/mediciones/bloque2/presupuesto_api_real_2026-10-14.md`):

| | Arranque en frío | Segunda partida, misma caché en disco |
| --- | ---: | ---: |
| Solicitudes realizadas | 7 de 9 | 3 de 9 |
| Fichas descargadas | 11 (2 lotes) | 0 |
| Salas descargadas | 6 (1 lote) | 0 (6 leídas del disco) |
| Fallos de caché | 2 | 0 |

En la segunda partida solo se piden la lista de criptas, los datos generales (que traen la
versión de la cripta) y la versión del catálogo. Todo lo demás sale del disco, validado por
versión.

### Límites conocidos

- **`dict` sería 9 a 12 veces más rápido** que nuestra tabla. Es el costo de cumplir §7.
- **Insertar liberando es más lento con la lista doble que con una `list`** hasta unas 1 000
  fichas, porque la `list` desplaza sus elementos en C. Lo aceptamos porque buscar es entre 5 y
  25 veces más frecuente que insertar.
- **Preguntar qué está en uso puede salir caro.** Hoy cuenta todos los enemigos cargados que
  siguen vivos, también los dormidos de salas que el jugador no visitó. En una cripta muy grande
  esa lista crece, y por eso la caché de 25 llegó a pasarse en 6 fichas en la cripta sintética.
- **No medimos FIFO ni LFU.** Las mediciones comparan las estructuras, no las políticas.
- **La tabla hash no se encoge** al eliminar, y el índice de disco se carga completo en memoria.
  Para el tamaño del catálogo de este juego no importa.
- **`fichas.datos` acumula bytes sin uso** si una ficha se vuelve a guardar. Se reinicia cuando
  cambia la versión del catálogo.
- **Los tiempos son de una sola computadora** (Windows, Python 3.13). Los conteos de frecuencia y
  de solicitudes no dependen del equipo.

### Pruebas

`tests/test_tabla_hash.py` (50 pruebas) cubre inserción, reemplazo, eliminación,
redimensionamiento, claves con tildes, 10 000 claves y las dos funciones hash contra valores
de referencia. `tests/test_cache_catalogo.py` (17) cubre el orden LRU, las fichas en uso y
el tope flexible. `tests/test_almacen_fichas.py` (19) cubre el formato, la búsqueda binaria, el
cambio de versión, los archivos dañados y el reemplazo atómico. `tests/test_almacen_cripta.py`
(9) cubre el esqueleto y el contenido por versión. `tests/test_repositorio_cripta.py` (26)
verifica de punta a punta 7 solicitudes en frío y 3 en caliente.


## 4.5 Inventario

Estado: implementado, probado, medido e integrado al motor.

### Problema

El inventario es una colección de objetos con un orden real, el orden en que el jugador los tiene, y un cursor que señala el objeto que se está viendo. El enunciado pide cinco cosas:

- recorrerlo hacia adelante y hacia atrás desde la posición actual;
- soltar el objeto que se está viendo sin que el costo dependa de su posición;
- que equipar mueva el objeto al frente del orden real;
- mostrar vistas ordenadas por peso, valor o nombre sin alterar ese orden;
- rechazar recoger cuando se llega a `inventario_max`.

Las operaciones que el programa ejecuta de verdad son estas:

| Operación | Cuándo ocurre |
| --- | --- |
| Avanzar o retroceder el cursor | comandos `sig` y `ant`, costo 0 |
| Recoger | comando `recoger`, costo 25 |
| Soltar el objeto actual | comando `soltar`, costo 25 |
| Equipar el objeto actual | comando `equipar`, costo 50 |
| Recorrer completo | cada `abrir`, porque el motor busca la llave recorriendo el inventario |
| Vista ordenada | comando `ver peso\|valor\|nombre` |

**Frecuencia medida: no aplica a un recorrido automático.** Todas son comandos del jugador, así que pasan a lo sumo una vez por decisión y nunca dentro del bucle de eventos. Lo que el recorrido sintético no puede medir es qué fracción de las decisiones son de inventario, porque eso depende de cómo juegue la persona. La única que el motor dispara sola es el recorrido completo al abrir una puerta. En `cripta-01`, `inventario_max` es 10, así que ese recorrido toca a lo sumo 10 nodos.

### Alternativas consideradas

| Estructura | Avanzar | Soltar el actual | Mover al frente | Memoria |
| --- | --- | --- | --- | --- |
| `list` de Python con un índice como cursor | O(1) | O(n − i), desplaza lo que viene detrás | O(i) | n |
| Lista simplemente enlazada con cursor | O(1) adelante, O(n) atrás | O(n), hay que encontrar el anterior | O(n) | n |
| **Lista doblemente enlazada con cursor** | **O(1)** en los dos sentidos | **O(1)** | **O(1)** | n más dos punteros por nodo |

La **`list` con índice** es la alternativa seria, y la medimos directamente. Quedó descartada por el requisito, no por velocidad. `pop(i)` desplaza todos los elementos que están detrás de `i`, así que su costo depende de la posición, que es justo lo que §4.5 prohíbe. Además, a los tamaños de `cripta-01` la `list` es más rápida (ver evidencia), y lo decimos sin adornos.

La **lista simplemente enlazada** se descartó sin medirla: retroceder el cursor obliga a recorrer desde el principio. Eso rompe el primer requisito por construcción.

### Decisión

Usamos una lista doblemente enlazada propia, `DoublyLinkedList` en `structures/inventory.py`, con dos nodos centinela, uno al principio y otro al final. Los centinelas eliminan los casos especiales de "es el primero" o "es el último": insertar y quitar siempre reenlazan dos vecinos que existen.

`Inventory` envuelve la lista y agrega el cursor, que es una referencia al nodo actual, no un índice. Con el nodo en la mano, soltar y mover al frente solo cambian punteros vecinos, sin importar dónde esté el nodo.

Otras decisiones de implementación:

- **El equipo vive en `Player`**, no en el inventario. `Player.equipped_weapon` y `Player.equipped_armor` ya existían y son los que usa el cálculo de ataque y defensa. El inventario solo los actualiza, para que no haya dos fuentes de verdad.
- **Equipar un arma con otra ya equipada** reemplaza la anterior, que queda en el inventario. Lo mismo con la armadura. Así nunca hay más de un arma y una armadura equipadas (§2.7).
- **Soltar un objeto equipado** lo desequipa.
- **Las vistas ordenadas** copian los objetos a una lista nueva y la ordenan con `structures/sorting.py`. El orden real no se toca.
- **El cursor queda sobre el objeto recogido.** El enunciado no define este caso. Lo elegimos para que `recoger` seguido de `equipar` o `usar` actúe sobre ese objeto sin un `sig` en medio. Un `recoger` rechazado no mueve el cursor.
- **Al soltar, el cursor pasa al siguiente**, o al anterior si se soltó el último.

### Análisis de complejidad

n es la cantidad de objetos, acotada por `inventario_max`.

| Operación | Costo |
| --- | --- |
| `next`, `previous` | O(1) |
| `pick_up` | O(1) |
| `drop_current` | O(1) en cualquier posición |
| `equip_current` | O(1) |
| Recorrer completo (búsqueda de llave) | O(n) |
| `sorted_view` | O(n) para copiar, más el costo del algoritmo de §4.9 |
| `consume_scroll` | O(n), porque busca el primer pergamino |
| Memoria | O(n) |

### Evidencia empírica

Esta es la sección que mide directamente la alternativa descartada, como pide §8.

**Soltar por posición.** Cada medición es la mejor de 200 muestras de un solo `remove` o `pop`. Mediana de tres corridas, en nanosegundos:

| n | Lista doble, inicio | medio | final | `list.pop(i)`, inicio | medio | final |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 201 | 208 | 201 | 84 | 83 | 81 |
| 100 | 221 | 218 | 222 | 94 | 89 | 83 |
| 1 000 | 337 | 284 | 316 | 267 | 216 | 113 |
| 10 000 | 800 | 813 | 773 | 1 924 | 1 169 | 382 |

Dos lecturas de esta tabla, y las dos importan.

**Primera: a la escala de `cripta-01`, la `list` es más rápida.** Con 10 objetos, `pop` cuesta unos 80 ns y la lista doble unos 200. La razón es que `list` está escrita en C y nuestra lista en Python. Si el único criterio fuera la velocidad en esta cripta, la `list` ganaría.

**Segunda: la `list` depende de la posición, y la lista doble no.** Con 10 000 objetos, `pop` al inicio cuesta 1 924 ns y al final 382: cinco veces más, solo por dónde estaba el objeto. La lista doble cuesta lo mismo en las tres posiciones, entre 773 y 813 ns. Eso es lo que exige §4.5. Entre 1 000 y 10 000 objetos, la lista doble también pasa a ser más rápida al soltar desde el inicio.

La lista doble también sube un poco con n (de 201 a 800 ns), aunque cada `remove` hace exactamente el mismo trabajo. Lo atribuimos a la memoria: con 10 000 nodos recién creados, el nodo que se toca ya no está en caché. No es un costo de la operación, y no depende de la posición.

**Otras operaciones**, con 50 objetos:

| Operación | Mediana |
| --- | ---: |
| Avanzar el cursor | 122 ns por paso |
| Vista ordenada (copia más ordenamiento) | 86.2 µs por vista |

La vista ordenada es la operación más cara del inventario. Aun así, son 86 µs para un comando que el jugador pide a mano, contra los 20 ms de §5.2.

### Límites conocidos

- **A tamaños pequeños, la decisión cuesta velocidad.** La pagamos a cambio de cumplir §4.5 y de que el costo no crezca si la cripta de la revisión trae un `inventario_max` mucho mayor (§9). Si el requisito no existiera, con `inventario_max` de 10 la `list` sería la opción razonable.
- **`consume_scroll` es O(n)** porque busca el primer pergamino. Con inventarios de decenas de objetos no importa. Con miles, convendría llevar los pergaminos en su propia lista.
- **Cada nodo ocupa más memoria** que una celda de `list`: tres referencias más un indicador. No es un problema a esta escala.
- **El cursor no es estado reversible.** Al deshacer un `soltar` vuelve al objeto restaurado. En los demás casos queda donde estaba. Ver §4.6.

### Pruebas

`tests/test_inventory.py`, 32 pruebas, todas pasan. Cubren:

- la lista doble en sí;
- inventario vacío, capacidad inválida y capacidad llena;
- recoger después de soltar estando lleno;
- recorrido en los dos sentidos y en los extremos;
- soltar al inicio, en medio, al final y el único objeto;
- soltar un objeto equipado;
- equipar, sustituir, arma y armadura a la vez, y objeto no equipable;
- las tres vistas, en los dos sentidos, con estabilidad y sin alterar el orden real;
- pergaminos ocupando espacio;
- que el cursor quede sobre lo recogido.

---

## 4.6 Pergaminos de retroceso e historial reversible

Estado: estructura implementada, probada y medida. La agenda y el reloj se revierten con el motor real. **Falta que el motor anote sus propios cambios y conecte `rewind()`**, y eso le corresponde a la Persona 1.

### Problema

Un pergamino devuelve el juego al instante inmediatamente anterior a la última acción del jugador. Revierte también todo lo que ocurrió después de esa acción y antes de la siguiente decisión: acciones enemigas, efectos, reloj, eventos programados o cancelados, rastro, vida, inventario, suelo, puertas y trampas (§2.11). Hay cuatro restricciones:

- se puede retroceder como máximo 5 acciones;
- no se pueden guardar copias completas del estado;
- los pergaminos quedan fuera de la reversión, en los dos sentidos;
- usar uno no consume tiempo.

Las operaciones que ocurren de verdad:

| Operación | Cuándo | Medido |
| --- | --- | --- |
| Abrir un intervalo | una vez por acción aceptada del jugador | 1.00 por decisión |
| Anotar un cambio | cada vez que algo cambia entre dos decisiones | 18.88 por decisión con 5 enemigos y 138.10 con 50 (cota inferior) |
| Deshacer | cuando el jugador usa un pergamino | depende del jugador; a lo sumo 5 seguidas |

La medición importante es la segunda fila. Anotar ocurre muchísimo más que deshacer, y crece con la cantidad de enemigos activos, igual que los eventos de la agenda. Con 50 errantes, el intervalo más largo tuvo 206 anotaciones. **Lo que tiene que ser barato es anotar, no deshacer.**

### Alternativas consideradas

| Estrategia | Anotar | Deshacer | Memoria | ¿La permite el enunciado? |
| --- | --- | --- | --- | --- |
| Copia completa del estado antes de cada acción | O(tamaño de la partida) | O(tamaño de la partida) | 5 copias de toda la partida | **No**, §2.11 la prohíbe |
| Volver a ejecutar desde el inicio con la misma semilla | O(1) | O(partida entera) | el log de comandos | No: no es "invertir los cambios" |
| **Registro de cambios inversos** | **O(1)** por cambio | O(cambios del intervalo) | proporcional a lo que cambió en 5 acciones | Sí |

La **copia completa** está prohibida explícitamente.

**Volver a ejecutar** es tentador, porque el replay ya existe, pero se descartó por tres razones. Su costo crece con la longitud de la partida, no con lo que cambió. Volvería a pedir contenido al API, que gasta presupuesto de red. Y §2.11 pide registrar "la información necesaria para invertir los cambios", no reconstruir.

Para el **almacenamiento de los intervalos** también hubo dos opciones: una `list` a la que se le quita el primero al pasar de 5, o un buffer circular. Elegimos el buffer circular de §4.8, que ya existía, para no tener dos implementaciones de lo mismo.

### Decisión

Usamos un registro de cambios inversos, `History` en `structures/history.py`.

Cada acción aceptada del jugador abre un intervalo con `begin_action()`, que guarda el valor del reloj en ese momento. Cada modificación del estado anota lo mínimo para deshacerse:

- **`AttributeChange`:** guarda el objeto, el nombre del atributo y su valor anterior. Funciona también con propiedades, así que `health` sigue recortándose en su setter al restaurarse.
- **`CallbackChange`:** guarda la operación que revierte el cambio, por ejemplo volver a insertar un evento en la agenda.

`undo()` saca el último intervalo, aplica sus anotaciones en orden inverso y devuelve el reloj con `GameState.rewind_clock_to()`. Mientras deshace, el historial ignora las anotaciones nuevas, así que las operaciones inversas pueden reutilizar métodos que normalmente anotan.

Los intervalos viven en un `CircularBuffer` de 5. Al abrir el sexto, el más antiguo se descarta solo.

**La agenda se anota sola.** La parte más difícil de revertir es la agenda de eventos, porque el motor la modifica decenas de veces por decisión. Hicimos `ReversibleEventQueue`, una subclase de `EventQueue`, siguiendo el mismo patrón que `CountingEventQueue`, y se la pasamos a `Game` por su parámetro `event_queue`. Cada operación anota su inversa:

| Operación | Inversa anotada |
| --- | --- |
| `push(e)` | marcar `e` como cancelado |
| sacar `e` del montículo | volver a insertarlo con su mismo `time` y `sequence` |
| `cancel(e)` | devolver `e.cancelled` a su valor anterior |

"Sacar del montículo" incluye los eventos cancelados que el montículo descarta por dentro, por eso se intercepta `_remove_root`. Un evento reinsertado conserva su `time` y su `sequence`, así que el montículo recupera exactamente el mismo orden. También se restaura `actor.scheduled_event`, del que depende cancelar en O(1).

**El reloj se restaura; el contador de secuencia no.** Así lo acordó el grupo en `DECISIONES.md`, y la prueba `test_sequence_counter_is_not_restored` lo verifica.

**Los pergaminos quedan fuera de la reversión.** Ni `Inventory` ni el motor anotan los movimientos de un pergamino de retroceso. `use_rewind_scroll()` primero deshace y después consume el pergamino, así que el consumo queda fuera del intervalo revertido.

**Qué no se revierte, a propósito:**
- la bitácora en pantalla, que es presentación;
- el generador aleatorio, acordado en `ARQUITECTURA.md`;
- el cursor del inventario, salvo al deshacer un `soltar`.

### Análisis de complejidad

c es la cantidad de cambios del intervalo.

| Operación | Costo |
| --- | --- |
| `begin_action` | O(1) |
| `record`, `assign` | O(1) |
| Operaciones de `ReversibleEventQueue` | lo mismo que `EventQueue` más O(1) por anotación |
| `undo` | O(c), más O(log n) por cada evento que vuelve a la agenda |
| Memoria | O(suma de c en las últimas 5 acciones), independiente de la longitud de la partida |

### Evidencia empírica

**Costo de anotar y deshacer.** Cinco acciones con c cambios cada una, anotadas y deshechas. Mediana por acción:

| Cambios por acción | Tiempo por acción |
| ---: | ---: |
| 1 | 3.22 µs |
| 10 | 6.56 µs |
| 100 | 36.9 µs |
| 1 000 | 412.5 µs |

De 100 a 1 000 cambios, el tiempo se multiplica por 11: es el crecimiento lineal que predice la teoría. El intervalo más grande que medimos en una partida tuvo 206 anotaciones, que queda entre las filas de 100 y 1 000. Por la tabla, anotar y deshacer esa acción cuesta del orden de 0.1 ms, muy lejos de los 20 ms de §5.2.

**Costo de la agenda reversible.** 300 eventos pendientes y 20 000 ciclos de sacar e insertar, con el mismo patrón de `scheduler_bench.py`:

| Agenda | Mediana |
| --- | ---: |
| `EventQueue` | 0.0842 s |
| `ReversibleEventQueue`, anotando cada cambio | 0.1243 s |

Anotar cuesta un 48 % más en la agenda. Es el precio de no copiar el estado.

Esa estimación se pudo reemplazar por una medición real cuando el motor quedó anotando sus propios cambios. El ciclo completo de §5.2 pasó de 0.3302 ms a 0.4403 ms con 50 enemigos, un 33 % más, y ese aumento incluye además la decisión del rastreador, que antes no existía. Sigue a sesenta veces del límite de 20 ms.

**Corrección con el motor real.** Las pruebas `TestReversibleQueueWithTheEngine` usan el `Game` real y verifican que después de deshacer queden idénticos el reloj, los eventos activos de la agenda con su `time` y `sequence`, y el `scheduled_event` de cada actor. Los casos son: un `wait()`, dos retrocesos seguidos, un cambio de velocidad y la cancelación por muerte.

**Prueba de que no se escapa nada.** `tests/verificar_retroceso.py` toma una foto de todo lo que §2.11 pide revertir, ejecuta una acción, usa el pergamino y compara. Contra el motor de la rama `mauricio-logica-juego`, que todavía no anota sus cambios, encontró que `wait()` deja `player_actions` en 1 después de deshacer, mientras que la agenda y el reloj sí vuelven bien. La foto solo existe dentro de las pruebas y nunca restaura nada.

### Límites conocidos

- **Un cambio sin anotar no lanza ninguna excepción: simplemente no se deshace.** Es el riesgo principal del diseño, y por eso existe el verificador. Cada acción y cada evento del motor necesitan su prueba de retroceso.
- **La memoria crece con lo que pasa en el intervalo, no con lo que el jugador hace.** Si una cripta tuviera cientos de enemigos activos, un intervalo largo (por ejemplo, un jugador lento) acumularía miles de anotaciones. Por la tabla de evidencia, 1 000 cambios cuestan 0.41 ms por acción, así que todavía hay margen amplio.
- **Inventario por encima del máximo.** Si el jugador suelta un objeto, después recoge un pergamino y retrocede hasta antes de soltar, el inventario puede quedar con un objeto más que `inventario_max`. Pasa porque el pergamino no se devuelve (§2.11) y el objeto soltado sí. El enunciado no define este caso; queda pendiente de decisión del grupo.
- **Si el vecino de un objeto soltado era un pergamino** que después salió sin anotarse, el objeto se reinserta junto al otro vecino, o al final si tampoco está. La prueba `test_neighbour_scroll_left_without_being_recorded` cubre este caso.
- **Cargar una partida guardada es un caso distinto.** Al cargar, `History.clear()` descarta el historial anterior. Restaurar el contador y el generador le corresponde al guardado de §4.10.

### Pruebas

`tests/test_history.py`, 35 pruebas, todas pasan. Están agrupadas en:

- historial básico: máximo 5, orden inverso, reloj sí, contador no, propiedades, listas y el ejemplo de §2.11 completo;
- agenda reversible por sí sola;
- agenda reversible con el motor real;
- inventario reversible;
- pergaminos: sin pergamino, sin historial, recoger o soltar un pergamino dentro del intervalo, dos seguidos y nunca más de 5.

`tests/test_verificar_retroceso.py`, 7 pruebas, verifica el propio verificador.

---

## 4.7 El rastro del jugador

Estado: implementado, probado, medido e integrado. El rastreador ya persigue al jugador con el motor real.

### Problema

Cada sala recuerda el último instante en que el jugador estuvo allí. Un rastreador mira solo las salas vecinas por salidas abiertas y se mueve hacia la de rastro más fresco, si ese rastro tiene menos de 400 unidades de antigüedad. Si hay empate, gana la sala de menor id (§2.9). El costo de cada decisión debe ser proporcional a las salidas de la sala, no al tamaño de la cripta ni al recorrido del jugador. Con varios rastreadores, el trabajo por ciclo no debe crecer más que linealmente con los enemigos que actúan (§4.7).

Las operaciones que ocurren de verdad:

| Operación | Cuándo | Medido |
| --- | --- | --- |
| Marcar la sala del jugador | al iniciar y en cada acción aceptada (Apéndice B) | 1.00 por decisión |
| Decidir hacia dónde va un rastreador | en cada turno de un rastreador | hasta 6.94 por decisión con 5 enemigos y 66.55 con 50, si todos fueran rastreadores |

Los rastreadores deciden muchísimo más seguido de lo que el jugador marca: con 50 enemigos, 66 veces más. **Lo que tiene que ser barato es consultar, no marcar.**

**Cuándo se marca.** Acordado con la Persona 1: la sala destino de un movimiento se marca con el reloj del instante en que se ejecuta la acción, no al terminar su costo. Lo dice §2.5 ("el jugador aparece en la sala destino al ejecutar la acción") y lo confirma el ejemplo de §2.13.

### Alternativas consideradas

**Dónde guardar el rastro:**

| Opción | Marcar | Consultar una sala | Por qué |
| --- | --- | --- | --- |
| Un campo `rastro` en `Room` | O(1) | O(1) | Habría que modificar `Room`, que es de otro integrante |
| Lista de las salas visitadas, en orden | O(1) | O(recorrido del jugador) | Viola §4.7: depende de la longitud del recorrido |
| **`TablaHash` de id de sala a instante** | **O(1) promedio** | **O(1) promedio** | Reutiliza la estructura de la Persona 2 y no toca `Room` |

**Cómo tratar los rastros viejos.** §4.7 pide decidirlo y justificarlo:

| Opción | Costo | Por qué se descartó o se eligió |
| --- | --- | --- |
| Eliminarlos activamente con un evento de expiración por marca | un evento más en la agenda por cada decisión del jugador | Más eventos por ciclo, más cambios que el retroceso tiene que revertir, y la consulta no se vuelve más barata |
| **Detectar la caducidad al consultar** | una resta: `reloj − rastro < 400` | Elegida |

### Decisión

Usamos `PlayerTrail` en `structures/trail.py`, sobre una `TablaHash`. Las salas que no tienen entrada nunca tuvieron rastro. Los rastros viejos se quedan en la tabla y simplemente se ignoran al consultarlos.

`freshest_exit(room, reloj)` recorre las salidas de la sala del rastreador. Ignora las que tienen la puerta cerrada y las que no tienen rastro fresco, y se queda con la de instante más alto. Si hay empate, gana el menor id de sala. Devuelve el `Exit`, que es lo que `Enemy.decide_action()` ya respondía con el errante, así que el motor no necesitó una interfaz nueva.

**El rastro es reversible.** Al marcar con un historial, anota el valor anterior, o que la sala no tenía entrada. El ejemplo de §2.11 menciona expresamente "el rastro correspondiente".

### Análisis de complejidad

| Operación | Costo |
| --- | --- |
| `mark` | O(1) promedio |
| `is_fresh`, `time_at` | O(1) promedio |
| `freshest_exit` | O(s), con s ≤ 4 salidas y una búsqueda O(1) promedio por salida |
| k rastreadores en un ciclo | O(k) |
| Memoria | O(salas visitadas), nunca más que las salas de la cripta |

Nada depende del tamaño de la cripta ni de la longitud del recorrido.

### Evidencia empírica

Cada rastreador en una sala con 1 a 4 salidas, con rastros al azar en sus vecinas. Mediana del tiempo por decisión:

| Rastreadores | Tiempo por decisión |
| ---: | ---: |
| 1 | 0.73 µs |
| 10 | 1.17 µs |
| 100 | 1.16 µs |
| 1 000 | 1.21 µs |

De 10 a 1 000 rastreadores, el costo de cada decisión se mantiene en 1.2 µs, así que el trabajo total crece linealmente con los rastreadores, como pide §4.7. El primer valor es menor porque a ese único rastreador le tocó una sala con 1 salida; los demás promedian entre 1 y 4.

**En contexto:** el escenario con más turnos de enemigos tuvo 66.55 por decisión del jugador. Si todos fueran rastreadores, decidir costaría unos 80 µs por ciclo, el 0.4 % de los 20 ms de §5.2.

No medimos la eliminación activa: por construcción, solo agregaría eventos a la agenda.

### Límites conocidos

- **La tabla no se encoge.** Conserva una entrada por cada sala que el jugador visitó alguna vez, aunque el rastro haya caducado. En una cripta de miles de salas recorrida entera serían miles de entradas: memoria O(salas), nunca más que el mapa.
- **El costo depende de la tabla hash.** El peor caso de la `TablaHash` es O(n) si todas las claves caen en la misma cubeta. Con su función crc32 y el redimensionamiento, no lo observamos.
- **Un rastreador sin rastro fresco espera**, que es lo que §2.8 manda cuando no hay ninguna opción disponible.

### Pruebas

`tests/test_trail.py`, 13 pruebas, todas pasan. Cubren:

- vigencia de 400, con el límite exacto en 399 y 400;
- rastro en el instante 0;
- sala sin visitar y sala sin salidas;
- el más fresco gana y el empate se resuelve por menor id;
- rastros caducados y puertas cerradas;
- marcar y deshacer, tanto al sobrescribir como en la primera visita.

---

## 4.8 Bitácora en pantalla

Estado: implementado, probado, medido e integrado. `Game` la usa por omisión.

### Problema

La interfaz muestra solo los últimos 20 mensajes. La memoria de la bitácora debe ser constante durante toda la partida, y agregar un mensaje no puede desplazar físicamente los 19 anteriores (§4.8).

Las operaciones que ocurren de verdad:

| Operación | Cuándo | Medido |
| --- | --- | --- |
| Agregar un mensaje | el motor escribe uno por acción y por evento visible | 3.38 por decisión con 5 enemigos y 3.71 con 50 |
| Recorrer los 20 | al armar `visible_state()`, una vez por decisión | 1 por decisión |

Algo que no esperábamos: los mensajes casi no crecen con los enemigos. De 5 a 50 errantes, los eventos se multiplican por 7.7, pero los mensajes solo por 1.1. La razón es que el motor no escribe ningún mensaje cuando un enemigo se mueve o espera, solo cuando ataca. Lo demás lo escribe por las acciones del jugador, las trampas, las puertas y los efectos.

### Alternativas consideradas

| Estructura | Agregar | Memoria | ¿Cumple §4.8? |
| --- | --- | --- | --- |
| `list` que crece sin límite | O(1) | crece con la partida | No: la memoria no es constante |
| `list` a la que se le quita el primero al pasar de 20 | O(20) por el `pop(0)` | constante | No: `pop(0)` desplaza los 19 restantes |
| `collections.deque(maxlen=20)` | O(1) | constante | Sustituiría la estructura evaluada por una de biblioteca |
| **Buffer circular propio** | **O(1)** | **constante** | **Sí** |

La primera era la provisional del motor. La segunda es la que medimos directamente. `deque` resolvería el problema, pero es justo la estructura que se está evaluando, hecha por la biblioteca.

### Decisión

Usamos `CircularBuffer` en `structures/circular_log.py`: un arreglo fijo de 20 posiciones, un índice al mensaje más antiguo y un contador. Al llenarse, el mensaje nuevo sobrescribe al más antiguo y el índice avanza una posición con aritmética modular. Nada se mueve.

`CircularLog` lo especializa para la bitácora: capacidad 20 y mensajes guardados como texto. Cumple el contrato que el motor ya pedía, `append()` y poder recorrerla, así que se conectó sin cambiar `Game`.

El mismo `CircularBuffer` guarda los 5 intervalos del historial de §4.6. Así hay una sola implementación del buffer circular en el proyecto.

### Análisis de complejidad

| Operación | Costo |
| --- | --- |
| `append` | O(1), sin desplazar nada |
| Recorrer | O(20) |
| Memoria | O(20), constante |

### Evidencia empírica

100 000 mensajes conservando los últimos 20. Mediana por mensaje:

| Estructura | Tiempo por mensaje |
| --- | ---: |
| Buffer circular | 172 ns |
| `list` + `pop(0)` (descartada) | 59 ns |

**Con 20 mensajes, la alternativa descartada es casi tres veces más rápida.** Igual que en §4.5, `list` está escrita en C y desplazar 19 punteros es baratísimo. La decisión no se sostiene por velocidad: se sostiene porque §4.8 prohíbe ese desplazamiento.

**El costo, en contexto:** con 3.71 mensajes por decisión, el buffer circular cuesta unos 0.6 µs por ciclo, y la alternativa, 0.2 µs. La diferencia es de 0.4 µs contra un presupuesto de 20 ms.

**Memoria constante, verificada:** la prueba `test_memory_stays_constant` agrega 10 000 mensajes y comprueba que el arreglo sigue teniendo 20 posiciones. La prueba `test_plugs_into_game` hace lo mismo con el `Game` real, con 30 esperas.

### Límites conocidos

- **La capacidad es fija.** Si el enunciado pidiera mostrar más mensajes, habría que crear el buffer con otra capacidad; no crece solo.
- **Recorrer cuesta O(20)** cada vez que se arma el estado visible. Si la capacidad fuera muy grande y la vista se redibujara muchas veces por decisión, habría que mostrar solo lo nuevo.
- **La bitácora no forma parte del estado reversible.** Después de un retroceso se siguen viendo los mensajes de lo que se deshizo. Es una decisión, no un descuido: es presentación.

### Pruebas

`tests/test_circular_log.py`, 12 pruebas, todas pasan. Cubren:

- capacidad inválida y buffer vacío;
- llenado exacto;
- sobrescritura del más antiguo;
- `pop_last` después de dar la vuelta;
- memoria constante con 10 000 mensajes;
- capacidad por omisión de 20;
- menos de 20, exactamente 20 y más de 20 mensajes;
- conexión con el `Game` real.

---

## 4.9 Ordenamiento

Estado: implementado, probado y medido. Se usa en la activación de enemigos de §2.4 y en las vistas del inventario. **La selección automática tiene un defecto medido que hay que corregir antes de entregar** (ver límites).

### Problema

El programa necesita ordenar en varios contextos (§4.9):

| Contexto | Quién lo usa | Tamaño típico |
| --- | --- | --- |
| Activación de enemigos por id ascendente (§2.4) | motor, al entrar a una sala | los enemigos de una sala: unos pocos |
| Vistas del inventario | comando `ver` | hasta `inventario_max`, 10 en `cripta-01` |
| Tabla de puntajes | al terminar una partida | crece con las partidas jugadas |
| Índices del guardado y listas del catálogo | guardado (§4.10) y bloque 2 | decenas a cientos |

Las condiciones son cuatro: dos algoritmos con características distintas, que el programa escoja automáticamente según propiedades medibles de los datos, que la decisión se sustente con mediciones propias considerando tamaños pequeños, datos casi ordenados y comparaciones costosas, y que no se use `sorted()` ni `list.sort()`.

**Frecuencia:** la activación de enemigos ocurre al entrar a una sala con enemigos dormidos, a lo sumo una vez por movimiento. Las vistas ocurren con cada `ver`. Ninguna está dentro del bucle de eventos. No contamos cuántas veces ordena el motor por partida, porque la integración en `_by_ascending_id()` se hizo en la rama de la Persona 1 y no en la que medimos.

### Alternativas consideradas

| Algoritmo | Mejor caso | Peor caso | Memoria extra | Estable | Para qué sirve |
| --- | --- | --- | --- | --- | --- |
| **Inserción** | O(n), datos ordenados | O(n²) | O(1) | Sí | pocos elementos o casi ordenados |
| **Mezcla (merge sort)** | O(n log n) | O(n log n) | O(n) | Sí | cualquier dato, con costo predecible |
| Quicksort | O(n log n) | O(n²) | O(log n) | No | descartado |
| Selección | O(n²) | O(n²) | O(1) | No | descartado |

**Quicksort** se descartó por no ser estable. Una vista por valor con dos objetos de igual valor debe conservar su orden real, y la tabla de puntajes necesita un desempate predecible. Su peor caso además aparece justo con datos ya ordenados si se elige mal el pivote.

**Selección** se descartó porque no aprovecha que los datos estén casi ordenados: siempre hace n²/2 comparaciones.

Inserción y mezcla son complementarias: una es la mejor con datos pequeños o casi ordenados, la otra es la única segura con datos grandes y desordenados.

### Decisión

Usamos `structures/sorting.py`, con `insertion_sort`, `merge_sort` y `sort`, que escoge entre los dos.

**Cómo escoge `sort`.** Hace una pasada que cuenta los **descensos**: las posiciones donde un elemento va antes que su anterior. Cuesta n − 1 comparaciones. Después aplica dos reglas:

- con n ≤ `SMALL_THRESHOLD` (16) usa inserción;
- con descensos ≤ n × `NEARLY_SORTED_RATIO` (5 %) usa inserción;
- en cualquier otro caso usa mezcla.

**Comparaciones costosas.** La clave de cada elemento se calcula **una sola vez**: se arma una lista de pares (clave, elemento) y se ordenan los pares. Así una clave cara, como pasar un nombre a minúsculas, no se recalcula en cada comparación. Además, mezcla hace muchas menos comparaciones que inserción con datos desordenados, que es lo que importa cuando comparar es caro.

Las tres funciones son estables, aceptan `reverse` y no modifican la entrada.

### Análisis de complejidad

| Función | Tiempo | Memoria extra |
| --- | --- | --- |
| `insertion_sort` | O(n + inversiones): O(n) si está ordenado, O(n²) si está invertido | O(n) por los pares |
| `merge_sort` | O(n log n) siempre | O(n) por los pares y el auxiliar |
| `sort` | O(n) de la pasada, más el algoritmo escogido | la del algoritmo escogido |

### Evidencia empírica

Mediana de tres corridas. Cada valor es el mejor de tres repeticiones. Se omitió inserción con n = 4 096 en los patrones desordenados, por lenta. "Automático" es `sort` y aparece con el algoritmo que escogió.

**Datos aleatorios** (µs):

| n | Inserción | Mezcla | Automático (escogió) |
| ---: | ---: | ---: | ---: |
| 4 | 2.1 | 3.0 | 1.7 (inserción) |
| 8 | 3.6 | 6.3 | 4.1 (inserción) |
| 16 | 6.8 | 15.4 | 8.3 (inserción) |
| 32 | 27.8 | 33.8 | 38.3 (mezcla) |
| 64 | 134.8 | 79.6 | 87.2 (mezcla) |
| 256 | 1 837 | 416 | 451 (mezcla) |
| 1 024 | 33 680 | 2 483 | 2 519 (mezcla) |

Con datos al azar, inserción gana hasta 32 elementos y mezcla gana desde 64. El umbral de 16 es conservador: con n = 32 escogió mezcla y tardó 38.3 µs, cuando inserción habría tardado 27.8. **El cruce medido está entre 32 y 64, así que `SMALL_THRESHOLD` debería subir a 32.**

**Comparaciones costosas** (cadenas de 200 caracteres con prefijo común, µs):

| n | Inserción | Mezcla | Automático (escogió) | Comparaciones, inserción contra mezcla |
| ---: | ---: | ---: | ---: | --- |
| 16 | 12.5 | 16.3 | 12.0 (inserción) | 58 contra 45 |
| 32 | 29.5 | 37.7 | 40.2 (mezcla) | 199 contra 121 |
| 64 | 141.2 | 83.9 | 91.7 (mezcla) | 1 077 contra 302 |
| 1 024 | 36 460 | 2 395 | 2 579 (mezcla) | 259 395 contra 8 929 |

Con comparaciones caras, el cruce queda en el mismo lugar, entre 32 y 64. Calcular la clave una sola vez hace que una comparación de cadenas largas no cambie el cuadro.

**Datos casi ordenados** (1 % de intercambios al azar, µs):

| n | Inserción | Mezcla | Automático (escogió) |
| ---: | ---: | ---: | ---: |
| 16 | 4.2 | 13.7 | 5.8 (inserción) |
| 32 | 10.1 | 31.5 | 33.6 (mezcla) |
| 64 | 20.2 | 69.5 | 24.3 (inserción) |
| 256 | 74.8 | 339.9 | 98.3 (inserción) |
| 1 024 | 892 | 1 916 | 959 (inserción) |
| 4 096 | 13 760 | 9 505 | 14 300 (inserción) |

Aquí inserción saca la ventaja que promete: con 256 elementos es 4.5 veces más rápida que mezcla. La selección acierta en casi toda la tabla, con dos fallos:

- **n = 32:** había más del 5 % de descensos, así que escogió mezcla, que fue 3 veces más lenta.
- **n = 4 096:** el 1 % de intercambios entre posiciones lejanas desplaza elementos muy lejos. Hay pocos descensos, pero muchas inversiones, y ahí inserción ya pierde contra mezcla.

**Datos invertidos:** desde n = 32 escogió mezcla en todos los casos, que es lo correcto. Con 1 024 elementos, inserción tardó 62.2 ms y mezcla 1.8 ms.

**Datos rotados**, el caso que delata el defecto (µs):

| n | Inserción | Mezcla | Automático (escogió) |
| ---: | ---: | ---: | ---: |
| 64 | 117.9 | 63.4 | 123.5 (inserción) |
| 256 | 1 796 | 309 | 1 785 (inserción) |
| 1 024 | 32 470 | 1 748 | 32 290 (inserción) |
| 4 096 | — | 8 375 | **537 800 (inserción)** |

Una lista rotada, como `[5, 6, 7, 8, 9, 0, 1, 2, 3, 4]`, tiene **un solo descenso**, así que la regla la considera casi ordenada y escoge inserción. Pero la mitad de los elementos está a n/2 posiciones de su lugar, e inserción hace O(n²) trabajo. Con 4 096 elementos, `sort` tardó 0.54 s cuando mezcla habría tardado 8.4 ms: **64 veces más lento.**

### Límites conocidos

- **Los descensos no miden bien el desorden.** Fallan con datos rotados y con pocos elementos muy desplazados. En el juego real la exposición es baja: las vistas del inventario (10 objetos en `cripta-01`) y la activación de enemigos (los de una sala) quedan por debajo del umbral de 16, donde siempre se usa inserción y en todas las mediciones fue la más rápida. Pero la tabla de puntajes y los índices del guardado pueden crecer, y §9 avisa que la cripta de la revisión puede ser más grande.

  **Corrección propuesta, pendiente de implementar y medir:** contar descensos sigue siendo O(n), pero además se le pone a inserción un tope de n (por ejemplo, 1 024) por encima del cual siempre se usa mezcla. Otra opción es medir también el desplazamiento máximo en la misma pasada. Cualquiera de las dos tiene que validarse con el benchmark antes de entrar.
- **El umbral pequeño es conservador.** Las mediciones ponen el cruce entre 32 y 64 tanto con datos al azar como con comparaciones caras. Hay que subir `SMALL_THRESHOLD` a 32 y repetir la medición en la máquina del grupo.
- **La pasada de descensos no es gratis.** Cuando escoge mezcla, `sort` tardó entre un 1 % y un 13 % más que llamar a mezcla directamente. Es el costo de decidir.
- **Mezcla usa O(n) de memoria extra.** Con los tamaños del juego no es un problema.
- **La recursión de mezcla tiene profundidad log₂ n**: 12 niveles con 4 096 elementos. No se acerca al límite de recursión de Python.

### Pruebas

`tests/test_sorting.py`, 14 pruebas, todas pasan. Para los tres algoritmos cubren:

- lista vacía y de un elemento;
- casos básicos y repetidos;
- que no modifican la entrada;
- orden descendente;
- estabilidad, también en orden descendente;
- 1 000 datos al azar con resultados iguales entre algoritmos;
- claves de texto;
- el contador de comparaciones.

También cubren la regla de selección: pequeños, grandes desordenados, casi ordenados, invertidos y orden descendente.

---

---

## 4.10 — Guardado binario de la partida

**Pendiente, y sin responsable asignado.** La tabla de `ARQUITECTURA.md` pone la
persistencia del lado de la Persona 2, pero en la coordinación del 13 de octubre la
Persona 4 había propuesto encargarse de `save_file.py` y `json_save.py`. Hay que
decidirlo.

Del lado del motor ya está resuelto: `Game.load()` reconstruye una partida guardada sin
hacer el trabajo de inicio, y `GameState.restore()` y `EventQueue.active_events()`
entregan el estado temporal y la agenda. Lo que falta es el formato del archivo, el
acceso a una sala sin leerlo completo, la validación de versión y la comparación contra
JSON que pide §4.10.

---

## 4.11 Bitácora de partida y reproducción

Estado: implementado, probado y medido. Responsable principal: Persona 4.

### Problema

Cada partida tiene que dejar un archivo de texto al que solo se le agregan líneas,
con una por cada acción del jugador. La cabecera lleva por lo menos el id de la
cripta, su versión, la versión del catálogo y la semilla. Con `--replay partida.log`
el programa tiene que volver a jugar la partida entera sin preguntarle nada a nadie.
Si las versiones del log ya no están disponibles, tiene que decirlo y no reproducir.

El enunciado aclara que la reproducción es el mecanismo principal para reportar y
repetir errores durante la evaluación. O sea que no es un extra: si el replay falla,
el profesor no puede mostrarnos un error ni comprobar que lo arreglamos.

Las operaciones que ejecuta el programa, y cuántas veces:

| Operación | Cuándo ocurre | Medido |
| --- | --- | ---: |
| Anotar una línea | una vez por acción aceptada del jugador | 2 000 líneas en una partida de 2 000 acciones |
| Leer e interpretar el log | una vez por `--replay` | 2 000 líneas en 2.5 a 5.0 ms |
| Comprobar las versiones | una vez por `--replay`, antes de cargar nada | 1 |
| Volver a simular | una vez por línea del log | lo mismo que cuesta jugar la acción |

La operación frecuente es la primera, y además ocurre **dentro** del ciclo que §5.2
limita a 20 ms por decisión del jugador. Lo que cueste anotar se suma a cada acción.

Lo que de verdad condiciona el diseño es otra cosa: el log solo sirve si el modelo es
determinista. §2.6 garantiza que misma versión de cripta, misma semilla y mismas
acciones dan la misma partida. La bitácora se apoya por completo en esa garantía.

### Alternativas consideradas

**Qué se anota.** Miramos tres opciones.

| Opción | Qué guarda | Reproducir | Tamaño medido por acción |
| --- | --- | --- | ---: |
| Comandos aceptados | lo que escribió el jugador | vuelve a simular todo | 8.1 bytes |
| Eventos procesados | cada evento que sacó la agenda, con su resultado | lee los resultados | 41.8 líneas por cada línea de comandos |
| Foto del estado | actores, puertas, trampas y suelo después de cada acción | lee las fotos | 4 274 bytes, 530 veces más |

Las otras dos tienen una ventaja: no dependen de que el modelo sea determinista,
porque no vuelven a simular nada. Las descartamos por tres razones.

1. **No sirven para lo que pide la evaluación.** Un replay que solo lee resultados no
   ejecuta el código del motor. Si el error está en el motor, reproducir el log no lo
   repite, solo lo muestra. Con los comandos el motor vuelve a correr, el error vuelve
   a pasar, y después de arreglarlo se puede ver que ya no pasa.
2. **Crecen con lo que no controla el jugador.** Un log de eventos crece con la
   cantidad de enemigos y efectos; una foto, con el tamaño de la cripta. El de
   comandos depende solo de cuántas acciones hizo el jugador.
3. **La foto se parece demasiado a lo que §2.11 prohíbe** para el retroceso: guardar
   copias completas del estado. No es la misma regla, pero no queríamos defender esa
   cercanía.

**Cuándo se escribe al disco.** También tres opciones: dejar que el sistema junte
las escrituras sin forzarlas, hacer `flush` en cada línea, o hacer `flush` y además
`fsync` en cada línea. Sin `flush`, si el programa se cae, las últimas acciones se
pierden, y son justo las que llevaron al error que se quería reportar. Con `fsync`
la línea queda en el disco aunque se caiga el sistema operativo, pero cuesta mucho
más (ver la evidencia).

**Formato.** Texto plano con una acción por línea frente a JSON o binario. El binario
ahorraría poco, porque una acción ya ocupa 8 bytes. El texto se puede leer y editar a
mano, y eso importa para reportar un error: se puede recortar el log hasta la acción
que falla o anotar un comentario con `#`. Además cada línea se interpreta con el mismo
`parse_command()` que lee el teclado, así que no hay un segundo intérprete que pueda
diferir del primero.

**Qué pasa si las versiones no coinciden.** Reproducir igual mostrando un aviso, o
negarse. §4.11 prohíbe reproducir en silencio contra datos distintos, y un aviso que
nadie lee termina siendo lo mismo. Nos negamos.

### Decisión

Un log de comandos, en texto, con `flush` en cada línea:

```text
# CRIPTA replay
formato=1
cripta=cripta-01
version_cripta=fd58f7743b9e
version_catalogo=be68d322d2f5
semilla=5
---
mover N
esperar
```

- **Cabecera.** Lleva `formato` para detectar un log de otra versión del programa, y
  los cuatro datos que exige el enunciado. Las versiones salen de
  `RepositorioCripta.versiones_de_la_partida()`. La semilla la elige `main.py`, fuera
  del modelo, con `random.SystemRandom`, o la fija `--semilla`. El modelo solo usa su
  propio `random.Random(semilla)`.
- **Escritura** (`replay/replay_log.py`). `ReplayLogWriter` abre el archivo en modo
  `"x"`, para no pisar nunca un log que ya existe, y escribe cada línea con `flush`.
  Cada comando se escribe en su forma canónica (`Command.to_text()`), y
  `parse_command(c.to_text())` devuelve un comando igual a `c`. Los logs quedan en
  `partidas/<cripta>-<fecha>-<hora>.log`.
- **Quién anota.** `GameController` anota solo las acciones que el modelo **aceptó**.
  Teclado y replay pasan por el mismo `execute()`, así que el replay ejecuta
  exactamente el mismo código que la partida original.
- **Carga de salas.** Antes de `mover`, el controlador carga la sala destino con el
  repositorio, y después de cada acción aceptada pide la precarga. Como eso vive en el
  controlador, el replay carga las mismas salas en el mismo orden. Sin esto la
  reproducción se detenía en el primer `mover`.
- **Reproducción** (`replay/replay.py`, `controller/application.py`). `--replay` lee
  la cabecera y llama a `iniciar_partida(id, (version_cripta, version_catalogo))`. Si
  la fuente tiene otras versiones, `VersionesIncompatibles` se lanza **antes** de cargar
  nada y el programa muestra el mensaje y termina. Si coinciden, arma la partida con la
  semilla del log y ejecuta cada línea. No se crea la vista interactiva (§6): la salida
  es una función que se le pasa.
- **Divergencias.** Como el log solo tiene acciones aceptadas, si una de ellas se
  rechaza al reproducir, la partida ya no es la misma. `replay_commands()` se detiene
  con `ReplayDivergence` e indica la línea. Lo mismo hace si la partida termina y al
  log todavía le quedan acciones.

Qué se anota y qué no, como lo acordó el grupo (ARQUITECTURA, sección 6):

| Comando | ¿Se anota? | Por qué |
| --- | --- | --- |
| Mover, abrir, atacar, esperar, recoger, soltar, usar, equipar | Sí | Cambian el estado |
| `sig` y `ant` | Sí | `soltar`, `usar` y `equipar` actúan sobre el objeto del cursor; sin la navegación, el replay elegiría otro objeto |
| `retroceder` | Sí | §2.11 lo excluye del historial reversible, no de la bitácora. Si no se anotara, la partida reproducida sería otra |
| Una acción rechazada | No | No consume tiempo, no cambia el estado y no consulta el azar: omitirla no cambia nada |
| `ver` y las vistas ordenadas | No | No alteran el orden real ni el estado (§4.5) |
| `ayuda`, `guardar`, `cargar`, `salir` | No | Los atiende la aplicación, no el modelo |

### Análisis de complejidad

Con `L` acciones en el log:

| Operación | Costo | Comentario |
| --- | --- | --- |
| Anotar una acción | O(1) | Una línea corta y un `flush`. No depende de cuánto lleva la partida |
| Memoria del escritor | O(1) | No guarda las acciones: van directo al archivo |
| Comprobar versiones | O(1) | Dos comparaciones de texto, antes de cargar nada |
| Leer el log | O(L) | Una pasada por las líneas |
| Reproducir | O(L) ciclos del motor | Cuesta lo mismo que jugar la partida, porque es jugarla otra vez |

El costo de reproducir es el mismo que el de jugar, y eso es intencional: es lo que
hace que el replay pase por el mismo código. El tope de §5.2 por ciclo vale igual.

### Evidencia empírica

Medido con `benchmark/replay_bench.py`, que también corre dentro de `--bench`. Python
3.13.2 sobre Windows 11, en la máquina de la Persona 4. Las secciones anteriores se
midieron con Python 3.14.6 en otra máquina, así que los números no se comparan entre
secciones. Una corrida completa quedó en `docs/mediciones/replay/corrida_2026-10-17.txt`.
Los rangos salen de todas las corridas que hicimos: cuatro para la escritura sola y siete para la partida.

El escenario es la cripta sintética de `scheduler_bench`: 50 salas en línea con
trampas que se rearman, una puerta de cada tres con cierre automático y 30 enemigos
errantes. El jugador hace 2 000 acciones a través del controlador de verdad.

**Costo de anotar, solo la escritura**, 2 000 líneas, mejor de 5 repeticiones:

| Forma de escribir | Por línea |
| --- | ---: |
| Sin `flush` (descartada) | 0.57 a 0.79 µs |
| `flush` por línea (elegida) | 4.2 a 4.8 µs |
| `flush` y `fsync` por línea (descartada) | 683 a 1 655 µs |

**Lo mismo, dentro de una partida.** Sin bitácora, una acción con su ciclo de eventos
costó entre 237 y 332 µs. Con `flush` por línea, entre 256 y 355 µs. La diferencia
entre las dos queda dentro de la variación de una corrida a otra: hubo corridas en que
la versión sin `flush` fue más lenta que la elegida. Con `fsync`, en cambio, la acción
subió a entre 1 048 y 1 937 µs.

Leído en términos del tope de §5.2: el `flush` agrega unos 4.5 µs a cada acción, el
0.02 % de los 20 ms. El `fsync` agrega entre 0.7 y 1.7 ms, entre el 3 y el 8 % del
tope, y variable, porque depende del disco. Pagar eso en cada acción para protegerse
de una caída del sistema operativo no nos pareció razonable. Frente a una caída del
programa, que es lo que nos preocupa, el `flush` ya alcanza.

**Tamaño**, misma partida:

| Qué se anota | Medido |
| --- | --- |
| Comandos (elegido) | 16 117 bytes para 2 000 acciones: 8.1 bytes por acción |
| Eventos procesados (descartado) | 41.8 eventos por acción: 41.8 veces más líneas |
| Foto del estado (descartado) | 4 274 bytes por acción con 50 salas y 30 enemigos: 530 veces más |

Esas dos alternativas no están implementadas como bitácora. Se midió lo que tendrían
que anotar en la misma partida: los eventos con el contador `events_processed` del
motor, y la foto serializando a JSON los actores, puertas, trampas y suelo, igual que
lo haría esa bitácora.

**Reproducir.** Leer e interpretar las 2 000 líneas tomó entre 1.2 y 2.5 µs por
línea. Ejecutarlas tomó entre 0.23 y 0.34 ms por acción, lo mismo que jugarlas. En
todas las corridas la partida reproducida terminó en el mismo reloj, la misma sala y
la misma vida que la original.

**Contra la cripta real.** Con `cripta-01` sin conexión y semilla 5, una partida de
`mover N` y `esperar` termina en derrota en el instante 198. Reproducida con
`--replay` termina igual, con cero solicitudes de red. El mismo log con
`version_cripta` cambiada a mano se rechaza con el mensaje de versiones incompatibles,
sin reproducir ninguna acción.

### Límites conocidos

- **La fidelidad depende de que el modelo sea determinista.** Si alguien usa el
  generador global de `random`, la hora del sistema o el orden de llegada de una
  respuesta HTTP para decidir algo, el replay deja de ser fiel. `ReplayDivergence`
  solo detecta una acción rechazada o un final anticipado, no una diferencia más
  sutil, por ejemplo un daño distinto que no cambia ninguna decisión. Para detectar eso
  habría que anotar también un control del estado después de cada acción, por ejemplo
  el reloj, y compararlo al reproducir. No lo hicimos.
- **Una versión que ya no existe.** Si el API publica una versión nueva de la cripta y
  no hay copia local de la anterior, sus logs no se pueden reproducir. El programa lo
  informa (supuesto S18) y la salida es usar `--offline` con una copia de esos datos.
- **Partidas cargadas desde un guardado.** Un log empieza en la semilla y en el
  instante 0, así que no reproduce una partida que se cargó de un archivo a mitad de
  camino. Queda por decidir junto con el guardado de §4.10, que todavía no está
  integrado.
- **El nombre del jugador no va en la cabecera.** Hoy no afecta: ningún mensaje del
  motor lo usa y el replay no registra puntajes. Si algún mensaje empezara a usarlo, el
  texto reproducido cambiaría aunque la partida fuera la misma.
- **El `flush` no protege contra un corte del sistema operativo**, solo contra la
  caída del programa. Lo aceptamos por el costo medido del `fsync`.
- **Tamaño.** A 8 bytes por acción, un megabyte alcanza para unas 125 000 acciones. No
  esperamos que eso sea un problema.

### Pruebas

| Archivo | Qué cubre | Pruebas |
| --- | --- | ---: |
| `tests/test_replay_log.py` | Cabecera, formato, modo `"x"`, comentarios, errores con número de línea | 16 |
| `tests/test_replay.py` | Misma semilla y mismas acciones dan la misma partida; divergencias | 6 |
| `tests/test_commands.py` | `parse_command()` y la forma canónica que se escribe en el log | 20 |
| `tests/test_game_controller.py` | Se anotan solo las acciones aceptadas | 8 |
| `tests/test_controller_repository.py` | Carga de la sala antes de mover; partida en `cripta-01` grabada y reproducida con una caché nueva | 9 |
| `tests/test_application.py` | Flujo completo: jugar, grabar y reproducir; log con otra versión rechazado | 9 |

---

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

### Recoger deja el objeto seleccionado

El enunciado no define dónde queda el cursor después de recoger. §4.5 solo pide poder
recorrer el inventario "desde la posición actual", así que es una decisión de
implementación.

La primera versión dejaba el cursor donde estaba, de modo que recoger un arma y
equiparla necesitaba una navegación en el medio. Se cambió para que el objeto recogido
quede seleccionado: es lo que el jugador espera y evita un comando extra en cada
secuencia de la bitácora de reproducción. Si recoger se rechaza porque el inventario
está lleno, el cursor no se mueve.

El motor depende de ese comportamiento en `pick_up()` seguido de `equip_item()` o
`use_item()`, así que hay dos pruebas que lo fijan.

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

### El pergamino de retroceso

El motor no guarda copias del estado, que es lo que §2.11 prohíbe. Lo que hace es
anotar, por cada cambio, cómo deshacerlo. El historial reversible de la Persona 3 guarda
esas anotaciones agrupadas por intervalo, y un intervalo va desde una acción del jugador
hasta la siguiente.

**El motor abre el intervalo, no el historial.** `history.begin_action()` se llama en
cada acción **aceptada**, después de validarla y antes de tocar nada. Las rechazadas no
lo llaman, porque §4.6 solo guarda cinco acciones y una acción que no hizo nada no debe
gastar una de esas cinco. Por eso `use_item()` comprueba primero si el objeto tiene un
efecto que aplicar y recién después abre el intervalo.

**Todo cambio de estado pasa por el historial.** Son veintisiete lugares en `game.py`:
vida, sala, velocidad, resultado, contadores, puertas, trampas, antorcha, activación de
enemigos, efectos y objetos del suelo. En lugar de `actor.take_damage(x)` se escribe
`history.assign(actor, "health", actor.health - x)`, que cambia el valor y anota el
anterior. Funciona con las propiedades, así que el recorte de la vida sigue ocurriendo
en su setter.

La agenda y el inventario se revierten solos: `ReversibleEventQueue` anota sus propias
operaciones y `Inventory` las suyas.

**Cuando no hay historial no hay que preguntar.** `Game` recibe uno opcional y, si no se
lo dan, usa un objeto que aplica los cambios sin anotarlos. Así los veintisiete lugares
no llevan un `if` cada uno.

**El pergamino se consume después de deshacer, no antes.** Si se consumiera primero, ese
consumo quedaría dentro del intervalo que se está revirtiendo y el retroceso lo
devolvería, de modo que una sola unidad permitiría retroceder sin fin. Es la trampa que
el propio §2.11 advierte. Lo mismo vale para los pergaminos del suelo: recogerlos o
soltarlos no se anota.

**El retroceso funciona con la partida terminada**, y es la única acción que lo hace.
§2.11 no pone esa condición, el resultado se anota en el historial como cualquier otro
cambio, y un pergamino que no sirviera justo cuando al jugador lo matan no serviría para
nada. Es una interpretación declarada.

#### Cómo sabemos que no falta nada

Acá estaba el riesgo real: un cambio que el motor olvide anotar no lanza ninguna
excepción, simplemente no se deshace. Encontrarlo leyendo el código es poco confiable.

La Persona 3 escribió `tests/verificar_retroceso.py`, que toma una foto de todo lo que
§2.11 exige revertir, ejecuta una acción, usa el pergamino y compara, nombrando el campo
exacto que quedó distinto. La foto vive solo dentro de la prueba y nunca restaura nada,
de modo que no es la copia de estado que §2.11 prohíbe.

`tests/test_rewind.py` lo aplica a dieciséis situaciones: esperar, atacar, matar a un
enemigo que suelta objetos, moverse, pisar una trampa, abrir una puerta con cierre
automático, recoger, soltar, equipar, beber una poción de curación, beber una de
velocidad, encender una antorcha, usar un antídoto, el turno de un errante, el de un
rastreador y ganar la partida.

#### Verificado contra la cripta real

| | reloj | vida | sala | rata | trampa | pergaminos |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Inicio | 0 | 30/30 | 1 | 12/12 | armada | 2 |
| Entra a la sala 2 | 100 | 18/30 | 2 | 12/12 | desarmada | 2 |
| Ataca a la rata | 198 | 0/30 | 2 | 3/12 | desarmada | 2 |
| Usa un pergamino | 100 | 18/30 | 2 | 12/12 | desarmada | 1 |
| Usa el segundo | 0 | 30/30 | 1 | 12/12 | armada | 0 |

El jugador muere en el instante 198 y el primer pergamino lo devuelve vivo al 100, con
la vida de la rata restaurada. El segundo lo lleva al principio, con la trampa rearmada.
Los pergaminos no vuelven.

### Cargar una partida es un camino aparte del constructor

El constructor de `Game` hace trabajo de inicio de partida: marca el rastro de la sala
inicial, programa la primera acción del jugador en el instante 0, activa los enemigos de
esa sala y procesa eventos hasta la primera decisión (§2.4).

Al cargar una partida guardada nada de eso debe ocurrir, porque la agenda viene del
archivo, los enemigos ya tienen su estado y el reloj no está en cero. Si se usara el
constructor normal, la partida cargada quedaría mal **sin producir ningún error**: el
jugador tendría dos acciones programadas y los enemigos se reactivarían.

Por eso existe `Game.load()`, un constructor alternativo que recibe los mismos objetos
que el normal más lo que cambia durante la partida, y que no hace ese trabajo. Se
descartó una bandera en el constructor porque un parámetro que cambia lo que hace el
método es fácil de pasar mal, y acá pasarlo mal no da error.

`load()` también deja apuntando a cada actor su acción pendiente a partir de los eventos
cargados, que es un detalle que el código de guardado tendría que recordar.

**Los efectos activos no hace falta guardarlos.** Si no se pasan, `load()` los deduce de
la agenda: un veneno son sus pulsos pendientes, y un cambio de velocidad o una antorcha
son su evento de fin.

Esto salió de una prueba. Al reconstruir una partida sin pasar los efectos, el daño del
veneno seguía ocurriendo, porque viene de los eventos, pero la lista de efectos quedaba
vacía. La consecuencia habría aparecido mucho después: un antídoto no habría podido
cancelar un veneno cargado de un archivo, y la interfaz no habría mostrado nada, sin que
nada diera error. Deducirlos de la agenda elimina esa clase de fallo y le ahorra trabajo
al archivo.

El historial del retroceso no se carga, porque el de la sesión anterior ya no aplica.
Tampoco la bitácora de los 20 mensajes, que es presentación, ni `events_processed`, que
es una medición.

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

El escenario actual recorre una cripta de verdad, con el motor completo. El jugador
camina de punta a punta y vuelve, cada sala tiene una trampa que se rearma, una de cada
tres puertas está cerrada y se cierra sola después de abrirla, y la mitad de los
enemigos son errantes y la otra mitad rastreadores. Hay además un veneno y una antorcha
corriendo, todos los enemigos regeneran, y **el historial del retroceso está conectado**,
de modo que el motor anota cada cambio como en una partida real.

Que el escenario ejercita lo que dice está comprobado. En la corrida de la cripta
pequeña hubo 833 entradas a salas con sus 833 activaciones de trampa, 167 aperturas de
puerta y 167 cierres automáticos. Los rastreadores rastrean de verdad: en una corrida de
control los tres terminaron en la sala del jugador, habiendo arrancado repartidos por la
cripta. Y el historial anotó 199 cambios en sus cinco intervalos.

| | 6 salas, 6 enemigos | 40 salas, 50 enemigos |
| --- | ---: | ---: |
| Decisiones del jugador | 1 000 | 1 000 |
| Eventos por decisión | 13.1 | 90.5 |
| Tamaño máximo de la agenda | 21 | 109 |
| **Tiempo por ciclo** | **0.0596 ms** | **0.4403 ms** |
| Lo que permite §5.2 | 20 ms | 20 ms |

En el caso grande usamos el 2.2 % del presupuesto.

Dos cosas que vale leer de estos números. El costo crece con la cantidad de enemigos
activos y no con el tamaño de la cripta: lo que pesa es cuántos actores programan
eventos, no cuántas salas hay.

Y la segunda sale de comparar contra la medición anterior, cuando el motor todavía no
tenía rastreadores ni anotaba para el retroceso: el mismo escenario grande daba 0.3302 ms
por ciclo y ahora da 0.4403, un 33 % más caro. Ese es el precio de la decisión del
rastreador, que examina las salas vecinas y consulta el rastro, y de anotar cada cambio
de estado. Sigue a sesenta veces del límite.

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
| `tests/test_inventory_actions.py` | 34 |
| `tests/test_rewind.py` | 25 |
| `tests/test_save_load.py` | 20 |
| **Total del motor** | **270** |

Con las del bloque 2 integradas, el proyecto tiene 761 pruebas y todas pasan en
Python 3.14.6. Se corren con `python -m unittest discover -s tests -t . -v` desde
`cripta/`, con las dependencias de `requirements.txt` instaladas.

El motor se probó además contra los datos reales de `cripta-01`: se recorre la cripta
desde la sala inicial hasta la de salida, disparando la trampa de la sala 2, abriendo
con la llave negra la puerta de la salida y terminando en victoria con el reloj en 350
y cero solicitudes de red.

Las mediciones se corren con `python -m benchmark.scheduler_bench` desde la misma
carpeta.

---

## Pendientes antes de entregar

1. **Correr el benchmark en la máquina del grupo** y reemplazar las cifras de este documento:
   ```
   python -m benchmark.persona3_bench
   python -m benchmark.persona3_frecuencias
   ```
2. **Corregir la selección de §4.9** (umbral de 32 y tope para inserción), volver a medir y actualizar esa sección.
3. **Medir la frecuencia de las operaciones de inventario y ordenamiento en una partida real**, cuando el motor de la Persona 1 ya las use.
4. **Repetir la frecuencia del historial** cuando el motor anote sus cambios. La cifra de este documento es una cota inferior.
5. **Que el grupo decida** el caso del inventario por encima del máximo (§4.6).
