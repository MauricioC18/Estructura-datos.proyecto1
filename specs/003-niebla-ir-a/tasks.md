# Tareas: Niebla de guerra y viaje automático «ir a»

**Especificación**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Modelo de datos**: [data-model.md](./data-model.md) · **Contratos**: [contracts/](./contracts/)

## Cómo leer esta lista

Formato: `- [ ] Tnnn [P] [Hn] [AB] [BLOQUEADA: …] Descripción, en archivo — requisitos`

- **[P]**: se puede hacer en paralelo con las otras [P] de su fase porque toca archivos distintos y no depende de una tarea incompleta de esa fase.
- **[H1]…[H7]**: la historia de la especificación a la que pertenece. Las tareas de base no llevan historia.
- **[AB]**: estrictamente necesaria para los seis casos del Apéndice B. Si falta tiempo, se hacen primero estas y se recorta el resto.
- **[BLOQUEADA: …]**: depende de un cambio en un archivo de otro integrante. Se dice quién y qué hace falta.
- **Cada tarea cita los requisitos que atiende. No hay tareas sin requisito.**
- **Cada prueba cita en su nombre o en su docstring el FR que comprueba** (§2.5), igual que `tests/test_cazador.py`.

**Restricciones que valen para todas las tareas** (constitución, principio I, y §6.2): las tablas son `TablaHash` con claves `int`; el orden de exploración es una `list` usada como pila; la búsqueda de ruta es `RutasMasBaratas`. No se usa ninguna estructura de la biblioteca estándar como índice o caché, ni bibliotecas de colas, de búsqueda binaria o de grafos. Las alternativas descartadas que se miden en la Fase 6 se escriben **solo** dentro del módulo de mediciones.

**El orden de las fases es el que pidió el grupo**, no el de prioridad de las historias: mapa conocido, antorcha y reversión; «ir a»; vista; exportar e importar; mediciones; documentación.

---

## Fase 1 — El mapa conocido, sin el motor (se puede empezar ya)

**Objetivo**: la estructura completa y probada en aislamiento, llamándola a mano desde las pruebas. No depende de nadie.

