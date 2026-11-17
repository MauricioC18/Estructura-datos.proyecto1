# Guía de validación: Niebla de guerra y viaje automático «ir a»

**Plan**: [plan.md](./plan.md)

Cómo comprobar de punta a punta que la capacidad funciona, una vez implementada. No contiene código de implementación.

## Requisitos previos

- Python 3.11 o superior con `requests` instalado (`pip install -r requirements.txt`).
- Estar en la carpeta `cripta/`.

## 1. Pruebas automatizadas

```text
python -m unittest discover -s tests -t .
```

Resultado esperado: todas pasan, incluidas las nuevas de `tests/test_mapa_conocido.py`, `tests/test_niebla.py` y `tests/test_ir_a.py`. Cada caso del Apéndice B tiene una prueba que cita su requisito (SC-001):

| Caso del Apéndice B | Requisito citado |
| --- | --- |
| `ir a` hacia una sala no explorada | FR-022 |
| Puerta recordada abierta que está cerrada | FR-006, FR-026, FR-028 |
| `ir a` entra a una sala con enemigos dormidos | FR-028 |
| Antorcha: explora vecinas sin activar nada | FR-009, FR-010 |
| Pergamino revierte una entrada con antorcha | FR-015 |
| Pergamino después de un viaje | FR-032 |

## 2. Partida a mano, sin red

```text
python main.py --offline --semilla 1 --nombre prueba
```

1. Al empezar, la vista muestra la sala inicial; las salidas hacia salas no exploradas dicen «hay algo en esa dirección», sin id.
2. Escribir `mapa`: aparece solo la sala inicial. El reloj no cambia.
3. Moverse a una sala vecina y volver a escribir `mapa`: aparecen las dos salas.
4. Escribir `ir a <id de la sala inicial>`: el jugador vuelve por la ruta más barata y se informa «Llegaste a la sala …».
5. Escribir `ir a 999999`: se rechaza con el mismo mensaje que una sala no explorada y el reloj no cambia.
6. Salir y abrir la bitácora de `partidas/`: el viaje aparece como `# ir a …` seguido de líneas `mover …`.

## 3. Reproducción

```text
python main.py --offline --replay partidas/<archivo>.log
```

Resultado esperado: la reproducción termina con el mismo reloj y las mismas acciones que la partida original, sin instanciar la vista (SC-003).

## 4. Guardar y cargar

Dentro de una partida: explorar varias salas, `guardar prueba.bin` y `salir`. Luego:

```text
python main.py --offline --cargar prueba.bin
```

Resultado esperado: `mapa` muestra exactamente las mismas salas y los mismos estados de puerta que antes de guardar (SC-005).

## 5. Mediciones

```text
python main.py --bench
```

Resultado esperado: aparece la suite del mapa conocido con las cinco mediciones del plan, cada una con su alternativa descartada, y el tiempo de un paso de «ir a» con el mapa conocido completo (SC-006, SC-007).

## Limitaciones de esta guía

- El paquete sin conexión trae solo `cripta-01`, de 6 salas y sin antorchas en un lugar conveniente ni cazadores. Los casos de la antorcha, el cazador y la puerta con cierre automático se validan con las pruebas automatizadas, que arman criptas pequeñas a medida.
