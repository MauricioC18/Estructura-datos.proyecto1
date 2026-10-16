import unittest

from model.enemy import Enemy
from model.event import Event
from model.game import Game
from model.game_state import GameState
from model.trap import Trap
from structures.history import (
    MAX_REWIND_ACTIONS,
    CallbackChange,
    History,
    ReversibleEventQueue,
    use_rewind_scroll,
)
from structures.inventory import Inventory
from structures.sorting import sort
from structures.trail import PlayerTrail
from tests.objetos_persona3 import (
    make_item,
    make_player,
    make_scroll,
    make_weapon,
    names,
)


class Holder:
    def __init__(self, value):
        self.value = value


def advance(state, time):
    state.advance_clock_to(time)


def agenda_snapshot(queue):
    events = sort(queue.active_events(), key=lambda event: (event.time, event.sequence))
    return [(event.time, event.sequence, event.event_type, event.actor) for event in events]


class TestHistoryBasics(unittest.TestCase):
    def setUp(self):
        self.state = GameState(seed=1)
        self.history = History(self.state)

    def test_max_is_5(self):
        self.assertEqual(MAX_REWIND_ACTIONS, 5)
        self.assertEqual(self.history.max_actions, 5)

    def test_undo_without_actions(self):
        self.assertFalse(self.history.undo())

    def test_nothing_recorded_before_first_action(self):
        holder = Holder(10)
        self.history.assign(holder, "value", 5)
        self.assertEqual(self.history.recorded_changes(), 0)
        self.assertEqual(holder.value, 5)

    def test_undo_in_reverse_order(self):
        holder = Holder(10)
        self.history.begin_action()
        self.history.assign(holder, "value", 8)
        self.history.assign(holder, "value", 3)
        self.assertTrue(self.history.undo())
        self.assertEqual(holder.value, 10)

    def test_restores_the_clock(self):
        advance(self.state, 100)
        self.history.begin_action()
        advance(self.state, 250)
        self.history.undo()
        self.assertEqual(self.state.clock, 100)

    def test_sequence_counter_is_not_restored(self):
        self.history.begin_action()
        self.state.next_sequence()
        self.state.next_sequence()
        self.history.undo()
        self.assertEqual(self.state.sequence_counter, 2)

    def test_discards_oldest_beyond_5(self):
        holder = Holder(0)
        for value in range(1, 8):
            self.history.begin_action()
            self.history.assign(holder, "value", value)
        self.assertEqual(self.history.available_actions(), 5)
        for _ in range(5):
            self.assertTrue(self.history.undo())
        self.assertEqual(holder.value, 2)
        self.assertFalse(self.history.undo())

    def test_does_not_record_while_undoing(self):
        holder = Holder(10)

        def inverse_that_records(value):
            self.history.assign(holder, "value", value)

        self.history.begin_action()
        self.history.assign(holder, "value", 4)
        self.history.record(CallbackChange(inverse_that_records, 99))
        self.history.undo()
        self.assertEqual(holder.value, 10)
        self.assertEqual(self.history.recorded_changes(), 0)

    def test_works_with_properties(self):
        player = make_player()
        self.history.begin_action()
        self.history.assign(player, "health", 12)
        self.history.undo()
        self.assertEqual(player.health, 30)

    def test_list_helpers(self):
        floor = ["daga", "pocion"]
        self.history.begin_action()
        self.history.list_append(floor, "llave")
        self.assertEqual(self.history.list_pop(floor, 0), "daga")
        self.history.undo()
        self.assertEqual(floor, ["daga", "pocion"])

    def test_clear(self):
        self.history.begin_action()
        self.history.clear()
        self.assertFalse(self.history.can_undo())

    def test_statement_example(self):
        player = make_player()
        rat = Enemy("e-201", "Rata gigante", 12, 5, 1, 150, 2, Enemy.TRACKER)
        trap = Trap("t-17", "trp_dardos", "Dardos", 4, 300, 2, armed=False)
        trail = PlayerTrail(self.history)
        trail.mark(2, 60)
        advance(self.state, 100)

        self.history.begin_action()
        self.history.assign(rat, "health", rat.health - 7)
        trail.mark(2, 100)
        advance(self.state, 120)
        self.history.assign(player, "health", player.health - 2)
        advance(self.state, 150)
        self.history.assign(player, "health", player.health - 4)
        advance(self.state, 180)
        self.history.assign(trap, "armed", True)
        advance(self.state, 200)

        self.history.undo()
        self.assertEqual(self.state.clock, 100)
        self.assertEqual(rat.health, 12)
        self.assertEqual(player.health, 30)
        self.assertFalse(trap.armed)
        self.assertEqual(trail.time_at(2), 60)


