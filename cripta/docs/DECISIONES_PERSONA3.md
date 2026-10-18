# Documento de Decisiones: secciones 4.5 a 4.9 (Persona 3)

Estas son las secciones del inventario, el historial reversible, el rastro, la bitácora y el ordenamiento. Siguen el mismo formato que `DECISIONES.md` y están escritas para copiarse ahí tal cual cuando el grupo las revise.

Cada sección lleva los seis apartados de §8: problema con frecuencia medida, alternativas, decisión, complejidad, evidencia empírica y límites conocidos. También lleva sus pruebas.

## Dónde salen las cifras

Ninguna cifra es inventada.

- **Tiempos:** `python -m benchmark.persona3_bench`, corrido tres veces. Se reporta la mediana. Las tres corridas y las medianas están en `docs/mediciones/persona3/`.
- **Frecuencias:** `python -m benchmark.persona3_frecuencias`. Recorre con el motor real la misma cripta sintética de `benchmark/scheduler_bench.py`, sin modificar `Game`.
- **Entorno:** Python 3.13.16 sobre Linux x86_64, no en la máquina del grupo (Python 3.14.6 sobre Windows 11). Hay que repetir las mediciones ahí antes de entregar. Lo que importa son las proporciones y cómo crece cada columna; eso no debería cambiar, pero los valores absolutos sí.

| Escenario de frecuencia | 6 salas, 5 errantes | 40 salas, 50 errantes |
| --- | ---: | ---: |
| Decisiones del jugador | 1 000 | 1 000 |
| Eventos procesados | 8 940 | 68 549 |
| Turnos de enemigos | 6 940 (6.94 por decisión) | 66 550 (66.55 por decisión) |
| Mensajes escritos en la bitácora | 3 380 (3.38 por decisión) | 3 710 (3.71 por decisión) |
| Marcas de rastro | 1 001 (1.00 por decisión) | 1 001 (1.00 por decisión) |
| Anotaciones en el historial | 18 879 (18.88 por decisión) | 138 098 (138.10 por decisión) |
| Intervalo más grande, en anotaciones | 26 | 206 |

Las anotaciones del historial son una **cota inferior**. Solo cuentan lo que anotan solas la agenda reversible y el rastro: el motor todavía no anota sus cambios de vida, puertas y trampas.

---

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

Anotar cuesta un 48 % más en la agenda. Es el precio de no copiar el estado. El grupo midió 0.3302 ms por ciclo con 50 errantes; aun si ese ciclo completo costara un 48 % más, seguiría muy lejos del límite.

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
