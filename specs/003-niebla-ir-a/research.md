# Investigación: Niebla de guerra y viaje automático «ir a»

**Plan**: [plan.md](./plan.md) | **Fecha**: 2026-11-16

Cada punto sigue el formato Decisión / Motivo / Alternativas. Las tablas completas de alternativas están en el plan. Aquí queda lo que se revisó en el código para tomar cada decisión.

## 1. Qué estructuras propias existen y sirven

- **Decisión**: reutilizar `TablaHash`, el historial reversible y `RutasMasBaratas`; agregar solo el mapa conocido.
- **Motivo**: la constitución (principio I) pide reutilizar y justificar cuando no se hace. Revisado:
  - `structures/tabla_hash.py`: `insertar`, `obtener`, `contiene`, `eliminar`, `claves`. Solo admite claves `int` y `str` (`structures/funciones_hash.py`, `hash_crc32`); cualquier otro tipo da `TypeError`.
  - `structures/history.py`: `record(change)` guarda una anotación solo mientras hay un intervalo abierto y no se está deshaciendo (`is_recording`). `CallbackChange(función, *args)` ejecuta la inversa al deshacer.
  - `structures/trail.py:47-53`: el patrón exacto de «si la clave existía, anotar reinsertar el valor anterior; si no, anotar eliminar».
  - `structures/rutas_mas_baratas.py`: recibe `vecinas_abiertas(sala) -> (id, costo, referencia)`, un origen y un corte opcional. `primer_paso_desde(sala)` aplica el desempate de menor id y, entre dos salidas a la misma vecina, la más barata.
- **Alternativas**: escribir estructuras nuevas para cada cosa. Descartada por la constitución.

## 2. Si el conocimiento puede leer el mapa de salas

- **Decisión**: el mapa conocido guarda solo exploradas, contadores y puertas recordadas; el nombre, las salidas y los costos de una sala explorada se leen del mapa de salas al mostrarlos o al buscar.
- **Motivo**: FR-005 dice que el jugador conoce el nombre, las salidas y el costo de las salidas de una sala explorada, y ninguno de esos datos cambia durante la partida (`model/room.py`: `Room.name`, `Room.exits()` y `Door.cost` se fijan al armar el mapa). Lo único que cambia es el estado de las puertas, y ese se lee del recuerdo, nunca de `Door.closed`. FR-012 queda respetado: lo que se muestra se deriva del conocimiento.
- **Alternativas**: copiar nombre y salidas al explorar. Descartada: duplica datos inmutables y encarece explorar.

## 3. Pasos de un solo sentido

- **Decisión (revisada el 2026-11-17)**: expandir la búsqueda de «ir a» por las salidas conocidas que **entran** a cada sala y dar el primer paso por las que **salen**. El mapa conocido ofrece `entrantes_conocidas(u)`: filtra un índice de salidas entrantes, armado una vez en O(V + E) desde la topología, por sala de origen explorada y puerta recordada abierta (clave `w × 4 + dirección` del lado de origen). Ver plan, alternativa 9.
- **Motivo**: el grupo confirmó que el servicio puede publicar salidas de un solo sentido (el contrato describe cada salida como dirigida y no exige la vuelta), y la especificación lo recoge en los escenarios 7 y 8 de la Historia 4. Con ellas, buscar desde el destino por las salidas que salen calcula la distancia en el sentido contrario: con 1→3, 3→2 y 2→1, todas de costo 1, el jugador en 1 queda sin ruta hacia 3 teniendo una salida directa. Carlos ya cambió el cazador de la misma manera y `RutasMasBaratas` ya acepta `salidas_de`.
- **Alternativas**: mantener el índice de entrantes conocidas al explorar (descartada: estado nuevo que explorar y revertir tendrían que actualizar, para ahorrar un filtro O(1) por salida); buscar desde el jugador por las salidas salientes (descartada: el origen cambia en cada paso y se pierde la reutilización de la ruta, y el desempate de FR-024 desde cada sala exigiría rehacer la búsqueda o escribir otra); reutilizar el índice del motor (descartada: es privado y filtra por el estado real de las puertas).
- **Pendiente de Carlos**: su `RutasMasBaratas` rechaza `parar_en` junto con `salidas_de`. El cableado en `model/viaje.py` espera a que lo levante.
- *Decisión original, del 2026-11-16*: seguir el supuesto del cazador (grafo sin dirección), porque en `cripta-01` las 10 salidas tienen vuelta y no había evidencia de pasos de un solo sentido.

## 4. Dónde se engancha el motor

- **Decisión**: dos avisos al mapa conocido, «el jugador entró a la sala X» y «una puerta cambió».
- **Motivo**: revisado `model/game.py`:
  - Inicio: `_begin_new_game` (`:159`) marca el rastro, programa al jugador y activa enemigos.
  - Movimiento: `move` (`:304-318`) cambia `player.room_id` con el historial, invalida rutas, activa enemigos, registra el mensaje, comprueba la victoria y dispara trampas. El aviso va después de cambiar la sala y antes de activar enemigos, para que la observación de puertas sea la del instante de entrada.
  - Puertas: solo `open_door` (`:354`) y `_close_door` (`:1050`) cambian `closed` con el historial. El retroceso las cambia por `AttributeChange` sin pasar por el motor, y eso es correcto: revertir no es observar.
  - Antorcha: `self.torch_lit` (`:147`), que ya es reversible (`light_torch` y `TORCH_END` lo cambian con el historial).
