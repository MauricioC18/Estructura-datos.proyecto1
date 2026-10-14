import unittest

from model.actor import Actor
from model.event import Event


def make_actor(speed=100, max_health=30, health=None):
    return Actor(
        actor_id="e-201",
        name="Rata gigante",
        max_health=max_health,
        attack=5,
        defense=1,
        speed=speed,
        room_id=2,
        health=health,
    )


class TestActorInterval(unittest.TestCase):

    def test_reference_speed_pays_the_full_cost(self):
        actor = make_actor(speed=100)

        self.assertEqual(actor.interval_for(100), 100)

    def test_speed_150_matches_the_statement_example(self):
        actor = make_actor(speed=150)

        self.assertEqual(actor.interval_for(100), 66)

    def test_slower_actor_takes_longer(self):
        actor = make_actor(speed=50)

        self.assertEqual(actor.interval_for(100), 200)

    def test_cheap_action_with_fast_actor(self):
        actor = make_actor(speed=150)

        self.assertEqual(actor.interval_for(25), 16)

    def test_interval_is_never_zero(self):
        actor = make_actor(speed=10000)

        self.assertEqual(actor.interval_for(25), 1)

    def test_next_time_is_measured_from_the_current_instant(self):
        actor = make_actor(speed=150)

        self.assertEqual(actor.next_time_after(0, 100), 66)
        self.assertEqual(actor.next_time_after(66, 100), 132)

    def test_player_sequence_from_the_statement_example(self):
        player = make_actor(speed=100)

        move = player.next_time_after(0, 100)
        pick_up = player.next_time_after(move, 25)
        equip = player.next_time_after(pick_up, 50)

        self.assertEqual([move, pick_up, equip], [100, 125, 175])


class TestActorHealth(unittest.TestCase):

    def test_health_starts_at_maximum_by_default(self):
        actor = make_actor(max_health=30)

        self.assertEqual(actor.health, 30)
        self.assertTrue(actor.is_alive)

    def test_instance_can_start_wounded(self):
        actor = make_actor(max_health=12, health=7)

        self.assertEqual(actor.health, 7)

    def test_healing_never_exceeds_the_maximum(self):
        actor = make_actor(max_health=30, health=28)

        actor.heal(10)

        self.assertEqual(actor.health, 30)

    def test_damage_never_goes_below_zero(self):
        actor = make_actor(max_health=30, health=4)

        actor.take_damage(9)

        self.assertEqual(actor.health, 0)

    def test_actor_dies_when_health_reaches_zero(self):
        actor = make_actor(max_health=30, health=4)

        actor.take_damage(4)

        self.assertFalse(actor.is_alive)

    def test_initial_health_above_the_maximum_is_clamped(self):
        actor = make_actor(max_health=12, health=50)

        self.assertEqual(actor.health, 12)


class TestActorValidation(unittest.TestCase):

    def test_speed_zero_is_rejected(self):
        with self.assertRaises(ValueError):
            make_actor(speed=0)

    def test_negative_speed_is_rejected(self):
        with self.assertRaises(ValueError):
            make_actor(speed=-100)

    def test_max_health_zero_is_rejected(self):
        with self.assertRaises(ValueError):
            make_actor(max_health=0)

    def test_empty_actor_id_is_rejected(self):
        with self.assertRaises(ValueError):
            Actor(
                actor_id="",
                name="Sin nombre",
                max_health=10,
                attack=1,
                defense=0,
                speed=100,
                room_id=1,
            )


class TestActorSpeedChange(unittest.TestCase):

    def setUp(self):
        self.actor = make_actor(speed=100)
        self.actor.scheduled_event = Event(300, 7, "actor_action", "e-201")

    def test_speeding_up_brings_the_next_action_closer(self):
        rescheduled = self.actor.change_speed(250, 200)

        self.assertEqual(rescheduled, 275)
        self.assertEqual(self.actor.speed, 200)

    def test_slowing_down_pushes_the_next_action_away(self):
        rescheduled = self.actor.change_speed(250, 50)

        self.assertEqual(rescheduled, 350)

    def test_rescheduled_time_always_moves_forward(self):
        self.actor.scheduled_event = Event(251, 8, "actor_action", "e-201")

        rescheduled = self.actor.change_speed(250, 10000)

        self.assertEqual(rescheduled, 251)

    def test_speed_change_without_a_pending_action(self):
        self.actor.scheduled_event = None

        rescheduled = self.actor.change_speed(250, 200)

        self.assertIsNone(rescheduled)
        self.assertEqual(self.actor.speed, 200)

    def test_rescale_uses_the_previous_speed_not_the_new_one(self):
        rescheduled = self.actor.change_speed(250, 200)

        wrong_if_new_speed_were_used = 250 + max(1, 50 * 200 // 200)

        self.assertNotEqual(rescheduled, wrong_if_new_speed_were_used)
        self.assertEqual(rescheduled, 275)

    def test_the_pending_event_is_not_modified(self):
        self.actor.change_speed(250, 200)

        self.assertEqual(self.actor.scheduled_event.time, 300)
        self.assertEqual(self.actor.scheduled_event.sequence, 7)


if __name__ == "__main__":
    unittest.main()
