# CRIPTA

Juego de mazmorra dirigido por eventos, desarrollado como primer proyecto del curso Estructuras de Datos II, II Ciclo 2026, Universidad Nacional de Costa Rica.

El proyecto consiste en diseñar, implementar y evaluar las estructuras de datos necesarias para resolver los problemas planteados en el enunciado: selección del siguiente evento, precarga de contenido, resolución del catálogo, caché persistente, inventario, historial reversible, rastro del jugador, bitácora en pantalla, ordenamiento y guardado binario.

El enunciado oficial está en `docs/proyecto_cripta.md` y es la referencia para cualquier duda sobre las reglas del juego.

## Estado actual

El proyecto está en desarrollo. Lo implementado y probado hasta ahora es:

| Módulo | Contenido |
| --- | --- |
| `model/event.py` | Representación de un evento programado |
| `structures/event_queue.py` | Agenda de eventos, montículo binario mínimo |
| `model/game_state.py` | Reloj virtual, numeración de eventos y azar reproducible |
| `adapters/fuente_datos.py`, `fuente_http.py`, `fuente_offline.py` | Contrato común de las fuentes de datos, cliente del API y modo sin conexión |
| `adapters/almacen_fichas.py`, `almacen_cripta.py` | Caché persistente en disco: fichas del catálogo, esqueleto y contenido, validados por versión |
| `structures/tabla_hash.py`, `cache_catalogo.py`, `grafo_salas.py`, `lista_sin_repetidos.py` | Tabla hash propia, caché LRU del catálogo, grafo de salas con BFS |
| `repository/repositorio_cripta.py` | Punto de entrada del bloque 2 para el controlador: precarga, catálogo, caché y reporte de red |

Todavía no existe un juego ejecutable. El punto de entrada `main.py` está vacío. El bloque 2 ya resuelve la lectura sin conexión, la verificación de versiones que necesita la reproducción y sus propias mediciones, pero todavía no está conectado a `main.py`. Cómo integrarlo está en `docs/BLOQUE_2_PARA_EL_GRUPO.md`.

## Requisitos

Python 3.11 o superior. El desarrollo se está realizando sobre Python 3.14.6.

Las dependencias están en `requirements.txt`. Se instalan con:

```
pip install -r requirements.txt
```

## Ejecutar las pruebas

Desde la carpeta `cripta/`:

```
python -m unittest discover -s tests -t . -v
```

En Windows también funciona `py` en lugar de `python`.

## Herramientas del bloque 2

También desde la carpeta `cripta/`:

| Comando | Qué hace |
| --- | --- |
| `python -m tools.simular_partida_bloque2` | Recorre una cripta usando solo el bloque 2 y muestra el reporte de solicitudes. Con `--offline datos_offline` no usa la red; con `--borrar-cache` fuerza un arranque en frío |
| `python -m tools.descargar_datos_offline` | Descarga las criptas publicadas del API a `datos_offline/` |
| `python -m tools.ejecutar_verificaciones` | Corre todas las pruebas y los benchmarks del bloque 2 y guarda la salida en `resultados_verificacion.txt` |
| `python -m benchmark.bench_tabla_hash` | Mide la tabla hash contra sus alternativas (también `bench_cache_catalogo`, `bench_almacen_fichas` y `bench_precarga_contenido`) |

## Comandos del programa

Pendientes de implementar. Según el enunciado, la versión final debe aceptar:

| Bandera | Función |
| --- | --- |
| `--offline` | Leer las respuestas desde un paquete en disco en lugar de la red |
| `--cache-size` | Tope de fichas de catálogo en memoria, 25 por omisión |
| `--replay partida.log` | Reproducir una partida completa sin interacción del usuario |
| `--bench` | Ejecutar las mediciones de rendimiento por subsistema |

## Organización del proyecto

La estructura de carpetas, las responsabilidades de cada módulo y las interfaces acordadas están en `docs/ARQUITECTURA.md`.

Las decisiones de diseño, con sus alternativas, complejidades y evidencia, están en `docs/DECISIONES.md`.

El registro de uso de herramientas de IA está en `PROMPTS_LLM.md`.

## Archivos generados

| Ubicación | Qué contiene |
| --- | --- |
| `cache_cripta/` | Caché persistente del bloque 2: fichas del catálogo (`catalogo/`) y esqueleto y contenido de cada cripta (`criptas/`). Se puede borrar sin problema; el programa la vuelve a llenar. No se sube al repositorio |
| `resultados_verificacion.txt` | Salida de `tools.ejecutar_verificaciones`. No se sube al repositorio |

La carpeta `datos_offline/` sí está en el repositorio: tiene `cripta-01` descargada del API real, para desarrollar y probar sin red. El código del programa nunca debe depender de su contenido, porque la revisión usa una cripta no publicada (§9).

Pendiente de definir: los archivos de guardado binario, las bitácoras de partida y la tabla de puntajes, cuando esos módulos existan.
