import unittest

from model.enemy import Enemy
from model.game import DEFEAT, IN_PROGRESS, VICTORY, Game
from model.game_state import GameState
from model.item import Item
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from model.trap import Trap
from structures.circular_log import CircularLog
from structures.trail import PlayerTrail


OPPOSITE = {"N": "S", "S": "N", "E": "O", "O": "E"}


def make_player(speed=100, max_health=100, defense=10, room_id=1):
    return Player(
        actor_id="p-1",
        name="Heroe",
        max_health=max_health,
        attack=6,
        defense=defense,
        speed=speed,
        room_id=room_id,
    )


def make_key(type_id, instance_id="itm-1"):
    """Una llave como las que entrega el Traductor.

    El campo `opens` lleva a proposito un valor que no es el id de la llave,
    igual que en los datos reales, donde la llave negra trae
    `abre: "puerta_salida"`. Lo que debe coincidir con la puerta es el type_id.
    """
    return Item(
        instance_id=instance_id,
        type_id=type_id,
        name="Llave",
        item_class=Item.KEY,
        weight=1,
        value=5,
        opens="nombre_de_la_puerta",
    )


def make_trap(instance_id="t-1", room_id=2, damage=4, rearm_interval=300):
    return Trap(
        instance_id=instance_id,
        type_id="trp_dardos",
        name="Dardos en la pared",
        damage=damage,
        rearm_interval=rearm_interval,
        room_id=room_id,
    )


def connect(room_a, room_b, direction, closed=False, key_id=None, auto_close=None):
    """Une dos salas con una sola puerta compartida, como hace el bloque 2."""
    door = Door(
        room_a.room_id,
        room_b.room_id,
        closed=closed,
        key_id=key_id,
        auto_close=auto_close,
    )
    room_a.add_exit(Exit(direction, room_b.room_id, door))
    room_b.add_exit(Exit(OPPOSITE[direction], room_a.room_id, door))

    return door


def make_map(door_between_2_and_3_closed=False, key_id=None, auto_close=None):
    """Tres salas en linea: 1 -N-> 2 -N-> 3."""
    rooms = [
        Room(1, "Entrada derruida"),
        Room(2, "Pasillo de las urnas"),
        Room(3, "Camara final"),
    ]

    for room in rooms:
        room.content_loaded = True

    connect(rooms[0], rooms[1], "N")
    door = connect(
        rooms[1],
        rooms[2],
        "N",
        closed=door_between_2_and_3_closed,
        key_id=key_id,
        auto_close=auto_close,
    )

    room_map = RoomMap()

    for room in rooms:
        room_map.add(room)

    return room_map, door


def make_game(room_map, player=None, enemies=None, exit_room_id=None, seed=2026):
    return Game(
        GameState(seed=seed),
        make_player() if player is None else player,
        enemies,
        room_map=room_map,
        exit_room_id=exit_room_id,
    )


class TestMovement(unittest.TestCase):

    def test_moving_through_an_open_exit(self):
        room_map, _ = make_map()
        game = make_game(room_map)

        result = game.move("N")

        self.assertTrue(result.accepted)
        self.assertEqual(game.player.room_id, 2)

    def test_moving_costs_one_hundred(self):
        room_map, _ = make_map()
        game = make_game(room_map)

        game.move("N")

        self.assertEqual(game.state.clock, 100)

    def test_moving_counts_as_a_player_action(self):
        room_map, _ = make_map()
        game = make_game(room_map)

        game.move("N")

        self.assertEqual(game.player_actions, 1)

    def test_a_direction_without_exit_is_rejected(self):
        room_map, _ = make_map()
        game = make_game(room_map)

        result = game.move("E")

        self.assertFalse(result.accepted)
        self.assertEqual(game.player.room_id, 1)
        self.assertEqual(game.state.clock, 0)

    def test_an_invalid_direction_is_rejected(self):
        room_map, _ = make_map()
        game = make_game(room_map)

        result = game.move("X")

        self.assertFalse(result.accepted)
        self.assertEqual(game.state.clock, 0)

    def test_a_closed_door_blocks_the_movement(self):
        room_map, _ = make_map(door_between_2_and_3_closed=True)
        game = make_game(room_map)
        game.move("N")

        result = game.move("N")

        self.assertFalse(result.accepted)
        self.assertEqual(game.player.room_id, 2)

    def test_a_room_without_content_cannot_be_entered(self):
        room_map, _ = make_map()
        room_map.room(2).content_loaded = False
        game = make_game(room_map)

        result = game.move("N")

        self.assertFalse(result.accepted)
        self.assertEqual(game.player.room_id, 1)
        self.assertEqual(game.state.clock, 0)

    def test_without_a_map_there_is_no_movement(self):
        game = Game(GameState(seed=2026), make_player())

        self.assertFalse(game.move("N").accepted)

    def test_entering_a_room_activates_its_enemies(self):
        room_map, _ = make_map()
        sleeping = Enemy(
            "e-1", "Rata gigante", 12, 5, 1, 150, 2, Enemy.GUARDIAN
        )
        game = make_game(room_map, enemies=[sleeping])

        self.assertFalse(sleeping.is_active)

        game.move("N")

        self.assertTrue(sleeping.is_active)
        self.assertIsNotNone(sleeping.scheduled_event)

    def test_an_enemy_of_another_room_stays_asleep(self):
        room_map, _ = make_map()
        far_away = Enemy("e-9", "Rata gigante", 12, 5, 1, 150, 3, Enemy.GUARDIAN)
        game = make_game(room_map, enemies=[far_away])

        game.move("N")

        self.assertFalse(far_away.is_active)


