import unittest

from model.effects import POISON, POISON_DURATION, POISON_PULSE_INTERVAL
from model.enemy import Enemy
from model.game import DEFEAT, IN_PROGRESS, Game
from model.game_state import GameState
from model.player import Player


def make_player(speed=100, max_health=100, attack=6, defense=10, health=None):
    return Player(
        actor_id="p-1",
        name="Heroe",
        max_health=max_health,
        attack=attack,
        defense=defense,
        speed=speed,
        room_id=1,
        health=health,
    )


def make_enemy(actor_id="e-201", speed=150, room_id=7, max_health=12, health=None,
               regeneration=0):
    return Enemy(
        actor_id=actor_id,
        name="Rata gigante",
        max_health=max_health,
        attack=5,
        defense=1,
        speed=speed,
        room_id=room_id,
        behavior=Enemy.GUARDIAN,
        health=health,
        regeneration=regeneration,
    )


def make_game(player=None, enemies=None, seed=2026):
    player = make_player() if player is None else player

    return Game(GameState(seed=seed), player, enemies)


class TestPoison(unittest.TestCase):

    def test_poison_schedules_one_pulse_every_eighty_units(self):
        game = make_game()

        effect = game.apply_poison(game.player, 2)

        self.assertEqual(
            [event.time for event in effect.events],
            [80, 160, 240, 320, 400],
        )

    def test_poison_lasts_four_hundred_units_and_no_more(self):
        game = make_game()
        game.apply_poison(game.player, 2)

        for _ in range(6):
            game.wait()

        self.assertGreater(game.state.clock, POISON_DURATION)
        self.assertEqual(game.player.health, 100 - 5 * 2)

    def test_each_pulse_applies_its_damage(self):
        game = make_game()
        game.apply_poison(game.player, 3)

        game.wait()

        self.assertEqual(game.player.health, 97)

    def test_an_antidote_prevents_every_future_pulse(self):
        game = make_game()
        game.apply_poison(game.player, 2)

        game.wait()
        health_after_the_first_pulse = game.player.health
        cancelled = game.cancel_poison(game.player)

        for _ in range(6):
            game.wait()

        self.assertTrue(cancelled)
        self.assertEqual(game.player.health, health_after_the_first_pulse)

    def test_an_antidote_without_poison_does_nothing(self):
        game = make_game()

        self.assertFalse(game.cancel_poison(game.player))

    def test_poison_can_defeat_the_player(self):
        game = make_game(player=make_player(max_health=5, health=5))
        game.apply_poison(game.player, 4)

        for _ in range(4):
            game.wait()

        self.assertEqual(game.result, DEFEAT)

    def test_poison_shows_up_in_the_visible_state(self):
        game = make_game()
        game.apply_poison(game.player, 2)

        names = [effect.name for effect in game.visible_state().effects]

        self.assertIn(POISON, names)

    def test_a_cancelled_poison_disappears_from_the_visible_state(self):
        game = make_game()
        game.apply_poison(game.player, 2)
        game.cancel_poison(game.player)

        self.assertEqual(game.visible_state().effects, [])


class TestRegeneration(unittest.TestCase):

    def test_a_wounded_enemy_recovers_every_two_hundred_units(self):
        enemy = make_enemy(room_id=1, max_health=20, health=5, regeneration=3)
        game = make_game(enemies=[enemy])

        game.wait()
        game.wait()

        self.assertEqual(enemy.health, 8)

    def test_regeneration_never_exceeds_the_maximum(self):
        enemy = make_enemy(room_id=1, max_health=10, health=9, regeneration=5)
        game = make_game(enemies=[enemy])

        for _ in range(4):
            game.wait()

        self.assertEqual(enemy.health, 10)

    def test_an_enemy_without_regeneration_does_not_recover(self):
        enemy = make_enemy(room_id=1, max_health=20, health=5)
        game = make_game(enemies=[enemy])

        for _ in range(4):
            game.wait()

        self.assertEqual(enemy.health, 5)

    def test_regeneration_stops_when_the_enemy_dies(self):
        enemy = make_enemy(room_id=1, max_health=20, health=1, regeneration=3)
        game = make_game(enemies=[enemy])

        game.attack("e-201")

        for _ in range(4):
            game.wait()

        self.assertFalse(enemy.is_alive)
        self.assertEqual(enemy.health, 0)


