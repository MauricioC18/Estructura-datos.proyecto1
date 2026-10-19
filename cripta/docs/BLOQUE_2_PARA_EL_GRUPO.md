# Bloque 2 — API, caché y persistencia: guía para el grupo

Responsable: Mauricio (persona 2). Última actualización: 18 de octubre de 2026.

Este documento explica qué está listo en el bloque 2, cómo usarlo desde el resto del
programa, qué datos entrega y **qué necesita el bloque 2 de cada integrante** para quedar
terminado.

---

## 1. Estado

| Pieza | Archivo | Estado |
|---|---|---|
| Tabla hash propia (reemplaza a `dict`, §7) | `structures/tabla_hash.py` | Listo |
| Lista sin repetidos | `structures/lista_sin_repetidos.py` | Listo |
| Grafo de salas y BFS | `structures/grafo_salas.py` | Listo |
| Caché LRU del catálogo (`--cache-size`) | `structures/cache_catalogo.py` | Listo |
| Contrato común de fuentes | `adapters/fuente_datos.py` | Listo |
| Cliente del API (UUID, timeout, 429, errores, presupuesto) | `adapters/fuente_http.py` | Listo |
| Modo `--offline` | `adapters/fuente_offline.py` | Listo |
| Fichas en disco (índice binario ordenado) | `adapters/almacen_fichas.py` | Listo |
| Esqueleto y contenido en disco por versión | `adapters/almacen_cripta.py` | Listo |
| Fichas: memoria → disco → API en lotes de 10 | `repository/gestor_catalogo.py` | Listo |
| Contenido con precarga BFS | `repository/gestor_contenido.py` | Listo |
| Frecuencia medida de las operaciones (§8.1) y estrategias del catálogo | `benchmark/bench_frecuencia_bloque2.py` | Listo |
| Secciones 4.2, 4.3 y 4.4 del Documento de Decisiones | `docs/DECISIONES.md` | Listo |
| **Punto de entrada para el controlador** | `repository/repositorio_cripta.py` | Listo |
| `Traductor` (JSON → objetos del modelo) | `repository/traductor.py` | Listo |
| Clases del modelo que faltaban: sala, puerta, salida, mapa | `model/room.py` | Listo (revisar con la persona 1) |
| Instancia de objeto y de trampa | `model/item.py`, `model/trap.py` | Listo (revisar con la persona 1) |

Pruebas: 300 del bloque 2; la rama del bloque 2 tiene 387 y todas pasan
(`python -m unittest discover -s tests -t .` desde `cripta/`). Unida con las ramas de las
personas 1 y 4 (revisión del 15 de octubre), el proyecto tiene 528 pruebas y todas pasan. Conexión real con el API
verificada. Las mediciones están en `docs/mediciones/bloque2/`.

Todo el código del bloque 2 vive dentro de las carpetas que define `docs/ARQUITECTURA.md`
(`adapters/`, `structures/`, `benchmark/`, `tests/`), más dos carpetas nuevas: `repository/` y
`tools/`. Los nombres de archivos, clases y métodos están en español; la convención de nombres
sigue entre las decisiones pendientes del grupo (ARQUITECTURA, sección 9).

Presupuesto medido con cripta-01 (presupuesto 9):
- arranque en frío: **7 solicitudes** (lista, datos generales, versión del catálogo, 1 página,
  1 lote de contenido con las 6 salas, 2 lotes de catálogo con las 11 fichas). Las 7 ocurren
  antes del primer movimiento, así que recorrer la cripta completa no hace esperar en ninguna
  puerta;
- arranque en caliente (copia en disco vigente): **3 solicitudes** (lista, datos generales,
  versión del catálogo).

---

## 2. Cómo se usa desde el controlador (persona 4)

El controlador solo usa `RepositorioCripta`. Nunca usa HTTP, archivos ni la caché directamente.

