# Registro de uso de herramientas de IA

Este archivo registra los prompts relacionados con el proyecto CRIPTA que se enviaron a un modelo de lenguaje, según lo exige la sección 10.3 del enunciado.

El código y el texto generados con ayuda de un modelo de lenguaje son responsabilidad del grupo. Cada integrante debe poder explicar y modificar lo entregado, independientemente de cómo se haya escrito.

Varios de los prompts de la sección 3 se dictaron por voz, de modo que aparecen con los errores de transcripción con los que llegaron. Se reproducen tal cual porque el enunciado pide el texto del prompt enviado.

Cuando un prompt consistió en pegar un documento completo, se describe el documento en lugar de copiarlo, para que este archivo siga siendo legible. Esos documentos están en el repositorio o disponibles si se solicitan.

---

## 1. Preparación y arquitectura

Herramienta: ChatGPT

Fecha: 2026-10-08

Objetivo: Organizar la estructura inicial del proyecto CRIPTA, definir las responsabilidades de los módulos y establecer una distribución inicial del trabajo.

Prompts utilizados:

- [Pegar aquí el prompt original utilizado.]

Uso en el proyecto: Se utilizó la respuesta como apoyo para preparar la estructura de carpetas y el documento inicial de arquitectura.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

## 2. Diseño de la agenda de eventos

Herramienta: ChatGPT

Fecha: [Fecha de la interacción]

Objetivo: Comprender y diseñar la agenda de eventos del motor del juego, comparando estructuras posibles antes de implementarla.

Prompts utilizados:

- [Pegar aquí el prompt original utilizado.]

Uso en el proyecto: [Describir cómo se aprovechó la respuesta.]

Cambios realizados por el estudiante: [Indicar las decisiones, modificaciones y pruebas realizadas.]

## 3. Implementación del motor (Persona 1)

Todas las entradas de esta sección corresponden a la misma herramienta: **Claude Opus, mediante Claude Code en VS Code**, con acceso a los archivos del repositorio.

### 3.1 Contexto del proyecto e implementación de la agenda de eventos

Fecha: 2026-10-08

Objetivo: Trasladar a una herramienta nueva el estado del proyecto, verificar qué había realmente en los archivos e implementar y probar la agenda de eventos.

Prompts utilizados:

- Documento titulado "PROMPT MAESTRO — PROYECTO CRIPTA", de unas 500 líneas, con el contexto académico, los requisitos del proyecto, la arquitectura acordada, la distribución del trabajo entre los cuatro integrantes, la metodología de trabajo exigida, las decisiones ya tomadas sobre el montículo binario mínimo, y el código propuesto para `model/event.py`, `structures/event_queue.py` y `tests/test_event_queue.py`. Terminaba indicando: "Tu primera acción debe ser confirmar el estado real de `model/event.py`, `structures/event_queue.py` y `tests/test_event_queue.py`, y continuar desde la agenda de eventos." Se adjuntó además el archivo `cripta/docs/proyecto_cripta.md` con el enunciado oficial.

Uso en el proyecto: La herramienta revisó los archivos del repositorio y confirmó que los seis archivos `.py` existentes estaban vacíos, que no existía la carpeta `tests/` ni `docs/DECISIONES.md`, y que por lo tanto nada de lo propuesto previamente estaba implementado ni probado. A partir de ahí se implementaron `model/event.py` y `structures/event_queue.py`, se creó `tests/test_event_queue.py` con 10 pruebas y se redactó la sección 4.1 de `docs/DECISIONES.md`.

Cambios realizados por el estudiante: [Indicar qué se revisó y qué se aceptó.] Se aceptaron tres correcciones al diseño previo, planteadas tras consultar el enunciado: los identificadores de instancia pasaron de entero a texto, porque el servicio los entrega en ese formato según §3.3; `is_empty()` pasó a descartar las raíces canceladas, porque antes podía informar que la agenda no estaba vacía cuando ya no quedaba ningún evento ejecutable; y se señaló que los ids de instancia en texto dejan ambiguo el orden de activación de §2.4.

### 3.2 Estilo de los comentarios en el código

Fecha: 2026-10-08

Objetivo: Corregir la forma en que la herramienta estaba documentando el código.

Prompts utilizados:

- "Ocupo que solo pongas comentarios necesarios no que expliques el codigo en comentarios dame las explicaciones en un chat aparte"