class TestVictory(unittest.TestCase):

    def test_entering_the_exit_room_wins_the_game(self):
        room_map, _ = make_map()
        game = make_game(room_map, exit_room_id=3)

        game.move("N")
        result = game.move("N")

        self.assertTrue(result.accepted)
        self.assertEqual(game.result, VICTORY)

    def test_a_won_game_rejects_more_actions(self):
        room_map, _ = make_map()
        game = make_game(room_map, exit_room_id=3)

        game.move("N")
        game.move("N")

        self.assertTrue(game.is_over)
        self.assertFalse(game.wait().accepted)

    def test_another_room_does_not_win_the_game(self):
        room_map, _ = make_map()
        game = make_game(room_map, exit_room_id=3)

        game.move("N")

        self.assertEqual(game.result, IN_PROGRESS)


class TestDoors(unittest.TestCase):

    def player_with_key(self, key_id="itm_llave_bronce"):
        player = make_player()
        player.inventory = [make_key(key_id)]

        return player

    def test_the_key_matches_by_its_type_id_and_not_by_opens(self):
        room_map, door = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_bronce"
        )
        player = make_player()
        key = make_key("itm_llave_bronce")
        player.inventory = [key]
        game = make_game(room_map, player=player)
        game.move("N")

        self.assertNotEqual(key.opens, "itm_llave_bronce")
        self.assertTrue(game.open_door("N").accepted)
        self.assertTrue(door.is_open)

    def test_opening_a_door_with_the_right_key(self):
        room_map, door = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_bronce"
        )
        game = make_game(room_map, player=self.player_with_key())
        game.move("N")

        result = game.open_door("N")

        self.assertTrue(result.accepted)
        self.assertTrue(door.is_open)

    def test_opening_a_door_costs_fifty(self):
        room_map, _ = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_bronce"
        )
        game = make_game(room_map, player=self.player_with_key())
        game.move("N")
        clock_before = game.state.clock

        game.open_door("N")

        self.assertEqual(game.state.clock, clock_before + 50)

    def test_the_key_is_not_consumed(self):
        room_map, _ = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_bronce"
        )
        player = self.player_with_key()
        game = make_game(room_map, player=player)
        game.move("N")

        game.open_door("N")

        self.assertEqual(len(player.inventory), 1)

    def test_opening_without_the_key_is_rejected_and_costs_nothing(self):
        room_map, door = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_negra"
        )
        game = make_game(room_map, player=self.player_with_key())
        game.move("N")
        clock_before = game.state.clock

        result = game.open_door("N")

        self.assertFalse(result.accepted)
        self.assertFalse(door.is_open)
        self.assertEqual(game.state.clock, clock_before)

    def test_opening_without_any_inventory_is_rejected(self):
        room_map, _ = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_bronce"
        )
        game = make_game(room_map)
        game.move("N")

        self.assertFalse(game.open_door("N").accepted)

    def test_opening_an_already_open_door_is_rejected(self):
        room_map, _ = make_map()
        game = make_game(room_map)

        self.assertFalse(game.open_door("N").accepted)

    def test_opening_lets_the_player_through(self):
        room_map, _ = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_bronce"
        )
        game = make_game(room_map, player=self.player_with_key())
        game.move("N")
        game.open_door("N")

        self.assertTrue(game.move("N").accepted)
        self.assertEqual(game.player.room_id, 3)

    def test_the_door_is_the_same_object_from_both_sides(self):
        room_map, door = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_bronce"
        )
        game = make_game(room_map, player=self.player_with_key())
        game.move("N")
        game.open_door("N")

        from_the_other_side = room_map.room(3).exit_towards("S")

        self.assertTrue(from_the_other_side.door.is_open)


