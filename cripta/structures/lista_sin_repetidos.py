"""
Lista que conserva el orden en que llegan los elementos e ignora repetidos.

Problema que resuelve
    Los ids del catálogo se descubren en un orden que el programa no
    controla y se repiten entre salas (§4.3). Hay que recordarlos en el
    orden de descubrimiento (para que los lotes sean deterministas) y sin
    repetidos (para no pedir dos veces el mismo id).

Cómo funciona
    - elementos: una list de Python con el orden de llegada.
    - una TablaHash con los elementos ya vistos, para saber en O(1)
      promedio si uno nuevo es repetido.

Complejidad
    agregar, contiene: O(1) promedio. Espacio: O(n).
"""
from structures.tabla_hash import TablaHash


class ListaSinRepetidos:
    """Elementos en orden de llegada, cada uno una sola vez."""

    def __init__(self):
        self.elementos = []
        self._ya_vistos = TablaHash()

    def agregar(self, elemento):
        """Agrega el elemento si no estaba. Devuelve True si era nuevo."""
        if self._ya_vistos.contiene(elemento):
            return False
        self._ya_vistos.insertar(elemento, True)
        self.elementos.append(elemento)
        return True

    def contiene(self, elemento):
        return self._ya_vistos.contiene(elemento)

    def cantidad(self):
        return len(self.elementos)
