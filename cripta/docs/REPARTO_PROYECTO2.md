# Reparto de la segunda parte

Enunciado: `docs/SegundoProyecto-EDII-2026.md`. **Entrega: miércoles 18 de noviembre.**

---

## Lo primero: el orden importa más que el reparto

El enunciado exige en §2.6 que **el historial de Git muestre la especificación de cada capacidad confirmada antes que el código que la implementa**. No es una recomendación: una especificación escrita después del código se penaliza, y en la defensa se escoge un requisito al azar y hay que recorrer su escenario, su tarea, su código y su prueba (§2.5).

O sea: nadie escribe código antes de confirmar su `spec.md`. Aunque sea una especificación corta.

El proceso spec-kit vale **20 %**, el rubro más pesado de los siete. Es también el más barato de conseguir, porque es Markdown y no algoritmos.

---

## El reparto

Se reparte siguiendo lo que cada quien ya domina de la primera parte. Con dos días, el tiempo de volver a aprender un módulo ajeno es tiempo que no hay.

| Integrante | Capacidad | Peso | Por qué le toca |
| --- | --- | ---: | --- |
| **Carlos Mauricio** | Terreno, cazador e invalidación de rutas (§3.1, §3.2, §5.1, §5.2) | 20 % | Dueño del motor, la agenda de eventos y los comportamientos de enemigo. El cazador necesita una cola de prioridad propia porque `heapq` está prohibido, y el montículo de `structures/event_queue.py` ya existe, está probado y medido |
| **Mauricio Arguedas** | Verificación de resolubilidad y campos nuevos del servicio (§3.5, §4, §5.4) | 15 % | Dueño del cliente del API, el esqueleto, el catálogo, el traductor y la caché. Los tres datos nuevos (`costo`, `cazador`/`rango`, `GET /llaves`) son todos de su capa, y la verificación se alimenta justo de esos datos |
| **Erick** | Línea de tiempo y puntos de control (§3.6, §5.5) | 15 % | Dueño del historial reversible y del pergamino. La línea de tiempo es la extensión directa de su registro de cambios inversos, e interactúa con el retroceso |
| **Steven** | Niebla de guerra, «ir a», banderas nuevas e integración (§3.3, §3.4, §5.3, §7.2, §7.3) | 10 % | Dueño del MVC, la vista, el controlador, el replay y el ejecutor de `--bench`. La niebla es sobre todo qué muestra la vista, `ir a` es un comando del controlador, y las cuatro banderas nuevas son suyas |

**Sobre el equilibrio.** En peso de rúbrica no es parejo: 20, 15, 15 y 10. Se compensa así:

- Steven carga, además de su 10 %, las cuatro banderas nuevas de **todos** (`--verificar`, `--forzar`, `--checkpoint-cada`, `--replay --hasta`), la integración de `--bench` y el README. Es el mismo rol que tuvo en la primera parte.
- Carlos carga el 20 % más la instalación de spec-kit y la constitución, que son del grupo.
- El 20 % del proceso se reparte igual entre los cuatro: **cada uno escribe su propia `spec.md`, `plan.md` y `tasks.md`**.

Si alguien considera que le quedó pesado, se discute hoy y se mueve. Mañana ya no.

---

## El orden de arranque, que es lo que desbloquea a todos

Hay dos cosas que bloquean al resto. Si no salen primero, los otros tres trabajan a ciegas.

**Bloque 0 — hoy, antes que nada (Carlos)**
1. Instalar spec-kit y correr `specify init --here`. **Lo hace una sola persona**, porque escribe en la raíz del repositorio; si lo corren los cuatro se pisan.
2. Escribir `.specify/memory/constitution.md` con los siete principios de §2.3.
3. Commitear y avisar. Recién entonces los demás hacen `git pull` y pueden usar los comandos.

**Bloque 1 — en cuanto exista la constitución (en paralelo)**
- **Mauricio Arguedas:** que el traductor lea `costo` en las salidas, `comportamiento: cazador` con `rango` en el catálogo, y el nuevo `GET /criptas/<id>/llaves`. **Sin esto nadie puede probar nada.** Es lo más urgente del proyecto después de la constitución.
- **Carlos:** que moverse cueste el costo de la salida en vez de 100 fijo (§3.1). Es un cambio chico en el motor y es la base del cazador y de «ir a».

**Bloque 2 — cuando lo anterior esté**
- Cada quien su capacidad, en paralelo, con el flujo completo de spec-kit.

---

## Qué le toca a cada uno, en concreto

### Carlos Mauricio — Terreno y cazador

Secciones: §3.1, §3.2, §5.1, §5.2, §6.3.

- El costo de moverse pasa a ser el costo de la salida: `intervalo = max(1, costo_salida * 100 // velocidad)`. Aplica a todos los actores.
- Comportamiento `cazador`: si comparte sala ataca; si no, calcula el costo mínimo *d* hasta el jugador por salidas abiertas; si no hay ruta o *d* > `rango`, espera con costo 100; si hay, da un paso por una ruta de costo *d*.
- **Desempate obligatorio:** entre las vecinas *v* con `costo(u,v) + dist(v, jugador) = d`, va a la de **menor id**.
- **Equivalencia observable:** la decisión debe ser idéntica a calcular desde cero en ese instante. Se puede reutilizar cálculo, pero jamás a costa de una decisión distinta.
- Mediciones en `--bench`: un cazador contra muchos, rango chico contra rango grande, cálculo compartido contra individual, y puertas estables contra puertas inestables, incluyendo la alternativa de recalcular siempre.
- Repetir la medición de la agenda de eventos de la primera parte con la carga nueva (§5.6).

