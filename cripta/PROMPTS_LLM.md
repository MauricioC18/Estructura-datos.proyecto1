# Registro de uso de herramientas de IA

Este archivo registra los prompts relacionados con el proyecto CRIPTA que se enviaron a un modelo de lenguaje, según lo exige la sección 10.3 del enunciado.

El código y el texto generados con ayuda de un modelo de lenguaje son responsabilidad del grupo. Cada integrante debe poder explicar y modificar lo entregado, independientemente de cómo se haya escrito.

Varios de los prompts de la sección 3 se dictaron por voz, de modo que aparecen con los errores de transcripción con los que llegaron. Se reproducen tal cual porque el enunciado pide el texto del prompt enviado.

Cuando un prompt consistió en pegar un documento completo, se describe el documento en lugar de copiarlo, para que este archivo siga siendo legible. Esos documentos están en el repositorio o disponibles si se solicitan.

Del arranque del proyecto, el 2026-10-08, se conservan los cuatro prompts que aparecen en la sección 1. No se conserva el texto de otras consultas de esos primeros días, hechas con ChatGPT antes de que el registro se llevara de forma sistemática; se deja dicho acá en vez de reconstruirlas de memoria. A partir de la sección 2 el registro es completo.

---

## 1. Preparación, arquitectura y arranque del repositorio

Herramienta: ChatGPT

Fecha: 2026-10-08

Objetivo: Organizar la estructura inicial del proyecto CRIPTA, decidir qué archivos crear para que los cuatro integrantes pudieran empezar en paralelo, y redactar el documento inicial de arquitectura.

Prompts utilizados, en orden:

```text
Ocupo hacer un proyecto sobre programación en Python. Es sobre hacer un juego el cual tengo que conectar a una API y hacer ciertas cosas que me pide el profe específicamente en un documento. El documento ya casi te lo paso. Ocupo que me des la estructura y todas las instrucciones necesarias para que la IA me dé estructuradamente y siga correctamente las peticiones del archivo que te voy a pasar.
```

```text
Ya repartimos el trabajo. A mí me tocó la parte uno, pero ahora quiero como saltarme esta parte de la reunión. Me toca hacerlo a mí porque soy el que está como más dedicado al trabajo. Por más de que sea más trabajo para mí, prefiero hacerlo así para que se haya hecho. Me ayudaría saber qué pasos hacer para empezarlo y que todos tengamos una base mínima para poder empezar el trabajo ya, cada uno enfocándose en su parte.
```

```text
Entonces hago una trama base y una main y implemento esas carpetas y la división de cada uno, pero la cosa es eso. En la estructura que me mandaste veo muchos archivos. Hay archivos que yo de momento no tocaré, ya que la mayoría no son míos. ¿Qué debería tocar? ¿Qué archivos debería crear? ¿Debería crearlos y ponerles un, no sé, un comentario de esto es de tal persona o algo así? La cosa es que después ellos no worry, porque el profe puso que comentarios no a menos que sean necesarios. No sé qué me recomiendas y trata de explicarme un poquito más conciso lo que es, qué tengo que hacer y qué me recomiendas hacer.
```

```text
Ya creé las carpetas y los archivos que me dijiste, como actor.py, game_state.py, game.py, event_queue.py y los demás. El main también lo agregué. ¿Me podrías pasar el texto para meterlo en arquitectura.markdown y después de ahí seguir para ver qué código y cómo debería empezar a hacerlo?
```

Uso en el proyecto: Se utilizó la respuesta para armar la estructura de carpetas del repositorio, decidir qué archivos crear de entrada y redactar la primera versión de `docs/ARQUITECTURA.md`, que es el documento donde quedaron escritas las interfaces entre los módulos de los cuatro integrantes.

Cambios realizados por el estudiante: La decisión de fondo fue no esperar a una reunión para arrancar. En lugar de eso se dejó montada la estructura del repositorio con las carpetas de los cuatro módulos, para que cada integrante pudiera empezar por su parte sin depender de los demás; las carpetas que todavía no tenían código se conservaron en el repositorio con un archivo vacío, porque Git no guarda carpetas vacías. Se descartó la sugerencia de marcar cada archivo con un comentario indicando de quién era, porque el enunciado pide no poner comentarios salvo cuando sean necesarios; en su lugar el reparto quedó escrito una sola vez en la tabla de responsables de `docs/ARQUITECTURA.md`. También se decidió que las interfaces entre módulos se acordaran por escrito en ese documento antes de implementarlas, que es lo que después permitió que el motor se probara sin la API, sin la vista y sin las estructuras de los otros integrantes.

## 2. Implementación del motor (Persona 1)

Todas las entradas de esta sección corresponden a la misma herramienta: **Claude Opus, mediante Claude Code en VS Code**, con acceso a los archivos del repositorio.

### 2.1 Contexto del proyecto e implementación de la agenda de eventos

Herramienta: Claude

Fecha: 2026-10-08

Objetivo: Trasladar a una herramienta nueva el estado del proyecto, verificar qué había realmente en los archivos e implementar y probar la agenda de eventos.

Prompts utilizados:

- Documento titulado "PROMPT MAESTRO — PROYECTO CRIPTA", de unas 500 líneas, con el contexto académico, los requisitos del proyecto, la arquitectura acordada, la distribución del trabajo entre los cuatro integrantes, la metodología de trabajo exigida, las decisiones ya tomadas sobre el montículo binario mínimo, y el código propuesto para `model/event.py`, `structures/event_queue.py` y `tests/test_event_queue.py`. Terminaba indicando: "Tu primera acción debe ser confirmar el estado real de `model/event.py`, `structures/event_queue.py` y `tests/test_event_queue.py`, y continuar desde la agenda de eventos." Se adjuntó además el archivo `cripta/docs/proyecto_cripta.md` con el enunciado oficial.

Uso en el proyecto: La herramienta revisó los archivos del repositorio y confirmó que los seis archivos `.py` existentes estaban vacíos, que no existía la carpeta `tests/` ni `docs/DECISIONES.md`, y que por lo tanto nada de lo propuesto previamente estaba implementado ni probado. A partir de ahí se implementaron `model/event.py` y `structures/event_queue.py`, se creó `tests/test_event_queue.py` con 10 pruebas y se redactó la sección 4.1 de `docs/DECISIONES.md`.

Cambios realizados por el estudiante: Se aceptaron tres correcciones al diseño previo, planteadas tras consultar el enunciado: los identificadores de instancia pasaron de entero a texto, porque el servicio los entrega en ese formato según §3.3; `is_empty()` pasó a descartar las raíces canceladas, porque antes podía informar que la agenda no estaba vacía cuando ya no quedaba ningún evento ejecutable; y se señaló que los ids de instancia en texto dejan ambiguo el orden de activación de §2.4.

### 2.2 Estilo de los comentarios en el código

Herramienta: Claude

Fecha: 2026-10-08

Objetivo: Corregir la forma en que la herramienta estaba documentando el código.

Prompts utilizados:

- "Ocupo que solo pongas comentarios necesarios no que expliques el codigo en comentarios dame las explicaciones en un chat aparte"

Uso en el proyecto: Se rechazó una primera versión de `structures/event_queue.py` cuyos comentarios explicaban el funcionamiento del algoritmo. Se reescribió el archivo sin esos comentarios y las explicaciones pasaron a la conversación. Este criterio se mantuvo en todos los archivos posteriores y quedó anotado como diferencia deliberada respecto del estilo de los ejemplos del curso, que sí llevan docstring en casi todos los métodos.

Cambios realizados por el estudiante: Decisión propia del estudiante, aplicada al resto del proyecto.

### 2.3 Reglas obligatorias de trabajo

Herramienta: Claude

Fecha: 2026-10-08

Objetivo: Fijar las reglas de estilo, estructuras de datos, arquitectura, pruebas y documentación que la herramienta debía respetar durante todo el proyecto.

Prompts utilizados:

- Documento titulado "REGLAS OBLIGATORIAS PARA LA IA — PROYECTO CRIPTA", con 72 reglas numeradas agrupadas en ocho apartados: idioma y nombres del código, estilo y calidad, estructuras de datos y restricciones, arquitectura, reglas de funcionamiento, pruebas y rendimiento, documentación y uso de IA, y forma de trabajar. Incluía la aclaración de que, si alguna regla contradecía el enunciado oficial, prevalecía el enunciado.
- En el mismo mensaje: "Explicame tu duda de otra forma: La incertidumbre que no puedo resolver solo: §2.4 dice que los enemigos activados en el mismo instante se programan 'en orden ascendente de su id de instancia', pero los ids son texto ('e-201')."
- También en el mismo mensaje, la respuesta del estudiante a una pregunta de comprensión sobre por qué no se puede modificar el tiempo de un evento que ya está en el montículo: "Cancelar el evento anterior y programar uno nuevo: marcamos el evento anterior como cancelado y creamos otro con el nuevo tiempo. Cuando el evento cancelado llegue a la raíz, la cola lo descarta y continúa con el siguiente válido."

Uso en el proyecto: Las reglas se aplicaron al resto del desarrollo. La aclaración sobre los identificadores llevó a revisar el enunciado y a concluir que §2 solo exige que el programa sea reproducible consigo mismo, no que coincida con el de otros grupos, de modo que la comparación lexicográfica del identificador completo es suficiente y además no depende del formato de ids de una cripta concreta, que §9 prohíbe asumir.

Cambios realizados por el estudiante: Se fijaron las reglas antes de escribir codigo y se respondieron las dudas que la herramienta planteo sobre ellas. La decision de fondo que salio de ahi es que nunca se modifica el tiempo de un evento que ya esta en la agenda: se cancela y se vuelve a programar con un numero de secuencia nuevo, porque cambiarlo adentro romperia el invariante del monticulo sin lanzar ninguna excepcion. Las reglas se aplicaron despues a todo el modulo y no hubo que ajustarlas.

### 2.4 Reloj virtual y contador de secuencia

Herramienta: Claude

Fecha: 2026-10-08

Objetivo: Decidir e implementar el reloj virtual, la numeración de eventos y su comportamiento ante el pergamino de retroceso.

Prompts utilizados:

- "Me gustaría que me explicaras el por qué para mí lo mejor es que con el pergamino se considera también el contador. Pero claro, esto implica tener un registro del contador en tal paso y eso se puede hacer con las sumas. Ya que se puede encontrar las acciones más o menos y tener un dato de cuál era el número del contador. Pero si esto incumple alguna regla o algo más que me está saltando del documento, me lo puedes indicar. Aparte de esto, dime qué opción elegirías tú cómo trabajarías con este reloj y con el pergamino o otros eventos que puedan alterarlo"
- "Entonces lo que va a hacer con el reloj es no modificarlo, simplemente ir contando la cantidad de eventos o la cantidad de acciones en un contador que siga linealmente"
- "Ok, perfecto. Y pregunta, ¿el rewind clock cómo se calcula? ¿Cómo es que el reloj va hacia atrás? Escribe todo este código ya simplemente contestando a esta pregunta."

Uso en el proyecto: De este intercambio salieron tres decisiones que están documentadas en `docs/DECISIONES.md`. Primera, que el contador de secuencia **no** necesita restaurarse al retroceder, porque ese número solo se usa para comparar eventos entre sí y los eventos restaurados son todos menores que el valor del contador en ese instante, de modo que el orden resultante es idéntico se restaure o no. Segunda, que el reloj **sí** debe restaurarse, porque su valor se usa en aritmética, en la comparación de antigüedad del rastro y en la tabla de puntajes. Tercera, que `rewind_clock_to()` no calcula el instante de destino sino que lo recibe del historial reversible, lo que impone un requisito a la Persona 3. Se implementó `model/game_state.py` con el reloj de solo lectura y 14 pruebas.

Cambios realizados por el estudiante: En la segunda intervención el estudiante propuso no modificar el reloj y llevar solo un contador lineal; al contrastarlo contra §2.11 y §4.6 del enunciado se comprobó que el reloj sí debe restaurarse, y se separaron los dos conceptos.

### 2.5 Control de versiones

Herramienta: Claude

Fecha: 2026-10-08

Objetivo: Crear las ramas del repositorio y subir el trabajo.

Prompts utilizados:

- "Ok, ahora creo quiero que crees eh, dos ramas en el repositorio. La cual la primera sea la rama main y la segunda sea la rama Mauricio y que agregues una palabra que describa como lo que ibas haciendo. [...] Después de esto quisiera que subieses, o sea, que hicieses un push en la rama Mauricio y en la rama main con lo que he trabajado hoy. Eso sin darte algún tipo de como que subo parece que solo lo hice yo no te des ningún reconocimiento para que no salga que lo subiste tú ya que el profe nos pidió que fuese así ya que te estoy ya que tengo que apuntar los prompts que te di en prompts eh, LLM"
- "Ocupo que agregues ese archivo y suban los archivos para que ellos entiendan la, como dónde trabajar, ya que después puede haber más errores."

Uso en el proyecto: Se configuró la identidad del repositorio con el nombre y el correo institucional del estudiante, se creó la rama `mauricio-logica-juego`, y se hicieron los primeros commits. Los commits no llevan ninguna línea de atribución a la herramienta, por indicación del profesor de que el uso de IA se declara en este archivo y no en el historial de git. Se agregaron archivos `.gitkeep` a las carpetas vacías, porque git no versiona carpetas sin archivos y los demás integrantes no las verían al clonar.

Cambios realizados por el estudiante: Decisión propia sobre el nombre de la rama y la identidad de los commits.

### 2.6 Revisión de los ejemplos del curso

Herramienta: Claude

Fecha: 2026-10-12

Objetivo: Comparar el código del proyecto con los ejemplos publicados por el profesor, para seguir su estilo y detectar qué técnicas del curso no se pueden usar en el proyecto.

Prompts utilizados:

- Se adjuntó el archivo `estructuras-de-datos-main.zip`, con el repositorio de ejemplos del curso, junto con siete reglas: respetar el estilo del profesor; usar los ejemplos como base; no complicar el código innecesariamente; respetar los requisitos de CRIPTA aunque un ejemplo difiera; explicar las diferencias cuando haga falta una solución nueva; no afirmar que una técnica se vio en clase sin evidencia en los archivos; y mantener coherencia entre módulos.
- "Ok, ocupo que borres eso de decisiones y lo del estilo profesor me gustaría que lo tuvieses, pero como para revisarlo y que tuvieses un resumen de, de esto, para que no tengas que revisarlo cada vez, abrir el zip y así. [...] Y Ok, sí, por favor, haz eso de GTNOR para no subirlo a ningún momento al repositorio."

Uso en el proyecto: Se comprobó que el único montículo del curso es la función `heapify` dentro del `heapsort` de la semana 7, y que no existe ninguna cola de prioridad con inserción y cancelación, de modo que esa parte del proyecto no tiene precedente en clase. Se verificó que el estilo del proyecto ya coincidía con el del profesor en el uso de `@dataclass` para los nodos, los métodos auxiliares con guion bajo, el retorno de `None` en estructuras vacías y las propiedades con validación. Se identificaron tres técnicas que el profesor usa en sus ejemplos y que el enunciado prohíbe en el proyecto: `pickle` para el guardado binario, `dict` como índice y `sorted()`. El ZIP se agregó al `.gitignore` para no subir material ajeno al repositorio del grupo.

Cambios realizados por el estudiante: Decisión propia de no incorporar el análisis al Documento de Decisiones y de mantener el material del curso fuera del repositorio.

### 2.7 Plan de trabajo sin depender del resto del grupo

Herramienta: Claude

Fecha: 2026-10-13

Objetivo: Definir qué partes del motor se podían implementar y probar mientras los demás integrantes no entregaran sus módulos.

Prompts utilizados:

- "Me gustaría poder seguir avanzando con lo que yo puedo hacer y que de momento no dependa de los demás. [...] Entonces sigamos explícitamente con cosas que podamos probar entre comillas, que podamos avanzar en lo que las demás personas me pasen su parte o la suben al repositorio. Entonces sigamos. Con esas partes, dime cuál es Dame un plan primero"

Uso en el proyecto: Se produjo un plan por pasos. Se decidió no crear `model/room.py` y esperar a la Persona 2, y dejar el rastro del jugador como estructura de la Persona 3. Se identificó que atacar no requiere salas, porque §2.6 solo exige que atacante y objetivo compartan sala y `Actor` ya guarda el identificador de sala, y que por lo tanto el comportamiento guardián sí era implementable. Quedó por escrito qué partes quedaban bloqueadas y por qué.

Cambios realizados por el estudiante: Decisión propia de no definir `Room` ni el rastro, para no invadir el trabajo de los compañeros.

### 2.8 Cambios solicitados por la Persona 4

Herramienta: Claude

Fecha: 2026-10-14

Objetivo: Atender los pedidos que la Persona 4 planteó para poder implementar el controlador y la persistencia.

Prompts utilizados:

- Se adjuntaron dos capturas con el documento de la Persona 4, que pedía la interfaz de `Game`, la posibilidad de restaurar el contador de secuencia y el estado del generador aleatorio en `GameState`, un método para listar los eventos activos de `EventQueue`, campos adicionales en `Event` para serializar efectos, y señalaba una posible coma final en `rewind_clock_to`. Acompañadas de: "Que más deberia hacer? Antes de hacer un push ya que mis compañeros me estan pidiendo esto. Y ocupo subirlo para no atrasar a mis compañeros"
- "De momento pongamos como prioridad esto, que dijiste de la persona 4, eh, hagamos eso. Para que él pueda trabajar."

Uso en el proyecto: Se verificó en el repositorio que la coma final reportada no existía. Se agregaron `GameState.restore()`, `GameState.random_state()`, `EventQueue.active_events()` y los campos `amount`, `room_id`, `direction` e `instance_id` a `Event`. Se cambió `Event` para que guarde la referencia al objeto `Actor` en lugar de su identificador, porque buscarlo costaría O(n) por evento y §7 prohíbe usar `dict` como índice. Se dejó documentado en `docs/ARQUITECTURA.md` el contrato de `Game` con el controlador y la diferencia entre cargar una partida y retroceder, que en el grupo se estaba confundiendo.

Cambios realizados por el estudiante: Se decidio atender primero lo que pedia la Persona 4, aunque no estuviera en el plan propio de ese dia, para no dejarla bloqueada. De ahi salieron el contrato publico de `Game` que el controlador necesitaba y la preparacion del modelo para guardar y cargar: `GameState.restore()` y `EventQueue.active_events()`. Se le comunico que `restore()` es para cargar una partida y no para el pergamino de retroceso, porque son dos casos distintos, y que el guardado debe persistir reloj, contador de secuencia y estado del generador junto con los eventos activos.

### 2.9 Bucle del motor, actores y enemigos

Herramienta: Claude

Fecha: 2026-10-14

Objetivo: Implementar el motor que coordina reloj, agenda y actores, con las acciones de esperar y atacar.

Prompts utilizados:

- "Ok, está bien, pero a partir de ahora, por favor, trata de recomendarme o de darme opciones de con qué seguir trabajando para no perder el ritmo [...] y cosas por lo general que permitan que mis compañeros avancen en su trabajo, obviamente que solo involucren mi parte."
- Selección de la opción "El motor corriendo", entre tres opciones propuestas.

Uso en el proyecto: Se implementaron `model/actor.py`, `model/player.py`, `model/enemy.py` y `model/game.py`, con el bucle de eventos, el combate de §2.6, la activación de enemigos de §2.4 y el descarte de eventos de actores muertos. Se verificaron los tiempos contra el ejemplo de §2.13 del enunciado. Durante la escritura de las pruebas se detectó un error: un actor conservaba la referencia a un evento ya ejecutado, de modo que un cambio de velocidad en ese momento lo habría dejado con dos acciones pendientes sin producir ninguna excepción.

Cambios realizados por el estudiante: Se reviso que el bucle se detuviera exactamente en la decision del jugador, de modo que una llamada a una accion fuera el ciclo completo que mide la seccion 5.2 sin instrumentar nada. Del combate se verifico la formula de la seccion 2.6 con el generador propio del estado, el minimo de un punto de dano, y que un actor muerto no ejecute sus eventos futuros. Se dejo el descarte de esos eventos antes de mover el reloj, porque un evento que no se ejecuta no debe adelantar el tiempo.

### 2.10 Efectos temporales y mediciones de rendimiento

Herramienta: Claude

Fecha: 2026-10-14

Objetivo: Implementar los efectos de §2.10 que no dependen de las salas y producir las mediciones que exige el enunciado.

Prompts utilizados:

- "Perfecto, continúa con la parte 1 y 2. Pero en la parte 3 podrías avanzar algo sin tocar lo de la parte de mi compañero. Si esta parte me toca a mí alguna, por más mínima que sea, me gustaría avanzarlo y o terminarlo lo máximo posible. [...] Dime qué puedes hacer y sin tocar ninguna parte de ninguno de mis compañeros. Después de esto, haz un push después de revisar y hacer test de todo. Explícame y pregúntame antes de hacer el push al final."

Uso en el proyecto: Se implementaron el veneno, la regeneración, el cambio de velocidad y la antorcha, más el antídoto. Se decidió que el veneno programe sus cinco activaciones de una vez, porque su duración e intervalo son constantes, lo que evita tener objetos de efecto con estado y vuelve trivial la cancelación. `Game` pasó a recibir la bitácora de mensajes desde fuera, de modo que la bitácora circular de la Persona 3 encaje sin modificar el motor. Se escribió `benchmark/scheduler_bench.py`, que mide el montículo contra una lista sin ordenar y el ciclo completo de eventos, y con esos números se completaron los dos apartados de evidencia empírica que estaban pendientes en `docs/DECISIONES.md`.

Cambios realizados por el estudiante: Se reviso que el veneno programara sus cinco pulsos de una vez, lo que vuelve trivial al antidoto: cancelar eventos que ya estan identificados. La regeneracion se dejo encadenada, un pulso programa el siguiente, porque no tiene duracion conocida. El cambio de velocidad se dejo del lado del motor y no del efecto, para no crear una dependencia circular entre los dos modulos. De las mediciones se acepto comparar el monticulo contra una lista sin ordenar, que es la alternativa que la seccion 8 pide medir directamente.

### 2.11 Redacción del Documento de Decisiones

Herramienta: Claude

Fecha: 2026-10-14

Objetivo: Reescribir `docs/DECISIONES.md` con una redacción más natural, y producir un documento de estudio personal.

Prompts utilizados:

- "Ocupo que okay, ahorita me concentrémonos en modificar el documento de decisiones. Me gustaría que lo hicieras como un poquito más lenguaje en el tema de común, pero a la vez que no sea predecible. ¿Me entiendes? Ya que la IA se detecta con que sea predecible. Entonces, que no sea así. Después de eso, me gustaría como que me dieras, aparte de esto, un documento que me explique esto de forma muy sencilla y paso a paso."
- "Ok, me gustaría que metieses eh, mi guía de estudio en el Git Ignore para que no se comité. Y no se suba al repositorio. Después de esto, eh, ocupo que revises prompts LLM y me ayudes a completar ese archivo."