```python
from adapters.fuente_http import FuenteHttp
from adapters.fuente_offline import FuenteOffline
from adapters.fuente_datos import ErrorFuenteDatos, PresupuestoAgotado
from repository.repositorio_cripta import RepositorioCripta, VersionesIncompatibles

# Al iniciar el programa (una vez por ejecución):
fuente = FuenteOffline(carpeta) if argumentos.offline else FuenteHttp()
repositorio = RepositorioCripta(
    fuente,
    "cache_cripta",                # carpeta de la caché en disco
    argumentos.cache_size,         # --cache-size (25 por defecto)
    consultar_ids_en_uso,          # función del controlador, ver más abajo
)

# Al empezar una partida:
repositorio.empezar_conteo_de_partida()       # la lista de criptas ya cuenta (§5.1)
criptas = repositorio.listar_criptas()        # [{"id", "nombre", "salas", "dificultad"}, ...]
datos = repositorio.iniciar_partida(id_elegido)
# datos.sala_inicial, datos.sala_salida, datos.llave_salida, datos.inventario_max,
# datos.presupuesto_solicitudes, datos.jugador (vida_max, ataque, defensa, velocidad)

# Objetos del modelo (los crea el Traductor, sección 2.1):
jugador = repositorio.crear_jugador()         # Player en la sala inicial
mapa = repositorio.crear_mapa()               # RoomMap: salas con salidas y puertas compartidas
enemigos = repositorio.cargar_contenido_de_sala(mapa.room(jugador.room_id))
partida = Game(estado, jugador, enemigos)     # el motor guarda la lista plana de enemigos

# Antes de confirmar que el jugador entra a una sala (§2.5):
try:
    nuevos = repositorio.cargar_contenido_de_sala(mapa.room(id_destino))
    partida.enemies.extend(nuevos)            # llegan dormidos; el motor los activa (§2.4)
except PresupuestoAgotado:
    ...  # rechazar el movimiento SIN consumir tiempo virtual (supuesto S1)

# Después de cada acción del jugador (precarga contenido y fichas):
repositorio.despues_de_accion(id_sala_actual)

# Cuando un enemigo muere: no hace falta la red. Sus objetos ya vienen creados.
sala.floor_items.extend(enemigo.drops)

# Si alguna vez hace falta el JSON del API sin traducir:
repositorio.sala_del_esqueleto(id_sala)   # la sala con sus salidas
repositorio.contenido_de_sala(id_sala)    # enemigos, objetos y trampas
repositorio.obtener_ficha(id_tipo)        # ficha del catálogo; nunca usa la red
repositorio.vecinos_de_sala(id_sala)      # ids vecinos en orden N, S, E, O

# Al terminar (§5.1):
for linea in repositorio.reporte_de_red().lineas_de_texto():
    print(linea)
```

### 2.1 Objetos del modelo que entrega el Traductor

`repository/traductor.py` es el único archivo que conoce los nombres de los campos del API.
El controlador no lo usa directamente: `RepositorioCripta` lo crea en `iniciar_partida` y
ofrece `crear_jugador`, `crear_mapa`, `cargar_contenido_de_sala` e `ids_en_uso`.

| Clase | Archivo | Qué trae |
|---|---|---|
| `Player` | `model/player.py` (persona 1) | Estadísticas de los datos generales, en la sala inicial. Id `"jugador"` |
| `Enemy` | `model/enemy.py` (persona 1) | Estadísticas de su ficha; `behavior` ya convertido a `Enemy.GUARDIAN`, `WANDERER` o `TRACKER`; `drops` con los `Item` que suelta |
| `RoomMap` | `model/room.py` | Todas las salas, buscables por id con `room(id)` (usa `TablaHash`) |
| `Room` | `model/room.py` | `exit_towards("N")`, `exits()` en orden N, S, E, O, `floor_items`, `traps`, `content_loaded` |
| `Exit` / `Door` | `model/room.py` | Salida: `direction`, `destination`, `door`. Puerta: `closed`, `key_id`, `auto_close`, `is_open` |
| `Item` | `model/item.py` | `instance_id`, `type_id`, `name`, `item_class`, `weight`, `value`, `attack_bonus`, `defense_bonus`, `heal`, `speed_modifier`, `duration`, `opens` |
| `Trap` | `model/trap.py` | `instance_id`, `type_id`, `name`, `damage`, `rearm_interval` (300 si falta), `room_id`, `armed` |

