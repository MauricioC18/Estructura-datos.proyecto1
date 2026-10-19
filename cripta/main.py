"""Punto de entrada de CRIPTA.

Uso, desde la carpeta cripta/:
    python main.py                          jugar contra el API
    python main.py --offline                jugar con los datos de datos_offline/
    python main.py --offline CARPETA        jugar con otro paquete sin conexion
    python main.py --replay partida.log     reproducir una partida sin interaccion
    python main.py --bench                  medir los subsistemas

    python main.py --puntajes [CRIPTA]      mostrar la tabla de puntajes

Otras opciones: --cripta ID, --semilla N, --nombre TEXTO, --cache-size N,
--cache CARPETA. Solo interpreta las banderas y conecta los componentes; el
flujo esta en controller/application.py y las reglas en el modelo.
"""
import argparse
import random
import sys

from structures.cache_catalogo import CAPACIDAD_POR_DEFECTO


DEFAULT_OFFLINE_DIRECTORY = "datos_offline"
DEFAULT_CACHE_DIRECTORY = "cache_cripta"
DEFAULT_SCORES_PATH = "puntajes.txt"


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        description="CRIPTA: juego de mazmorra dirigido por eventos."
    )
    parser.add_argument(
        "--offline",
        nargs="?",
        const=DEFAULT_OFFLINE_DIRECTORY,
        metavar="CARPETA",
        help=f"leer las respuestas desde disco (por defecto {DEFAULT_OFFLINE_DIRECTORY})",
    )
    parser.add_argument(
        "--cache-size",
        type=int,
        default=CAPACIDAD_POR_DEFECTO,
        help=f"fichas del catalogo en memoria (por defecto {CAPACIDAD_POR_DEFECTO})",
    )
    parser.add_argument(
        "--cache",
        default=DEFAULT_CACHE_DIRECTORY,
        metavar="CARPETA",
        help=f"carpeta de la cache persistente (por defecto {DEFAULT_CACHE_DIRECTORY})",
    )
    parser.add_argument("--replay", metavar="LOG", help="reproducir una partida registrada")
    parser.add_argument(
        "--cargar",
        metavar="ARCHIVO",
        help="continuar una partida guardada con el comando guardar",
    )
    parser.add_argument("--bench", action="store_true", help="medir los subsistemas")
    parser.add_argument("--cripta", metavar="ID", help="id de la cripta, sin preguntar")
    parser.add_argument("--semilla", type=int, help="semilla de la partida")
    parser.add_argument("--nombre", help="nombre del jugador")
    parser.add_argument(
        "--puntajes",
        nargs="?",
        const="",
        metavar="CRIPTA",
        help="mostrar la tabla de puntajes, de todas las criptas o de una",
    )

    arguments = parser.parse_args(argv)

    if arguments.cache_size < 1:
        parser.error("--cache-size debe ser al menos 1.")

    if arguments.replay and arguments.bench:
        parser.error("--replay y --bench no se pueden usar juntos.")

    return arguments


def make_repository(arguments, in_use):
    """Crea la fuente (red o disco) y el repositorio del bloque 2.

    Es el unico lugar donde se decide si los datos vienen de HTTP o de
    archivos (§3.4): el resto del programa recibe el mismo repositorio.
    """
    from adapters.fuente_http import FuenteHttp
    from adapters.fuente_offline import FuenteOffline
    from repository.repositorio_cripta import RepositorioCripta

    source = FuenteOffline(arguments.offline) if arguments.offline else FuenteHttp()
    repository = RepositorioCripta(source, arguments.cache, arguments.cache_size, in_use)
    in_use.repository = repository

    return repository


def print_network_report(repository):
    """Lo que §5.1 pide reportar al terminar la partida."""
    print()
    for line in repository.reporte_de_red().lineas_de_texto():
        print(line)


def run_scores(arguments):
    from adapters.scoreboard import Scoreboard, ScoreboardError
    from view.console_view import ConsoleView

    crypt_id = arguments.puntajes or None

    try:
        entries = Scoreboard(DEFAULT_SCORES_PATH).ranking(crypt_id)
    except ScoreboardError as error:
        print(f"Error: {error}")
        return 1

    ConsoleView().show_scores(entries, crypt_id)
    return 0


def run_bench():
    from benchmark.benchmark import main as bench_main

    bench_main()
    return 0


def run_replay(arguments):
    from controller.application import DATA_ERRORS, InUseIds, replay
    from replay.replay_log import ReplayLogError

    in_use = InUseIds()

    try:
        repository = make_repository(arguments, in_use)
        game = replay(repository, arguments.replay, in_use=in_use)
    except FileNotFoundError:
        print(f"No existe el log '{arguments.replay}'.")
        return 1
    except ReplayLogError as error:
        print(f"El log no se puede leer: {error}")
        return 1
    except DATA_ERRORS as error:
        print(f"Error: {error}")
        return 1

    if game is None:
        return 1

    print_network_report(repository)

    return 0


def run_game(arguments):
    from adapters.almacen_partida import ArchivoDePartidaDanado, PartidaIncompatible
    from adapters.scoreboard import Scoreboard
    from controller.application import DATA_ERRORS, InUseIds, ask_player_name, play
    from view.console_view import ConsoleView

    seed = arguments.semilla
    if seed is None:
        # La semilla de la partida se elige aqui, fuera del modelo, y queda en
        # la bitacora. El modelo usa solo su propio random.Random(semilla).
        seed = random.SystemRandom().randrange(1, 2**31)

    in_use = InUseIds()
    view = ConsoleView()

    try:
        repository = make_repository(arguments, in_use)
        name = None

        if arguments.cargar is None:
            name = arguments.nombre if arguments.nombre else ask_player_name(view)

        game = play(
            repository, view, seed, arguments.cripta, name, in_use,
            scoreboard=Scoreboard(DEFAULT_SCORES_PATH),
            load_path=arguments.cargar,
        )
    except DATA_ERRORS as error:
        print(f"Error: {error}")
        return 1
    except (PartidaIncompatible, ArchivoDePartidaDanado) as error:
        print(f"Error: {error}")
        return 1
    except OSError as error:
        print(f"Error: no se pudo leer {arguments.cargar}: {error}")
        return 1
    except KeyboardInterrupt:
        print("\nSesion terminada.")
        return 0

    if game is not None:
        print_network_report(repository)

    return 0


def main(argv=None):
    arguments = parse_arguments(argv)

    if arguments.puntajes is not None:
        return run_scores(arguments)

    if arguments.bench:
        return run_bench()

    if arguments.replay:
        return run_replay(arguments)

    return run_game(arguments)


if __name__ == "__main__":
    sys.exit(main())
