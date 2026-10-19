"""
Frecuencia medida de las operaciones de la Persona 3 (§8.1).

Recorre la misma cripta sintetica que benchmark/scheduler_bench.py con el
motor real, ya integrado: Game abre los intervalos del historial, anota sus
cambios, marca el rastro y ordena los enemigos al activarlos. Este archivo no
simula nada de eso; solo le pasa a Game versiones con contadores del
historial, el rastro y la bitacora, igual que CountingEventQueue hace con la
agenda.

    python -m benchmark.persona3_frecuencias

Escenarios
    - 6 salas y 5 errantes, y 40 salas y 50 errantes: los mismos de
      scheduler_bench, para poder comparar.
    - 40 salas y 50 rastreadores: los rastreadores consultan el rastro en
      cada turno, asi que es el escenario que mide esa operacion.

Que no se mide
    Las operaciones de inventario y las vistas ordenadas dependen de los
    comandos que escriba el jugador. Un recorrido automatico solo se mueve y
    abre puertas, asi que no las ejecuta.
"""
import time

import model.game as game_module
from benchmark.scheduler_bench import build_synthetic_crypt, walk_the_crypt
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.player import Player
from structures.circular_log import CircularLog
from structures.history import History, ReversibleEventQueue
from structures.trail import PlayerTrail

SEED = 2026
DECISIONS = 1_000
SCENARIOS = (
    (6, 5, Enemy.WANDERER, "errantes"),
    (40, 50, Enemy.WANDERER, "errantes"),
    (40, 50, Enemy.TRACKER, "rastreadores"),
)


class CountingLog(CircularLog):
    def __init__(self):
        super().__init__()
        self.appended = 0

    def append(self, message):
        super().append(message)
        self.appended += 1


class CountingHistory(History):
    def __init__(self, state):
        super().__init__(state)
        self.intervals = 0
        self.records = 0
        self.max_interval = 0
        self._in_interval = 0

    def begin_action(self):
        super().begin_action()
        self.intervals += 1
        self._in_interval = 0

    def record(self, change):
        if self.is_recording:
            self.records += 1
            self._in_interval += 1
            if self._in_interval > self.max_interval:
                self.max_interval = self._in_interval
        super().record(change)

    def assign(self, target, attribute, value):
        if self.is_recording:
            self.records += 1
            self._in_interval += 1
            if self._in_interval > self.max_interval:
                self.max_interval = self._in_interval
        super().assign(target, attribute, value)


class CountingTrail(PlayerTrail):
    def __init__(self, history):
        super().__init__(history)
        self.marks = 0
        self.decisions = 0

    def mark(self, room_id, time):
        super().mark(room_id, time)
        self.marks += 1

    def freshest_exit(self, room, current_time):
        self.decisions += 1
        return super().freshest_exit(room, current_time)


def measure(room_count, enemy_count, behavior, decisions=DECISIONS, seed=SEED):
    state = GameState(seed=seed)
    history = CountingHistory(state)
    trail = CountingTrail(history)
    log = CountingLog()

    room_map = build_synthetic_crypt(room_count)
    player = Player("p-1", "Heroe", 100_000_000, 6, 100, 100, 1)
    enemies = [
        Enemy(
            f"e-{index:04}",
            "Enemigo",
            1_000_000,
            5,
            1,
            150,
            1 + index % room_count,
            behavior,
        )
        for index in range(enemy_count)
    ]

    sorts = 0
    original_sort = game_module.sort

    def counted_sort(*args, **kwargs):
        nonlocal sorts
        sorts += 1
        return original_sort(*args, **kwargs)

    game_module.sort = counted_sort
    try:
        game = Game(
            state,
            player,
            enemies,
            room_map=room_map,
            trail=trail,
            history=history,
            message_log=log,
            event_queue=ReversibleEventQueue(history),
        )
        walk_the_crypt(game, decisions)
    finally:
        game_module.sort = original_sort

    actions = game.player_actions
    events = game.events_processed
    sizes = [len(interval.changes) for interval in history._intervals]
    clock = state.clock
    start = time.perf_counter()
    undone = 0
    while history.undo():
        undone += 1
    undo_seconds = time.perf_counter() - start

    return {
        "decisiones": actions,
        "eventos": events,
        "intervalos": history.intervals,
        "anotaciones": history.records,
        "max_intervalo": history.max_interval,
        "mensajes": log.appended,
        "marcas": trail.marks,
        "consultas_rastro": trail.decisions,
        "ordenamientos": sorts,
        "deshechos": undone,
        "anotaciones_deshechas": sum(sizes),
        "segundos_deshacer": undo_seconds,
        "reloj_final": clock,
        "reloj_tras_deshacer": state.clock,
    }


def main():
    for room_count, enemy_count, behavior, label in SCENARIOS:
        result = measure(room_count, enemy_count, behavior)
        decisions = result["decisiones"]

        def line(name, key):
            value = result[key]
            print(f"  {name:<40} {value:>10,}   {value / decisions:.2f} por decision")

        print(f"Recorrido, {room_count} salas, {enemy_count} {label}")
        print(f"  {'Decisiones del jugador':<40} {decisions:>10,}")
        print(f"  {'Eventos procesados':<40} {result['eventos']:>10,}")
        line("Intervalos abiertos en el historial", "intervalos")
        line("Anotaciones en el historial", "anotaciones")
        print(f"  {'Mayor intervalo (anotaciones)':<40} {result['max_intervalo']:>10,}")
        line("Mensajes en la bitacora", "mensajes")
        line("Marcas de rastro", "marcas")
        line("Consultas del rastro (rastreadores)", "consultas_rastro")
        line("Ordenamientos del motor", "ordenamientos")
        print(
            f"  Deshacer las ultimas {result['deshechos']} acciones: "
            f"{result['anotaciones_deshechas']} anotaciones en "
            f"{result['segundos_deshacer'] * 1000:.3f} ms; "
            f"reloj de {result['reloj_final']} a {result['reloj_tras_deshacer']}"
        )
        print()


if __name__ == "__main__":
    main()
