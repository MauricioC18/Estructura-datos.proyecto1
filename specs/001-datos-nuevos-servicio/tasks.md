---
description: "Lista de tareas de la especificación 001: datos nuevos del servicio"
---

# Tasks: Datos nuevos del servicio

**Input**: Design documents from `/specs/001-datos-nuevos-servicio/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ubicacion-de-llaves.md

**Tests**: La constitución exige al menos una prueba automatizada por escenario de aceptación, y que la prueba cite el identificador del requisito. Las pruebas de cada historia se escriben antes que su implementación.

**Organization**: Tareas agrupadas por historia de usuario. Cada tarea cita entre paréntesis los requisitos que atiende.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: la historia de usuario a la que pertenece (US1, US2, US3, US4)
- Las rutas son relativas a la raíz del repositorio

---

## Phase 1: Setup

**Purpose**: Punto de partida verificado.

- [ ] T001 Correr `python -m unittest discover -s tests -t .` desde `cripta/` y confirmar que las 861 pruebas de la primera parte pasan antes de cambiar código (SC-005)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Las piezas del modelo y del contrato de fuentes que usan todas las historias.

- [ ] T002 [P] Agregar `DEFAULT_EXIT_COST = 100`, el atributo `cost` de `Door` (por defecto 100) y la propiedad `cost` de `Exit` en `cripta/model/room.py` (FR-001, FR-003, FR-005)
- [ ] T003 [P] Agregar la constante `Enemy.HUNTER = "cazador"` y el atributo `hunt_range` (por defecto `None`) en `cripta/model/enemy.py`, sin cambiar el comportamiento de los demás enemigos (FR-006, FR-007, FR-009)
- [ ] T004 [P] Crear `KeyLocation(key_id, room_id, enemy_id=None)` con la propiedad `is_dropped_by_enemy` en `cripta/model/key_location.py` (FR-011, FR-012)
- [ ] T005 Agregar la operación abstracta `ubicacion_de_llaves(id_cripta)`, la excepción `UbicacionDeLlavesNoDisponible(ErrorFuenteDatos)` y la descripción de cómo cada fuente entrega sus datos, en `cripta/adapters/fuente_datos.py` (FR-011, FR-016, FR-025)
- [ ] T006 Implementar `ubicacion_de_llaves` en los dobles de fuente de datos: en las pruebas (`cripta/tests/test_fuente_datos.py`, `cripta/tests/test_repositorio_cripta.py`, `cripta/tests/test_gestor_catalogo.py`, `cripta/tests/test_gestor_contenido.py`) consumiendo una solicitud como el servicio real, y en los benchmarks (`cripta/benchmark/bench_frecuencia_bloque2.py`, `cripta/benchmark/bench_precarga_contenido.py`) sin consumir, para no alterar sus mediciones (FR-013)

**Checkpoint**: el modelo y el contrato de fuentes aceptan los datos nuevos; las pruebas de la primera parte siguen pasando.

---

## Phase 3: User Story 1 - Jugar una cripta nueva que tiene cazadores (Priority: P1) 🎯 MVP

**Goal**: Una cripta con cazadores se juega sin detenerse, y cada cazador tiene su rango.

**Independent Test**: Traducir una ficha de cazador con rango 600 y un enemigo de cada comportamiento de la primera parte.

### Tests for User Story 1

- [ ] T007 [US1] Escribir en `cripta/tests/test_datos_nuevos_servicio.py` las pruebas de los escenarios US1.1 a US1.5: cazador con rango 600, comportamientos de la primera parte intactos, rango ignorado en un no cazador, cazador sin rango o con rango en null, rango inválido (0, negativo, decimal, texto, booleano), comportamiento desconocido, y que `rango` no produce aviso de campo desconocido (FR-006, FR-007, FR-008, FR-009, FR-010, FR-023)

### Implementation for User Story 1

- [ ] T008 [US1] En `cripta/repository/traductor.py`: agregar `("cazador", Enemy.HUNTER)` a `COMPORTAMIENTOS`, agregar `"rango"` a los campos de la clase enemigo en `CAMPOS_POR_CLASE`, validar el rango solo cuando el comportamiento es cazador y pasarlo como `hunt_range` al crear el enemigo (FR-006, FR-007, FR-008, FR-009, FR-010, FR-023)

**Checkpoint**: las pruebas de US1 pasan; una cripta con cazadores ya se puede jugar.

---

## Phase 4: User Story 2 - Cada salida tiene su costo de movimiento (Priority: P1)

**Goal**: Cada paso tiene su costo, igual en ambos sentidos, desde que se carga el esqueleto.

**Independent Test**: Traducir esqueletos con salidas con costo, sin costo, con costo en null, con un solo lado declarado, con lados distintos y de un solo sentido.

### Tests for User Story 2

- [ ] T009 [US2] Escribir en `cripta/tests/test_datos_nuevos_servicio.py` las pruebas de los escenarios US2.1 a US2.7: costo declarado, ausente y en null, igual en ambos sentidos, un solo lado declarado, lados distintos con aviso que nombra las dos salas y el valor usado, costos inválidos con sala, dirección y valor en el mensaje, paso de un solo sentido, costo disponible sin contenido descargado, y que `costo` no produce aviso de campo desconocido (FR-001, FR-002, FR-003, FR-004, FR-005, FR-023)

### Implementation for User Story 2

- [ ] T010 [US2] En `cripta/repository/traductor.py`: agregar `"costo"` a `CAMPOS_DE_SALIDA`, validar el costo declarado de cada salida, guardar en la tabla de salidas pendientes el costo que declaró el primer lado, combinarlo con el del lado de vuelta usando la regla de la sala de menor id, y aplicar el 100 solo cuando ningún lado lo declara (FR-001, FR-002, FR-003, FR-004, FR-005, FR-023)

**Checkpoint**: las pruebas de US1 y US2 pasan. Este es el incremento que desbloquea al resto del grupo (terreno, cazador e «ir a»).

---

## Phase 5: User Story 3 - La ubicación de las llaves está disponible antes de jugar (Priority: P2)

**Goal**: Antes de la primera acción, el programa conoce la ubicación de llaves; la obtiene una vez por versión, respetando el presupuesto.

**Independent Test**: Iniciar dos veces la misma cripta con una fuente simulada: la primera hace una consulta y la guarda; la segunda la lee del disco.

### Tests for User Story 3

- [ ] T011 [US3] Escribir en `cripta/tests/test_datos_nuevos_servicio.py` las pruebas de los escenarios US3.1 a US3.11 y sus casos borde: ruta y conteo en la fuente HTTP, incluido un reintento tras HTTP 429; lectura offline y archivo ausente; copia en disco, copia dañada y copia de otra versión; validación de entradas (sin id, sin sala, tipos equivocados, sala inexistente, campos adicionales); llaves repetidas y orden conservado entre servicio, disco y offline; momento del inicio (después del esqueleto, antes de contenido y fichas); falla de la consulta y presupuesto agotado; carga de partida guardada sin consulta; reproducción con la misma consulta; y la línea del reporte final (FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-025)

### Implementation for User Story 3

- [ ] T012 [P] [US3] Implementar `ubicacion_de_llaves` en `cripta/adapters/fuente_http.py` con la ruta `/criptas/<id>/llaves` (FR-011, FR-013)
- [ ] T013 [P] [US3] Implementar `ubicacion_de_llaves` en `cripta/adapters/fuente_offline.py`, leyendo `<carpeta>/criptas/<id>/llaves.json` y lanzando `UbicacionDeLlavesNoDisponible` si no existe; describir lo que entrega como «leída del paquete offline» (FR-015, FR-016, FR-025)
- [ ] T014 [P] [US3] Agregar `leer_ubicacion_de_llaves` y `guardar_ubicacion_de_llaves` a `cripta/adapters/almacen_cripta.py`, con el archivo `<id_cripta>/llaves.json`; una copia dañada se lee como ausente (FR-014, FR-021, FR-022)
- [ ] T015 [US3] Agregar `crear_ubicaciones_de_llaves` a `cripta/repository/traductor.py`: valida la respuesta, comprueba cada sala contra el esqueleto, conserva el orden y las repeticiones, ignora campos adicionales y no consulta el catálogo (FR-012, FR-017, FR-018, FR-019, FR-024)
- [ ] T016 [US3] En `cripta/repository/repositorio_cripta.py`: obtener la ubicación de llaves en `iniciar_partida` después del esqueleto y antes del contenido, con el argumento `obtener_ubicacion_de_llaves`; leer de la copia vigente o pedirla a la fuente y guardarla; tratar `UbicacionDeLlavesNoDisponible` como no disponible con aviso; exponer `ubicacion_de_llaves()`; y agregar la línea del origen al reporte final (FR-011, FR-014, FR-016, FR-020, FR-025)
- [ ] T017 [US3] En `cripta/controller/application.py`: la carga de una partida guardada llama a `iniciar_partida` sin obtener la ubicación de llaves (FR-011)
- [ ] T018 [P] [US3] En `cripta/tools/descargar_datos_offline.py`: descargar también la ubicación de llaves de cada cripta, con su prueba en `cripta/tests/test_descargar_datos_offline.py` (FR-015)

**Checkpoint**: las pruebas de US1, US2 y US3 pasan; la verificación de resolubilidad ya tiene sus datos.

---

## Phase 6: User Story 4 - Lo guardado por la primera parte no se mezcla con las criptas nuevas (Priority: P3)

**Goal**: Las copias de otra versión no se usan, y el aviso de cambio de contrato sigue funcionando.

**Independent Test**: Dejar en disco una copia de otra versión y cargar datos con un campo inventado.

- [ ] T019 [US4] Escribir en `cripta/tests/test_datos_nuevos_servicio.py` las pruebas de los escenarios US4.1 a US4.3: una copia de otra versión (esqueleto, contenido y ubicación de llaves) no se usa y se reemplaza por la vigente; fichas guardadas solo con la versión vigente del catálogo; `costo` y `rango` no producen aviso, y un campo inventado en una salida o en una ficha sí, una sola vez (FR-022, FR-023, FR-024)

**Checkpoint**: todas las historias pasan sus pruebas.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T020 Ajustar en `cripta/tests/test_repositorio_cripta.py` (y donde aparezcan) las aserciones que cuentan las solicitudes exactas de un inicio de partida, sumando la consulta de llaves (FR-013, SC-005)
- [ ] T021 Correr la suite completa desde `cripta/` y los pasos de `quickstart.md`, incluida una partida offline con las criptas de la segunda parte (SC-001, SC-002, SC-003, SC-004, SC-005)

---

## Dependencies & Execution Order

- **Phase 1** no depende de nada.
- **Phase 2** depende de la Phase 1 y bloquea todas las historias. T002, T003 y T004 se pueden hacer en paralelo; T006 depende de T005.
- **US1 (Phase 3)** depende de T003. **US2 (Phase 4)** depende de T002. US1 y US2 tocan el mismo archivo (`traductor.py`), así que se hacen una después de la otra.
- **US3 (Phase 5)** depende de T004, T005 y T006. T012, T013 y T014 se pueden hacer en paralelo; T015 depende de T004; T016 depende de T012 a T015; T017 depende de T016.
- **US4 (Phase 6)** depende de US2 y US3.
- **Phase 7** depende de todas las historias.

### Parallel Opportunities

```text
Phase 2:  T002 (room.py)  |  T003 (enemy.py)  |  T004 (key_location.py)
Phase 5:  T012 (fuente_http.py)  |  T013 (fuente_offline.py)  |  T014 (almacen_cripta.py)  |  T018 (descargar_datos_offline.py)
```

## Implementation Strategy

### MVP primero

1. Phases 1 y 2.
2. US1 y US2: con eso el traductor ya entiende cazadores y costos, que es lo que bloquea al resto del grupo.
3. **Parar y validar**: correr las pruebas, confirmar el commit y avisar al grupo.

### Entrega incremental

4. US3: ubicación de llaves, con la que arranca la verificación de resolubilidad.
5. US4 y Phase 7: invalidación por versión, avisos, conteos de solicitudes y validación con datos reales.
