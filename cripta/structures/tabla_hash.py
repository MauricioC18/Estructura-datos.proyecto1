"""
Tabla hash propia con encadenamiento.

Problema que resuelve
    Buscar un valor por su clave sin recorrer todos los elementos y sin usar
    dict, que el enunciado prohíbe como índice, caché o tabla de búsqueda (§7).

Usos previstos en CRIPTA
    Caché del catálogo, salas por id, enemigos por instancia, ids pendientes
    de pedir al API y salas ya solicitadas.

Cómo funciona
    - La tabla tiene un arreglo de "cubetas" (una list de Python, permitida
      por §7 como almacenamiento contiguo). Cada cubeta es una lista corta de
      entradas (clave, valor).
    - La función hash convierte la clave en un número, y ese número decide
      la cubeta. Buscar, insertar o eliminar solo revisa esa cubeta.
    - La capacidad siempre es una potencia de 2. Así la cubeta se calcula con
      hash & (capacidad - 1), que da lo mismo que hash % capacidad pero es
      una operación más barata.
    - Cuando hay más de 0,75 entradas por cubeta en promedio (factor de
      carga), la capacidad se duplica y todas las entradas se redistribuyen.

Complejidad (n = cantidad de entradas)
    insertar, obtener, contiene, eliminar: O(1) promedio, O(n) peor caso
        (el peor caso ocurre si todas las claves caen en la misma cubeta).
    redimensionar: O(n), pero solo ocurre cuando n se duplica, así que su
        costo repartido entre las inserciones es O(1) amortizado.
    espacio: O(n + capacidad).

Orden de claves()
    Con una función hash determinista, el orden es el mismo en cada ejecución
    para la misma secuencia de operaciones. Pero no es el orden de inserción
    ni un orden alfabético: ninguna regla del juego debe depender de él.

Límite conocido
    La tabla no se encoge al eliminar. Después de muchas eliminaciones
    conserva su capacidad máxima alcanzada.
"""
from structures.funciones_hash import hash_crc32

CAPACIDAD_INICIAL = 8


class _Entrada:
    """Un par clave-valor guardado dentro de una cubeta."""

    __slots__ = ("clave", "valor")  # fija los atributos y ahorra memoria

    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor


class TablaHash:
    """Tabla hash con encadenamiento y redimensionamiento automático."""

    def __init__(self, capacidad_inicial=CAPACIDAD_INICIAL, funcion_hash=hash_crc32):
        if capacidad_inicial < 1:
            raise ValueError("La capacidad inicial debe ser al menos 1")
        capacidad = 1
        while capacidad < capacidad_inicial:  # redondear a potencia de 2
            capacidad *= 2
        self._funcion_hash = funcion_hash
        self._capacidad = capacidad
        self._cubetas = self._crear_cubetas(capacidad)
        self._cantidad = 0

    # ------------------------------------------------------------------
    # Operaciones principales
    # ------------------------------------------------------------------

    def insertar(self, clave, valor):
        """Guarda valor bajo clave. Si la clave ya existe, reemplaza su valor."""
        cubeta = self._cubeta_de(clave)
        for entrada in cubeta:
            if entrada.clave == clave:
                entrada.valor = valor
                return
        cubeta.append(_Entrada(clave, valor))
        self._cantidad += 1
        if self._cantidad * 4 > self._capacidad * 3:  # factor de carga > 0,75
            self._redimensionar(self._capacidad * 2)

    def obtener(self, clave, por_defecto=None):
        """Devuelve el valor de clave, o por_defecto si la clave no existe."""
        for entrada in self._cubeta_de(clave):
            if entrada.clave == clave:
                return entrada.valor
        return por_defecto

    def contiene(self, clave):
        """Indica si la clave existe (sirve aunque el valor guardado sea None)."""
        for entrada in self._cubeta_de(clave):
            if entrada.clave == clave:
                return True
        return False

    def eliminar(self, clave):
        """Elimina la clave. Devuelve True si existía y False si no."""
        cubeta = self._cubeta_de(clave)
        for posicion in range(len(cubeta)):
            if cubeta[posicion].clave == clave:
                del cubeta[posicion]
                self._cantidad -= 1
                return True
        return False

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def tamano(self):
        return self._cantidad

    def esta_vacia(self):
        return self._cantidad == 0

    def capacidad(self):
        return self._capacidad

    def claves(self):
        """Lista con todas las claves (ver la nota sobre su orden arriba)."""
        resultado = []
        for cubeta in self._cubetas:
            for entrada in cubeta:
                resultado.append(entrada.clave)
        return resultado

    def longitud_maxima_cubeta(self):
        """Cantidad de entradas de la cubeta más llena (mide las colisiones)."""
        maximo = 0
        for cubeta in self._cubetas:
            if len(cubeta) > maximo:
                maximo = len(cubeta)
        return maximo

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _cubeta_de(self, clave):
        return self._cubetas[self._funcion_hash(clave) & (self._capacidad - 1)]

    def _redimensionar(self, nueva_capacidad):
        cubetas_viejas = self._cubetas
        self._capacidad = nueva_capacidad
        self._cubetas = self._crear_cubetas(nueva_capacidad)
        for cubeta in cubetas_viejas:
            for entrada in cubeta:
                self._cubeta_de(entrada.clave).append(entrada)

    @staticmethod
    def _crear_cubetas(capacidad):
        return [[] for _ in range(capacidad)]
