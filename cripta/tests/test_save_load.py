import unittest

from model.effects import POISON
from model.enemy import Enemy
from model.game import ACTOR_ACTION, DEFEAT, IN_PROGRESS, VICTORY, Game
from model.event import Event
from model.game_state import GameState
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from structures.trail import PlayerTrail


def make_map():
    rooms = [Room(number, f"Sala {number}") for number in (1, 2, 3)]

    for room in rooms:
        room.content_loaded = True

    first = Door(1, 2)
    rooms[0].add_exit(Exit("N", 2, first))
    rooms[1].add_exit(Exit("S", 1, first))

    second = Door(2, 3)
    rooms[1].add_exit(Exit("N", 3, second))
    rooms[2].add_exit(Exit("S", 2, second))

    room_map = RoomMap()

    for room in rooms:
        room_map.add(room)

    return room_map


def make_player(room_id=1):
    return Player("p-1", "Heroe", 500, 6, 2, 100, room_id)


def make_enemy(actor_id="e-1", room_id=1, speed=150):
    return Enemy(actor_id, "Rata gigante", 20, 4, 1, speed, room_id, Enemy.GUARDIAN)


def played_game(actions=2):
    """Una partida en curso, con enemigos activos y un veneno encima."""
    room_map = make_map()
    game = Game(
        GameState(seed=2026),
        make_player(),
        [make_enemy()],
        room_map=room_map,
        exit_room_id=3,
        trail=PlayerTrail(),
    )
    game.apply_poison(game.player, 2)

    for _ in range(actions):
        game.wait()

    return game


def save(game):
    """Lo que el archivo de §4.10 guardaria de una partida."""
    return {
        "clock": game.state.clock,
        "sequence_counter": game.state.sequence_counter,
        "random_state": game.state.random_state(),
        "events": game.events.active_events(),
        "effects": list(game.effects),
        "torch_lit": game.torch_lit,
        "result": game.result,
        "player_actions": game.player_actions,
        "enemies_defeated": game.enemies_defeated,
    }


def load(saved, game):
    """Reconstruye la partida a partir de lo guardado."""
    state = GameState(seed=game.state.seed)
    state.restore(
        saved["clock"], saved["sequence_counter"], saved["random_state"]
    )

    return Game.load(
        state,
        game.player,
        game.enemies,
        game.room_map,
        game.exit_room_id,
        game.trail,
        events=saved["events"],
        effects=saved["effects"],
        torch_lit=saved["torch_lit"],
        result=saved["result"],
        player_actions=saved["player_actions"],
        enemies_defeated=saved["enemies_defeated"],
    )


def rebuilt_from(saved, game):
    """Carga la partida con objetos nuevos, como haria el archivo de §4.10.

    El jugador, los enemigos y el mapa se arman de cero con los valores
    guardados, y los eventos se reapuntan a los actores nuevos por su
    identificador. Es lo que hace el cargado real; aqui se imita para poder
    comprobar que la partida cargada es la misma.
    """
    player = make_player(game.player.room_id)
    player.health = game.player.health
    player.speed = game.player.speed

    enemies = []

    for old in game.enemies:
        enemy = make_enemy(old.actor_id, old.room_id, old.speed)
        enemy.health = old.health
        enemy.is_active = old.is_active
        enemies.append(enemy)

    room_map = make_map()
    trail = PlayerTrail()

    for room_id in game.room_map.room_ids():
        time = game.trail.time_at(room_id)

        if time is not None:
            trail.mark(room_id, time)

    by_id = {}

    for enemy in enemies:
        by_id[enemy.actor_id] = enemy

    events = []

    for old in saved["events"]:
        actor = None

        if old.actor is not None:
            actor = player if old.actor is game.player else by_id[old.actor.actor_id]

        events.append(
            Event(
                old.time,
                old.sequence,
                old.event_type,
                actor,
                amount=old.amount,
                room_id=old.room_id,
                direction=old.direction,
                instance_id=old.instance_id,
            )
        )

    state = GameState(seed=game.state.seed)
    state.restore(
        saved["clock"], saved["sequence_counter"], saved["random_state"]
    )

    return Game.load(
        state,
        player,
        enemies,
        room_map,
        game.exit_room_id,
        trail,
        events=events,
        torch_lit=saved["torch_lit"],
        result=saved["result"],
        player_actions=saved["player_actions"],
        enemies_defeated=saved["enemies_defeated"],
    )


class TestLoadRestoresTheState(unittest.TestCase):

    def setUp(self):
        self.original = played_game()
        self.loaded = load(save(self.original), self.original)

    def test_the_clock_comes_back(self):
        self.assertEqual(self.loaded.state.clock, self.original.state.clock)

    def test_the_counters_come_back(self):
        self.assertEqual(
            self.loaded.player_actions, self.original.player_actions
        )
        self.assertEqual(
            self.loaded.enemies_defeated, self.original.enemies_defeated
        )

    def test_the_pending_events_come_back_in_the_same_order(self):
        def order(game):
            agenda = []
            copy = list(game.events.active_events())

            for event in sorted(copy, key=lambda e: (e.time, e.sequence)):
                agenda.append((event.time, event.sequence, event.event_type))

            return agenda

        self.assertEqual(order(self.loaded), order(self.original))

    def test_each_actor_points_at_its_pending_action(self):
        for event in self.loaded.events.active_events():
            if event.event_type == ACTOR_ACTION:
                self.assertIs(event.actor.scheduled_event, event)

    def test_the_active_effects_come_back(self):
        self.assertEqual(
            [effect.name for effect in self.loaded.effects],
            [effect.name for effect in self.original.effects],
        )
        self.assertIn(POISON, [effect.name for effect in self.loaded.effects])

    def test_the_result_comes_back(self):
        self.assertEqual(self.loaded.result, self.original.result)


