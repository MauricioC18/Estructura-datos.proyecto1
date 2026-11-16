# Constitución de CRIPTA

Estos principios gobiernan todo el proyecto. Los agentes los leen en cada fase del flujo de spec-kit. Si un plan o una tarea los contradice, el error es del grupo y se corrige antes de implementar, no después.

El proyecto es un juego de mazmorra por consola dirigido por eventos, escrito en Python 3.11 o superior, desarrollado por cuatro personas sobre el repositorio de la primera parte.

## Principios

### I. Las estructuras de datos se implementan a mano (NO NEGOCIABLE)

Toda estructura que resuelva un problema evaluado se escribe en este repositorio. No se sustituye por una implementación equivalente de una biblioteca.

Están prohibidos, para los problemas evaluados:

`dict` como índice, caché, tabla de búsqueda o estructura propia · `set` en las mismas condiciones · `heapq` · `bisect` · `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`) · `networkx` o cualquier biblioteca de grafos o de búsqueda de rutas · `sorted()` y `list.sort()` para el problema de ordenamiento · `pickle`

Se permiten: `list` como almacenamiento contiguo de bajo nivel, `struct`, `json`, `requests` y las bibliotecas de interfaz. Los diccionarios que devuelve `respuesta.json()` se pueden leer; lo que no se puede es usarlos como la estructura que resuelve el problema.

Ya existen en `cripta/structures/` estructuras propias de la primera parte: montículo binario mínimo, tabla hash, lista doblemente enlazada, buffer circular, grafo de salas y ordenamientos. **Reutilizarlas es preferible a escribir una nueva**, y hay que justificar cuando no se reutilizan.

Cuando un plan generado por un agente proponga una dependencia prohibida, se detiene en la fase de plan. Detectarlo al implementar ya es tarde.

### II. Determinismo

La misma cripta, la misma semilla y la misma secuencia de acciones producen exactamente la misma partida, incluidos los mensajes.

- El azar sale de una instancia propia de `random.Random(semilla)`. El generador global de `random` está prohibido.
- El orden de los eventos es total: primero por tiempo, y los empates por número de secuencia, que nunca se repite.
- Donde el enunciado fija un desempate, se respeta siempre, aunque el algoritmo elegido llegue al resultado por otro camino.
- Todo resultado que el enunciado describa como determinista debe serlo aunque existan varias respuestas válidas.

El determinismo es lo que hace posible `--replay`, y se verifica con pruebas que corren la misma partida dos veces y comparan.

### III. Separación Modelo-Vista-Controlador

El modelo no conoce HTTP, ni archivos, ni la interfaz concreta. El acceso a red y a disco vive detrás de adaptadores.

- `--replay` y `--bench` **no instancian la vista interactiva**. Si el modelo necesitara una ventana o entrada de teclado para funcionar, la separación no cumple.
- El modelo recibe sus colaboradores desde afuera (bitácora, historial, rastro, agenda) en vez de construirlos. Eso es lo que permite probarlo sin la API ni la vista.
- Para lo que cruza módulos se prefiere el duck typing a importar la clase del compañero.

### IV. Ningún dato de una cripta concreta en el código

No se escriben en el código identificadores de entidades, nombres de cripta, números de sala, cantidades de páginas, presupuestos ni estadísticas de una cripta específica. Todo eso se lee de los datos.

En la revisión se apunta a una cripta que el grupo no ha visto, que puede tener más salas, más actores y más efectos simultáneos. Un valor fijo que hoy funciona es un defecto que aparece ese día.

Los datos de ejemplo en `datos_offline/` son para desarrollar y probar; el código nunca depende de su contenido.

### V. El presupuesto de solicitudes se respeta

Cada cripta declara su `presupuesto_solicitudes` y ese valor es el máximo de solicitudes HTTP de la partida. No se calcula con una constante en el cliente.

- Toda solicitud cuenta, incluidas la lista de criptas, los datos generales, las páginas, el contenido, el catálogo, las verificaciones de versión, la ubicación de llaves y cualquier reintento después de un 429.
- Las lecturas desde disco o en modo `--offline` no cuentan.
- Al terminar la partida se reportan solicitudes realizadas, presupuesto, aciertos y fallos de caché.
- La meta no es gastar el presupuesto: una caché caliente debería usar menos.

