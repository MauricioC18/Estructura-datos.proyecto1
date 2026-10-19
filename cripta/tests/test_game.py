import unittest

from model.enemy import Enemy
from model.game import DEFEAT, IN_PROGRESS, Game
from model.game_state import GameState
from model.player import Player
from structures.event_queue import EventQueue


class Weapon:

    def __init__(self, attack_bonus):
        self.attack_bonus = attack_bonus


def make_player(speed=100, max_health=100, attack=6, defense=10, room_id=1):
    return Player(
        actor_id="p-1",
        name="Heroe",
        max_health=max_health,
        attack=attack,
        defense=defense,
        speed=speed,
        room_id=room_id,
    )


def make_enemy(actor_id="e-201", speed=150, attack=5, room_id=1, max_health=12):
    return Enemy(
        actor_id=actor_id,
        name="Rata gigante",
        max_health=max_health,
        attack=attack,
        defense=1,
        speed=speed,
        room_id=room_id,
        behavior=Enemy.TRACKER,
    )


def make_game(player=None, enemies=None, seed=2026):
    player = make_player() if player is None else player

    return Game(GameState(seed=seed), player, enemies)


class TestEngineLoop(unittest.TestCase):

    def test_the_player_decides_at_instant_zero(self):
        game = make_game(enemies=[make_enemy()])

        self.assertEqual(game.state.clock, 0)
        self.assertEqual(game.result, IN_PROGRESS)

    def test_a_faster_enemy_acts_between_two_player_decisions(self):
        game = make_game(enemies=[make_enemy(speed=150)])

        game.wait()

        self.assertEqual(game.state.clock, 100)
        self.assertEqual(game.player.health, 99)

    def test_a_much_faster_enemy_acts_twice(self):
        game = make_game(enemies=[make_enemy(speed=250)])

        game.wait()

        self.assertEqual(game.state.clock, 100)
        self.assertEqual(game.player.health, 98)

    def test_an_enemy_in_another_room_never_acts(self):
        game = make_game(enemies=[make_enemy(room_id=7)])

        game.wait()
        game.wait()

        self.assertEqual(game.player.health, 100)

    def test_the_clock_only_moves_forward(self):
        game = make_game(enemies=[make_enemy(speed=250)])
        instants = [game.state.clock]

        for _ in range(5):
            game.wait()
            instants.append(game.state.clock)

        for previous, current in zip(instants, instants[1:]):
            self.assertLess(previous, current)


class TestCombat(unittest.TestCase):

    def test_attacking_reduces_the_enemy_health(self):
        enemy = make_enemy()
        game = make_game(enemies=[enemy])

        result = game.attack("e-201")

        self.assertTrue(result.accepted)
        self.assertLess(enemy.health, enemy.max_health)

    def test_damage_is_never_below_one(self):
        player = make_player(attack=1)
        enemy = make_enemy(max_health=50)
        enemy.defense = 100
        game = make_game(player=player, enemies=[enemy])

        game.attack("e-201")

        self.assertEqual(enemy.health, 49)

    def test_equipment_increases_the_damage(self):
        unarmed_enemy = make_enemy(max_health=50)
        unarmed_game = make_game(enemies=[unarmed_enemy])
        unarmed_game.attack("e-201")
        unarmed_damage = unarmed_enemy.max_health - unarmed_enemy.health

        armed_player = make_player()
        armed_player.equipped_weapon = Weapon(attack_bonus=3)
        armed_enemy = make_enemy(max_health=50)
        armed_game = make_game(player=armed_player, enemies=[armed_enemy])
        armed_game.attack("e-201")
        armed_damage = armed_enemy.max_health - armed_enemy.health

        self.assertEqual(armed_damage, unarmed_damage + 3)

    def test_a_dead_enemy_stops_acting(self):
        enemy = make_enemy(speed=250, max_health=1)
        game = make_game(enemies=[enemy])

        game.attack("e-201")
        health_after_the_kill = game.player.health

        game.wait()
        game.wait()

        self.assertFalse(enemy.is_alive)
        self.assertEqual(game.player.health, health_after_the_kill)

    def test_the_player_is_defeated_when_health_reaches_zero(self):
        player = make_player(max_health=3, defense=0)
        game = make_game(player=player, enemies=[make_enemy(speed=250, attack=20)])

        for _ in range(5):
            game.wait()

        self.assertEqual(game.result, DEFEAT)
        self.assertFalse(game.player.is_alive)


