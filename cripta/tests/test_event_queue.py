import random
import unittest

from model.event import Event
from structures.event_queue import EventQueue


class TestEventQueue(unittest.TestCase):

    def setUp(self):
        self.queue = EventQueue()

    def test_order_by_time(self):
        self.queue.push(Event(200, 1, "attack"))
        self.queue.push(Event(100, 2, "move"))

        self.assertEqual(self.queue.pop().time, 100)
        self.assertEqual(self.queue.pop().time, 200)

    def test_order_by_sequence(self):
        self.queue.push(Event(100, 5, "attack"))
        self.queue.push(Event(100, 2, "move"))

        self.assertEqual(self.queue.pop().sequence, 2)
        self.assertEqual(self.queue.pop().sequence, 5)

    def test_peek_does_not_remove_event(self):
        event = Event(100, 1, "move")
        self.queue.push(event)

        self.assertIs(self.queue.peek(), event)
        self.assertIs(self.queue.peek(), event)
        self.assertEqual(len(self.queue), 1)

    def test_cancel_event(self):
        event = Event(100, 1, "attack")
        self.queue.push(event)
        self.queue.cancel(event)

        self.assertIsNone(self.queue.pop())
        self.assertTrue(self.queue.is_empty())

    def test_empty_queue(self):
        self.assertIsNone(self.queue.peek())
        self.assertIsNone(self.queue.pop())
        self.assertTrue(self.queue.is_empty())

    def test_cancel_event_in_the_middle(self):
        first = Event(100, 1, "move")
        second = Event(200, 2, "attack")
        third = Event(300, 3, "wait")

        for event in (first, second, third):
            self.queue.push(event)

        self.queue.cancel(second)

        self.assertIs(self.queue.pop(), first)
        self.assertIs(self.queue.pop(), third)
        self.assertTrue(self.queue.is_empty())

    def test_cancel_all_events(self):
        events = [Event(time, time, "poison") for time in (300, 100, 200)]

        for event in events:
            self.queue.push(event)

        for event in events:
            self.queue.cancel(event)

        self.assertIsNone(self.queue.peek())
        self.assertTrue(self.queue.is_empty())
        self.assertEqual(len(self.queue), 0)

    def test_push_already_cancelled_event(self):
        cancelled = Event(50, 1, "trap", cancelled=True)
        active = Event(100, 2, "move")

        self.queue.push(cancelled)
        self.queue.push(active)

        self.assertIs(self.queue.pop(), active)
        self.assertTrue(self.queue.is_empty())

    def test_total_order_with_many_events(self):
        generator = random.Random(2026)
        events = []

        for sequence in range(500):
            time = generator.randrange(0, 50)
            events.append(Event(time, sequence, "tick"))

        shuffled = list(events)
        generator.shuffle(shuffled)

        for event in shuffled:
            self.queue.push(event)

        extracted = []

        while not self.queue.is_empty():
            extracted.append(self.queue.pop())

        self.assertEqual(len(extracted), len(events))

        for previous, current in zip(extracted, extracted[1:]):
            self.assertLess(
                (previous.time, previous.sequence),
                (current.time, current.sequence),
            )

    def test_interleaved_push_pop_keeps_order(self):
        self.queue.push(Event(300, 1, "move"))
        self.queue.push(Event(100, 2, "attack"))

        self.assertEqual(self.queue.pop().time, 100)

        self.queue.push(Event(150, 3, "poison"))
        self.queue.push(Event(150, 4, "poison"))

        self.assertEqual(self.queue.pop().sequence, 3)
        self.assertEqual(self.queue.pop().sequence, 4)
        self.assertEqual(self.queue.pop().time, 300)


if __name__ == "__main__":
    unittest.main()