class TestAutomaticDoorClose(unittest.TestCase):

    def opened_game(self, auto_close=200):
        room_map, door = make_map(
            door_between_2_and_3_closed=True,
            key_id="itm_llave_bronce",
            auto_close=auto_close,
        )
        player = make_player()
        player.inventory = [make_key("itm_llave_bronce")]
        game = make_game(room_map, player=player)
        game.move("N")
        game.open_door("N")

        return game, door

    def test_the_door_stays_open_before_the_interval(self):
        game, door = self.opened_game(auto_close=500)

        game.wait()

        self.assertTrue(door.is_open)

    def test_the_door_closes_by_itself_after_the_interval(self):
        game, door = self.opened_game(auto_close=200)

        game.wait()
        game.wait()
        game.wait()

        self.assertFalse(door.is_open)

    def test_a_door_without_automatic_close_stays_open(self):
        room_map, door = make_map(
            door_between_2_and_3_closed=True, key_id="itm_llave_bronce"
        )
        player = make_player()
        player.inventory = [make_key("itm_llave_bronce")]
        game = make_game(room_map, player=player)
        game.move("N")
        game.open_door("N")

        for _ in range(10):
            game.wait()

        self.assertTrue(door.is_open)

    def test_the_player_stays_where_they_are_when_a_door_closes(self):
        game, door = self.opened_game(auto_close=200)
        game.move("N")
        room_after_crossing = game.player.room_id

        for _ in range(5):
            game.wait()

        self.assertFalse(door.is_open)
        self.assertEqual(game.player.room_id, room_after_crossing)


class TestTraps(unittest.TestCase):

    def map_with_trap(self, damage=4, rearm_interval=300):
        room_map, _ = make_map()
        room_map.room(2).traps.append(
            make_trap(damage=damage, rearm_interval=rearm_interval)
        )

        return room_map

    def test_entering_a_room_sets_off_an_armed_trap(self):
        room_map = self.map_with_trap(damage=4)
        game = make_game(room_map)

        game.move("N")

        self.assertEqual(game.player.health, 96)

    def test_the_trap_is_disarmed_after_firing(self):
        room_map = self.map_with_trap()
        game = make_game(room_map)

        game.move("N")

        self.assertFalse(room_map.room(2).traps[0].armed)

    def test_a_disarmed_trap_does_nothing(self):
        room_map = self.map_with_trap(damage=4, rearm_interval=10_000)
        game = make_game(room_map)

        game.move("N")
        health_after_the_first_time = game.player.health
        game.move("S")
        game.move("N")

        self.assertEqual(game.player.health, health_after_the_first_time)

    def test_the_trap_rearms_after_its_interval(self):
        room_map = self.map_with_trap(damage=4, rearm_interval=200)
        game = make_game(room_map)

        game.move("N")

        for _ in range(4):
            game.wait()

        self.assertTrue(room_map.room(2).traps[0].armed)

    def test_a_rearmed_trap_fires_again(self):
        room_map = self.map_with_trap(damage=4, rearm_interval=200)
        game = make_game(room_map)

        game.move("N")

        for _ in range(4):
            game.wait()

        game.move("S")
        health_before = game.player.health
        game.move("N")

        self.assertEqual(game.player.health, health_before - 4)

    def test_a_trap_can_defeat_the_player(self):
        room_map = self.map_with_trap(damage=50)
        game = make_game(room_map, player=make_player(max_health=10, defense=0))

        game.move("N")

        self.assertEqual(game.result, DEFEAT)
        self.assertTrue(game.is_over)



