---
description: "Lista de tareas de la especificación 004: datos nuevos del servicio"
---

# Tasks: Datos nuevos del servicio

**Input**: Design documents from `/specs/004-datos-nuevos-servicio/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ubicacion-de-llaves.md

**Tests**: La constitución exige al menos una prueba automatizada por escenario de aceptación, y que la prueba cite el identificador del requisito. Aquí lo cita en su nombre (`test_fr013_...`) y en el nombre de su clase, que dice que es de la especificación 004. Las pruebas de cada historia se escriben antes que su implementación.

**Organization**: Tareas agrupadas por historia de usuario. Cada tarea cita entre paréntesis los requisitos que atiende.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: la historia de usuario a la que pertenece (US2, US3, US4)
- Las rutas son relativas a la raíz del repositorio

## Cubierto por otras especificaciones

Revisión del 2026-11-17, al integrar `main`. Estas tareas de la versión anterior de esta lista ya las hicieron las especificaciones 001 y 002 y no se repiten:

- Costo en la puerta, `Exit.cost` y `DEFAULT_EXIT_COST` en `cripta/model/room.py`; validación y combinación del costo en el traductor; `"costo"` como campo conocido (specs/001-terreno-costo-salidas).
- `Enemy.HUNTER` y el rango del cazador, que en el modelo se llama `pursuit_range`; validación del rango en el traductor; `"rango"` como campo conocido (specs/002-cazador-ruta-mas-barata).
- Las pruebas de las historias 1 y 2 están en `cripta/tests/test_traductor.py` y `cripta/tests/test_cazador.py`, salvo la del costo en null.

---

## Phase 1: Setup

**Purpose**: Punto de partida verificado.

- [x] T001 Correr `python -m unittest discover -s tests -t .` desde `cripta/` después de integrar `main` y confirmar que pasan las 1010 pruebas (SC-005)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Las piezas del modelo y del contrato de fuentes que usa la ubicación de llaves.

- [x] T002 [P] Crear `KeyLocation(key_id, room_id, enemy_id=None)` con la propiedad `is_dropped_by_enemy` en `cripta/model/key_location.py` (FR-011, FR-012)
- [x] T003 Agregar la operación abstracta `ubicacion_de_llaves(id_cripta)`, la excepción `UbicacionDeLlavesNoDisponible(ErrorFuenteDatos)` y `forma_de_obtencion()`, que describe cómo entrega sus datos cada fuente, en `cripta/adapters/fuente_datos.py` (FR-011, FR-016, FR-025)
- [x] T004 Implementar `ubicacion_de_llaves` en los dobles de fuente de datos: en las pruebas (`cripta/tests/test_fuente_datos.py`, `cripta/tests/test_repositorio_cripta.py`, `cripta/tests/test_gestor_catalogo.py`, `cripta/tests/test_gestor_contenido.py`) consumiendo una solicitud como el servicio real, y en los benchmarks (`cripta/benchmark/bench_frecuencia_bloque2.py`, `cripta/benchmark/bench_precarga_contenido.py`) sin consumir, para no alterar sus mediciones (FR-013)

**Checkpoint**: el contrato de fuentes acepta la operación nueva y las pruebas existentes siguen pasando.

---

## Phase 3: User Story 2 - Costo en null (Priority: P1)

**Goal**: Una salida con `"costo": null` vale 100, como permite el contrato 1.1.0.

**Independent Test**: Traducir un esqueleto con una salida cuyo costo viene en null.

- [x] T005 [US2] Escribir en `cripta/tests/test_datos_nuevos_servicio.py` la prueba del escenario US2.2: una salida con costo en null vale 100, también cuando el lado de vuelta declara un costo (FR-001, FR-003)
- [x] T006 [US2] En `cripta/repository/traductor.py`, `_costo_de_salida` trata un costo en null como no declarado (FR-001)

**Checkpoint**: las criptas que declaran costos en null se pueden cargar.

---

## Phase 4: User Story 3 - La ubicación de las llaves está disponible antes de jugar (Priority: P2)

**Goal**: Antes de la primera acción, el programa conoce la ubicación de llaves; la obtiene una vez por versión, respetando el presupuesto.

**Independent Test**: Iniciar dos veces la misma cripta con una fuente simulada: la primera hace una consulta y la guarda; la segunda la lee del disco.

### Tests for User Story 3

- [x] T007 [US3] Escribir en `cripta/tests/test_datos_nuevos_servicio.py` las pruebas de los escenarios US3.1 a US3.11 y sus casos borde: ruta y conteo en la fuente HTTP, incluido un reintento tras HTTP 429; lectura offline y archivo ausente; copia en disco, copia dañada y copia de otra versión; validación de entradas (sin id, sin sala, tipos equivocados, sala inexistente, campos adicionales); llaves repetidas y orden conservado entre servicio, disco y offline; momento del inicio (después del esqueleto, antes de contenido y fichas); falla de la consulta y presupuesto agotado; carga de partida guardada sin consulta; reproducción de una partida nueva y de una que empezó cargando; y la línea del reporte final (FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-025)

### Implementation for User Story 3

- [x] T008 [P] [US3] Implementar `ubicacion_de_llaves` en `cripta/adapters/fuente_http.py` con la ruta `/criptas/<id>/llaves` (FR-011, FR-013)
- [x] T009 [P] [US3] En `cripta/adapters/fuente_offline.py`: la ruta `<carpeta>/criptas/<id>/llaves.json`, `ubicacion_de_llaves` con `UbicacionDeLlavesNoDisponible` cuando falta el archivo, `forma_de_obtencion` «leída del paquete offline» y `guardar_ubicacion_de_llaves` en el guardador (FR-015, FR-016, FR-025)
- [x] T010 [P] [US3] Agregar `leer_ubicacion_de_llaves` y `guardar_ubicacion_de_llaves` a `cripta/adapters/almacen_cripta.py`, con el archivo `<id_cripta>/llaves.json`; un archivo que falta o no se puede leer se lee como ausente (FR-014, FR-021, FR-022)
- [x] T011 [US3] Agregar `crear_ubicaciones_de_llaves` a `cripta/repository/traductor.py`: valida la respuesta, comprueba cada sala contra el esqueleto, conserva el orden y las repeticiones, ignora campos adicionales y no consulta el catálogo (FR-012, FR-017, FR-018, FR-019, FR-024)
- [x] T012 [US3] En `cripta/repository/repositorio_cripta.py`: obtener la ubicación de llaves en `iniciar_partida` después del esqueleto y antes del contenido, con el argumento `obtener_ubicacion_de_llaves`; leer la copia vigente (y descartarla si no es válida) o pedirla a la fuente y guardarla; tratar `UbicacionDeLlavesNoDisponible` como no disponible con aviso; exponer `ubicacion_de_llaves()`; y agregar la línea del origen al reporte final (FR-011, FR-014, FR-016, FR-020, FR-021, FR-025)
- [x] T013 [US3] En `cripta/controller/application.py`: la carga de una partida guardada llama a `iniciar_partida` sin obtener la ubicación de llaves, y la reproducción la obtiene solo si su log no empezó cargando una partida guardada (FR-011)
- [x] T014 [P] [US3] En `cripta/tools/descargar_datos_offline.py`: descargar también la ubicación de llaves de cada cripta, con su prueba en `cripta/tests/test_descargar_datos_offline.py` (FR-015)

**Checkpoint**: las pruebas de US2 y US3 pasan; la verificación de resolubilidad ya tiene sus datos.

---

## Phase 5: User Story 4 - Lo guardado por la primera parte no se mezcla con las criptas nuevas (Priority: P3)

**Goal**: Las copias de otra versión no se usan, y el aviso de cambio de contrato sigue funcionando.

**Independent Test**: Dejar en disco una copia de otra versión y cargar datos con un campo inventado.

- [x] T015 [US4] Escribir en `cripta/tests/test_datos_nuevos_servicio.py` las pruebas de los escenarios US4.1 a US4.3: una copia de otra versión (esqueleto, contenido y ubicación de llaves) no se usa y se reemplaza por la vigente; `costo` y `rango` no producen aviso de campo desconocido, y un campo inventado en una salida o en una ficha sí, una sola vez (FR-022, FR-023, FR-024)

**Checkpoint**: todas las historias pasan sus pruebas.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T016 Ajustar en `cripta/tests/test_repositorio_cripta.py` (y donde aparezcan) las aserciones que cuentan las solicitudes exactas de un inicio de partida o las líneas del reporte final, sumando la consulta de llaves y su línea (FR-013, FR-025, SC-005)
- [x] T017 Correr la suite completa desde `cripta/` y los pasos de `quickstart.md`, incluida una partida offline con las criptas de la segunda parte (SC-001, SC-002, SC-003, SC-004, SC-005). Hecho en `main` (dd75587): paso 1, las 37 pruebas de aceptación; paso 2, la suite completa con 1341 pruebas, todas pasan y una cuenta como fallo esperado (la de la línea de tiempo que describe el README), en Windows y en Linux; paso 3, el paquete `datos_offline_p2/` descargado del servicio, con el `llaves.json` de las cinco criptas (commit aa5187f); paso 4, una partida offline en `cripta-06` que inicia, muestra los costos y termina con `Ubicación de llaves: leída del paquete offline`, y otra en `cripta-02` que entra a la sala 14, donde está el cazador `e-cripta-02-7`, sin ningún aviso por `costo` ni por `rango` (en `cripta-06` los cazadores están detrás de puertas con llave); paso 5, una partida en `cripta-01` con el paquete de la primera parte, que termina con `Ubicación de llaves: no disponible` y el aviso de datos.

---

## Dependencies & Execution Order

- **Phase 1** no depende de nada.
- **Phase 2** depende de la Phase 1. T004 depende de T003.
- **US2 (Phase 3)** no depende de la Phase 2: solo toca el traductor.
- **US3 (Phase 4)** depende de T002, T003 y T004. T008, T009 y T010 se pueden hacer en paralelo; T011 depende de T002; T012 depende de T008 a T011; T013 depende de T012.
- **US4 (Phase 5)** depende de US3.
- **Phase 6** depende de todas las historias.

### Parallel Opportunities

```text
Phase 4:  T008 (fuente_http.py)  |  T009 (fuente_offline.py)  |  T010 (almacen_cripta.py)  |  T014 (descargar_datos_offline.py)
```

## Implementation Strategy

1. Phases 1 y 2, y el costo en null (US2), que es un cambio de una línea con su prueba.
2. US3: ubicación de llaves, con la que arranca la verificación de resolubilidad (especificación 006).
3. US4 y Phase 6: invalidación por versión, avisos, conteos de solicitudes y validación con datos reales.
