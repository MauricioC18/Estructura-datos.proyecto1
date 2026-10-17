import sys

from controller.commands import HELP_LINES


class ConsoleView:
    """Vista de consola: muestra el estado visible y recoge lo que escribe el jugador.

    Solo lee el VisibleState que entrega Game; nunca modifica el modelo. La
    salida y la entrada se reciben desde fuera para poder probarla sin teclado.

    Las salidas, el suelo y el inventario llegan como RoomView e ItemView,
    que arma la aplicacion porque VisibleState todavia no los incluye.
    """

    PROMPT = "> "

    def __init__(self, output=None, read_line=input):
        self.output = sys.stdout if output is None else output
        self.read_line_function = read_line

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

    def show_crypts(self, crypts):
        self._print("Criptas publicadas:")

        for number, crypt in enumerate(crypts, start=1):
            self._print(
                f"  {number}. {crypt['id']}  {crypt.get('nombre', '')}  "
                f"({crypt.get('salas', '?')} salas, dificultad "
                f"{crypt.get('dificultad', '?')})"
            )

    def show_room(self, room):
        self._print(f"Estas en: {room.name}")

        if room.exits:
            exits = []

            for exit_ in room.exits:
                state = "" if exit_.is_open else " (cerrada)"
                exits.append(f"{exit_.direction}->{exit_.destination}{state}")

            self._print("Salidas: " + ", ".join(exits))
        else:
            self._print("No hay salidas.")

        if room.floor:
            self._print("En el suelo:")

            for position, item in enumerate(room.floor):
                self._print(f"  {position}. {item.name} ({item.item_class})")

    def show_inventory(self, items, criterion=None):
        if not items:
            self._print("El inventario esta vacio.")
            return

        title = "Inventario" if criterion is None else f"Inventario por {criterion}"
        self._print(f"{title}:")

        for item in items:
            marks = ("> " if item.current else "  ") + ("[E] " if item.equipped else "")
            self._print(
                f"  {marks}{item.name} ({item.item_class}) "
                f"peso {item.weight}, valor {item.value}"
            )

    def show_scores(self, entries, crypt_id=None):
        title = "Puntajes" if crypt_id is None else f"Puntajes de {crypt_id}"

        if not entries:
            self._print(f"{title}: todavia no hay partidas.")
            return

        self._print(f"{title}:")
        self._print(
            f"  {'#':>2}  {'Jugador':<16} {'Cripta':<12} {'Resultado':<9} "
            f"{'Reloj':>7} {'Acciones':>8} {'Enemigos':>8}"
        )

        for place, entry in enumerate(entries, start=1):
            self._print(
                f"  {place:>2}  {entry.player_name[:16]:<16} {entry.crypt_id[:12]:<12} "
                f"{entry.result:<9} {entry.final_clock:>7} "
                f"{entry.player_actions:>8} {entry.enemies_defeated:>8}"
            )

    def read_line(self, prompt):
        """Lee una linea con un mensaje propio, o None si la entrada se cerro."""
        try:
            return self.read_line_function(prompt)
        except EOFError:
            return None

    def read_command(self):
        """Devuelve la linea escrita, o None si la entrada se cerro."""
        try:
            return self.read_line_function(self.PROMPT)
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