class TestLoadDoesNotStartANewGame(unittest.TestCase):

    def test_it_does_not_schedule_an_extra_player_action(self):
        original = played_game()
        before = len(original.events.active_events())

        loaded = load(save(original), original)

        self.assertEqual(len(loaded.events.active_events()), before)

    def test_it_does_not_move_the_clock_back_to_zero(self):
        original = played_game()

        loaded = load(save(original), original)

        self.assertGreater(loaded.state.clock, 0)

    def test_it_does_not_reactivate_the_enemies(self):
        original = played_game()
        saved = save(original)
        events_before = len(saved["events"])

        loaded = load(saved, original)

        self.assertEqual(len(loaded.events.active_events()), events_before)

    def test_a_new_game_does_start(self):
        """El constructor normal sigue haciendo el trabajo de inicio."""
        room_map = make_map()
        enemy = make_enemy()
        game = Game(
            GameState(seed=2026),
            make_player(),
            [enemy],
            room_map=room_map,
            trail=PlayerTrail(),
        )

        self.assertTrue(enemy.is_active)
        self.assertEqual(game.state.clock, 0)


class TestTheLoadedGameKeepsPlaying(unittest.TestCase):

    def test_it_continues_exactly_like_the_original(self):
        """La prueba de fondo del guardado.

        La partida cargada se arma con objetos NUEVOS, como haria el archivo de
        verdad, no con los mismos que usaba la original. Despues se juegan las
        mismas acciones en las dos y tienen que terminar iguales.
        """
        original = played_game()
        loaded = rebuilt_from(save(original), original)

        for _ in range(3):
            loaded.wait()
            original.wait()

        self.assertEqual(loaded.state.clock, original.state.clock)
        self.assertEqual(loaded.player.health, original.player.health)
        self.assertEqual(loaded.player_actions, original.player_actions)
        self.assertEqual(
            [enemy.health for enemy in loaded.enemies],
            [enemy.health for enemy in original.enemies],
        )
        self.assertEqual(
            list(loaded.messages)[-3:], list(original.messages)[-3:]
        )

    def test_the_poison_keeps_hurting_after_loading(self):
        original = played_game(actions=1)
        health_before = original.player.health
        loaded = load(save(original), original)

        for _ in range(3):
            loaded.wait()

        self.assertLess(loaded.player.health, health_before)

    def test_a_loaded_game_can_be_won(self):
        original = played_game(actions=1)
        loaded = load(save(original), original)

        loaded.move("N")
        loaded.move("N")

        self.assertEqual(loaded.result, VICTORY)

    def test_a_finished_game_comes_back_finished(self):
        original = played_game(actions=1)
        original.result = DEFEAT

        loaded = load(save(original), original)

        self.assertEqual(loaded.result, DEFEAT)
        self.assertTrue(loaded.is_over)
        self.assertFalse(loaded.wait().accepted)

    def test_an_empty_save_starts_from_the_defaults(self):
        state = GameState(seed=1)
        game = Game.load(state, make_player(), room_map=make_map())

        self.assertEqual(game.result, IN_PROGRESS)
        self.assertEqual(game.player_actions, 0)
        self.assertEqual(game.effects, [])
        self.assertTrue(game.events.is_empty())



class TestEffectsAreRebuiltFromTheAgenda(unittest.TestCase):
    """El archivo no necesita guardar los efectos: se deducen de la agenda."""

    def test_a_loaded_poison_shows_as_an_active_effect(self):
        original = played_game(actions=1)
        loaded = rebuilt_from(save(original), original)

        self.assertIn(
            POISON, [effect.name for effect in loaded.visible_state().effects]
        )

    def test_an_antidote_can_cancel_a_loaded_poison(self):
        """Sin enemigos, para que lo unico que pueda quitar vida sea el veneno."""
        original = Game(
            GameState(seed=2026),
            make_player(),
            None,
            room_map=make_map(),
            trail=PlayerTrail(),
        )
        original.apply_poison(original.player, 2)
        original.wait()

        loaded = rebuilt_from(save(original), original)

        self.assertTrue(loaded.cancel_poison(loaded.player))

        health = loaded.player.health

        for _ in range(6):
            loaded.wait()

        self.assertEqual(loaded.player.health, health)

    def test_without_the_antidote_a_loaded_poison_keeps_hurting(self):
        original = Game(
            GameState(seed=2026),
            make_player(),
            None,
            room_map=make_map(),
            trail=PlayerTrail(),
        )
        original.apply_poison(original.player, 2)
        original.wait()

        loaded = rebuilt_from(save(original), original)
        health = loaded.player.health

        for _ in range(6):
            loaded.wait()

        self.assertLess(loaded.player.health, health)

    def test_without_pending_pulses_there_is_no_effect(self):
        room_map = make_map()
        game = Game.load(GameState(seed=1), make_player(), room_map=room_map)

        self.assertEqual(game.effects, [])

    def test_explicit_effects_win_over_the_deduced_ones(self):
        original = played_game(actions=1)
        saved = save(original)
        state = GameState(seed=2026)
        state.restore(
            saved["clock"], saved["sequence_counter"], saved["random_state"]
        )

        loaded = Game.load(
            state,
            original.player,
            original.enemies,
            original.room_map,
            events=saved["events"],
            effects=[],
        )

        self.assertEqual(loaded.effects, [])


if __name__ == "__main__":
    unittest.main()