Acuerdos que salen de cómo están hechas:
- **Una sola puerta por paso** (S9): el mismo objeto `Door` aparece en las dos salas, así que
  abrirla desde un lado se ve desde el otro. Las reglas (abrir con llave, cierre automático)
  las aplica el motor.
- **Los enemigos no se guardan en `Room`**: llegan dormidos y el motor los agrega a su lista
  plana (`Game.enemies`), cada uno con su `room_id`, porque se mueven entre salas.
- **Lo que suelta un enemigo ya viene creado** en `enemigo.drops`. Las fichas de esos objetos
  se aseguran antes de entrar a la sala (normalmente con la precarga), nunca a mitad de un
  combate.
- **`Item` es plana**, como `Event`: los campos que no aplican a una clase valen 0 o `None`.
  Así el guardado binario (§4.10) la empaqueta igual para todas las clases. `attack_bonus` y
  `defense_bonus` son los nombres que `Player` ya usa por duck typing.
- **El modelo nunca compara contra textos del API**: el Traductor convierte `"guardián"` a
  `Enemy.GUARDIAN`. Un comportamiento desconocido es un error de datos (`ErrorDatosCripta`).
- Datos raros del esqueleto (salida a una sala inexistente, llaves distintas en cada lado de
  una puerta) no detienen el juego: se resuelven según S9 y aparecen como aviso en el reporte.

### La función `consultar_ids_en_uso`

La caché no puede liberar una ficha "en uso" (§4.4). El controlador le entrega al repositorio
una función sin argumentos que devuelve una `TablaHash` con los **ids de tipo** en uso. El
repositorio ya la arma con `ids_en_uso`; el controlador solo le pasa los objetos del modelo:

```python
def consultar_ids_en_uso():
    sala = mapa.room(jugador.room_id)
    objetos = inventario_y_equipo() + sala.floor_items   # Item (persona 3 y persona 1)
    return repositorio.ids_en_uso(partida.enemies, objetos, sala.traps)
```

Cuenta los enemigos vivos (y lo que sueltan), los objetos y las trampas. Solo se llama cuando
la caché necesita liberar algo, que es poco frecuente. Como el repositorio se crea antes que
el mapa, la función puede devolver una `TablaHash()` vacía mientras la partida no haya empezado.

### `--replay` (§4.11)

- Para el encabezado del log: `repositorio.versiones_de_la_partida()` devuelve
  `(id_cripta, version_cripta, version_catalogo)`.
- Al reproducir: `repositorio.iniciar_partida(id_cripta, (version_cripta, version_catalogo))`.
  Si la fuente tiene otras versiones lanza `VersionesIncompatibles` con un mensaje listo para
  mostrar, **antes** de cargar nada (supuesto S18).

### `--bench`

Cada benchmark del bloque 2 expone `run()`, igual que `benchmark/scheduler_bench.py`: devuelve
una lista de `Measurement` con `name`, `seconds` y `detail`. En la precarga, que cuenta
solicitudes y no mide tiempo, `seconds` es `None` y los números van en `detail`. Además tienen
`ejecutar()` e `imprimir()` para correrlos sueltos. Los módulos son
`benchmark.bench_tabla_hash`, `benchmark.bench_cache_catalogo`, `benchmark.bench_almacen_fichas`,
`benchmark.bench_precarga_contenido` y `benchmark.bench_frecuencia_bloque2`. El último cuenta
cuántas veces se ejecuta cada operación del bloque 2 en una partida y compara tres formas de
pedir el catálogo; sus cifras son las de las secciones 4.2 a 4.4 del Documento de Decisiones.

### Errores que el controlador debe atrapar

| Error | Módulo | Qué hacer |
|---|---|---|
| `PresupuestoAgotado` | `adapters.fuente_datos` | Rechazar la acción sin consumir tiempo y avisar |
| `ErrorFuenteDatos` | `adapters.fuente_datos` | Mostrar el mensaje (ya dice qué operación falló) |
| `VersionesIncompatibles` | `repository.repositorio_cripta` | En `--replay`: mostrar el mensaje y no reproducir |
| `FichaNoDisponible`, `ContenidoNoDisponible` | `repository.gestor_*` | Error de datos del API o de uso; mostrar el mensaje |
| `ErrorDatosCripta` | `repository.traductor` | El API mandó datos que no se pueden convertir al modelo; mostrar el mensaje |

