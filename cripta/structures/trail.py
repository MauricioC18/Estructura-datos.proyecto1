"""
Rastro del jugador (§2.9, §4.7).

Problema que resuelve
    Cada sala recuerda el ultimo instante en que el jugador estuvo alli. Un
    rastreador examina solo las salas vecinas por salidas abiertas y va hacia
    el rastro mas fresco, si tiene menos de 400 unidades de antiguedad.

Estructura
    Una TablaHash de structures/tabla_hash.py: id de sala -> instante. Room no
    tiene un campo de rastro y no es de este modulo modificarla. Las salas sin
    entrada nunca tuvieron rastro.

Caducidad perezosa
    Los rastros viejos no se eliminan. Se detecta que caducaron al
    consultarlos (reloj - rastro < 400), que es una resta. Eliminarlos de
    forma activa necesitaria un evento de expiracion por sala en la agenda:
    mas eventos por ciclo y mas cambios que el retroceso tendria que revertir,
    sin que la decision del rastreador cueste menos.

Complejidad
    mark: O(1) promedio. freshest_exit: O(salidas de la sala), como maximo 4
    salidas con una busqueda O(1) promedio cada una. No depende del tamano de
    la cripta ni del recorrido del jugador. Con k rastreadores que actuan, el
    trabajo del ciclo es O(k).
    Espacio: O(salas visitadas).
"""
from structures.history import CallbackChange
from structures.tabla_hash import TablaHash

TRAIL_LIFETIME = 400


class PlayerTrail:

    def __init__(self, history=None):
        self._times = TablaHash()
        self._history = history

    def mark(self, room_id, time):
        """Anota que el jugador esta en la sala en ese instante.

        El motor debe llamarlo al iniciar la partida con la sala inicial en el
        instante 0 y despues en cada accion aceptada del jugador, con la sala
        en la que queda (§2.9 y Apendice B).
        """
        if self._history is not None:
            if self._times.contiene(room_id):
                self._history.record(
                    CallbackChange(self._times.insertar, room_id, self._times.obtener(room_id))
                )
            else:
                self._history.record(CallbackChange(self._times.eliminar, room_id))

        self._times.insertar(room_id, time)

    def time_at(self, room_id):
        """Instante del ultimo paso del jugador por la sala, o None."""
        return self._times.obtener(room_id)

    def is_fresh(self, room_id, current_time):
        time = self._times.obtener(room_id)
        return time is not None and current_time - time < TRAIL_LIFETIME

    def freshest_exit(self, room, current_time):
        """La salida abierta hacia el rastro mas fresco, o None si no hay.

        Empate de instantes: gana la sala de menor id (§2.9). Devuelve el Exit
        para que Enemy.decide_action() pueda responder (MOVE, salida).
        """
        best_exit = None
        best_time = None

        for exit_ in room.exits():
            if not exit_.door.is_open:
                continue

            time = self._times.obtener(exit_.destination)

            if time is None or current_time - time >= TRAIL_LIFETIME:
                continue

            if (
                best_exit is None
                or time > best_time
                or (time == best_time and exit_.destination < best_exit.destination)
            ):
                best_exit = exit_
                best_time = time

        return best_exit
