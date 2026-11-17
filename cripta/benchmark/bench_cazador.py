"""
Mediciones de la persecución del cazador (§5.1 y §5.2 del enunciado).

Qué se mide y por qué
    1. Rango fijo y pequeño en criptas de tamaño creciente. §5.1 exige que la
       decisión de un cazador de rango pequeño no cueste proporcionalmente al
       tamaño de la cripta, sino a la región dentro de su rango. Lo que se
       quiere ver es que el tiempo se aplane cuando la cripta crece.
    2. Cantidad creciente de cazadores persiguiendo al mismo jugador, con el
       cálculo compartido y con un cálculo por cazador. §5.1 pide medir cuál
       conviene y bajo qué condiciones cambia la respuesta. Incluye un caso de
       rangos muy desiguales, porque el corte compartido es el rango mayor y
       el cazador de rango pequeño paga por una región que no le interesa:
       FR-017 obliga a reportar ese sobrecosto.
    3. Puertas que cambian mucho y puertas que casi nunca cambian, con el
       cálculo compartido y recalculando siempre desde cero. §5.2 pide las dos
       criptas y pide medir la alternativa de recalcular siempre.
    4. El ciclo completo de eventos entre dos decisiones del jugador con 50
       cazadores activos, contra el límite de 20 ms (FR-018, SC-006).

Las tres alternativas del plan
    El programa usa el cálculo compartido con invalidación. Las otras dos,
    una búsqueda por cazador y recalcular siempre, se implementan aquí porque
    el principio VI de la constitución pide medir la alternativa descartada:
    sin ese contraste la decisión no está defendida.

Las criptas sintéticas son deterministas por semilla, como exige la
constitución. El reparto de costos es por posición, no al azar.
"""
import time

from benchmark.scheduler_bench import build_synthetic_crypt
from benchmark.utilidades_medicion import Measurement, calentar_procesador
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.player import Player
from structures.rutas_mas_baratas import RutasMasBaratas


SEED = 2026
HUNTER_SPEED = 120


def make_player(room_id=1, speed=100):
    return Player(
        actor_id="p-1",
        name="Heroe",
        max_health=10 ** 9,
        attack=6,
        defense=10 ** 6,
        speed=speed,
        room_id=room_id,
    )


def make_hunter(number, room_id, pursuit_range):
    return Enemy(
        actor_id=f"c-{number}",
        name=f"Sabueso {number}",
        max_health=18,
        attack=1,
        defense=2,
        speed=HUNTER_SPEED,
        room_id=room_id,
        behavior=Enemy.HUNTER,
        pursuit_range=pursuit_range,
    )


def build_chase(room_count, hunter_count, pursuit_ranges, always_recompute=False,
                auto_close=400, seed=SEED):
    """Partida con cazadores repartidos por la cripta, todos ya despiertos.

    pursuit_ranges se recorre en ciclo, de modo que una sola tupla da todos
    los cazadores con el mismo rango y una tupla de varios valores da rangos
    desiguales.
    """
    room_map = build_synthetic_crypt(room_count, auto_close=auto_close)
    hunters = []

    for number in range(hunter_count):
        room_id = room_count - (number % max(1, room_count - 1))
        hunters.append(
            make_hunter(
                number,
                max(2, room_id),
                pursuit_ranges[number % len(pursuit_ranges)],
            )
        )

    game = Game(
        GameState(seed=seed),
        make_player(),
        hunters,
        room_map=room_map,
        always_recompute_routes=always_recompute,
    )

    for hunter in hunters:
        game._activate_enemies_in(hunter.room_id)

    return game, hunters


def open_exits_of(room_map):
    def vecinas(room_id):
        neighbours = []

        for exit_ in room_map.room(room_id).exits():
            if exit_.door.is_open:
                neighbours.append((exit_.destination, exit_.cost, exit_))

        return neighbours

    return vecinas


# ----------------------------------------------------------------------
# 1. Rango pequeno en cripta grande (FR-017, SC-005)
# ----------------------------------------------------------------------