class TestSpeedChange(unittest.TestCase):

    def test_speeding_up_lets_the_player_act_more_often(self):
        normal = make_game()
        normal.wait()
        normal_clock = normal.state.clock

        hasted = make_game()
        hasted.apply_speed_change(hasted.player, 200, 1000)
        hasted.wait()

        self.assertLess(hasted.state.clock, normal_clock)

    def test_the_speed_returns_to_its_previous_value_when_the_effect_ends(self):
        game = make_game()
        game.apply_speed_change(game.player, 200, 300)

        self.assertEqual(game.player.speed, 200)

        for _ in range(10):
            game.wait()

        self.assertEqual(game.player.speed, 100)

    def test_the_effect_is_visible_while_it_lasts(self):
        game = make_game()
        game.apply_speed_change(game.player, 200, 300)

        self.assertEqual(
            [effect.name for effect in game.visible_state().effects],
            ["velocidad"],
        )

    def test_the_effect_disappears_after_it_ends(self):
        game = make_game()
        game.apply_speed_change(game.player, 200, 300)

        for _ in range(10):
            game.wait()

        self.assertEqual(game.visible_state().effects, [])

    def test_ending_the_effect_reschedules_an_enemy_action(self):
        enemy = make_enemy(room_id=7, speed=100)
        game = make_game(enemies=[enemy])
        game._activate_enemies_in(7)
        before = enemy.scheduled_event

        game.apply_speed_change(enemy, 200, 300)

        self.assertTrue(before.cancelled)
        self.assertGreater(enemy.scheduled_event.sequence, before.sequence)


class TestTorch(unittest.TestCase):

    def test_lighting_a_torch_turns_it_on(self):
        game = make_game()

        game.light_torch(500)

        self.assertTrue(game.visible_state().torch_lit)

    def test_the_torch_goes_out_after_its_duration(self):
        game = make_game()
        game.light_torch(250)

        game.wait()
        self.assertTrue(game.torch_lit)

        game.wait()
        game.wait()

        self.assertFalse(game.torch_lit)

    def test_the_torch_appears_as_an_active_effect(self):
        game = make_game()
        game.light_torch(500)

        self.assertEqual(
            [effect.name for effect in game.visible_state().effects],
            ["antorcha"],
        )


class TestEffectsAndDeterminism(unittest.TestCase):

    def play(self, seed):
        game = make_game(enemies=[make_enemy(room_id=1, speed=250)], seed=seed)
        game.apply_poison(game.player, 2)
        game.light_torch(300)
        game.apply_speed_change(game.player, 150, 400)

        for _ in range(4):
            game.attack("e-201")

        return game

    def test_the_same_seed_produces_the_same_game_with_effects(self):
        first = self.play(2026)
        second = self.play(2026)

        self.assertEqual(first.player.health, second.player.health)
        self.assertEqual(first.state.clock, second.state.clock)
        self.assertEqual(first.messages, second.messages)

    def test_the_game_stays_in_progress_with_several_effects(self):
        game = self.play(2026)

        self.assertIn(game.result, (IN_PROGRESS, DEFEAT))


class TestInjectedMessageLog(unittest.TestCase):

    def test_the_game_uses_the_log_it_receives(self):
        log = []
        game = Game(GameState(seed=2026), make_player(), None, message_log=log)

        game.wait()

        self.assertEqual(log, game.messages)
        self.assertIn("Esperas.", log)

    def test_any_structure_with_append_works(self):

        class BoundedLog:

            def __init__(self, limit):
                self.limit = limit
                self.items = []

            def append(self, message):
                self.items.append(message)

                if len(self.items) > self.limit:
                    self.items.pop(0)

            def __iter__(self):
                return iter(self.items)

        log = BoundedLog(2)
        game = Game(GameState(seed=2026), make_player(), None, message_log=log)

        for _ in range(5):
            game.wait()

        self.assertEqual(len(game.visible_state().messages), 2)


if __name__ == "__main__":
    unittest.main()