---

## 3. Lo que el bloque 2 necesita de cada integrante

### Persona 1 (motor)
1. **Revisar las clases nuevas del modelo** (`model/room.py`, `model/item.py`,
   `model/trap.py`). Las hizo el bloque 2 para poder terminar el Traductor y siguen el estilo
   de `Actor` y `Event` (nombres en inglés, sin reglas del juego). No se modificó ningún
   archivo existente del modelo. Si en tu rama ya tienes tu propio `room.py`, avísame para
   unificar antes de fusionar.
2. **`Game.move()` ya encaja con el bloque 2.** Rechaza entrar a una sala sin
   `content_loaded`, y el modelo no llama al repositorio (MVC). Quien carga la sala antes de
   llamar a `move()` es el controlador (persona 4, punto 1). Al morir un enemigo, sus `drops`
   ya pasan a `floor_items` de su sala.
3. Revisar los supuestos S9 a S15 (sección 5), que afectan al motor.
4. Detalles del modelo frente a los datos reales del API (ya resueltos en el Traductor):
   - `Enemy.GUARDIAN` vale `"guardian"` y el API envía `"guardián"` con tilde. El Traductor
     convierte el texto del API a la constante, así que `decide_action()` puede comparar con
     `Enemy.GUARDIAN` sin problema. No hay que cambiar `Enemy`.
   - `Enemy` acepta `regeneration`, pero el contrato del API no tiene ningún campo para
     declararla (S13, verificado en el Swagger): el Traductor la deja en 0 y, si algún día
     llega un campo nuevo, lo avisa en el reporte final.
   - `Player` usa `attack_bonus` y `defense_bonus`; `Item` usa esos mismos nombres, así que
     equipar un `Item` funciona sin cambiar `Player`.

### Persona 3 (inventario, retroceso, rastro, ordenamientos)
1. **El inventario guarda objetos `Item`** (`model/item.py`): `weight` y `value` sirven para
   el peso y los ordenamientos, `instance_id` distingue dos objetos del mismo tipo y `type_id`
   es lo que se pasa a `ids_en_uso`.
2. Coordinar §4.9: el enunciado menciona "listas auxiliares del catálogo" entre los contextos
   de ordenamiento. Hoy el índice de fichas se mantiene ordenado insertando cada id en su
   lugar, sin llamar a un algoritmo de ordenamiento. Hay que decidir si ese contexto lo cubre
   su módulo o basta con los otros.
3. Usar `TablaHash` para cualquier búsqueda por clave (`dict` está prohibido, §7).
4. Recordar que **la caché no entra en el retroceso** (§2.11) y revisar S16 y S17.

### Persona 4 (MVC, interfaz, replay, bench)
1. **Cargar la sala destino antes de `Game.move()`, también al reproducir.** El controlador
   debe hacerlo antes de pasarle `mover` al modelo:
   ```python
   salida = mapa.room(partida.player.room_id).exit_towards(direccion)
   if salida is not None and salida.door.is_open:
       try:
           partida.enemies.extend(repositorio.cargar_contenido_de_sala(mapa.room(salida.destination)))
       except PresupuestoAgotado as error:
           return ActionResult(False, str(error))   # rechazada: no consume tiempo (S1)
   resultado = partida.move(direccion)
   ```
   y, después de cada acción aceptada, llamar a `repositorio.despues_de_accion(sala_actual)`.
   Si esto vive en `GameController`, `--replay` lo hereda sin cambios. Verificado el 15 de
   octubre con cripta-01 offline: con el `GameController` actual, `replay_commands()` se
   detiene en el primer `mover` ("El contenido de la sala 2 todavía no está disponible");
   con la carga previa, la partida reproducida termina igual que la original.
2. **`main.py`** (hoy vacío): `--offline` y `--cache-size` para crear el repositorio;
   `crear_jugador()`, `crear_mapa()` y `cargar_contenido_de_sala()` de la sala inicial;
   `Game(GameState(semilla), jugador, enemigos, mapa, datos.sala_salida)`; y al terminar,
   `reporte_de_red().lineas_de_texto()` (§5.1).
