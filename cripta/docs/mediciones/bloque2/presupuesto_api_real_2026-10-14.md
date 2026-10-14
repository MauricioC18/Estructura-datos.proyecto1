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
