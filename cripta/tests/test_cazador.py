"""Pruebas del cazador (seccion 3.2 de la segunda parte).

Cubren los cinco casos del Apendice B bajo "Terreno y cazador" que no cubre la
capacidad 001, y la equivalencia que exige FR-011: la decision de cada turno
tiene que ser la que daria un calculo desde cero.
"""
import unittest

from model.enemy import Enemy
from model.game import ATTACK_COST, DEFEAT, WAIT_COST, Game
from model.game_state import GameState
from model.player import Player
from model.room import DEFAULT_EXIT_COST, Door, Exit, Room, RoomMap


OPPOSITE = {"N": "S", "S": "N", "E": "O", "O": "E"}


def make_player(speed=100, room_id=1, max_health=100):
    return Player(
        actor_id="p-1",
        name="Heroe",
        max_health=max_health,
        attack=6,
        defense=10,
        speed=speed,
        room_id=room_id,
    )


def make_hunter(room_id, pursuit_range=600, speed=100, actor_id="e-1", attack=1):
    hunter = Enemy(
        actor_id=actor_id,
        name="Sabueso oseo",
        max_health=18,
        attack=attack,
        defense=2,
        speed=speed,
        room_id=room_id,
        behavior=Enemy.HUNTER,
        pursuit_range=pursuit_range,
    )

    return hunter


def connect(rooms, id_a, id_b, direction, cost=DEFAULT_EXIT_COST, closed=False,
            auto_close=None):
    door = Door(id_a, id_b, closed=closed, auto_close=auto_close, cost=cost)
    rooms[id_a].add_exit(Exit(direction, id_b, door))
    rooms[id_b].add_exit(Exit(OPPOSITE[direction], id_a, door))

    return door


def make_rooms(ids):
    rooms = {}

    for room_id in ids:
        room = Room(room_id, f"Sala {room_id}")
        room.content_loaded = True
        rooms[room_id] = room

    return rooms


def make_game(rooms, player=None, enemies=None, seed=2026, always_recompute=False,
              wake=True):
    """Partida de prueba, con los enemigos ya despiertos salvo que se pida.

    Los activa por el camino del propio motor, no poniendoles el campo a mano:
    es ese camino el que tambien los programa en la agenda, asi que un enemigo
    activado a mano nunca tomaria un turno y la prueba pasaria en vano.
    """
    room_map = RoomMap()

    for room_id in sorted(rooms):
        room_map.add(rooms[room_id])

    game = Game(
        GameState(seed=seed),
        make_player() if player is None else player,
        enemies,
        room_map=room_map,
        always_recompute_routes=always_recompute,
    )

    if wake:
        for enemy in game.enemies:
            game._activate_enemies_in(enemy.room_id)

    return game


def decision_of(game, hunter):
    """La decision que tomaria el cazador ahora mismo, sin ejecutarla."""
    return hunter.decide_action(
        game.player,
        game.room_map.room(hunter.room_id),
        game.state.random_generator,
        game.trail,
        game.state.clock,
        game._routes_for(hunter),
    )