- [X] T001 [AB] Crear la estructura del mapa conocido en `cripta/structures/mapa_conocido.py`. Recibe el mapa de salas y el historial desde afuera (duck typing; el historial es opcional). Campos según `data-model.md`: exploradas (`TablaHash` id de sala → `True`), contadores de avistamiento (`TablaHash` id de sala → entero > 0), puertas recordadas (`TablaHash` clave `int` → `bool` abierta) y orden de exploración (`list` como pila). Clave de puerta: «id de `room_a` × 4 + índice de la dirección en que la puerta sale de `room_a`», con el índice según `DIRECTIONS` de `cripta/model/room.py`. Consultas `estado_de_sala(id)` → `explorada` / `avistada` / `desconocida`, `puerta_recordada(puerta)` → `abierta` / `cerrada` / `desconocida`, y `salas_exploradas()` en orden de exploración — FR-001, FR-004, FR-005, FR-007, FR-008, FR-033
- [X] T002 [AB] Agregar `jugador_entro(sala, antorcha_encendida)` en `cripta/structures/mapa_conocido.py` (depende de T001). Marca la sala como explorada si no lo estaba, suma 1 al contador de cada destino de sus salidas y observa todas sus puertas. Con la antorcha encendida, además explora cada vecina por **cualquier** salida, abierta o cerrada, **sin** observar las puertas de esas vecinas y sin tocar enemigos, objetos ni trampas: la estructura no los conoce — FR-002, FR-003, FR-006, FR-009, FR-010, FR-011, FR-034
- [X] T003 [AB] Agregar `puerta_cambio(puerta, sala_del_jugador)` en `cripta/structures/mapa_conocido.py` (depende de T001). Actualiza el recuerdo solo si la sala del jugador es una de las dos que conecta la puerta — FR-006, FR-007
- [X] T004 [AB] Anotar las inversas en el historial, en `cripta/structures/mapa_conocido.py` (depende de T002 y T003), con el patrón de `PlayerTrail.mark` (`cripta/structures/trail.py:47-53`). Explorar anota «deshacer la exploración de esta sala»: quitarla de exploradas, sacarla de la pila y restar a los contadores de sus destinos, borrando la entrada cuando llega a 0. Cambiar un recuerdo anota el valor anterior o «no se recordaba». **No anotar nada** si la sala ya estaba explorada o el recuerdo no cambia — FR-015, FR-035
- [X] T005 [AB] Agregar `vecinas_conocidas(sala)` en `cripta/structures/mapa_conocido.py` (depende de T001). Devuelve `(id, costo, salida)` por cada salida de la sala hacia una sala explorada cuya puerta se recuerda **abierta**. Las recordadas cerradas o desconocidas no se devuelven. Tiene la misma forma que `Game._open_exits_of` (`cripta/model/game.py:708`) — FR-012, FR-023, FR-027
- [X] T006 [P] [H1] Pruebas de los tres estados, en `cripta/tests/test_mapa_conocido.py` (depende de T002), con un mapa de salas armado a mano y llamando a `jugador_entro` directamente. Una prueba por cada escenario de la Historia 1 (1 a 4). Agregar: una sala alcanzada por dos salidas de salas exploradas, y una salida de un solo sentido, que según el plan no debe hacer avistada a la sala de origen — FR-001, FR-002, FR-003, FR-004, FR-005
- [X] T007 [P] [H2] Pruebas de la memoria de puertas, en `cripta/tests/test_mapa_conocido.py` (depende de T003), cambiando `closed` a mano y llamando a `puerta_cambio`. Escenarios 1 a 4 de la Historia 2. Incluir: un cambio con el jugador en `room_b` de la puerta, y otro con el jugador en una tercera sala, que no debe actualizar nada — FR-006, FR-007
- [X] T008 [P] [H3] [AB] Pruebas de la antorcha a nivel de estructura, en `cripta/tests/test_mapa_conocido.py` (depende de T002). Escenarios 1, 3, 4 y 5 de la Historia 3: las vecinas detrás de salidas abiertas y cerradas quedan exploradas; sus puertas lejanas quedan desconocidas; sus destinos pasan a avistados; sin antorcha solo se explora la sala. Agregar: una vecina que ya estaba explorada no cambia — FR-008, FR-009, FR-010, FR-011
- [X] T009 [P] [H6] [AB] Pruebas de la reversión a nivel de estructura, en `cripta/tests/test_mapa_conocido.py` (depende de T004), con un `History` real de `cripta/structures/history.py` y `begin_action`/`undo`. Casos: deshacer una entrada con antorcha que exploró la sala y cuatro vecinas (Historia 6, escenario 1); deshacer un cambio de recuerdo de puerta (escenario 2); una sala avistada por dos exploradas sigue avistada al deshacer una sola; lo explorado antes de abrir un intervalo no se puede deshacer; cuántas anotaciones deja una entrada (como mucho una por sala nueva más una por puerta cuyo recuerdo cambió) — FR-002, FR-015, FR-035
- [X] T010 [P] [H4] Prueba del proveedor de vecinas, en `cripta/tests/test_mapa_conocido.py` (depende de T005). Excluye salas no exploradas, puertas recordadas cerradas y puertas desconocidas aunque en realidad estén abiertas — FR-012, FR-023

**Punto de control**: el mapa conocido pasa sus pruebas sin que el motor sepa que existe.

---

## Fase 2 — El mapa conocido dentro de la partida

**Objetivo**: que la partida real explore, observe y revierta. Casi toda esta fase espera a Carlos.

