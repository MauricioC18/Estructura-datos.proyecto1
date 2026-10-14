# Registro de uso de herramientas de IA

Este archivo registra los prompts relacionados con el proyecto CRIPTA que se enviaron a un modelo de lenguaje, según lo exige la sección 10.3 del enunciado.

El código y el texto generados con ayuda de un modelo de lenguaje son responsabilidad del grupo. Cada integrante debe poder explicar y modificar lo entregado, independientemente de cómo se haya escrito.

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

## 3. Implementación de la agenda de eventos y del reloj virtual

Herramienta: Claude Opus, mediante Claude Code

Fecha: 2026-10-08

Objetivo: Verificar el estado real de los archivos del proyecto, implementar y probar la agenda de eventos, implementar el reloj virtual y la numeración de eventos, y documentar las decisiones correspondientes.

Prompts utilizados:

- [Pegar aquí el prompt maestro con el contexto del proyecto.]
- [Pegar aquí la lista de reglas obligatorias.]
- [Pegar aquí las preguntas sobre el reloj virtual y el contador de secuencia.]

Uso en el proyecto: Se implementaron `model/event.py`, `structures/event_queue.py` y `model/game_state.py`, junto con sus pruebas en `tests/test_event_queue.py` y `tests/test_game_state.py`. Se redactó `docs/DECISIONES.md` con la sección 4.1 y la sección del reloj virtual, y se actualizó `docs/ARQUITECTURA.md` con las interfaces de `EventQueue` y `GameState`.

Cambios realizados por el estudiante: [Indicar qué se revisó y qué se decidió.] Se corrigieron tres puntos del diseño previo tras consultar el enunciado: los identificadores de instancia pasaron de entero a texto, porque el servicio los entrega en ese formato; `is_empty()` pasó a descartar las raíces canceladas, porque antes podía informar que la agenda no estaba vacía cuando ya no quedaba ningún evento ejecutable; y se descartó restaurar el contador de secuencia al usar un pergamino de retroceso, al comprobar que el orden de los eventos no depende del valor absoluto de ese número.


--ST--
## 4. Revisión de interfaces existentes y contrato de la Persona 4

Herramienta: Claude (Claude Sonnet 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Revisar el contenido real de `docs/ARQUITECTURA.md`, `model/game_state.py`, `model/event.py` y `structures/event_queue.py` para detectar qué necesita la Persona 4 (MVC, interfaz, replay, benchmark e integración) de los módulos ya implementados.

Prompts utilizados:

- "listo, 2. game.py y actor.py no tienen nada en este momento, game state: [se pegó el código completo de `GameState`], event.py: [se pegó el código de `Event`], event_queue.py: [se pegó el código de `EventQueue`]" (acompañado del contenido completo de `docs/ARQUITECTURA.md`, en respuesta a la lista de archivos solicitada previamente).

Uso en el proyecto: Se utilizó la respuesta para identificar huecos que afectan a la Persona 4: la interfaz de `Game` aún no existe, `GameState` no permite restaurar el contador de secuencia ni el estado del generador aleatorio, `EventQueue` no permite listar los eventos activos, `Event` carece de los datos necesarios para serializar efectos, y la propiedad de `adapters/persistence.py` y de la tabla de puntajes no está asignada. También se utilizó para proponer un contrato `Game` ↔ controlador y un formato de log de replay.

Cambios realizados por el estudiante: [Indicar qué se verificó en el repositorio (por ejemplo, la coma final en `rewind_clock_to`), qué propuestas se aceptaron o descartaron y qué se acordó con el grupo.]

## 5. Resumen de puntos para la reunión del grupo

Herramienta: Claude (Claude Sonnet 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Condensar el análisis anterior en una lista de puntos concretos para discutir con el equipo.

Prompts utilizados:

- "Me puedes si resumir en puntos especificos para poder ir y ver con el equipo"

Uso en el proyecto: Se utilizó la respuesta como guía para la reunión del grupo: interfaz pendiente de `Game`, cambios solicitados a `GameState`, `EventQueue` y `Event`, reparto de archivos de persistencia, decisiones abiertas sobre el log de replay y formato de log propuesto.

Cambios realizados por el estudiante: [Indicar qué puntos se discutieron con el grupo y qué se decidió.]