class HunterChasesTest(unittest.TestCase):
    """Historia 1: persigue por donde le cuesta menos."""

    def test_sharing_the_room_attacks_without_computing_a_route(self):
        """FR-003: compartir sala tiene prioridad sobre todo lo demas."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N")
        hunter = make_hunter(room_id=1)
        game = make_game(rooms, enemies=[hunter])

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.ATTACK)
        self.assertIsNone(chosen)

    def test_moves_one_room_towards_the_player(self):
        """FR-007: da un paso por una ruta de costo minimo."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N")
        connect(rooms, 2, 3, "N")
        hunter = make_hunter(room_id=3)
        game = make_game(rooms, enemies=[hunter])

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 2)

    def test_takes_the_cheaper_route_even_if_it_has_more_rooms(self):
        """Apendice B y SC-001: cuenta el costo, no la cantidad de salas.

        Del 1 al 9 hay dos caminos: por la sala 2, dos salidas que cuestan 500
        en total; por la sala 3, cuatro salidas que cuestan 200.
        """
        rooms = make_rooms([1, 2, 3, 4, 5, 9])
        connect(rooms, 9, 2, "N", cost=250)
        connect(rooms, 2, 1, "N", cost=250)
        connect(rooms, 9, 3, "E", cost=50)
        connect(rooms, 3, 4, "E", cost=50)
        connect(rooms, 4, 5, "E", cost=50)
        connect(rooms, 5, 1, "E", cost=50)
        hunter = make_hunter(room_id=9)
        game = make_game(rooms, enemies=[hunter])

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 3)

    def test_the_turn_costs_what_the_exit_it_crosses_costs(self):
        """FR-007: el costo de la accion es el costo de esa salida."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N", cost=100)
        connect(rooms, 2, 3, "N", cost=250)
        hunter = make_hunter(room_id=3, speed=100)
        game = make_game(rooms, enemies=[hunter])
        start = game.state.clock

        game._run_enemy_turn(hunter)

        self.assertEqual(hunter.room_id, 2)
        self.assertEqual(hunter.scheduled_event.time, start + 250)

    def test_a_closed_exit_is_not_counted_even_if_it_is_the_short_way(self):
        """FR-010: un enemigo no abre puertas cerradas."""
        rooms = make_rooms([1, 2, 3, 4])
        connect(rooms, 4, 1, "N", cost=1, closed=True)
        connect(rooms, 4, 2, "E", cost=100)
        connect(rooms, 2, 3, "E", cost=100)
        connect(rooms, 3, 1, "E", cost=100)
        hunter = make_hunter(room_id=4)
        game = make_game(rooms, enemies=[hunter])

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 2)

    def test_deciding_does_not_depend_on_the_room_content_being_loaded(self):
        """FR-012: el calculo usa el esqueleto, no el contenido."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N")
        connect(rooms, 2, 3, "N")
        rooms[2].content_loaded = False
        hunter = make_hunter(room_id=3)
        game = make_game(rooms, enemies=[hunter])

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 2)

    def test_arriving_at_the_player_room_attacks_only_on_the_next_turn(self):
        """Caso borde: ese turno fue un movimiento, no un ataque."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N")
        hunter = make_hunter(room_id=2)
        game = make_game(rooms, enemies=[hunter])
        health_before = game.player.health

        game._run_enemy_turn(hunter)

        self.assertEqual(hunter.room_id, 1)
        self.assertEqual(game.player.health, health_before)

        game._run_enemy_turn(hunter)

        self.assertLess(game.player.health, health_before)


class HunterTieBreakTest(unittest.TestCase):
    """Historia 2: dos rutas igual de baratas."""

    def test_two_tied_neighbours_go_to_the_lower_id(self):
        """Apendice B y SC-002: gana la vecina de menor id.

        Desde la sala 1 hay dos rutas de costo 200 hacia el jugador, en la
        sala 9: una por la sala 7 y otra por la sala 4.
        """
        rooms = make_rooms([1, 4, 7, 9])
        connect(rooms, 1, 7, "N", cost=100)
        connect(rooms, 7, 9, "N", cost=100)
        connect(rooms, 1, 4, "E", cost=100)
        connect(rooms, 4, 9, "E", cost=100)
        hunter = make_hunter(room_id=1)
        game = make_game(rooms, player=make_player(room_id=9), enemies=[hunter])

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 4)

    def test_the_tie_break_does_not_follow_the_order_of_expansion(self):
        """FR-008: la vecina correcta no es la que se asienta primero.

        La sala 8 queda a 200 del jugador y la 2 a 50, asi que la 8 se asienta
        antes. Las dos empiezan rutas de costo 300 desde la sala 1, y la regla
        del enunciado manda la 2.
        """
        rooms = make_rooms([1, 2, 5, 8])
        connect(rooms, 1, 8, "N", cost=100)
        connect(rooms, 8, 5, "N", cost=200)
        connect(rooms, 1, 2, "E", cost=250)
        connect(rooms, 2, 5, "E", cost=50)
        hunter = make_hunter(room_id=1)
        game = make_game(rooms, player=make_player(room_id=5), enemies=[hunter])

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 2)

    def test_many_tied_routes_still_go_to_the_lower_id(self):
        """FR-008: cuatro vecinas empatadas."""
        rooms = make_rooms([1, 3, 7, 12, 40, 99])
        legs = (("N", "E", 12), ("S", "O", 3), ("E", "N", 40), ("O", "S", 7))

        for towards_middle, towards_player, middle in legs:
            connect(rooms, 1, middle, towards_middle, cost=100)
            connect(rooms, middle, 99, towards_player, cost=100)

        hunter = make_hunter(room_id=1)
        game = make_game(rooms, player=make_player(room_id=99), enemies=[hunter])

        _, chosen = decision_of(game, hunter)

        self.assertEqual(chosen.destination, 3)

    def test_several_hunters_in_the_same_room_decide_the_same(self):
        """Caso borde: el desempate no depende de quien pregunta."""
        rooms = make_rooms([1, 4, 7, 9])
        connect(rooms, 1, 7, "N", cost=100)
        connect(rooms, 7, 9, "N", cost=100)
        connect(rooms, 1, 4, "E", cost=100)
        connect(rooms, 4, 9, "E", cost=100)
        hunters = [
            make_hunter(room_id=1, actor_id="e-1"),
            make_hunter(room_id=1, actor_id="e-2", pursuit_range=900),
            make_hunter(room_id=1, actor_id="e-3", speed=200),
        ]
        game = make_game(rooms, player=make_player(room_id=9), enemies=hunters)

        destinations = [decision_of(game, hunter)[1].destination for hunter in hunters]

        self.assertEqual(destinations, [4, 4, 4])

    def test_the_same_seed_gives_the_same_decisions(self):
        """FR-016: la partida es reproducible."""
        def play():
            rooms = make_rooms([1, 4, 7, 9])
            connect(rooms, 1, 7, "N", cost=100)
            connect(rooms, 7, 9, "N", cost=100)
            connect(rooms, 1, 4, "E", cost=100)
            connect(rooms, 4, 9, "E", cost=100)
            hunter = make_hunter(room_id=1, speed=150)
            game = make_game(rooms, player=make_player(room_id=9), enemies=[hunter])
            seen = []

            for _ in range(6):
                game.wait()
                seen.append((game.state.clock, hunter.room_id, game.player.health))

            return seen

        self.assertEqual(play(), play())


class HunterRangeTest(unittest.TestCase):
    """Historia 3: el rango."""

    def test_no_open_route_waits_with_cost_one_hundred(self):
        """Apendice B: sin ruta, espera con costo 100."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N", closed=True)
        hunter = make_hunter(room_id=2, pursuit_range=10 ** 6, speed=100)
        game = make_game(rooms, enemies=[hunter])
        start = game.state.clock

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.WAIT)
        self.assertIsNone(chosen)

        game._run_enemy_turn(hunter)

        self.assertEqual(hunter.room_id, 2)
        self.assertEqual(hunter.scheduled_event.time, start + WAIT_COST)

    def test_a_route_dearer_than_the_range_waits_with_cost_one_hundred(self):
        """Apendice B: ruta de 700 y rango 600, espera."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N", cost=400)
        connect(rooms, 2, 3, "N", cost=300)
        hunter = make_hunter(room_id=3, pursuit_range=600, speed=100)
        game = make_game(rooms, enemies=[hunter])
        start = game.state.clock

        action, _ = decision_of(game, hunter)

        self.assertEqual(action, Enemy.WAIT)

        game._run_enemy_turn(hunter)

        self.assertEqual(hunter.room_id, 3)
        self.assertEqual(hunter.scheduled_event.time, start + WAIT_COST)

    def test_a_route_that_costs_exactly_the_range_is_walked(self):
        """FR-006: el rango es el costo maximo aceptado, no uno ya excluido."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N", cost=300)
        connect(rooms, 2, 3, "N", cost=300)
        hunter = make_hunter(room_id=3, pursuit_range=600)
        game = make_game(rooms, enemies=[hunter])

        action, chosen = decision_of(game, hunter)

        self.assertEqual(action, Enemy.MOVE)
        self.assertEqual(chosen.destination, 2)

    def test_a_range_of_zero_never_chases(self):
        """Caso borde: cualquier ruta cuesta al menos 1."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N", cost=1)
        hunter = make_hunter(room_id=2, pursuit_range=0)
        game = make_game(rooms, enemies=[hunter])

        action, _ = decision_of(game, hunter)

        self.assertEqual(action, Enemy.WAIT)

    def test_a_range_of_zero_still_attacks_in_the_same_room(self):
        """Caso borde: compartir sala tiene prioridad sobre el rango."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N")
        hunter = make_hunter(room_id=1, pursuit_range=0)
        game = make_game(rooms, enemies=[hunter])

        action, _ = decision_of(game, hunter)

        self.assertEqual(action, Enemy.ATTACK)

    def test_an_unreachable_player_never_moves_the_hunter(self):
        """SC-003: cripta partida en dos, el cazador no se mueve nunca."""
        rooms = make_rooms([1, 2, 8, 9])
        connect(rooms, 1, 2, "N")
        connect(rooms, 8, 9, "N")
        hunter = make_hunter(room_id=8, pursuit_range=10 ** 6, speed=400)
        game = make_game(rooms, enemies=[hunter])

        for _ in range(10):
            game.wait()

        self.assertEqual(hunter.room_id, 8)

    def test_the_wait_of_a_hunter_scales_with_its_speed(self):
        """FR-005: la espera es la de cualquier actor."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N", closed=True)
        hunter = make_hunter(room_id=2, speed=200)
        game = make_game(rooms, enemies=[hunter])
        start = game.state.clock

        game._run_enemy_turn(hunter)

        self.assertEqual(hunter.scheduled_event.time, start + WAIT_COST * 100 // 200)


class HunterRecomputesTest(unittest.TestCase):
    """Historia 4: la decision se recalcula."""

    def _diamond(self):
        """Dos rutas del 1 al 9: por la 4, barata; por la 7, cara."""
        rooms = make_rooms([1, 4, 7, 9])
        cheap = connect(rooms, 1, 4, "E", cost=50)
        connect(rooms, 4, 9, "E", cost=50)
        connect(rooms, 1, 7, "N", cost=300)
        connect(rooms, 7, 9, "N", cost=300)

        return rooms, cheap

    def test_a_door_that_closes_between_turns_changes_the_next_decision(self):
        """Apendice B y FR-011: decide como si calculara desde cero."""
        rooms, cheap = self._diamond()
        hunter = make_hunter(room_id=1, pursuit_range=10 ** 6)
        game = make_game(rooms, player=make_player(room_id=9), enemies=[hunter])

        _, before = decision_of(game, hunter)
        self.assertEqual(before.destination, 4)

        game._close_door(1, "E")
        self.assertTrue(cheap.closed)

        _, after = decision_of(game, hunter)
        self.assertEqual(after.destination, 7)

    def test_the_only_route_cut_by_a_closed_door_leaves_the_hunter_waiting(self):
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N")
        connect(rooms, 2, 3, "N")
        hunter = make_hunter(room_id=3, pursuit_range=10 ** 6)
        game = make_game(rooms, enemies=[hunter])

        self.assertEqual(decision_of(game, hunter)[0], Enemy.MOVE)

        game._close_door(2, "N")

        self.assertEqual(decision_of(game, hunter)[0], Enemy.WAIT)

    def test_a_door_the_player_opens_shortens_the_route(self):
        """FR-011: abrir una puerta tambien invalida el calculo."""
        rooms = make_rooms([1, 4, 7, 9])
        connect(rooms, 1, 4, "E", cost=50, closed=True)
        connect(rooms, 4, 9, "E", cost=50)
        connect(rooms, 1, 7, "N", cost=300)
        connect(rooms, 7, 9, "N", cost=300)
        hunter = make_hunter(room_id=1, pursuit_range=10 ** 6)
        game = make_game(rooms, player=make_player(room_id=9), enemies=[hunter])

        self.assertEqual(decision_of(game, hunter)[1].destination, 7)

        game.player.room_id = 1
        game.open_door("E")
        game.player.room_id = 9
        game._invalidate_routes()

        self.assertEqual(decision_of(game, hunter)[1].destination, 4)

    def test_a_player_who_moves_is_chased_to_the_new_room(self):
        """FR-011: persigue la sala donde el jugador esta."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N")
        connect(rooms, 2, 3, "N")
        hunter = make_hunter(room_id=1, pursuit_range=10 ** 6)
        game = make_game(rooms, player=make_player(room_id=1), enemies=[hunter])
        hunter.room_id = 3

        self.assertEqual(decision_of(game, hunter)[1].destination, 2)

        game.player.room_id = 2
        game._invalidate_routes()
        hunter.room_id = 1

        self.assertEqual(decision_of(game, hunter)[1].destination, 2)

    def test_moving_a_hunter_does_not_force_a_new_search(self):
        """El movimiento de un cazador no cambia la respuesta, asi que no
        invalida: es el ahorro que el plan defiende."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N")
        connect(rooms, 2, 3, "N")
        hunter = make_hunter(room_id=3, pursuit_range=10 ** 6)
        game = make_game(rooms, enemies=[hunter])

        game._run_enemy_turn(hunter)
        searches = game.route_searches

        game._run_enemy_turn(hunter)

        self.assertEqual(game.route_searches, searches)

    def _busy_crypt(self, always_recompute):
        """Partida donde las puertas cambian todo el tiempo.

        El jugador abre una puerta con cierre automatico y se mueve por ella,
        asi que la puerta se abre y se cierra sola una y otra vez. Eso es lo
        que de verdad invalida el calculo compartido: sin abrir ninguna
        puerta, un cierre automatico nunca llega a programarse.
        """
        rooms = make_rooms([1, 2, 3, 4, 5, 6])
        connect(rooms, 1, 2, "N", cost=50, closed=True, auto_close=120)
        connect(rooms, 2, 3, "N", cost=50, closed=True, auto_close=150)
        connect(rooms, 1, 4, "E", cost=200)
        connect(rooms, 4, 5, "E", cost=200)
        connect(rooms, 5, 3, "E", cost=200)
        connect(rooms, 3, 6, "N", cost=50)
        hunters = [
            make_hunter(room_id=3, pursuit_range=1200, speed=120, actor_id="e-1"),
            make_hunter(room_id=6, pursuit_range=400, speed=90, actor_id="e-2"),
            make_hunter(room_id=5, pursuit_range=10 ** 6, speed=150, actor_id="e-3"),
        ]
        game = make_game(
            rooms,
            player=make_player(room_id=1, max_health=10 ** 6),
            enemies=hunters,
            always_recompute=always_recompute,
        )
        seen = []

        for step in range(24):
            if step % 4 == 0:
                game.open_door("N")
            elif step % 4 == 1:
                game.move("N")
            elif step % 4 == 2:
                game.wait()
            else:
                game.move("S")

            seen.append(
                (
                    game.state.clock,
                    game.player.room_id,
                    tuple(hunter.room_id for hunter in hunters),
                    game.player.health,
                )
            )

        return game, seen

    def test_sharing_matches_always_recomputing_turn_by_turn(self):
        """FR-011 y SC-004: la prueba central de la equivalencia.

        No compara contra valores escritos a mano: corre la misma partida en
        modo compartido y en modo recalcular siempre, con puertas que se
        abren y se cierran solas, y exige que las decisiones sean identicas
        turno por turno.
        """
        shared_game, shared = self._busy_crypt(always_recompute=False)
        _, from_scratch = self._busy_crypt(always_recompute=True)

        self.assertEqual(shared, from_scratch)
        self.assertGreater(
            shared_game.route_searches,
            1,
            "la invalidacion no se disparo, asi que la prueba no compara nada",
        )

    def test_a_quiet_crypt_needs_a_single_search(self):
        """El ahorro que el plan defiende: sin cambios, una sola busqueda.

        El jugador espera, nadie abre puertas y los cazadores se mueven. Nada
        de eso cambia la sala del jugador ni el estado de las puertas, asi que
        el calculo compartido sigue siendo valido todo el tiempo.
        """
        rooms = make_rooms([1, 2, 3, 4])
        connect(rooms, 1, 2, "N", cost=50)
        connect(rooms, 2, 3, "N", cost=50)
        connect(rooms, 3, 4, "N", cost=50)
        hunters = [
            make_hunter(room_id=4, pursuit_range=1200, speed=120, actor_id="e-1"),
            make_hunter(room_id=3, pursuit_range=1200, speed=90, actor_id="e-2"),
        ]
        game = make_game(
            rooms,
            player=make_player(room_id=1, max_health=10 ** 6),
            enemies=hunters,
        )

        for _ in range(20):
            game.wait()

        self.assertEqual(game.route_searches, 1)
        self.assertEqual([hunter.room_id for hunter in hunters], [1, 1])

    def test_a_rewind_scroll_invalidates_the_shared_search(self):
        """El pergamino revierte el historial, asi que puede mover al jugador
        y cambiar puertas de golpe."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N")
        connect(rooms, 2, 3, "N")
        hunter = make_hunter(room_id=3, pursuit_range=10 ** 6)
        game = make_game(rooms, enemies=[hunter])

        game._routes_towards_player()
        self.assertIsNotNone(game._routes)

        game._invalidate_routes()

        self.assertIsNone(game._routes)


