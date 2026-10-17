from dataclasses import dataclass

from structures.tabla_hash import TablaHash

DIRECTIONS = ("N", "S", "E", "O")


def direction_index(direction):
    """Posicion de una direccion en DIRECTIONS. Son 4, asi que es O(1)."""
    for index in range(len(DIRECTIONS)):
        if DIRECTIONS[index] == direction:
            return index

    raise ValueError(f"Direccion invalida: {direction!r}. Se esperaba N, S, E u O.")


class Door:
    """La puerta de un paso entre dos salas.

    Es un solo objeto compartido por las dos salas que conecta, de modo que
    abrirla o cerrarla se ve igual desde ambos lados (§2.1, §2.5). Si la salida
    de vuelta no existe, el paso es de un solo sentido y la puerta solo aparece
    en la sala que la declara.

    key_id es el id de la ficha llave que la abre (§2.7); auto_close es el
    intervalo de cierre automatico, o None si la puerta no se cierra sola.
    """

    def __init__(self, room_a, room_b, closed=False, key_id=None, auto_close=None):
        self.room_a = room_a
        self.room_b = room_b
        self.closed = closed
        self.key_id = key_id
        self.auto_close = auto_close

    @property
    def is_open(self):
        return not self.closed

    def connects(self, room_id):
        return room_id == self.room_a or room_id == self.room_b

    def other_side(self, room_id):
        if room_id == self.room_a:
            return self.room_b

        if room_id == self.room_b:
            return self.room_a

        raise ValueError(f"La puerta no conecta con la sala {room_id}.")


@dataclass
class Exit:
    """Una salida de una sala: hacia donde, a que sala lleva y por cual puerta."""

    direction: str
    destination: int
    door: Door


class Room:
    """Una sala: sus salidas y lo que hay en el suelo.

    Las salidas se guardan en una lista fija de 4 posiciones, una por
    direccion, en lugar de un dict (§7).

    floor_items conserva el orden del contenido, porque recoger un objeto se
    hace por su posicion en el suelo. Los enemigos no se guardan aqui: el motor
    los lleva en su propia lista, cada uno con su room_id, porque se mueven
    entre salas.

    content_loaded indica si el contenido de la sala ya entro al modelo. Que
    entre no activa a los enemigos; eso ocurre cuando el jugador entra (§2.4).
    """

    def __init__(self, room_id, name):
        self.room_id = room_id
        self.name = name
        self._exits = [None] * len(DIRECTIONS)
        self.floor_items = []
        self.traps = []
        self.content_loaded = False

    def add_exit(self, exit_):
        index = direction_index(exit_.direction)
        if self._exits[index] is not None:
            raise ValueError(
                f"La sala {self.room_id} ya tiene una salida hacia {exit_.direction}."
            )

        self._exits[index] = exit_

    def exit_towards(self, direction):
        """La salida en esa direccion, o None si no existe."""
        return self._exits[direction_index(direction)]

    def exits(self):
        """Las salidas que existen, en orden N, S, E, O."""
        result = []
        for exit_ in self._exits:
            if exit_ is not None:
                result.append(exit_)

        return result


class RoomMap:
    """Todas las salas de la cripta, buscables por id en O(1) promedio."""

    def __init__(self):
        self._rooms_by_id = TablaHash()
        self._ids_in_order = []

    def add(self, room):
        if self._rooms_by_id.contiene(room.room_id):
            raise ValueError(f"La sala {room.room_id} esta repetida.")

        self._rooms_by_id.insertar(room.room_id, room)
        self._ids_in_order.append(room.room_id)

    def contains(self, room_id):
        return self._rooms_by_id.contiene(room_id)

    def room(self, room_id):
        room = self._rooms_by_id.obtener(room_id)
        if room is None:
            raise ValueError(f"La sala {room_id} no existe en esta cripta.")

        return room

    def room_ids(self):
        """Ids en el orden del esqueleto."""
        return list(self._ids_in_order)

    def __len__(self):
        return len(self._ids_in_order)