- [ ] T011 [AB] [BLOQUEADA: Carlos — `cripta/model/game.py`] `Game` recibe el mapa conocido como colaborador opcional en `__init__` y en `Game.load`, con un objeto nulo que ignora los avisos cuando no se pasa, igual que `_NoHistory` (`game.py:48`) — FR-003, FR-012
- [ ] T012 [AB] [BLOQUEADA: Carlos — `cripta/model/game.py`] (depende de T011) Aviso `jugador_entro(sala, self.torch_lit)`: en `_begin_new_game` (`game.py:159`), antes de activar enemigos; y en `move` (`game.py:304-307`), justo después de `history.assign(self.player, "room_id", …)` y antes de `_activate_enemies_in` y `_trigger_traps` — FR-002, FR-003, FR-006, FR-009, FR-037
- [ ] T013 [AB] [BLOQUEADA: Carlos — `cripta/model/game.py`] (depende de T011) Aviso `puerta_cambio(puerta, self.player.room_id)`: en `open_door` (`game.py:354`) y en `_close_door` (`game.py:1050`), justo después de cambiar `closed`. El retroceso **no** avisa, y eso es lo correcto — FR-006
- [ ] T014 [AB] [BLOQUEADA: T011] Armar el mapa conocido en la partida nueva, en `cripta/controller/application.py` `build_game` (`application.py:91`), con el mismo `history` que el rastro, y pasarlo a `Game` y al `GameController` (T025). **No integrar antes de T011**: pasarle a `Game` un parámetro que todavía no acepta hace fallar el inicio de toda partida — FR-003, FR-015
- [ ] T015 [H2] [AB] [BLOQUEADA: T012, T013] Pruebas con el motor de la memoria de puertas, en `cripta/tests/test_niebla.py`. Abrir una puerta con cierre automático, alejarse, dejar que se cierre, comprobar que se sigue recordando abierta y que al volver se corrige (Historia 2, escenarios 2 y 3). Un cierre automático con el jugador presente se observa en ese instante (escenario 4). Para SC-002: en cada instante de una partida con cierres automáticos, el recuerdo de cada puerta de la sala del jugador coincide con su estado real — FR-006, FR-007
- [ ] T016 [P] [H3] [AB] [BLOQUEADA: T012] Pruebas con el motor de la antorcha, en `cripta/tests/test_niebla.py`. Caso del Apéndice B: encender la antorcha, entrar a una sala cuya vecina tiene enemigos dormidos y una trampa armada; la vecina queda explorada, sus enemigos siguen inactivos y sin turno en la agenda, y la trampa sigue armada (Historia 3, escenarios 1 y 2). Encender la antorcha dentro de una sala no explora nada (escenario 6). La antorcha apagada a mitad de camino deja de explorar — FR-009, FR-010, FR-011, FR-037
- [ ] T017 [P] [H6] [AB] [BLOQUEADA: T012, T013] Pruebas con el motor de la reversión, en `cripta/tests/test_niebla.py`. Caso del Apéndice B: entrar con la antorcha y usar un pergamino; las salas exploradas en esa entrada vuelven a su estado anterior (Historia 6, escenario 1). Un recuerdo de puerta actualizado durante la acción revertida vuelve al anterior (escenario 2). Revertir no cuenta como observar. Usar `tests/verificar_retroceso.py` si sirve para comparar antes y después — FR-015
- [ ] T018 [P] [H6] [BLOQUEADA: T012] Prueba de determinismo, en `cripta/tests/test_niebla.py`: la misma cripta, semilla y acciones jugadas dos veces dan el mismo conocimiento en cada instante (Historia 6, escenario 4) — FR-017
- [ ] T019 [P] [BLOQUEADA: T012] Prueba de no interferencia, en `cripta/tests/test_niebla.py`: la misma partida con y sin mapa conocido da las mismas decisiones de enemigos, el mismo reloj y el mismo resultado — FR-013

**Punto de control**: una partida real tiene niebla de guerra, antorcha y reversión.

---

## Fase 3 — Viaje automático «ir a»

**Objetivo**: el viaje completo con sus motivos de parada. Las reglas van en el modelo y el bucle en el controlador (plan, decisión 8).