class HunterIsStillAnEnemyTest(unittest.TestCase):
    """Historia 5: sigue siendo un enemigo como los otros."""

    def test_an_inactive_hunter_does_not_chase(self):
        """FR-015: duerme hasta que se activa."""
        rooms = make_rooms([1, 2, 3])
        connect(rooms, 1, 2, "N")
        connect(rooms, 2, 3, "N")
        hunter = make_hunter(room_id=3, pursuit_range=10 ** 6, speed=400)
        game = make_game(rooms, enemies=[hunter], wake=False)

        for _ in range(10):
            game.wait()

        self.assertEqual(hunter.room_id, 3)
        self.assertFalse(hunter.is_active)

    def test_an_inactive_hunter_is_not_counted_in_the_shared_cut(self):
        """El corte lo fijan los cazadores activos."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N")
        sleeping = make_hunter(room_id=2, pursuit_range=10 ** 6)
        game = make_game(rooms, enemies=[sleeping], wake=False)

        routes = game._routes_towards_player()

        self.assertEqual(routes.corte, 0)

    def test_a_dead_hunter_is_not_counted_in_the_shared_cut(self):
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N")
        dead = make_hunter(room_id=2, pursuit_range=10 ** 6)
        dead.health = 0
        game = make_game(rooms, enemies=[dead])

        self.assertEqual(game._routes_towards_player().corte, 0)

    def test_the_other_three_behaviours_ignore_the_search(self):
        """FR-013: guardian, errante y rastreador deciden igual que antes."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N")
        game = make_game(rooms)

        for behavior in (Enemy.GUARDIAN, Enemy.WANDERER, Enemy.TRACKER):
            enemy = Enemy(
                actor_id=f"e-{behavior}",
                name=behavior,
                max_health=10,
                attack=1,
                defense=1,
                speed=100,
                room_id=2,
                behavior=behavior,
            )

            self.assertIsNone(game._routes_for(enemy))

    def test_a_hunter_rejects_an_invalid_range(self):
        """FR-002: el rango es un entero mayor o igual que 0."""
        for invalid in (-1, "600", 1.5, True, None):
            with self.assertRaises(ValueError):
                make_hunter(room_id=1, pursuit_range=invalid)

    def test_a_non_hunter_enemy_has_a_neutral_range(self):
        enemy = Enemy(
            actor_id="e-9",
            name="Centinela",
            max_health=10,
            attack=1,
            defense=1,
            speed=100,
            room_id=2,
            behavior=Enemy.GUARDIAN,
        )

        self.assertEqual(enemy.pursuit_range, 0)

    def test_the_game_ends_with_a_hunter_turn_still_scheduled(self):
        """Caso borde: no aparece ninguna regla nueva."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N")
        hunter = make_hunter(room_id=1, pursuit_range=10 ** 6, speed=400, attack=10 ** 6)
        game = make_game(rooms, player=make_player(max_health=1), enemies=[hunter])

        for _ in range(5):
            game.wait()

        self.assertEqual(game.result, DEFEAT)

    def test_attacking_costs_what_attacking_has_always_cost(self):
        """FR-006 de la capacidad 001: el costo de atacar no cambia."""
        rooms = make_rooms([1, 2])
        connect(rooms, 1, 2, "N")
        hunter = make_hunter(room_id=1, speed=100, attack=1)
        game = make_game(rooms, player=make_player(max_health=10 ** 6), enemies=[hunter])
        start = game.state.clock

        game._run_enemy_turn(hunter)

        self.assertEqual(hunter.scheduled_event.time, start + ATTACK_COST)


if __name__ == "__main__":
    unittest.main()