Casos del Apéndice B que le toca cubrir: los **siete** de «Terreno y cazador».

### Mauricio Arguedas — Resolubilidad y datos nuevos

Secciones: §3.5, §4.1, §4.2, §4.3, §5.4.

- Campos nuevos por el traductor: `costo` en salidas (ausente equivale a 100), `cazador` con `rango` en el catálogo, y `GET /criptas/<id>/llaves`. Esa consulta **cuenta dentro del presupuesto de solicitudes**.
- Verificación antes de jugar: con los supuestos de §3.5, determinar si se puede obtener `llave_salida` y llegar a `sala_salida`.
- Si es resoluble: un orden de obtención de llaves, **determinista**.
- Si no: las llaves inalcanzables, las puertas de la frontera bloqueada con su llave, dónde está cada llave, y señalar el **ciclo** si una llave está detrás de la puerta que ella misma abre.
- **El costo total debe crecer aproximadamente lineal** con salas, salidas y llaves. Repetir el recorrido por cada llave no cumple.
- Medir contra esa alternativa ingenua, con criptas sintéticas de muchas llaves encadenadas.
- Las criptas de la segunda parte tienen versiones nuevas: lo persistido por la primera parte se invalida **por la validación de versión ya implementada**, no borrando archivos.

Casos del Apéndice B: los **cuatro** de «Resolubilidad».

### Erick — Línea de tiempo y puntos de control

Secciones: §3.6, §5.5.

- Consultar el estado en cualquier instante pasado, sin modificar la partida.
- `historia <t>` e `historia #k`. No consume tiempo virtual, no se registra en `partida.log`, no toca el historial de retroceso.
- Puntos de control: copias completas, **máximo una cada *K* acciones**, con `--checkpoint-cada K`. El valor por defecto lo escoge el grupo y se justifica con mediciones.
- Una consulta no puede aplicar ni deshacer cambios de más de *K* acciones.
- Al usar un pergamino, la línea se recorta **sin recorrer toda la historia**.
- Si se reconstruye hacia adelante re-simulando, el punto de control debe incluir el estado de `random.Random`.
- Medir memoria y tiempo de consulta para **al menos tres valores de K**, más la alternativa sin puntos de control.
- Repetir la medición del historial de retroceso de la primera parte con la carga nueva (§5.6).

Casos del Apéndice B: los **seis** de «Línea de tiempo».

### Steven — Niebla de guerra, «ir a» e integración

Secciones: §3.3, §3.4, §5.3, §7.2, §7.3.

- Tres estados por sala: explorada, avistada, desconocida.
- **Memoria de puertas:** el mapa recuerda el estado de cada puerta según la última observación, aunque haya cambiado después.
- La antorcha pasa a tener efecto: al entrar a una sala con ella encendida quedan exploradas las vecinas, sin activar sus enemigos ni sus trampas.
- El conocimiento del jugador **es estado del juego**: se guarda, se revierte con el pergamino y entra en la línea de tiempo. Hay que coordinarlo con Erick y con Carlos.
- `ir a <sala>`: solo a salas exploradas, por salidas que el mapa recuerda abiertas, recalculando antes de cada paso, con el mismo desempate del cazador. Se detiene al llegar, al entrar a una sala con enemigos, al recibir daño o si deja de existir ruta.
- Comandos y banderas nuevas: ver el mapa conocido, `ir a`, `historia`, `--verificar`, `--forzar`, `--checkpoint-cada`, `--replay --hasta`.
- La vista debe mostrar los costos de las salidas de la sala actual y distinguir a los cazadores.
- README: versión de spec-kit, agente usado, comandos nuevos y cómo correr las pruebas de aceptación.

Casos del Apéndice B: los **seis** de «Niebla de guerra e ir a».

---

## Lo que no puede faltar, sea quien sea

De §6.2, además de todo lo de la primera parte, quedan **prohibidos** para los problemas evaluados:

`heapq` · `bisect` · `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`) · `networkx` · cualquier librería de grafos o rutas · **`set`**, en las mismas condiciones que `dict`

Ojo con esto: **si el agente propone `heapq` o `set` en un `plan.md`, hay que detenerlo ahí**, no al implementar. El enunciado lo pregunta explícitamente en §8.

---

## Preguntas para el profesor, hoy

1. ¿Hay una versión concreta de spec-kit que quiera que fijemos? El enunciado pide `@vX.Y.Z` igual para todo el grupo pero no dice cuál.
2. La §6.1 remite a una «§2.7» para las enmiendas, pero **la §2.7 no existe** en el documento.
3. ¿Ya está publicada la cripta de referencia? §6.1 dice que los límites pueden ajustarse cuando se publique.
4. ¿El API ya devuelve los campos nuevos y el endpoint `GET /criptas/<id>/llaves`?