def make_wanderer(actor_id="e-1", room_id=2, speed=100):
    return Enemy(
        actor_id=actor_id,
        name="Errante",
        max_health=100,
        attack=1,
        defense=0,
        speed=speed,
        room_id=room_id,
        behavior=Enemy.WANDERER,
    )


class TestWandererBehaviour(unittest.TestCase):

    def test_a_wanderer_changes_room_in_a_real_game(self):
        room_map, _ = make_map()
        wanderer = make_wanderer(room_id=2)
        game = make_game(room_map, enemies=[wanderer])
        game.move("N")
        game.move("S")

        for _ in range(5):
            game.wait()

        self.assertNotEqual(wanderer.room_id, 2)

    def test_a_wanderer_with_no_exits_at_all_waits(self):
        import random

        isolated = Room(99, "Celda tapiada")
        wanderer = make_wanderer(room_id=99)
        player = make_player(room_id=1)

        action, exit_ = wanderer.decide_action(
            player, isolated, random.Random(2026)
        )

        self.assertEqual(action, Enemy.WAIT)
        self.assertIsNone(exit_)

    def test_a_wanderer_never_chooses_a_closed_exit(self):
        """Prueba directa de la decision, porque en una partida el errante
        acaba compartiendo sala con el jugador y deja de moverse."""
        import random

        room_map, _ = make_map(door_between_2_and_3_closed=True)
        room = room_map.room(2)
        wanderer = make_wanderer(room_id=2)
        player = make_player(room_id=1)
        generator = random.Random(2026)

        chosen = set()

        for _ in range(100):
            action, exit_ = wanderer.decide_action(player, room, generator)
            self.assertEqual(action, Enemy.MOVE)
            chosen.add(exit_.destination)

        self.assertEqual(chosen, {1})

    def test_a_wanderer_uses_every_open_exit_eventually(self):
        import random

        room_map, _ = make_map()
        room = room_map.room(2)
        wanderer = make_wanderer(room_id=2)
        player = make_player(room_id=1)
        generator = random.Random(2026)

        chosen = set()

        for _ in range(100):
            _, exit_ = wanderer.decide_action(player, room, generator)
            chosen.add(exit_.destination)

        self.assertEqual(chosen, {1, 3})

    def test_a_wanderer_without_open_exits_waits(self):
        room_map, _ = make_map(door_between_2_and_3_closed=True)
        wanderer = make_wanderer(room_id=3)
        game = make_game(room_map, enemies=[wanderer])
        game._activate_enemies_in(3)

        for _ in range(10):
            game.wait()

        self.assertEqual(wanderer.room_id, 3)

    def test_a_wanderer_that_shares_the_room_attacks_instead_of_moving(self):
        room_map, _ = make_map()
        wanderer = make_wanderer(room_id=2, speed=250)
        game = make_game(room_map, enemies=[wanderer])
        game.move("N")

        health_before = game.player.health
        game.wait()

        self.assertEqual(wanderer.room_id, 2)
        self.assertLess(game.player.health, health_before)

    def test_the_wanderer_is_reproducible_with_the_same_seed(self):
        def run(seed):
            room_map, _ = make_map()
            wanderer = make_wanderer(room_id=2)
            game = make_game(room_map, enemies=[wanderer], seed=seed)
            game.move("N")
            game.move("S")
            path = []

            for _ in range(10):
                game.wait()
                path.append(wanderer.room_id)

            return path

        self.assertEqual(run(2026), run(2026))

    def test_a_guardian_never_leaves_its_room(self):
        room_map, _ = make_map()
        guardian = Enemy("e-2", "Guardian", 100, 1, 0, 100, 2, Enemy.GUARDIAN)
        game = make_game(room_map, enemies=[guardian])
        game.move("N")
        game.move("S")

        for _ in range(10):
            game.wait()

        self.assertEqual(guardian.room_id, 2)


