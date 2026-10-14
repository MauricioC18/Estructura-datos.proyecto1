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

    @property
    def sequence_counter(self):
        """Numero que recibira el proximo evento programado."""
        return self._next_sequence_number

    def next_sequence(self):
        sequence = self._next_sequence_number
        self._next_sequence_number += 1
        return sequence

    def random_state(self):
        return self.random_generator.getstate()

    def restore(self, clock, sequence_counter, random_state):
        """Devuelve el estado temporal al guardado en un archivo de partida.

        Es distinto del pergamino de retroceso: cargar una partida debe
        continuar exactamente donde se quedo, de modo que tambien restaura el
        contador de secuencia y el estado del generador aleatorio.
        """
        if clock < 0:
            raise ValueError(
                f"El reloj virtual no puede ser negativo, se recibio {clock}."
            )

        if sequence_counter < 0:
            raise ValueError(
                "El contador de secuencia no puede ser negativo, "
                f"se recibio {sequence_counter}."
            )

        self._clock = clock
        self._next_sequence_number = sequence_counter
        self.random_generator.setstate(random_state)

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
