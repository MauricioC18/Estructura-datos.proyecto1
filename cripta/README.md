# CRIPTA

Juego de mazmorra dirigido por eventos, desarrollado como primer proyecto del curso Estructuras de Datos II, II Ciclo 2026, Universidad Nacional de Costa Rica.

El proyecto consiste en diseñar, implementar y evaluar las estructuras de datos necesarias para resolver los problemas planteados en el enunciado: selección del siguiente evento, precarga de contenido, resolución del catálogo, caché persistente, inventario, historial reversible, rastro del jugador, bitácora en pantalla, ordenamiento y guardado binario.

La **segunda parte** (`docs/SegundoProyecto-EDII-2026.md`) agrega cuatro capacidades, cada una con su especificación de spec-kit en `../specs/`: el terreno y el cazador, con su ruta más barata y la invalidación de rutas (001 y 002); la línea de tiempo con puntos de control (003); los datos nuevos del servicio (004); la niebla de guerra y el viaje «ir a» (005); y la verificación de resolubilidad (006). Las decisiones de diseño de cada problema están en `docs/DECISIONES.md`, §5.1 a §5.6.

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

Python 3.11 o superior.

Las dependencias están en `requirements.txt`. Se instalan con:

```
pip install -r requirements.txt
```

### Desde cero

En una máquina sin nada instalado del proyecto, con Python 3.11 o superior:

```
git clone https://github.com/MauricioC18/Estructura-datos.proyecto1.git
cd Estructura-datos.proyecto1/cripta
python -m venv .venv
.venv\Scripts\activate            (en Windows)
source .venv/bin/activate           (en Linux o macOS)
pip install -r requirements.txt
python -m unittest discover -s tests -t .
python main.py --verificar cripta-06 --offline datos_offline_p2
python main.py --verificar cripta-05 --offline datos_offline_p2
python main.py --bench --offline datos_offline_p2
```

El primer `--verificar` termina con código 0 (resoluble) y el segundo con 1 (no resoluble). `--bench` tarda uno o dos minutos. Las partidas jugadas dejan su bitácora en `partidas/`, que no se versiona.

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

Estado al 2026-11-18, en la rama `Parte_2-niebla-ir-a`: **1341 pruebas, todas pasan**, medido con Python 3.12.3 en WSL (no hay un Python de Windows instalado en el equipo donde se corrieron). Una se cuenta como *fallo esperado* (ver «Lo que todavía no funciona»). Incluye lo unido de `main` (con el arreglo de T023 de la línea de tiempo) y de la rama de Mauricio (`specs/004-datos-nuevos-servicio`, `specs/006-resolubilidad` y el paquete `datos_offline_p2/`).

### Pruebas de aceptación por capacidad

Cada prueba cita en su docstring el requisito (`FR-xxx`) de la especificación que comprueba (§2.5). Para correr solo las de una capacidad, también desde `cripta/`:

| Capacidad | Especificación | Comando |
| --- | --- | --- |
| Verificación de resolubilidad | `specs/006-resolubilidad/spec.md` | `python -m unittest discover -s tests -t . -p "test_resolubilidad.py"`, y para las banderas `--verificar` y `--forzar` y el reporte al iniciar, `-p "test_banderas_resolubilidad.py"` |
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
| `python main.py --replay partidas/ARCHIVO.log --hasta T` | Reproduce la partida y al final imprime el estado del instante `T`, el mismo resumen que el comando `historia`, sin la vista interactiva. Si `T` es posterior al final de la partida, muestra el estado final y avisa que la partida terminó antes. **Ver la nota sobre la línea de tiempo más abajo** |
| `python main.py --verificar CRIPTA` | Solo verifica si la cripta se puede ganar y muestra el reporte, sin la vista del juego y sin empezar una partida (§3.5). Termina con 0 si es resoluble, 1 si no lo es y 2 si no se pudo verificar porque falta la ubicación de llaves; 3 si la cripta no se pudo leer. Funciona con `--offline CARPETA`, por ejemplo `python main.py --verificar cripta-05 --offline datos_offline_p2` |
| `python main.py --forzar` | Empieza la partida aunque la cripta no sea resoluble. Sin `--forzar`, una partida nueva de una cripta no resoluble no empieza y se muestra el reporte. Con o sin la bandera, el reporte de resolubilidad se muestra antes de la primera acción. Una partida cargada no se verifica de nuevo, y `--replay` nunca se detiene por la verificación |
| `python main.py --bench` | Corre las mediciones de todos los subsistemas (§5.3). Tarda uno o dos minutos (2 min 9 s con `--offline datos_offline_p2` en WSL) |
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
| `ir a <sala>` | Viajar a una sala explorada por la ruta conocida más barata, un movimiento por paso (§3.4); al detenerse dice por qué. Respeta las salidas de un solo sentido: solo las recorre en su sentido |
| `historia <t>`, `historia #k` | Ver el estado de la partida en el instante `t` o antes de la acción `k`, incluido el mapa conocido de ese momento. **Ver la nota sobre la línea de tiempo más abajo** |
| `salir` | Terminar la sesión |

