import hashlib
from dataclasses import dataclass

from controller.commands import CommandError, is_game_action, parse_command


FORMAT_VERSION = 1

TITLE = "# CRIPTA replay"
SEPARATOR = "---"

FORMAT_KEY = "formato"
CRYPT_KEY = "cripta"
CRYPT_VERSION_KEY = "version_cripta"
CATALOG_VERSION_KEY = "version_catalogo"
SEED_KEY = "semilla"
SAVED_GAME_KEY = "partida_cargada"
SAVED_GAME_DIGEST_KEY = "huella_partida"


class ReplayLogError(ValueError):
    """El archivo no es un log de reproduccion valido o es de otro formato."""


@dataclass
class ReplayHeader:
    """Lo minimo que exige la seccion 4.11 para reproducir fielmente."""

    crypt_id: str
    crypt_version: str
    catalog_version: str
    seed: int
    # Solo en una sesion que empezo cargando un guardado (§4.10): de que
    # archivo salio y su huella SHA-256, para reproducir desde ese estado y no
    # desde el instante 0. Vacios en una partida nueva.
    saved_game: str = ""
    saved_game_digest: str = ""


@dataclass
class LoggedCommand:
    line_number: int
    command: object


@dataclass
class ReplayLog:
    header: ReplayHeader
    commands: list


class ReplayLogWriter:
    """Bitacora de solo anexado de una partida (seccion 4.11).

    Escribe la cabecera al crearla y luego una linea por accion aceptada, en su
    forma canonica. Cada linea se vacia a disco al escribirla, para que el log
    sirva para reproducir un error aunque el programa termine de golpe.

    Se abre en modo "x": un log existente nunca se sobrescribe.
    """

    def __init__(self, path, header):
        _check_value(header.crypt_id, CRYPT_KEY)
        _check_value(header.crypt_version, CRYPT_VERSION_KEY)
        _check_value(header.catalog_version, CATALOG_VERSION_KEY)

        self.path = path
        self._file = open(path, "x", encoding="utf-8", newline="\n")
        self._write_line(TITLE)
        self._write_line(f"{FORMAT_KEY}={FORMAT_VERSION}")
        self._write_line(f"{CRYPT_KEY}={header.crypt_id}")
        self._write_line(f"{CRYPT_VERSION_KEY}={header.crypt_version}")
        self._write_line(f"{CATALOG_VERSION_KEY}={header.catalog_version}")
        self._write_line(f"{SEED_KEY}={header.seed}")

        if header.saved_game:
            _check_value(header.saved_game, SAVED_GAME_KEY)
            _check_value(header.saved_game_digest, SAVED_GAME_DIGEST_KEY)
            self._write_line(f"{SAVED_GAME_KEY}={header.saved_game}")
            self._write_line(f"{SAVED_GAME_DIGEST_KEY}={header.saved_game_digest}")

        self._write_line(SEPARATOR)

    def append(self, command):
        self._write_line(command.to_text())

    def close(self):
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.close()

    def _write_line(self, text):
        self._file.write(text + "\n")
        self._file.flush()


def read_replay_log(path):
    """Lee un log completo y devuelve su cabecera y sus comandos.

    Las lineas vacias y las que empiezan con # se ignoran en el cuerpo, para
    poder anotar a mano un log al reportar un error. Lanza ReplayLogError con el
    numero de linea si algo no se puede interpretar.
    """
    with open(path, encoding="utf-8") as file:
        lines = file.read().splitlines()

    separator_index = _find_separator(lines)
    header = _parse_header(lines[:separator_index])
    commands = []

    for index in range(separator_index + 1, len(lines)):
        text = lines[index].strip()

        if not text or text.startswith("#"):
            continue

        commands.append(LoggedCommand(index + 1, _parse_body_line(text, index + 1)))

    return ReplayLog(header, commands)


def _find_separator(lines):
    if not lines or lines[0].strip() != TITLE:
        raise ReplayLogError(
            f"El archivo no es un log de reproduccion de CRIPTA: falta '{TITLE}'."
        )

    for index in range(len(lines)):
        if lines[index].strip() == SEPARATOR:
            return index

    raise ReplayLogError(f"La cabecera del log no termina con '{SEPARATOR}'.")


def _parse_header(lines):
    format_version = None
    crypt_id = None
    crypt_version = None
    catalog_version = None
    seed = None
    saved_game = ""
    saved_game_digest = ""

    for index in range(1, len(lines)):
        text = lines[index].strip()

        if not text:
            continue

        key, separator, value = text.partition("=")

        if not separator:
            raise ReplayLogError(f"Linea {index + 1}: se esperaba clave=valor.")

        if key == FORMAT_KEY:
            format_version = _integer(value, key, index + 1)
        elif key == CRYPT_KEY:
            crypt_id = value
        elif key == CRYPT_VERSION_KEY:
            crypt_version = value
        elif key == CATALOG_VERSION_KEY:
            catalog_version = value
        elif key == SEED_KEY:
            seed = _integer(value, key, index + 1)
        elif key == SAVED_GAME_KEY:
            saved_game = value
        elif key == SAVED_GAME_DIGEST_KEY:
            saved_game_digest = value
        else:
            raise ReplayLogError(f"Linea {index + 1}: clave desconocida '{key}'.")

    if format_version is None:
        raise ReplayLogError(f"Falta '{FORMAT_KEY}' en la cabecera del log.")

    if format_version != FORMAT_VERSION:
        raise ReplayLogError(
            f"El log usa el formato {format_version} y este programa lee el "
            f"formato {FORMAT_VERSION}. No se puede reproducir."
        )

    _require(crypt_id, CRYPT_KEY)
    _require(crypt_version, CRYPT_VERSION_KEY)
    _require(catalog_version, CATALOG_VERSION_KEY)
    _require(seed, SEED_KEY)

    if bool(saved_game) != bool(saved_game_digest):
        raise ReplayLogError(
            f"La cabecera trae '{SAVED_GAME_KEY}' o '{SAVED_GAME_DIGEST_KEY}' "
            "sin la otra: no se sabe desde que estado reproducir."
        )

    return ReplayHeader(
        crypt_id, crypt_version, catalog_version, seed,
        saved_game, saved_game_digest,
    )


def _parse_body_line(text, line_number):
    try:
        command = parse_command(text)
    except CommandError as error:
        raise ReplayLogError(f"Linea {line_number}: {error}") from error

    if not is_game_action(command):
        raise ReplayLogError(
            f"Linea {line_number}: '{command.name}' no es una accion de partida."
        )

    return command


def _integer(value, key, line_number):
    try:
        return int(value)
    except ValueError:
        raise ReplayLogError(
            f"Linea {line_number}: '{key}' debe ser un entero, se leyo '{value}'."
        ) from None


def _require(value, key):
    if value is None or value == "":
        raise ReplayLogError(f"Falta '{key}' en la cabecera del log.")


def _check_value(value, key):
    if not value or "\n" in value:
        raise ValueError(f"'{key}' no puede estar vacio ni tener saltos de linea.")


def file_digest(path):
    """Huella SHA-256 de un archivo, para saber si un guardado cambio."""
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for block in iter(lambda: file.read(65536), b""):
            digest.update(block)

    return digest.hexdigest()
