# Modelo de datos: Niebla de guerra y viaje automático «ir a»

**Plan**: [plan.md](./plan.md) | **Especificación**: [spec.md](./spec.md)

## Mapa conocido

Lo que el jugador sabe del mapa. Es estado del juego.

| Campo | Estructura | Contenido | Por qué |
| --- | --- | --- | --- |
| exploradas | `TablaHash` id de sala → `True` | Una entrada por sala explorada | «¿está explorada?» en O(1) promedio (FR-033) |
| orden de exploración | `list` usada como pila | Ids de sala en el orden en que se exploraron | Exportar en un orden determinista y revertir sacando el último elemento |
| contadores de avistamiento | `TablaHash` id de sala → entero > 0 | Cuántas salidas de salas exploradas llevan a esa sala | «¿está avistada?» en O(1) promedio; explorar cuesta lo revelado (FR-034) |
| puertas recordadas | `TablaHash` clave de puerta (`int`) → `bool` (abierta) | Una entrada por puerta observada al menos una vez | Estado recordado en O(1) promedio; ausente significa desconocida (FR-008) |
| mapa de salas | referencia, no se copia | El mapa real | De ahí se leen nombre, salidas y costos de las salas exploradas, que no cambian |
| historial | referencia, duck typing | El historial reversible | Donde se anotan las inversas |

**Ninguna clave es una tupla**: todas son `int`, porque `TablaHash` solo admite `int` y `str`.

### Clave de una puerta

`clave = id de room_a × 4 + índice de la dirección en que la puerta sale de room_a`, con el índice según `DIRECTIONS = ("N", "S", "E", "O")` de `model/room.py`.

- Es única: dentro de una sala, cada dirección tiene a lo sumo una salida.
- Es la misma desde los dos lados: siempre se calcula desde `room_a`.
- Sobrevive a guardar y cargar: depende de ids y direcciones, no del objeto en memoria.

### Estado de una sala (derivado, no guardado)

```text
si está en exploradas        → explorada
si su contador es mayor que 0 → avistada
en otro caso                 → desconocida
```

### Estado recordado de una puerta (derivado de la tabla)

`abierta` · `cerrada` · `desconocida` (sin entrada)

## Transiciones

| Evento | Efecto | Anotación para el pergamino |
| --- | --- | --- |
| Inicio de partida | La sala inicial pasa a explorada y se observan sus puertas | Ninguna: no hay intervalo abierto (FR-002) |
| El jugador entra a la sala S | S pasa a explorada si no lo estaba; se observan todas las puertas de S | Una por sala nueva y una por cada puerta cuyo recuerdo cambió |
| Lo mismo con la antorcha encendida | Además, cada vecina de S por cualquier salida pasa a explorada; sus puertas **no** se observan | Una por vecina nueva |
| Una puerta cambia | Si el jugador está en una de sus dos salas, se actualiza el recuerdo | Una, si el recuerdo cambió |
| Encender la antorcha | Nada (FR-037) | Ninguna |
| Pergamino | Se aplican las inversas del intervalo | — |
| Cargar partida | Importar | Ninguna |

Una sala explorada **nunca** vuelve a desconocida ni a avistada salvo por una reversión.

## Viaje

No es estado del juego y no se guarda. Vive mientras dura una orden `ir a`.

| Campo | Contenido |
| --- | --- |
| destino | id de una sala explorada distinta de la actual |
| pasos | cuántos movimientos se ejecutaron |
| motivos de parada | lista ordenada como en FR-028 |
| enemigos al entrar | si la sala destino del paso en curso tenía enemigos vivos en el instante de entrar; se pregunta justo antes del movimiento |

## Motivo de parada

Un valor de esta lista, en este orden de presentación (FR-029): `llegada`, `enemigos`, `daño`, `sin_ruta`, `partida_terminada`, `contenido_no_disponible`.

## Exportación (para el archivo de partida y los puntos de control)

```text
exploradas: [id, id, ...]                    en orden de exploración
puertas:    [(clave, abierta), ...]          en orden creciente de clave
```

Los contadores de avistamiento no se exportan: se rehacen al importar.