- [X] T020 [AB] Crear `cripta/model/viaje.py` con la validación de la orden (depende de T001). Recibe el estado de la partida y el mapa conocido explícitamente, para no depender de T011. Acepta solo una sala explorada distinta de la actual. Una sala no explorada y un id inexistente se rechazan con **el mismo mensaje**. El rechazo no consume tiempo ni toca nada — FR-022
- [X] T021 [AB] Agregar el siguiente paso en `cripta/model/viaje.py` (depende de T005, T020): construir `RutasMasBaratas(mapa.vecinas_conocidas, origen=destino, corte=None)` desde `cripta/structures/rutas_mas_baratas.py` y devolver `primer_paso_desde(sala_del_jugador)` (una salida), o nada si no hay ruta. Se recalcula en cada llamada, sin reutilizar nada (plan, decisión 7) — FR-023, FR-024, FR-026, FR-027
- [X] T022 [AB] Agregar los motivos de parada en `cripta/model/viaje.py` (depende de T020) — FR-025, FR-028, FR-029, FR-030. Son dos funciones:
  - (1) **Antes de mover**: «¿hay enemigos vivos en esta sala?», para la sala destino del paso, con su contenido ya cargado. Cuenta los vivos, activos o dormidos (FR-028 (b)); los muertos no.
  - (2) **Después del paso**: recibe la partida, el destino, la vida del jugador antes del paso, la respuesta de (1) y si el paso fue rechazado, y devuelve la lista **en el orden de FR-028**: `llegada`, `enemigos`, `daño`, `sin_ruta`, `partida_terminada`, `contenido_no_disponible`.

  Los enemigos se toman **solo** de la respuesta de (1), nunca del estado después del ciclo: un enemigo que llega a la sala del jugador sin atacarlo no es motivo, y uno que estaba al entrar sí lo es aunque se haya ido. Partir de una sala con enemigos no es un motivo.
- [X] T023 [P] [AB] Agregar un método para escribir un comentario en la bitácora, en `cripta/replay/replay_log.py` `ReplayLogWriter`. Escribe `# <texto>` y vacía a disco igual que `_write_line`. La lectura ya ignora esas líneas, así que no se toca — FR-031
- [X] T024 [P] [AB] Interpretar `ir a <sala>` en `cripta/controller/commands.py`: un comando nuevo con argumento entero, que **no** es acción del modelo (`is_game_action` sigue en falso para él) y aparece en la ayuda. Sin argumento o con un argumento no entero, error de sintaxis como los demás comandos — FR-022
- [ ] T025 [AB] Bucle del viaje en `cripta/controller/game_controller.py` (depende de T021, T022, T023, T024) — FR-022, FR-025, FR-026, FR-028, FR-029, FR-031, FR-032
  - `GameController` recibe el mapa conocido como **parámetro opcional del constructor**. Si no se pasa, usa el de la partida, que existe desde T011. Las pruebas T027 y T028 lo pasan explícitamente.
  - Validar con `viaje`; si se acepta, escribir el comentario `ir a <sala>` en la bitácora.
  - Mientras no haya motivo de parada:
    1. Pedir el siguiente paso. Sin paso, el motivo es `sin_ruta` y no se mueve.
    2. Cargar el contenido de la sala destino con `_load_destination` (`game_controller.py:72`), que no hace nada si ya está cargada. Si falla, el motivo es `contenido_no_disponible` y no se mueve.
    3. Preguntar a `viaje` si hay enemigos vivos en esa sala (T022 (1)).
    4. Guardar la vida del jugador.
    5. Ejecutar `execute(Command(MOVE, dirección))`, el mismo camino que un `mover` escrito a mano: registra en la bitácora y precarga.
    6. Pedir los motivos (T022 (2)).
  - Devolver los motivos para la vista.
