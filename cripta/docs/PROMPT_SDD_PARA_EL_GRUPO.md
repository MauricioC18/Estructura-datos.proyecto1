# Prompt para arrancar con spec-kit

Cada integrante copia el **bloque común** y le pega debajo **su bloque personal**. Eso se le manda a la IA como primer mensaje.

Antes de usarlo hay que haber hecho `git pull`, porque la constitución y los comandos de spec-kit los sube una sola persona.

---

## Bloque común (lo copian los cuatro)

```text
Estoy en la segunda parte de un proyecto universitario de Estructuras de Datos II, en equipo de cuatro. Se continúa sobre el repositorio de la primera parte, que ya está terminado y entregado.

QUÉ ES EL PROYECTO
"CRIPTA" es un juego de mazmorra por consola dirigido por eventos: no hay turnos, hay un reloj virtual entero y una agenda de eventos. Se conecta a un API con un presupuesto limitado de solicitudes, tiene caché persistente, guardado binario de formato propio, bitácora de reproducción (--replay), tabla de puntajes y banco de mediciones (--bench). Arquitectura MVC. Python 3.11+. Hoy tiene 861 pruebas y todas pasan.

El enunciado completo de esta segunda parte está en el repositorio, en cripta/docs/SegundoProyecto-EDII-2026.md. Leelo entero antes de responder. El reparto del trabajo está en cripta/docs/REPARTO_PROYECTO2.md. El enunciado de la primera parte está en cripta/docs/proyecto_cripta.md y sus decisiones de diseño en cripta/docs/DECISIONES.md.

METODOLOGÍA OBLIGATORIA
El profesor exige desarrollo dirigido por especificaciones con GitHub spec-kit. El flujo por capacidad es:
/speckit.specify -> /speckit.clarify -> /speckit.plan -> /speckit.tasks -> /speckit.analyze -> /speckit.implement

Reglas que no se pueden romper:
1. La especificación se confirma en Git ANTES del código que la implementa. El historial se revisa y una especificación escrita después del código se penaliza.
2. Si durante la implementación resulta que la especificación estaba mal, se corrige primero la especificación y luego el código, en confirmaciones separadas.
3. spec.md lleva reglas del juego, historias de usuario, escenarios de aceptación y requisitos numerados con identificador estable (FR-001, FR-002...). NO lleva nombres de estructuras de datos, clases ni módulos.
4. plan.md lleva las estructuras elegidas, alternativas consideradas, complejidad esperada, módulos afectados y mediciones planificadas. NO lleva reglas nuevas que no estén en spec.md.
5. tasks.md lleva tareas pequeñas y verificables, cada una referenciando el requisito que atiende. No hay tareas sin requisito.
6. Cada caso del Apéndice B del enunciado que me corresponda debe aparecer como escenario de aceptación, y cada escenario necesita al menos una prueba automatizada que cite el identificador del requisito.

RESTRICCIONES DE IMPLEMENTACIÓN (las más importantes)
Las estructuras de datos de los problemas evaluados se implementan a mano. Están PROHIBIDOS: dict como índice o caché, set en las mismas condiciones, heapq, bisect, collections entero (deque, OrderedDict, defaultdict, Counter), networkx, cualquier librería de grafos o de rutas, sorted() y list.sort() para el problema de ordenamiento, y pickle.

Si en algún momento vas a proponer heapq, set o similares en el plan, detenete y decímelo: es un error que hay que atajar en la fase de plan, no al implementar. Sí se pueden reutilizar las estructuras propias que ya existen en cripta/structures/.

OTROS PRINCIPIOS QUE RIGEN TODO
- Determinismo: misma cripta, misma semilla y mismas acciones producen la misma partida. El azar sale de un random.Random(semilla) propio, nunca del generador global.
- Separación MVC: --replay y --bench no instancian la vista interactiva.
- Ningún dato de una cripta concreta escrito en el código: ni ids, ni números de sala, ni presupuestos.
- Toda afirmación de rendimiento se respalda con una medición de --bench.

CÓMO QUIERO QUE TRABAJEMOS
- Explicame la decisión antes de implementarla. Tengo que poder defender cualquier parte en una revisión oral, y en la defensa se escoge un requisito al azar y hay que mostrar su escenario, su tarea, su código y su prueba.
- Comentarios en el código solo cuando sean necesarios; las explicaciones van en el chat.
- Cada vez que use un comando de spec-kit con texto propio, hay que registrarlo en cripta/PROMPTS_LLM.md, porque el profesor lo exige.
- Vamos con el tiempo muy encima: la entrega es el miércoles 18 de noviembre.

Empezá leyendo el enunciado y el reparto, y decime qué entendiste que me toca a mí antes de escribir nada.
```

