"""El controlador carga la sala destino antes de mover y precarga despues.

Las primeras pruebas usan un repositorio falso. La ultima juega cripta-01 con
los datos offline del repositorio, registra la partida y la reproduce con un
repositorio y una cache nuevos, como hara --replay.
"""
import os
import tempfile
import unittest

from adapters.fuente_datos import ErrorFuenteDatos, PresupuestoAgotado
from adapters.fuente_offline import FuenteOffline
from controller.commands import parse_command
from controller.game_controller import GameController
from model.game import Game
from model.game_state import GameState
from model.room import Door, Exit, Room, RoomMap
from replay.replay import replay_commands
from replay.replay_log import ReplayHeader, ReplayLogWriter, read_replay_log
from repository.repositorio_cripta import RepositorioCripta
from tests.test_game import make_enemy, make_player


OFFLINE_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_offline")


def make_two_rooms(closed=False):
    """Sala 1 y sala 2 unidas por una puerta hacia el norte."""
    first = Room(1, "Entrada")
    second = Room(2, "Pasillo")
    door = Door(1, 2, closed=closed)
    first.add_exit(Exit("N", 2, door))
    second.add_exit(Exit("S", 1, door))
    first.content_loaded = True

    room_map = RoomMap()
    room_map.add(first)
    room_map.add(second)

    return room_map


class FakeRepository:
    """Imita lo que el controlador usa de RepositorioCripta."""

    def __init__(self, enemies=(), error=None):
        self.enemies = list(enemies)
        self.error = error
        self.loaded = []
        self.preloaded = []

    def cargar_contenido_de_sala(self, room):
        if self.error is not None:
            raise self.error

        self.loaded.append(room.room_id)
        if room.content_loaded:
            return []

        room.content_loaded = True
        return self.enemies

    def despues_de_accion(self, room_id):
        self.preloaded.append(room_id)


def make_controller(repository, closed=False):
    game = Game(GameState(seed=3), make_player(), room_map=make_two_rooms(closed))

    return GameController(game, repository=repository), game


class TestLoadBeforeMoving(unittest.TestCase):

    def test_the_destination_is_loaded_and_the_move_is_accepted(self):
        repository = FakeRepository()
        controller, game = make_controller(repository)

        result = controller.execute(parse_command("mover N"))

        self.assertTrue(result.accepted, result.message)
        self.assertEqual(repository.loaded, [2])
        self.assertEqual(game.player.room_id, 2)

    def test_the_enemies_of_the_new_room_join_the_game(self):
        rat = make_enemy("e-201", room_id=2)
        controller, game = make_controller(FakeRepository([rat]))

        controller.execute(parse_command("mover N"))

        self.assertIn(rat, game.enemies)

    def test_nothing_is_loaded_through_a_closed_door(self):
        repository = FakeRepository()
        controller, game = make_controller(repository, closed=True)

        result = controller.execute(parse_command("mover N"))

        self.assertFalse(result.accepted)
        self.assertEqual(repository.loaded, [])

    def test_nothing_is_loaded_where_there_is_no_exit(self):
        repository = FakeRepository()
        controller, _ = make_controller(repository)

        result = controller.execute(parse_command("mover E"))

        self.assertFalse(result.accepted)
        self.assertEqual(repository.loaded, [])

    def test_without_budget_the_move_is_rejected_without_time(self):
        repository = FakeRepository(error=PresupuestoAgotado("descargar contenido", 9))
        log = []
        controller, game = make_controller(repository)
        controller.replay_log = log

        result = controller.execute(parse_command("mover N"))

        self.assertFalse(result.accepted)
        self.assertEqual(game.state.clock, 0)
        self.assertEqual(game.player.room_id, 1)
        self.assertEqual(log, [])

    def test_a_network_error_is_reported_and_not_raised(self):
        repository = FakeRepository(error=ErrorFuenteDatos("descargar contenido", "error del servidor", 500))
        controller, game = make_controller(repository)

        result = controller.execute(parse_command("mover N"))

        self.assertFalse(result.accepted)
        self.assertIn("HTTP 500", result.message)


class TestPreloadAfterActions(unittest.TestCase):

    def test_each_accepted_action_preloads_around_the_player(self):
        repository = FakeRepository()
        controller, _ = make_controller(repository)

        controller.execute(parse_command("esperar"))
        controller.execute(parse_command("mover N"))

        self.assertEqual(repository.preloaded, [1, 2])

    def test_a_rejected_action_does_not_preload(self):
        repository = FakeRepository()
        controller, _ = make_controller(repository)

        controller.execute(parse_command("atacar e-999"))

        self.assertEqual(repository.preloaded, [])


class TestReplayAgainstOfflineCrypt(unittest.TestCase):
    """Partida real con datos offline: jugarla, registrarla y reproducirla."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.directory.name, "partida.log")

    def tearDown(self):
        self.directory.cleanup()

    def start(self, cache_name, versions=None, crypt_id=None):
        repository = RepositorioCripta(
            FuenteOffline(OFFLINE_DATA),
            os.path.join(self.directory.name, cache_name),
        )
        repository.empezar_conteo_de_partida()
        if crypt_id is None:
            crypt_id = repository.listar_criptas()[0]["id"]
        data = repository.iniciar_partida(crypt_id, versions)

        player = repository.crear_jugador()
        room_map = repository.crear_mapa()
        enemies = repository.cargar_contenido_de_sala(room_map.room(player.room_id))
        game = Game(GameState(seed=11), player, enemies, room_map, data.sala_salida)

        return repository, game

    def play(self, controller, steps):
        """Avanza por la primera salida abierta; si no hay, espera."""
        for _ in range(steps):
            if controller.is_over:
                return

            room = controller.game.room_map.room(controller.game.player.room_id)
            open_exits = [exit_ for exit_ in room.exits() if exit_.door.is_open]
            text = f"mover {open_exits[0].direction}" if open_exits else "esperar"
            controller.execute(parse_command(text))

    def snapshot(self, game):
        alive = [(enemy.actor_id, enemy.room_id, enemy.health) for enemy in game.enemies]

        return (game.state.clock, game.player.room_id, game.player.health,
                game.result, alive, list(game.messages))

    def test_the_reproduced_game_ends_like_the_original(self):
        repository, original = self.start("cache_original")
        crypt_id, crypt_version, catalog_version = repository.versiones_de_la_partida()
        header = ReplayHeader(crypt_id, crypt_version, catalog_version, 11)

        with ReplayLogWriter(self.log_path, header) as log:
            controller = GameController(original, log, repository)
            self.play(controller, 6)

        replay_log = read_replay_log(self.log_path)
        moves = [entry for entry in replay_log.commands if entry.command.name == "mover"]
        self.assertTrue(moves, "la partida de prueba deberia incluir movimientos")

        replay_repository, reproduced = self.start(
            "cache_replay",
            (replay_log.header.crypt_version, replay_log.header.catalog_version),
            replay_log.header.crypt_id,
        )
        replay_commands(
            GameController(reproduced, repository=replay_repository),
            replay_log.commands,
        )

        self.assertEqual(self.snapshot(reproduced), self.snapshot(original))


if __name__ == "__main__":
    unittest.main()