- [ ] T026 Atender `ir a` en el bucle de comandos de `cripta/controller/application.py` (`_command_loop`, `application.py:365`) y mostrar los motivos (depende de T025; la presentación es T035) — FR-029
- [ ] T027 [P] [H4] [AB] Pruebas del viaje que no necesitan los avisos del motor, en `cripta/tests/test_ir_a.py`, con el conocimiento armado a mano llamando a `jugador_entro`. Caso del Apéndice B: `ir a` hacia una sala no explorada se rechaza y el reloj no cambia (Historia 4, escenario 1). También: id inexistente con el mismo mensaje; la sala actual se rechaza; ruta de menor costo frente a la de menos salas (escenario 2); desempate por menor id (escenario 3); no abre una puerta cerrada aunque tenga la llave (escenario 4); cada paso consume su intervalo y entre pasos corren los eventos (escenario 5); la bitácora tiene `# ir a …` y una línea `mover` por paso, y reproducirla da la misma partida (escenario 6 y SC-003). Para SC-008: a lo largo de un viaje completo de varios pasos, cada salida atravesada tenía su puerta recordada abierta justo antes del paso, y ninguna puerta pasó de cerrada a abierta por el viaje. Además, en `cripta/tests/test_replay_log.py`: el método de comentario escribe `# <texto>` y `read_replay_log` lo ignora — FR-012, FR-022, FR-023, FR-024, FR-025, FR-027, FR-031
- [ ] T028 [P] [H5] [AB] Pruebas de motivos de parada que no necesitan los avisos del motor, en `cripta/tests/test_ir_a.py`. Caso del Apéndice B: la ruta pasa por una sala con enemigos dormidos; al entrar se activan y el viaje se detiene (Historia 5, escenario 2). Caso del Apéndice B: viaje de varios pasos y luego un pergamino; vuelve a la sala anterior al último paso con el reloj de entonces, y no ocurre ningún paso más (escenario 7). También: llegada (escenario 4); daño por ataque, por veneno y por trampa (escenario 3); llegada a un destino con enemigos informa los dos motivos en orden (escenario 6); se puede partir de una sala con enemigos; un enemigo que llega a la sala del jugador durante el ciclo **sin atacarlo** no detiene el viaje (caso borde); un enemigo que estaba en la sala al entrar y se fue antes de la siguiente decisión **sí** lo detiene; un enemigo muerto en la sala no lo detiene; la partida termina a mitad de viaje; con un repositorio de prueba que lanza un error de datos, el paso se rechaza sin consumir tiempo — FR-028, FR-029, FR-030, FR-032
- [ ] T029 [H5] [AB] [BLOQUEADA: T012, T013] Prueba del caso del Apéndice B de la puerta recordada, en `cripta/tests/test_ir_a.py`. El mapa recuerda abierta una puerta que en realidad está cerrada; al llegar a la sala desde la que se observa, el recuerdo se corrige y la ruta se recalcula; si no queda ruta, el viaje se detiene con `sin_ruta` y el reloj queda donde lo dejó el último paso (Historia 5, escenario 1) — FR-006, FR-026, FR-028

**Punto de control**: con los seis casos del Apéndice B pasando, el núcleo de la capacidad está completo.

---

## Fase 4 — Lo que ve el jugador

**Objetivo**: comando `mapa`, salidas según el conocimiento y cazadores distinguidos.

- [X] T030 [P] [H7] Interpretar `mapa` en `cripta/controller/commands.py`: sin argumentos, no es acción del modelo y aparece en la ayuda — FR-018, FR-019
- [ ] T031 [H7] Armar la vista del mapa conocido en `cripta/controller/application.py` (depende de T001): las salas exploradas ordenadas por id con `sort` de `cripta/structures/sorting.py`; por cada salida, dirección, costo, estado recordado y destino (id si el destino está explorado; ninguno si está avistado) — FR-005, FR-018
- [ ] T032 [H7] Cambiar `room_view` (`cripta/controller/application.py:172`) para que las salidas salgan del conocimiento: estado recordado en lugar de `door.is_open`, y destino sin id cuando está avistado — FR-012, FR-020
- [ ] T033 [H7] Atender `mapa` en `_command_loop` de `cripta/controller/application.py` sin pasar por el controlador del modelo ni por la bitácora (depende de T030, T031) — FR-019
- [ ] T034 [H7] [BLOQUEADA blanda: Carlos — `cripta/model/game.py:77-82`] Indicar en `EnemyView` si el enemigo es cazador y llenarlo en `visible_state`. Si Carlos no puede, se deduce en `cripta/controller/application.py` buscando el enemigo por id en `game.enemies` — FR-021
- [ ] T035 [H7] Presentación en `cripta/view/console_view.py` (depende de T031, T032, T034): mostrar el mapa conocido según `contracts/comandos.md`; «hay algo en esa dirección» para los destinos avistados; la marca de cazador en la lista de enemigos; los motivos de parada del viaje — FR-018, FR-020, FR-021, FR-029
- [ ] T036 [P] [H7] Pruebas de la vista, en `cripta/tests/test_console_view.py` y `cripta/tests/test_commands.py`. Escenarios 1 a 5 de la Historia 7: mapa con salas exploradas y sus salidas; avistada sin id ni nombre; `mapa` no cambia el reloj ni la bitácora; cazador marcado; desconocida ausente. Interpretación de `mapa` e `ir a`. Ajustar **solo** las pruebas existentes que fijan el id de destinos no explorados, que es la excepción de SC-009 — FR-018, FR-019, FR-020, FR-021, FR-029

