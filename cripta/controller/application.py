"""Flujo de la aplicacion: armar una partida, jugarla y reproducirla.

main.py solo interpreta las banderas y llama a estas funciones. Aqui se unen
el repositorio del bloque 2, el modelo, el controlador, la vista y la bitacora
de reproduccion. No hay reglas del juego en este archivo.

La reproduccion (--replay) no instancia la vista interactiva (§6): recibe una
funcion de salida y nada mas.
"""
import os
import time
from dataclasses import dataclass

from adapters.almacen_fichas import ErrorAlmacenDisco
from adapters.almacen_partida import (
    ArchivoDePartidaDanado,
    PartidaIncompatible,
    cargar_partida,
    comprobar_versiones_vigentes,
    construir_juego_reversible,
    guardar_partida,
)
from adapters.fuente_datos import ErrorFuenteDatos
from adapters.scoreboard import ScoreboardError, ScoreEntry
from controller.commands import (
    HELP,
    LOAD,
    QUIT,
    SAVE,
    VIEW,
    CommandError,
    is_game_action,
    parse_command,
)
from controller.game_controller import GameController
from model.game import DEFEAT, VICTORY, Game
from model.game_state import GameState
from replay.replay import ReplayDivergence, replay_commands
from replay.replay_log import (
    ReplayHeader,
    ReplayLogWriter,
    file_digest,
    read_replay_log,
)
from repository.gestor_catalogo import FichaNoDisponible
from repository.gestor_contenido import ContenidoNoDisponible
from repository.repositorio_cripta import VersionesIncompatibles
from repository.traductor import ErrorDatosCripta
from structures.history import History, ReversibleEventQueue
from structures.inventory import Inventory
from structures.tabla_hash import TablaHash
from structures.trail import PlayerTrail


LOG_DIRECTORY = "partidas"

# Errores de datos que el programa reporta con su mensaje en vez de caerse
# (§3.1). Todos traen un texto listo para mostrar.
DATA_ERRORS = (
    ErrorFuenteDatos,
    FichaNoDisponible,
    ContenidoNoDisponible,
    ErrorDatosCripta,
    ErrorAlmacenDisco,
)


class InUseIds:
    """La funcion consultar_ids_en_uso que pide la cache (§4.4).

    El repositorio se crea antes que la partida, asi que esta funcion empieza
    sin partida y devuelve una tabla vacia. Cuando la partida existe cuenta los
    enemigos vivos, el inventario y el suelo y las trampas de la sala actual.
    """

    def __init__(self):
        self.repository = None
        self.game = None

    def __call__(self):
        if self.repository is None or self.game is None:
            return TablaHash()

        game = self.game
        room = game.room_map.room(game.player.room_id)
        items = list(game.player.inventory) + list(room.floor_items)

        return self.repository.ids_en_uso(game.enemies, items, room.traps)


def build_game(repository, seed, player_name=None, in_use=None):
    """Arma una partida nueva sobre la cripta que el repositorio ya inicio.

    El historial reversible lo comparten el inventario, el rastro y la agenda,
    para que el pergamino pueda deshacer todo lo que paso en el intervalo.
    """
    data = repository.datos_de_partida()
    state = GameState(seed)
    history = History(state)

    player = (
        repository.crear_jugador()
        if player_name is None
        else repository.crear_jugador(player_name)
    )
    player.inventory = Inventory(data.inventario_max, history)

    room_map = repository.crear_mapa()
    enemies = repository.cargar_contenido_de_sala(room_map.room(player.room_id))

    game = Game(
        state,
        player,
        enemies,
        room_map=room_map,
        exit_room_id=data.sala_salida,
        trail=PlayerTrail(history),
        history=history,
        event_queue=ReversibleEventQueue(history),
    )

    if in_use is not None:
        in_use.game = game

    return game


