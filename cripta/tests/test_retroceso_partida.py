"""
El retroceso del motor integrado, a lo largo de una partida.

test_rewind.py prueba cada accion por separado. Esta prueba recorre la cripta
sintetica de benchmark/scheduler_bench.py con 50 enemigos, y despues de cada
accion aceptada deshace y compara contra la foto de tests/verificar_retroceso.py:
reloj, actores, puertas, trampas, suelo, agenda, efectos y rastro. Asi se
cubren las combinaciones que aparecen solas en una partida: trampas que se
rearman, puertas que se cierran, enemigos que se mueven y atacan.

Despues de deshacer se vuelve a ejecutar la accion para seguir avanzando. No
se exige que rehacer de el mismo estado: el retroceso no restaura el generador
aleatorio ni el contador de secuencia (DECISIONES.md, "El reloj virtual y la
numeracion de eventos"), asi que un errante puede escoger otra salida.
"""
import unittest

from benchmark.scheduler_bench import build_synthetic_crypt
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.player import Player
from structures.history import History, ReversibleEventQueue
from structures.trail import PlayerTrail
from tests.verificar_retroceso import differences, snapshot

ROOMS = 40
ENEMIES = 50
ACTIONS = 60


def build_game(behavior):
    state = GameState(seed=2026)
    history = History(state)
    trail = PlayerTrail(history)
    player = Player("p-1", "Heroe", 100_000_000, 6, 100, 100, 1)
    enemies = [
        Enemy(f"e-{index:04}", "Enemigo", 1_000_000, 5, 1, 150, 1 + index % ROOMS, behavior)
        for index in range(ENEMIES)
    ]
    game = Game(
        state,
        player,
        enemies,
        room_map=build_synthetic_crypt(ROOMS),
        trail=trail,
        history=history,
        event_queue=ReversibleEventQueue(history),
    )
    return game, history, trail


class TestRewindAlongAGame(unittest.TestCase):

    def walk_undoing_every_action(self, behavior):
        game, history, trail = build_game(behavior)
        direction = "N"
        checked = 0

        while checked < ACTIONS:
            before = snapshot(game, trail)
            action = game.move

            if not action(direction).accepted:
                action = game.open_door
                if not action(direction).accepted:
                    direction = "S" if direction == "N" else "N"
                    continue

            self.assertTrue(history.undo())
            found = differences(before, snapshot(game, trail))
            self.assertEqual(
                found,
                [],
                f"Accion {checked + 1}: el retroceso no restauro todo:\n  " + "\n  ".join(found),
            )

            checked += 1
            self.assertTrue(action(direction).accepted)

    def test_wanderers(self):
        self.walk_undoing_every_action(Enemy.WANDERER)

    def test_trackers(self):
        self.walk_undoing_every_action(Enemy.TRACKER)


if __name__ == "__main__":
    unittest.main()