---

## Fase 5 — Exportar e importar el conocimiento

**Objetivo**: guardar y cargar la partida conserva el conocimiento.

- [X] T037 [H6] Agregar `exportar()` e `importar(exploradas, puertas)` en `cripta/structures/mapa_conocido.py` (depende de T004). Exportar devuelve los ids explorados en orden de exploración y los pares `(clave int, abierta bool)` en orden creciente de clave, ordenados con `sort` de `cripta/structures/sorting.py`. Importar rehace los contadores sumando las salidas de cada explorada y **no** anota nada en el historial — FR-014, FR-016
- [X] T038 [P] [H6] Prueba de ida y vuelta, en `cripta/tests/test_mapa_conocido.py` (depende de T037): exportar, importar en un mapa conocido nuevo y comparar estados de sala, recuerdos de puerta y orden de exploración — FR-014
- [ ] T039 [H6] [BLOQUEADA: Carlos y Erick — una sola subida de versión del formato en `cripta/adapters/almacen_partida.py`] Guardar las dos listas en el bloque global y, al cargar, armar el mapa conocido con el historial en `construir_juego` y `construir_juego_reversible` (`almacen_partida.py:1055`, `:1126`). Sube `VERSION_DEL_FORMATO` (`almacen_partida.py:94`) — FR-014
- [ ] T040 [P] [H6] [BLOQUEADA: T039] Prueba de guardar y cargar, en `cripta/tests/test_almacen_partida.py`: tras cargar, el conocimiento es idéntico (Historia 6, escenario 3, y SC-005). Ajustar **solo** las pruebas que fijan la versión del formato, que es la excepción de SC-009 — FR-014
- [ ] T041 [H6] [BLOQUEADA: Erick — decisión de su plan] Acordar con la línea de tiempo cómo se recupera el conocimiento por instante: las anotaciones del historial si reconstruye hacia atrás, o la exportación como copia en el punto de control si reconstruye hacia adelante. **La prueba de FR-016 vive en la especificación de la línea de tiempo, de Erick**: esta especificación no tiene escenario propio para FR-016 porque la consulta por instante está fuera de su alcance. Esta tarea solo cierra la interfaz en `specs/003-niebla-ir-a/contracts/interfaz-mapa-conocido.md` — FR-016

---

## Fase 6 — Mediciones

**Objetivo**: respaldar FR-033 a FR-036 con `--bench`, midiendo la alternativa descartada.

- [ ] T042 Crear `cripta/benchmark/bench_mapa_conocido.py` con `run()` que devuelve `Measurement` como los demás (depende de T005 y T021) — FR-033, FR-034, FR-035, FR-036. Dos fuentes, sin ningún tamaño ni id de cripta en el código:
  - (1) criptas sintéticas deterministas por semilla en tres tamaños crecientes de mapa conocido, generadas por el propio módulo;
  - (2) para la medición 5, el mapa conocido completo de **cada** cripta del paquete sin conexión, cargada con `FuenteOffline` (`cripta/adapters/fuente_offline.py`) y reportada con el id que traen sus datos. Si el paquete no contiene la cripta de referencia, la suite lo informa y sigue solo con las sintéticas, sin fallar.

  Las cinco mediciones de la tabla del plan, cada una **contra su alternativa descartada escrita dentro de este módulo**:
  - lista recorrida en cada consulta, frente a la tabla de exploradas;
  - clave de puerta de texto, frente a la entera;
  - recalcular todas las avistadas al explorar, frente a los contadores;
  - copiar el conocimiento antes de cada acción, frente a las anotaciones;
  - reutilizar la ruta del viaje, y selección lineal del mínimo sin montículo, frente a recalcular con `RutasMasBaratas`.
- [ ] T043 [P] Agregar la suite a `SUITES` en `cripta/benchmark/benchmark.py` — FR-036
- [ ] T044 (depende de T042) Correr `--bench` y anotar los resultados reales en una sección «Resultado de las mediciones» de `specs/003-niebla-ir-a/plan.md`: los tres tamaños sintéticos y, en cuanto el paquete sin conexión contenga la cripta de referencia, la fila de esa cripta, que es la que comprueba FR-036 y SC-006. Si un paso de «ir a» pasa de 5 ms, cambiar a la alternativa medida y corregir el plan — FR-036