Al terminar una partida el programa muestra el resultado, la registra en la tabla de puntajes si se ganó o se perdió, y muestra el reporte de red: solicitudes realizadas, presupuesto de la cripta, aciertos y fallos de caché (§5.1).

Una partida reproducida con `--replay` solo se ejecuta si la fuente tiene las mismas versiones de cripta y catálogo que indica el log. Si no las tiene, el programa lo informa y no reproduce. Para un log viejo se usa `--offline` con una copia de los datos de esas versiones.

El log de una sesión que empezó cargando un guardado, con `--cargar` o con `cargar`, indica en su cabecera de qué archivo salió (`partida_cargada`) y su huella (`huella_partida`). Para reproducirlo, ese archivo tiene que seguir en la misma ruta y sin cambios; si no, el programa lo informa y no reproduce.

## Lo que todavía no funciona

- **`historia` y `--replay --hasta` de un instante entre dos decisiones del jugador, en un caso.** El arreglo de T023 (`main`) hace que, en general, no se cuenten los eventos posteriores al instante. Pero si hay una copia de la línea de tiempo justo en la última acción anterior al instante, el resumen todavía incluye los eventos posteriores hasta la siguiente decisión. Solo afecta a los tramos que siguen a una acción con copia: con el valor por omisión (*K* = 50), una de cada 50 acciones más las copias forzadas; con `--checkpoint-cada 1`, todos. La prueba `tests/test_eventos_mismo_instante.py` (`test_un_evento_posterior_al_instante_no_cuenta`) sigue marcada como fallo esperado. Está descrito en `docs/DECISIONES.md` §5.5 y reportado a Carlos.
- **«ir a» en mapas mucho más grandes que la cripta de referencia.** En cripta-06 (300 salas) un paso tarda como máximo 0.45 ms, y 3.19 ms con todas las puertas abiertas, debajo del límite de 5 ms. En las cuadrículas sintéticas de 400 y 1600 salas, el primer paso de un viaje largo pasa de 5 ms (5.59 y 30.31 ms en la última corrida); los pasos siguientes no (`docs/DECISIONES.md`, §5.3).
- **Salidas de un solo sentido en criptas reales.** «ir a» y la verificación de resolubilidad las respetan, pero ninguna cripta del paquete `datos_offline_p2/` tiene una, así que solo lo comprueban las pruebas con mapas sintéticos.
- **La verificación de resolubilidad con salidas de un solo sentido** supone que una llave obtenida sirve en toda la región alcanzable, aunque el jugador no siempre pueda volver a la puerta que abre. Es un límite declarado en `specs/006-resolubilidad/spec.md` (Assumptions) y en `docs/DECISIONES.md` §5.4.
- **`historia #k` cuenta las acciones desde 0 en el programa, y la especificación dice desde 1.** La spec 003 (FR-003) fija que `historia #1` es el estado justo antes de la primera acción, igual que `historia 0`. El modelo (`model/consulta_historia.py`) toma `#k` como el estado después de *k* acciones, así que hoy `historia #1` muestra «antes de la accion 2», y `historia #k` con *k* igual a las acciones tomadas se acepta y muestra el presente en vez de la última acción. Es un desfase conocido, pendiente de corregir en el código. Mientras tanto, `historia <t>` con un instante del reloj responde bien.
- **Python 3.11 no se probó en este equipo.** Todas las pruebas y mediciones de la entrega se corrieron con Python 3.12.3 en WSL, porque en el equipo no hay un Python 3.11 ni un Python de Windows instalado.

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