3. Armar `consultar_ids_en_uso` con `repositorio.ids_en_uso(...)` (sección 2.1).
4. En `--replay`: la cabecera sale de `versiones_de_la_partida()`, y al reproducir se llama a
   `iniciar_partida(id_cripta, (version_cripta, version_catalogo))`.
5. Incluir en `--bench` el `run()` de los cinco benchmarks del bloque 2.

---

## 4. Contrato de datos (lo que entrega el API)

Este es el JSON que llega del API. El `Traductor` lo convierte en objetos del modelo
aplicando estos valores por defecto. Los campos marcados "puede faltar" pueden no venir
o venir en `null`.

**Datos generales** (`DatosDePartida`): `id`, `version`, `salas_total`, `paginas`,
`salas_por_pagina`, `sala_inicial`, `sala_salida`, `llave_salida` (id de ficha),
`presupuesto_solicitudes`, `inventario_max`, `jugador` {`vida_max`, `ataque`, `defensa`, `velocidad`}.

**Sala del esqueleto**: `id` (entero), `nombre`, `salidas` (puede faltar):
`{"N"|"S"|"E"|"O": {"sala", "cerrada", "llave", "cierre_automatico"}}`.
En cada salida, `cerrada` falta = abierta; `llave` es el id de la ficha llave;
`cierre_automatico` es un entero mayor que 0 o falta.

**Contenido de una sala**: `sala` (entero) y tres listas que pueden faltar (= vacías):
- `enemigos`: `{"instancia", "tipo", "vida"}`; si `vida` falta, empieza con `vida_max`;
- `objetos`: lista de ids de ficha, **sin id de instancia** (ver S12);
- `trampas`: `{"instancia", "tipo"}`.

**Fichas del catálogo** (todas traen `id`, `nombre`, `clase`). En el Swagger, cada esquema es
cerrado (`"additionalProperties": false`): una ficha no puede traer campos fuera de esta tabla.

| `clase` | Campos | Notas |
|---|---|---|
| `enemigo` | `vida_max`, `ataque`, `defensa`, `velocidad`, `comportamiento`, `suelta` (puede faltar) | `comportamiento` es `"guardián"` (con tilde), `"errante"` o `"rastreador"` |
| `arma` | `peso`, `valor`, `ataque_bonus` | |
| `armadura` | `peso`, `valor`, `defensa_bonus` | |
| `pocion` | `peso`, `valor`, `cura`, `modificador_velocidad`, `duracion` (los tres pueden faltar) | |
| `antidoto` | `peso`, `valor` | |
| `llave` | `peso`, `valor`, `abre` (puede faltar) | No usar `abre` para abrir (S10) |
| `antorcha` | `peso`, `valor`, `duracion` | |
| `pergamino_retroceso` | `peso`, `valor` | |
| `trampa` | `daño` (con ñ), `rearme` (puede faltar → 300, §2.10) | |

Ejemplos reales: `tests/datos_cripta_01.py` y la carpeta `datos_offline/`. Ningún código del
programa puede depender de esos datos (§9): la revisión usa una cripta no publicada.

---

## 5. Supuestos y decisiones del grupo

El enunciado no define estos casos. Son decisiones razonadas que deben quedar en el README y en
el Documento de Decisiones.

**Red y presupuesto**
- **S1.** Si no quedan solicitudes para cargar la sala destino, el movimiento se rechaza sin
  consumir tiempo virtual (mismo patrón que el Apéndice B para acciones imposibles).
- **S2.** La cuenta de una partida empieza antes de listar las criptas. Toda solicitud enviada
  cuenta aunque falle, y cada reintento tras HTTP 429 cuenta aparte. Hay como máximo 5
  reintentos; si el API no indica la espera, se esperan 5 segundos.
- **S3.** La precarga se detiene cuando quedan 2 solicitudes o menos: se reservan para el
  contenido y las fichas de una sala a la que el jugador realmente intenta entrar.
- **S4.** Las solicitudes son síncronas y el contenido entra al modelo cuando el jugador entra
  a la sala, así que el orden de las respuestas nunca cambia la partida (§2.4).

