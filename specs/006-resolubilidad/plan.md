# Implementation Plan: Verificación de resolubilidad

**Branch**: `Parte_2-API-cache-persistencia` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-resolubilidad/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

La verificación es una función del modelo que recibe el mapa de salas (el mismo `RoomMap` que arma el traductor), las salas inicial y de salida, `llave_salida` y la ubicación de llaves de la especificación 004, y devuelve un reporte. Recorre la cripta **por rondas** desde `sala_inicial`: cada sala se visita una vez, y cada puerta cerrada que se encuentra se anota en la **lista de espera de su llave**. Al terminar una ronda, las llaves halladas se ordenan por id, se dan por obtenidas y liberan las salas de sus listas de espera, que forman la ronda siguiente. Así ninguna sala ni salida se vuelve a examinar por cada llave nueva (§5.4).

Si queda alguna llave sin obtener, el mismo recorrido **continúa más allá de la frontera** abriendo «en hipótesis» las puertas de una llave a la vez, en el orden que fijó la aclaración P2 (primero las llaves sin ubicación, después por id). Cada sala alcanzada así queda custodiada por la llave de la última puerta abierta en hipótesis para llegar a ella, y cada llave bloqueada **depende** de la llave que custodia su sala. Como cada llave depende de a lo sumo una, los ciclos se encuentran siguiendo esos punteros una sola vez.

El repositorio corre la verificación justo después de obtener la ubicación de llaves y antes de pedir contenido. Si se le pide exigir la resolubilidad, lanza `CriptaNoResoluble` con el reporte. `--verificar` usa un camino que se detiene ahí. La medición de §5.4 compara contra una variante ingenua que repite el recorrido completo en cada ronda, en criptas sintéticas con llaves encadenadas generadas con semilla.

## Technical Context

**Language/Version**: Python 3.11 o superior (las pruebas corren también en 3.13).

**Primary Dependencies**: Ninguna nueva. Se reutilizan `TablaHash` y `merge_sort` del proyecto.

**Storage**: No guarda nada propio. Lee el esqueleto y la ubicación de llaves que ya obtiene la especificación 004.

**Testing**: `unittest`, desde `cripta/` con `python -m unittest discover -s tests -t .`.

**Target Platform**: Consola en Windows y Linux.

**Project Type**: Juego de consola (CLI) con arquitectura MVC.

**Performance Goals**: Menos de 200 ms en la cripta publicada más grande (§6.1). Costo O(S + E + L + K log K) para S salas, E salidas, L entradas de ubicación y K llaves, más O(F log F) para ordenar las F puertas que se anotan en espera.

**Constraints**: Constitución: nada de `dict`, `set`, `heapq`, `bisect` ni `collections` como estructura de trabajo; ningún dato de una cripta concreta en el código; determinismo. La verificación no hace solicitudes ni cambia el estado de la partida.

**Scale/Scope**: La cripta de referencia (`cripta-06`) tiene 300 salas, 760 salidas y 4 llaves. Las criptas sintéticas de la medición llegan a 2001 salas y 400 llaves encadenadas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
| --- | --- | --- |
| I. Estructuras a mano | Rondas y llaves en `TablaHash` propia; listas como almacenamiento contiguo; el orden con `merge_sort` propio; la cola de prioridad de la explicación es un montículo binario propio, porque `heapq` está prohibido. | Cumple |
| II. Determinismo | El orden va por rondas y por id; las salidas se recorren en el orden fijo N, S, E, O; las puertas en espera se ordenan por sala y dirección antes de abrirse en hipótesis; el desempate de las explicaciones es fijo. Nada depende del orden en que llegan los datos. | Cumple |
| III. MVC | La verificación vive en el modelo y no sabe de HTTP, archivos ni vista. El repositorio la llama con objetos del modelo. Mostrar el reporte y conectar las banderas es de la vista y el controlador (especificación 005). | Cumple |
| IV. Sin datos de una cripta | Ningún id, sala ni llave escrito en el código. La medición de la cripta más grande la busca por tamaño dentro del paquete offline. | Cumple |
| V. Presupuesto | No hace solicitudes; usa lo que ya obtuvo la especificación 004. | Cumple |
| VI. Mediciones | Cada afirmación de costo se respalda con `--bench`: tiempo y conteo de salas y salidas examinadas, contra la alternativa ingenua, en varios tamaños. | Cumple |
| VII. Spec antes que código | La especificación, sus aclaraciones, este plan y las tareas se confirman en Git antes del código. | Cumple |

Revisión después del diseño (Phase 1): sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/006-resolubilidad/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── interfaz-resolubilidad.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
cripta/
├── model/
│   └── resolubilidad.py               nuevo: verificación por rondas, explicación del bloqueo, reporte
├── repository/
│   └── repositorio_cripta.py          verifica después de la ubicación de llaves; CriptaNoResoluble; verificar_cripta
├── benchmark/
│   ├── bench_resolubilidad.py         nuevo: variante ingenua, criptas sintéticas con semilla, mediciones
│   └── benchmark.py                   suma la suite a --bench
├── docs/
│   ├── INTERFAZ_RESOLUBILIDAD.md      nuevo: lo que la especificación 005 llama para --verificar y --forzar
│   └── DECISIONES.md                  sección 5.4
└── tests/
    └── test_resolubilidad.py          nuevo: una prueba por escenario, cada una cita su FR
```

**Structure Decision**: La verificación es una regla del juego sobre el mapa, así que va en el modelo, junto a las demás clases que no conocen la red. El repositorio ya es quien sabe en qué momento del inicio están listos el esqueleto y las llaves, así que es quien la llama. La variante ingenua solo existe para medir, por eso vive en `benchmark/`.

## Mediciones planificadas

- **Incremental contra ingenua** en criptas sintéticas con 25, 50, 100, 200 y 400 llaves encadenadas (5 salas por llave), generadas con semilla: mejor de 3 tiempos y conteo de salas y salidas examinadas. El conteo no depende de la máquina y muestra el crecimiento lineal contra el cuadrático.
- **Igualdad de resultados**: en cada tamaño, las dos variantes deben dar las mismas líneas de reporte.
- **Cripta publicada más grande**: la más grande del paquete `datos_offline_p2`, si existe y trae la ubicación de llaves; mejor de 5 tiempos contra el límite de 200 ms.

## Dependencias y coordinación

- **Especificación 004**: entrega el esqueleto y la ubicación de llaves (`RepositorioCripta.ubicacion_de_llaves()`), y el estado «no disponible» que aquí da el código de salida 2.
- **Especificación 005**: conecta `--verificar` y `--forzar`, muestra el reporte al iniciar y usa el código de salida, según `cripta/docs/INTERFAZ_RESOLUBILIDAD.md`. Los requisitos de esas banderas son FR-016 a FR-018 y FR-020 de esta especificación.
- **Paquete offline de la segunda parte** (`datos_offline_p2`): lo necesita la medición de la cripta más grande con su ubicación de llaves real.

## Complexity Tracking

Sin violaciones de la constitución que justificar.
