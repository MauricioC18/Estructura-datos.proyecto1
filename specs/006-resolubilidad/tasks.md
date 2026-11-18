---
description: "Lista de tareas de la especificación 006: verificación de resolubilidad"
---

# Tasks: Verificación de resolubilidad

**Input**: Design documents from `/specs/006-resolubilidad/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/interfaz-resolubilidad.md

**Tests**: La constitución exige al menos una prueba automatizada por escenario de aceptación, y que la prueba cite el identificador del requisito. Aquí lo cita en su nombre (`test_fr012_...`) y en el nombre de su clase, que dice que es de la especificación 006. Las cuatro pruebas del Apéndice B lo dicen además en su nombre (`apendice_b`).

**Organization**: Tareas agrupadas por historia de usuario. Cada tarea cita entre paréntesis los requisitos que atiende.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: la historia de usuario a la que pertenece (US1, US2, US3, US4)
- Las rutas son relativas a la raíz del repositorio

---

## Phase 1: Setup

- [x] T001 Integrar `main` en la rama y correr `python -m unittest discover -s tests -t .` desde `cripta/` para confirmar el punto de partida (SC-005)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T002 Crear en `cripta/model/resolubilidad.py` las clases de datos del reporte (`LlaveEnElOrden`, `PuertaDeFrontera`, `LlaveNoObtenible`, `ReporteDeResolubilidad` con `lineas_de_texto()` y `codigo_de_salida()`) y `reporte_sin_verificar` (FR-018, FR-020, FR-021)

**Checkpoint**: el reporte existe y se puede armar a mano.

---

## Phase 3: User Story 1 - Saber antes de jugar si la cripta se puede ganar (Priority: P1) 🎯 MVP

**Goal**: Decidir si la cripta es resoluble y dar el orden de llaves.

**Independent Test**: Verificar criptas pequeñas armadas a mano y comparar decisión y orden.

- [x] T003 [US1] Escribir en `cripta/tests/test_resolubilidad.py` las pruebas de los escenarios US1.1 a US1.8: resoluble simple, llave necesaria antes en el orden, llave de un errante ubicada en su sala inicial (Apéndice B), dos ejecuciones con el mismo orden (Apéndice B), el mismo resultado con salas y entradas en otro orden, salida de un solo sentido, falta de una puerta que pida `llave_salida`, y aviso de llaves inalcanzables en una cripta resoluble (FR-003, FR-004, FR-005, FR-006, FR-007, FR-008)
- [x] T004 [US1] Implementar en `cripta/model/resolubilidad.py` el recorrido por rondas con listas de espera por llave, la decisión de FR-005 y el orden por rondas y por id con su ubicación (FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-023)

**Checkpoint**: las pruebas de US1 pasan.

---

## Phase 4: User Story 2 - Entender por qué una cripta no se puede ganar (Priority: P1)

**Goal**: Reporte completo del bloqueo.

**Independent Test**: Verificar criptas no resolubles armadas a mano y comparar cada parte del reporte.

- [x] T005 [US2] Escribir en `cripta/tests/test_resolubilidad.py` las pruebas de los escenarios US2.1 a US2.7: `llave_salida` detrás de la única puerta que ella abre (Apéndice B), ciclo de dos llaves, llave sin ubicación, puertas de la frontera con y sin llave, ubicación con enemigo, dependencia de cada llave no obtenible, dependencia de una llave sin ubicación que no es ciclo, desempate por id, zona sin acceso y orden determinista de las listas (FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015)
- [x] T006 [US2] Implementar en `cripta/model/resolubilidad.py` la frontera, la continuación más allá de la frontera con el montículo propio de llaves pendientes, las dependencias y la detección de ciclos (FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-024, FR-025)

**Checkpoint**: las pruebas de US1 y US2 pasan.

---

## Phase 5: User Story 3 - No empezar una partida que no se puede ganar (Priority: P1)

**Goal**: El inicio respeta la verificación y `--verificar` tiene de dónde leer.

**Independent Test**: Iniciar con una fuente simulada una cripta no resoluble, con y sin exigir la resolubilidad.

- [x] T007 [US3] Escribir en `cripta/tests/test_resolubilidad.py` las pruebas de los escenarios US3.1 a US3.7 en el repositorio: sin `--forzar` no inicia y trae el reporte (Apéndice B), con `--forzar` inicia, una cripta resoluble inicia con su orden, `verificar_cripta` no pide contenido ni fichas y da su código, sin ubicación de llaves se informa y la partida inicia, al cargar no se verifica, no se agregan solicitudes, y la reproducción nunca exige la resolubilidad (FR-001, FR-016, FR-017, FR-018, FR-019, FR-020, FR-022)
- [x] T008 [US3] En `cripta/repository/repositorio_cripta.py`: verificar después de la ubicación de llaves y antes del contenido, con un mapa armado por un traductor aparte; agregar `exigir_resolubilidad`, `CriptaNoResoluble`, `verificar_cripta` y `reporte_de_resolubilidad` (FR-001, FR-016, FR-017, FR-018, FR-019, FR-020, FR-022)
- [x] T009 [P] [US3] Publicar el contrato para la especificación 005 en `cripta/docs/INTERFAZ_RESOLUBILIDAD.md`, igual a `specs/006-resolubilidad/contracts/interfaz-resolubilidad.md` (FR-016, FR-017, FR-018, FR-021)

**Dependencia externa**: conectar `--verificar` y `--forzar` en `cripta/main.py` y `cripta/controller/application.py`, y mostrar el reporte al iniciar, lo hace la especificación 005 con ese contrato (FR-016, FR-017, FR-018).

**Checkpoint**: las pruebas de US1, US2 y US3 pasan.

---

## Phase 6: User Story 4 - Una verificación rápida y medida (Priority: P2)

**Goal**: Demostrar con mediciones el costo lineal y el límite de 200 ms.

**Independent Test**: Ejecutar `python -m benchmark.bench_resolubilidad`.

- [x] T010 [US4] Escribir en `cripta/tests/test_resolubilidad.py` las pruebas de los escenarios US4.1 a US4.4: el conteo de salas y salidas examinadas crece en proporción al tamaño y el de la ingenua mucho más rápido, una cripta sintética de 300 salas se verifica en menos de 200 ms, las dos variantes dan el mismo reporte también en criptas no resolubles, y la misma semilla genera la misma cripta (FR-023, FR-024, FR-025, FR-026, FR-027, FR-028)
- [x] T011 [US4] Crear `cripta/benchmark/bench_resolubilidad.py` con la variante ingenua, el generador de criptas encadenadas con semilla, el conteo de operaciones y la medición de la cripta más grande de `datos_offline_p2`, y sumarlo a `cripta/benchmark/benchmark.py` (FR-026, FR-027, FR-028)
- [x] T012 [US4] Escribir la sección 5.4 de `cripta/docs/DECISIONES.md` con el problema, las alternativas, la decisión y si coincide con este plan, la complejidad, las mediciones de `--bench` y los límites conocidos (FR-023, FR-026, FR-027)

**Checkpoint**: todas las historias pasan sus pruebas y la medición está documentada.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T013 Correr la suite completa y `python -m benchmark.bench_resolubilidad` desde `cripta/` (SC-001, SC-002, SC-003, SC-004)
- [x] T014 Medir la cripta publicada más grande con su ubicación de llaves real, una vez que `datos_offline_p2` la traiga, y anotar el resultado en la sección 5.4 de DECISIONES (FR-026, SC-002)

---

## Dependencies & Execution Order

- **Phase 1** no depende de nada. **Phase 2** depende de la 1.
- **US1** depende de T002. **US2** depende de US1 (usa el resultado de las rondas). **US3** depende de US1 y US2. **US4** depende de US1 y US2.
- T009 se puede hacer en cualquier momento después del plan.
- T014 depende de que el paquete `datos_offline_p2` traiga `llaves.json`.

### Parallel Opportunities

```text
T009 (INTERFAZ_RESOLUBILIDAD.md)  |  T011 (bench_resolubilidad.py)
```

## Implementation Strategy

1. Phases 1 y 2, y US1: con eso ya se sabe si una cripta se puede ganar.
2. US2: el reporte completo, con lo que se cubren los cuatro casos del Apéndice B junto con US3.
3. US3 y el contrato: la especificación 005 puede conectar las banderas.
4. US4 y Phase 7: mediciones y DECISIONES.
