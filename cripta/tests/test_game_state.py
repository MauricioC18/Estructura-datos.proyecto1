import unittest

from model.game_state import GameState


class TestGameState(unittest.TestCase):

    def setUp(self):
        self.state = GameState(seed=2026)

    def test_clock_starts_at_zero(self):
        self.assertEqual(self.state.clock, 0)

    def test_clock_can_start_at_another_instant(self):
        loaded = GameState(seed=2026, clock=750)

        self.assertEqual(loaded.clock, 750)

    def test_clock_is_read_only(self):
        with self.assertRaises(AttributeError):
            self.state.clock = 500

    def test_sequence_numbers_start_at_zero_and_increase(self):
        numbers = [self.state.next_sequence() for _ in range(4)]

        self.assertEqual(numbers, [0, 1, 2, 3])

    def test_advance_clock_moves_forward(self):
        self.state.advance_clock_to(100)
        self.state.advance_clock_to(250)

        self.assertEqual(self.state.clock, 250)

    def test_advance_clock_to_same_instant_is_allowed(self):
        self.state.advance_clock_to(100)
        self.state.advance_clock_to(100)

        self.assertEqual(self.state.clock, 100)

    def test_advance_clock_backwards_is_rejected(self):
        self.state.advance_clock_to(200)

        with self.assertRaises(ValueError):
            self.state.advance_clock_to(199)

        self.assertEqual(self.state.clock, 200)

    def test_rewind_clock_moves_backwards(self):
        self.state.advance_clock_to(200)
        self.state.rewind_clock_to(100)

        self.assertEqual(self.state.clock, 100)

    def test_rewind_clock_forwards_is_rejected(self):
        self.state.advance_clock_to(100)

        with self.assertRaises(ValueError):
            self.state.rewind_clock_to(200)

        self.assertEqual(self.state.clock, 100)

    def test_clock_can_advance_again_after_a_rewind(self):
        self.state.advance_clock_to(200)
        self.state.rewind_clock_to(100)
        self.state.advance_clock_to(150)

        self.assertEqual(self.state.clock, 150)

    def test_sequence_numbers_do_not_go_back_after_a_rewind(self):
        before_rewind = [self.state.next_sequence() for _ in range(3)]
        self.state.advance_clock_to(200)
        self.state.rewind_clock_to(0)
        after_rewind = self.state.next_sequence()

        self.assertEqual(before_rewind, [0, 1, 2])
        self.assertEqual(after_rewind, 3)

    def test_same_seed_produces_the_same_sequence_of_rolls(self):
        other = GameState(seed=2026)

        rolls = [self.state.random_generator.randint(0, 4) for _ in range(10)]
        other_rolls = [other.random_generator.randint(0, 4) for _ in range(10)]

        self.assertEqual(rolls, other_rolls)

    def test_different_seeds_produce_different_rolls(self):
        other = GameState(seed=1807)

        rolls = [self.state.random_generator.randint(0, 4) for _ in range(20)]
        other_rolls = [other.random_generator.randint(0, 4) for _ in range(20)]

        self.assertNotEqual(rolls, other_rolls)

    def test_seed_is_available_for_the_save_file_and_the_replay_header(self):
        self.assertEqual(self.state.seed, 2026)


if __name__ == "__main__":
    unittest.main()
