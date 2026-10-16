import unittest

from model.game import Game
from model.game_state import GameState
from model.player import Player
from structures.circular_log import LOG_CAPACITY, CircularBuffer, CircularLog


class TestCircularBuffer(unittest.TestCase):
    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            CircularBuffer(0)

    def test_empty(self):
        buffer = CircularBuffer(3)
        self.assertTrue(buffer.is_empty())
        self.assertEqual(list(buffer), [])
        with self.assertRaises(IndexError):
            buffer.pop_last()
        with self.assertRaises(IndexError):
            buffer.last()

    def test_fill_to_capacity(self):
        buffer = CircularBuffer(3)
        for value in (1, 2, 3):
            self.assertIsNone(buffer.append(value))
        self.assertTrue(buffer.is_full())
        self.assertEqual(list(buffer), [1, 2, 3])

    def test_overwrites_the_oldest(self):
        buffer = CircularBuffer(3)
        for value in (1, 2, 3):
            buffer.append(value)
        self.assertEqual(buffer.append(4), 1)
        self.assertEqual(buffer.append(5), 2)
        self.assertEqual(list(buffer), [3, 4, 5])
        self.assertEqual(len(buffer), 3)

    def test_pop_last_after_wrapping(self):
        buffer = CircularBuffer(3)
        for value in range(1, 6):
            buffer.append(value)
        self.assertEqual(buffer.pop_last(), 5)
        self.assertEqual(buffer.last(), 4)
        buffer.append(9)
        self.assertEqual(list(buffer), [3, 4, 9])

    def test_memory_stays_constant(self):
        buffer = CircularBuffer(20)
        for value in range(10000):
            buffer.append(value)
        self.assertEqual(len(buffer._slots), 20)
        self.assertEqual(list(buffer), list(range(9980, 10000)))

    def test_clear(self):
        buffer = CircularBuffer(2)
        buffer.append(1)
        buffer.clear()
        self.assertTrue(buffer.is_empty())
        buffer.append(7)
        self.assertEqual(list(buffer), [7])


class TestCircularLog(unittest.TestCase):
    def test_default_capacity_is_20(self):
        self.assertEqual(LOG_CAPACITY, 20)
        self.assertEqual(CircularLog().capacity, 20)

    def test_keeps_the_last_20_in_order(self):
        log = CircularLog()
        for index in range(25):
            log.append(f"m{index}")
        messages = list(log)
        self.assertEqual(len(messages), 20)
        self.assertEqual(messages[0], "m5")
        self.assertEqual(messages[-1], "m24")

    def test_exactly_20(self):
        log = CircularLog()
        for index in range(20):
            log.append(f"m{index}")
        self.assertEqual(list(log)[0], "m0")

    def test_stores_text(self):
        log = CircularLog()
        log.append(42)
        self.assertEqual(list(log), ["42"])

    def test_plugs_into_game(self):
        player = Player("p-1", "Heroe", 30, 6, 2, 100, 1)
        log = CircularLog()
        game = Game(GameState(seed=1), player, message_log=log)
        for _ in range(30):
            game.wait()
        state = game.visible_state()
        self.assertEqual(len(state.messages), 20)
        self.assertEqual(len(log._slots), 20)


if __name__ == "__main__":
    unittest.main()
