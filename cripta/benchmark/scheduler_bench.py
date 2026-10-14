"""Mediciones de la agenda de eventos y del ciclo del motor.

Responde a dos exigencias del enunciado:

- La seccion 8 pide que al menos una seccion del Documento de Decisiones mida
  directamente la alternativa descartada. Aqui se mide la lista sin ordenar
  frente al monticulo binario minimo.
- La seccion 5.2 fija un presupuesto de 20 ms para resolver un ciclo completo de
  eventos entre dos decisiones consecutivas del jugador.

Se ejecuta con `python -m benchmark.scheduler_bench` desde `cripta/`.
"""

import random
import time
from dataclasses import dataclass

from model.enemy import Enemy
from model.event import Event
from model.game import Game
from model.game_state import GameState
from model.player import Player
from structures.event_queue import EventQueue


PENDING_EVENTS = 300
CYCLES = 50_000
PLAYER_DECISIONS = 2_000
ENEMIES_PER_ROOM = 20
SEED = 2026


@dataclass
class Measurement:
    name: str
    seconds: float
    detail: str


class UnsortedEventList:
    """Alternativa descartada en la seccion 4.1.

    Insertar cuesta O(1) y extraer el minimo obliga a examinar todos los eventos
    pendientes. Se implementa solo para medirla; el motor no la usa.
    """

    def __init__(self):
        self._events = []

    def __len__(self):
        return len(self._events)

    def is_empty(self):
        return len(self._events) == 0

    def push(self, event):
        self._events.append(event)

    def pop(self):
        if not self._events:
            return None

        best = 0

        for position in range(1, len(self._events)):
            candidate = self._events[position]
            current = self._events[best]

            if candidate.time < current.time or (
                candidate.time == current.time
                and candidate.sequence < current.sequence
            ):
                best = position

        self._events[best], self._events[-1] = (
            self._events[-1],
            self._events[best],
        )

        return self._events.pop()


def measure_agenda(agenda, pending_events, cycles, seed):
    """Llena la agenda y repite el patron que ejecuta el motor: sacar y meter.

    El motor extrae el evento mas proximo y, al ejecutarlo, programa el
    siguiente, de modo que el tamano de la agenda se mantiene estable.
    """
    generator = random.Random(seed)
    sequence = 0

    for _ in range(pending_events):
        agenda.push(Event(generator.randrange(0, 1000), sequence, "actor_action"))
        sequence += 1

    start = time.perf_counter()

    for _ in range(cycles):
        event = agenda.pop()
        agenda.push(
            Event(event.time + generator.randrange(1, 200), sequence, "actor_action")
        )
        sequence += 1

    return time.perf_counter() - start


def measure_event_cycle(decisions, enemies_per_room, seed):
    """Tiempo por ciclo completo de eventos entre dos decisiones del jugador.

    Excluye red y renderizado, como indica la seccion 5.2. Para que cada ciclo
    tenga trabajo real, los enemigos son mas rapidos que el jugador y hay varios
    efectos temporales en curso.
    """
    player = Player("p-1", "Heroe", 10_000_000, 6, 100, 100, 1)
    enemies = [
        Enemy(
            f"e-{index:04}",
            "Rata gigante",
            1_000_000,
            5,
            1,
            250,
            1,
            Enemy.GUARDIAN,
            regeneration=1,
        )
        for index in range(enemies_per_room)
    ]

    game = Game(GameState(seed=seed), player, enemies)
    game.apply_poison(player, 1)
    game.light_torch(10_000_000)

    start = time.perf_counter()

    for _ in range(decisions):
        game.wait()

    elapsed = time.perf_counter() - start

    return elapsed, game


def report(title, measurements):
    print(title)

    for measurement in measurements:
        print(f"  {measurement.name:<34} {measurement.seconds:>9.4f} s   {measurement.detail}")

    print()


def run():
    """Devuelve las mediciones de este modulo, para el ejecutor de --bench."""
    heap_seconds = measure_agenda(EventQueue(), PENDING_EVENTS, CYCLES, SEED)
    list_seconds = measure_agenda(
        UnsortedEventList(), PENDING_EVENTS, CYCLES, SEED
    )
    cycle_seconds, game = measure_event_cycle(
        PLAYER_DECISIONS, ENEMIES_PER_ROOM, SEED
    )

    per_cycle_ms = cycle_seconds / PLAYER_DECISIONS * 1000

    return [
        Measurement(
            "Agenda: monticulo binario minimo",
            heap_seconds,
            f"{PENDING_EVENTS} eventos, {CYCLES:,} extracciones",
        ),
        Measurement(
            "Agenda: lista sin ordenar",
            list_seconds,
            f"{PENDING_EVENTS} eventos, {CYCLES:,} extracciones",
        ),
        Measurement(
            "Ciclo de eventos del motor",
            cycle_seconds,
            f"{PLAYER_DECISIONS:,} decisiones, {per_cycle_ms:.4f} ms por ciclo",
        ),
    ]


def main():
    print(f"Python {__import__('sys').version.split()[0]}\n")

    measurements = run()
    report("Mediciones", measurements)

    heap, unsorted_list, cycle = measurements

    print(f"El monticulo es {unsorted_list.seconds / heap.seconds:.1f} veces mas")
    print("rapido que la lista sin ordenar en esta carga.")
    print()

    per_cycle_ms = cycle.seconds / PLAYER_DECISIONS * 1000
    budget = "cumple" if per_cycle_ms < 20 else "NO cumple"
    print(f"Ciclo de eventos: {per_cycle_ms:.4f} ms, {budget} el limite de 20 ms.")


if __name__ == "__main__":
    main()
