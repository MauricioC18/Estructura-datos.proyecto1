from dataclasses import dataclass


MOVE = "mover"
OPEN = "abrir"
ATTACK = "atacar"
WAIT = "esperar"
PICK_UP = "recoger"
DROP = "soltar"
USE = "usar"
EQUIP = "equipar"
NEXT = "sig"
PREVIOUS = "ant"
REWIND = "retroceder"

VIEW = "ver"
SAVE = "guardar"
LOAD = "cargar"
HELP = "ayuda"
QUIT = "salir"

DIRECTIONS = ("N", "S", "E", "O")
SORT_CRITERIA = ("peso", "valor", "nombre")

HELP_LINES = (
    "mover N|S|E|O      moverse a la sala vecina",
    "abrir N|S|E|O      abrir la puerta con la llave",
    "atacar <id>        atacar al enemigo indicado, por ejemplo atacar e-201",
    "esperar            dejar pasar una accion",
    "recoger <n>        recoger el objeto n del suelo, contando desde 0",
    "soltar             soltar el objeto que se esta viendo",
    "usar               usar el objeto que se esta viendo",
    "equipar            equipar el objeto que se esta viendo",
    "sig | ant          ver el objeto siguiente o el anterior del inventario",
    "ver [peso|valor|nombre]  mostrar el inventario, ordenado si se indica",
    "retroceder         usar un pergamino de retroceso",
    "guardar <archivo>  guardar la partida",
    "cargar <archivo>   cargar una partida",
    "ayuda              mostrar esta lista",
    "salir              terminar la sesion",
)


class CommandError(ValueError):
    """El texto escrito no corresponde a ningun comando valido."""


@dataclass
class Command:
    """Comando ya interpretado.

    argument es una direccion, un id de instancia, una posicion del suelo, un
    criterio de orden o un nombre de archivo, segun el comando. Los comandos
    sin argumento lo dejan en None.
    """

    name: str
    argument: str | int | None = None

    def to_text(self):
        """Forma canonica, la que se escribe en la bitacora de reproduccion.

        parse_command(command.to_text()) devuelve un comando igual.
        """
        if self.argument is None:
            return self.name

        return f"{self.name} {self.argument}"


def is_game_action(command):
    """True si el comando lo ejecuta el modelo y puede quedar en la bitacora.

    Los demas (ver, guardar, cargar, ayuda, salir) no cambian el estado de la
    partida o los atiende la aplicacion, no el modelo.
    """
    return command.name in (
        MOVE,
        OPEN,
        ATTACK,
        WAIT,
        PICK_UP,
        DROP,
        USE,
        EQUIP,
        NEXT,
        PREVIOUS,
        REWIND,
    )


def parse_command(text):
    """Convierte una linea escrita por el jugador o leida del log en un Command.

    La palabra del comando no distingue mayusculas; la direccion se normaliza a
    mayuscula. Lanza CommandError con un mensaje listo para mostrar.
    """
    words = text.split()

    if not words:
        raise CommandError("No se escribio ningun comando.")

    name = words[0].lower()
    arguments = words[1:]

    if name in (MOVE, OPEN):
        return Command(name, _direction(name, arguments))

    if name == ATTACK:
        return Command(name, _single_word(name, arguments, "el id del enemigo"))

    if name == PICK_UP:
        return Command(name, _floor_position(arguments))

    if name == VIEW:
        return Command(name, _optional_criterion(arguments))

    if name in (SAVE, LOAD):
        return Command(name, _single_word(name, arguments, "el nombre del archivo"))

    if name in (WAIT, DROP, USE, EQUIP, NEXT, PREVIOUS, REWIND, HELP, QUIT):
        _no_arguments(name, arguments)
        return Command(name)

    raise CommandError(f"Comando desconocido: '{words[0]}'. Escriba ayuda.")


def _direction(name, arguments):
    direction = _single_word(name, arguments, "una direccion N, S, E u O").upper()

    if direction not in DIRECTIONS:
        raise CommandError(
            f"'{arguments[0]}' no es una direccion. Use N, S, E u O."
        )

    return direction


def _floor_position(arguments):
    text = _single_word(PICK_UP, arguments, "la posicion del objeto en el suelo")

    if not text.isdigit():
        raise CommandError(
            f"'{text}' no es una posicion valida. Use un numero desde 0."
        )

    return int(text)


def _optional_criterion(arguments):
    if not arguments:
        return None

    criterion = _single_word(VIEW, arguments, "un criterio").lower()

    if criterion not in SORT_CRITERIA:
        raise CommandError(
            f"'{arguments[0]}' no es un criterio. Use peso, valor o nombre."
        )

    return criterion


def _single_word(name, arguments, what):
    if len(arguments) != 1:
        raise CommandError(f"'{name}' necesita {what}.")

    return arguments[0]


def _no_arguments(name, arguments):
    if arguments:
        raise CommandError(f"'{name}' no lleva argumentos.")
