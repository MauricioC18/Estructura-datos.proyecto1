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