class TestEnemyDrops(unittest.TestCase):

    def dropped_item(self):
        return Item(
            instance_id="itm-9",
            type_id="itm_pocion_menor",
            name="Pocion menor",
            item_class=Item.POTION,
            weight=1,
            value=10,
            heal=5,
        )

    def test_a_dead_enemy_leaves_its_items_on_the_floor(self):
        room_map, _ = make_map()
        loot = self.dropped_item()
        enemy = Enemy(
            "e-1", "Rata gigante", 1, 1, 0, 100, 1, Enemy.GUARDIAN, drops=[loot]
        )
        game = make_game(room_map, enemies=[enemy])

        game.attack("e-1")

        self.assertIn(loot, room_map.room(1).floor_items)

    def test_the_items_land_in_the_room_where_it_died(self):
        room_map, _ = make_map()
        loot = self.dropped_item()
        enemy = Enemy(
            "e-1", "Rata gigante", 1, 1, 0, 100, 2, Enemy.GUARDIAN, drops=[loot]
        )
        game = make_game(room_map, enemies=[enemy])
        game.move("N")

        game.attack("e-1")

        self.assertIn(loot, room_map.room(2).floor_items)
        self.assertNotIn(loot, room_map.room(1).floor_items)

    def test_an_enemy_without_drops_leaves_nothing(self):
        room_map, _ = make_map()
        enemy = Enemy("e-1", "Rata gigante", 1, 1, 0, 100, 1, Enemy.GUARDIAN)
        game = make_game(room_map, enemies=[enemy])

        game.attack("e-1")

        self.assertEqual(room_map.room(1).floor_items, [])

    def test_the_items_are_dropped_only_once(self):
        room_map, _ = make_map()
        loot = self.dropped_item()
        enemy = Enemy(
            "e-1", "Rata gigante", 1, 1, 0, 100, 1, Enemy.GUARDIAN, drops=[loot]
        )
        game = make_game(room_map, enemies=[enemy])

        game.attack("e-1")
        game.attack("e-1")
        game.wait()

        self.assertEqual(room_map.room(1).floor_items.count(loot), 1)

    def test_an_enemy_killed_by_poison_also_drops(self):
        room_map, _ = make_map()
        loot = self.dropped_item()
        enemy = Enemy(
            "e-1", "Rata gigante", 100, 1, 0, 100, 1, Enemy.GUARDIAN,
            health=3, drops=[loot],
        )
        game = make_game(room_map, enemies=[enemy])
        game.apply_poison(enemy, 2)

        for _ in range(5):
            game.wait()

        self.assertFalse(enemy.is_alive)
        self.assertIn(loot, room_map.room(1).floor_items)



class TestMessageOrder(unittest.TestCase):

    def test_entering_is_announced_before_the_trap_fires(self):
        room_map, _ = make_map()
        room_map.room(2).traps.append(make_trap(damage=4))
        game = make_game(room_map)

        game.move("N")

        entered = list(game.messages).index("Entras a Pasillo de las urnas.")
        trap = next(
            index
            for index, text in enumerate(list(game.messages))
            if "Dardos" in text
        )

        self.assertLess(entered, trap)

    def test_entering_is_announced_before_winning(self):
        room_map, _ = make_map()
        game = make_game(room_map, exit_room_id=2)

        game.move("N")

        entered = list(game.messages).index("Entras a Pasillo de las urnas.")
        won = list(game.messages).index("Has encontrado la salida de la cripta.")

        self.assertLess(entered, won)



def make_tracker(actor_id="e-1", room_id=3, speed=100):
    return Enemy(
        actor_id=actor_id,
        name="Rastreador",
        max_health=1000,
        attack=1,
        defense=0,
        speed=speed,
        room_id=room_id,
        behavior=Enemy.TRACKER,
    )