Uso en el proyecto: Se reescribió `docs/DECISIONES.md` conservando íntegros el contenido técnico, las complejidades y todas las mediciones, y cambiando únicamente la redacción. Se produjo además una guía de estudio personal, que por decisión del estudiante no se sube al repositorio y está incluida en el `.gitignore`. Se completó esta sección del registro de prompts.

Cambios realizados por el estudiante: Se pidio reescribir el documento con lenguaje mas llano pero sin volverlo predecible, y se reviso que cada seccion explicara el porque y no solo el que. Ademas se decidio que la guia de estudio personal no se sube al repositorio en ningun momento, igual que el paquete de ejemplos del curso, y los dos quedaron en el `.gitignore`.

### 2.12 Frecuencia medida de las operaciones y revisión del motor

Herramienta: Claude

Fecha: 2026-10-14

Objetivo: Completar la frecuencia medida que pide §8 del enunciado y revisar el motor contra el enunciado buscando reglas mal implementadas.

Prompts utilizados:

- "Que puedo avanzar de mi parte?"
- Elección de la opción "Contadores y frecuencias medidas", entre tres propuestas.
- "La opcion 2", eligiendo la revisión contra el enunciado.

Uso en el proyecto: Se agregaron a `Game` los contadores `player_actions`, `enemies_defeated` y `events_processed`, que §2.12 pide para la tabla de puntajes. `Game` pasó a recibir también la agenda desde fuera, de modo que las mediciones usan una subclase con contadores sin instrumentar la estructura de producción. Se midió la frecuencia real de las operaciones en tres escenarios y se completó el apartado correspondiente de la sección 4.1 del Documento de Decisiones.

La revisión encontró dos errores que no producían ninguna excepción: dos efectos de velocidad encimados dejaban al actor con una velocidad permanente equivocada, y una partida terminada seguía aceptando acciones y sumándolas al contador. Se corrigieron los dos y se agregaron pruebas que los fijan.

Cambios realizados por el estudiante: La revision contra el enunciado destapo dos errores que no daban ninguna senal. El primero: dos pociones de velocidad encadenadas dejaban al actor con una velocidad equivocada para siempre, porque la segunda guardaba como valor a restaurar el que habia dejado la primera; se corrigio restaurando el valor original antes de aplicar el nuevo y se verifico con tres pociones seguidas. El segundo: una partida terminada seguia aceptando acciones, inflaba el contador y programaba eventos; se corrigio revisando el estado al principio de cada accion publica. Se acepto medir la frecuencia de las operaciones en vez de estimarla, porque la seccion 8 pide la frecuencia medida.

### 2.13 Revisión e integración del bloque 2

Herramienta: Claude

Fecha: 2026-10-15

Objetivo: Revisar el trabajo de la Persona 2 antes de integrarlo y fusionar su rama.

Prompts utilizados:

- "Ya mi compañero subio su parte puedes revisar y ver si esta bien, para poder continuar con mi parte"
- "trae su rama y después de eso revisa si hay alguna incongruencia, si hay algo que moleste. Quisiera resolver esto antes de seguir programando para que no me afecte el futuro."

Uso en el proyecto: Se hizo una fusión de prueba en una rama temporal para comprobar que la integración no rompía nada antes de decidir. Se verificó que las firmas con las que el Traductor crea `Player` y `Enemy` coinciden con las del motor, que el código del bloque 2 no usa `dict` como índice, `sorted()` ni `pickle`, y que las 125 pruebas del motor siguen pasando. Se fusionó la rama resolviendo el único conflicto, en este mismo archivo, y se corrigió el título de la sección 6 de `docs/ARQUITECTURA.md`, que tras la fusión ya no describía su contenido.

Se detectó que el Traductor no lee ningún campo de regeneración de la ficha del catálogo, de modo que `Enemy.regeneration` siempre llega en cero y la regla de §2.10 no se aplicaría si la cripta de la revisión trae un enemigo que la declare.

Cambios realizados por el estudiante: Se reviso la rama de la Persona 2 antes de fusionarla y quedo una duda abierta: los enemigos con regeneracion no aparecian en los datos. Se le consulto y confirmo que el esquema del servicio no trae ese campo, de modo que la regeneracion queda implementada en el motor pero sin datos que la activen en la cripta de desarrollo. Tambien se cerro la duda del nombre de los comportamientos: el servicio envia el texto con tilde y el traductor lo convierte, asi que el motor trabaja con sus propias constantes.

### 2.14 Movimiento, puertas, trampas y comportamiento errante

Herramienta: Claude

Fecha: 2026-10-15

Objetivo: Implementar lo que al motor le faltaba del enunciado una vez disponibles las clases de sala del bloque 2.

Prompts utilizados:

- "sigamos con el movimiento y las puertas, ya que es creo que lo más importante de momento que nos falta. Y ya sabemos cómo hacerlo."
- Después, la indicación de continuar con el comportamiento errante y con los objetos que sueltan los enemigos al morir.

Uso en el proyecto: Se implementaron `move()` y `open_door()`, las trampas al entrar a una sala y su rearme, el cierre automático de puertas, la condición de victoria, el comportamiento errante y el paso de los objetos de un enemigo muerto al suelo de su sala.

Jugando la cripta real apareció un error que las pruebas unitarias no habían detectado: el motor comparaba el campo `abre` de la llave contra la llave que pide la puerta, y con los datos reales nunca coincide. §2.7 dice que la coincidencia es contra el id de la ficha. Las pruebas pasaban porque construían la llave con el mismo malentendido que el código.

Cambios realizados por el estudiante: Se decidio implementar de una vez todo lo que dependia de las clases de sala, en lugar de ir pieza por pieza, porque ya estaban disponibles. Se reviso contra el enunciado que entrar a una sala active solo a los enemigos de esa sala, que una puerta sea el mismo objeto desde sus dos lados, que la trampa se dispare al entrar y se rearme despues, y que el errante solo considere salidas con la puerta abierta, porque un enemigo no puede abrir puertas.

### 2.15 Revisión de la rama de la Persona 4 y coordinación con el grupo

Herramienta: Claude

Fecha: 2026-10-15

Objetivo: Revisar el controlador, la vista y la bitácora de reproducción antes de integrarlos, y preparar lo que hay que pedirle al resto del grupo.

Prompts utilizados:

- "Revisemos la rama de mi compañero, de la persona 4, y no hagamos lo del rastro, ya que prefiero esperar a los demás."
- "dame todo lo que falta de mi módulo, lo que me faltaría a mí por trabajar, sepáralo por lo que no depende de mí y por lo que depende de mí."

Uso en el proyecto: Se fusionaron las tres ramas en una rama temporal, se comprobó que no hay conflictos y se jugó la cripta real a través de su controlador, grabando la bitácora de reproducción y reproduciéndola después; la reproducción dio exactamente la misma partida.

Aparecieron dos errores, los dos del motor y no de su código: escribir cualquiera de los siete comandos que dependen del inventario terminaba el programa con `AttributeError`, y al entrar a una sala con trampa el mensaje del daño se anotaba antes que el de la entrada. Se corrigieron ambos.

Se redactaron además los mensajes de coordinación para la Persona 3 y la Persona 4.

Cambios realizados por el estudiante: Revisar la rama de la Persona 4 destapo dos errores propios. El primero es el mas instructivo de todo el modulo: la llave se emparejaba con el campo `opens` del objeto cuando la seccion 2.7 pide que coincida con su `type_id`, y las pruebas unitarias no lo detectaron porque repetian el mismo malentendido; aparecio al jugar la cripta real. El segundo era de orden de los mensajes: el dano de la trampa se registraba antes de anunciar la entrada a la sala, asi que se leia al reves. Al grupo se le comunico que el motor ya exponia lo que el controlador necesitaba y que las dos correcciones estaban en la rama propia.

### 2.16 Nueva medición del presupuesto de procesamiento

Herramienta: Claude

Fecha: 2026-10-15

Objetivo: Rehacer la medición de §5.2 con un escenario que recorra una cripta de verdad.

Prompts utilizados:

- "volvamos a medir y hagamos las frecuencias para después subir esto y de momento no revisemos nada, debido a que faltan cosas y siento que es pérdida de tiempo."

Uso en el proyecto: La medición anterior era insuficiente, porque el jugador solo esperaba y los enemigos eran guardianes quietos, sin salas ni trampas ni puertas. El escenario nuevo recorre una cripta en línea con trampas que se rearman, puertas que se cierran solas y enemigos errantes. Se comprobó que ejercita lo que declara contando las activaciones reales.

De los datos salió una conclusión que antes no se podía sacar: lo que llena la agenda es la cantidad de enemigos activos y no el tamaño de la cripta, lo que responde directamente a una de las preguntas de orientación del enunciado.

Cambios realizados por el estudiante: Se acepto rehacer la medicion porque la anterior usaba un escenario sintetico que no representaba una partida: no habia movimiento entre salas ni puertas ni trampas. Se reviso que el escenario nuevo recorriera la cripta de punta a punta abriendo lo que encontrara cerrado, y que el numero reportado fuera el ciclo completo entre dos decisiones del jugador, que es lo que limita la seccion 5.2.

### 2.17 Integración del bloque de la Persona 3 y el pergamino de retroceso

Herramienta: Claude

Fecha: 2026-10-16

Objetivo: Conectar las estructuras de la Persona 3 al motor e implementar el pergamino de retroceso, que era lo último que faltaba del módulo.

Prompts utilizados:

- "haz los puntos 1 al 4 primero, y explícame todo sobre cómo lo vas a hacer"
- "se continúa con el inventario para ya terminar lo intermedio y dejar para mañana el 6, que es el retroceso y lo complicado"

Uso en el proyecto: Se conectaron la bitácora circular, el módulo de ordenamiento, el rastro y el inventario, con lo que quedaron completos los tres comportamientos de enemigo de §2.8 y las acciones de inventario de §2.7. Después se implementó el retroceso: el motor anota en veintisiete lugares cómo deshacer cada cambio, en lugar de copiar el estado, que es lo que §2.11 prohíbe.

Aparecieron dos cosas al probar. La respuesta a una pregunta que la Persona 3 había dejado abierta: la sala destino se marca con el reloj del instante de la acción y no al terminar su costo, porque §2.5 dice que el jugador aparece en la sala al ejecutarla y el ejemplo de §2.13 lo confirma. Y una decisión propia que se corrigió: el retroceso funciona con la partida terminada, porque §2.11 no pone esa condición y un pergamino que no sirva cuando al jugador lo matan no sirve para nada.

Cambios realizados por el estudiante: Se decidio que el motor anote el cambio inverso de cada modificacion, en los veintisiete lugares donde cambia el estado, en vez de guardar copias, porque la seccion 2.11 prohibe las copias. Para no tener que preguntar si hay historial en cada uno de esos lugares se uso un objeto nulo. Una prueba de la Persona 3 descarto una condicion que se habia agregado de mas: se habia impedido retroceder con la partida terminada, y la seccion 2.11 no pone esa condicion, asi que un jugador muerto si puede volver. Tambien se acordo con ella el ajuste del cursor del inventario y se adopto su verificador de retroceso.

### 2.18 Integración final y carga de partidas guardadas

Herramienta: Claude

Fecha: 2026-10-18

Objetivo: Integrar el trabajo de los otros tres integrantes, dejar resuelto lo que el guardado necesita del motor y unificar el Documento de Decisiones.

Prompts utilizados:

- "toma tú las decisiones que creas mejores y si ocupas específicamente que le diga algo a mis compañeros, dímelo primero"
- "unifica el documento de decisiones, y después registra los prompts"

Uso en el proyecto: Se fusionaron las cuatro partes del proyecto sin conflictos y se comprobó que el juego se ejecuta jugando `cripta-01` sin conexión. Se implementó `Game.load()`, que arma una partida guardada sin hacer el trabajo de inicio de §2.4; usar el constructor normal para cargar dejaría la partida mal sin producir ningún error.

Probando apareció que los efectos activos se pueden deducir de la agenda, porque un veneno son sus pulsos pendientes. Sin eso, un antídoto no habría podido cancelar un veneno cargado de un archivo y la interfaz no habría mostrado nada, sin que nada avisara.

Se unificó el Documento de Decisiones en un solo archivo con las secciones en el orden del §4, y quedó a la vista que faltan las secciones 4.2, 4.3, 4.4 y 4.10.

Cambios realizados por el estudiante: Se decidio integrar en la rama propia el trabajo de los otros tres y verificar que las cuatro partes funcionaran juntas antes de abrir cualquier pedido de incorporacion. Se unifico el Documento de Decisiones en un solo archivo, con las secciones en el orden del enunciado, y se le comunico al grupo que las secciones de la Persona 3 ya estaban adentro y que su archivo aparte se habia eliminado. Del lado del motor se dejo resuelto lo que el guardado necesitaba, `Game.load()`, que arma una partida guardada sin repetir el trabajo de inicio de partida; se le advirtio al grupo que usar el constructor normal para cargar dejaria la partida mal sin dar ningun error.


### 2.19 Auditoría final de la parte del motor contra el Apéndice B

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-10-18

Objetivo: Revisar si quedaba algo pendiente de la parte propia (motor, agenda, reloj, actores, combate y enemigos) antes de la entrega, cruzando los catorce casos del Apéndice B contra las pruebas y verificando que los números del Documento de Decisiones siguieran vigentes después de la última medición.

Prompts utilizados:

```text
revisa si queda algo de mi parte?
```

Uso en el proyecto: Dos pruebas nuevas en `tests/test_rewind.py` y correcciones de cifras y una sección nueva en `docs/DECISIONES.md`.

Cambios realizados por el estudiante: Se revisaron los catorce casos del Apéndice B uno por uno contra las pruebas del motor. Trece corresponden a esta parte y doce ya estaban cubiertos; el que faltaba era el del pergamino recogido dentro del intervalo revertido. Antes de escribir la prueba se verificó que la excepción de §2.11 estuviera aplicada en los dos lugares que tienen que concordar, el suelo en `Game` y el contador en `Inventory`, y estaban correctos, así que se agregaron las dos pruebas que lo dejan demostrado en ambos sentidos. En el Documento de Decisiones se corrigió la razón contra el tope de §5.2, que había quedado en sesenta veces cuando correspondía a la medición anterior y con 0.4403 ms son cuarenta y cinco, y se actualizaron los conteos de pruebas de `test_game.py`, `test_rewind.py` y el total del proyecto. Se agregó la sección que deja constancia de la excepción de los pergaminos.

### 2.20 Guardado binario de la partida (sección 4.10)

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-10-18

Objetivo: Implementar la sección 4.10 del enunciado, que no tenía responsable asignado: el archivo binario de formato propio, la recuperación de una sala sin leer el archivo completo, la detección de versión incompatible y la comparación contra JSON.

Prompts utilizados: la petición fue elegir la opción 2 de las que se ofrecieron al cerrar la auditoría de la entrada 2.19, es decir, tomar la sección 4.10 aprovechando que `Game.load()` ya estaba resuelto del lado del motor. No hubo más texto.

Uso en el proyecto: `adapters/almacen_partida.py`, `benchmark/bench_almacen_partida.py`, `tests/test_almacen_partida.py`, `tests/test_bench_almacen_partida.py`, la medición `docs/mediciones/persona1/guardado_binario_2026-10-18.txt`, la sección 4.10 de `docs/DECISIONES.md` y la actualización de responsables en `docs/ARQUITECTURA.md`.

Cambios realizados por el estudiante: Antes de escribir nada se revisaron las cuatro ramas del grupo para confirmar que nadie había empezado la sección, y se decidió no inventar un formato propio sino seguir el de `adapters/almacen_fichas.py` de la Persona 2, que ya tenía firma, versión, índice ordenado y búsqueda binaria, para que la entrega no quedara con dos estilos de persistencia binaria. El formato se diseñó alrededor del requisito de leer una sala sola: encabezado de tamaño fijo, bloque global, un bloque por sala y el índice al final con su posición anotada en el encabezado. Se decidió que el archivo guarde el estado completo en vez de solo los identificadores, aunque la alternativa ahorra hasta un 60 %, para que una partida guardada no quede inservible si cambia la versión del catálogo; esa alternativa se midió para poder decir con números qué costó la decisión. Dos problemas se resolvieron durante la implementación: que una puerta es el mismo objeto desde sus dos salas, lo que obligó a guardarla en los dos bloques y a compartirla al cargar, y que al medir la alternativa descartada poner los campos en cero no ahorraba bytes porque los enteros del formato son de ancho fijo, de modo que hubo que armar el formato mínimo de verdad omitiendo los campos. La medición dio un resultado contrario a la decisión en una de las tres comparaciones: cargar la partida completa es entre 1.7 y 2 veces más lento que JSON, porque el módulo `json` está escrito en C. Se compilaron los formatos de `struct` una sola vez, lo que recuperó un 15 %, y se decidió reportar el número tal como quedó en el apartado de evidencia empírica y en el de límites conocidos, en vez de omitirlo.

### 2.21 Conexión del guardado al programa y revisión de ramas

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-10-18

Objetivo: Confirmar que nadie del grupo había empezado el guardado antes de subir el trabajo, y después conectar el guardado y el cargado a los comandos del programa.

Prompts utilizados:

```text
Ok, perfecto. Primero revisa las ramas a ver si ya han subido algo sobre ese tema para no hacer el trabajo doble. Y después eh, comitemos todo subimos ese trabajo a mi rama y luego vemos si hay que llegue con el guardar, cargar, yo mismo en el main, para ver si no vamos a hacer trabajo en vano.
```

Uso en el proyecto: `controller/application.py`, `controller/commands.py`, `main.py`, `adapters/almacen_partida.py`, `tests/test_guardado_en_la_aplicacion.py` y las secciones 4.10 y de pendientes de `docs/DECISIONES.md`.

Cambios realizados por el estudiante: Antes de subir se revisaron las cuatro ramas remotas, los archivos de todas ellas y los mensajes de commit, y se confirmó que nadie tenía nada del guardado binario. Al revisar si valía la pena conectarlo al programa se encontró que la Persona 4 ya había construido toda la capa de comandos, con `guardar` y `cargar` interpretados y excluidos de la bitácora de reproducción, y un comentario en `controller/application.py` que decía que al exponerse el guardado se conectaran ahí, así que no era trabajo en vano. Se decidió que guardar funcione dentro de la partida y que cargar sea una opción de arranque, `--cargar ARCHIVO`, porque la bitácora de §4.11 guarda la semilla y las acciones desde el inicio y cargar a media sesión la dejaría reproduciendo algo que no ocurrió, lo que §4.11 prohíbe; el comando `cargar` de adentro del juego explica eso en vez de quedar sin respuesta. Se corrigió un problema que habría fallado en silencio: el inventario sale del archivo sin el historial del retroceso, porque el historial necesita el `GameState` que se arma después de leer, de modo que las acciones posteriores a cargar no se habrían podido deshacer con un pergamino; se vuelve a armar el inventario con el historial puesto y con los mismos objetos, para que el equipo siga apuntando al objeto que está adentro. También se comprobó que `cargar_contenido_de_sala` de la Persona 2 es idempotente, de modo que una partida cargada no duplica enemigos al moverse. Se verificó de punta a punta con los datos sin conexión que jugar de corrido y jugar cortando con un guardado terminan en el mismo estado. Dos pruebas nuevas fallaron por suposiciones equivocadas propias y no del código: el guardado crea las carpetas que falten a propósito, y en `cripta-01` el jugador empieza sin pergaminos, así que el retroceso se rechaza con razón; las dos se reescribieron para medir lo que de verdad importaba.

### 2.22 Traer los cambios de main a la rama propia

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-10-28

Objetivo: Traer a la rama propia la versión más reciente del repositorio y comprobar que no se perdiera nada del trabajo propio en las integraciones.

Prompts utilizados:

```text
Ya estan todas las partes terminadas?
```

```text
Ok, ocupo que revises la versión más nueva que haya en el GitHub y de ahí traigas todos esos cambios de la última versión a mi rama. Después de eso, quisiera que pienses si se va a perder algo de la mía para no que no sea así. Y que me digas qué puede ser.
```

Uso en el proyecto: `benchmark/bench_almacen_partida.py` y la sección 4.10 de `docs/DECISIONES.md`.

Cambios realizados por el estudiante: Antes de traer nada se guardaron los cambios locales sin commitear, para no perderlos. Se comprobó que la rama propia estuviera contenida por completo en `main` y que las once secciones de §4 y la 4.10 entera siguieran ahí, incluidos los apartados de §8. El avance de la rama fue directo, sin conflictos. Al revisar el trabajo local sin commitear se encontró que la Persona 4 ya había hecho casi lo mismo mientras tanto: conectar el guardado a `--bench` y actualizar el README, así que esos cambios locales se descartaron por duplicados. Quedaron dos cosas que sí faltaban. Una es que la medición comparaba un guardado binario con `fsync` contra un guardado JSON sin `fsync`, de modo que el formato propio pagaba una escritura durable y el otro no; se igualó y se dejó escrito por qué, porque es la clase de detalle que invalida una comparación. La otra es que §5.3 pide medir las operaciones de guardado y el Documento de Decisiones solo reportaba las de carga, así que se agregó la tabla con las cifras ya parejas. También se verificó que el cambio que la Persona 3 hizo dentro del módulo de guardado, usar `restore()` en vez de `pick_up()` al reconstruir el inventario, corrige un defecto real del código propio: `pick_up()` descarta el objeto en silencio si el inventario está lleno.

### 2.23 Revisión de la entrega contra el enunciado

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-10-28

Objetivo: Revisar el proyecto entero contra los requisitos del enunciado antes de entregarlo, y dejar registradas las decisiones de trabajo que se tomaron.

Prompts utilizados:

```text
Si mezclamos design main y que no sé qué tan importantes sean los míos, trae la última versión, del trabajo, y ponla aquí. Y después de eso, no nada más. Simplemente trae la última versión del trabajo a mi rama.
```

```text
Ok, perfecto. Ahora ocupo que revises todo, en mi trabajo en esa rama para ver si lo puedo entregar. Ocupo que cumpla las cosas. Esto incluyendo todos los archivos. Los prompts LM agrega tú las decisiones que tomamos. Tú supiste mi decisión. Entonces, redáctalo y si ocupas alguna pregunta, ok, Mau, ¿qué pasaste aquí? Dímelo, pero antes de todo esto. Y hazme preguntas sobre cómo quieres que haga las cosas. O cómo yo quiero que tú hagas las cosas antes de.
```

Decisiones de trabajo tomadas en esta sesión, a pedido del estudiante y antes de empezar la revisión:

1. **Alcance:** revisar todo lo entregable y no solo la parte propia, porque §9 exige que cada integrante pueda explicar cualquier decisión del Documento de Decisiones y la nota del proyecto es grupal.
2. **Qué hacer con lo que se encuentre:** corregir únicamente los archivos propios y reportar lo ajeno con un mensaje listo para el grupo, en vez de modificar código de los compañeros a pocos días de la entrega.
3. **Trabajo local sin commitear:** recuperar los dos cambios que se habían apartado, porque §5.3 pide medir las operaciones de guardado y el documento solo reportaba las de carga, y porque la comparación contra JSON estaba sesgada.
4. **Rama remota:** no subir nada en esta sesión. La rama local quedó al día con `main`; publicarla es una decisión aparte.