def measure_cut_by_range(room_count, pursuit_range, repetitions, seed=SEED):
    """Una decision aislada, para que solo se mida la busqueda.

    La cripta va sin puertas cerradas a proposito: con una cerrada de cada
    tres, la region alcanzable desde la sala del jugador es de dos o tres
    salas por grande que sea la cripta, y la medicion no mostraria el efecto
    del corte sino el del bloqueo.
    """
    room_map = build_synthetic_crypt(room_count, closed_every=0)
    vecinas = open_exits_of(room_map)
    hunter_room = room_count

    start = time.perf_counter()

    for _ in range(repetitions):
        routes = RutasMasBaratas(vecinas, 1, pursuit_range)
        routes.primer_paso_desde(hunter_room)

    return time.perf_counter() - start


# ----------------------------------------------------------------------
# 2. Compartido frente a uno por cazador (SC-008)
# ----------------------------------------------------------------------

def measure_shared(room_count, hunter_count, pursuit_ranges, decisions, seed=SEED):
    """Una sola busqueda desde el jugador sirve a todos los cazadores."""
    room_map = build_synthetic_crypt(room_count, closed_every=0)
    vecinas = open_exits_of(room_map)
    hunter_rooms = [
        max(2, room_count - (number % max(1, room_count - 1)))
        for number in range(hunter_count)
    ]
    cut = max(pursuit_ranges)

    start = time.perf_counter()

    for _ in range(decisions):
        routes = RutasMasBaratas(vecinas, 1, cut)

        for room_id in hunter_rooms:
            routes.primer_paso_desde(room_id)

    return time.perf_counter() - start


def measure_per_hunter(room_count, hunter_count, pursuit_ranges, decisions,
                       seed=SEED):
    """Una busqueda por cazador, cortada en su propio rango."""
    room_map = build_synthetic_crypt(room_count, closed_every=0)
    vecinas = open_exits_of(room_map)
    hunters = [
        (
            max(2, room_count - (number % max(1, room_count - 1))),
            pursuit_ranges[number % len(pursuit_ranges)],
        )
        for number in range(hunter_count)
    ]

    start = time.perf_counter()

    for _ in range(decisions):
        for room_id, pursuit_range in hunters:
            routes = RutasMasBaratas(vecinas, 1, pursuit_range)
            routes.primer_paso_desde(room_id)

    return time.perf_counter() - start


# ----------------------------------------------------------------------
# 3. Puertas que cambian mucho y puertas que casi nunca cambian (SC-007)
# ----------------------------------------------------------------------

def walk_opening_doors(game, decisions):
    """Camina abriendo lo que encuentre cerrado, para que las puertas cambien."""
    direction = "N"

    while game.player_actions < decisions and not game.is_over:
        if game.move(direction).accepted:
            continue

        if game.open_door(direction).accepted:
            continue

        direction = "S" if direction == "N" else "N"

        if not game.wait().accepted:
            return


def measure_door_churn(room_count, hunter_count, pursuit_range, decisions,
                       auto_close, always_recompute, seed=SEED):
    game, _ = build_chase(
        room_count,
        hunter_count,
        (pursuit_range,),
        always_recompute=always_recompute,
        auto_close=auto_close,
        seed=seed,
    )

    start = time.perf_counter()
    walk_opening_doors(game, decisions)
    seconds = time.perf_counter() - start

    return seconds, game


# ----------------------------------------------------------------------
# 4. El ciclo de eventos con cazadores (FR-018, SC-006)
# ----------------------------------------------------------------------

def measure_event_cycle_with_hunters(room_count, hunter_count, pursuit_range,
                                     decisions, seed=SEED):
    game, _ = build_chase(room_count, hunter_count, (pursuit_range,), seed=seed)

    start = time.perf_counter()

    for _ in range(decisions):
        if game.is_over:
            break
        game.wait()

    return time.perf_counter() - start, game


