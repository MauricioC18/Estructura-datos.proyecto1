# Data Model: Verificación de resolubilidad

Todas las clases nuevas viven en `cripta/model/resolubilidad.py`, salvo `CriptaNoResoluble`, que vive en el repositorio junto a `VersionesIncompatibles`.

## Entradas (ya existen)

| Entrada | De dónde sale | Uso |
| --- | --- | --- |
| `RoomMap` | `Traductor.crear_mapa(salas)` | Salas, salidas en orden N, S, E, O, y puertas con `closed` y `key_id`. |
| `sala_inicial`, `sala_salida`, `llave_salida` | `DatosDePartida` | Dónde empieza el recorrido y qué define «resoluble» (FR-005). |
| `list[KeyLocation]` | Especificación 004 | Dónde se obtiene cada llave (FR-003). |

## LlaveEnElOrden

| Campo | Tipo | Regla | Requisito |
| --- | --- | --- | --- |
| `ronda` | entero ≥ 0 | La ronda en que la llave se alcanza por primera vez. | FR-006 |
| `ubicacion` | `KeyLocation` | La de menor sala entre las ubicaciones alcanzadas en esa ronda. | FR-006, FR-003 |
| `llave` | propiedad | `ubicacion.key_id`. | FR-006 |

## PuertaDeFrontera

| Campo | Tipo | Regla | Requisito |
| --- | --- | --- | --- |
| `sala_origen` | entero | Una sala de la región alcanzable. | FR-010 |
| `direccion` | `"N"`, `"S"`, `"E"` u `"O"` | La salida de esa sala. | FR-010 |
| `sala_destino` | entero | Una sala fuera de la región alcanzable. | FR-010 |
| `llave` | texto o `None` | La llave que pide; `None` si la puerta está cerrada sin llave. | FR-010 |

Orden: por sala de origen y, dentro de ella, por dirección N, S, E, O (FR-015).

## LlaveNoObtenible

| Campo | Tipo | Regla | Requisito |
| --- | --- | --- | --- |
| `llave` | texto | Una llave de la ubicación de llaves o que pide alguna puerta, que no se obtiene. | FR-009 |
| `motivo` | `"depende"`, `"sin_ubicacion"` o `"sin_acceso"` | Por qué no se obtiene. | FR-009, FR-013 |
| `depende_de` | texto o `None` | La llave que custodia su sala, cuando el motivo es «depende». | FR-009, FR-014 |

Orden: por id de llave (FR-015).

## ReporteDeResolubilidad

| Campo u operación | Tipo | Regla | Requisito |
| --- | --- | --- | --- |
| `se_pudo_verificar` | booleano | Falso solo si la ubicación de llaves no está disponible. | FR-020 |
| `es_resoluble` | booleano o `None` | `None` si no se pudo verificar. | FR-005 |
| `orden_de_llaves` | `list[LlaveEnElOrden]` | Todas las llaves obtenibles, por rondas y por id. | FR-006, FR-007 |
| `llaves_no_obtenibles` | `list[LlaveNoObtenible]` | Vacía si todas se obtienen. | FR-008, FR-009 |
| `puertas_de_la_frontera` | `list[PuertaDeFrontera]` | Solo si no es resoluble. | FR-010 |
| `ubicaciones_de_la_frontera` | lista de pares (llave, `list[KeyLocation]`) | Una entrada por llave que piden las puertas de la frontera; la lista vacía es «sin ubicación». | FR-011 |
| `ciclos` | lista de listas de ids | Cada ciclo empieza en su llave de menor id; la lista va ordenada. | FR-012, FR-025 |
| `falta_puerta_hacia_la_salida` | booleano | `llave_salida` se obtiene, pero ninguna puerta alcanzable que la pida lleva a `sala_salida`. | FR-005 |
| `lineas_de_texto()` | `list[str]` | El reporte listo para mostrar. | FR-021 |
| `codigo_de_salida()` | 0, 1 o 2 | Resoluble, no resoluble, sin verificar. | FR-018 |

## CriptaNoResoluble (repositorio)

Excepción con el atributo `reporte`. La lanza `iniciar_partida(..., exigir_resolubilidad=True)` cuando el código de salida es 1, antes de pedir contenido o fichas (FR-016).

## RepositorioCripta (cambios)

| Operación | Regla | Requisito |
| --- | --- | --- |
| `iniciar_partida(id, versiones_requeridas=None, obtener_ubicacion_de_llaves=True, exigir_resolubilidad=False)` | Verifica después de la ubicación de llaves; si se exige y no es resoluble, lanza `CriptaNoResoluble`. | FR-001, FR-016, FR-019, FR-022 |
| `verificar_cripta(id)` | Llega hasta la verificación y devuelve el reporte, sin pedir contenido ni fichas. | FR-001, FR-018 |
| `reporte_de_resolubilidad()` | El reporte del último inicio, o `None` si no se verificó (partida cargada). | FR-017, FR-019 |