Uso en el proyecto: Se rechazó una primera versión de `structures/event_queue.py` cuyos comentarios explicaban el funcionamiento del algoritmo. Se reescribió el archivo sin esos comentarios y las explicaciones pasaron a la conversación. Este criterio se mantuvo en todos los archivos posteriores y quedó anotado como diferencia deliberada respecto del estilo de los ejemplos del curso, que sí llevan docstring en casi todos los métodos.

Cambios realizados por el estudiante: Decisión propia del estudiante, aplicada al resto del proyecto.

### 3.3 Reglas obligatorias de trabajo

Fecha: 2026-10-08

Objetivo: Fijar las reglas de estilo, estructuras de datos, arquitectura, pruebas y documentación que la herramienta debía respetar durante todo el proyecto.

Prompts utilizados:

- Documento titulado "REGLAS OBLIGATORIAS PARA LA IA — PROYECTO CRIPTA", con 72 reglas numeradas agrupadas en ocho apartados: idioma y nombres del código, estilo y calidad, estructuras de datos y restricciones, arquitectura, reglas de funcionamiento, pruebas y rendimiento, documentación y uso de IA, y forma de trabajar. Incluía la aclaración de que, si alguna regla contradecía el enunciado oficial, prevalecía el enunciado.
- En el mismo mensaje: "Explicame tu duda de otra forma: La incertidumbre que no puedo resolver solo: §2.4 dice que los enemigos activados en el mismo instante se programan 'en orden ascendente de su id de instancia', pero los ids son texto ('e-201')."
- También en el mismo mensaje, la respuesta del estudiante a una pregunta de comprensión sobre por qué no se puede modificar el tiempo de un evento que ya está en el montículo: "Cancelar el evento anterior y programar uno nuevo: marcamos el evento anterior como cancelado y creamos otro con el nuevo tiempo. Cuando el evento cancelado llegue a la raíz, la cola lo descarta y continúa con el siguiente válido."

Uso en el proyecto: Las reglas se aplicaron al resto del desarrollo. La aclaración sobre los identificadores llevó a revisar el enunciado y a concluir que §2 solo exige que el programa sea reproducible consigo mismo, no que coincida con el de otros grupos, de modo que la comparación lexicográfica del identificador completo es suficiente y además no depende del formato de ids de una cripta concreta, que §9 prohíbe asumir.

Cambios realizados por el estudiante: [Indicar qué reglas se ajustaron después de aplicarlas.]

### 3.4 Reloj virtual y contador de secuencia

Fecha: 2026-10-08

Objetivo: Decidir e implementar el reloj virtual, la numeración de eventos y su comportamiento ante el pergamino de retroceso.

Prompts utilizados:

- "Me gustaría que me explicaras el por qué para mí lo mejor es que con el pergamino se considera también el contador. Pero claro, esto implica tener un registro del contador en tal paso y eso se puede hacer con las sumas. Ya que se puede encontrar las acciones más o menos y tener un dato de cuál era el número del contador. Pero si esto incumple alguna regla o algo más que me está saltando del documento, me lo puedes indicar. Aparte de esto, dime qué opción elegirías tú cómo trabajarías con este reloj y con el pergamino o otros eventos que puedan alterarlo"
- "Entonces lo que va a hacer con el reloj es no modificarlo, simplemente ir contando la cantidad de eventos o la cantidad de acciones en un contador que siga linealmente"
- "Ok, perfecto. Y pregunta, ¿el rewind clock cómo se calcula? ¿Cómo es que el reloj va hacia atrás? Escribe todo este código ya simplemente contestando a esta pregunta."

Uso en el proyecto: De este intercambio salieron tres decisiones que están documentadas en `docs/DECISIONES.md`. Primera, que el contador de secuencia **no** necesita restaurarse al retroceder, porque ese número solo se usa para comparar eventos entre sí y los eventos restaurados son todos menores que el valor del contador en ese instante, de modo que el orden resultante es idéntico se restaure o no. Segunda, que el reloj **sí** debe restaurarse, porque su valor se usa en aritmética, en la comparación de antigüedad del rastro y en la tabla de puntajes. Tercera, que `rewind_clock_to()` no calcula el instante de destino sino que lo recibe del historial reversible, lo que impone un requisito a la Persona 3. Se implementó `model/game_state.py` con el reloj de solo lectura y 14 pruebas.