- **Alternativas**: que el mapa conocido revise, en cada vista, las puertas de la sala del jugador. Descartada: no detecta el cambio en el instante en que ocurre (aclaración del 2026-11-16 y FR-006), solo cuando se muestra, y eso cambia lo que vería una consulta histórica.

## 5. Cómo se detectan los motivos de parada

- **Decisión**: después de cada paso, el modelo decide con el estado de la partida y la vida del jugador antes del paso.
- **Motivo**:
  - (a) Llegada: la sala del jugador es el destino.
  - (b) Enemigos: algún enemigo **vivo** (FR-028 (b), corregido tras la revisión) está en la sala destino **en el instante de entrar**. Se pregunta justo antes del `move`, después de cargar el contenido de esa sala con el mismo método que usa `execute` (`_load_destination`, `game_controller.py:72`, que no hace nada si la sala ya está cargada), de modo que los dormidos ya están en `Game.enemies`. Entre la pregunta y la entrada no corre ningún evento, porque el movimiento ocurre en el instante de la decisión del jugador. `Game.enemies` conserva a los muertos con vida 0; por eso se filtra por `is_alive`, como `visible_state` (`game.py:593`). **No se evalúa después del ciclo**: así, un enemigo que llega sin atacar no detiene el viaje (caso borde de la especificación) y uno que estaba al entrar sí lo detiene aunque se vaya antes de la siguiente decisión.
  - (c) Daño: la vida bajó. Ver el riesgo del plan.
  - (d) Sin ruta: el siguiente cálculo no encuentra primer paso.
  - (e) Partida terminada: `Game.is_over`.
  - (f) Contenido no disponible: `GameController.execute` devuelve rechazo cuando falla la carga (`game_controller.py:91-95`), sin consumir tiempo.
- **Alternativas**: un contador de daño en el motor. Más robusto, pero es un cambio en el archivo de Carlos que hoy no hace falta.

## 6. La bitácora de reproducción

- **Decisión**: los pasos se registran como `mover` por el camino normal del controlador; la orden se escribe como comentario `#` antes del primer paso.
- **Motivo**: `read_replay_log` ya ignora las líneas vacías y las que empiezan con `#` (`replay/replay_log.py`), y la reproducción ejecuta solo acciones del modelo. Reproducir una partida con viajes es reproducir sus movimientos.
- **Alternativas**: registrar `ir a` como acción y volver a calcular la ruta al reproducir. Descartada: FR-031 pide registrar cada paso, y recalcular al reproducir haría depender la reproducción de que el cálculo no cambie entre versiones del programa.

## 7. Tamaño de las mediciones

- **Decisión**: dos fuentes. (1) Criptas sintéticas deterministas por semilla en tres tamaños crecientes de mapa conocido, generadas por el módulo de mediciones. (2) Los datos reales de cada cripta del paquete sin conexión, cargados con `FuenteOffline` (`cripta/adapters/fuente_offline.py`), lo que incluye la cripta de referencia en cuanto el paquete la contenga. No se escribe ningún tamaño ni id de cripta.
- **Motivo**: decisión del grupo tras la revisión de consistencia (hallazgos F5 e I1). Las sintéticas muestran la tendencia que piden FR-033 a FR-035 sin depender de datos externos. La cripta de referencia, ya publicada, es la condición literal de §6.1 para FR-036. Recorrer todas las criptas del paquete evita nombrar una en el código.
- **Alternativas (medición)**: (a) Fijar un tamaño a partir de la cripta publicada más grande. Descartada: nombra un dato concreto y no es la condición de §6.1. (b) Medir solo sintéticas. Descartada: no comprueba FR-036 sobre la cripta que el enunciado indica.

## 8. Por qué un paso de «ir a» pasa de 5 ms y qué se prueba

- **Decisión**: probar en orden (a) la clave de puerta calculada desde la salida, (b) la parada anticipada de la búsqueda en la sala del jugador y (c) reutilizar la ruta durante el viaje. Detalle en el plan, «Decisión revisada para FR-036».
- **Motivo**: medido con `--bench` el 2026-11-16 (resultados en el plan). Un experimento aparte separó los dos costos con la misma búsqueda sobre las mismas cuadrículas:
  - con las vecinas reales: 1.40 ms con 100 salas, 6.64 ms con 400 y 30.72 ms con 1600;
  - con las vecinas conocidas: 2.40, 11.22 y 51.17 ms;
  - solo pedir las vecinas conocidas de todas las salas: 1.24, 5.63 y 24.18 ms.

  O sea, la búsqueda misma ya supera los 5 ms en mapas medianos (de ahí la mejora b), y el proveedor de vecinas conocidas le suma un costo parecido, casi todo por buscar la dirección de cada puerta (de ahí la mejora a). Reutilizar la ruta (c) baja el promedio por paso pero no el primer paso, así que va última.
- **Alternativas**:
  - Escribir una búsqueda propia de «ir a» con parada. Descartada: duplicaría el desempate. El parámetro opcional deja al cazador igual.
  - Volver a la clave de texto. Descartada: no es única cuando dos salidas unen las mismas salas.
  - Cambiar FR-036. Descartada: repite el enunciado (§6.1).