**Caché y disco**
- **S5.** La política de desalojo es LRU. El tope de `--cache-size` es flexible: si todas las
  candidatas están en uso, se excede temporalmente y se informa. Un tope menor que 1 se rechaza.
- **S6.** Qué fichas están en uso se consulta al modelo solo al liberar.
- **S7.** Acierto de caché: ficha obtenida sin red (memoria o disco). Fallo: hubo que descargarla.
- **S8.** Si el disco falla, se juega sin persistencia y el reporte lo avisa.

**Datos y motor (persona 1)**
- **S9.** Cada paso entre dos salas tiene una sola puerta compartida. Está cerrada si
  cualquiera de los lados la declara cerrada; la llave y el cierre automático se toman del lado
  que los declara; si ambos declaran valores distintos, gana el de la sala con menor id. Sin
  salida de vuelta, el paso es de un solo sentido. *Confirmado en los datos reales: las puertas
  2↔5 y 4↔6 están declaradas cerradas solo desde un lado.*
- **S10.** Una puerta se abre comparando el campo `llave` de la salida con el id de la llave
  (§2.7). El campo `abre` solo se muestra: en los datos reales no coincide con nada
  (`"puerta_2_7"` en una puerta que une las salas 2 y 5).
- **S11.** Si un enemigo no trae `vida`, empieza con `vida_max`. Si `suelta` falta o es `null`,
  es una lista vacía. Las listas de contenido que faltan son vacías.
- **S12.** Los objetos del suelo reciben ids deterministas: sala y posición (`o-12-0`). Los
  objetos que suelta un enemigo usan su instancia y posición (`e-201-s0`).
- **S13.** Veneno y regeneración se implementan y se prueban aunque el API no tenga campos para
  activarlos. El antídoto se consume aunque no haya veneno activo. *Verificado en el contrato
  del API (`/openapi.json`, versión 1.0.0, 15 de octubre de 2026): el esquema `Enemy` solo
  permite `id`, `nombre`, `clase`, `vida_max`, `ataque`, `defensa`, `velocidad`,
  `comportamiento` y `suelta`; `EnemyPlacement` solo permite `instancia`, `tipo` y `vida`;
  los dos son cerrados y la palabra "regenera" no aparece en todo el documento.* Como la
  cripta de la revisión sale del mismo servicio, tampoco puede declarar regeneración. Si el
  contrato cambiara, el Traductor ignora cualquier campo que no conoce y lo anota en el
  reporte final, una vez por campo; leerlo sería una línea en `crear_enemigo`.
- **S14.** `modificador_velocidad` se suma a la velocidad (mínimo 1) durante `duracion`. La
  cripta publicada no tiene pociones de velocidad.
- **S15.** La antorcha se consume al encenderla y solo se muestra como efecto activo.

**Inventario, retroceso y rastro (persona 3)**
- **S16.** El retroceso **no** restaura el estado del generador aleatorio. Esto ya lo decidió
  el grupo (ARQUITECTURA, sección 6, "Qué registra la bitácora de reproducción"); la propuesta
  inicial de este bloque era la contraria y se descartó.
- **S17.** El rastro se actualiza en cada acción del jugador (Apéndice B).

**Replay y modo offline (persona 4)**
- **S18.** Un log solo se reproduce si la fuente tiene las mismas versiones de cripta y
  catálogo. Si no, se informa y no se reproduce. Para un log viejo se usa `--offline` con una
  copia de los datos de esas versiones.
- **S19.** `datos_offline/` usa un formato propio mientras el curso publica su paquete. Cuando
  lo publique, solo cambia `FuenteOffline` (o se convierte el paquete).

---

## 6. Cómo verificar el bloque 2

Desde la carpeta `cripta/`:

```
python -m unittest discover -s tests -t .                     # 387 pruebas (300 del bloque 2)
python -m benchmark.bench_frecuencia_bloque2                  # frecuencias de las secciones 4.2 a 4.4
python -m tools.simular_partida_bloque2 --borrar-cache        # recorrido contra el API real, en frío
python -m tools.simular_partida_bloque2                       # otra vez: arranque en caliente
python -m tools.simular_partida_bloque2 --offline datos_offline
python -m tools.ejecutar_verificaciones                       # pruebas + benchmarks a un archivo
```