Cambios realizados por el estudiante: [Indicar qué se verificó y qué se aceptó.] En la segunda intervención el estudiante propuso no modificar el reloj y llevar solo un contador lineal; al contrastarlo contra §2.11 y §4.6 del enunciado se comprobó que el reloj sí debe restaurarse, y se separaron los dos conceptos.

### 3.5 Control de versiones

Fecha: 2026-10-08

Objetivo: Crear las ramas del repositorio y subir el trabajo.

Prompts utilizados:

- "Ok, ahora creo quiero que crees eh, dos ramas en el repositorio. La cual la primera sea la rama main y la segunda sea la rama Mauricio y que agregues una palabra que describa como lo que ibas haciendo. [...] Después de esto quisiera que subieses, o sea, que hicieses un push en la rama Mauricio y en la rama main con lo que he trabajado hoy. Eso sin darte algún tipo de como que subo parece que solo lo hice yo no te des ningún reconocimiento para que no salga que lo subiste tú ya que el profe nos pidió que fuese así ya que te estoy ya que tengo que apuntar los prompts que te di en prompts eh, LLM"
- "Ocupo que agregues ese archivo y suban los archivos para que ellos entiendan la, como dónde trabajar, ya que después puede haber más errores."

Uso en el proyecto: Se configuró la identidad del repositorio con el nombre y el correo institucional del estudiante, se creó la rama `mauricio-logica-juego`, y se hicieron los primeros commits. Los commits no llevan ninguna línea de atribución a la herramienta, por indicación del profesor de que el uso de IA se declara en este archivo y no en el historial de git. Se agregaron archivos `.gitkeep` a las carpetas vacías, porque git no versiona carpetas sin archivos y los demás integrantes no las verían al clonar.

Cambios realizados por el estudiante: Decisión propia sobre el nombre de la rama y la identidad de los commits.

### 3.6 Revisión de los ejemplos del curso

Fecha: 2026-10-12

Objetivo: Comparar el código del proyecto con los ejemplos publicados por el profesor, para seguir su estilo y detectar qué técnicas del curso no se pueden usar en el proyecto.

Prompts utilizados:

- Se adjuntó el archivo `estructuras-de-datos-main.zip`, con el repositorio de ejemplos del curso, junto con siete reglas: respetar el estilo del profesor; usar los ejemplos como base; no complicar el código innecesariamente; respetar los requisitos de CRIPTA aunque un ejemplo difiera; explicar las diferencias cuando haga falta una solución nueva; no afirmar que una técnica se vio en clase sin evidencia en los archivos; y mantener coherencia entre módulos.
- "Ok, ocupo que borres eso de decisiones y lo del estilo profesor me gustaría que lo tuvieses, pero como para revisarlo y que tuvieses un resumen de, de esto, para que no tengas que revisarlo cada vez, abrir el zip y así. [...] Y Ok, sí, por favor, haz eso de GTNOR para no subirlo a ningún momento al repositorio."

Uso en el proyecto: Se comprobó que el único montículo del curso es la función `heapify` dentro del `heapsort` de la semana 7, y que no existe ninguna cola de prioridad con inserción y cancelación, de modo que esa parte del proyecto no tiene precedente en clase. Se verificó que el estilo del proyecto ya coincidía con el del profesor en el uso de `@dataclass` para los nodos, los métodos auxiliares con guion bajo, el retorno de `None` en estructuras vacías y las propiedades con validación. Se identificaron tres técnicas que el profesor usa en sus ejemplos y que el enunciado prohíbe en el proyecto: `pickle` para el guardado binario, `dict` como índice y `sorted()`. El ZIP se agregó al `.gitignore` para no subir material ajeno al repositorio del grupo.

Cambios realizados por el estudiante: Decisión propia de no incorporar el análisis al Documento de Decisiones y de mantener el material del curso fuera del repositorio.

### 3.7 Plan de trabajo sin depender del resto del grupo

Fecha: 2026-10-13

Objetivo: Definir qué partes del motor se podían implementar y probar mientras los demás integrantes no entregaran sus módulos.

Prompts utilizados:

- "Me gustaría poder seguir avanzando con lo que yo puedo hacer y que de momento no dependa de los demás. [...] Entonces sigamos explícitamente con cosas que podamos probar entre comillas, que podamos avanzar en lo que las demás personas me pasen su parte o la suben al repositorio. Entonces sigamos. Con esas partes, dime cuál es Dame un plan primero"

