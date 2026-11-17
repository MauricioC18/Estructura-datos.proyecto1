# Contrato: comandos del jugador

**Plan**: [../plan.md](../plan.md)

La sintaxis exacta es decisión del grupo (P1 §10.2 permite variarla). Este contrato fija la que se va a implementar y probar.

## `mapa`

- Sin argumentos. Con un argumento se rechaza con «'mapa' no lleva argumentos.», como los demás comandos sin argumento.
- No consume tiempo, no se registra en la bitácora, no cambia nada (FR-019).
- Muestra, por cada sala explorada en orden creciente de id:

```text
Sala <id>: <nombre>
  N -> <id del destino> (costo <c>) abierta
  E -> hay algo en esa direccion (costo <c>) desconocida
  S -> <id del destino> (costo <c>) cerrada
```

- El destino se muestra con su id si está explorado y como «hay algo en esa dirección» si está avistado (FR-005, FR-018).
- El estado es el **recordado**: `abierta`, `cerrada` o `desconocida` (FR-007, FR-008).
- Las salas desconocidas no aparecen (Historia 7, escenario 5).

## `ir a <sala>`

- `<sala>` es un entero (supuesto del grupo). Si falta o no es entero, error de sintaxis, como los demás comandos.
- Se rechaza sin consumir tiempo ni registrar nada si la sala no está explorada, no existe o es la sala actual. Para «no explorada» y «no existe», **el mismo mensaje** (FR-022).
- Si se acepta:
  1. se escribe en la bitácora la línea `# ir a <sala>`;
  2. cada paso se registra como `mover <dirección>`, igual que uno escrito a mano;
  3. al detenerse se muestran todos los motivos que se cumplieron, en el orden de FR-028.

Motivos que se muestran:

| Motivo | Texto |
| --- | --- |
| llegada | Llegaste a la sala <id>. |
| enemigos | Hay enemigos en esta sala. |
| daño | Recibiste daño. |
| sin_ruta | No hay una ruta conocida hacia la sala <id>. |
| partida_terminada | La partida terminó. |
| contenido_no_disponible | <mensaje del error de carga> |

Los textos son de la interfaz y pueden ajustarse; las pruebas comprueban el motivo, no la redacción.

## Vista de la sala actual

- Cada salida muestra dirección, costo, estado recordado y destino con el mismo criterio que `mapa` (FR-020).
- En la lista de enemigos, los cazadores llevan una marca visible, por ejemplo `[cazador]` (FR-021).
