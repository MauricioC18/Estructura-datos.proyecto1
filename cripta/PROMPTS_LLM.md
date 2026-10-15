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

## 6. API, caché y persistencia (Persona 2)

Registro de la Persona 2. Los prompts se reproducen tal cual, incluidos los errores de escritura. En la entrada 6.2 se pegaron dos textos de un compañero, que se describen en lugar de copiarlos. Algunos mensajes de coordinación (por ejemplo, avisos de pausa) no se registraron porque no pidieron nada sobre el proyecto.

### 6.1 Análisis del enunciado y del programa del curso

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

### 6.2 Revisión del flujo de trabajo y de la distribución del grupo

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

### 6.3 Fecha de entrega y plan de trabajo

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-10

Objetivo: Planificar el trabajo del bloque 2 según la fecha de entrega.

Prompts utilizados:

```text
la fecha de entrega esta en duda ya que la primera fecha dada es para mañana 11 de octubre pero recordamos que el profesor dio tiempo al 18 de octubre
```

Uso en el proyecto: Plan de trabajo diario del bloque 2 para las dos fechas posibles de entrega.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.4 Análisis del bloque 2

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-10

Objetivo: Analizar los requisitos, decisiones abiertas e interfaces del bloque 2 (API, caché y persistencia).

Prompts utilizados:

```text
Si, iniciemos con el análisis del bloque 2 que me corresponde y luego vemos la tabla hash ya que anteriormente mencionaste que me debe corresponder a mi
```

Uso en el proyecto: Lista de requisitos del bloque 2, costo en solicitudes de una partida, decisiones D1 a D9 e interfaces a acordar con el grupo.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.5 Supuestos para lo que el enunciado no define

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

### 6.6 `dict` frente a una tabla hash propia

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Comparar la eficiencia del `dict` de Python contra una tabla hash propia, con una medición de prueba.

Prompts utilizados:

```text
Que tan eficiente es utilizar bibliotecas de python en lugar de tablas hash ya que en si mismas son tablas hash en su funcionamiento?
```

Uso en el proyecto: Script de comparación `dict` contra tabla propia; confirmó que la restricción de §7 tiene un costo medible y que la función hash es lo que más pesa.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.7 Elección de la función hash e implementación de `TablaHash`

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

### 6.8 Benchmark de la tabla hash e interfaz `FuenteDatos`

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

### 6.9 Benchmark con calentamiento del procesador

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

### 6.10 Métodos abstractos de `FuenteDatos`

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Entender qué son los métodos abstractos de `FuenteDatos` y quién los implementa.

Prompts utilizados:

```text
Del archivo FuenteDatos tengo una duda, los metodos que estan solo con comentarios es porque falta la implementacion y tiene que hacerlo alguno de los compañeros segun la parte que tienen que hacer ?
```

Uso en el proyecto: Aclaración: `FuenteHttp` y `FuenteOffline` implementan el contrato; son parte del bloque 2.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.11 `FuenteHttp`, `FuenteOffline` y descarga de datos para el modo offline

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

### 6.12 Carpeta desde la que se ejecutan las pruebas

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Saber desde qué carpeta ejecutar las pruebas y la herramienta de descarga.

Prompts utilizados:

```text
Para probar con los comandos de test que me diste, los pruebo desde la carpeta cripta que me diste en el zip??
```

Uso en el proyecto: Instrucciones para ejecutar las pruebas desde la carpeta correcta.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.13 Primera conexión real con el API

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

### 6.14 Revisión de los datos reales de `cripta-01`

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

### 6.15 Caché LRU del catálogo

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Implementar la caché LRU del catálogo (`CacheCatalogo`) con sus pruebas y su benchmark.

Prompts utilizados:

```text
Si, implementala asi
```

Uso en el proyecto: `structures/cache_catalogo.py`, sus pruebas y su benchmark.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.16 Almacén de fichas en disco

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Implementar el almacén de fichas en disco (`AlmacenFichas`, decisión D6) con sus pruebas y su benchmark.

Prompts utilizados:

```text
Si, sigamos con el almacen en disco de la parte D6
```

Uso en el proyecto: `adapters/almacen_fichas.py`, sus pruebas y su benchmark.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.17 Proyecto en una sola carpeta, con README y verificación automática

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Ordenar el proyecto en una sola carpeta lista para abrir y ejecutar, con README y un script que corre las pruebas y los benchmarks y guarda los resultados.

Prompts utilizados:

```text
Dame los archivos ordenados como deberian de estar para abrir la carpeta y ejecutar en consola los comandos que me pides probar y pasarte los resultados
```

Uso en el proyecto: README, `tools/ejecutar_verificaciones.py` y proyecto ordenado en una sola carpeta.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.18 Resultados de la verificación y diseño del `GestorCatalogo`

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

### 6.19 Implementación del `GestorCatalogo`

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

### 6.20 Comprobación de un archivo enviado aparte

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Confirmar que el archivo `gestor_catalogo.py` enviado aparte es idéntico al que viene dentro del zip.

Prompts utilizados:

```text
Ya hare las pruebas pero tengo la duda si el archivo gestor catalogo que me das es el mismo que esta dentro del zip
```

Uso en el proyecto: Confirmación de que el archivo enviado aparte era idéntico al del proyecto.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.21 Segunda medición y diseño de la precarga por BFS

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

### 6.22 `GestorContenido` con precarga por BFS

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-13

Objetivo: Implementar el `GestorContenido` con la precarga por BFS (grafo de salas, pruebas y benchmark de solicitudes).

Prompts utilizados:

```text
Continuemos con el proyecto, implementa el GestorContenido con la precarga por BFS y una vez que este listo, corro la tercera medicion de los test para verificar que todo este funcionando correctamente\
```

Uso en el proyecto: `structures/grafo_salas.py`, `repository/gestor_contenido.py`, sus pruebas y `benchmark/bench_precarga_contenido.py`.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.23 Tercera medición y medianas

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

### 6.24 `RepositorioCripta`, persistencia por versión y guía para el grupo

Herramienta: Claude (Claude Opus 5.5), mediante la interfaz de chat de claude.ai

Fecha: 2026-10-14

Objetivo: Implementar el `RepositorioCripta` (punto de entrada del bloque 2), la persistencia del esqueleto y del contenido, la verificación de versiones para `--replay`, una herramienta de simulación y un documento de integración para el grupo.

Prompts utilizados:

```text
Sigamos con el RepositorioCripta, avancemos en los archivos todo lo que sea posible para actualizar el proyecto en github y asi los demas puedan avanzar y con eso pueda yo solicitarle los archivos necesarios para poder terminar este bloque del proyecto
```

Uso en el proyecto: `repository/repositorio_cripta.py`, `adapters/almacen_cripta.py`, `tools/simular_partida_bloque2.py` y `docs/BLOQUE_2_PARA_EL_GRUPO.md`.

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.25 Presupuesto de solicitudes medido contra el API real

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

### 6.26 `Traductor` y clases de sala, objeto y trampa

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

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]

### 6.27 Verificación del `Traductor` contra el API real

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

Cambios realizados por el estudiante: [Indicar qué se revisó, modificó o decidió después de evaluar la propuesta.]
