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
FREQUENCY_DECISIONS = 1_000
SEED = 2026


@dataclass
class Measurement:
    name: str
    seconds: float
    detail: str


class CountingEventQueue(EventQueue):
    """Agenda que lleva la cuenta de las operaciones que recibe.

    Existe para responder a la seccion 8 del enunciado, que pide indicar con
    que frecuencia medida se ejecuta cada operacion. Es una subclase y no una
    modificacion de EventQueue para no sumar contadores en el camino que el
    juego recorre decenas de miles de veces, que es justamente el que se mide.
    """

    def __init__(self):
        super().__init__()
        self.pushes = 0
        self.pops = 0
        self.cancels = 0
        self.discarded = 0
        self.max_size = 0

    def push(self, event):
        super().push(event)
        self.pushes += 1

        if len(self) > self.max_size:
            self.max_size = len(self)

    def pop(self):
        event = super().pop()

        if event is not None:
            self.pops += 1

        return event

    def cancel(self, event):
        if not event.cancelled:
            self.cancels += 1

        super().cancel(event)

    def _discard_cancelled_roots(self):
        before = len(self)
        super()._discard_cancelled_roots()
        self.discarded += before - len(self)


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


def measure_operation_frequency(enemy_count, decisions, seed):
    """Cuenta las operaciones que una partida real ejecuta sobre la agenda.

    Responde a la seccion 8 del enunciado. El jugador recibe mucha vida y
    defensa alta para que la partida no termine antes de completar las
    decisiones pedidas y la muestra quede completa.
    """
    player = Player("p-1", "Heroe", 10_000_000, 6, 100, 100, 1)
    enemies = [
        Enemy(
            f"e-{index:04}",
            "Rata gigante",
            1_000_000,
            5,
            1,
            150,
            1,
            Enemy.GUARDIAN,
            regeneration=1,
        )
        for index in range(enemy_count)
    ]

    agenda = CountingEventQueue()
    game = Game(GameState(seed=seed), player, enemies, event_queue=agenda)
    game.apply_poison(player, 1)
    game.light_torch(10_000_000)

    for _ in range(decisions):
        game.wait()

    return game, agenda


def measure_cancellation_frequency(enemy_count, seed):
    """Cuenta las cancelaciones de una partida con combate.

    El escenario anterior no cancela nada, porque nadie muere. Aqui el jugador
    mata a un enemigo por accion, lo que cancela la accion pendiente de cada
    uno, y ademas se aplica y se corta un veneno cada diez ataques, cortandolo al ataque siguiente para que no expire solo.
    """
    player = Player("p-1", "Heroe", 10_000_000, 1_000, 100, 100, 1)
    enemies = [
        Enemy(f"e-{index:04}", "Rata gigante", 1, 5, 1, 150, 1, Enemy.GUARDIAN)
        for index in range(enemy_count)
    ]

    agenda = CountingEventQueue()
    game = Game(GameState(seed=seed), player, enemies, event_queue=agenda)

    for index, enemy in enumerate(enemies):
        if index % 10 == 0:
            game.apply_poison(player, 1)

        if index % 10 == 1:
            game.cancel_poison(player)

        game.attack(enemy.actor_id)

    return game, agenda


def report_frequency(title, game, agenda, decisions):
    print(title)
    print(f"  Decisiones del jugador           {decisions:>12,}")
    print(f"  Eventos procesados               {game.events_processed:>12,}")
    print(
        f"  Eventos por decision             "
        f"{game.events_processed / decisions:>12.1f}"
    )
    print(f"  Inserciones en la agenda         {agenda.pushes:>12,}")
    print(f"  Extracciones de la agenda        {agenda.pops:>12,}")
    print(
        f"  Inserciones por extraccion       "
        f"{agenda.pushes / agenda.pops:>12.2f}"
    )
    print(f"  Cancelaciones                    {agenda.cancels:>12,}")
    print(f"  Cancelados descartados           {agenda.discarded:>12,}")
    print(f"  Tamano maximo de la agenda       {agenda.max_size:>12,}")
    print()


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
    report("Mediciones de tiempo", measurements)

    for label, enemy_count in (("Cripta pequena", 5), ("Cripta grande", 50)):
        game, agenda = measure_operation_frequency(
            enemy_count, FREQUENCY_DECISIONS, SEED
        )
        report_frequency(
            f"Frecuencia de operaciones, {label.lower()} ({enemy_count} enemigos)",
            game,
            agenda,
            FREQUENCY_DECISIONS,
        )

    combat_game, combat_agenda = measure_cancellation_frequency(500, SEED)
    report_frequency(
        "Frecuencia de operaciones, partida con combate (500 enemigos)",
        combat_game,
        combat_agenda,
        combat_game.player_actions,
    )
    print(f"  Enemigos derrotados              {combat_game.enemies_defeated:>12,}")
    print()

    heap, unsorted_list, cycle = measurements

    print(f"El monticulo es {unsorted_list.seconds / heap.seconds:.1f} veces mas")
    print("rapido que la lista sin ordenar en esta carga.")
    print()

    per_cycle_ms = cycle.seconds / PLAYER_DECISIONS * 1000
    budget = "cumple" if per_cycle_ms < 20 else "NO cumple"
    print(f"Ciclo de eventos: {per_cycle_ms:.4f} ms, {budget} el limite de 20 ms.")


if __name__ == "__main__":
    main()
