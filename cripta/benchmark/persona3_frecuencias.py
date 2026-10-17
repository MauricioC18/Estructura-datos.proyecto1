"""
Frecuencia medida de las operaciones de la Persona 3 (§8.1).

Recorre la misma cripta sintetica que benchmark/scheduler_bench.py, con el
motor real, y cuenta cuantas veces se ejecuta cada operacion por decision del
jugador. No modifica Game: se le inyectan la bitacora y la agenda con
contadores, igual que hace CountingEventQueue.

    python -m benchmark.persona3_frecuencias

Que se mide y que no
    - Mensajes de la bitacora: medidos, son los que el motor escribe.
    - Cambios que la agenda anota en el historial: medidos con
      ReversibleEventQueue. Es una cota inferior del tamano del historial,
      porque los cambios de atributos del motor todavia no se anotan.
    - Marcas de rastro: una por accion aceptada del jugador, mas la inicial,
      como pide el Apendice B. Se cuentan desde este recorrido.
    - Decisiones de rastreador: se cuentan los turnos de enemigos, que es lo
      que costaria si todos fueran rastreadores.
    - Inventario y vistas ordenadas: dependen de los comandos del jugador, no
      del motor. No se pueden medir con un recorrido automatico.
"""
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
SCENARIOS = ((6, 5), (40, 50))


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
        self.records = 0
        self.max_interval = 0
        self._in_interval = 0

    def begin_action(self):
        super().begin_action()
        self._in_interval = 0

    def record(self, change):
        if self.is_recording:
            self.records += 1
            self._in_interval += 1
            if self._in_interval > self.max_interval:
                self.max_interval = self._in_interval
        super().record(change)


def measure(room_count, wanderers, decisions=DECISIONS, seed=SEED):
    state = GameState(seed=seed)
    history = CountingHistory(state)
    log = CountingLog()
    trail = PlayerTrail(history)

    room_map = build_synthetic_crypt(room_count)
    player = Player("p-1", "Heroe", 100_000_000, 6, 100, 100, 1)
    enemies = [
        Enemy(
            f"e-{index:04}",
            "Errante",
            1_000_000,
            5,
            1,
            150,
            1 + index % room_count,
            Enemy.WANDERER,
        )
        for index in range(wanderers)
    ]

    game = Game(
        state,
        player,
        enemies,
        room_map=room_map,
        message_log=log,
        event_queue=ReversibleEventQueue(history),
    )

    for room_id in range(1, room_count + 1):
        game._activate_enemies_in(room_id)

    trail.mark(player.room_id, state.clock)
    marks = 1
    enemy_turns = 0

    original_move = game.move
    original_open = game.open_door
    original_enemy_turn = game._run_enemy_turn

    def counted_enemy_turn(enemy):
        nonlocal enemy_turns
        enemy_turns += 1
        original_enemy_turn(enemy)

    def as_player_action(action):
        def wrapped(direction):
            nonlocal marks
            clock = state.clock
            history.begin_action()
            result = action(direction)
            if result.accepted:
                trail.mark(player.room_id, clock)
                marks += 1
            else:
                history.undo()
            return result
        return wrapped

    game._run_enemy_turn = counted_enemy_turn
    game.move = as_player_action(original_move)
    game.open_door = as_player_action(original_open)

    walk_the_crypt(game, decisions)

    actions = game.player_actions
    return {
        "salas": room_count,
        "errantes": wanderers,
        "decisiones": actions,
        "eventos": game.events_processed,
        "mensajes": log.appended,
        "anotaciones": history.records,
        "max_intervalo": history.max_interval,
        "marcas": marks,
        "turnos_enemigos": enemy_turns,
    }


def main():
    for room_count, wanderers in SCENARIOS:
        result = measure(room_count, wanderers)
        decisions = result["decisiones"]
        print(f"Recorrido, {room_count} salas, {wanderers} errantes")
        print(f"  Decisiones del jugador                 {decisions:>10,}")
        print(f"  Eventos procesados                     {result['eventos']:>10,}")
        print(f"  Mensajes en la bitacora                {result['mensajes']:>10,}   {result['mensajes'] / decisions:.2f} por decision")
        print(f"  Anotaciones de la agenda en historial  {result['anotaciones']:>10,}   {result['anotaciones'] / decisions:.2f} por decision")
        print(f"  Mayor intervalo (anotaciones)          {result['max_intervalo']:>10,}")
        print(f"  Marcas de rastro                       {result['marcas']:>10,}   {result['marcas'] / decisions:.2f} por decision")
        print(f"  Turnos de enemigos                     {result['turnos_enemigos']:>10,}   {result['turnos_enemigos'] / decisions:.2f} por decision")
        print()


if __name__ == "__main__":
    main()