class TestTrackerBehaviour(unittest.TestCase):

    def test_it_follows_the_freshest_trail(self):
        room_map, _ = make_map()
        trail = PlayerTrail()
        trail.mark(1, 0)
        tracker = make_tracker(room_id=2)

        action, chosen = tracker.decide_action(
            make_player(room_id=3), room_map.room(2), None, trail, 100
        )

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 1)

    def test_it_waits_when_there_is_no_trail(self):
        room_map, _ = make_map()
        tracker = make_tracker(room_id=2)

        action, chosen = tracker.decide_action(
            make_player(room_id=3), room_map.room(2), None, PlayerTrail(), 100
        )

        self.assertEqual(action, Enemy.WAIT)
        self.assertIsNone(chosen)

    def test_it_ignores_a_trail_of_four_hundred_units_or_more(self):
        room_map, _ = make_map()
        trail = PlayerTrail()
        trail.mark(1, 0)
        tracker = make_tracker(room_id=2)
        player = make_player(room_id=3)

        fresh, _ = tracker.decide_action(
            player, room_map.room(2), None, trail, 399
        )
        stale, _ = tracker.decide_action(
            player, room_map.room(2), None, trail, 400
        )

        self.assertEqual(fresh, Enemy.MOVE)
        self.assertEqual(stale, Enemy.WAIT)

    def test_a_tie_is_broken_by_the_lower_room_id(self):
        room_map, _ = make_map()
        trail = PlayerTrail()
        trail.mark(1, 50)
        trail.mark(3, 50)
        tracker = make_tracker(room_id=2)

        action, chosen = tracker.decide_action(
            make_player(room_id=99), room_map.room(2), None, trail, 100
        )

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 1)

    def test_it_never_crosses_a_closed_door(self):
        room_map, _ = make_map(door_between_2_and_3_closed=True)
        trail = PlayerTrail()
        trail.mark(3, 50)
        tracker = make_tracker(room_id=2)

        action, chosen = tracker.decide_action(
            make_player(room_id=3), room_map.room(2), None, trail, 100
        )

        self.assertEqual(action, Enemy.WAIT)

    def test_sharing_the_room_beats_tracking(self):
        room_map, _ = make_map()
        trail = PlayerTrail()
        trail.mark(1, 50)
        tracker = make_tracker(room_id=2)

        action, chosen = tracker.decide_action(
            make_player(room_id=2), room_map.room(2), None, trail, 100
        )

        self.assertEqual(action, Enemy.ATTACK)

    def test_it_chases_the_player_in_a_real_game(self):
        room_map, _ = make_map()
        trail = PlayerTrail()
        tracker = make_tracker(room_id=3)
        game = Game(
            GameState(seed=2026),
            make_player(max_health=100000, defense=1000),
            [tracker],
            room_map=room_map,
            trail=trail,
        )
        game._activate_enemies_in(3)

        game.move("N")

        for _ in range(4):
            game.wait()

        self.assertEqual(tracker.room_id, game.player.room_id)


class TestTrailMarking(unittest.TestCase):

    def game_with_trail(self):
        room_map, _ = make_map()
        trail = PlayerTrail()
        game = Game(
            GameState(seed=2026),
            make_player(),
            None,
            room_map=room_map,
            trail=trail,
        )

        return game, trail

    def test_the_initial_room_is_marked_at_instant_zero(self):
        _, trail = self.game_with_trail()

        self.assertEqual(trail.time_at(1), 0)

    def test_every_accepted_action_refreshes_the_trail(self):
        game, trail = self.game_with_trail()

        game.wait()
        game.wait()

        self.assertEqual(trail.time_at(1), 100)

    def test_a_rejected_action_does_not_refresh_the_trail(self):
        game, trail = self.game_with_trail()

        game.wait()
        game.move("E")

        self.assertEqual(trail.time_at(1), 0)

    def test_moving_marks_the_destination_room(self):
        game, trail = self.game_with_trail()

        game.wait()
        game.move("N")

        self.assertEqual(trail.time_at(2), 100)

    def test_the_trail_uses_the_instant_of_the_action(self):
        """El jugador llega a la sala al ejecutar la accion, no al terminar su
        costo: §2.5 dice que aparece en la sala destino al ejecutarla, y el
        ejemplo de §2.13 lo confirma. Por eso el rastro se marca antes de correr
        el ciclo de eventos y queda por debajo del reloj con el que vuelve el
        metodo."""
        game, trail = self.game_with_trail()

        game.move("N")

        self.assertEqual(trail.time_at(2), 0)
        self.assertEqual(game.state.clock, 100)


class TestTheDefaultMessageLog(unittest.TestCase):

    def test_the_game_uses_a_circular_log_by_default(self):
        game = make_game(make_map()[0])

        self.assertIsInstance(game.messages, CircularLog)

    def test_the_messages_stop_at_twenty(self):
        room_map, _ = make_map()
        game = make_game(room_map, player=make_player(max_health=100000))

        for _ in range(40):
            game.wait()

        self.assertEqual(len(game.visible_state().messages), 20)


if __name__ == "__main__":
    unittest.main()