### VI. Toda afirmación de rendimiento se respalda con una medición

No se escribe que algo es rápido, ni que una estructura es mejor que otra, sin un número obtenido con `--bench` en este proyecto.

- Cada problema evaluado mide también **la alternativa que se descartó**. Sin ese contraste, la decisión no está defendida.
- Se distingue siempre la complejidad teórica de la medición real.
- Las criptas sintéticas que genere `--bench` son deterministas por semilla.
- Concluir que una alternativa sencilla alcanza para cierta escala es válido **si las mediciones lo sustentan** y el programa sigue cumpliendo los requisitos cuando la cripta crece.
- Cuando una medición contradice lo que esperábamos, se reporta tal cual. Un número incómodo documentado vale más que uno favorable sin respaldo.

### VII. La especificación precede a la implementación (NO NEGOCIABLE)

Ninguna capacidad se implementa antes de que su especificación esté confirmada en el repositorio.

- El historial de Git debe mostrar el `spec.md` de cada capacidad commiteado **antes** que el código que la implementa.
- Si durante la implementación se descubre que la especificación estaba mal, **se corrige primero la especificación y luego el código, en confirmaciones separadas**. Una especificación desactualizada respecto del programa entregado se penaliza.
- Un programa que hace cosas que ninguna especificación describe es un defecto del mismo tipo que una especificación que no describe lo que el programa hace.

## Qué va en cada artefacto

| Artefacto | Contiene | No contiene |
| --- | --- | --- |
| `spec.md` | Reglas del juego, historias de usuario, escenarios de aceptación, requisitos funcionales y de rendimiento numerados | Nombres de estructuras de datos, clases o módulos |
| `plan.md` | Estructuras elegidas, alternativas consideradas, complejidad esperada, módulos afectados, mediciones planificadas | Reglas nuevas que no estén en `spec.md` |
| `tasks.md` | Tareas pequeñas y verificables, con dependencias y referencia al requisito que atienden | Tareas sin requisito asociado |

El `plan.md` de cada capacidad es el borrador de la sección correspondiente del Documento de Decisiones. Las mediciones finales van en el Documento.

## Trazabilidad

- Cada requisito funcional tiene un identificador estable, por ejemplo `FR-012`.
- Cada caso del Apéndice B del enunciado aparece como escenario de aceptación en alguna especificación.
- Cada escenario de aceptación tiene al menos una prueba automatizada, o una bitácora de reproducción que lo ejercita, y la prueba cita el identificador del requisito.
- Cada tarea referencia los requisitos que atiende.

En la defensa se escoge un requisito al azar y hay que mostrar su escenario, su tarea, su código y su prueba. La trazabilidad no es documentación de adorno: es lo que se va a pedir.

## Cómo se trabaja

- **Comentarios solo cuando son necesarios.** El código se explica por sus nombres y su estructura; las explicaciones largas van en los docstrings de módulo y en el Documento de Decisiones.
- **Las pruebas acompañan al código**, no se dejan para después. El proyecto tiene 861 pruebas de la primera parte y todas deben seguir pasando.
- **Cada integrante debe poder explicar cualquier decisión**, no solo la de la capacidad que implementó.
- **Cada invocación de un comando de spec-kit con texto propio es un prompt a un modelo de lenguaje** y se registra en `cripta/PROMPTS_LLM.md`, con fecha, herramienta, el texto enviado y para qué se usó la respuesta.
- Si algo del enunciado es ambiguo, se resuelve con `/speckit.clarify` y la respuesta queda escrita en la especificación, no en la cabeza de quien la escribió.

## Gobernanza

Esta constitución está por encima de cualquier preferencia de estilo o de comodidad de implementación. Vale igual para el código escrito a mano y para el generado por un agente: lo entregado es responsabilidad del grupo.

Una enmienda requiere acuerdo del grupo, queda registrada en este archivo y sube el número de versión. Si una enmienda invalida trabajo ya hecho, se documenta el antes y el después en el Documento de Decisiones.

spec-kit y el agente de programación son herramientas de proceso. No pueden introducir dependencias prohibidas en el código entregado ni sustituir el criterio del grupo.

**Version**: 1.0.0 | **Ratified**: 2026-11-16 | **Last Amended**: 2026-11-16
