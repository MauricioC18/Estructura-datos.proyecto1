# CRIPTA

Juego de mazmorra dirigido por eventos, desarrollado como primer proyecto del curso Estructuras de Datos II, II Ciclo 2026, Universidad Nacional de Costa Rica.

El proyecto consiste en diseñar, implementar y evaluar las estructuras de datos necesarias para resolver los problemas planteados en el enunciado: selección del siguiente evento, precarga de contenido, resolución del catálogo, caché persistente, inventario, historial reversible, rastro del jugador, bitácora en pantalla, ordenamiento y guardado binario.

El enunciado oficial está en `docs/proyecto_cripta.md` y es la referencia para cualquier duda sobre las reglas del juego.

## Estado actual

El juego se puede jugar completo desde la consola, contra el API o sin conexión. Cada partida queda registrada para reproducirla con `--replay`, y se puede guardar en un archivo binario propio (§4.10) para continuarla después con `--cargar`.

| Parte | Módulos |
| --- | --- |
| Motor, agenda y reloj | `model/game.py`, `model/game_state.py`, `model/event.py`, `structures/event_queue.py`, actores y efectos en `model/` |
| Red, caché y persistencia de la cripta | `adapters/fuente_*.py`, `adapters/almacen_*.py`, `structures/tabla_hash.py`, `structures/cache_catalogo.py`, `repository/` |
| Inventario, retroceso, rastro, bitácora y ordenamientos | `structures/inventory.py`, `history.py`, `trail.py`, `circular_log.py`, `sorting.py` |
| Aplicación, interfaz, reproducción y mediciones | `main.py`, `controller/`, `view/console_view.py`, `replay/`, `benchmark/benchmark.py`, `adapters/scoreboard.py` |

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

## Cómo jugar

Desde la carpeta `cripta/`:

| Comando | Qué hace |
| --- | --- |
| `python main.py` | Juega contra el API. Pregunta el nombre y la cripta |
| `python main.py --offline` | Juega sin red, con el paquete de `datos_offline/`. Con `--offline CARPETA` usa otro paquete |
| `python main.py --cargar ARCHIVO` | Continúa una partida guardada con el comando `guardar` |
| `python main.py --replay partidas/ARCHIVO.log` | Reproduce una partida completa, sin interacción y sin la vista interactiva (§4.11). Funciona también con `--offline` |
| `python main.py --bench` | Corre las mediciones de todos los subsistemas (§5.3). Tarda alrededor de un minuto |
| `python main.py --puntajes [CRIPTA]` | Muestra la tabla de puntajes, de todas las criptas o de una |

Otras opciones:

| Bandera | Función |
| --- | --- |
| `--cripta ID` | Elige la cripta sin preguntar |
| `--semilla N` | Fija la semilla de la partida. Si no se indica, se elige una al azar y queda escrita en la bitácora |
| `--nombre TEXTO` | Nombre del jugador para la tabla de puntajes |
| `--cache-size N` | Tope de fichas del catálogo en memoria, 25 por omisión (§4.4) |
| `--cache CARPETA` | Carpeta de la caché persistente, `cache_cripta` por omisión |

Comandos dentro de la partida (con `ayuda` se ven en pantalla):

| Comando | Acción |
| --- | --- |
| `mover N\|S\|E\|O` | Moverse a la sala vecina |
| `abrir N\|S\|E\|O` | Abrir una puerta con la llave del inventario |
| `atacar <id>` | Atacar a un enemigo de la sala, por ejemplo `atacar e-201` |
| `esperar` | Dejar pasar una acción |
| `recoger <n>` | Recoger el objeto `n` del suelo, contando desde 0 |
| `soltar`, `usar`, `equipar` | Actúan sobre el objeto que se está viendo en el inventario |
| `sig`, `ant` | Ver el objeto siguiente o el anterior del inventario |
| `ver [peso\|valor\|nombre]` | Mostrar el inventario, en su orden real u ordenado |
| `retroceder` | Usar un pergamino de retroceso |
| `guardar <archivo>` | Guardar la partida en el archivo binario indicado |
| `cargar <archivo>` | Deja la partida actual y continúa la guardada, con una bitácora nueva. Si el archivo no sirve, se sigue en la partida actual |
| `salir` | Terminar la sesión |

Al terminar una partida el programa muestra el resultado, la registra en la tabla de puntajes si se ganó o se perdió, y muestra el reporte de red: solicitudes realizadas, presupuesto de la cripta, aciertos y fallos de caché (§5.1).

Una partida reproducida con `--replay` solo se ejecuta si la fuente tiene las mismas versiones de cripta y catálogo que indica el log. Si no las tiene, el programa lo informa y no reproduce. Para un log viejo se usa `--offline` con una copia de los datos de esas versiones.

El log de una sesión que empezó cargando un guardado, con `--cargar` o con `cargar`, indica en su cabecera de qué archivo salió (`partida_cargada`) y su huella (`huella_partida`). Para reproducirlo, ese archivo tiene que seguir en la misma ruta y sin cambios; si no, el programa lo informa y no reproduce.

## Herramientas del bloque 2

También desde la carpeta `cripta/`:

| Comando | Qué hace |
| --- | --- |
| `python -m tools.simular_partida_bloque2` | Recorre una cripta usando solo el bloque 2 y muestra el reporte de solicitudes. Con `--offline datos_offline` no usa la red; con `--borrar-cache` fuerza un arranque en frío |
| `python -m tools.descargar_datos_offline` | Descarga las criptas publicadas del API a `datos_offline/` |
| `python -m tools.ejecutar_verificaciones` | Corre todas las pruebas y los benchmarks del bloque 2 y guarda la salida en `resultados_verificacion.txt` |
| `python -m benchmark.bench_tabla_hash` | Mide un subsistema suelto (también `bench_cache_catalogo`, `bench_almacen_fichas`, `bench_precarga_contenido`, `scheduler_bench` `persona3_bench` y `bench_almacen_partida`) |

## Organización del proyecto

La estructura de carpetas, las responsabilidades de cada módulo y las interfaces acordadas están en `docs/ARQUITECTURA.md`.

Las decisiones de diseño, con sus alternativas, complejidades y evidencia, están en `docs/DECISIONES.md`.

El registro de uso de herramientas de IA está en `PROMPTS_LLM.md`.

## Archivos generados

Todos se crean dentro de la carpeta desde la que se ejecuta el programa (normalmente `cripta/`) y ninguno se sube al repositorio.

| Ubicación | Qué contiene |
| --- | --- |
| `partidas/` | Una bitácora de reproducción por partida, `<cripta>-<fecha>-<hora>.log`. La cabecera tiene la cripta, sus versiones y la semilla; después va una acción aceptada por línea |
| `puntajes.txt` | Tabla de puntajes local (§2.12): una línea por partida terminada |
| `cache_cripta/` | Caché persistente: fichas del catálogo (`catalogo/`) y esqueleto y contenido de cada cripta (`criptas/`). Se puede borrar sin problema; el programa la vuelve a llenar |
| `<archivo>` de `guardar` | Partida guardada en formato binario propio (§4.10), en la ruta que se indique |
| `resultados_verificacion.txt` | Salida de `tools.ejecutar_verificaciones` |

La carpeta `datos_offline/` sí está en el repositorio: tiene `cripta-01` descargada del API real, para desarrollar y probar sin red. El código del programa nunca depende de su contenido, porque la revisión usa una cripta no publicada (§9).
