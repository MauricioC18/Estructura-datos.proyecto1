# Presupuesto de solicitudes contra el API real — 14 de octubre de 2026

> Nota: estas mediciones se tomaron antes de integrar el bloque 2 en la estructura de carpetas
> del repositorio. Los comandos `herramientas.*` y `bench.*` ahora son `tools.*` y `benchmark.*`,
> y se ejecutan desde la carpeta `cripta/`. El código medido no cambió.

Equipo: computadora de Mauricio (Windows), conectada al API real
(`https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1`).
Captura original: `presupuesto_api_real_2026-10-14.png`.

Comandos, desde la raíz del proyecto:

```
python -m herramientas.simular_partida_bloque2 --borrar-cache   # arranque en frío
python -m herramientas.simular_partida_bloque2                  # arranque en caliente
```

Cripta: `cripta-01` (versión `fd58f7743b9e`, catálogo `be68d322d2f5`), presupuesto 9.
Recorrido (20 pasos al azar con semilla 2026, igual en ambas corridas):
1 → 2 → 1 → 2 → 3 → 2 → 5 → 2 → 5 → 2 → 3 → 4 → 3 → 4 → 6 → 4 → 6 → 4 → 6 → 4 → 3

| | Arranque en frío | Arranque en caliente |
|---|---|---|
| Solicitudes realizadas | **7 de 9** | **3 de 9** |
| Aciertos de caché | 49 (49 en memoria, 0 desde disco) | 49 (38 en memoria, 11 desde disco) |
| Fallos de caché | 2 | 0 |
| Fichas descargadas | 11 (2 lotes) | 0 |
| Salas descargadas | 6 (1 lote) | 0 (6 recuperadas de disco) |
| Esperas en la puerta | 0 | 0 |

Lectura:
- El arranque en frío usa exactamente las 7 solicitudes previstas en el análisis del presupuesto:
  lista, datos generales, versión del catálogo, 1 página de esqueleto, 1 lote de contenido con las
  6 salas y 2 lotes de catálogo con las 11 fichas.
- Con la caché en disco vigente, la misma partida usa 3 solicitudes (lista, datos generales y
  versión del catálogo): lo demás sale del disco, validado por versión (§4.4, §5.1).
- Las 11 recuperaciones desde disco son la primera vez que se usa cada ficha; después quedan en
  memoria.
- Los resultados en frío son idénticos a los de la misma simulación con `--offline datos_offline`,
  lo que confirma que ambas fuentes cumplen el mismo contrato (§3.4).
- No hubo respuestas HTTP 429 y el jugador nunca esperó en una puerta.

## Segunda medición: con el Traductor (14 de octubre de 2026, 18:45)

Misma computadora, mismo API y misma cripta, después de integrar el `Traductor`
(`repository/traductor.py`). Ahora la simulación crea los objetos del modelo (jugador, mapa,
enemigos, objetos y trampas) y llena cada sala antes de entrar, como lo hará el controlador.
Captura: `presupuesto_api_real_traductor_2026-10-14.png`.

Comandos, desde la carpeta `cripta/` (se borró la caché antes de la primera corrida):

```
python -m tools.simular_partida_bloque2 --borrar-cache   # arranque en frío
python -m tools.simular_partida_bloque2                  # arranque en caliente
```

Recorrido de la corrida en caliente (el mismo que en la primera medición):
1 → 2 → 1 → 2 → 3 → 2 → 5 → 2 → 5 → 2 → 3 → 4 → 3 → 4 → 6 → 4 → 6 → 4 → 6 → 4 → 3

Modelo creado por el Traductor: salas 6 (con contenido 6), enemigos 3, objetos en el suelo 8,
objetos que sueltan los enemigos 2, trampas 1.

| | Arranque en frío | Arranque en caliente |
|---|---|---|
| Solicitudes realizadas | **7 de 9** | **3 de 9** |
| Aciertos de caché | 16 (16 en memoria, 0 desde disco) | 16 (5 en memoria, 11 desde disco) |
| Fallos de caché | 2 | 0 |
| Fichas descargadas | 11 (2 lotes) | 0 |
| Salas descargadas | 6 (1 lote) | 0 (6 recuperadas de disco) |
| Esperas en la puerta | 0 | 0 |

Lectura:
- El presupuesto no cambió con el Traductor: 7 solicitudes en frío y 3 en caliente.
- Los aciertos bajan de 49 a 16 porque cambió lo que hace la simulación, no la caché. Antes
  pedía las fichas de una sala cada vez que entraba a ella; ahora cada sala se traduce una sola
  vez y las visitas siguientes no vuelven a leer fichas. Los fallos (2) y las descargas (11 fichas
  en 2 lotes) son los mismos.
- Salvo el conteo de solicitudes (el modo offline no usa la red), los números de ambas corridas
  son idénticos a los de la misma simulación con `--offline datos_offline`.
- Siguió sin haber esperas en la puerta: las fichas de lo que sueltan los enemigos se
  descargan con la precarga, antes del primer movimiento.