---

## Fase 7 — Documentación y cierre

- [ ] T045 Escribir la sección de §5.3 en `cripta/docs/DECISIONES.md` con los seis apartados de P1 §8, enlazando la especificación y el plan, e indicando si la decisión final coincide con la del plan y, si no, qué medición la cambió (§7.1) (depende de T044) — FR-033, FR-034, FR-035, FR-036
- [ ] T046 [P] Agregar `mapa` e `ir a <sala>` a la tabla de comandos de `cripta/README.md`, y cómo correr las pruebas de aceptación de esta capacidad — FR-018, FR-022
- [ ] T047 Correr la suite completa desde `cripta/` y comprobar que solo cambiaron las pruebas que admite SC-009 — FR-013, FR-017

---

## Dependencias

```text
Fase 1  T001 → T002, T003, T005 → T004
        T006–T010 detrás de su tarea
Fase 2  T011 (Carlos) → T012, T013 (Carlos) → T015–T019
        T011 → T014 (no integrar antes)
Fase 3  T020 → T021, T022;  T023, T024 libres;  T021+T022+T023+T024 → T025 → T026
        T027, T028 detrás de T025;  T029 además detrás de T012 y T013
Fase 4  T030, T031, T032 libres;  T034 (blanda, Carlos) → T035 → T036
Fase 5  T004 → T037 → T038;  T039 (Carlos + Erick) → T040;  T041 (Erick)
Fase 6  T005 + T021 → T042 → T043, T044 → T045
Fase 7  T047 al final
```

### Lo que se puede empezar ya, sin esperar a nadie

T001–T010, T020–T028, T030–T033, T035–T038 (T035 con la alternativa de T034), y T042–T047 en su orden.

### Lo que está bloqueado, y por quién

| Tarea | Bloqueada por | Qué hace falta |
| --- | --- | --- |
| T011, T012, T013 | **Carlos** | Colaborador y dos avisos en `cripta/model/game.py` |
| T014 | T011 | Que `Game` acepte el mapa conocido |
| T015, T016, T017, T018, T019, T029 | T012 / T013 | Pruebas con el motor real |
| T034 | **Carlos** (blanda) | Campo de cazador en `EnemyView`; hay alternativa |
| T039, T040 | **Carlos y Erick** | Una sola subida de la versión del formato de partida |
| T041 | **Erick** | Cómo reconstruye la línea de tiempo |

### Si falta tiempo: lo mínimo para los seis casos del Apéndice B

Las [AB]: T001–T005, T008, T009, T011–T017, T020–T025, T027–T029. Con T026 la orden se puede usar desde la consola. Todo lo demás (vista del mapa, exportar e importar, mediciones y documentación) se puede recortar, **pero FR-014, FR-018 a FR-021 y FR-033 a FR-036 quedarían sin cumplir**, y FR-036 es un límite de §6.1.

| Caso del Apéndice B | Prueba | Tareas de implementación |
| --- | --- | --- |
| `ir a` hacia una sala no explorada | T027 | T001, T020, T024, T025 |
| Puerta recordada abierta que está cerrada | T029 | T001–T005, T012, T013, T021, T022, T025 |
| `ir a` entra a una sala con enemigos dormidos | T028 | T020–T025 |
| Antorcha: explora sin activar enemigos ni trampas | T008, T016 | T001, T002, T011, T012 |
| Pergamino revierte una entrada con antorcha | T009, T017 | T004, T011–T014 |
| Pergamino después de un viaje | T028 | T025 |

## Notas

- **Registro de prompts.** Las invocaciones de spec-kit y de implementación se registran en `cripta/PROMPTS_LLM.md`, como exigen §2.6 y la constitución. No figura como tarea porque no atiende ningún FR de esta especificación, y la regla es que no haya tareas sin requisito.
- **Enemigos vivos.** FR-028 (b) ya dice «enemigos vivos, activos o dormidos» (hallazgo A1 de la revisión). Esa corrección de la especificación va en un commit propio, antes de implementar T022.
- **Terminología**: ver el Resumen de `plan.md`.
