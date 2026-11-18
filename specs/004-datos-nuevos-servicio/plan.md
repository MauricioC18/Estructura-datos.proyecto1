# Implementation Plan: Datos nuevos del servicio

**Branch**: `Parte_2-API-cache-persistencia` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-datos-nuevos-servicio/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

El programa debe leer los tres datos nuevos del contrato 1.1.0 del servicio: el costo de cada salida, el comportamiento cazador con su rango, y la ubicación de llaves. Los dos primeros ya están en `main`: los implementaron las especificaciones 001 y 002, con el costo en la puerta compartida por las dos salas y el rango en `Enemy.pursuit_range`. Este plan cubre lo que falta: el costo en null, que el contrato permite y hoy se rechaza, y la ubicación de llaves. La ubicación de llaves se agrega como una operación más del contrato de fuentes de datos (HTTP y offline), se guarda en la copia en disco de la cripta junto al esqueleto y se valida en el traductor, de modo que dé lo mismo de dónde venga. Se obtiene dentro del inicio de la partida, justo después del esqueleto y antes de cualquier contenido.

## Technical Context

**Language/Version**: Python 3.11 o superior (las pruebas corren también en 3.13).

**Primary Dependencies**: `requests` (ya usado por la fuente HTTP), `json` de la biblioteca estándar. Ninguna dependencia nueva.

**Storage**: Archivos JSON. La copia en disco de cada cripta vive en `cache_cripta/<id_cripta>/` y se invalida por versión. El paquete offline vive en `datos_offline/` o en la carpeta que se pase a `--offline`.

**Testing**: `unittest`, desde `cripta/` con `python -m unittest discover -s tests -t .`.

**Target Platform**: Consola en Windows y Linux.

**Project Type**: Juego de consola (CLI) con arquitectura MVC.

**Performance Goals**: Ninguna operación evaluada nueva. Traducir el costo agrega trabajo constante por salida, así que `crear_mapa` sigue en O(S + E). Traducir la ubicación de llaves es O(L) para L entradas, con una búsqueda de sala O(1) promedio por entrada.

**Constraints**: Constitución del grupo: nada de `dict` o `set` como índice, ningún dato de una cripta concreta en el código, y toda solicitud cuenta en `presupuesto_solicitudes`. La consulta de llaves es exactamente una solicitud por inicio sin copia vigente.

**Scale/Scope**: La cripta más grande publicada (`cripta-06`) tiene 300 salas, 760 salidas y 4 llaves distintas. Las fichas de enemigo con rango son pocas (2 de 16 fichas del catálogo actual).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
| --- | --- | --- |
| I. Estructuras a mano | Se reutiliza la `TablaHash` propia que ya empareja las salidas en el traductor. La ubicación de llaves se guarda en una `list` en el orden recibido, que la constitución permite como almacenamiento contiguo. No se usa `dict` ni `set` como índice. Los diccionarios de `respuesta.json()` solo se leen. | Cumple |
| II. Determinismo | No hay azar. La ubicación de llaves conserva el orden en que llega, y el combinado de costos usa una regla fija (sala de menor id). | Cumple |
| III. MVC | El modelo recibe objetos (`KeyLocation`; `Door.cost` y `Enemy.pursuit_range` ya existen) y no sabe de HTTP ni de archivos. La red y el disco siguen detrás de las fuentes y del almacén. No se toca la vista. | Cumple |
| IV. Sin datos de una cripta | El 100 por defecto es una regla del enunciado (§3.1), no un dato de cripta. No se escribe ningún rango, id ni sala. | Cumple |
| V. Presupuesto | La consulta pasa por `_consumir_solicitud`, igual que las demás, incluidos los reintentos por HTTP 429. La copia en disco y el modo offline no gastan solicitudes. | Cumple |
| VI. Mediciones | El plan no afirma ninguna mejora de rendimiento. Lo único medible es el número de solicitudes, que se comprueba en las pruebas y en la línea nueva del reporte final. | Cumple |
| VII. Spec antes que código | La especificación se confirmó en el commit `b34c03a` antes de cualquier cambio de código. Este plan y las tareas van en un commit de documentación, también antes del código. | Cumple |

Revisión después del diseño (Phase 1): sin cambios. Ninguna decisión de `research.md` agrega dependencias prohibidas.

## Project Structure

### Documentation (this feature)

```text
specs/004-datos-nuevos-servicio/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ubicacion-de-llaves.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
cripta/
├── model/
│   └── key_location.py          nuevo: KeyLocation
├── repository/
│   ├── traductor.py             costo en null y ubicación de llaves
│   └── repositorio_cripta.py    obtiene la ubicación de llaves al iniciar; línea nueva del reporte final
├── adapters/
│   ├── fuente_datos.py          operación ubicacion_de_llaves y UbicacionDeLlavesNoDisponible
│   ├── fuente_http.py           GET /criptas/<id>/llaves
│   ├── fuente_offline.py        <carpeta>/criptas/<id>/llaves.json
│   └── almacen_cripta.py        copia en disco <id_cripta>/llaves.json
├── controller/
│   └── application.py           al cargar una partida guardada, y al reproducir una que empezó así, no se pide la ubicación de llaves
├── tools/
│   └── descargar_datos_offline.py   descarga también la ubicación de llaves
├── benchmark/                   los dobles de fuente de datos implementan la operación nueva
└── tests/
    ├── test_datos_nuevos_servicio.py   nuevo: una prueba por escenario, cada una cita su FR
    └── (dobles de fuente y conteos de solicitudes de las pruebas existentes)
```

**Structure Decision**: Se mantiene la estructura de la primera parte. Cada dato nuevo entra por la misma capa que sus vecinos: lo que es campo del API, por el traductor; lo que es consulta HTTP, por las fuentes; lo que se guarda en disco, por el almacén de la cripta. Las pruebas de aceptación de esta especificación van juntas en un archivo nuevo para que la trazabilidad FR → prueba se lea en un solo lugar.

## Mediciones planificadas

Esta especificación no resuelve ninguno de los problemas evaluados de §5, así que no agrega mediciones a `--bench`. Lo que sí se verifica con números:

- Solicitudes de un inicio de partida, con y sin copia en disco y en modo offline (SC-002), en las pruebas y en el reporte final (FR-025).
- Los dobles de fuente de datos de los benchmarks de la primera parte implementan la operación nueva sin consumir solicitudes, para que esas mediciones no cambien.

## Dependencias y coordinación

- **Especificaciones 001 y 002**: ya implementaron el costo, el cazador y el rango (`Enemy.HUNTER`, `Enemy.pursuit_range`). Este plan solo toca `_costo_de_salida` del traductor para aceptar el null.
- **Guardado binario**: ya guarda el costo de las puertas y el rango de los enemigos (formato versión 3, en `main`).
- **Especificación 005 (niebla e «ir a»)**: su rama cambia `controller/application.py` y `main.py`. Este plan cambia en `application.py` solo dos llamadas a `iniciar_partida` (la carga y la reproducción). Al juntar ramas, el conflicto posible se resuelve conservando los dos cambios.
- **Especificación 006 (resolubilidad)**: es la que usa la ubicación de llaves, mediante `RepositorioCripta.ubicacion_de_llaves()`.

## Complexity Tracking

Sin violaciones de la constitución que justificar.