---

## Bloques personales

### Carlos Mauricio

```text
MI PARTE: terreno, cazador e invalidación de rutas. Secciones §3.1, §3.2, §5.1, §5.2 del enunciado.

En la primera parte me tocó el motor: la agenda de eventos, el reloj virtual, los actores, el combate, los enemigos y el guardado binario. Ya existe un montículo binario mínimo propio en structures/event_queue.py, probado y medido, que puede servir como cola de prioridad ya que heapq está prohibido.

Lo crítico: el desempate del cazador (entre vecinas de igual costo mínimo, la de menor id) y la equivalencia observable (la decisión debe ser idéntica a calcular desde cero en ese instante).

Me toca cubrir los siete casos del Apéndice B de "Terreno y cazador".
```

### Mauricio Arguedas

```text
MI PARTE: verificación de resolubilidad y los campos nuevos del servicio. Secciones §3.5, §4 y §5.4 del enunciado.

En la primera parte me tocó el API, las fuentes de datos, la precarga, el catálogo, la caché persistente y el traductor. Los tres datos nuevos son de mi capa: el campo costo en las salidas del esqueleto, el comportamiento cazador con su rango en el catálogo, y el nuevo GET /criptas/<id>/llaves.

URGENTE: los campos nuevos bloquean al resto del equipo. Nadie puede probar su parte hasta que el traductor los lea.

Lo crítico: el costo total de la verificación debe crecer aproximadamente lineal con salas, salidas y llaves; repetir el recorrido por cada llave no cumple. Y el reporte de una cripta no resoluble tiene que salir del mismo recorrido, incluyendo la detección del ciclo cuando una llave está detrás de la puerta que ella misma abre.

Me toca cubrir los cuatro casos del Apéndice B de "Resolubilidad".
```

### Erick

```text
MI PARTE: línea de tiempo y puntos de control. Secciones §3.6 y §5.5 del enunciado.

En la primera parte me tocó el inventario, el historial reversible con el pergamino de retroceso, el rastro del jugador, la bitácora de 20 mensajes y los ordenamientos. La línea de tiempo es la extensión de mi historial de cambios inversos.

Lo crítico: una consulta no puede aplicar ni deshacer cambios de más de K acciones del jugador, y al usar un pergamino la línea se recorta sin recorrer toda la historia. Hay que medir memoria y tiempo de consulta para al menos tres valores de K y justificar el valor por defecto.

Me toca cubrir los seis casos del Apéndice B de "Línea de tiempo".
```

### Steven

```text
MI PARTE: niebla de guerra, el comando "ir a", las banderas nuevas y la integración. Secciones §3.3, §3.4, §5.3, §7.2 y §7.3 del enunciado.

En la primera parte me tocó el MVC, la vista de consola, el controlador, la bitácora de reproducción, el ejecutor de --bench, la tabla de puntajes y la integración.

Además de mi capacidad me toca conectar las cuatro banderas nuevas de todo el equipo (--verificar, --forzar, --checkpoint-cada, --replay --hasta), integrar las mediciones nuevas a --bench y actualizar el README con la versión de spec-kit, el agente usado y los comandos nuevos.

Lo crítico: el mapa del jugador recuerda el estado de cada puerta según la última observación, aunque haya cambiado después. Y el conocimiento del jugador es estado del juego: se guarda, se revierte con el pergamino y entra en la línea de tiempo, así que hay que coordinarlo con Erick y con Carlos.

Me toca cubrir los seis casos del Apéndice B de "Niebla de guerra e ir a".
```
