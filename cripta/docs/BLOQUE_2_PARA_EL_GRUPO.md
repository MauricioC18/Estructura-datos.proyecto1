# Bloque 2 — API, caché y persistencia: guía para el grupo

Responsable: Mauricio (persona 2). Última actualización: 14 de octubre de 2026.

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
| **Punto de entrada para el controlador** | `repository/repositorio_cripta.py` | Listo |
| `Traductor` (JSON → objetos del modelo) | — | **Pendiente: necesita las clases de la persona 1** |

Pruebas: 216 del bloque 2; con las del resto del grupo son 303 y todas pasan
(`python -m unittest discover -s tests -t .` desde `cripta/`). Conexión real con el API
verificada. Las mediciones están en `docs/mediciones/bloque2/`.

Todo el código del bloque 2 vive dentro de las carpetas que define `docs/ARQUITECTURA.md`
(`adapters/`, `structures/`, `benchmark/`, `tests/`), más dos carpetas nuevas: `repository/` y
`tools/`. Los nombres de archivos, clases y métodos están en español; la convención de nombres
sigue entre las decisiones pendientes del grupo (ARQUITECTURA, sección 9).

Presupuesto medido con cripta-01 (presupuesto 9):
- arranque en frío: **7 solicitudes** (lista, datos generales, versión del catálogo, 1 página,
  1 lote de contenido con las 6 salas, 2 lotes de catálogo con las 11 fichas);
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

# Antes de confirmar que el jugador entra a una sala (§2.5):
try:
    entrada = repositorio.preparar_entrada_a_sala(id_destino)
except PresupuestoAgotado:
    ...  # rechazar el movimiento SIN consumir tiempo virtual (supuesto S1)

# Después de cada acción del jugador (precarga contenido y fichas):
repositorio.despues_de_accion(id_sala_actual)

# Cuando un enemigo muere y suelta objetos:
repositorio.asegurar_fichas(ids_de_los_objetos)

# Datos que va a necesitar el Traductor / el modelo:
repositorio.sala_del_esqueleto(id_sala)   # la sala con sus salidas (JSON del API)
repositorio.contenido_de_sala(id_sala)    # enemigos, objetos y trampas (JSON del API)
repositorio.obtener_ficha(id_tipo)        # ficha del catálogo (JSON del API); nunca usa la red
repositorio.vecinos_de_sala(id_sala)      # ids vecinos en orden N, S, E, O

# Al terminar (§5.1):
for linea in repositorio.reporte_de_red().lineas_de_texto():
    print(linea)
```

### La función `consultar_ids_en_uso`

La caché no puede liberar una ficha "en uso" (§4.4). El controlador le entrega al repositorio
una función sin argumentos que devuelve una `TablaHash` con los **ids de tipo** en uso:

- tipos de los enemigos vivos (persona 1);
- tipos de los objetos del inventario (persona 3);
- tipos de los objetos y trampas del suelo de la sala actual (persona 1).

```python
from structures.tabla_hash import TablaHash

def consultar_ids_en_uso():
    en_uso = TablaHash()
    for tipo in tipos_en_uso_del_modelo():   # lo arma el controlador con datos del modelo
        en_uso.insertar(tipo, True)
    return en_uso
```

Solo se llama cuando la caché necesita liberar algo, que es poco frecuente.

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
`benchmark.bench_tabla_hash`, `benchmark.bench_cache_catalogo`, `benchmark.bench_almacen_fichas`
y `benchmark.bench_precarga_contenido`.

### Errores que el controlador debe atrapar

| Error | Módulo | Qué hacer |
|---|---|---|
| `PresupuestoAgotado` | `adapters.fuente_datos` | Rechazar la acción sin consumir tiempo y avisar |
| `ErrorFuenteDatos` | `adapters.fuente_datos` | Mostrar el mensaje (ya dice qué operación falló) |
| `VersionesIncompatibles` | `repository.repositorio_cripta` | En `--replay`: mostrar el mensaje y no reproducir |
| `FichaNoDisponible`, `ContenidoNoDisponible` | `repository.gestor_*` | Error de datos del API o de uso; mostrar el mensaje |

---

## 3. Lo que el bloque 2 necesita de cada integrante

### Persona 1 (motor)
1. **Las clases que faltan del modelo**: sala y puerta/salida (`model/room.py`), objeto en el
   suelo y trampa. `Player` y `Enemy` ya existen, así que la parte del `Traductor` que crea al
   jugador y a los enemigos ya se puede escribir; el resto espera esas clases.
2. **Los tipos en uso del motor**: enemigos vivos y objetos y trampas del suelo de la sala actual.
3. Revisar los supuestos S9 a S15 (sección 5), que afectan al motor. El mecanismo para
   rechazar una acción sin consumir tiempo ya existe (`ActionResult`); cuando exista `move()`,
   deberá usarlo si el repositorio lanza `PresupuestoAgotado` (S1).
4. Tres detalles del modelo actual frente a los datos reales del API:
   - `Enemy.GUARDIAN` vale `"guardian"`, pero el API envía `"guardián"` con tilde (verificado
     en el esquema del API y en los datos de `cripta-01`). Si `decide_action()` compara con esa
     constante, un guardián real no se reconocería. `"errante"` y `"rastreador"` coinciden.
   - `Enemy` acepta `regeneration`, pero las fichas del API no traen ningún campo de
     regeneración (S13): con los datos actuales siempre será 0.
   - `Player` usa `attack_bonus` y `defense_bonus`; el API envía `ataque_bonus` y
     `defensa_bonus`. El `Traductor` hará esa conversión, así que no hay que cambiar `Player`.

### Persona 3 (inventario, retroceso, rastro, ordenamientos)
1. **Los tipos de los objetos del inventario**, porque esas fichas también están en uso.
2. Coordinar §4.9: el enunciado menciona "listas auxiliares del catálogo" entre los contextos
   de ordenamiento. Hoy el índice de fichas se mantiene ordenado insertando cada id en su
   lugar, sin llamar a un algoritmo de ordenamiento. Hay que decidir si ese contexto lo cubre
   su módulo o basta con los otros.
3. Usar `TablaHash` para cualquier búsqueda por clave (`dict` está prohibido, §7).
4. Recordar que **la caché no entra en el retroceso** (§2.11) y revisar S16 y S17.

### Persona 4 (MVC, interfaz, replay, bench)
1. Integrar `RepositorioCripta` como muestra la sección 2.
2. Pasar `--offline` y `--cache-size`, y armar `consultar_ids_en_uso` con lo que entreguen
   las personas 1 y 3.
3. Usar `versiones_de_la_partida()` y `versiones_requeridas` en `--replay`.
4. Incluir en `--bench` el `run()` de los cuatro benchmarks del bloque 2.

---

## 4. Contrato de datos (lo que entrega el API)

El repositorio entrega el JSON del API tal cual. El `Traductor` lo convertirá en objetos del
modelo aplicando estos valores por defecto. Los campos marcados "puede faltar" pueden no venir
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

**Fichas del catálogo** (todas traen `id`, `nombre`, `clase`):

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
  activarlos. El antídoto se consume aunque no haya veneno activo.
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
python -m unittest discover -s tests -t .                     # 303 pruebas (216 del bloque 2)
python -m tools.simular_partida_bloque2 --borrar-cache        # recorrido contra el API real, en frío
python -m tools.simular_partida_bloque2                       # otra vez: arranque en caliente
python -m tools.simular_partida_bloque2 --offline datos_offline
python -m tools.ejecutar_verificaciones                       # pruebas + benchmarks a un archivo
```