class TestRejectedActions(unittest.TestCase):

    def test_attacking_an_unknown_enemy_is_rejected(self):
        game = make_game(enemies=[make_enemy()])

        result = game.attack("e-999")

        self.assertFalse(result.accepted)

    def test_attacking_an_enemy_in_another_room_is_rejected(self):
        game = make_game(enemies=[make_enemy(room_id=7)])

        result = game.attack("e-201")

        self.assertFalse(result.accepted)

    def test_a_rejected_action_consumes_no_time(self):
        game = make_game(enemies=[make_enemy()])
        clock_before = game.state.clock

        game.attack("e-999")

        self.assertEqual(game.state.clock, clock_before)

    def test_a_rejected_action_consumes_no_randomness(self):
        game = make_game(enemies=[make_enemy()])
        state_before = game.state.random_state()

        game.attack("e-999")

        self.assertEqual(game.state.random_state(), state_before)


class TestDeterminism(unittest.TestCase):

    def play(self, seed):
        game = make_game(enemies=[make_enemy(speed=250)], seed=seed)

        game.attack("e-201")
        game.wait()
        game.attack("e-201")

        return game

    def test_the_same_seed_produces_the_same_game(self):
        first = self.play(2026)
        second = self.play(2026)

        self.assertEqual(first.player.health, second.player.health)
        self.assertEqual(first.state.clock, second.state.clock)
        self.assertEqual(list(first.messages), list(second.messages))

    def test_a_different_seed_produces_a_different_game(self):
        first = self.play(2026)
        other = self.play(1807)

        self.assertNotEqual(list(first.messages), list(other.messages))


class TestEnemyActivation(unittest.TestCase):

    def test_enemies_activate_in_ascending_identifier_order(self):
        later = make_enemy(actor_id="e-9")
        earlier = make_enemy(actor_id="e-10")
        game = make_game(enemies=[later, earlier])

        self.assertLess(
            earlier.scheduled_event.sequence,
            later.scheduled_event.sequence,
        )

    def test_only_the_enemies_of_the_player_room_are_activated(self):
        here = make_enemy(actor_id="e-1", room_id=1)
        elsewhere = make_enemy(actor_id="e-2", room_id=7)
        make_game(enemies=[here, elsewhere])

        self.assertTrue(here.is_active)
        self.assertFalse(elsewhere.is_active)

    def test_an_activated_enemy_is_scheduled_with_a_base_cost_of_one_hundred(self):
        enemy = make_enemy(speed=150)
        make_game(enemies=[enemy])

        self.assertEqual(enemy.scheduled_event.time, 66)


class TestSpeedChange(unittest.TestCase):

    def test_changing_speed_cancels_the_previous_event(self):
        enemy = make_enemy(speed=100)
        game = make_game(enemies=[enemy])
        previous_event = enemy.scheduled_event

        game.change_actor_speed(enemy, 200)

        self.assertTrue(previous_event.cancelled)
        self.assertIsNot(enemy.scheduled_event, previous_event)

    def test_the_rescheduled_event_gets_a_new_sequence_number(self):
        enemy = make_enemy(speed=100)
        game = make_game(enemies=[enemy])
        previous_event = enemy.scheduled_event

        game.change_actor_speed(enemy, 200)

        self.assertGreater(
            enemy.scheduled_event.sequence,
            previous_event.sequence,
        )

    def test_speeding_up_brings_the_enemy_action_closer(self):
        enemy = make_enemy(speed=100)
        game = make_game(enemies=[enemy])
        previous_time = enemy.scheduled_event.time

        game.change_actor_speed(enemy, 200)

        self.assertLess(enemy.scheduled_event.time, previous_time)

    def test_the_player_has_no_pending_event_during_their_turn(self):
        game = make_game(enemies=[make_enemy()])

        self.assertIsNone(game.player.scheduled_event)

        game.change_actor_speed(game.player, 200)

        self.assertIsNone(game.player.scheduled_event)
        self.assertEqual(game.player.speed, 200)


