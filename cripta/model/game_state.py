import random


class GameState:
    """Estado temporal de la partida: reloj virtual, numeracion de eventos y azar.

    El reloj es de solo lectura. El motor lo mueve con advance_clock_to(), que
    rechaza retrocesos, y el pergamino de retroceso es el unico autorizado a
    usar rewind_clock_to().
    """

    def __init__(self, seed, clock=0):
        self._clock = clock
        self._next_sequence_number = 0
        self.seed = seed
        self.random_generator = random.Random(seed)

    @property
    def clock(self):
        return self._clock

    def next_sequence(self):
        sequence = self._next_sequence_number
        self._next_sequence_number += 1
        return sequence

    def advance_clock_to(self, time):
        if time < self._clock:
            raise ValueError(
                "El reloj virtual no puede retroceder: "
                f"esta en {self._clock} y se intento avanzar a {time}."
            )

        self._clock = time

    def rewind_clock_to(self, time):
        if time > self._clock:
            raise ValueError(
                "El retroceso no puede adelantar el reloj virtual: "
                f"esta en {self._clock} y se intento retroceder a {time}."
            )

        self._clock = time
