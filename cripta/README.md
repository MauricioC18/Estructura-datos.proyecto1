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

### Desarrollo dirigido por especificaciones (segunda parte)

La segunda parte se desarrolla con GitHub spec-kit. Todo el grupo usa la misma
version, fijada:

```
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.4.1
```

| | |
| --- | --- |
| Version de spec-kit | **v1.4.1** |
| Agente de programacion | **Claude Code** |

El repositorio ya esta inicializado: `.specify/` y `.claude/` estan versionados,
asi que **no hay que volver a correr `specify init`**; basta con `git pull`. Los
principios que gobiernan el proyecto estan en `.specify/memory/constitution.md` y
las especificaciones de cada capacidad en `specs/`.

Nota: el enunciado menciona la bandera `--ai`, que es de la version 1.1 de
spec-kit. En la 1.4.1 se llama `--integration`.

## Ejecutar las pruebas

Desde la carpeta `cripta/`:

```
python -m unittest discover -s tests -t . -v
```

En Windows también funciona `py` en lugar de `python`.

Estado al 2026-11-17, en la rama `Parte_2-niebla-ir-a`: **1229 pruebas, todas pasan**, medido con Python 3.12.3. Dos de ellas se cuentan como *fallos esperados* (ver «Lo que todavía no funciona»).

### Pruebas de aceptación por capacidad

Cada prueba cita en su docstring el requisito (`FR-xxx`) de la especificación que comprueba (§2.5). Para correr solo las de una capacidad, también desde `cripta/`:

| Capacidad | Especificación | Comando |
| --- | --- | --- |
| Niebla de guerra e «ir a» | `specs/005-niebla-ir-a/spec.md` | `python -m unittest discover -s tests -t . -p "test_mapa_conocido.py"`, y lo mismo con `test_viaje.py`, `test_ir_a.py`, `test_ir_a_sentido.py`, `test_equivalencia_sentido.py`, `test_niebla.py`, `test_niebla_guardado.py`, `test_comando_mapa.py`, `test_vista_mapa_conocido.py`, `test_vista_sala_actual.py`, `test_historia_mapa_conocido.py`, `test_parada_anticipada.py`, `test_reutilizar_ruta.py` y `test_bench_paquete_sin_conexion.py` |

Las mediciones de esta capacidad están en la suite «Mapa conocido y viaje ir a» de `python main.py --bench`. Al final de la suite hay una fila por cada cripta del paquete sin conexión, con el id que traen sus datos y su número de salas. Para medir otro paquete, como el de la segunda parte, se usa `python main.py --bench --offline CARPETA`; sin `--offline` se mide `datos_offline/`. La fila mide «ir a» con todo el mapa conocido explorado y muestra:

- hacia dónde fue el viaje: de la sala inicial de la cripta (la `sala_inicial` de sus datos generales) a la última sala del esqueleto, con su costo mínimo. Si con el mapa conocido no hay ruta entre ellas, o la sala inicial ya es la última, la fila lo dice y mide el viaje hacia la sala más lejana que se alcanza desde la inicial por costo mínimo (si empatan, la de menor id). Si desde la sala inicial no se alcanza ninguna otra, también lo dice;
- el primer paso del viaje, como lo calcula el programa;
- el promedio por paso del viaje entero y cuántos pasos tuvo. Si el viaje no dio ningún paso, la fila lo dice en vez de mostrar un promedio;
- la búsqueda completa sin mejoras y la búsqueda sin montículo, como referencias.

La búsqueda del cazador en la misma cripta no está en esta fila: está en la suite «Persecucion del cazador».

Para ver solo las filas de las criptas reales, sin las cuadrículas sintéticas: `python -c "from benchmark.bench_mapa_conocido import mediciones_de_criptas_reales as m; [print(x.name, x.detail) for x in m('CARPETA')]"`.

## Cómo jugar

Desde la carpeta `cripta/`:

| Comando | Qué hace |
| --- | --- |
| `python main.py` | Juega contra el API. Pregunta el nombre y la cripta |
| `python main.py --offline` | Juega sin red, con el paquete de `datos_offline/`. Con `--offline CARPETA` usa otro paquete |
| `python main.py --cargar ARCHIVO` | Continúa una partida guardada con el comando `guardar` |
| `python main.py --replay partidas/ARCHIVO.log` | Reproduce una partida completa, sin interacción y sin la vista interactiva (§4.11). Funciona también con `--offline` |
| `python main.py --replay partidas/ARCHIVO.log --hasta T` | Reproduce la partida y al final imprime el estado del instante `T`, el mismo resumen que el comando `historia`, sin la vista interactiva. **Ver la nota sobre la línea de tiempo más abajo** |
| `python main.py --bench` | Corre las mediciones de todos los subsistemas (§5.3). Tarda alrededor de un minuto |
| `python main.py --bench --offline CARPETA` | Igual, pero la medición de «ir a» en criptas reales usa las criptas del paquete de `CARPETA` en vez de `datos_offline/`. Las demás suites no cambian |
| `python main.py --puntajes [CRIPTA]` | Muestra la tabla de puntajes, de todas las criptas o de una |

Otras opciones:

| Bandera | Función |
| --- | --- |
| `--cripta ID` | Elige la cripta sin preguntar |
| `--semilla N` | Fija la semilla de la partida. Si no se indica, se elige una al azar y queda escrita en la bitácora |
| `--nombre TEXTO` | Nombre del jugador para la tabla de puntajes |
| `--cache-size N` | Tope de fichas del catálogo en memoria, 25 por omisión (§4.4) |
| `--cache CARPETA` | Carpeta de la caché persistente, `cache_cripta` por omisión |
| `--checkpoint-cada K` | Acciones del jugador entre dos copias completas del estado de la línea de tiempo, 50 por omisión; tiene que ser al menos 1 |

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
| `mapa` | Ver las salas exploradas, sus salidas, el estado recordado de cada puerta y las salas avistadas (niebla de guerra, §3.3). No consume tiempo |
| `ir a <sala>` | Viajar a una sala explorada por la ruta conocida más barata, un movimiento por paso (§3.4); al detenerse dice por qué. **Todavía no respeta las salidas de un solo sentido**: ver la nota más abajo |
| `historia <t>`, `historia #k` | Ver el estado de la partida en el instante `t` o antes de la acción `k`, incluido el mapa conocido de ese momento. **Ver la nota sobre la línea de tiempo más abajo** |
| `salir` | Terminar la sesión |

Al terminar una partida el programa muestra el resultado, la registra en la tabla de puntajes si se ganó o se perdió, y muestra el reporte de red: solicitudes realizadas, presupuesto de la cripta, aciertos y fallos de caché (§5.1).

Una partida reproducida con `--replay` solo se ejecuta si la fuente tiene las mismas versiones de cripta y catálogo que indica el log. Si no las tiene, el programa lo informa y no reproduce. Para un log viejo se usa `--offline` con una copia de los datos de esas versiones.

El log de una sesión que empezó cargando un guardado, con `--cargar` o con `cargar`, indica en su cabecera de qué archivo salió (`partida_cargada`) y su huella (`huella_partida`). Para reproducirlo, ese archivo tiene que seguir en la misma ruta y sin cambios; si no, el programa lo informa y no reproduce.

## Lo que todavía no funciona

- **«ir a» con salidas de un solo sentido.** La búsqueda todavía recorre cada salida en los dos sentidos, así que con una salida sin vuelta puede declarar «no hay ruta» teniendo una salida directa, o no ver una ruta válida. La corrección está escrita (`MapaConocido.entrantes_conocidas`) y probada por equivalencia, pero conectarla necesita que la búsqueda compartida (`structures/rutas_mas_baratas.py`) acepte la parada anticipada junto con el proveedor de salidas. Las dos pruebas de los escenarios 7 y 8 de la Historia 4 (`tests/test_ir_a_sentido.py`) están marcadas como fallo esperado hasta entonces (tarea T052 de `specs/005-niebla-ir-a/tasks.md`).
- **`historia` y `--replay --hasta` con copias espaciadas.** Para un instante posterior a un movimiento hacia una sala cuyo contenido no estaba cargado cuando se tomó la copia, la reconstrucción repite el movimiento, el motor lo rechaza porque esa sala no tiene contenido, y el resumen entero sale en la sala anterior, sin ningún error. Con `--checkpoint-cada 1` no pasa. Es un defecto de la reconstrucción de la línea de tiempo, reportado a su responsable.
- **La cripta de referencia de §6.1** (cripta-06, de 300 salas) no está en el paquete sin conexión, así que el límite de 5 ms por paso de «ir a» no está comprobado sobre ella. En las cuadrículas sintéticas, el primer paso de un viaje entre los extremos pasa de 5 ms desde 400 salas (`docs/DECISIONES.md`, §5.3).
- `--verificar` y `--forzar` (resolubilidad) no están implementadas.

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
