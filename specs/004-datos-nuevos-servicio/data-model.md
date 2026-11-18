# Data Model: Datos nuevos del servicio

Solo se describen los cambios respecto de la primera parte.

## Door, Exit y Enemy (modelo, ya en `main`)

Las especificaciones 001 y 002 ya agregaron lo que esta especificación necesita de estas clases:

| Clase | Campo | Regla | Requisito de esta especificación |
| --- | --- | --- | --- |
| `Door` | `cost` | Entero ≥ 1, igual en ambos sentidos; 100 (`DEFAULT_EXIT_COST`) cuando ningún lado lo declara o lo declara en null. | FR-001 a FR-005 |
| `Exit` | `cost` | Propiedad de solo lectura que devuelve `door.cost`. | FR-001, FR-005 |
| `Enemy` | `HUNTER` | Cuarto comportamiento, `"cazador"`. | FR-006 |
| `Enemy` | `pursuit_range` | Rango del cazador, entero ≥ 1; 0 en los demás enemigos. | FR-007, FR-009 |

## KeyLocation (modelo nuevo, `model/key_location.py`)

| Campo | Tipo | Regla | Requisito |
| --- | --- | --- | --- |
| `key_id` | texto no vacío | El id de la llave, tal como lo entrega el servicio; no se comprueba contra el catálogo. | FR-011, FR-017 |
| `room_id` | entero | Una sala que existe en el esqueleto. Si la llave la suelta un enemigo, es la sala donde ese enemigo inicia. | FR-012, FR-017 |
| `enemy_id` | texto o `None` | La instancia de enemigo que suelta la llave, o `None` si la llave está en el suelo. | FR-012 |
| `is_dropped_by_enemy` | propiedad | Verdadero cuando `enemy_id` no es `None`. | FR-012 |

## Ubicación de llaves de la partida (repositorio)

| Estado | Representación | Origen informado en el reporte final |
| --- | --- | --- |
| Obtenida | `list` de `KeyLocation` en el orden recibido; puede estar vacía | «descargada del servicio», «recuperada de disco» o «leída del paquete offline» |
| No disponible | `None` | «no disponible», más un aviso de datos |

Reglas de validación (FR-017, FR-024):

- La respuesta es un objeto con la lista `llaves`.
- Cada entrada es un objeto con `id` (texto no vacío) y `sala` (entero que existe en el esqueleto). Si trae `enemigo`, es texto o `null`.
- Los campos adicionales de una entrada se ignoran sin aviso.
- Cualquier incumplimiento lanza `ErrorDatosCripta` y la partida no inicia.

Ciclo de vida (FR-014, FR-021, FR-022):

1. Al iniciar una partida nueva, una reproducción o `--verificar`, después del esqueleto: si hay copia vigente en disco, se lee de ahí; si no, se pide a la fuente y se guarda en disco.
2. Si cambia la versión de la cripta, el almacén borra la copia completa de esa cripta, incluida la ubicación de llaves.
3. Una copia dañada se trata como ausente y se vuelve a pedir.
4. Al cargar una partida guardada no se obtiene, y tampoco al reproducir una partida que empezó así (FR-011).

## ReporteDeRed (repositorio)

| Campo | Tipo | Regla | Requisito |
| --- | --- | --- | --- |
| `origen_de_la_ubicacion_de_llaves` | texto | Una de las cuatro descripciones de la tabla anterior, o «no se obtuvo en esta partida» si la partida empezó cargando una partida guardada; se muestra como `Ubicación de llaves: <origen>`. | FR-025 |