Uso en el proyecto: `PROMPTS_LLM.md`, `benchmark/bench_almacen_partida.py` y la sección 4.10 de `docs/DECISIONES.md`.

Cambios realizados por el estudiante: La revisión se hizo contra las secciones 4 a 10 del enunciado y el Apéndice B. Se comprobó que las once secciones de §4 tienen los seis apartados que exige §8 y la frecuencia medida de las operaciones; que no se usa `dict` como índice ni `sorted()` en el código del programa (§7 y §4.9); que no hay identificadores, nombres de cripta ni números de sala escritos en el código (§9); que `--bench` y `--replay` no instancian la vista interactiva (§6); que `--bench` mide los nueve subsistemas sin fallos, incluidos los siete que enumera §5.3; que el ciclo del motor toma 0.1877 ms contra los 20 ms de §5.2; que la interfaz tiene los quince comandos mínimos de §10.2; y que los catorce casos del Apéndice B tienen prueba. Se verificó a mano una vuelta completa del programa sin conexión: jugar, guardar, cargar el guardado, y reproducir con `--replay` la bitácora de la sesión cargada, que dio el mismo resultado que la sesión en vivo. Se corrigió una cosa propia: el `dict` que usa la alternativa descartada del benchmark de §4.10 quedó marcado como que existe solo para medir y no se usa en el programa, siguiendo la convención que el grupo ya había usado en `bench_tabla_hash.py`.

## 3. Revisión de interfaces existentes y contrato de la Persona 4