class TestReversibleEventQueue(unittest.TestCase):
    def setUp(self):
        self.state = GameState(seed=7)
        self.history = History(self.state)
        self.queue = ReversibleEventQueue(self.history)

    def event(self, time, actor=None, event_type="actor_action"):
        return Event(time, self.state.next_sequence(), event_type, actor)

    def test_undo_push(self):
        self.queue.push(self.event(10))
        before = agenda_snapshot(self.queue)
        self.history.begin_action()
        self.queue.push(self.event(5))
        self.history.undo()
        self.assertEqual(agenda_snapshot(self.queue), before)

    def test_undo_pop(self):
        first = self.event(5)
        self.queue.push(first)
        self.queue.push(self.event(10))
        self.history.begin_action()
        self.assertIs(self.queue.pop(), first)
        self.history.undo()
        self.assertIs(self.queue.pop(), first)

    def test_undo_cancel_after_lazy_discard(self):
        early = self.event(5)
        late = self.event(10)
        self.queue.push(early)
        self.queue.push(late)
        self.history.begin_action()
        self.queue.cancel(early)
        self.assertIs(self.queue.pop(), late)
        self.history.undo()
        self.assertIs(self.queue.pop(), early)
        self.assertIs(self.queue.pop(), late)

    def test_restores_scheduled_event(self):
        actor = make_player()
        event = self.event(5, actor)
        actor.scheduled_event = event
        self.queue.push(event)
        self.history.begin_action()
        self.queue.pop()
        actor.scheduled_event = None
        self.history.undo()
        self.assertIs(actor.scheduled_event, event)


class TestReversibleQueueWithTheEngine(unittest.TestCase):
    """La agenda y el reloj se revierten con el motor real, sin modificarlo."""

    def setUp(self):
        self.state = GameState(seed=3)
        self.history = History(self.state)
        self.player = make_player()
        self.rat = Enemy("e-1", "Rata", 50, 1, 1, 150, 1, Enemy.GUARDIAN)
        self.game = Game(
            self.state,
            self.player,
            [self.rat],
            event_queue=ReversibleEventQueue(self.history),
        )

    def test_wait_is_reverted(self):
        clock = self.state.clock
        agenda = agenda_snapshot(self.game.events)
        rat_event = self.rat.scheduled_event
        self.history.begin_action()
        self.game.wait()
        self.history.undo()
        self.assertEqual(self.state.clock, clock)
        self.assertEqual(agenda_snapshot(self.game.events), agenda)
        self.assertIs(self.rat.scheduled_event, rat_event)
        self.assertIsNone(self.player.scheduled_event)

    def test_same_action_after_undo_gives_same_times(self):
        self.history.begin_action()
        self.game.wait()
        first_clock = self.state.clock
        self.history.undo()
        self.history.begin_action()
        self.game.wait()
        self.assertEqual(self.state.clock, first_clock)

    def test_two_undos_in_a_row(self):
        clock = self.state.clock
        agenda = agenda_snapshot(self.game.events)
        for _ in range(2):
            self.history.begin_action()
            self.game.wait()
        self.history.undo()
        self.history.undo()
        self.assertEqual(self.state.clock, clock)
        self.assertEqual(agenda_snapshot(self.game.events), agenda)

    def test_speed_change_is_reverted(self):
        old_event = self.rat.scheduled_event
        agenda = agenda_snapshot(self.game.events)
        self.history.begin_action()
        self.history.assign(self.rat, "speed", self.rat.speed)
        self.game.change_actor_speed(self.rat, 300)
        self.history.undo()
        self.assertIs(self.rat.scheduled_event, old_event)
        self.assertEqual(self.rat.speed, 150)
        self.assertEqual(agenda_snapshot(self.game.events), agenda)

    def test_cancelling_a_dead_actor_is_reverted(self):
        old_event = self.rat.scheduled_event
        self.history.begin_action()
        self.game.events.cancel(self.rat.scheduled_event)
        self.rat.scheduled_event = None
        self.history.undo()
        self.assertIs(self.rat.scheduled_event, old_event)
        self.assertFalse(old_event.cancelled)