def new_log_path(crypt_id, directory=LOG_DIRECTORY):
    """partidas/<cripta>-<fecha>-<hora>.log, sin pisar un log existente."""
    os.makedirs(directory, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(directory, f"{crypt_id}-{stamp}.log")
    copy = 1

    while os.path.exists(path):
        copy += 1
        path = os.path.join(directory, f"{crypt_id}-{stamp}-{copy}.log")

    return path


# ----------------------------------------------------------------------
# Lo que la vista necesita y VisibleState todavia no trae
# ----------------------------------------------------------------------


@dataclass
class ExitView:
    direction: str
    destination: int
    is_open: bool


@dataclass
class ItemView:
    name: str
    item_class: str
    weight: int
    value: int
    equipped: bool = False
    current: bool = False


@dataclass
class RoomView:
    name: str
    exits: list
    floor: list


def room_view(game):
    """Salidas y suelo de la sala del jugador, solo para mostrar."""
    room = game.room_map.room(game.player.room_id)
    exits = [
        ExitView(exit_.direction, exit_.destination, exit_.door.is_open)
        for exit_ in room.exits()
    ]
    floor = [_item_view(game.player, item) for item in room.floor_items]

    return RoomView(room.name, exits, floor)


def inventory_view(game, criterion=None):
    """El inventario en su orden real, o una copia ordenada (§4.5).

    La vista ordenada no cambia el orden real ni el cursor, por eso no pasa
    por el controlador ni queda en la bitacora.
    """
    inventory = game.player.inventory
    items = list(inventory) if criterion is None else inventory.sorted_view(criterion)
    current = inventory.current()

    return [
        _item_view(game.player, item, current=item is current) for item in items
    ]


def _item_view(player, item, current=False):
    equipped = item is player.equipped_weapon or item is player.equipped_armor

    return ItemView(item.name, item.item_class, item.weight, item.value, equipped, current)


# ----------------------------------------------------------------------
# Partida interactiva
# ----------------------------------------------------------------------


def choose_crypt(repository, view, crypt_id=None):
    """Lista las criptas publicadas y deja elegir una. None si se cancela."""
    crypts = repository.listar_criptas()

    if crypt_id is not None:
        return crypt_id

    view.show_crypts(crypts)

    while True:
        text = view.read_line("Cripta (numero o id, vacio para salir): ")

        if text is None or not text.strip():
            return None

        text = text.strip()

        if text.isdigit() and 1 <= int(text) <= len(crypts):
            return crypts[int(text) - 1]["id"]

        for crypt in crypts:
            if crypt["id"] == text:
                return text

        view.show_message(f"No hay ninguna cripta '{text}'.")


def ask_player_name(view):
    """Nombre para la tabla de puntajes, o None para el nombre por defecto."""
    text = view.read_line("Nombre del jugador (vacio para el de siempre): ")

    if text is None or not text.strip():
        return None

    return text.strip()


def load_saved_game(repository, view, load_path, in_use=None):
    """Arma la partida guardada de load_path (§4.10).

    Devuelve (game, id_cripta, semilla), o (None, None, None) si el archivo no
    se pudo usar. El id de la cripta viene adentro del archivo, asi que hay que
    leerlo antes de poder iniciar el repositorio y comprobar las versiones.
    """
    partida = cargar_partida(load_path)

    if not partida.id_cripta:
        view.show_message(
            f"{load_path} no dice de que cripta es la partida."
        )
        return None, None, None

    repository.iniciar_partida(partida.id_cripta)
    comprobar_versiones_vigentes(partida, repository)
    game = construir_juego_reversible(partida)

    if in_use is not None:
        in_use.game = game

    view.show_message(
        f"Partida cargada de {load_path}: "
        f"{partida.player_actions} acciones jugadas, reloj en {partida.clock}."
    )

    return game, partida.id_cripta, partida.seed


def play(repository, view, seed, crypt_id=None, player_name=None, in_use=None,
         log_directory=LOG_DIRECTORY, scoreboard=None, load_path=None):
    """Juega una partida completa con la vista de consola.

    Devuelve el Game al terminar, o None si no se llego a empezar. Si la
    partida termina en victoria o derrota y hay tabla de puntajes, la registra
    y muestra el ranking de esa cripta (§2.12). Una partida interrumpida con
    salir no entra en la tabla.

    Con load_path la partida sale de un archivo guardado (§4.10) en vez de
    empezar de cero. Se carga antes de abrir la bitacora, y la cabecera anota
    de que archivo salio y su huella, para que --replay arranque desde ese
    estado (§4.11).

    El comando cargar a media partida cierra la sesion actual, cuya bitacora
    queda completa y reproducible hasta ahi, y abre una sesion nueva con su
    propia bitacora, igual que --cargar. Una bitacora nunca mezcla dos partidas.
    """
    while True:
        repository.empezar_conteo_de_partida()
        header_extra = ("", "")

        if load_path is not None:
            game, crypt_id, seed = load_saved_game(
                repository, view, load_path, in_use
            )

            if game is None:
                return None

            header_extra = (load_path, file_digest(load_path))
        else:
            crypt_id = choose_crypt(repository, view, crypt_id)

            if crypt_id is None:
                return None

            repository.iniciar_partida(crypt_id)
            game = build_game(repository, seed, player_name, in_use)

        crypt, crypt_version, catalog_version = repository.versiones_de_la_partida()
        header = ReplayHeader(
            crypt, crypt_version, catalog_version, seed, *header_extra
        )
        log_path = new_log_path(crypt, log_directory)

        view.show_message(
            f"Partida en {crypt} (version {crypt_version}), semilla {seed}. "
            f"Bitacora: {log_path}"
        )
        view.show_message("Escriba ayuda para ver los comandos.")

        with ReplayLogWriter(log_path, header) as log:
            controller = GameController(game, log, repository)
            load_path = _command_loop(controller, view)

        if load_path is None:
            break

        view.show_message(_ending_text(game))
        view.show_message(f"Bitacora cerrada: {log_path}. Cargando {load_path}.")

    view.show_message(_ending_text(game))

    if scoreboard is not None and game.result in (VICTORY, DEFEAT):
        record_score(scoreboard, game, crypt, crypt_version, view)

    return game


def record_score(scoreboard, game, crypt_id, crypt_version, view, limit=10):
    entry = ScoreEntry(
        game.player.name,
        crypt_id,
        crypt_version,
        game.result,
        game.player_actions,
        game.enemies_defeated,
        game.state.clock,
    )

    try:
        scoreboard.add(entry)
        view.show_scores(scoreboard.ranking(crypt_id, limit), crypt_id)
    except (OSError, ScoreboardError) as error:
        view.show_message(f"No se pudo registrar el puntaje: {error}")


def _command_loop(controller, view):
    game = controller.game
    show = True

    while not controller.is_over:
        if show:
            view.show_state(controller.visible_state())
            view.show_room(room_view(game))

        show = True
        text = view.read_command()

        if text is None:
            return

        try:
            command = parse_command(text)
        except CommandError as error:
            view.show_message(str(error))
            show = False
            continue

        if command.name == QUIT:
            return

        if command.name == HELP:
            view.show_help()
            show = False
            continue

        if command.name == VIEW:
            view.show_inventory(inventory_view(game, command.argument), command.argument)
            show = False
            continue

        if command.name == SAVE:
            try:
                escritos = guardar_partida(
                    controller.game, command.argument, controller.repository
                )
            except OSError as error:
                view.show_message(f"No se pudo guardar: {error}")
            else:
                view.show_message(
                    f"Partida guardada en {command.argument} "
                    f"({escritos} bytes)."
                )

            show = False
            continue

        if command.name == LOAD:
            # Se revisa el archivo antes de soltar la partida actual: si no
            # sirve, el jugador sigue donde estaba. play() cierra esta
            # bitacora y abre otra para la partida cargada.
            problem = _saved_game_problem(command.argument, controller.repository)

            if problem is None:
                return command.argument

            view.show_message(f"No se pudo cargar: {problem}")
            show = False
            continue

        if not is_game_action(command):
            view.show_message(f"Comando sin atender: '{command.name}'.")
            continue

        try:
            result = controller.execute(command)
        except DATA_ERRORS as error:
            view.show_message(str(error))
            continue

        if not result.accepted:
            view.show_message(result.message)
            show = False

    if controller.is_over:
        view.show_state(controller.visible_state())

    return None


def _saved_game_problem(path, repository):
    """Por que no se puede cargar path, o None si se puede.

    Lee el archivo completo y, si es de la misma cripta, compara sus versiones
    con las de la sesion. Si es de otra cripta, sus versiones se comprueban al
    cargarla, porque para eso hay que iniciar el repositorio con esa cripta.
    """
    try:
        partida = cargar_partida(path)
    except FileNotFoundError:
        return f"no existe el archivo {path}."
    except OSError as error:
        return f"no se pudo leer {path}: {error}"
    except (ArchivoDePartidaDanado, PartidaIncompatible) as error:
        return str(error)

    if not partida.id_cripta:
        return f"{path} no dice de que cripta es la partida."

    crypt, _, _ = repository.versiones_de_la_partida()

    if partida.id_cripta == crypt:
        try:
            comprobar_versiones_vigentes(partida, repository)
        except PartidaIncompatible as error:
            return str(error)

    return None


def _ending_text(game):
    if game.result == VICTORY:
        outcome = "Victoria"
    elif game.result == DEFEAT:
        outcome = "Derrota"
    else:
        outcome = "Partida interrumpida"

    return (
        f"{outcome}. Reloj final {game.state.clock}, "
        f"acciones {game.player_actions}, "
        f"enemigos derrotados {game.enemies_defeated}."
    )


# ----------------------------------------------------------------------
# Reproduccion (--replay)
# ----------------------------------------------------------------------


def replay(repository, log_path, output=print, in_use=None, verbose=True):
    """Reproduce un log sin interaccion (§4.11). Devuelve el Game o None.

    Si la fuente no tiene las versiones del log lo informa y no reproduce:
    nunca reproduce en silencio contra datos distintos.
    """
    log = read_replay_log(log_path)
    header = log.header

    repository.empezar_conteo_de_partida()

    try:
        repository.iniciar_partida(
            header.crypt_id, (header.crypt_version, header.catalog_version)
        )
    except VersionesIncompatibles as error:
        # El mensaje ya explica que no se puede garantizar una reproduccion fiel.
        output(str(error))
        return None

    if header.saved_game:
        game = _game_from_logged_save(header, output)

        if game is None:
            return None

        if in_use is not None:
            in_use.game = game
    else:
        game = build_game(repository, header.seed, in_use=in_use)

    controller = GameController(game, repository=repository)

    output(
        f"Reproduciendo {log_path}: {header.crypt_id} (version "
        f"{header.crypt_version}), semilla {header.seed}, "
        f"{len(log.commands)} acciones."
    )

    def show_step(logged, result):
        if verbose:
            output(
                f"[{game.state.clock:>6}] {logged.command.to_text():<16} "
                f"{result.message}"
            )

    try:
        replay_commands(controller, log.commands, show_step)
    except ReplayDivergence as error:
        output(f"La reproduccion diverge de la partida original. {error}")
        return game

    output(_ending_text(game))

    return game


def _game_from_logged_save(header, output):
    """El estado inicial de un log que empezo cargando un guardado, o None.

    Sin el mismo archivo no hay reproduccion fiel: si falta o su huella no es
    la de la cabecera, se informa y no se reproduce (§4.11). Las versiones de
    cripta y catalogo ya se comprobaron con las de la cabecera.
    """
    path = header.saved_game
    cannot = (
        "No se puede garantizar una reproduccion fiel: el log empieza desde "
        f"la partida guardada {path}"
    )

    try:
        digest = file_digest(path)
    except OSError:
        output(f"{cannot}, y ese archivo no esta.")
        return None

    if digest != header.saved_game_digest:
        output(f"{cannot}, y ese archivo cambio desde que se jugo.")
        return None

    try:
        partida = cargar_partida(path)
    except (OSError, ArchivoDePartidaDanado, PartidaIncompatible) as error:
        output(f"{cannot}, y no se pudo leer: {error}")
        return None

    if partida.id_cripta != header.crypt_id:
        output(f"{cannot}, que es de otra cripta ({partida.id_cripta}).")
        return None

    return construir_juego_reversible(partida)
