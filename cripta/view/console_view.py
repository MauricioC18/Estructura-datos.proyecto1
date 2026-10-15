import sys

from controller.commands import HELP_LINES


class ConsoleView:
    """Vista de consola: muestra el estado visible y recoge lo que escribe el jugador.

    Solo lee el VisibleState que entrega Game; nunca modifica el modelo. La
    salida y la entrada se reciben desde fuera para poder probarla sin teclado.

    Las salidas, los objetos del suelo y el inventario se agregaran cuando
    VisibleState los incluya.
    """

    PROMPT = "> "

    def __init__(self, output=None, read_line=input):
        self.output = sys.stdout if output is None else output
        self.read_line = read_line

    def show_state(self, state):
        self._print("")
        self._print(f"Reloj {state.clock}   Sala {state.room_id}")
        self._print(
            f"{state.player_name}: vida {state.health}/{state.max_health}, "
            f"ataque {state.attack}, defensa {state.defense}, "
            f"velocidad {state.speed}"
        )
        self._show_effects(state)
        self._show_enemies(state.enemies)
        self._show_messages(state.messages)

    def show_message(self, message):
        self._print(message)

    def show_help(self):
        for line in HELP_LINES:
            self._print(f"  {line}")

    def read_command(self):
        """Devuelve la linea escrita, o None si la entrada se cerro."""
        try:
            return self.read_line(self.PROMPT)
        except EOFError:
            return None

    def _show_effects(self, state):
        names = []

        for effect in state.effects:
            if effect.ends_at is None:
                names.append(effect.name)
            else:
                names.append(f"{effect.name} hasta {effect.ends_at}")

        if names:
            self._print("Efectos: " + ", ".join(names))

    def _show_enemies(self, enemies):
        if not enemies:
            self._print("No hay enemigos a la vista.")
            return

        self._print("Enemigos:")

        for enemy in enemies:
            self._print(
                f"  {enemy.name} [{enemy.actor_id}] "
                f"vida {enemy.health}/{enemy.max_health}"
            )

    def _show_messages(self, messages):
        if not messages:
            return

        self._print("Mensajes:")

        for message in messages:
            self._print(f"  {message}")

    def _print(self, text):
        self.output.write(text + "\n")
