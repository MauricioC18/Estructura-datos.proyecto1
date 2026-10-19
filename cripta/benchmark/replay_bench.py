"""Mediciones de la bitacora de partida y de la reproduccion (§4.11).

Responde a lo que el Documento de Decisiones afirma sobre la bitacora:

- Cuanto cuesta anotar cada accion con un flush por linea, frente a dejar que
  el sistema junte las escrituras (alternativa descartada) y frente a forzar
  la escritura al disco con fsync (alternativa descartada).
- Cuanto ocupa el log por accion, frente a registrar todos los eventos
  procesados o una foto del estado despues de cada accion (alternativas
  descartadas).
- Cuanto tarda leer y reproducir una partida larga, y si termina igual.

No usa la red: la partida corre sobre la cripta sintetica de
scheduler_bench, con el controlador de verdad. Se ejecuta con
`python -m benchmark.replay_bench` desde `cripta/`.
"""
import json
import os
import tempfile
import time

from benchmark.scheduler_bench import build_synthetic_crypt
from benchmark.utilidades_medicion import Measurement, descripcion_del_equipo
from controller.commands import parse_command
from controller.game_controller import GameController
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.player import Player
from replay.replay import replay_commands
from replay.replay_log import ReplayHeader, ReplayLogWriter, read_replay_log


ROOMS = 50
WANDERERS = 30
ACTIONS = 2_000
SEED = 2026
HEADER = ReplayHeader("cripta-sintetica", "v-bench", "cat-bench", SEED)


class _BufferedLogWriter(ReplayLogWriter):
    """Alternativa descartada: sin flush, el sistema decide cuando escribir."""

    def _write_line(self, text):
        self._file.write(text + "\n")


class _SyncedLogWriter(ReplayLogWriter):
    """Alternativa descartada: flush y ademas fsync en cada linea."""

    def _write_line(self, text):
        self._file.write(text + "\n")
        self._file.flush()
        os.fsync(self._file.fileno())


class _NullLog:
    def append(self, command):
        pass


def make_game():
    """Misma partida que mide scheduler_bench: errantes, trampas y puertas."""
    player = Player("p-1", "Heroe", 100_000_000, 6, 100, 100, 1)
    enemies = [
        Enemy(
            f"e-{index:04}", "Errante", 1_000_000, 5, 1, 150,
            1 + index % ROOMS, Enemy.WANDERER,
        )
        for index in range(WANDERERS)
    ]
    game = Game(GameState(seed=SEED), player, enemies, room_map=build_synthetic_crypt(ROOMS))

    for room_id in range(1, ROOMS + 1):
        game._activate_enemies_in(room_id)

    return game


def play(log):
    """Camina la cripta por el controlador, como lo haria el jugador.

    Devuelve el juego y los segundos que tomo, contando solo el trabajo del
    controlador y del motor (con la escritura del log incluida).
    """
    game = make_game()
    controller = GameController(game, log)
    direction = "N"
    move = {"N": parse_command("mover N"), "S": parse_command("mover S")}
    open_ = {"N": parse_command("abrir N"), "S": parse_command("abrir S")}

    start = time.perf_counter()

    while game.player_actions < ACTIONS and not game.is_over:
        if controller.execute(move[direction]).accepted:
            continue

        if controller.execute(open_[direction]).accepted:
            continue

        direction = "S" if direction == "N" else "N"

    return game, time.perf_counter() - start


def _play_with(writer_class, directory, name):
    path = os.path.join(directory, name)

    with writer_class(path, HEADER) as log:
        game, seconds = play(log)

    return game, seconds, path


def write_only(writer_class, directory, lines=ACTIONS, repetitions=5):
    """Solo el costo de anotar, sin simular: el mejor de varias corridas."""
    command = parse_command("mover N")
    best = None

    for repetition in range(repetitions):
        path = os.path.join(directory, f"solo-{writer_class.__name__}-{repetition}.log")
        start = time.perf_counter()

        with writer_class(path, HEADER) as log:
            for _ in range(lines):
                log.append(command)

        elapsed = time.perf_counter() - start
        best = elapsed if best is None else min(best, elapsed)

    return best


