# Contrato: interfaz del mapa conocido con el resto del programa

**Plan**: [../plan.md](../plan.md)

Lo que el mapa conocido ofrece a los demás módulos y lo que espera de ellos. Los nombres de los métodos son provisionales hasta acordarlos con Carlos y Erick; lo que no cambia es **qué** se intercambia.

## Lo que recibe al construirse

| Parámetro | Qué es | Contrato que espera (duck typing) |
| --- | --- | --- |
| mapa de salas | el `RoomMap` de la partida | `room(id)`, `contains(id)`; cada sala con `exits()` y cada salida con `direction`, `destination`, `door`, `cost` |
| historial | el historial reversible, o nada | `record(change)`. Sin historial, los cambios no se anotan, igual que el rastro |

## Avisos que necesita del motor (Carlos)

| Aviso | Cuándo | Qué hace |
| --- | --- | --- |
| `jugador_entro(sala, antorcha_encendida)` | Al iniciar la partida con la sala inicial, y en cada movimiento del jugador justo después de cambiar su sala | Explora la sala, observa todas sus puertas y, con la antorcha, explora las vecinas |
| `puerta_cambio(puerta, sala_del_jugador)` | Cada vez que el motor cambia el estado de una puerta (abrir con llave, cierre automático) | Si el jugador está en una de las dos salas de la puerta, actualiza el recuerdo |

El motor recibe el mapa conocido como colaborador opcional. Sin él, usa un objeto nulo que ignora los avisos, igual que `_NoHistory`.

## Consultas que ofrece

| Consulta | Devuelve | Costo |
| --- | --- | --- |
| `estado_de_sala(id)` | `explorada`, `avistada` o `desconocida` | O(1) promedio |
| `puerta_recordada(puerta)` | `abierta`, `cerrada` o `desconocida` | O(1) promedio |
| `salas_exploradas()` | ids en orden de exploración | O(k) |
| `vecinas_conocidas(sala)` | `(id, costo, salida)` por cada salida de la sala hacia una sala explorada cuya puerta se recuerda abierta | O(4) |

`vecinas_conocidas` es el proveedor que recibe `RutasMasBaratas`. Tiene la misma forma que `Game._open_exits_of` (`model/game.py:708`), así que la búsqueda no distingue si le pasan el mapa real o el conocido.

## Exportar e importar (Carlos para el guardado, Erick para los puntos de control)

| Operación | Contrato |
| --- | --- |
| `exportar()` | `(exploradas, puertas)`: una lista de ids en orden de exploración y una lista de pares `(clave int, abierta bool)` en orden creciente de clave |
| `importar(exploradas, puertas)` | Deja el mapa conocido exactamente como estaba al exportar. No anota nada en el historial |

Es todo lo que el archivo de partida necesita guardar. El formato binario es de Carlos.

## Lo que la línea de tiempo puede usar (Erick)

- Si reconstruye **hacia atrás**: los cambios del conocimiento son anotaciones del historial reversible, por el mismo camino que todos los demás.
- Si reconstruye **hacia adelante**: la exportación es la copia del conocimiento para el punto de control; re-simular las acciones vuelve a producir los mismos cambios, porque son deterministas (FR-017).
- Para el resumen de `historia`: las mismas consultas de arriba, sobre el conocimiento reconstruido.