Uso en el proyecto: Se produjo un plan por pasos. Se decidió no crear `model/room.py` y esperar a la Persona 2, y dejar el rastro del jugador como estructura de la Persona 3. Se identificó que atacar no requiere salas, porque §2.6 solo exige que atacante y objetivo compartan sala y `Actor` ya guarda el identificador de sala, y que por lo tanto el comportamiento guardián sí era implementable. Quedó por escrito qué partes quedaban bloqueadas y por qué.

Cambios realizados por el estudiante: Decisión propia de no definir `Room` ni el rastro, para no invadir el trabajo de los compañeros.

### 3.8 Cambios solicitados por la Persona 4

Fecha: 2026-10-14

Objetivo: Atender los pedidos que la Persona 4 planteó para poder implementar el controlador y la persistencia.

Prompts utilizados:

- Se adjuntaron dos capturas con el documento de la Persona 4, que pedía la interfaz de `Game`, la posibilidad de restaurar el contador de secuencia y el estado del generador aleatorio en `GameState`, un método para listar los eventos activos de `EventQueue`, campos adicionales en `Event` para serializar efectos, y señalaba una posible coma final en `rewind_clock_to`. Acompañadas de: "Que más deberia hacer? Antes de hacer un push ya que mis compañeros me estan pidiendo esto. Y ocupo subirlo para no atrasar a mis compañeros"
- "De momento pongamos como prioridad esto, que dijiste de la persona 4, eh, hagamos eso. Para que él pueda trabajar."

Uso en el proyecto: Se verificó en el repositorio que la coma final reportada no existía. Se agregaron `GameState.restore()`, `GameState.random_state()`, `EventQueue.active_events()` y los campos `amount`, `room_id`, `direction` e `instance_id` a `Event`. Se cambió `Event` para que guarde la referencia al objeto `Actor` en lugar de su identificador, porque buscarlo costaría O(n) por evento y §7 prohíbe usar `dict` como índice. Se dejó documentado en `docs/ARQUITECTURA.md` el contrato de `Game` con el controlador y la diferencia entre cargar una partida y retroceder, que en el grupo se estaba confundiendo.

Cambios realizados por el estudiante: [Indicar qué se comunicó a la Persona 4 y qué se acordó.]

### 3.9 Bucle del motor, actores y enemigos

Fecha: 2026-10-14

Objetivo: Implementar el motor que coordina reloj, agenda y actores, con las acciones de esperar y atacar.

Prompts utilizados:

- "Ok, está bien, pero a partir de ahora, por favor, trata de recomendarme o de darme opciones de con qué seguir trabajando para no perder el ritmo [...] y cosas por lo general que permitan que mis compañeros avancen en su trabajo, obviamente que solo involucren mi parte."
- Selección de la opción "El motor corriendo", entre tres opciones propuestas.

Uso en el proyecto: Se implementaron `model/actor.py`, `model/player.py`, `model/enemy.py` y `model/game.py`, con el bucle de eventos, el combate de §2.6, la activación de enemigos de §2.4 y el descarte de eventos de actores muertos. Se verificaron los tiempos contra el ejemplo de §2.13 del enunciado. Durante la escritura de las pruebas se detectó un error: un actor conservaba la referencia a un evento ya ejecutado, de modo que un cambio de velocidad en ese momento lo habría dejado con dos acciones pendientes sin producir ninguna excepción.

Cambios realizados por el estudiante: [Indicar qué se revisó del bucle y del combate.]

### 3.10 Efectos temporales y mediciones de rendimiento

Fecha: 2026-10-14

Objetivo: Implementar los efectos de §2.10 que no dependen de las salas y producir las mediciones que exige el enunciado.

Prompts utilizados:

- "Perfecto, continúa con la parte 1 y 2. Pero en la parte 3 podrías avanzar algo sin tocar lo de la parte de mi compañero. Si esta parte me toca a mí alguna, por más mínima que sea, me gustaría avanzarlo y o terminarlo lo máximo posible. [...] Dime qué puedes hacer y sin tocar ninguna parte de ninguno de mis compañeros. Después de esto, haz un push después de revisar y hacer test de todo. Explícame y pregúntame antes de hacer el push al final."

