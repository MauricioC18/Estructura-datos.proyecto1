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

- **Decisión**: seguir el mismo supuesto del cazador (grafo sin dirección), dejarlo como riesgo y coordinarlo con Carlos.
- **Motivo**: el traductor empareja cada salida con la de vuelta (`repository/traductor.py:183-206`) y, si no la hay, la puerta solo aparece en la sala que la declara. Se revisó `datos_offline/criptas/cripta-01`: 6 salas, 10 salidas, todas con vuelta. No hay evidencia de pasos de un solo sentido, pero el formato no los prohíbe.
- **Alternativas**: un proveedor de salidas entrantes para expandir la búsqueda y otro de salidas para el primer paso. Es correcta en cualquier caso, pero obliga a cambiar la interfaz de `RutasMasBaratas`, que es de Carlos, y a construir las salidas entrantes al iniciar. Queda como la corrección a aplicar si se confirma que existen.

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
- **Alternativas**: (a) Fijar un tamaño a partir de la cripta publicada más grande. Descartada: nombra un dato concreto y no es la condición de §6.1. (b) Medir solo sintéticas. Descartada: no comprueba FR-036 sobre la cripta que el enunciado indica.