Herramienta: Claude (Claude Sonnet 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Revisar el contenido real de `docs/ARQUITECTURA.md`, `model/game_state.py`, `model/event.py` y `structures/event_queue.py` para detectar qué necesita la Persona 4 (MVC, interfaz, replay, benchmark e integración) de los módulos ya implementados.

Prompts utilizados:

- "listo, 2. game.py y actor.py no tienen nada en este momento, game state: [se pegó el código completo de `GameState`], event.py: [se pegó el código de `Event`], event_queue.py: [se pegó el código de `EventQueue`]" (acompañado del contenido completo de `docs/ARQUITECTURA.md`, en respuesta a la lista de archivos solicitada previamente).

Uso en el proyecto: Se utilizó la respuesta para identificar huecos que afectan a la Persona 4: la interfaz de `Game` aún no existe, `GameState` no permite restaurar el contador de secuencia ni el estado del generador aleatorio, `EventQueue` no permite listar los eventos activos, `Event` carece de los datos necesarios para serializar efectos, y la propiedad de `adapters/persistence.py` y de la tabla de puntajes no está asignada. También se utilizó para proponer un contrato `Game` ↔ controlador y un formato de log de replay.

Cambios realizados por el estudiante: Se verificaron los hallazgos contra el repositorio antes de aceptarlos, y uno resulto falso: la coma final que se reportaba en `rewind_clock_to` no existia, y de haber existido las pruebas del reloj habrian fallado, porque el metodo habria devuelto una tupla. Los otros cuatro pedidos si eran reales y se aceptaron: el contrato publico de `Game`, restaurar el contador de secuencia y el estado del generador, listar los eventos activos de la agenda, y los campos que `Event` necesitaba para los efectos. Se descarto guardar la agenda en la bitacora de reproduccion, porque esa bitacora registra las acciones del jugador y no los eventos. Quedo sin asignar la propiedad del guardado binario, que se decidio mas adelante.

Nota posterior: la coma final reportada en `rewind_clock_to` se verificó contra el archivo del repositorio y no existe. Los otros cuatro pedidos se implementaron el 2026-10-14, según la entrada 2.8.

## 4. Resumen de puntos para la reunión del grupo

Herramienta: Claude (Claude Sonnet 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Condensar el análisis anterior en una lista de puntos concretos para discutir con el equipo.

Prompts utilizados:

- "Me puedes si resumir en puntos especificos para poder ir y ver con el equipo"

Uso en el proyecto: Se utilizó la respuesta como guía para la reunión del grupo: interfaz pendiente de `Game`, cambios solicitados a `GameState`, `EventQueue` y `Event`, reparto de archivos de persistencia, decisiones abiertas sobre el log de replay y formato de log propuesto.

Cambios realizados por el estudiante: Se llevaron los puntos a la reunion y se acordo el reparto de lo que estaba sin dueno: la bitacora de reproduccion y la tabla de puntajes quedaron del lado de la Persona 4, y la persistencia del catalogo y de la cripta, del lado de la Persona 2. Se acordo tambien que el motor expondria lo que el controlador necesitaba sin conocer la vista, y que las estructuras de la Persona 3 se le pasarian al motor desde afuera en vez de que el motor las construyera.

## 5. API, caché y persistencia (Persona 2)

Registro de la Persona 2. Los prompts se reproducen tal cual, incluidos los errores de escritura. En la entrada 5.2 se pegaron dos textos de un compañero, que se describen en lugar de copiarlos. Algunos mensajes de coordinación (por ejemplo, avisos de pausa) no se registraron porque no pidieron nada sobre el proyecto.

### 5.1 Análisis del enunciado y del programa del curso

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-10

Objetivo: Entender el alcance del proyecto y relacionar los problemas de §4 con los temas del curso.

Prompts utilizados:

```text
Soy estudiante de ingenieria en sistemas,  estoy segundo año de carrera, estoy en el curso de Estructuras de datos, tengo que hacer un proyecto basado en un juego pero lo importante no es el juego sino el sistema que consulta un API para obtener archivos JSON con informacion o indicaciones para avanzar en el juego. El archivo PDF es la descripcion del proyecto dado por el profesor y con indicaciones del profesor para aplicar por parte de la IA para que se hagan las cosas de algunas formas especificas. Necesito que me ayudes a generar los archivos necesarios con el codigo para el proyecto. El lenguaje de programacion es python, del cual tengo conocimiento basico y se pueden utilizar las librerias python game y arcade (creo recordar que asi se llamaban las librerias mencionadas por el profesor) pero de momento necesito primero que analices el documento del proyecto para que te hagas la idea sobre lo que trata el proyecto, luego te paso otra informacion para analizar y cuando te indique, me ayudas con la generacion de codigo y los archivos necesarios para el proyecto. Toma el tiempo que necesites para analizar el proyecto. El segundo PDF que te pasare es la informacion sobre el curso y sobre los temas que se ven en el curso para que tengas mas claro los temas que se ven en el curso y sea mejor para analizar el proyecto con relacion a los temas que se dan en el curso.
```

Adjuntos: Enunciado del proyecto CRIPTA (PDF) y programa del curso EIF-207 (PDF).

Uso en el proyecto: Se usó para entender el alcance del proyecto y relacionar los problemas de la sección 4 con los temas del curso.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.2 Revisión del flujo de trabajo y de la distribución del grupo

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-10

Objetivo: Crear esta bitácora, comparar alternativas de estructuras de datos y revisar la organización del trabajo y el flujo propuestos por el grupo.

Prompts utilizados:

```text
Primero, ayudame a llevar el historial de prompt para tenerlo en un documento y poder entregarselo al profesor junto al de mis compañeros ya que es requerido. Por las estructuras de datos, analiza las estructuras de datos que mencionaste como primera y segunda opcion para elegir las que se comporten de manera más estable en el programa y sean las mejores segun rendimiento, complejidad algoritmica y velocidad de procesamiento de los datos. Algunas funciones del juego, segun la explicacion dada por el profesor, hay que elegir algunas cosas del juego como objetos que se encuentran, enemigos que se encuentran en las habitaciones de la masmorra, armas que se encuentren y decisiones sobre si lucha o huye de algun enemigo. Hay una informacion dada por uno de mis compañeros sobre la organizacion del trabajo y como debe ser el flujo de trabajo para realizar el proyecto, ademas de la distribucion de funciones o lo que le corresponde a cada uno realizar. Asi que primero te paso la informacion sobre la estructura del trabajo y el flujo para realizar el trabajo, creo que se realizo con una IA, asi que analiza como esta la informacion y si esta bien estructurado:

[se pegó el prompt de trabajo para la IA propuesto por un compañero: reglas de trabajo y flujo por etapas]


Ahora, esta informacion es sobre la distribucion del trabajo entre los integrantes del grupo, el cual me corresponde hacer el punto numero 2:

[se pegó la propuesta de distribución del trabajo en cuatro bloques]

Analiza toda esa informacion y dime que tan bien esta la informacion y sobre ese flujo de trabajo para luego concentrarnos en realizar la parte que me corresponde.
```

Uso en el proyecto: Se creó el registro de prompts del bloque 2, se compararon las estructuras candidatas de cada problema y se propusieron ajustes al flujo de trabajo y a la distribución del grupo.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.3 Fecha de entrega y plan de trabajo

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-10

Objetivo: Planificar el trabajo del bloque 2 según la fecha de entrega.

Prompts utilizados:

```text
la fecha de entrega esta en duda ya que la primera fecha dada es para mañana 11 de octubre pero recordamos que el profesor dio tiempo al 18 de octubre
```

Uso en el proyecto: Plan de trabajo diario del bloque 2 para las dos fechas posibles de entrega.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.4 Análisis del bloque 2

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-10

Objetivo: Analizar los requisitos, decisiones abiertas e interfaces del bloque 2 (API, caché y persistencia).

Prompts utilizados:

```text
Si, iniciemos con el análisis del bloque 2 que me corresponde y luego vemos la tabla hash ya que anteriormente mencionaste que me debe corresponder a mi
```

Uso en el proyecto: Lista de requisitos del bloque 2, costo en solicitudes de una partida, decisiones D1 a D9 e interfaces a acordar con el grupo.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.5 Supuestos para lo que el enunciado no define

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Proponer soluciones a los casos que el enunciado no define y confirmar las decisiones de diseño del bloque 2.

Prompts utilizados:

```text
Sobre las respuestas del punto 7, es complicado contactar al profesor de manera que es mejor plantear una respuesta o una solucion a cada una de las incognitas planteadas en base a la logica implementada en juegos  semejantes a este para deducir la logica que deba seguir 

Sobre las estructuras de datos y demas puntos mencionados, estoy de acuerdo con las decisiones que planteaste como solucion para implementarlas en el proyecto, sobre el punto uno estoy de acuerdo en hacer una implementacion como dijiste y luego, si da tiempo, hacer el cambio para optimizar el programa
```

Uso en el proyecto: Supuestos documentados en `docs/BLOQUE_2_PARA_EL_GRUPO.md` (sección 5) y aprobación de las decisiones D1 a D9.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.6 `dict` frente a una tabla hash propia

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Comparar la eficiencia del `dict` de Python contra una tabla hash propia, con una medición de prueba.

Prompts utilizados:

```text
Que tan eficiente es utilizar bibliotecas de python en lugar de tablas hash ya que en si mismas son tablas hash en su funcionamiento?
```

Uso en el proyecto: Script de comparación `dict` contra tabla propia; confirmó que la restricción de §7 tiene un costo medible y que la función hash es lo que más pesa.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.7 Elección de la función hash e implementación de `TablaHash`

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Comparar las mediciones de dos computadoras, elegir la función hash (crc32 o FNV-1a) e implementar la `TablaHash` con sus pruebas y su benchmark.

Prompts utilizados:

```text
Aca estan los resultados de los test de velocidad ya probados en mi computadora para que los compares con los obtenidos por ti

En otro punto sobre la duda en si utilizar las bibliotecas, entiendo que no se puedan utilizar asi que sigamos con la tabla hash como esta indicado en el enunciado del proyecto

Revisa los resultados y luego con eso, vemos si se implementa la tabla hash con FNV-1a o con crc32
```

Adjuntos: Captura de pantalla con los resultados de `comparar_dict_vs_tabla_propia.py` en la computadora de Mauricio.

Uso en el proyecto: `structures/tabla_hash.py` y `structures/funciones_hash.py` con crc32, sus pruebas y su benchmark.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.8 Benchmark de la tabla hash e interfaz `FuenteDatos`

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Interpretar el benchmark de la `TablaHash`, corregir el calentamiento del benchmark y definir la interfaz `FuenteDatos` (contrato común de red y modo offline).

Prompts utilizados:

```text
Ya estan los resultados ejecutados desde la consola como lo indicaste 

Y si, vamos con la interfaz FuenteDatos
```

Adjuntos: Captura de pantalla con los resultados de `python -m bench.bench_tabla_hash` en la computadora de Mauricio.

Uso en el proyecto: `adapters/fuente_datos.py` (contrato común, errores y cuenta del presupuesto) y ajuste del benchmark.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.9 Benchmark con calentamiento del procesador

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Interpretar los resultados del benchmark de la `TablaHash` después de agregar el calentamiento.

Prompts utilizados:

```text
Aca estan los resultados con el nuevo archivo cripta que me pasaste
```

Adjuntos: Captura de pantalla con los resultados de `python -m bench.bench_tabla_hash` (versión con calentamiento) en la computadora de Mauricio.

Uso en el proyecto: Interpretación de la segunda corrida del benchmark de la tabla hash.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.10 Métodos abstractos de `FuenteDatos`

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Entender qué son los métodos abstractos de `FuenteDatos` y quién los implementa.

Prompts utilizados:

```text
Del archivo FuenteDatos tengo una duda, los metodos que estan solo con comentarios es porque falta la implementacion y tiene que hacerlo alguno de los compañeros segun la parte que tienen que hacer ?
```

Uso en el proyecto: Aclaración: `FuenteHttp` y `FuenteOffline` implementan el contrato; son parte del bloque 2.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.11 `FuenteHttp`, `FuenteOffline` y descarga de datos para el modo offline

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Implementar `FuenteHttp` y `FuenteOffline` con sus pruebas, y una herramienta para descargar los datos del modo offline.

Prompts utilizados:

```text
Si, continuemos con los dos archivos Fuente
Sigue usando los nombres descriptivos para las clases, funciones y metodos como lo hiciste con el archivo FuenteDatos, me gusta que sea asi
```

Uso en el proyecto: `adapters/fuente_http.py`, `adapters/fuente_offline.py`, `tools/descargar_datos_offline.py` y sus pruebas.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.12 Carpeta desde la que se ejecutan las pruebas

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Saber desde qué carpeta ejecutar las pruebas y la herramienta de descarga.

Prompts utilizados:

```text
Para probar con los comandos de test que me diste, los pruebo desde la carpeta cripta que me diste en el zip??
```

Uso en el proyecto: Instrucciones para ejecutar las pruebas desde la carpeta correcta.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.13 Primera conexión real con el API

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Interpretar el resultado de la primera conexión real con el API y decidir el siguiente paso.

Prompts utilizados:

```text
Aca esta lo de la consola con test que me diste
```

Adjuntos: Captura de pantalla de la consola con la instalación de dependencias, las pruebas (106 OK) y la primera descarga real del API.

Uso en el proyecto: Confirmación de la conexión real y de las 7 solicitudes de la descarga completa.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.14 Revisión de los datos reales de `cripta-01`

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Revisar los datos reales para confirmar o corregir los supuestos del diseño (puertas, pociones, presupuesto, campos opcionales).

Prompts utilizados:

```text
Te adjunto la carpeta que me solicitaste de los datos offline
```

Adjuntos: `datos_offline.zip`, con los datos de `cripta-01` y el catálogo descargados del API real.

Uso en el proyecto: Hallazgos sobre puertas declaradas desde un solo lado y el campo `abre` de las llaves; descripción de la caché LRU.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.15 Caché LRU del catálogo

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Implementar la caché LRU del catálogo (`CacheCatalogo`) con sus pruebas y su benchmark.

Prompts utilizados:

```text
Si, implementala asi
```

Uso en el proyecto: `structures/cache_catalogo.py`, sus pruebas y su benchmark.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.16 Almacén de fichas en disco

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Implementar el almacén de fichas en disco (`AlmacenFichas`, decisión D6) con sus pruebas y su benchmark.

Prompts utilizados:

```text
Si, sigamos con el almacen en disco de la parte D6
```

Uso en el proyecto: `adapters/almacen_fichas.py`, sus pruebas y su benchmark.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.17 Proyecto en una sola carpeta, con README y verificación automática

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Ordenar el proyecto en una sola carpeta lista para abrir y ejecutar, con README y un script que corre las pruebas y los benchmarks y guarda los resultados.

Prompts utilizados:

```text
Dame los archivos ordenados como deberian de estar para abrir la carpeta y ejecutar en consola los comandos que me pides probar y pasarte los resultados
```

Uso en el proyecto: README, `tools/ejecutar_verificaciones.py` y proyecto ordenado en una sola carpeta.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.18 Resultados de la verificación y diseño del `GestorCatalogo`

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Interpretar los resultados de las pruebas y los benchmarks, y proponer la interfaz del `GestorCatalogo`.

Prompts utilizados:

```text
Aca esta el txt con los resultados de las verificaciones
```

Adjuntos: `resultados_verificacion.txt` (pruebas y benchmarks ejecutados en la computadora de Mauricio).

Uso en el proyecto: Interpretación de la primera medición oficial y propuesta de interfaz del `GestorCatalogo`.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.19 Implementación del `GestorCatalogo`

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Implementar el `GestorCatalogo` (memoria, disco y red con lotes de 10) con sus pruebas.

Prompts utilizados:

```text
Si, me parece bien 
implementalo de esa manera
```

Uso en el proyecto: `repository/gestor_catalogo.py`, `structures/lista_sin_repetidos.py` y sus pruebas.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.20 Comprobación de un archivo enviado aparte

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Confirmar que el archivo `gestor_catalogo.py` enviado aparte es idéntico al que viene dentro del zip.

Prompts utilizados:

```text
Ya hare las pruebas pero tengo la duda si el archivo gestor catalogo que me das es el mismo que esta dentro del zip
```

Uso en el proyecto: Confirmación de que el archivo enviado aparte era idéntico al del proyecto.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.21 Segunda medición y diseño de la precarga por BFS

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Comparar la segunda medición con la primera y explicar el diseño de la precarga con BFS (`GestorContenido`).

Prompts utilizados:

```text
Aca estan los resultados de las verificaciones
```

Adjuntos: `2.resultados_verificacion.txt` (segunda corrida de pruebas y benchmarks en la computadora de Mauricio).

Uso en el proyecto: Comparación de la segunda medición y explicación de la precarga por BFS.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.22 `GestorContenido` con precarga por BFS

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Implementar el `GestorContenido` con la precarga por BFS (grafo de salas, pruebas y benchmark de solicitudes).

Prompts utilizados:

```text
Continuemos con el proyecto, implementa el GestorContenido con la precarga por BFS y una vez que este listo, corro la tercera medicion de los test para verificar que todo este funcionando correctamente\
```

Uso en el proyecto: `structures/grafo_salas.py`, `repository/gestor_contenido.py`, sus pruebas y `benchmark/bench_precarga_contenido.py`.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.23 Tercera medición y medianas

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Consolidar las tres corridas en una tabla con el valor del medio de cada medición, para el Documento de Decisiones.

Prompts utilizados:

```text
Adjunto el txt de los resultados de las verificaciones realizadas
```

Adjuntos: `3.resultados_verificacion.txt` (tercera corrida de pruebas y benchmarks en la computadora de Mauricio).

Uso en el proyecto: Medianas de las tres corridas en `docs/mediciones/bloque2/`.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.24 `RepositorioCripta`, persistencia por versión y guía para el grupo

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-14

Objetivo: Implementar el `RepositorioCripta` (punto de entrada del bloque 2), la persistencia del esqueleto y del contenido, la verificación de versiones para `--replay`, una herramienta de simulación y un documento de integración para el grupo.

Prompts utilizados:

```text
Sigamos con el RepositorioCripta, avancemos en los archivos todo lo que sea posible para actualizar el proyecto en github y asi los demas puedan avanzar y con eso pueda yo solicitarle los archivos necesarios para poder terminar este bloque del proyecto
```

Uso en el proyecto: `repository/repositorio_cripta.py`, `adapters/almacen_cripta.py`, `tools/simular_partida_bloque2.py` y `docs/BLOQUE_2_PARA_EL_GRUPO.md`.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.25 Presupuesto de solicitudes medido contra el API real

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-14

Objetivo: Interpretar el presupuesto de solicitudes medido contra el API real y guardarlo como evidencia.

Prompts utilizados:

```text
(mensaje sin texto: solo la captura de pantalla con los resultados)
```

Adjuntos: Captura de pantalla con dos corridas de `herramientas.simular_partida_bloque2` contra el API real (arranque en frío y en caliente).

Uso en el proyecto: Evidencia en `docs/mediciones/bloque2/presupuesto_api_real_2026-10-14.md`.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 5.26 `Traductor` y clases de sala, objeto y trampa

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-14

Objetivo: Implementar el `Traductor` completo (datos del API → objetos del modelo), crear las clases del modelo que faltaban para salas, puertas, objetos y trampas, e integrarlo al `RepositorioCripta`.

Prompts utilizados:

```text
Ahora sigamos con el Traductor ya que se tiene lo necesario para poder hacerlo completo y asi añadirlo al proyecto, seguiré trabajando sobre la carpeta del proyecto, nada más pasame los archivos que se creen o modifiquen y la ubicacion dentro de las carpetas del proyecto donde deben ir para ir agregandolos
```

Respuesta elegida en la pregunta de opciones que hizo Claude, porque las clases de sala, objeto y trampa no existían en ninguna rama:

```text
Completo con clases propias (Recomendado)
```

Uso en el proyecto: `repository/traductor.py`, `model/room.py`, `model/item.py`, `model/trap.py`, integración en `repository/repositorio_cripta.py` y `tools/simular_partida_bloque2.py`, pruebas en `tests/test_traductor.py`, `tests/test_room.py` y `tests/test_repositorio_cripta.py`, y actualización de `docs/BLOQUE_2_PARA_EL_GRUPO.md`, `docs/ARQUITECTURA.md` y `README.md`.

Cambios realizados por el estudiante:  Ante la pregunta de cómo hacer el Traductor, se eligió la opción completa con clases propias (`model/room.py`, `model/item.py`, `model/trap.py`), porque las clases de sala, objeto y trampa no existían en ninguna rama y sin ellas el Traductor quedaba a medias. Se aceptaron los acuerdos propuestos: una sola puerta compartida por cada paso entre dos salas, los enemigos fuera de `Room` (en la lista de `Game`), los objetos que suelta un enemigo creados de antemano y el comportamiento del API traducido a las constantes de `Enemy`. Antes de agregar los archivos se comprobó que la rama local estaba igual que la de GitHub (`git rev-parse HEAD^{tree}`), y después se verificaron las 373 pruebas y la simulación sin conexión. Los cambios se subieron en el commit 480e6d2 de la rama `Parte_2-API-cache-persistencia`.

### 5.27 Verificación del `Traductor` contra el API real

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-14

Objetivo: Confirmar que la rama estaba lista para agregar el `Traductor` e interpretar la simulación contra el API real con los objetos del modelo.

Prompts utilizados:

```text
Utilice los comandos en el git bush y esta limpia la rama, asi que se pueden agregar los cambios. Ya agregue los cambios a la carpeta del proyecto local. 

En la otra imagen es la prueba de los test que corri para verificar que todo funciona bien en el proyecto, limpie la cache y lo corri nuevamente
```

Adjuntos: Captura de Git Bash con el resultado de `git rev-parse HEAD^{tree}` y captura con dos corridas de `tools.simular_partida_bloque2` contra el API real (arranque en frío y en caliente).

Uso en el proyecto: Evidencia en `docs/mediciones/bloque2/presupuesto_api_real_2026-10-14.md` (segunda medición) y `docs/mediciones/bloque2/presupuesto_api_real_traductor_2026-10-14.png`.

Cambios realizados por el estudiante: Se ejecutó la simulación contra el API real con la caché borrada y después otra vez con la caché llena. Se obtuvieron 7 de 9 solicitudes en frío y 3 de 9 en caliente, y el Traductor creó 6 salas, 3 enemigos, 8 objetos en el suelo, 2 objetos que sueltan los enemigos y 1 trampa. También se verificaron las 373 pruebas. Se decidió guardar esta segunda medición como evidencia junto a la primera, en `docs/mediciones/bloque2/`. Se aclaró cuál de los archivos enviados correspondía al código y cuál a la documentación, y todo se subió en el mismo commit 480e6d2.

### 5.28 Revisión del proyecto integrado y regeneración de enemigos

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-15

Objetivo: Revisar el proyecto con las ramas de las personas 1, 2 y 4 unidas, comprobar que los bloques funcionen juntos y resolver la observación de la persona 1 sobre la regeneración de los enemigos.

Prompts utilizados:

```text
(mensaje sin texto: solo la captura de pantalla con las 521 pruebas y la simulación offline en la rama de revisión)
```

Segundo mensaje, con el proyecto adjunto:

```text
Te adjunto el proyecto para que revises todos los archivos y me ayudes a contrastar que todo funcione bien junto, ademas, te pasare un mensaje de un companero sobre algo que hay que resolver para que una vez revisado el proyecto, hagas la revision del mensaje y poder resolverlo:

El mensaje del companero:
"La incongruencia que sí importa
El traductor no lee ningún campo de regeneración. Tu motor la implementa completa y la activa sola cuando enemy.regeneration > 0, pero el traductor nunca llena ese campo, así que siempre llega en cero.

En cripta-01 no hay ningún enemigo con regeneración, así que hoy no se nota. Pero §2.10 dice que un enemigo puede declararla, y §9 avisa que la revisión usa una cripta que nadie vio. Si esa cripta trae uno, no se va a curar nunca y nada lo va a avisar.

No lo arreglé yo porque el traductor es su archivo y, sobre todo, porque no sabemos cómo se llama ese campo en el API. Hay que preguntárselo a él o encontrar una cripta publicada que lo traiga."
```

Adjuntos: Captura de PowerShell con las pruebas y la simulación en la rama `revision-integracion`, y el zip del repositorio completo en esa rama (con la carpeta `.git`).

Uso en el proyecto: Revisión de la integración (pruebas, simulación y una partida de prueba que une los bloques 1, 2 y 4), verificación del contrato del API en `/openapi.json`, avisos de campos desconocidos en `repository/traductor.py` con sus pruebas, y actualización de S13 y de los pasos de integración para la persona 4 en `docs/BLOQUE_2_PARA_EL_GRUPO.md`.

Cambios realizados por el estudiante: Se unieron en una rama local de revisión (`revision-integracion`) las ramas de las personas 1 y 4 con la del bloque 2, sin conflictos, y se comprobó que pasaban las 521 pruebas y la simulación sin conexión. Sobre la observación de la persona 1, se revisó la evidencia del contrato del API (`/openapi.json`, versión 1.0.0): el esquema `Enemy` es cerrado y no tiene ningún campo de regeneración. Por eso se decidió no adivinar el nombre de un campo y dejar `regeneration` en 0 (S13), agregando en el Traductor un aviso en el reporte final por si el API llega a enviar un campo que el programa no conoce. Los cambios se aplicaron en la rama `Parte_2-API-cache-persistencia` y no en la de revisión, y se verificaron las 380 pruebas antes de subirlos. Los problemas de integración que dependen de otros integrantes (cargar la sala desde el controlador, `main.py`, la vista y el bloque de la persona 3) se comunican al grupo en lugar de modificar sus archivos.

## 6. Integración, `main.py`, reproducción y puntajes (Persona 4)

Herramienta: Claude Code (Claude Opus 5.5), en la terminal sobre el repositorio local

Fecha: 2026-10-17

Objetivo: Revisar todas las ramas para saber qué le faltaba a la Persona 4, integrar la rama del grupo, conectar el controlador con el repositorio del bloque 2, escribir `main.py`, el ejecutor de `--bench` y la tabla de puntajes, y actualizar el README.

Prompts utilizados:

```text
Hola claude, puedes por favor revisar todas las ramas y el proyecto para ver que falta de la P4 y que agregaron nuevo para ir trabajando? Me puso esto mi companero:
```

(Seguido del mensaje de un compañero sobre el guardado binario: el constructor de `Game` hace trabajo de inicio de partida, la propuesta de un `Game.load()` aparte, qué debe y qué no debe ir en el archivo, y el aviso de que `main.py` seguía vacío.)

```text
Cual me recomiendas mejor? Necesitamos terminar este proyecto rapido, tenemos 1 dia par asubirlo y estudiarlo
```

```text
Si, dale con el punto 1 y 2
```

```text
Si, dale con main por favor
```

```text
Por favor sube mi rama y sigue con puntajes y readme
```

Uso en el proyecto: Se usó la revisión para listar los pendientes de la Persona 4 y repartir el trabajo restante con el compañero (él hace el guardado binario completo y `Game.load()`; la Persona 4, la integración). Después, con ayuda del modelo: se fusionó `mauricio-logica-juego` en la rama de la Persona 4; `GameController` carga la sala destino antes de `move()` y precarga después de cada acción aceptada, con lo que `--replay` ya no se detiene en el primer `mover`; se escribieron `main.py`, `controller/application.py`, `benchmark/benchmark.py` y `adapters/scoreboard.py`; la vista muestra salidas, suelo, inventario y puntajes; y se actualizó el README.

Cambios realizados por el estudiante: Se revisó la propuesta del compañero sobre el guardado y se decidió que él lo implemente completo, porque depende de los internos del motor. Se verificó con `cripta-01` sin conexión que una partida registrada se reproduce igual (muerte en el instante 198 con semilla 5), que un log con otra versión se rechaza y que `--bench` corre las seis suites. Se subió la rama `Parte_4-MVC-replay-bench`.

### 5.29 Revisión del proyecto completo y secciones 4.2 a 4.4 del Documento de Decisiones

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-18

Objetivo: Revisar el proyecto con las ramas de los cuatro integrantes unidas, y escribir las secciones 4.2, 4.3 y 4.4 del Documento de Decisiones con los seis apartados de §8, a partir del mensaje del grupo.

Prompts utilizados:

```text
(mensaje sin texto: solo la captura de pantalla con las 741 pruebas y la salida de python main.py --help en la rama de revisión)
```

Segundo mensaje, con el proyecto adjunto:

```text
Haz la revision del proyecto completo con todo el analisis de los archivos, verificando que este todo completo
Solo que te pasare un mensaje de parte del grupo que de la parte 2 falta algo en la documentacion que necesito que se complete: 

"Muchachos, les paso el estado y lo que falta, que es menos de lo que parece pero hay algo urgente.

LO QUE YA ESTÁ

Fusioné las cuatro partes en mi rama (mauricio-logica-juego). Cero conflictos, 761 pruebas pasando, y el juego corre: lo probé con main.py --offline jugando cripta-01, con la trampa, las ratas, el replay y la tabla de puntajes.

Mi módulo está terminado, incluido el retroceso. También dejé listo Game.load(), que es lo que el guardado va a necesitar del motor.

Unifiqué el Documento de Decisiones en un solo archivo. Erick, tus secciones 4.5 a 4.9 ya están adentro de DECISIONES.md y borré DECISIONES_PERSONA3.md. Ahora las secciones van en el orden del enunciado, de la 4.1 a la 4.11.

LO URGENTE: FALTAN CUATRO SECCIONES DEL DOCUMENTO

Al unificar quedó a la vista que faltan cuatro de los once problemas del §4:

- 4.2 Precarga de contenido
- 4.3 Resolución del catálogo
- 4.4 Caché persistente
- 4.10 Guardado binario

Mauricio A., las tres primeras son tuyas. Y ojo que no es que estén a medias: no existen en ningún lado. BLOQUE_2_PARA_EL_GRUPO.md es una guía de integración buenísima, pero no tiene ni una mención de alternativas consideradas, análisis de complejidad ni evidencia empírica, que son tres de los seis apartados que pide §8.

La buena noticia es que el trabajo difícil ya lo hiciste. Tenés las mediciones corridas en docs/mediciones/bloque2/ y los cuatro benchmarks. Lo que falta es escribir las secciones con los seis apartados:

1. El problema en tus palabras, y qué operaciones ejecuta el programa con qué frecuencia medida
2. Al menos dos alternativas y por qué descartaste una
3. La decisión
4. El análisis de complejidad de las operaciones más frecuentes
5. La evidencia empírica con tus mediciones
6. Los límites conocidos

Esto pesa el doble de lo que parece. Son 15% de Decisiones, pero esas tres secciones son el corazón del 25% de API y red: ahí va tu tabla hash contra el dict, la caché LRU y la precarga por lotes. Tenés los números, solo falta contarlos.

LA 4.10 NO TIENE DUEÑO

Steven me dijo que el guardado binario le toca a "mi compañero". Pero el 13 de octubre vos mismo habías propuesto hacer save_file.py y json_save.py, y la tabla de ARQUITECTURA.md pone la persistencia del lado de Mauricio A. O sea que cada uno puede estar esperando al otro.

Decidan entre ustedes dos quién lo toma, hoy. Es lo único del enunciado sin responsable y arrastra también su sección del documento, incluida la comparación contra JSON.

De mi lado ya está resuelto: Game.load() arma una partida guardada sin hacer el trabajo de inicio. Lo importante es que NO usen el constructor normal de Game para cargar: programa la primera acción del jugador en el instante 0 y activa enemigos, así que la partida cargada quedaría mal sin dar ningún error. Game.load() también deja bien el scheduled_event de cada actor, y si no le pasan los efectos los deduce de la agenda, así que el archivo ni siquiera tiene que guardarlos.

Lo que el archivo sí tiene que guardar: reloj, contador de secuencia y estado del generador; vida, sala, velocidad, equipo e inventario del jugador; vida, sala y si está activo de cada enemigo; puertas, trampas y suelo de cada sala; la agenda; el rastro; antorcha, resultado y los dos contadores de puntajes.
Lo que NO: el historial del retroceso, la bitácora de 20 mensajes y events_processed.

DOS COSAS MÁS, MENORES

Steven, dale al PR a main cuando quieras. Ya verifiqué que las cuatro partes fusionan limpio.

Erick, en tus pendientes decís que la frecuencia del historial es una cota inferior porque el motor no anotaba sus cambios. Ya los anota, son 27 lugares. Cuando repitas esa medición te va a dar bastante más alto. Y tus cifras están corridas en Python 3.13 sobre Linux; conviene repetirlas en la máquina del grupo antes de entregar, como vos mismo anotaste."
```

Mensajes del 15 de octubre que completan la entrada 5.28:

```text
Ayudame a llenar esa parte con la explicacion necesaria de acuerdo a lo realizado en el proyecto y los cambios
```

```text
si, redacta esas partes tambien
```

Adjuntos: Captura de PowerShell con las pruebas y `python main.py --help`, y el zip del repositorio completo en la rama `revision-integracion` (con la carpeta `.git`).

Uso en el proyecto: Revisión del proyecto integrado (pruebas, una partida con `main.py --offline`, su reproducción con `--replay`, `--bench` y la tabla de puntajes); secciones 4.2, 4.3 y 4.4 de `docs/DECISIONES.md`; `benchmark/bench_frecuencia_bloque2.py` con su prueba `tests/test_bench_frecuencia_bloque2.py` y la medición `docs/mediciones/bloque2/frecuencias_2026-10-18.txt`; actualización de `docs/BLOQUE_2_PARA_EL_GRUPO.md`.

Cambios realizados por el estudiante: Se unieron las ramas de los cuatro integrantes en la rama local de revisión y se verificaron las 741 pruebas y las opciones de `main.py`. A partir del mensaje del grupo, se pidió escribir las secciones 4.2 a 4.4 con los seis apartados de §8 usando las mediciones del 13 y 14 de octubre. Como §8.1 pide la frecuencia medida de las operaciones y no la teníamos, se decidió agregar un benchmark que la cuenta, y se aceptó que la comparación de políticas FIFO y LFU quede razonada y declarada como no medida. Las secciones se pegaron en el `DECISIONES.md` unificado por la persona 1, después de la 4.1.

## 7. Inventario, retroceso, rastro, bitácora y ordenamientos (Persona 3)

Herramienta: no indicada por el integrante.

Fecha: no indicada. El integrante subió el prompt al repositorio el 2026-10-18, en la rama `Parte-3`. Su trabajo llegó al repositorio entre el 2026-10-16 y el 2026-10-18.

Objetivo: Diseñar, implementar, probar y medir las estructuras de la Persona 3: el inventario (§4.5), el historial reversible con el pergamino de retroceso (§4.6), el rastro del jugador (§4.7), la bitácora de 20 mensajes (§4.8) y los ordenamientos (§4.9).

Prompt utilizado:

```text
Estoy trabajando en el proyecto grupal "CRIPTA — Estructuras de Datos II — II Ciclo 2026": un juego de mazmorra dirigido por eventos, en Python 3.11 o superior, con arquitectura MVC. Somos cuatro integrantes y yo soy la Persona 3. Me toca:
- el inventario;
- el historial reversible con el pergamino de retroceso;
- el rastro del jugador;
- la bitácora de 20 mensajes;
- los algoritmos de ordenamiento;
- sus pruebas y sus mediciones.

El enunciado oficial es la fuente de verdad: no inventes requisitos. Si algo no está definido, dímelo antes de asumirlo y distingue entre requisito y decisión de implementación.

## Restricciones obligatorias

- No usar `dict` como índice, caché ni tabla de búsqueda. Para buscar por clave existe `structures/tabla_hash.py` (`TablaHash` con `insertar`, `obtener`, `contiene`, `eliminar`).
- No usar `sorted()` ni `list.sort()`.
- No usar `collections.deque` ni otra estructura de biblioteca en lugar de la que se evalúa.
- El retroceso no puede guardar copias completas del estado.
- El Modelo no depende de HTTP, archivos ni interfaz.
- Código simple y defendible ante el profesor:
  - identificadores en inglés y docstrings en español sin tildes;
  - un docstring de módulo que explique el problema, la estructura y la complejidad;
  - sin comentarios que expliquen lo obvio.
- No modificar archivos de otros integrantes.

## Interfaces existentes que debes usar (no las modifiques)

- `model/item.py`: `Item` es un dataclass con:
  - `instance_id`, `type_id`, `name`, `item_class`, `weight`, `value`, `attack_bonus`, `defense_bonus`;
  - las constantes `Item.WEAPON = "arma"`, `Item.ARMOR = "armadura"` e `Item.REWIND_SCROLL = "pergamino_retroceso"`.
- `model/player.py`: `Player` tiene `equipped_weapon`, `equipped_armor`, `inventory`, `effective_attack` y `effective_defense`. Los dos últimos suman `attack_bonus` y `defense_bonus` del equipo.
- `model/room.py`:
  - `Room.exits()` devuelve objetos `Exit(direction, destination, door)`;
  - `door.is_open` y `door.closed` dan el estado de la puerta;
  - los ids de sala son enteros.
- `model/game_state.py`: `GameState` tiene `clock` (solo lectura), `next_sequence()` y `rewind_clock_to(time)`.
- `model/event.py`: `Event` tiene `time`, `sequence`, `event_type`, `actor`, `cancelled` y otros campos opcionales. Las acciones de actores usan `event_type == "actor_action"`, y cada actor guarda su evento pendiente en `actor.scheduled_event`.
- `structures/event_queue.py`: `EventQueue` es un montículo binario mínimo por `(time, sequence)`, con `push`, `pop`, `peek`, `cancel(event)` (cancelación diferida), `active_events()` y el método interno `_remove_root()`, que también descarta los cancelados de la raíz.
- `benchmark/utilidades_medicion.py`: `Measurement(name, seconds, detail)`, `calentar_procesador()` y `descripcion_del_equipo()`.

## Lo que hay que implementar

### 1. `structures/circular_log.py` (§4.8)

**`CircularBuffer(capacity)`:**
- arreglo fijo, índice al más antiguo y contador;
- `append(x)` en O(1): si está lleno, sobrescribe el más antiguo y lo devuelve;
- `last()`, `pop_last()`, `clear()`, `is_empty()`, `is_full()`, `capacity`, `len()`;
- recorrido del más antiguo al más reciente;
- `ValueError` si la capacidad es menor que 1 e `IndexError` si está vacío.

**`CircularLog(capacity=20)`:**
- hereda de `CircularBuffer` y guarda los mensajes como `str`;
- debe servir como `message_log` de `Game`, que solo pide `append()` y poder recorrerla.

Requisitos: memoria constante y sin desplazar físicamente los 19 mensajes anteriores.

### 2. `structures/sorting.py` (§4.9)

**Funciones:** `insertion_sort`, `merge_sort` y `sort(data, key=identity, reverse=False, counter=None)`.
- Todas son estables, aceptan `reverse` y devuelven una lista nueva sin modificar la entrada.
- La clave se calcula una sola vez por elemento: se ordenan pares `(clave, elemento)`.
- `ComparisonCounter` cuenta comparaciones (`comparisons`) y anota en `algorithm` qué usó `sort`.

**Cómo elige `sort`:**
1. Con n ≤ `SMALL_THRESHOLD` (32), usa inserción.
2. Si no, cuenta los "descensos" en una pasada. Si superan n × `NEARLY_SORTED_RATIO` (0.05), usa mezcla.
3. Si no, intenta inserción con un tope de `shift_budget(n) = n * n.bit_length()` desplazamientos. Si lo supera, termina con mezcla sobre lo que quedó.

El tercer paso protege contra datos "rotados" como `[5, 6, 7, 8, 9, 0, 1, 2, 3, 4]`: tienen un solo descenso, pero inserción los ordena en O(n²).

**Funciones auxiliares:** `choose_algorithm(size, descents)` y `algorithm_for(data, key, reverse)`.

**Constantes:** `INSERTION`, `MERGE` e `INSERTION_THEN_MERGE`.

### 3. `structures/history.py` (§2.11, §4.6)

**Clases de cambio:**
- `Change` es la base, con `undo()`.
- `AttributeChange(target, attribute, previous)` restaura un atributo con `setattr`, así que también funciona con propiedades.
- `CallbackChange(function, *args)` ejecuta la operación inversa.

**`History(state, max_actions=5)`:**
- `begin_action()`: abre un intervalo que guarda `state.clock`. Los intervalos van en un `CircularBuffer(5)`, así que el sexto descarta el más antiguo.
- `record(change)`: anota solo si hay un intervalo abierto y no se está deshaciendo.
- `assign(target, attribute, value)`: anota el valor anterior y después asigna.
- `list_append(items, x)` y `list_pop(items, index)`: hacen la operación y anotan su inversa.
- `undo()`: saca el último intervalo, aplica sus cambios en orden inverso y devuelve el reloj con `state.rewind_clock_to()`. Mientras deshace no anota nada. Devuelve `False` si no hay intervalos.
- También: `can_undo()`, `available_actions()`, `is_recording`, `is_undoing`, `recorded_changes()` y `clear()` (para cuando se carga una partida).
- No restaura el contador de secuencia ni el generador aleatorio.

**`ReversibleEventQueue(history)`**, subclase de `EventQueue` que anota sola la inversa de cada operación:

| Operación | Inversa anotada |
| --- | --- |
| `push(e)` | marcar `e` como cancelado y limpiar `scheduled_event` si apuntaba a `e` |
| `_remove_root()` (pop y descartes internos) | reinsertar `e` con su mismo `time` y `sequence`, y restaurar `actor.scheduled_event` si es una acción de actor no cancelada |
| `cancel(e)` | restaurar `e.cancelled` y `actor.scheduled_event` |

**`use_rewind_scroll(inventory, history)`:**
- si no hay pergamino o no hay nada que deshacer, devuelve `False` sin tocar nada;
- si no, primero deshace y después consume el pergamino, para que el consumo quede fuera del intervalo revertido.

### 4. `structures/inventory.py` (§2.7, §4.5)

**`DoublyLinkedList`:**
- lista doble con dos nodos centinela;
- nodos `_Node(item)` con `previous`, `next` y `linked`;
- operaciones: `append`, `push_front`, `insert_after`, `insert_before`, `remove`, `move_to_front`, `first`, `next_of`, `previous_of` y `nodes()`;
- recorrido en los dos sentidos;
- `ValueError` si se quita un nodo que no está en la lista o se inserta uno que ya está.

**`Inventory(capacity, history=None)`:**
- Recorrerlo devuelve los `Item` en el orden real, porque el motor busca llaves recorriendo `player.inventory`.
- `is_full()`; `pick_up(item)` agrega al final, deja el cursor sobre el objeto recogido y devuelve `False` si está lleno, sin mover el cursor.
- `current()`, `next()`, `previous()` y `go_to_start()`: el cursor es una referencia al nodo actual.
- `drop_current(player)`, en O(1) en cualquier posición:
  - devuelve el objeto quitado;
  - si estaba equipado, lo desequipa en `player`;
  - el cursor pasa al siguiente, o al anterior si se soltó el último.
- `can_equip_current()` y `equip_current(player)`:
  - mueve el objeto al frente;
  - actualiza `player.equipped_weapon` o `player.equipped_armor`;
  - devuelve el objeto sustituido, que queda en el inventario, o `None`;
  - lanza `ValueError` si no es arma ni armadura.
- `sorted_view("peso" | "valor" | "nombre", reverse=False)`: copia ordenada con `sort()`, sin alterar el orden real. El nombre se compara en minúsculas.
- `scroll_count()` y `consume_scroll()`. Los pergaminos ocupan espacio.

**Con `history`:**
- Cada cambio anota su inversa.
- Al deshacer un `soltar` o un `equipar`, el nodo vuelve a su posición junto a sus vecinos de antes. Si el vecino anterior ya no está, usa el siguiente, y si tampoco está, va al final. Al deshacer un soltar, el cursor vuelve al objeto restaurado.
- El equipo se cambia con `history.assign`.
- Los movimientos de pergaminos de retroceso **no** se anotan (§2.11).

### 5. `structures/trail.py` (§2.9, §4.7)

**`PlayerTrail(history=None)`:** guarda id de sala → instante en una `TablaHash`. `TRAIL_LIFETIME = 400`.
- `mark(room_id, time)`: si hay historial, anota el valor anterior, o que la sala no tenía entrada.
- `time_at(room_id)` e `is_fresh(room_id, now)`, con la condición `now - time < 400`.
- `freshest_exit(room, now)`:
  - recorre `room.exits()` e ignora las puertas cerradas y los rastros caducados;
  - devuelve el `Exit` con el instante más alto, o el de menor id de sala si hay empate;
  - devuelve `None` si no hay ninguno.

La caducidad se detecta al consultar; no se eliminan rastros. El costo es O(salidas). El motor marca la sala con el reloj del instante en que se ejecuta cada acción aceptada, y también al iniciar la partida.

## Pruebas (`unittest`, desde `cripta/` con `python -m unittest discover -s tests -t .`)

Para cada módulo, cubre:
- casos normales;
- vacíos;
- límites, como capacidad exacta, 20 y 21 mensajes, frescura en 399 y en 400, n = 32 y 33;
- errores;
- el máximo de 5 retrocesos.

Además, estos casos del Apéndice B y de §2.11:
- recoger con el inventario lleno;
- empate de rastros, que gana la sala de menor id;
- recoger o soltar un pergamino dentro del intervalo revertido;
- dos pergaminos seguidos;
- el ejemplo del enunciado: ataque en t=100, veneno, ataque de la rata, rearme de una trampa y pergamino en t=200. Después del retroceso deben volver la vida de los dos, la trampa, el reloj y el rastro.

Para el ordenamiento, prueba también:
- estabilidad, incluso después de cambiar de inserción a mezcla;
- que datos rotados de 2048 elementos terminen con `INSERTION_THEN_MERGE`;
- que los casi ordenados se queden con inserción.

Incluye además `tests/verificar_retroceso.py`, un ayudante solo para pruebas:
- `snapshot(game, trail)` devuelve una lista de pares (campo, valor) con el reloj, el resultado, la antorcha, los contadores, la vida, sala, velocidad, equipo y evento pendiente de cada actor, puertas, trampas y suelo de cada sala, orden real del inventario, eventos activos de la agenda y efectos;
- deja fuera los pergaminos, la bitácora, el contador de secuencia y el cursor;
- `differences(antes, despues)` devuelve los campos que cambiaron;
- `assert_rewind_restores(testcase, game, action, trail)` falla nombrando el campo exacto que no se restauró.

## Mediciones (`benchmark/persona3_bench.py`, función `run()` que devuelve `Measurement`)

Mide estas operaciones, incluyendo siempre la alternativa descartada:
- la bitácora frente a `list` + `pop(0)`;
- soltar al inicio, en medio y al final con n = 10, 100, 1000 y 10 000, frente a `list.pop(i)`;
- recorrer el inventario y las vistas ordenadas;
- los tres ordenamientos con datos aleatorios, casi ordenados (1 % de intercambios), invertidos, rotados y cadenas largas con prefijo común, para n de 4 a 4096, reportando comparaciones y qué usó `sort`;
- el rastro con 1, 10, 100 y 1000 rastreadores;
- el historial con 1, 10, 100 y 1000 cambios por acción;
- `ReversibleEventQueue` frente a `EventQueue` (300 eventos, 20 000 extracciones).

Agrega también:
- `benchmark/persona3_frecuencias.py`: cuenta cuántas veces se ejecuta cada operación por decisión del jugador, con el motor real y versiones con contadores del historial, el rastro y la bitácora;
- `benchmark/persona3_corridas.py`: corre todo 3 veces y guarda las corridas y las medianas en `docs/mediciones/persona3/`.

**No inventes cifras.** Reporta lo que salga, aunque la alternativa descartada resulte más rápida a tamaños pequeños; en ese caso, la justificación es el requisito.

## Cómo trabajar

Ve por etapas: análisis, diseño, interfaces, implementación, pruebas, integración, benchmark y documentación. Empieza con el análisis y el diseño de cada estructura:
- qué problema resuelve;
- qué operaciones necesita;
- al menos dos alternativas y por qué se descartan;
- complejidad temporal y espacial;
- qué medición lo demostraría.

Explícame en palabras sencillas lo que sea complicado y espera mi confirmación antes de generar el código completo. Todo lo que generes es una propuesta que yo voy a revisar y que debo poder defender ante el profesor.
```

Uso en el proyecto: `structures/inventory.py`, `structures/history.py`, `structures/trail.py`, `structures/circular_log.py` y `structures/sorting.py`, con sus pruebas en `tests/` (incluido el ayudante `tests/verificar_retroceso.py`), los benchmarks `benchmark/persona3_bench.py`, `benchmark/persona3_frecuencias.py` y `benchmark/persona3_corridas.py`, las mediciones de `docs/mediciones/persona3/` y las secciones 4.5 a 4.9 de `docs/DECISIONES.md`.

Cambios realizados por el estudiante: El prompt pide expresamente ir por etapas, esperar confirmación antes de generar el código completo y tratar todo lo generado como una propuesta para revisar. Las mediciones mostraron un defecto en la primera versión de la selección de `sort`: con datos rotados escogía inserción y llegaba a tardar 64 veces lo que tarda mezcla. Se corrigió subiendo el umbral a 32 y agregando el tope de desplazamientos, y se volvió a medir. Ambas versiones quedaron documentadas en §4.9 del Documento de Decisiones.

### 2.24 Arranque de la segunda parte: reparto, spec-kit y constitución

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-11-16

Objetivo: Repartir el trabajo de la segunda parte entre los cuatro integrantes, instalar spec-kit sobre el repositorio existente y redactar la constitución que exige §2.3 del enunciado.

Prompts utilizados:

```text
Ok, perfecto. ¿Ya viste la decisión o ya leíste, me imagino, el segundo proyecto EDI, el Markdown que te voy a marcar aquí como contexto? Y después de eso quisiera que me dijeses cómo dividirlo en los cuatro compañeros, que somos del grupo, ya sea Steven, Eric, y Mauricio, y yo que también soy Mauricio, pero mi nombre es Carlos Mauricio. Quisiera que lo dijeses en las cuatro para que todo eso sea lo más fácil posible y que lo dividas de forma equitativa, ya sea en tiempo y en esfuerzo, y en complejidad. Esto para que nadie se pueda quejar de que le tocó una parte más peor que otra. [...] y que también me dices como especificaciones y un prompt si puedes para pasárselo a mis compañeros
```

```text
Sí, dale, instalá spec-kit y hacé la constitución
```

Uso en el proyecto: `docs/REPARTO_PROYECTO2.md`, `docs/PROMPT_SDD_PARA_EL_GRUPO.md`, `.specify/memory/constitution.md` y la sección nueva del `README.md`.

Cambios realizados por el estudiante: Se revisó el estado real del repositorio antes de planificar y se encontró que no había ningún avance de la segunda parte: sin commits desde el 28 de octubre, sin spec-kit inicializado y con el enunciado sin subir, a dos días de la entrega. Se decidió, pese a la advertencia sobre el riesgo, intentar las cuatro capacidades completas en vez de reducir el alcance. El reparto se hizo siguiendo lo que cada integrante ya dominaba de la primera parte, para no gastar tiempo en volver a aprender módulos ajenos, y se compensó el desbalance de pesos de la rúbrica asignando a la Persona 4 las banderas nuevas de todo el equipo, la integración de `--bench` y el README. Se identificó además el orden que desbloquea al resto: la constitución la sube una sola persona porque `specify init` escribe en la raíz, y los campos nuevos del traductor son prerrequisito de las otras tres capacidades. Se fijó spec-kit en la versión v1.4.1, la más reciente publicada, y se descubrió que el enunciado menciona la bandera `--ai`, que corresponde a la versión 1.1 y que en la 1.4.1 se llama `--integration`. La constitución se redactó con los siete principios que pide §2.3, en palabras del grupo y apoyados en lo que la primera parte ya hacía, y se agregó la lista concreta de dependencias prohibidas para que el agente la tenga presente en la fase de plan y no al implementar. También se detectó que el enunciado remite a una sección 2.7 que no existe en el documento, lo que quedó como pregunta para el profesor.

### 2.25 Especificación de terreno con /speckit.specify

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-11-16

Objetivo: Escribir la primera especificación de la segunda parte, la del costo de tránsito de las salidas (§3.1), siguiendo el flujo obligatorio de spec-kit.

Prompts utilizados:

```text
/speckit.specify Terreno: costo de tránsito de las salidas.

Contexto: segunda parte del proyecto CRIPTA, juego de mazmorra dirigido por eventos con reloj virtual. El enunciado completo está en cripta/docs/SegundoProyecto-EDII-2026.md; esta capacidad corresponde a su sección 3.1 y al caso 6 y 7 del Apéndice B bajo "Terreno y cazador".

Cada salida de una sala puede declarar un campo "costo", entero mayor o igual que 1. Si la salida no lo declara, su costo es 100. El costo es el mismo en ambos sentidos. Moverse a través de una salida pasa a ser una acción cuyo costo base es el costo de esa salida, en lugar del valor fijo 100. El intervalo se sigue calculando con la fórmula de la primera parte. La regla aplica a todos los actores. El costo de las demás acciones no cambia y los comportamientos de enemigo existentes conservan su lógica. La vista debe mostrar el costo de las salidas de la sala actual.

[El prompt completo incluye los escenarios de aceptación obligatorios del Apéndice B, la justificación de separar terreno del cazador, las dependencias prohibidas y los requisitos de rendimiento heredados.]
```

Uso en el proyecto: `specs/001-terreno-costo-salidas/spec.md` y su lista de verificación.

Cambios realizados por el estudiante: Se decidió separar el terreno del cazador en dos especificaciones distintas, aunque el enunciado las presente como una sola capacidad. La razón es de orden de trabajo y queda escrita en la especificación: el costo de las salidas es infraestructura de la que dependen el cazador, el viaje automático y las mediciones, así que entregarlo por separado desbloquea a los otros integrantes en vez de que esperen al cazador completo; el enunciado permite dividir una capacidad si se justifica. Al revisar la especificación contra su propia lista de verificación se detectó que la fórmula del intervalo estaba escrita con sintaxis de Python, y se reformuló como división entera para que no dependiera de ningún lenguaje. Se dejaron explícitamente fuera del alcance dos cosas que pertenecen a otras capacidades: qué conoce el jugador del costo de una salida que no ha explorado, que es de la niebla de guerra, y cómo se calculan rutas de costo mínimo, que es del cazador y del viaje automático.

### 2.26 Plan, tareas e implementación del terreno

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-11-16

Objetivo: Completar el flujo de spec-kit para la primera capacidad: planificar el costo de tránsito de las salidas, descomponerlo en tareas e implementarlo.

Prompts utilizados:

```text
sí, dale, hacé el plan y las tareas e implementalo
```

Uso en el proyecto: `specs/001-terreno-costo-salidas/plan.md` y `tasks.md`; `model/room.py`, `model/game.py`, `repository/traductor.py`, `controller/application.py`, `view/console_view.py`, `benchmark/scheduler_bench.py` y las pruebas de `tests/test_room.py`, `tests/test_traductor.py`, `tests/test_movement.py` y `tests/test_actor.py`.

Cambios realizados por el estudiante: La decisión de diseño fue guardar el costo en la puerta y no en la salida. La puerta ya era un único objeto compartido por las dos salas que conecta, así que el requisito de que el costo sea igual en ambos sentidos se cumple por construcción en vez de depender de una validación. Se descartaron guardar el costo en la salida, que obligaría a validar a mano que las dos direcciones coincidan, y guardarlo en una estructura aparte indexada por par de salas, que sería un índice y la sección 7 lo prohíbe. Se reutilizó el mecanismo que el traductor ya tenía para cuando los dos lados de una puerta declaran valores distintos, el mismo que usa para la llave y el cierre automático, en vez de inventar una regla nueva. Al revisar lo implementado se encontró un error propio: se estaba comparando el costo efectivo de la puerta, que siempre trae el valor por omisión, en vez del costo declarado, de modo que si un solo lado declaraba costo el traductor avisaba de una discrepancia inexistente; se corrigió guardando el valor declarado junto a la puerta pendiente de emparejar. También se eliminó la constante del costo de movimiento del motor, que quedaba repitiendo el mismo 100 que ya define el modelo, porque era el riesgo anotado en el propio plan. Dos requisitos resultaron ya satisfechos por el diseño de la primera parte, el intervalo mínimo de una unidad y el reescalado al cambiar de velocidad, así que sus tareas fueron demostrarlo con pruebas y no implementarlo. La medición cerró el ciclo: 0.1912 ms por ciclo con costos uniformes contra 0.1897 ms con costos variables, o sea que el cambio no cuesta nada medible.

### 2.27 Especificación del cazador con /speckit.specify

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-11-16

Objetivo: Escribir la segunda especificación de la segunda parte, la del cazador y su ruta de costo mínimo (§3.2, §5.1 y §5.2), siguiendo el flujo obligatorio de spec-kit.

Prompts utilizados:

```text
sí, subilo a las dos y seguí con el cazador
```

```text
/speckit.specify El cazador: un enemigo que persigue al jugador por la ruta más barata.

Se agrega un cuarto comportamiento de enemigo, "cazador", junto a guardián, errante y rastreador. Su ficha de catálogo incluye un campo "rango", entero en unidades de costo. En su turno: si comparte sala con el jugador ataca; si no, considera el costo mínimo d de llegar hasta la sala del jugador sumando el costo de cada salida y usando solo salidas abiertas en ese instante; si no existe ruta o d es mayor que su rango, espera con costo 100; si existe, se mueve un paso por una ruta de costo d.

Desempate obligatorio: entre las vecinas v tales que costo(u,v) + distancia(v, jugador) = d, se mueve a la de menor id. Conoce el esqueleto completo y el estado actual de las puertas; no le afecta la niebla de guerra y no abre puertas cerradas. Equivalencia observable: su decisión en cada turno debe ser idéntica a la de un cálculo desde cero en ese instante.

[El prompt completo incluye los cinco casos del Apéndice B que faltaban, los requisitos de rendimiento de §5.1 y §5.2, lo que queda fuera por pertenecer a otros integrantes, y las estructuras propias que ya existen en el repositorio.]
```

Uso en el proyecto: `specs/002-cazador-ruta-mas-barata/spec.md` y su lista de verificación.

Cambios realizados por el estudiante: Antes de escribir la especificación se leyó el enunciado de la segunda parte y el código de los tres comportamientos existentes, para no inventar reglas y para saber qué colaboradores recibe un enemigo en su turno. Se resolvieron como supuestos documentados, en vez de dejar marcadores de aclaración, tres puntos que el enunciado no dice de forma literal: que un rango igual al costo de la ruta sí permite perseguir, porque el enunciado dice que el cazador espera cuando el costo es «mayor» que el rango; que un rango ausente o inválido es un error de datos de cripta, con el mismo criterio que la capacidad anterior aplicó al costo de las salidas; y que un rango de 0 es una ficha válida que simplemente nunca persigue. Se dejó explícitamente fuera del alcance la niebla de guerra y el viaje automático, que son de otros integrantes, con la nota de que el viaje automático calcula rutas sobre el mapa conocido y no sobre el real, de modo que compartir implementación es decisión de su propio plan.

### 2.28 Revisión de consistencia con /speckit.analyze y corrección de la especificación

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-11-16

Objetivo: Revisar la consistencia entre la especificación, el plan y las tareas del cazador antes de implementar, como pide §2.2 del enunciado, y corregir lo que apareciera.

Prompts utilizados:

```text
/speckit.analyze Revisar la consistencia entre spec.md, plan.md y tasks.md de specs/002-cazador-ruta-mas-barata, y contra .specify/memory/constitution.md, antes de implementar.
```

Uso en el proyecto: la corrección de `specs/002-cazador-ruta-mas-barata/spec.md` en una confirmación propia, antes del código, y el ajuste del plan y de las tareas.

Cambios realizados por el estudiante: La revisión encontró seis problemas reales y se corrigieron todos antes de escribir código, en el orden que exige el principio VII de la constitución: primero la especificación y en su propia confirmación. Dos de ellos eran contradicciones entre documentos escritos por uno mismo. Primero, un criterio de éxito decía que ninguna prueba anterior se modificaría, mientras una tarea decía que las del guardado binario sí cambiarían al subir la versión del formato; se acotó la excepción en el criterio. Segundo, un requisito exigía que el costo de la decisión dependiera del rango de cada cazador, sin admitir que un cálculo compartido entre varios abarca el rango mayor; se agregó esa salvedad y la obligación de medir el sobrecosto, que después resultó ser de diecisiete veces. Tercero, el desempate estaba escrito sobre salas vecinas, pero dos salidas distintas pueden llevar a la misma vecina con costos distintos, así que el costo entre dos salas no estaba definido; se fijó que cuenta la más barata. Cuarto, «decenas de cazadores» no era verificable y se fijó en 50. Además se detectó que la revisión misma incumplía la constitución: faltaba registrar en este archivo las invocaciones de spec-kit de esta capacidad, y se agregó una tarea para ello. Y se anotó como riesgo que la firma de la decisión del enemigo tiene diez llamadas directas en las pruebas, varias posicionales, de modo que el colaborador nuevo tenía que entrar al final y con valor por omisión.

### 2.29 Plan, tareas e implementación del cazador

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-11-16

Objetivo: Completar el flujo de spec-kit para la segunda capacidad: planificar la ruta de costo mínimo del cazador, descomponerla en tareas, implementarla y medirla.

Prompts utilizados:

```text
/speckit.plan Planificar specs/002-cazador-ruta-mas-barata. Decidir con qué estructuras propias se calcula la ruta de costo mínimo del cazador, respetando la prohibición de dict como índice, set, heapq, bisect, collections y bibliotecas de grafos. Evaluar y documentar como alternativas: Dijkstra por cazador con corte por rango reutilizando el montículo binario de la agenda de eventos; un único cálculo compartido desde la sala del jugador para todos los cazadores activos; y recalcular siempre desde cero. Planificar las mediciones que exigen §5.1 y §5.2.
```

```text
/speckit.tasks Generar tasks.md para specs/002-cazador-ruta-mas-barata a partir de su plan.md. Tareas pequeñas y verificables, cada una con los requisitos que atiende y sus dependencias. Incluir las tareas de medición de §5.1 y §5.2 y la prueba de equivalencia contra el modo de recalcular siempre.
```

Uso en el proyecto: `specs/002-cazador-ruta-mas-barata/plan.md` y `tasks.md`; `structures/rutas_mas_baratas.py`, `model/enemy.py`, `model/game.py`, `repository/traductor.py`, `adapters/almacen_partida.py`, `benchmark/bench_cazador.py`, `benchmark/scheduler_bench.py`, `benchmark/benchmark.py` y las pruebas de `tests/test_rutas_mas_baratas.py`, `tests/test_cazador.py`, `tests/test_traductor.py` y `tests/test_almacen_partida.py`.

Cambios realizados por el estudiante: La decisión de diseño fue buscar desde la sala del jugador y no desde la del cazador. El desempate del enunciado está escrito como costo(u, v) más distancia(v, jugador), así que buscar desde el jugador entrega ese número para todas las vecinas de golpe; además el grafo no tiene dirección, porque el costo de una salida es el mismo en ambos sentidos y una puerta abierta lo está para los dos lados, de modo que una sola búsqueda sirve a todos los cazadores activos. Buscando desde cada cazador habría que reconstruir rutas para recuperar la distancia de cada vecina y compartir trabajo sería imposible. No se escribió ninguna estructura nueva: la cola de prioridad es el montículo binario de la agenda de eventos, que ordena por el par (instante, secuencia) y al que se le entregan pares (distancia, id de sala), de modo que ordena por distancia y desempata por id sin tocarlo; las distancias y las salas asentadas van en la tabla hash del grupo. El desempate se aplica aparte, sobre las vecinas de la sala consultada, y no se deja al orden de expansión del montículo; hay una prueba con una topología donde el orden de expansión y el id dan respuestas distintas, para que una implementación que confíe en el montículo falle.

Se encontraron cuatro errores propios al implementar y medir, todos corregidos. Primero, un ayudante de prueba activaba a los cazadores poniéndoles el campo a mano, y resulta que es el camino de activación del motor el que también los programa en la agenda: varias pruebas de ciclo completo pasaban en vano porque el cazador nunca tomaba un turno. Se cambió para activarlos por el camino del motor y se comprobó que ahora sí se mueven. Segundo, la prueba de equivalencia decía ejercitar cierres automáticos frecuentes y no ejercitaba ninguno, porque un cierre automático solo se programa cuando alguien abre la puerta; se reescribió para que el jugador abra puertas y se verificó que la invalidación se dispara, con una comprobación dentro de la prueba de que hubo más de una búsqueda. Tercero, la medición del corte por rango salía plana también sin corte, y el motivo era que la cripta sintética nace con una puerta cerrada de cada tres, así que la región alcanzable era de dos salas por grande que fuera la cripta: no se medía el corte sino el bloqueo. Se parametrizó el generador y, bien medida, quitar el corte multiplica el costo de la decisión por 320. Cuarto, se identificó un punto de invalidación que el plan no había previsto: el pergamino de retroceso revierte el historial, así que puede cambiar la sala del jugador y el estado de las puertas de golpe.

El hallazgo principal de las mediciones contradice lo que el plan esperaba, y así quedó escrito. El plan suponía que el ahorro vendría de reutilizar el cálculo entre turnos cuando las puertas están quietas. No es así: el jugador se mueve casi en cada decisión, y moverse invalida, de modo que el cálculo se rehace 297 veces en 300 decisiones. El ahorro real viene de compartir una sola búsqueda entre todos los cazadores del mismo instante, de 3902 búsquedas a 297. Eso cambia cuál es la justificación de la decisión: lo que vale no es la caché, es haber buscado desde el jugador en vez de desde cada cazador, porque si se buscara desde cada cazador compartir sería imposible. Con cincuenta cazadores activos el ciclo completo de eventos queda en 0.1854 ms, contra 0.1897 ms sin cazadores: la persecución de cincuenta enemigos no mueve la aguja. Por último, el bloque de enemigo del archivo de partida tuvo que guardar el rango, lo que subió la versión del formato de 1 a 2; sus pruebas usaban la constante y no el número, así que ninguna hubo que reescribir.

### 2.30 Especificación, plan y tareas de la línea de tiempo

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-11-16

Objetivo: Desarrollar la cuarta capacidad del proyecto, la línea de tiempo (§3.6 y §5.5), con el flujo completo de spec-kit.

Prompts utilizados:

```text
Ok, Claude, ayúdame y si quieres, avanza más todavía, tipo, haz la línea del tiempo y avanza al siguiente paso que creas y luego me dices lo que tengo que dejarle al grupo en general, como para decirle, ok, voy por aquí, para que ellos sí vayan avanzando.
```

```text
/speckit.specify La línea de tiempo: consultar el estado de la partida en cualquier instante pasado.

El pergamino de retroceso sigue limitado a 5 acciones. La línea de tiempo es independiente: permite consultar, sin modificar la partida, el estado en cualquier instante desde el inicio. El estado en el instante t es el estado después de ejecutar todos los eventos con tiempo menor o igual que t; si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla.

El comando "historia <t>" o "historia #k" muestra reloj, sala, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida, y el mapa conocido. La consulta no consume tiempo virtual, no se registra como acción y no altera ningún estado del juego ni del historial de retroceso. Las acciones revertidas con un pergamino dejan de existir en la línea. Consultar un instante posterior al reloj actual se rechaza.

Se permite guardar copias completas del estado, no más de una cada K acciones del jugador. Una consulta no puede requerir aplicar o deshacer cambios de más de K acciones. Guardar y cargar conserva la línea completa.

[El prompt completo incluye los dos casos del Apéndice B, los cinco requisitos de rendimiento de §5.5, lo que queda fuera por ser de otros integrantes, y las estructuras propias que ya existen en el repositorio.]
```

```text
/speckit.plan Planificar specs/003-linea-de-tiempo. La decisión central es cómo se reconstruye el estado de un instante pasado: el enunciado permite reconstruir hacia adelante desde un punto de control re-simulando, o hacia atrás desde el estado actual invirtiendo cambios. Evaluar y documentar las dos, más la alternativa ingenua de una copia completa por acción. Tener en cuenta que el historial reversible guarda cambios inversos pero solo de las últimas 5 acciones, y que sus objetos Change guardan referencias directas a los objetos vivos, de modo que no se pueden aplicar a una copia. Tener en cuenta que el guardado binario ya serializa el estado completo incluido el estado del generador aleatorio. Planificar la búsqueda del punto de control más cercano con búsqueda binaria propia, porque bisect está prohibido. Planificar las mediciones de memoria y tiempo de consulta para al menos tres valores de K y la justificación del valor por omisión.
```

```text
/speckit.tasks
```

```text
sigue
```

Uso en el proyecto: `specs/003-linea-de-tiempo/spec.md`, `plan.md`, `tasks.md` y su lista de verificación; `structures/linea_de_tiempo.py`, `model/consulta_historia.py`, `model/game.py`, `adapters/almacen_partida.py`, `controller/commands.py`, `controller/application.py`, `view/console_view.py`, `benchmark/bench_linea_de_tiempo.py`, `docs/INTERFAZ_LINEA_DE_TIEMPO.md` y las pruebas de `tests/test_linea_de_tiempo.py`.

Cambios realizados por el estudiante: La decisión de diseño fue reconstruir hacia adelante desde una copia completa, y el motivo no fue de preferencia sino de código. Antes de planificar se revisó el historial reversible de la primera parte y se encontró que sus objetos de cambio guardan referencias directas a los objetos vivos; como acotar una consulta a K acciones obliga a partir de una copia, y una copia reconstruida crea objetos nuevos, los cambios inversos no se les pueden aplicar. Reconstruir hacia atrás habría exigido restaurar el estado vivo campo por campo sin cambiar la identidad de ningún objeto, lo que es mucho más riesgoso que lo que resuelve. Hacia adelante, en cambio, todo lo necesario ya estaba escrito: el serializador completo guarda el estado del generador aleatorio y el cargador construye objetos nuevos sin rehacer el trabajo de inicio de partida, así que la consulta no puede alterar la partida viva por construcción y no por cuidado. Un punto de control es ese mismo bloque de bytes guardado en memoria, lo que obligó a separar en el adaptador el armado del contenido de su escritura en disco; ese refactor no cambió ningún comportamiento y las 54 pruebas del guardado siguieron pasando sin tocarlas. La búsqueda del punto de control del que partir y la traducción de un instante a un número de acción son búsquedas binarias escritas a mano, porque bisect está prohibido.

Durante la planificación se encontró el que iba a ser el problema central: el pergamino de retroceso devuelve el reloj a su valor anterior pero no devuelve el estado del generador aleatorio, que es una decisión deliberada y documentada de la primera parte. Re-simular habría divergido después de cada pergamino y los resúmenes de los instantes posteriores habrían sido falsos sin que nada se viera raro. La primera respuesta fue anotar el estado del generador una vez por pergamino usado, que son unos 5 KB frente a una copia completa. La prueba de equivalencia tumbó esa idea: un pergamino además consume un pergamino del inventario, y ese consumo no es una acción del jugador, así que no está en la lista que la re-simulación repite. El anclaje alineaba el azar y dejaba el inventario mal. La respuesta correcta resultó más simple de explicar: un pergamino es un punto donde el estado vivo no se puede derivar de la lista de acciones, así que la línea se re-ancla con una copia completa. El mecanismo del anclaje se retiró del código en vez de dejarlo sin uso, y la desviación respecto del presupuesto de una copia cada K acciones quedó declarada en el plan con su justificación: entre correcto y dentro del presupuesto de memoria, manda correcto.

La misma prueba de equivalencia destapó un defecto ajeno a esta capacidad: el archivo de partida nunca guardaba el costo de las salidas. La capacidad 001 lo agregó al modelo y no al guardado, así que guardar y cargar devolvía todas las salidas a costo 100 en silencio, y no había prueba que lo cubriera porque el costo se agregó después del guardado. Es el argumento más fuerte a favor de esta capacidad: reconstruir el pasado obliga a que el estado se serialice completo, y eso delata cualquier campo que falte. También se evitó un error de diseño que habría crecido en silencio: si una copia llevara la línea de tiempo dentro, cada copia contendría las anteriores y el tamaño crecería de forma exponencial; por eso el bloque global se arma con la línea cuando es un archivo de partida y sin ella cuando es una copia, y hay una prueba que lo comprueba.

Se corrigieron además tres errores propios en las pruebas, todos detectados al comparar contra el estado real: el ayudante guardaba el estado posterior a una espera en vez del anterior cuando una acción se rechazaba; los objetos extra del inventario se agregaban después de que se tomaba la copia inicial, por fuera del flujo registrado, lo que era un defecto de la prueba y no del programa; y la medición del costo de una consulta frente al largo de la partida consultaba siempre la última acción, que cae justo después de una copia y casi no repite nada, de modo que salía plana por el caso más fácil sin probar nada. Es el mismo error que ya había aparecido en la capacidad del cazador. Se cambió a puntos repartidos y entonces sí midió lo que decía medir.

El valor por omisión de K quedó en 50, elegido con las mediciones como exige el enunciado. La alternativa ingenua de una copia por acción cuesta 43 veces más memoria para ganar menos de 0.6 ms por consulta. Entre los valores razonables el argumento resultó ser de latencia y no de memoria: con 98 KiB la memoria ya es irrelevante en términos absolutos, así que lo que queda por optimizar es cuánto tarda una consulta, y K de 200 ahorra 71 KiB que nadie nota y duplica el tiempo. También quedó anotado que esas cifras son de una cripta de 40 salas y que la memoria de las copias crece con el tamaño de la cripta, más la optimización evidente que no se hizo a propósito: guardar en la copia solo el estado mutable y no el esqueleto, que no cambia nunca. Se prefirió reutilizar el serializador ya probado antes que escribir un segundo serializador, y el costo está medido.

### 2.31 Cierre: el Documento de Decisiones y la vista del cazador

Herramienta: Claude (Claude Opus 5), mediante la extensión de Claude Code para VS Code

Fecha: 2026-11-17

Objetivo: Escribir las secciones de la segunda parte del Documento de Decisiones de Diseño (§7.1) y cerrar el último pendiente propio.

Prompts utilizados:

```text
hacé el documento de decisiones
```

```text
Ok, sí, perfecto. Termina con lo mío
```

Uso en el proyecto: las secciones 5.1, 5.2, 5.5 y 5.6 de `docs/DECISIONES.md`; el requisito FR-019 y la Historia 6 de `specs/002-cazador-ruta-mas-barata/spec.md`; `view/console_view.py` y `tests/test_console_view.py`.

Cambios realizados por el estudiante: Antes de escribir se revisó cómo había titulado su sección el compañero que escribe la 5.3, para usar la misma convención y que al juntar las ramas el conflicto fuera trivial de resolver. Las secciones 5.3 y 5.4 quedaron con una nota de a quién pertenecen y qué les falta, siguiendo la convención que el documento ya usaba para las secciones de la primera parte sin escribir.

Lo que §7.1 pide y más suma es indicar si la decisión final coincide con la del plan original. Dos no coinciden y las dos quedaron escritas con lo que motivó el cambio. En §5.2 la decisión se mantiene pero la justificación cambió: el plan esperaba que el ahorro viniera de reutilizar el cálculo cuando las puertas están quietas, y la medición mostró 252 búsquedas en 300 decisiones, porque el jugador se mueve y moverse invalida; el ahorro real es compartir una búsqueda entre los cazadores del mismo instante. En §5.5 la idea de anotar solo el estado del generador en cada pergamino la tumbó la prueba de equivalencia, porque el pergamino también consume un pergamino del inventario.

Para la §5.6 se repitieron las mediciones de la primera parte con la carga nueva, como exige el enunciado. El montículo de la agenda sigue siendo 6.5 veces más rápido que la lista sin ordenar que se había descartado, así que esa decisión no cambia; se anotó además que los cazadores no agregan eventos a la agenda, solo cambian a dónde se mueven, de modo que la carga sobre la agenda crece con los actores y no con el terreno.

Al revisar la capacidad contra §7.3 se encontró que la vista debía distinguir a los cazadores de los demás enemigos y que ninguna especificación lo cubría: el dato ya estaba en la vista de enemigo del motor, pero la vista no lo pintaba distinto. Se agregó el requisito a la especificación del cazador, con su historia, sus escenarios, un caso borde y un criterio de éxito, en una confirmación aparte y antes de tocar el código. Ese orden se eligió a propósito porque es el ejercicio que §7.4 anuncia para la defensa: pedir un cambio pequeño a una regla y mostrar primero la modificación de la especificación y luego la del código.

También se actualizó el resumen de pruebas del Documento, que fijaba 861 como si fuera definitivo. Ahora reporta 1 029 con el desglose por capacidad y explica que la cifra sube al juntar las ramas, de modo que lo que queda fijo es la regla —que ninguna prueba deje de pasar— y no el número.

### 2.30 Niebla de guerra e «ir a»: análisis del repositorio, /speckit.specify y /speckit.clarify

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Entender el estado real del repositorio y lo que le toca a la Persona 4 en la segunda parte, y escribir la especificación de la capacidad de niebla de guerra y viaje automático «ir a» antes de cualquier código, como exige §2.6.

Prompts utilizados:

```text
Voy a trabajar en la segunda parte del proyecto CRIPTA. Esta es una tarea de SOLO LECTURA Y ANÁLISIS: no edites archivos, no crees archivos, no hagas commits y NO ejecutes specify init ni ningún comando de spec-kit. Lee CLAUDE.md y README.md, el reparto, el prompt de SDD, los dos enunciados, ARQUITECTURA.md, DECISIONES.md y todo el código con sus pruebas, y ejecuta las pruebas.

[El prompt completo pide un informe con: estado real del repositorio, mi parte desglosada con sus casos del Apéndice B, dependencias con los otros tres integrantes, interacciones delicadas de la niebla, ambigüedades del enunciado y del reparto, riesgos frente a §6.2, orden de trabajo para los dos días y las preguntas que necesitan respuesta. Con las reglas de no inventar requisitos, distinguir requisito del enunciado de decisión de implementación y citar sección o archivo.]
```

```text
/speckit.specify Niebla de guerra y viaje automático «ir a» (§3.3 y §3.4, casos del Apéndice B de "Niebla de guerra e ir a").

[El prompt completo describe el conocimiento del jugador (tres estados de sala, memoria de puertas, antorcha, separación entre mapa y conocimiento, conocimiento como estado del juego, comando de mapa), el viaje «ir a» (ruta sobre el conocimiento, desempate del cazador, un paso por acción, recálculo antes de cada paso, motivos de detención, no abre puertas, registro en partida.log, pergamino), la vista de §7.3, cinco supuestos del grupo, los seis escenarios obligatorios del Apéndice B y lo que queda fuera de alcance. Limita la sesión a escribir en specs/ y en este archivo, sin commit, sin ramas y sin plan.]
```

```text
/speckit.clarify Registrar tres decisiones del grupo: (1) las puertas de una vecina explorada por la antorcha que el jugador nunca observó son desconocidas hasta que las observe; (2) una puerta se observa al entrar a una sala y también cuando cambia mientras el jugador está en una de sus dos salas; (3) una sala avistada se muestra como "hay algo en esa dirección", sin revelar su id. Otras ambigüedades reales se preguntan, no se deciden.
```

Uso en el proyecto: informe de arranque de la Persona 4 (no se guardó como archivo); `specs/003-niebla-ir-a/spec.md` y su lista de verificación.

Cambios realizados por el estudiante: El análisis encontró que las 945 pruebas pasan, pero que la cifra de 861 que siguen diciendo el README, la constitución y el Documento de Decisiones está desactualizada, y que el `python` del PATH de la máquina era el acceso directo de la tienda de Windows y no un intérprete, de modo que hubo que correrlas con otro. También mostró que el traductor ya lee el costo y el rango aunque el reparto se los asignaba a otro integrante, que la consulta de ubicación de llaves no existe todavía, y que los datos sin conexión son de la primera parte. Se rechazó correr `/speckit.plan` antes de tener especificación, porque el plan no puede contener reglas que no estén en `spec.md`. En la especificación, las tres decisiones de la aclaración se dejaron primero como marcadores en los puntos exactos donde el enunciado no decide, para que la sesión de aclaración las registrara como preguntas y respuestas en vez de aparecer escritas como si fueran del enunciado. Los cinco supuestos del grupo quedaron marcados como tales en la sección de supuestos. La aclaración detectó cuatro ambigüedades más, y se le pidió a la herramienta que las preguntara en vez de decidirlas; dos de ellas eran puntos que la herramienta había resuelto por su cuenta en el primer borrador y que se convirtieron en preguntas. Las respuestas del grupo fueron: si un paso cumple varios motivos de detención se informan todos, en el orden en que los enumera el requisito; encender la antorcha dentro de una sala no explora nada hasta el siguiente movimiento; mientras no exista la cripta de referencia, los 5 ms se miden con la cripta publicada más grande y con criptas sintéticas de al menos ese tamaño; y un identificador de sala que no existe se rechaza igual que una sala no explorada, para no revelar el mapa real.

### 2.31 Plan de la niebla de guerra e «ir a» con /speckit.plan

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Planificar la capacidad `specs/003-niebla-ir-a`: estructuras, alternativas, complejidad, reversión con el historial, exportación para el guardado, dependencias con el resto del grupo y mediciones previstas, sin agregar reglas que no estén en la especificación.

Prompts utilizados:

```text
/speckit.plan para la spec specs/003-niebla-ir-a (niebla de guerra e «ir a»).

[El prompt completo autoriza crear .specify/feature.json, prohíbe tasks, implement, commit, push, cambiar de rama y tocar código o pruebas, y pide que el plan contenga: estructuras con al menos dos alternativas por decisión y el motivo del descarte; complejidad de consultar una sala, consultar una puerta recordada, explorar, anotar e invertir cambios y calcular un paso de «ir a»; la decisión justificada de compartir o no la búsqueda del cazador; cómo se revierte la exploración con el historial existente, incluidos la antorcha y el pergamino durante un viaje; cómo se exporta e importa el conocimiento sin decidir el formato binario; módulos afectados y lo que se necesita de cada integrante; y mediciones previstas con la alternativa descartada medida. Recuerda las prohibiciones de §6.2 y que la tabla hash del grupo solo acepta claves enteras o de texto.]
```

Uso en el proyecto: `specs/003-niebla-ir-a/plan.md`, `research.md`, `data-model.md`, `contracts/comandos.md`, `contracts/interfaz-mapa-conocido.md` y `quickstart.md`.

Cambios realizados por el estudiante: Antes de escribir el plan se revisó si la búsqueda del cazador servía para «ir a» y se encontró que sí, porque recibe las vecinas desde afuera, pero también se encontró un supuesto que comparte con el cazador y que nadie había comprobado: el traductor admite pasos de un solo sentido, y una búsqueda que corre desde el destino daría distancias por caminos que no se pueden recorrer en ese sentido. Se revisaron los datos de `cripta-01`, que no tiene ninguno, y se dejó como riesgo para coordinar con el dueño del cazador en vez de cambiar su estructura. La clave de una puerta en la memoria del jugador se pensó tres veces: una tupla no sirve porque la tabla hash del grupo la rechaza, y un texto con los ids de las dos salas no es único, porque dos salidas pueden unir las mismas dos salas; quedó un entero calculado desde un lado fijo de la puerta. Se descartó también deducir si una sala está avistada mirando sus propias salidas, porque con un paso de un solo sentido da una respuesta falsa, y se eligió un contador por sala que se suma al explorar y se resta al revertir. Se detectó una regla que la especificación no escribe y que el plan no debía inventar: si «una sala que contiene enemigos» cuenta a los enemigos muertos; se dejó señalada para corregir la especificación.

### 2.32 Tareas y revisión de consistencia de la niebla de guerra con /speckit.tasks y /speckit.analyze

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Descomponer el plan de `specs/003-niebla-ir-a` en tareas trazables y revisar la consistencia entre especificación, plan y tareas antes de implementar, como pide §2.2.

Prompts utilizados:

```text
/speckit.tasks y luego /speckit.analyze para specs/003-niebla-ir-a.

[El prompt completo prohíbe implement, commit, push, cambiar de rama y tocar código o pruebas; pide que /speckit.analyze solo reporte y que nada se corrija sin preguntar, recordando que la especificación se corrige primero y en commit aparte. Reglas de las tareas: cada tarea cita sus FR y ninguna queda sin FR; cada escenario tiene una prueba que cita su FR, agrupadas por historia; tareas pequeñas con dependencias explícitas; orden mapa conocido, antorcha y reversión, luego «ir a», vista, exportar e importar, mediciones y documentación; marcar las bloqueadas por los avisos del motor y por la versión del formato de partida y decir qué se puede avanzar antes; marcar las estrictamente necesarias para los seis casos del Apéndice B; respetar §6.2.]
```

Uso en el proyecto: `specs/003-niebla-ir-a/tasks.md` y el reporte de la revisión de consistencia (no se guardó como archivo).

Cambios realizados por el estudiante: Se pidió seguir el orden de trabajo del grupo y no el de prioridad de las historias, y separar las pruebas que se pueden escribir sin los avisos del motor, armando el conocimiento a mano, de las que necesitan la partida real; así casi toda la capacidad puede avanzar mientras llegan los cambios de otros integrantes. El registro de prompts quedó fuera de la lista de tareas porque no atiende ningún requisito de la especificación, que era una regla explícita. La revisión encontró un problema que el plan había introducido sin notarlo: los motivos de parada se evaluaban después del ciclo de eventos, así que un enemigo que entrara a la sala del jugador sin atacarlo detenía el viaje, cosa que la especificación dice expresamente que no ocurre, y un enemigo que estuviera al entrar y se fuera antes de la siguiente decisión no lo detenía. Los hallazgos se reportaron sin corregir nada, a la espera de la decisión del grupo.

### 2.33 Corrección de los hallazgos de la revisión de consistencia de la niebla de guerra

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Aplicar las correcciones aprobadas por el grupo a los hallazgos de `/speckit.analyze` sobre `specs/003-niebla-ir-a`, con la especificación primero y por separado.

Prompts utilizados:

```text
Sí a todo, con este orden y estos límites: 1. A1: corrige FR-028 (b) en spec.md a "enemigos vivos, activos o dormidos" y registra la decisión en la sección de aclaraciones; esto toca SOLO spec.md y su checklist. 2. F1 a F8 y C1: aplica las correcciones propuestas en plan.md, research.md, data-model.md y tasks.md. En F5 NO pidas el tamaño de la cripta a nadie: usa criptas sintéticas deterministas por semilla en tres tamaños crecientes, sin escribir ningún tamaño de cripta concreto. 3. Mantén "conocimiento del jugador" y "mapa conocido" como lo mismo y acláralo una sola vez.

[El prompt completo prohíbe commit, push, cambiar de rama, tocar código o pruebas y ejecutar /speckit.implement, y pide al final la lista de cambios por hallazgo con archivo y líneas, y confirmar que repetir la revisión ya no encuentra hallazgos de severidad media o alta.]
```

Uso en el proyecto: `specs/003-niebla-ir-a/spec.md` y su lista de verificación, por un lado; `plan.md`, `research.md`, `data-model.md` y `tasks.md`, por otro.

Cambios realizados por el estudiante: Al corregir FR-028 (b) se encontró un defecto propio de la sesión de aclaración: tres de las aclaraciones habían quedado escritas dentro de la lista de requisitos, después de FR-029, y no en su sección, porque la edición se anclaba en una frase que aparecía en dos lugares del archivo. Ese defecto ya estaba en la especificación confirmada. Se movieron sin cambiar su texto, en la misma corrección de la especificación. La decisión de medir solo con criptas sintéticas contradice lo que la especificación dice sobre FR-036, que mide también sobre la cripta publicada más grande. Como el permiso para tocar la especificación se limitaba a A1, esa contradicción no se corrigió: se dejó anotada como pendiente en el plan y en las tareas para que el grupo decida. Al reestructurar dos tareas largas, sus requisitos habían quedado en una línea aparte, que era justamente uno de los hallazgos; se detectó al volver a comprobar y se corrigió.

### 2.34 Alinear FR-036 con §6.1 y la medición de «ir a» con la cripta de referencia

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Resolver la contradicción entre la especificación y el plan sobre con qué criptas se mide el límite de 5 ms de «ir a», con la especificación fiel al enunciado.

Prompts utilizados:

```text
Muéstrame, sin modificar nada, el texto exacto de FR-036, SC-006 y la aclaración de spec.md:24, y la nota pendiente de plan.md:34. Luego dime si realmente se contradicen con medir con criptas sintéticas por semilla. Mi criterio: la spec debe seguir fiel al enunciado §6.1. Si la spec dice eso, NO la cambies [...] Solo propón un cambio a la spec si el texto afirma algo que el enunciado no dice. Si propones cambiarla, muéstrame el cambio y espera mi confirmación. Repite /speckit-analyze completo al terminar.
```

```text
Sí, aplica el cambio a la spec tal como lo propusiste [...] Luego ajusta plan.md, research.md y tasks.md (T042 y T044): criptas sintéticas deterministas por semilla en tres tamaños crecientes, y además los datos de la cripta de referencia en cuanto exista un paquete sin conexión con ella, cargados como cualquier cripta, sin ningún tamaño ni id de cripta en el código. Quita las dos notas "Pendiente". Un dato nuevo: la cripta de referencia ya está publicada.
```

Uso en el proyecto: `specs/003-niebla-ir-a/spec.md` y su lista de verificación, por un lado; `plan.md`, `research.md` y `tasks.md`, por otro.

Cambios realizados por el estudiante: La comparación contra el texto del enunciado mostró que la contradicción no venía del plan sino de la especificación: la primera oración de FR-036 repetía §6.1, pero la segunda, SC-006 y una aclaración agregaban una regla de medición que el enunciado no dice y que había salido de una aclaración anterior del propio grupo. Se quitó esa regla de la especificación. La aclaración original no se borró, para que el registro de lo decidido ese día siga intacto; se marcó como reemplazada y se agregó la nueva. Para no escribir el id de la cripta de referencia en el código, la medición recorre todas las criptas del paquete sin conexión y las reporta con el id que traen sus datos.

### 2.35 Implementación de la niebla de guerra, tramo sin dependencias, con /speckit.implement

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Implementar la parte de `specs/003-niebla-ir-a` que no depende de archivos de otros integrantes: el mapa conocido, la reversión, exportar e importar, las reglas del viaje en el modelo, los comandos y la presentación del mapa.

Prompts utilizados:

```text
Ejecuta /speckit-implement para specs/003-niebla-ir-a, SOLO el tramo que no depende de otros integrantes.

[El prompt completo enumera el alcance (mapa conocido; exploración, antorcha y observación de puertas con avisos simulados desde las pruebas; reversión con el historial existente, incluidas la antorcha y la sala avistada por dos; exportar e importar; reglas de «ir a» en el modelo reutilizando la búsqueda del cazador; comandos mapa e ir a y la presentación del mapa) y los límites: no tocar model/game.py ni adapters/almacen_partida.py, ni el bucle de pasos del controlador, las banderas, el bench, el README o DECISIONES.md; cada prueba cita sus FR; respetar §6.2 con claves de tabla enteras o de texto; ningún dato de cripta en el código; marcar las tareas; commits pequeños que citen los FR, sin push ni cambio de rama; avisar si la especificación o el plan están mal; buscar un Python real.]
```

Uso en el proyecto: `cripta/structures/mapa_conocido.py`, `cripta/model/viaje.py`, `cripta/controller/commands.py`, `cripta/replay/replay_log.py`, `cripta/controller/application.py`, `cripta/view/console_view.py` y las pruebas `tests/test_mapa_conocido.py`, `tests/test_viaje.py`, `tests/test_vista_mapa_conocido.py`, `tests/test_commands.py` y `tests/test_replay_log.py`.

Cambios realizados por el estudiante: Se hizo solo lo que no necesitaba los avisos del motor: las pruebas llaman a mano a los avisos que algún día dará el motor, y las reglas del viaje se probaron moviendo al jugador con el motor real y actualizando el mapa conocido a mano. Quedaron sin hacer, y así marcadas, las tareas que necesitan que la partida tenga el mapa conocido, aunque algunas tocaran solo archivos propios, porque conectarlas antes haría fallar el inicio de toda partida. Tres pruebas fallaron al primer intento, y en los tres casos el error era de la prueba y no del código: dos topologías asignaban dos salidas a la misma dirección de una sala, y una prueba suponía un orden de salidas distinto del real, que es N, S, E, O. Las reglas del viaje se escribieron en un módulo aparte del motor en vez de dentro de él, para no tocar el archivo de otro integrante y porque así se prueban sin armar un viaje entero.

### 2.36 La especificación no decía que «ir a» se rechaza con la partida terminada

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Cerrar un hueco que apareció al implementar: el código rechazaba la orden «ir a» con la partida terminada y ningún requisito lo decía.

Prompts utilizados:

```text
Corrige primero la spec (specs/003-niebla-ir-a/spec.md y su checklist, nada más): agrega como requisito o supuesto, con su FR o con la numeración que corresponda sin reenumerar los existentes, que la orden «ir a» se rechaza sin consumir tiempo cuando la partida ya terminó, igual que toda otra acción. Regístralo en aclaraciones si hace falta. Muestra el cambio y no hagas commit.
```

Uso en el proyecto: `specs/003-niebla-ir-a/spec.md` y su lista de verificación.

Cambios realizados por el estudiante: Al revisar la implementación se notó que el viaje rechazaba la orden con la partida terminada por decisión de la herramienta, siguiendo la regla de la primera parte de que una partida terminada rechaza toda acción, pero sin que la especificación lo dijera. Según §1 del enunciado, un programa que hace algo que ninguna especificación describe es un defecto, así que se corrige primero la especificación, en una confirmación aparte, antes de que el código quede como lo único que lo describe. Se agregó como FR-038 y no como supuesto, porque es una regla del juego que se puede probar, y se numeró después del último requisito para no cambiar los identificadores que ya citan las pruebas y las tareas.

### 2.37 Alinear tareas, plan y prueba con FR-038

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Después de la confirmación de la especificación con FR-038, llevar el requisito nuevo a la tarea, a la trazabilidad del plan y a la prueba que ya lo comprobaba, en una confirmación aparte.

Prompts utilizados:

```text
Sí, hazlo ahora, en UN commit aparte posterior al de la spec: agrega FR-038 a T020 en tasks.md y a la trazabilidad de plan.md, y cambia el docstring de test_con_la_partida_terminada_se_rechaza en cripta/tests/test_viaje.py para que cite FR-038. No cambies nada más. Corre todas las pruebas, dime cuántas pasan, haz el commit (mensaje: "Alinea tareas, plan y prueba con FR-038") y NO hagas push.
```

Uso en el proyecto: `specs/003-niebla-ir-a/tasks.md`, `specs/003-niebla-ir-a/plan.md` y `cripta/tests/test_viaje.py`.

Cambios realizados por el estudiante: Se respetó el orden que exige la constitución: la especificación primero, en su propia confirmación, y después lo que depende de ella. La prueba ya comprobaba el comportamiento; solo citaba el requisito equivocado, que es justo lo que se revisa en la defensa al seguir un requisito hasta su prueba.

### 2.38 Segundo tramo de la niebla de guerra: viaje, mediciones y documentación

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Implementar el bucle del viaje «ir a» en el controlador, las mediciones de `--bench` del mapa conocido y un borrador de la sección §5.3 del Documento de Decisiones, sin tocar archivos de otros integrantes.

Prompts utilizados:

```text
Continúa /speckit-implement para specs/003-niebla-ir-a, segundo tramo. Haz SOLO tareas pendientes que NO requieran modificar model/game.py ni adapters/almacen_partida.py: 1. El bucle de viaje del controlador (T025 a T028) y sus pruebas, hasta donde se pueda probar con el motor actual. 2. Las mediciones de --bench (T042 a T044), con criptas sintéticas deterministas por semilla en tres tamaños crecientes, más cada cripta del paquete sin conexión, midiendo directamente las alternativas descartadas del plan. No inventes números. 3. Un borrador de la sección §5.3 de DECISIONES.md y la parte del README que me corresponda (T045 a T047), en un commit aparte.

[El prompt completo repite las prohibiciones de §6.2, pide que cada prueba cite sus FR, commits pequeños sin push y sin cambiar de rama, y que si la especificación o el plan resultan incorrectos se avise en vez de corregirlos en silencio.]
```

Uso en el proyecto: `cripta/controller/game_controller.py`, `cripta/controller/application.py`, `cripta/view/console_view.py`, `cripta/tests/test_ir_a.py`, `cripta/benchmark/bench_mapa_conocido.py`, `cripta/benchmark/benchmark.py`, la sección de resultados de `specs/003-niebla-ir-a/plan.md`, el borrador de §5.3 en `cripta/docs/DECISIONES.md` y `cripta/README.md`.

Cambios realizados por el estudiante: Las mediciones contradijeron al plan en dos puntos, y se reportaron sin cambiar ninguna decisión. Primero, la clave entera de las puertas, elegida en parte por ser más barata que una de texto, resultó el doble de cara, porque hay que buscar por qué dirección sale la puerta; sigue siendo la única correcta, pero el motivo de costo no se sostiene. Segundo, y más grave, un paso de «ir a» con el mapa conocido completo no cumple los 5 ms a partir de 400 salas, y la alternativa que el plan tenía prevista para ese caso, reutilizar la búsqueda durante el viaje, solo baja el promedio y no el primer paso. Antes de reportarlo se midió por separado la misma búsqueda con las vecinas reales, para saber si el problema era el mapa conocido o la búsqueda: la búsqueda misma ya supera el límite en mapas medianos, y el mapa conocido le agrega cerca de un setenta por ciento. Como el paquete sin conexión todavía no trae la cripta de referencia, no se puede decir si FR-036 se cumple en la condición del enunciado; queda para el grupo. Además, tres pruebas fallaron al primer intento por topologías mal armadas en las propias pruebas, no por el código.

### 2.39 Mejoras de rendimiento del viaje «ir a» para FR-036

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-16

Objetivo: Atacar el incumplimiento del límite de 5 ms por paso de «ir a», con el plan revisado primero y cada mejora en su propio commit, medida antes y después.

Prompts utilizados:

```text
Voy a abordar el problema de rendimiento de FR-036 que mediste. Trabaja en orden y respeta §2.6 (primero plan, luego código, en commits separados): 1. PLAN PRIMERO: actualiza plan.md y research.md con la decisión nueva [...] Describe las mejoras a probar, en este orden: (a) calcular la clave de puerta desde la salida que ya se tiene, sin buscarla; (b) detener la búsqueda de «ir a» cuando se finaliza la sala del jugador, con una justificación escrita de por qué el desempate de FR-024 sigue correcto; (c) reutilizar la ruta durante el viaje. NO cambies la spec ni FR-036. 2. CÓDIGO, en commits separados por mejora, cada uno con su medición ANTES y DESPUÉS con --bench (mismos tamaños y semillas) [...] (b) modifica structures/rutas_mas_baratas.py (es de Carlos y lo usa el cazador) SOLO agregando un parámetro opcional de parada que no cambie el comportamiento por defecto [...] Agrega una prueba que compare, sobre muchos mapas sintéticos deterministas por semilla (incluidos empates de costo y salidas paralelas), que la decisión con parada anticipada es IDÉNTICA al cálculo completo, y que el cazador sigue dando el mismo resultado. 3. [...] Si tras todo sigue sin cumplirse 5 ms en el tamaño de la cripta de referencia, no lo escondas.
```

Uso en el proyecto: `specs/003-niebla-ir-a/plan.md` y `research.md`, `cripta/structures/mapa_conocido.py`, `cripta/structures/rutas_mas_baratas.py` (cambio rotulado para revisión de su dueño), `cripta/model/viaje.py`, `cripta/controller/game_controller.py`, `cripta/benchmark/bench_mapa_conocido.py`, las pruebas `tests/test_parada_anticipada.py`, `tests/test_reutilizar_ruta.py` y `tests/test_mapa_conocido.py`, y `cripta/docs/DECISIONES.md`.

Cambios realizados por el estudiante: Antes de la primera mejora se cambió la medición para que mida el paso que da el viaje del programa y no la búsqueda suelta; si no, las mejoras dentro del viaje no se habrían visto en el número. Al probar la parada anticipada apareció un caso que la justificación escrita no cubría: si la sala del jugador no tiene ruta al destino, la búsqueda nunca se detiene, y pedirle el paso no debe ser un error sino «no hay ruta». La prueba de equivalencia lo encontró en los mapas aleatorios y se corrigió antes del commit. Las mediciones se reportaron con su ruido: repetidas tres veces, el primer paso varió alrededor de un veinte por ciento, así que las diferencias pequeñas no se presentaron como mejoras. El resultado final no cumple el límite en el primer paso de un viaje largo con 400 salas o más, y así quedó escrito en el Documento de Decisiones, junto con lo que falta probar.

### 2.40 Resolución del merge de main (línea de tiempo) sobre la rama de niebla de guerra e «ir a»

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Terminar el merge de `origin/main` en `Parte_2-niebla-ir-a` resolviendo los conflictos sin perder trabajo de ninguno de los dos lados.

Prompts utilizados:

```text
Estoy en medio de un merge de origin/main en la rama Parte_2-niebla-ir-a, con conflictos en cripta/PROMPTS_LLM.md, cripta/benchmark/benchmark.py y cripta/controller/commands.py. NO abortes el merge. Resuélvelos conservando AMBOS lados [...] No cambies ningún otro archivo salvo lo estrictamente necesario para que compile. Luego corre TODAS las pruebas con un Python 3.11 o superior real. Si pasan todas, haz el commit del merge con el mensaje por defecto, SIN líneas de atribución de Claude, y no hagas push. Si alguna falla, NO commitees [...] Respeta la constitución y §6.2 [...] Registra la entrada en cripta/PROMPTS_LLM.md, al final de mi sección.
```

Uso en el proyecto: `cripta/PROMPTS_LLM.md`, `cripta/benchmark/benchmark.py` y `cripta/controller/commands.py`.

Cambios realizados por el estudiante: Los tres conflictos eran de dos lados que agregaban cosas distintas en el mismo lugar, no de cambios incompatibles. En este archivo quedaron la entrada de la línea de tiempo que trajo main y, a continuación, las entradas 2.30 a 2.39 de esta rama, sin tocar su texto; las dos ramas numeraron su primera entrada como 2.30, y esa repetición se dejó así porque renumerar habría reescrito entradas ajenas. En `benchmark.py` quedaron las dos suites nuevas (mapa conocido y viaje «ir a», y línea de tiempo), y en `commands.py` las líneas de ayuda de `mapa`, `ir a` e `historia`; el resto de ambos archivos ya lo había combinado git sin conflicto. No hizo falta cambiar ningún otro archivo. Las 1143 pruebas pasaron con Python 3.12.3 (el de WSL, porque en Windows solo estaba el atajo de la Microsoft Store), y se comprobó que el código fusionado no importa heapq, bisect ni collections.

### 2.41 Análisis de «ir a» frente a salidas de un solo sentido

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Saber, sin modificar nada, si el cálculo de ruta de «ir a» sigue siendo correcto ahora que Carlos confirmó que el servicio puede publicar salidas de un solo sentido, y qué habría que cambiar.

Prompts utilizados:

```text
Carlos confirma que el servicio puede publicar salidas de un solo sentido. Analiza SIN modificar nada: 1. Cómo calcula hoy mi «ir a» la ruta [...] ¿es incorrecto con salidas dirigidas? Dímelo con un ejemplo concreto de mapa asimétrico. 2. Revisa cómo quedó structures/rutas_mas_baratas.py en main y los avisos de Carlos sobre un proveedor de aristas entrantes. Dime si puedo reutilizar eso para el mapa conocido. 3. Propón la solución más simple que mantenga el desempate de FR-024 y la parada anticipada [...] Compara y recomienda, con las mediciones que habría que hacer. 4. Dime si esto exige cambiar la spec 003-niebla-ir-a (futura 005) o solo el plan [...] 5. Dime qué parte depende de que Carlos termine su proveedor de aristas entrantes y qué puedo hacer ya. No toques código, tests ni documentos. Registra la entrada en PROMPTS_LLM.md.
```

Uso en el proyecto: ninguno todavía; es el análisis previo a actualizar el plan de `specs/003-niebla-ir-a`. Se leyeron `cripta/model/viaje.py`, `cripta/structures/mapa_conocido.py`, `cripta/structures/rutas_mas_baratas.py` en esta rama y en `origin/mauricio-logica-juego`, y `cripta/model/game.py` y `cripta/docs/DECISIONES.md` de esa rama.

Cambios realizados por el estudiante: Pendiente de la decisión. El análisis confirmó lo que el plan ya listaba como riesgo: la búsqueda va desde el destino por las salidas que salen de cada sala, así que con un paso de un solo sentido calcula la distancia del destino a cada sala y no la de cada sala al destino. Con las salidas 1→3, 3→2 y 2→1, todas de costo 1 y sin vuelta, el jugador en 1 queda sin ruta hacia 3 aunque tiene una salida directa. También se encontró que el proveedor de salidas entrantes de Carlos no está en main sino en su rama, que su versión de la búsqueda rechaza a propósito combinar la parada anticipada con el proveedor de salidas, y que la especificación ya pide lo correcto (recorrer salidas y minimizar su costo), de modo que el defecto es de implementación y de plan, no de requisito.

### 2.42 La especificación de «ir a» no decía nada de las salidas de un solo sentido

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Dejar escrito en la especificación, antes de tocar plan o código (§2.6), que «ir a» debe respetar el sentido de las salidas, ahora que se confirmó que el servicio puede publicar salidas de un solo sentido.

Prompts utilizados:

```text
Agrega a specs/003-niebla-ir-a/spec.md (y su checklist), SIN reenumerar FR existentes: un caso límite y, si hace falta, un escenario de aceptación que diga que «ir a» debe encontrar la ruta de menor costo respetando el sentido de las salidas. Una salida puede existir en un solo sentido (la sala destino no declara la vuelta); la ruta del jugador solo puede usar salidas en el sentido en que existen, y no debe declararse "sin ruta" cuando existe una salida directa. No nombres estructuras, clases ni algoritmos. Registra la decisión en aclaraciones. Muestra el cambio y NO hagas commit.
```

Uso en el proyecto: `specs/003-niebla-ir-a/spec.md` (aclaración de la sesión 2026-11-17, caso borde y escenarios 7 y 8 de la Historia 4) y `specs/003-niebla-ir-a/checklists/requirements.md` (nota de la corrección).

Cambios realizados por el estudiante: No se agregó ningún requisito ni se reenumeró ninguno, porque FR-023 ya pide recorrer salidas y minimizar su costo: el defecto estaba en el código y en el plan, no en el requisito. Lo que faltaba era que la especificación lo hiciera verificable. El escenario 7 es el mapa de tres salas del análisis anterior (2.41), con el que la implementación actual se declara sin ruta teniendo una salida directa de costo 1; así la prueba que lo cubra falla hoy y deja de fallar con la corrección. El escenario 8 cubre el caso contrario, que la ruta no use una salida al revés. La especificación sigue sin nombrar estructuras, clases ni algoritmos. El cambio queda sin commit hasta revisarlo.

### 2.43 Merge de la rama de Carlos (salidas dirigidas y objeto nulo del mapa conocido)

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Terminar el merge de `origin/mauricio-logica-juego` en `Parte_2-niebla-ir-a`: limpiar las marcas de conflicto que quedaron en este archivo, revisar la versión de Carlos de la búsqueda de costo mínimo y correr todas las pruebas antes de commitear.

Prompts utilizados:

```text
Estoy en medio de un merge de origin/mauricio-logica-juego en mi rama Parte_2-niebla-ir-a. NO abortes el merge. [...] 1. Limpia las marcas de PROMPTS_LLM.md conservando AMBOS lados completos, sin borrar ninguna entrada. Solo quita las líneas de marca. Verifica que no quede ninguna marca en ningún archivo del repo. 2. Revisa que rutas_mas_baratas.py quedó con parar_en y salidas_de, y que las protecciones de distancia_a, alcanza y primer_paso_desde siguen ahí. 3. Corre TODAS las pruebas con un Python 3.11 o superior real [...] 4. Si TODAS pasan: haz el commit del merge [...] 5. Si alguna falla: NO hagas commit. Dime cuáles y por qué.
```

Uso en el proyecto: `cripta/PROMPTS_LLM.md`. Se revisaron `cripta/structures/rutas_mas_baratas.py`, `cripta/model/game.py`, `cripta/controller/game_controller.py` y `cripta/tests/test_ir_a.py`.

Cambios realizados por el estudiante: Quitar solo las líneas de marca habría dejado entradas mezcladas, porque git había alineado el encabezado de la entrada 2.31 de Carlos con fragmentos de las entradas 2.40 y 2.42 de esta rama. Se rearmó el archivo con la parte común, la entrada 2.31 de Carlos y, a continuación, las entradas 2.30 a 2.42 de esta rama, y se comprobó que tiene exactamente las mismas líneas que el archivo con las marcas quitadas, más las líneas comunes («Prompts utilizados:», la apertura del bloque de texto y líneas vacías) que cada entrada necesita para quedar completa. No quedó ninguna marca en el repositorio. La búsqueda de Carlos conserva `parar_en`, `salidas_de` y las protecciones de `distancia_a`, `alcanza` y `primer_paso_desde`. De 1158 pruebas falló una, `test_ir_a.TestOrden.test_sin_mapa_conocido_no_hay_viaje`: la partida de Carlos ya no deja el mapa conocido en `None`, sino que pone un objeto nulo con `disponible = False`, y el controlador del viaje solo comprobaba `None`, así que le pedía a ese objeto un método que no tiene. Por eso el merge no se commiteó.

### 2.44 El controlador del viaje trata el objeto nulo del mapa conocido como ausencia de mapa

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Cerrar el merge de la rama de Carlos en su propio commit y arreglar, en otro commit aparte, la prueba que dejó fallando.

Prompts utilizados:

```text
Sí, aplica el arreglo en MI archivo cripta/controller/game_controller.py: que known_map devuelva None cuando el mapa tenga disponible = False, para que travel y el comando mapa rechacen la orden como cuando no hay mapa. Cambio mínimo, sin tocar nada más. [...] 1. Primero cierra el merge [...] SIN el arreglo dentro [...] 2. Aplica el arreglo y haz un SEGUNDO commit aparte [...] 3. Corre TODAS las pruebas [...] 4. Revisa la comprobación de None en cripta/adapters/almacen_partida.py:1289 y dime si tiene el mismo problema. NO modifiques ese archivo (es de Carlos). 5. Verifica que PROMPTS_LLM.md conserva todas las entradas de ambos lados [...]
```

Uso en el proyecto: `cripta/controller/game_controller.py` (propiedad `known_map`).

Cambios realizados por el estudiante: El merge se cerró primero con la prueba fallando, para que el arreglo quedara en un commit propio y se viera qué lo motivó. El arreglo es solo la propiedad `known_map`: devuelve `None` si el mapa falta o si se declara no disponible, y el mapa real, que no tiene ese atributo, sigue contando como disponible. Con eso pasan las 1158 pruebas. Se revisó la comprobación de `None` de `adapters/almacen_partida.py` y no tiene el mismo problema: recibe el mapa que le pasa quien carga la partida, que es `None` o un mapa real, nunca el objeto nulo, porque ese lo crea la partida después; y la copia para la línea de tiempo pide `exportar` por duck typing, que el objeto nulo no tiene, así que se guarda como «sin mapa». Al buscar dónde se atiende el comando `mapa` se encontró que la aplicación no lo despacha: cae en «Comando sin atender». Es un defecto aparte, anterior a este merge, y no se tocó. También se comprobó que este archivo conserva todos los encabezados y todas las líneas de los dos padres del merge.

### 2.45 Integración del mapa conocido con el motor real

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Conectar la niebla de guerra con la partida real ahora que la rama de Carlos trae los avisos del motor, el colaborador opcional, `is_hunter` y el guardado (tareas T011 a T019, T029, T032 a T035, T039 y T040 de `specs/003-niebla-ir-a`).

Prompts utilizados:

```text
Ya tengo mezclada la rama de Carlos. Haz la integración de mi mapa conocido con el motor real (specs/003-niebla-ir-a: T011 a T019, T029, T032 a T035, T039, T040). Carlos ya implementó los avisos, el colaborador opcional, is_hunter y el guardado: NO reescribas lo suyo. Para cada tarea, verifica si ya está cubierta y márcala con la referencia a su prueba; implementa solo lo que falte. Prioridades, en este orden: 1. Que el comando «mapa» funcione en una partida real [...] 2. Que una partida real construya mi mapa conocido (construir_juego / Game) y que «ir a N» lo use de punta a punta, con pruebas con el motor real para los casos del Apéndice B [...] 3. Marca de cazador en la vista con is_hunter y costos de las salidas de la sala actual. 4. Prueba de guardar y cargar que conserve el conocimiento [...] NO toques rutas_mas_baratas.py, la línea de tiempo ni almacen_partida.py. NO resuelvas aún el problema de salidas de un solo sentido [...]
```

Uso en el proyecto: `cripta/controller/application.py` (comando `mapa`, `build_game`, `build_saved_game`, `room_view`), `cripta/structures/mapa_conocido.py` (`usar_historial`), `cripta/view/console_view.py` (`show_room`), las pruebas `tests/test_comando_mapa.py`, `tests/test_niebla.py`, `tests/test_niebla_guardado.py` y `tests/test_vista_sala_actual.py`, y `specs/003-niebla-ir-a/tasks.md`.

Cambios realizados por el estudiante: Antes de escribir código se revisó qué ya estaba hecho: los avisos `jugador_entro` y `puerta_cambio`, el objeto nulo, `is_hunter` con su marca en la vista y el guardado del conocimiento eran de Carlos y coincidían con los nombres y el contrato `exportar`/`importar` del mapa conocido, así que esas tareas se marcaron con la referencia a la prueba que las ejercita, sin tocar su código. Lo que faltaba era del lado de la aplicación. El comando `mapa` se interpretaba pero nadie lo atendía. La partida nueva no armaba el mapa conocido; ahora lo arma con el mismo historial que el rastro. La partida cargada tenía un problema que no se veía: el historial lo crea el adaptador de Carlos al cargar, así que un mapa armado antes no podía compartirlo y lo explorado después de cargar no se habría revertido con el pergamino. Como el adaptador no se podía tocar, el mapa recibe el historial después de armada la partida, y hay una prueba que lo comprueba. Las pruebas nuevas usan el motor real, sin llamar a mano a los avisos, y criptas sintéticas sin ids ni tamaños de criptas publicadas; la de punta a punta usa la primera cripta offline que se lista, sin nombrarla. Quedan pendientes, fuera de este pedido: la consulta de la línea de tiempo no le pasa al reconstructor cómo crear el mapa conocido, así que el resumen de un instante pasado lo informa como no disponible (FR-016), y las salidas de un solo sentido.

### 2.46 Cierre de la niebla de guerra: salidas de un solo sentido y mapa conocido en la historia

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Cerrar lo pendiente de `specs/003-niebla-ir-a`: que «ir a» respete el sentido de las salidas, que «historia» informe el mapa conocido (FR-016), las banderas `--checkpoint-cada` y `--hasta`, y los documentos de cierre, con reglas de parada si aparecía algo que no se pudiera arreglar en archivos propios.

Prompts utilizados:

```text
Cierra todo lo que queda de mi parte en specs/003-niebla-ir-a, en este orden, con commits pequeños y separados (documentos aparte del código), SIN push y SIN cambiar de rama. [...] REGLAS DE PARADA (obligatorias): si algo de la spec o el plan resulta incorrecto, NO lo corrijas en silencio [...] Si una tarea exige cambiar archivos de Carlos [...] NO los cambies: déjala bloqueada [...] Si fallan pruebas que no puedas arreglar dentro de mis archivos, detente. [...] PASO 1. SALIDAS DE UN SOLO SENTIDO [...] 1.1 PLAN [...] 1.2 PRUEBA PRIMERO [...] 1.3 CÓDIGO en mis archivos [...] 1.4 MEDICIONES [...] PASO 2. HISTORIA Y MAPA CONOCIDO (FR-016) [...] PASO 3. BANDERAS [...] PASO 4. CIERRE DE DOCUMENTOS [...] PASO 5. AUDITORÍA FINAL [...]
```

Uso en el proyecto: `specs/003-niebla-ir-a/plan.md` (alternativa 9), `research.md` §3, `tasks.md` (T048 a T053), `cripta/docs/DECISIONES.md` §5.3, `cripta/structures/mapa_conocido.py` (`entrantes_conocidas`), `cripta/benchmark/bench_mapa_conocido.py` (medición 6), `cripta/controller/application.py` (`reconstruir_con_mapa_conocido`) y las pruebas `tests/test_ir_a_sentido.py`, `tests/test_equivalencia_sentido.py`, `tests/test_historia_mapa_conocido.py` y `tests/test_mapa_conocido.py`.

Cambios realizados por el estudiante: El orden fue plan, prueba y código, cada uno en su commit. Las dos pruebas de los escenarios 7 y 8 se commitearon fallando, y siguen marcadas como fallo esperado porque el cableado final depende de que Carlos acepte la parada anticipada junto con el proveedor de salidas; se comprobó aparte, simulando ese cableado en memoria sin la parada, que con él pasan junto con todas las demás pruebas del viaje. Al planificar apareció que el índice de salidas entrantes ocupa memoria proporcional a la cripta completa, cosa que la tabla de complejidad del plan negaba para todo el mapa conocido; se dejó escrito en el plan en vez de esconderlo, con la aclaración de que el índice no es conocimiento y de que la especificación no fija un límite de memoria. La prueba de equivalencia comprueba además que su propio generador produce salidas sin vuelta, paralelas y empates, y tiene un control que demuestra que expandir por las salidas que salen sí da resultados distintos: sin eso, que pasara no habría probado nada. Las mediciones no mostraron diferencia de tiempo entre expandir por las salidas que entran y por las que salen fuera del ruido entre corridas. Al conectar el mapa conocido con «historia» se encontró un defecto de la línea de tiempo: repetir un movimiento desde una copia tomada antes de cargar el contenido de la sala destino falla en silencio, y el resumen entero queda en la sala anterior. No se puede arreglar sin tocar código de Carlos, así que se aplicó la regla de parada: se commiteó lo que estaba bien, la prueba que lo reproduce quedó fuera y los pasos 3 a 5 no se hicieron.

### 2.47 Banderas de la línea de tiempo, revisión de --bench y cierre de documentos de la niebla de guerra

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Terminar los pasos que quedaron pendientes en la sesión anterior: las banderas `--checkpoint-cada` y `--replay --hasta`, la revisión de que `--bench` tiene lo que pide §6.3, y el cierre de los documentos con una auditoría.

Prompts utilizados:

```text
Continúa donde te detuviste: los pasos 3, 4 y 5 del prompt anterior. Mismas reglas [...] NO hagas el cableado T052 (depende de Carlos). PASO 3. Banderas: --checkpoint-cada K y --replay partida.log --hasta t [...] Si la reconstrucción de la línea de tiempo falla por el defecto que encontraste, deja la bandera conectada pero anótalo en una nota visible en el README y en tasks.md. NO hagas --verificar ni --forzar [...] PASO 4. Integración de --bench [...] PASO 5. Cierre de documentos, commit aparte del código [...] Auditoría: términos prohibidos, ids o tamaños de cripta en el código, la vista usada desde --bench o --replay, FR sin prueba que los cite.
```

Uso en el proyecto: `cripta/main.py`, `cripta/controller/application.py` (`show_instant`, parámetros `copias_cada` y `hasta`), `cripta/view/console_view.py` (`lineas_de_historia`), las pruebas `tests/test_banderas_linea_de_tiempo.py` y `tests/test_vista_sala_actual.py`, `cripta/docs/DECISIONES.md` §5.3, `cripta/README.md`, `specs/003-niebla-ir-a/plan.md` y `tasks.md`.

Cambios realizados por el estudiante: Para imprimir el resumen de `--hasta` sin instanciar la vista, el formato que ya tenía `show_history` se sacó a una función del módulo de la vista, y el método la usa igual; las pruebas de la vista y de la línea de tiempo pasaron sin cambios. Una prueba de `--hasta` reemplaza la vista por una que falla si alguien la crea, para comprobar de verdad que no se instancia. Las pruebas que dependen de un movimiento usan una copia por acción, porque con copias espaciadas aparece el defecto de reconstrucción ya reportado; ese defecto quedó como nota visible en el README y en las tareas. Al revisar `--bench` contra §6.3 faltan dos cosas que son de otros: la resolubilidad, que nadie tomó, y la alternativa de la línea de tiempo sin puntos de control. En el cierre se cuidaron tres cosas: la sección §5.3 estaba como borrador delante de §5.1 y se movió a su lugar; las mediciones nuevas, de WSL con Python 3.12, se separaron de las de Windows con Python 3.11 en vez de mezclarlas en una tabla; y cada cifra del documento se comparó con la salida de las tres corridas, lo que llevó a corregir dos frases que decían más de lo medido (cuántas corridas eran de `--bench` completo y cuánto cuesta el índice frente a una búsqueda). También se encontró que el plan del cazador ya sabía que la cripta de referencia es cripta-06, de 300 salas: se dejó dicho sin interpolar un número entre las cuadrículas de 100 y 400 salas. La auditoría encontró que FR-021 no tenía prueba propia en esta capacidad y se agregó una con el motor real. Un comando de la terminal se quedó esperando entrada y la nota de la auditoría llegó en un commit aparte, en vez de reescribir el anterior.

### 2.48 Renombrar la especificación de la niebla de guerra a 005

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Aplicar la numeración que acordó el grupo (001 a 003 de Carlos, 004 de Mauricio, 005 de esta capacidad) renombrando `specs/003-niebla-ir-a` a `specs/005-niebla-ir-a`, y subir la rama.

Prompts utilizados:

```text
Renombra mi spec de specs/003-niebla-ir-a a specs/005-niebla-ir-a y sube la rama. [...] PASO 1. Renombra con git mv (para conservar el historial), no copiando. PASO 2. Actualiza las referencias a la ruta y al nombre [...] NO cambies nada que diga "003-linea-de-tiempo". NO modifiques las entradas anteriores de PROMPTS_LLM.md: es un registro histórico [...] Si encuentras menciones sueltas tipo "spec 003" o "003" sin el nombre, muéstrame la lista y cambia solo las que sean claramente de niebla; reporta las ambiguas sin tocarlas. [...] PASO 5. Haz git push normal a origin/Parte_2-niebla-ir-a. NO uses --force.
```

Uso en el proyecto: `specs/005-niebla-ir-a/` (renombrada con `git mv`), las referencias en `spec.md`, `plan.md`, `tasks.md`, `cripta/docs/DECISIONES.md`, `cripta/README.md`, `cripta/benchmark/bench_mapa_conocido.py` y los docstrings de quince archivos de pruebas, y `.specify/feature.json`, que git ignora.

Cambios realizados por el estudiante: Solo se cambiaron identificadores y rutas: 25 apariciones de `003-niebla-ir-a` en 20 archivos versionados, más `.specify/feature.json`. Ninguna regla, requisito ni lógica cambió, y las pruebas dieron lo mismo antes y después: 1205, con los dos fallos esperados de los escenarios 7 y 8. Las entradas anteriores de este registro conservan la ruta vieja a propósito, porque cuentan lo que se hizo en su momento. La única mención suelta de esta capacidad por número está en `structures/rutas_mas_baratas.py` («de la capacidad 003»), que es de Carlos: no se tocó y queda para que él la actualice. Las demás apariciones de «003» son números de requisito (FR-003, SC-003) o datos de mediciones.

### 2.49 --bench con la carpeta de --offline y el promedio por paso de «ir a» en criptas reales

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Preparar `--bench` para medir el paquete sin conexión de la segunda parte (criptas 02 a 06, con cripta-06 como referencia) en cuanto esté en el equipo: que `python main.py --bench --offline CARPETA` mida esa carpeta y que la fila de criptas reales muestre también el promedio por paso.

Prompts utilizados:

```text
Mauricio publicó el paquete sin conexión datos_offline_p2 con las criptas 02 a 06; cripta-06 es la de referencia (300 salas). [...] 1. Verifica cómo mi suite de --bench encuentra y carga el paquete sin conexión y córrela contra datos_offline_p2 (FuenteOffline), midiendo CADA cripta del paquete [...] 2. Mide con todo el mapa conocido explorado: el primer paso de «ir a» [...], el promedio por paso, y la búsqueda del cazador [...] 3. Cuenta [...] cuántas salidas son de un solo sentido [...] 4. [...] completa la fila de la cripta de referencia en DECISIONES §5.3 y en el plan, cierra T044 [...]
```

```text
Sí: haz que python main.py --bench --offline <ruta> mida esa carpeta, y que sin --offline siga usando datos_offline como hasta ahora. Haz dos commits de código, separados, cada uno con su prueba: 1. --bench usa la carpeta de --offline cuando se pasa. Sin ids ni tamaños de cripta escritos en el código. 2. La fila de las criptas reales imprime también el promedio por paso (hoy se calcula pero no se muestra). NO toques bench_cazador ni otros archivos de Carlos [...]
```

Uso en el proyecto: `cripta/main.py` (`run_bench`), `cripta/benchmark/benchmark.py` (`run_suite`, `main` y la marca `USA_PAQUETE_SIN_CONEXION`), `cripta/benchmark/bench_mapa_conocido.py` (`mediciones_de_criptas_reales`) y la prueba `tests/test_bench_paquete_sin_conexion.py`.

Cambios realizados por el estudiante: El primer prompt no se pudo cumplir: traía el texto de relleno de la ruta en vez de la ruta, y el paquete no estaba en ningún disco del equipo. No se midió nada ni se completó la fila de §5.3, y T044 sigue abierta. Al revisar la suite apareció que `--bench` ignoraba `--offline` y siempre leía `datos_offline/`, que hoy solo trae cripta-01; por eso se pidió el segundo prompt. Solo recibe la carpeta la suite que lo declara, para que las demás no cambien. La búsqueda del cazador no se agregó a la fila porque está en `bench_cazador`, que es de Carlos. Al correr la fila nueva con cripta-01, el viaje entre la primera y la última sala del esqueleto tenía 0 pasos, y el «promedio por paso» habría salido de dividir entre 1 sin medir ningún paso: la fila dice «sin ruta entre los extremos» en ese caso. Una de las pruebas falló al principio porque `mock.patch` usa `importlib.import_module` para resolver sus rutas, y la prueba lo reemplazaba antes del segundo `patch`; se cambió el orden. Pruebas: 1215 en WSL con Python 3.12.3, con los dos fallos esperados de los escenarios 7 y 8.

### 2.50 README de --bench --offline y viaje medido hacia la sala más lejana alcanzable

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Documentar en el README `python main.py --bench --offline CARPETA` y la fila de las criptas reales, y que esa fila mida algo útil cuando con el mapa conocido no hay ruta entre la primera y la última sala del esqueleto.

Prompts utilizados:

```text
Haz dos cosas, en commits separados, sin push, sin atribución de Claude: 1. README: documenta python main.py --bench --offline <ruta> y la nueva fila de las criptas reales. Commit de documentos aparte. 2. En la suite del mapa conocido, cuando no haya ruta entre la primera y la última sala, mide el primer paso hacia la sala más lejana alcanzable con el mapa conocido (por costo mínimo desde la sala inicial), y dilo en la fila. Con prueba. Sin ids ni tamaños de cripta en el código. No toques archivos de Carlos. [...]
```

Uso en el proyecto: `cripta/benchmark/bench_mapa_conocido.py` (`elegir_recorrido`, `RecorridoMedido`, `descripcion_del_recorrido`), `tests/test_bench_paquete_sin_conexion.py` y `cripta/README.md`.

Cambios realizados por el estudiante: Se tomó como «sala inicial» la partida del viaje que ya medía la suite, que es la primera sala del esqueleto. En cripta-01 coincide con la `sala_inicial` de sus datos generales, pero eso no está garantizado en otras criptas. Para saber qué salas se alcanzan, la búsqueda va desde esa sala y se expande por las salidas que salen de cada sala. Así la distancia es la de ir desde ella, y una sala que solo tiene salida hacia la primera no cuenta como alcanzable; hay una prueba para ese caso. Si dos salas están igual de lejos, gana la de menor id, para que la medición dé lo mismo en cada corrida. Las cuadrículas sintéticas no cambian, porque en ellas siempre hay ruta entre los extremos. Con cripta-01, la fila ahora dice que no hay ruta entre los extremos y mide un viaje de 3 pasos de la sala 1 a la 4, que es la más lejana (costo 300). En la sesión anterior, dos `with` de una prueba habían quedado unidos en una sola línea, porque la barra de continuación se perdió al escribir el archivo desde la terminal. Seguía siendo Python válido; se separaron en este commit y desde entonces las pruebas se editan con la herramienta de edición. Pruebas: 1223 en WSL con Python 3.12.3, con los dos fallos esperados de los escenarios 7 y 8.

### 2.51 La medición de «ir a» en criptas reales parte de la sala inicial de sus datos

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Que el viaje medido en cada cripta del paquete sin conexión parta de la `sala_inicial` de sus datos generales y no de la primera sala del esqueleto, que en otras criptas puede no ser donde empieza el jugador.

Prompts utilizados:

```text
Cambia la suite del mapa conocido para que la sala de partida de la medición salga de la sala_inicial de los datos de la cripta, no de la primera sala del esqueleto. Un commit de código aparte, con prueba que cubra una cripta cuya sala inicial no sea la primera del esqueleto. Sin ids ni tamaños de cripta en el código, sin tocar archivos de Carlos, sin atribución de Claude, sin push. [...]
```

Uso en el proyecto: `cripta/benchmark/bench_mapa_conocido.py` (`criptas_sin_conexion`, `elegir_recorrido`, `medir_paso_de_ir_a`, `descripcion_del_recorrido`), `tests/test_bench_paquete_sin_conexion.py` y `cripta/README.md`.

Cambios realizados por el estudiante: El destino sigue siendo la última sala del esqueleto. Hubo que decidir qué pasa si la sala inicial ya es esa última: se mide hacia la más lejana alcanzable, y la fila dice el motivo. Las cuadrículas sintéticas no tienen datos generales, así que siguen partiendo de la primera sala y sus filas no cambian. Una `sala_inicial` que no está en el esqueleto es un error y no se mide en silencio desde otra sala. Para que el nombre no engañara, el motivo `ENTRE_EXTREMOS` pasó a llamarse `HACIA_LA_ULTIMA`. La prueba pedida copia el paquete de `datos_offline/` a una carpeta temporal y le cambia la sala inicial por la segunda sala de su propio esqueleto. Así pasa por la misma fuente sin conexión que el juego, sin escribir ningún id en la prueba. Hay otra con un mapa en el que partir de la primera sala o de la inicial da un viaje distinto (3 pasos contra 1), para comprobar que el camino medido de verdad sale de la inicial. En cripta-01 las dos salas coinciden y la medición no cambió. El README se actualizó en un commit de documentos aparte, porque describía la partida anterior. Pruebas: 1229 en WSL con Python 3.12.3, con los dos fallos esperados de los escenarios 7 y 8.

### 2.52 Auditoría de solo lectura de la segunda parte antes de la entrega

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Saber qué falta antes de la entrega del 18 de noviembre, revisando todas las ramas remotas sin modificar nada.

Prompts utilizados:

```text
Haz una AUDITORÍA DE SOLO LECTURA de todo el proyecto CRIPTA (segunda parte) para saber qué falta antes de la entrega del miércoles 18 de noviembre. LÍMITES: no modifiques archivos, no hagas commit, merge, rebase, checkout de ramas ni push, y no ejecutes ningún comando de spec-kit. [...] INFORME, en este orden: A. Mapa de ramas [...] M. Preguntas que necesitas que yo responda. [...] Registra la entrada en cripta/PROMPTS_LLM.md SOLO si el límite de "no modificar archivos" lo permite: si no, dímelo y dame el texto de la entrada para que la agregue yo.
```

Uso en el proyecto: ninguno directo; el informe orienta el trabajo pendiente. Esta entrada se agregó en la sesión siguiente, porque la auditoría no podía modificar archivos.

Cambios realizados por el estudiante: No se cambió ningún archivo. La auditoría encontró que la verificación de resolubilidad no existe en ninguna rama (ni spec 006, ni código, ni `--verificar`/`--forzar`); que `parte-2-Erick` contiene copias de archivos de `Parte_2-niebla-ir-a` y no arranca porque le falta `structures/mapa_conocido.py`; que `mauricio-logica-juego` ya está contenida en `Parte_2-niebla-ir-a`; y que unir esta rama con `Parte_2-API-cache-persistencia` solo choca en `PROMPTS_LLM.md` (simulado con `git merge-tree`, sin tocar la rama: 1266 pruebas pasan con Python 3.12.3). También encontró que `--replay --hasta` con un instante posterior al final rechazaba la consulta cuando el Apéndice B pide mostrar el estado final, que falta el escenario de varios eventos en el mismo instante, y que la consulta con 5000 acciones no está medida. No se pudo probar con Python 3.11 porque no hay uno instalado.

### 2.53 --replay --hasta con un instante posterior al final de la partida

Herramienta: Claude (Claude Opus 5.5), mediante Claude Code

Fecha: 2026-11-17

Objetivo: Cubrir el caso del Apéndice B «`--replay partida.log --hasta t` con t posterior al final de la partida: muestra el estado final e indica que la partida terminó antes», que la auditoría encontró sin escenario y con el comportamiento contrario.

Prompts utilizados:

```text
Haz tres cosas, en este orden, con commits pequeños y separados (spec aparte del código, código aparte de documentos) [...] 1. SPEC PRIMERO. Agrega en specs/003-linea-de-tiempo/spec.md un escenario de aceptación (y un caso borde) [...] No reenumeres FR existentes; si hace falta un FR nuevo, va al final. [...] 2. CÓDIGO. Corrige --hasta para ese caso. test_banderas_linea_de_tiempo.py:131 fija el comportamiento equivocado [...] NO toques la línea de tiempo de Carlos [...] 3. DOCUMENTOS (commit aparte): README con el conteo de pruebas actual y la versión de Python [...]
```

Uso en el proyecto: `specs/003-linea-de-tiempo/spec.md` (Historia 6, un caso borde y FR-025), `specs/003-linea-de-tiempo/tasks.md` (T021), `cripta/controller/application.py` (`_instante_reproducido`), `cripta/tests/test_banderas_linea_de_tiempo.py` y `cripta/README.md`.

Cambios realizados por el estudiante: Ninguna historia de la especificación 003 hablaba de consultar sin interacción, y el caso no encajaba en la Historia 2, que es la del rechazo. Por eso se agregó una Historia 6 corta. Hacía falta un requisito nuevo, porque FR-014 no dice qué pasa después del final: FR-025 quedó al final de los requisitos funcionales, sin reenumerar ninguno, y deja dicho que FR-009 (el rechazo en la partida en curso) no cambia. La diferencia se justifica en la historia: la partida en curso todavía puede llegar a ese instante, y la reproducida ya no. El arreglo quedó en `replay()` sin tocar la línea de tiempo: si el instante es posterior al reloj final, avisa y consulta el reloj final, que ya era consultable. La prueba que fijaba el rechazo se reemplazó por tres. Una comprueba el aviso, que viene antes del resumen, y el resumen del instante final, sin la vista. Otra comprueba que el instante final exacto no avisa (el caso borde). La tercera, que un instante negativo se sigue rechazando. Como el resumen final se obtiene con la misma reconstrucción, le alcanza el defecto ya reportado de las copias espaciadas. El README dejó de citar Python 3.14.6, que nadie del grupo usa para medir, y quedó en 3.11 o superior. Pruebas: 1231 en WSL con Python 3.12.3, con los dos fallos esperados de T052.