Uso en el proyecto: Se implementaron el veneno, la regeneración, el cambio de velocidad y la antorcha, más el antídoto. Se decidió que el veneno programe sus cinco activaciones de una vez, porque su duración e intervalo son constantes, lo que evita tener objetos de efecto con estado y vuelve trivial la cancelación. `Game` pasó a recibir la bitácora de mensajes desde fuera, de modo que la bitácora circular de la Persona 3 encaje sin modificar el motor. Se escribió `benchmark/scheduler_bench.py`, que mide el montículo contra una lista sin ordenar y el ciclo completo de eventos, y con esos números se completaron los dos apartados de evidencia empírica que estaban pendientes en `docs/DECISIONES.md`.

Cambios realizados por el estudiante: [Indicar qué se revisó de los efectos y de las mediciones.]

### 3.11 Redacción del Documento de Decisiones

Fecha: 2026-10-14

Objetivo: Reescribir `docs/DECISIONES.md` con una redacción más natural, y producir un documento de estudio personal.

Prompts utilizados:

- "Ocupo que okay, ahorita me concentrémonos en modificar el documento de decisiones. Me gustaría que lo hicieras como un poquito más lenguaje en el tema de común, pero a la vez que no sea predecible. ¿Me entiendes? Ya que la IA se detecta con que sea predecible. Entonces, que no sea así. Después de eso, me gustaría como que me dieras, aparte de esto, un documento que me explique esto de forma muy sencilla y paso a paso."
- "Ok, me gustaría que metieses eh, mi guía de estudio en el Git Ignore para que no se comité. Y no se suba al repositorio. Después de esto, eh, ocupo que revises prompts LLM y me ayudes a completar ese archivo."

Uso en el proyecto: Se reescribió `docs/DECISIONES.md` conservando íntegros el contenido técnico, las complejidades y todas las mediciones, y cambiando únicamente la redacción. Se produjo además una guía de estudio personal, que por decisión del estudiante no se sube al repositorio y está incluida en el `.gitignore`. Se completó esta sección del registro de prompts.

Cambios realizados por el estudiante: [Indicar qué partes del Documento de Decisiones se reescribieron con palabras propias.]

## 4. Revisión de interfaces existentes y contrato de la Persona 4

Herramienta: Claude (Claude Sonnet 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Revisar el contenido real de `docs/ARQUITECTURA.md`, `model/game_state.py`, `model/event.py` y `structures/event_queue.py` para detectar qué necesita la Persona 4 (MVC, interfaz, replay, benchmark e integración) de los módulos ya implementados.

Prompts utilizados:

- "listo, 2. game.py y actor.py no tienen nada en este momento, game state: [se pegó el código completo de `GameState`], event.py: [se pegó el código de `Event`], event_queue.py: [se pegó el código de `EventQueue`]" (acompañado del contenido completo de `docs/ARQUITECTURA.md`, en respuesta a la lista de archivos solicitada previamente).

Uso en el proyecto: Se utilizó la respuesta para identificar huecos que afectan a la Persona 4: la interfaz de `Game` aún no existe, `GameState` no permite restaurar el contador de secuencia ni el estado del generador aleatorio, `EventQueue` no permite listar los eventos activos, `Event` carece de los datos necesarios para serializar efectos, y la propiedad de `adapters/persistence.py` y de la tabla de puntajes no está asignada. También se utilizó para proponer un contrato `Game` ↔ controlador y un formato de log de replay.

Cambios realizados por el estudiante: [Indicar qué se verificó en el repositorio (por ejemplo, la coma final en `rewind_clock_to`), qué propuestas se aceptaron o descartaron y qué se acordó con el grupo.]

Nota posterior: la coma final reportada en `rewind_clock_to` se verificó contra el archivo del repositorio y no existe. Los otros cuatro pedidos se implementaron el 2026-10-14, según la entrada 3.8.

## 5. Resumen de puntos para la reunión del grupo

Herramienta: Claude (Claude Sonnet 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Condensar el análisis anterior en una lista de puntos concretos para discutir con el equipo.

Prompts utilizados:

- "Me puedes si resumir en puntos especificos para poder ir y ver con el equipo"

Uso en el proyecto: Se utilizó la respuesta como guía para la reunión del grupo: interfaz pendiente de `Game`, cambios solicitados a `GameState`, `EventQueue` y `Event`, reparto de archivos de persistencia, decisiones abiertas sobre el log de replay y formato de log propuesto.

Cambios realizados por el estudiante: [Indicar qué puntos se discutieron con el grupo y qué se decidió.]
