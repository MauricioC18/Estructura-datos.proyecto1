"""
Mediciones de inventario, historial reversible, rastro, bitacora y ordenamiento.

Expone run(), que devuelve una lista de Measurement como los demas benchmarks,
para el ejecutor de --bench. Tambien se corre suelto desde cripta/:

    python -m benchmark.persona3_bench

Cada medicion se repite y se toma la mejor, para reducir el ruido del sistema.
Las alternativas descartadas del Documento de Decisiones se miden aqui mismo,
como pide §8: list.pop(i) para soltar, list.pop(0) para la bitacora y cada
algoritmo de ordenamiento por separado.
"""
import random
import time

from benchmark.utilidades_medicion import Measurement, calentar_procesador, descripcion_del_equipo
from model.event import Event
from model.game_state import GameState
from model.item import Item
from model.room import Door, Exit, Room
from structures.circular_log import CircularLog
from structures.history import History, ReversibleEventQueue
from structures.inventory import DoublyLinkedList, Inventory, _Node
from structures.sorting import (
    ComparisonCounter,
    algorithm_for,
    insertion_sort,
    merge_sort,
    sort,
)
from structures.trail import PlayerTrail

SEED = 2026
REPETITIONS = 5


def _best(function, repetitions=REPETITIONS):
    best = None
    for _ in range(repetitions):
        start = time.perf_counter()
        function()
        elapsed = time.perf_counter() - start
        if best is None or elapsed < best:
            best = elapsed
    return best


def _item(index, generator):
    return Item(
        instance_id=f"o-{index}",
        type_id=f"itm_{index}",
        name=f"objeto {generator.randint(0, 10**6)}",
        item_class=Item.POTION,
        weight=generator.randint(1, 20),
        value=generator.randint(1, 100),
    )


def bench_log(messages=100_000):
    def circular():
        log = CircularLog()
        for _ in range(messages):
            log.append("m")

    def shifting_list():
        log = []
        for _ in range(messages):
            log.append("m")
            if len(log) > 20:
                log.pop(0)

    detail = f"{messages:,} mensajes, se conservan 20"
    return [
        Measurement("Bitacora: buffer circular", _best(circular) / messages, detail + ", s por mensaje"),
        Measurement("Bitacora: list + pop(0) [descartada]", _best(shifting_list) / messages, detail + ", s por mensaje"),
    ]


def bench_drop_by_position(sizes=(10, 100, 1_000, 10_000), samples=200):
    measurements = []

    for size in sizes:
        for label, fraction in (("inicio", 0.0), ("medio", 0.5), ("final", 1.0)):
            position = min(size - 1, int(size * fraction))
            linked = None
            plain = None

            for _ in range(samples):
                items = DoublyLinkedList()
                nodes = [_Node(index) for index in range(size)]
                for node in nodes:
                    items.append(node)
                start = time.perf_counter()
                items.remove(nodes[position])
                elapsed = time.perf_counter() - start
                linked = elapsed if linked is None or elapsed < linked else linked

                values = list(range(size))
                start = time.perf_counter()
                values.pop(position)
                elapsed = time.perf_counter() - start
                plain = elapsed if plain is None or elapsed < plain else plain

            detail = f"n={size}, posicion {label}"
            measurements.append(Measurement("Soltar: lista doble", linked, detail))
            measurements.append(Measurement("Soltar: list.pop(i) [descartada]", plain, detail))

    return measurements


def bench_inventory(capacity=50, steps=20_000):
    generator = random.Random(SEED)
    items = [_item(index, generator) for index in range(capacity)]

    def walk():
        inventory = Inventory(capacity)
        for item in items:
            inventory.pick_up(item)
        for _ in range(steps):
            if not inventory.next():
                inventory.go_to_start()

    def views():
        inventory = Inventory(capacity)
        for item in items:
            inventory.pick_up(item)
        for criterion in ("peso", "valor", "nombre"):
            inventory.sorted_view(criterion)

    return [
        Measurement("Inventario: avanzar el cursor", _best(walk) / steps, f"{capacity} objetos, s por paso"),
        Measurement("Inventario: vista ordenada", _best(views) / 3, f"{capacity} objetos, s por vista"),
    ]