class TestVisibleState(unittest.TestCase):

    def test_visible_state_reports_the_player_and_the_room_enemies(self):
        game = make_game(
            enemies=[make_enemy(actor_id="e-1"), make_enemy(actor_id="e-2", room_id=7)]
        )

        view = game.visible_state()

        self.assertEqual(view.clock, 0)
        self.assertEqual(view.result, IN_PROGRESS)
        self.assertEqual(view.health, 100)
        self.assertEqual([enemy.actor_id for enemy in view.enemies], ["e-1"])

    def test_visible_state_hides_dead_enemies(self):
        game = make_game(enemies=[make_enemy(max_health=1)])

        game.attack("e-201")

        self.assertEqual(game.visible_state().enemies, [])

    def test_visible_state_includes_the_equipment_bonus(self):
        player = make_player()
        player.equipped_weapon = Weapon(attack_bonus=3)
        game = make_game(player=player)

        self.assertEqual(game.visible_state().attack, 9)



class TestCounters(unittest.TestCase):

    def test_player_actions_counts_accepted_actions(self):
        game = make_game(enemies=[make_enemy()])

        game.wait()
        game.wait()
        game.attack("e-201")

        self.assertEqual(game.player_actions, 3)

    def test_rejected_actions_are_not_counted(self):
        game = make_game(enemies=[make_enemy()])

        game.wait()
        game.attack("e-999")
        game.attack("e-201")

        self.assertEqual(game.player_actions, 2)

    def test_defeated_enemies_are_counted(self):
        first = make_enemy(actor_id="e-1", max_health=1)
        second = make_enemy(actor_id="e-2", max_health=1)
        game = make_game(enemies=[first, second])

        self.assertEqual(game.enemies_defeated, 0)

        game.attack("e-1")
        game.attack("e-2")

        self.assertEqual(game.enemies_defeated, 2)

    def test_processed_events_grow_with_the_game(self):
        game = make_game(enemies=[make_enemy(speed=250)])
        after_start = game.events_processed

        game.wait()

        self.assertGreater(game.events_processed, after_start)

    def test_the_game_accepts_an_injected_agenda(self):
        agenda = EventQueue()
        game = Game(
            GameState(seed=2026),
            make_player(),
            [make_enemy()],
            event_queue=agenda,
        )

        self.assertIs(game.events, agenda)

        game.wait()

        self.assertIs(agenda.peek(), game.enemies[0].scheduled_event)



class TestActionsWithoutAnInventory(unittest.TestCase):
    """Un jugador sin inventario rechaza, no revienta.

    Ocurre antes de que el controlador le asigne uno. Las siete acciones
    existen y responden; ninguna lanza AttributeError.
    """


    def setUp(self):
        self.game = make_game(enemies=[make_enemy()])

    def pending_actions(self):
        return (
            ("pick_up", lambda: self.game.pick_up(0)),
            ("drop", self.game.drop),
            ("use_item", self.game.use_item),
            ("equip_item", self.game.equip_item),
            ("inventory_next", self.game.inventory_next),
            ("inventory_previous", self.game.inventory_previous),
            ("rewind", self.game.rewind),
        )

    def test_they_answer_instead_of_crashing(self):
        for name, action in self.pending_actions():
            with self.subTest(action=name):
                result = action()

                self.assertFalse(result.accepted)
                self.assertIn("Todavia no se puede", result.message)

    def test_they_consume_no_time(self):
        for name, action in self.pending_actions():
            with self.subTest(action=name):
                clock_before = self.game.state.clock

                action()

                self.assertEqual(self.game.state.clock, clock_before)

    def test_they_are_not_counted_as_player_actions(self):
        for name, action in self.pending_actions():
            with self.subTest(action=name):
                actions_before = self.game.player_actions

                action()

                self.assertEqual(self.game.player_actions, actions_before)

    def test_they_consume_no_randomness(self):
        for name, action in self.pending_actions():
            with self.subTest(action=name):
                state_before = self.game.state.random_state()

                action()

                self.assertEqual(self.game.state.random_state(), state_before)

    def test_the_message_names_what_is_missing(self):
        self.assertIn("inventario", self.game.drop().message)
        self.assertIn("inventario", self.game.rewind().message)


if __name__ == "__main__":
    unittest.main()
