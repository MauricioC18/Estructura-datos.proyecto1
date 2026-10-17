"""
Buffer circular y bitacora de los ultimos 20 mensajes (§4.8).

Problema que resuelve
    La interfaz muestra solo los ultimos 20 mensajes. La memoria debe ser
    constante durante toda la partida y agregar un mensaje no puede desplazar
    fisicamente a los 19 anteriores.

Como funciona
    Un arreglo fijo de `capacidad` posiciones (list de Python, permitida por §7
    como almacenamiento contiguo), un indice `_start` al elemento mas antiguo y
    un contador. Al llenarse, el mensaje nuevo sobrescribe al mas antiguo y
    `_start` avanza una posicion con aritmetica modular. Nada se mueve.

Complejidad
    append, last, pop_last: O(1). Recorrer: O(capacidad). Espacio: O(capacidad).

CircularBuffer tambien lo usa structures/history.py para guardar como maximo
5 acciones del jugador y descartar la mas antigua.
"""

LOG_CAPACITY = 20


class CircularBuffer:

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError(f"La capacidad debe ser al menos 1, se recibio {capacity}.")

        self._slots = [None] * capacity
        self._capacity = capacity
        self._start = 0
        self._count = 0

    @property
    def capacity(self):
        return self._capacity

    def __len__(self):
        return self._count

    def is_empty(self):
        return self._count == 0

    def is_full(self):
        return self._count == self._capacity

    def append(self, element):
        """Agrega al final. Si estaba lleno devuelve el elemento descartado."""
        if self._count == self._capacity:
            discarded = self._slots[self._start]
            self._slots[self._start] = element
            self._start = (self._start + 1) % self._capacity
            return discarded

        self._slots[(self._start + self._count) % self._capacity] = element
        self._count += 1
        return None

    def last(self):
        if self._count == 0:
            raise IndexError("El buffer esta vacio.")

        return self._slots[(self._start + self._count - 1) % self._capacity]

    def pop_last(self):
        if self._count == 0:
            raise IndexError("El buffer esta vacio.")

        index = (self._start + self._count - 1) % self._capacity
        element = self._slots[index]
        self._slots[index] = None
        self._count -= 1
        return element

    def clear(self):
        for index in range(self._capacity):
            self._slots[index] = None

        self._start = 0
        self._count = 0

    def __iter__(self):
        """Del mas antiguo al mas reciente."""
        for offset in range(self._count):
            yield self._slots[(self._start + offset) % self._capacity]


class CircularLog(CircularBuffer):
    """Bitacora en pantalla. Cumple el contrato de Game: append() y recorrer."""

    def __init__(self, capacity=LOG_CAPACITY):
        super().__init__(capacity)

    def append(self, message):
        super().append(str(message))