# La cripta de referencia publicada es cripta-06: 300 salas y 36 cazadores.
# Las mediciones usan esa escala, y no la de las criptas de prueba.
ROOMS = 300
HUNTERS = 36
SMALL_RANGE = 300
WIDE_RANGE = 10 ** 6
DECISIONS = 300
RANGE_REPETITIONS = 400


def run():
    """Devuelve las mediciones de este modulo, para el ejecutor de --bench."""
    calentar_procesador(0.3)

    measurements = []

    # 1. El corte por rango frente al tamano de la cripta.
    for room_count in (60, 300, 1200):
        seconds = measure_cut_by_range(room_count, SMALL_RANGE, RANGE_REPETITIONS)
        measurements.append(
            Measurement(
                f"Decision con rango {SMALL_RANGE} en cripta de {room_count} salas",
                seconds,
                f"{RANGE_REPETITIONS} decisiones, "
                f"{seconds / RANGE_REPETITIONS * 1000:.4f} ms por decision",
            )
        )

    # Sin corte, para ver cuanto ahorra el rango.
    seconds = measure_cut_by_range(1200, WIDE_RANGE, RANGE_REPETITIONS)
    measurements.append(
        Measurement(
            "Decision sin corte efectivo en cripta de 1200 salas",
            seconds,
            f"{RANGE_REPETITIONS} decisiones, "
            f"{seconds / RANGE_REPETITIONS * 1000:.4f} ms por decision",
        )
    )

    # 2. Compartido frente a uno por cazador, con rangos iguales y desiguales.
    for etiqueta, rangos in (
        ("rangos iguales", (SMALL_RANGE,)),
        ("rangos desiguales", (SMALL_RANGE, WIDE_RANGE)),
    ):
        compartido = measure_shared(ROOMS, HUNTERS, rangos, DECISIONS)
        por_cazador = measure_per_hunter(ROOMS, HUNTERS, rangos, DECISIONS)
        measurements.append(
            Measurement(
                f"{HUNTERS} cazadores, calculo compartido ({etiqueta})",
                compartido,
                f"{DECISIONS} instantes, "
                f"{compartido / DECISIONS * 1000:.4f} ms por instante",
            )
        )
        measurements.append(
            Measurement(
                f"{HUNTERS} cazadores, un calculo por cazador ({etiqueta})",
                por_cazador,
                f"{DECISIONS} instantes, "
                f"{por_cazador / DECISIONS * 1000:.4f} ms por instante",
            )
        )

    # 3. Puertas que cambian mucho y puertas que casi no cambian.
    for etiqueta, auto_close in (("puertas que cambian mucho", 150),
                                 ("puertas que casi no cambian", 10 ** 7)):
        for modo, siempre in (("compartido", False), ("recalcular siempre", True)):
            seconds, game = measure_door_churn(
                ROOMS, 10, WIDE_RANGE, DECISIONS, auto_close, siempre
            )
            measurements.append(
                Measurement(
                    f"10 cazadores, {etiqueta}, {modo}",
                    seconds,
                    f"{game.player_actions} decisiones, "
                    f"{game.route_searches} busquedas",
                )
            )

    # 4. El ciclo completo con 50 cazadores.
    seconds, game = measure_event_cycle_with_hunters(
        ROOMS, HUNTERS, WIDE_RANGE, DECISIONS
    )
    por_ciclo = seconds / max(1, game.player_actions) * 1000
    measurements.append(
        Measurement(
            f"Ciclo de eventos con {HUNTERS} cazadores activos",
            seconds,
            f"{game.player_actions} decisiones, {por_ciclo:.4f} ms por ciclo, "
            f"{por_ciclo / 20 * 100:.2f}% del limite de 20 ms",
        )
    )

    return measurements


def main():
    print(f"Python {__import__('sys').version.split()[0]}\n")

    for measurement in run():
        if measurement.seconds is None:
            print(f"{measurement.name}: {measurement.detail}")
        else:
            print(f"{measurement.name}: {measurement.seconds:.4f} s  ({measurement.detail})")


if __name__ == "__main__":
    main()