def state_snapshot(game):
    """Lo minimo que habria que anotar para no tener que re-simular: una foto
    del estado de los actores y de las salas despues de la accion."""
    rooms = []

    for room_id in game.room_map.room_ids():
        room = game.room_map.room(room_id)
        rooms.append({
            "id": room.room_id,
            "puertas": [exit_.door.is_open for exit_ in room.exits()],
            "trampas": [trap.armed for trap in room.traps],
            "suelo": [item.instance_id for item in room.floor_items],
        })

    return json.dumps({
        "reloj": game.state.clock,
        "jugador": [game.player.room_id, game.player.health],
        "enemigos": [[enemy.actor_id, enemy.room_id, enemy.health] for enemy in game.enemies],
        "salas": rooms,
    })


def run():
    measurements = []

    with tempfile.TemporaryDirectory() as directory:
        game_null, seconds_null = play(_NullLog())
        game_flush, seconds_flush, path = _play_with(ReplayLogWriter, directory, "flush.log")
        _, seconds_buffered, _ = _play_with(_BufferedLogWriter, directory, "buffer.log")
        _, seconds_synced, _ = _play_with(_SyncedLogWriter, directory, "fsync.log")

        for name, writer_class in (
            ("flush por linea (elegida)", ReplayLogWriter),
            ("sin flush (descartada)", _BufferedLogWriter),
            ("fsync por linea (descartada)", _SyncedLogWriter),
        ):
            seconds = write_only(writer_class, directory)
            measurements.append(Measurement(
                f"Solo escribir: {name}", seconds,
                f"{ACTIONS} lineas, {seconds / ACTIONS * 1e6:.2f} us por linea",
            ))

        actions = game_flush.player_actions
        lines = len(read_replay_log(path).commands)
        size = os.path.getsize(path)

        for name, seconds in (
            ("Partida sin bitacora", seconds_null),
            ("Bitacora con flush por linea (elegida)", seconds_flush),
            ("Bitacora sin flush (descartada)", seconds_buffered),
            ("Bitacora con fsync por linea (descartada)", seconds_synced),
        ):
            per_action = seconds / actions * 1e6
            measurements.append(Measurement(
                f"Grabar: {name}", seconds,
                f"{actions} acciones, {per_action:.1f} us por accion",
            ))

        events_per_action = game_flush.events_processed / actions
        snapshot_bytes = len(state_snapshot(game_flush).encode("utf-8")) + 1
        measurements.append(Measurement(
            "Tamano: log de comandos (elegido)", None,
            f"{size} bytes, {lines} lineas, {size / lines:.1f} bytes por accion",
        ))
        measurements.append(Measurement(
            "Tamano: log de eventos (descartado)", None,
            f"{events_per_action:.1f} eventos procesados por accion: "
            f"{events_per_action:.1f} veces mas lineas",
        ))
        measurements.append(Measurement(
            "Tamano: foto del estado por accion (descartado)", None,
            f"{snapshot_bytes} bytes por accion con {ROOMS} salas y "
            f"{WANDERERS} enemigos, {snapshot_bytes / (size / lines):.0f} veces mas",
        ))

        start = time.perf_counter()
        log = read_replay_log(path)
        seconds_read = time.perf_counter() - start

        reproduced = make_game()
        start = time.perf_counter()
        replay_commands(GameController(reproduced), log.commands)
        seconds_replay = time.perf_counter() - start

    same = (
        reproduced.state.clock == game_flush.state.clock
        and reproduced.player.room_id == game_flush.player.room_id
        and reproduced.player.health == game_flush.player.health
        and game_null.state.clock == game_flush.state.clock
    )

    measurements.append(Measurement(
        "Reproducir: leer e interpretar el log", seconds_read,
        f"{lines} lineas, {seconds_read / lines * 1e6:.1f} us por linea",
    ))
    measurements.append(Measurement(
        "Reproducir: ejecutar las acciones", seconds_replay,
        f"{seconds_replay / lines * 1e3:.3f} ms por accion, "
        f"termina igual que la original: {'si' if same else 'NO'}",
    ))

    return measurements


def main():
    print(descripcion_del_equipo())
    for measurement in run():
        seconds = "-" if measurement.seconds is None else f"{measurement.seconds:.3e} s"
        print(f"{measurement.name:<52} {seconds:>12}  {measurement.detail}")


if __name__ == "__main__":
    main()