class TestReversibleInventory(unittest.TestCase):
    def setUp(self):
        self.history = History(GameState(seed=1))
        self.player = make_player()
        self.inventory = Inventory(5, self.history)
        for name in ("a", "b", "c"):
            self.inventory.pick_up(make_item(name))
        self.inventory.go_to_start()

    def test_undo_pick_up(self):
        self.history.begin_action()
        self.inventory.pick_up(make_item("d"))
        self.history.undo()
        self.assertEqual(names(self.inventory), ["a", "b", "c"])

    def test_undo_drop_restores_position(self):
        self.inventory.next()
        self.history.begin_action()
        self.inventory.drop_current(self.player)
        self.history.undo()
        self.assertEqual(names(self.inventory), ["a", "b", "c"])
        self.assertEqual(self.inventory.current().name, "b")

    def test_undo_pick_up_moves_cursor_off_the_item(self):
        self.history.begin_action()
        self.inventory.pick_up(make_item("d"))
        self.assertEqual(self.inventory.current().name, "d")
        self.history.undo()
        self.assertEqual(self.inventory.current().name, "c")

    def test_undo_drop_first(self):
        self.history.begin_action()
        self.inventory.drop_current(self.player)
        self.history.undo()
        self.assertEqual(names(self.inventory), ["a", "b", "c"])

    def test_undo_equip_restores_order_and_equipment(self):
        inventory = Inventory(5, self.history)
        inventory.pick_up(make_item("pocion"))
        inventory.pick_up(make_weapon("daga"))
        inventory.pick_up(make_weapon("hacha"))
        inventory.go_to_start()
        inventory.next()
        self.history.begin_action()
        inventory.equip_current(self.player)
        inventory.next()
        inventory.next()
        self.history.begin_action()
        inventory.equip_current(self.player)
        self.assertEqual(names(inventory), ["hacha", "daga", "pocion"])
        self.history.undo()
        self.assertEqual(names(inventory), ["daga", "pocion", "hacha"])
        self.assertEqual(self.player.equipped_weapon.name, "daga")
        self.history.undo()
        self.assertEqual(names(inventory), ["pocion", "daga", "hacha"])
        self.assertIsNone(self.player.equipped_weapon)

    def test_undo_drop_of_equipped_weapon(self):
        inventory = Inventory(5, self.history)
        inventory.pick_up(make_weapon("daga"))
        inventory.equip_current(self.player)
        self.history.begin_action()
        inventory.drop_current(self.player)
        self.history.undo()
        self.assertEqual(self.player.equipped_weapon.name, "daga")
        self.assertEqual(names(inventory), ["daga"])


class TestRewindScroll(unittest.TestCase):
    def setUp(self):
        self.state = GameState(seed=1)
        self.history = History(self.state)
        self.inventory = Inventory(10, self.history)
        self.player = make_player()

    def act(self, health):
        self.history.begin_action()
        self.history.assign(self.player, "health", health)

    def test_no_scroll(self):
        self.act(20)
        self.assertFalse(use_rewind_scroll(self.inventory, self.history))
        self.assertEqual(self.player.health, 20)

    def test_no_history_keeps_the_scroll(self):
        self.inventory.pick_up(make_scroll())
        self.assertFalse(use_rewind_scroll(self.inventory, self.history))
        self.assertEqual(self.inventory.scroll_count(), 1)

    def test_rewinds_and_consumes(self):
        self.inventory.pick_up(make_scroll())
        self.act(20)
        self.assertTrue(use_rewind_scroll(self.inventory, self.history))
        self.assertEqual(self.player.health, 30)
        self.assertEqual(self.inventory.scroll_count(), 0)

    def test_picking_a_scroll_in_the_interval_is_not_reverted(self):
        self.inventory.pick_up(make_scroll("p1"))
        self.history.begin_action()
        self.inventory.pick_up(make_scroll("p2"))
        self.history.assign(self.player, "health", 25)
        self.assertTrue(use_rewind_scroll(self.inventory, self.history))
        self.assertEqual(self.player.health, 30)
        self.assertEqual(self.inventory.scroll_count(), 1)

    def test_dropping_a_scroll_in_the_interval_is_not_reverted(self):
        self.inventory.pick_up(make_scroll("p1"))
        self.inventory.pick_up(make_scroll("p2"))
        self.inventory.next()
        self.history.begin_action()
        self.inventory.drop_current(self.player)
        self.assertTrue(use_rewind_scroll(self.inventory, self.history))
        self.assertEqual(self.inventory.scroll_count(), 0)

    def test_two_scrolls_in_a_row(self):
        self.inventory.pick_up(make_scroll())
        self.inventory.pick_up(make_scroll())
        self.act(20)
        self.act(10)
        self.assertTrue(use_rewind_scroll(self.inventory, self.history))
        self.assertEqual(self.player.health, 20)
        self.assertTrue(use_rewind_scroll(self.inventory, self.history))
        self.assertEqual(self.player.health, 30)

    def test_never_more_than_5(self):
        for _ in range(7):
            self.inventory.pick_up(make_scroll())
        for health in range(29, 22, -1):
            self.act(health)
        uses = 0
        while use_rewind_scroll(self.inventory, self.history):
            uses += 1
        self.assertEqual(uses, 5)
        self.assertEqual(self.player.health, 28)
        self.assertEqual(self.inventory.scroll_count(), 2)

    def test_neighbour_scroll_left_without_being_recorded(self):
        self.inventory.pick_up(make_item("a"))
        self.inventory.pick_up(make_scroll("p"))
        self.inventory.pick_up(make_item("b"))
        self.inventory.pick_up(make_scroll("q"))
        self.inventory.go_to_start()
        self.inventory.next()
        self.inventory.next()
        self.history.begin_action()
        self.inventory.drop_current(self.player)
        self.history.begin_action()
        self.inventory.go_to_start()
        self.inventory.next()
        self.inventory.drop_current(self.player)
        self.history.undo()
        self.history.undo()
        self.assertEqual(names(self.inventory), ["a", "b", "q"])


if __name__ == "__main__":
    unittest.main()