def _pattern(name, size, generator):
    if name == "aleatorio":
        return [generator.randint(0, size) for _ in range(size)]
    if name == "casi ordenado":
        data = list(range(size))
        for _ in range(max(1, size // 100)):
            first = generator.randrange(size)
            second = generator.randrange(size)
            data[first], data[second] = data[second], data[first]
        return data
    if name == "invertido":
        return list(range(size, 0, -1))
    if name == "rotado":
        half = size // 2
        return list(range(half, size)) + list(range(half))
    if name == "cadenas largas":
        prefix = "x" * 200
        return [prefix + str(generator.randint(0, size)) for _ in range(size)]
    raise ValueError(name)


def bench_sorting(sizes=(4, 8, 16, 32, 64, 128, 256, 1_024, 4_096)):
    generator = random.Random(SEED)
    measurements = []
    algorithms = (("insercion", insertion_sort), ("mezcla", merge_sort), ("automatico", sort))

    for pattern in ("aleatorio", "casi ordenado", "invertido", "rotado", "cadenas largas"):
        for size in sizes:
            data = _pattern(pattern, size, generator)
            chosen = algorithm_for(data)

            for label, algorithm in algorithms:
                if label == "insercion" and size > 1_024 and pattern != "casi ordenado":
                    continue

                counter = ComparisonCounter()
                algorithm(data, counter=counter)
                detail = f"{pattern}, n={size}, {counter.comparisons} comparaciones"
                if label == "automatico":
                    detail += f", escogio {chosen}"

                measurements.append(
                    Measurement(f"Ordenamiento: {label}", _best(lambda: algorithm(data), 3), detail)
                )

    return measurements


def bench_trail(trackers=(1, 10, 100, 1_000)):
    generator = random.Random(SEED)
    measurements = []

    for count in trackers:
        trail = PlayerTrail()
        rooms = []
        for index in range(count):
            room = Room(index, "sala")
            for direction in ("N", "S", "E", "O")[: generator.randint(1, 4)]:
                destination = generator.randint(1, 500)
                room.add_exit(Exit(direction, destination, Door(index, destination)))
                trail.mark(destination, generator.randint(0, 1_000))
            rooms.append(room)

        def decide():
            for room in rooms:
                trail.freshest_exit(room, 1_000)

        measurements.append(
            Measurement("Rastro: decision de rastreadores", _best(decide) / count, f"{count} rastreadores, s por decision")
        )

    return measurements


class _Target:
    def __init__(self):
        self.health = 100


def bench_history(changes_per_action=(1, 10, 100, 1_000)):
    measurements = []

    for count in changes_per_action:
        targets = [_Target() for _ in range(count)]

        def record_and_undo():
            history = History(GameState(seed=SEED))
            for _ in range(5):
                history.begin_action()
                for target in targets:
                    history.assign(target, "health", target.health - 1)
            for _ in range(5):
                history.undo()

        measurements.append(
            Measurement(
                "Historial: 5 acciones, anotar y deshacer",
                _best(record_and_undo) / 5,
                f"{count} cambios por accion, s por accion",
            )
        )

    return measurements


def bench_reversible_queue(pending=300, cycles=20_000):
    """Costo de anotar la agenda, comparado con la misma carga sin anotar."""
    from structures.event_queue import EventQueue

    def load(queue, state):
        generator = random.Random(SEED)
        for _ in range(pending):
            queue.push(Event(generator.randint(0, 1_000), state.next_sequence(), "x"))
        for _ in range(cycles):
            event = queue.pop()
            queue.push(Event(event.time + generator.randint(1, 200), state.next_sequence(), "x"))

    def plain():
        load(EventQueue(), GameState(seed=SEED))

    def reversible():
        state = GameState(seed=SEED)
        history = History(state)
        queue = ReversibleEventQueue(history)
        history.begin_action()
        load(queue, state)

    detail = f"{pending} eventos, {cycles:,} extracciones"
    return [
        Measurement("Agenda: EventQueue", _best(plain, 3), detail),
        Measurement("Agenda: ReversibleEventQueue", _best(reversible, 3), detail + ", anotando cada cambio"),
    ]


def run():
    calentar_procesador()
    measurements = []
    for bench in (
        bench_log,
        bench_drop_by_position,
        bench_inventory,
        bench_sorting,
        bench_trail,
        bench_history,
        bench_reversible_queue,
    ):
        measurements.extend(bench())
    return measurements


def main():
    print(descripcion_del_equipo())
    for measurement in run():
        seconds = "-" if measurement.seconds is None else f"{measurement.seconds:.3e} s"
        print(f"{measurement.name:<45} {seconds:>14}  {measurement.detail}")


if __name__ == "__main__":
    main()
