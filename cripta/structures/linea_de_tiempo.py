"""
Linea de tiempo de la partida: lo que hace falta para reconstruir el pasado.

Problema que resuelve
    Responder como estaba la partida en cualquier instante anterior, sin
    tocarla y sin guardar una copia del mundo por cada accion (seccion 3.6 y
    5.5 del enunciado de la segunda parte).

Que guarda, y que no
    Tres listas contiguas, y nada mas:
      - las acciones del jugador, con su nombre, su argumento y el reloj al
        que ocurrieron. Es un registro diminuto: lo justo para repetirlas.
      - las copias completas del estado, en bytes, una cada K acciones. Son
        los puntos de control que el enunciado permite.
    Un pergamino fuerza una copia, porque deja la partida en un estado que la
    lista de acciones no puede reproducir: devuelve el reloj pero no el estado
    del generador aleatorio, y ademas consume un pergamino del inventario, que
    no es una accion del jugador.

    Esta estructura NO reconstruye nada y no conoce el motor. Solo guarda y
    localiza. Quien reconstruye es model/consulta_historia.py.

Busqueda binaria propia
    Localizar de que copia partir, y traducir un instante del reloj a un
    numero de accion, son busquedas frecuentes sobre listas que ya estan
    ordenadas porque se construyen en orden. Se resuelven con busqueda
    binaria escrita aqui: bisect esta prohibido (P1 seccion 7).

Complejidad (A = acciones, C = copias)
    registrar_accion: O(1).
    guardar_copia: O(1) mas lo que cueste armar el bloque, que es de quien lo
        arma.
    copia_para_accion, accion_en_instante: O(log C) y O(log A).
    recortar_ultima_accion: O(1). No recorre la historia.
    espacio: O(A + ((A/K) + pergaminos) * tamano del estado).
"""

# Acciones del jugador entre dos copias completas del estado. El valor sale de
# las mediciones de la capacidad: con 50, la memoria de las copias queda 43
# veces por debajo de la alternativa ingenua de una copia por accion, y una
# consulta sigue cerca de 1 ms. Se configura por partida.
COPIAS_CADA = 50


class AccionRegistrada:
    """Lo justo para repetir una accion del jugador.

    argumento es una direccion, un id de enemigo, una posicion del suelo o el
    id de un objeto del inventario, segun la accion. Para soltar, usar y
    equipar es el id del objeto y no su posicion, porque el cursor del
    inventario lo mueven comandos que no son acciones y la posicion no se
    podria repetir.
    """

    __slots__ = ("nombre", "argumento", "reloj")

    def __init__(self, nombre, argumento, reloj):
        self.nombre = nombre
        self.argumento = argumento
        self.reloj = reloj


class CopiaDelEstado:
    """Punto de control: el estado completo en bytes, y donde se tomo."""

    __slots__ = ("acciones", "reloj", "bloque")

    def __init__(self, acciones, reloj, bloque):
        self.acciones = acciones
        self.reloj = reloj
        self.bloque = bloque



class LineaDeTiempo:
    """Acciones del jugador y copias completas del estado de una partida."""

    def __init__(self, copias_cada=COPIAS_CADA):
        if isinstance(copias_cada, bool) or not isinstance(copias_cada, int):
            raise ValueError(
                f"Las acciones entre copias deben ser un entero: {copias_cada!r}"
            )
        if copias_cada < 1:
            raise ValueError(
                f"Las acciones entre copias deben ser al menos 1: {copias_cada!r}"
            )

        self._copias_cada = copias_cada
        self._acciones = []
        self._copias = []

    @property
    def copias_cada(self):
        return self._copias_cada

    def cantidad_de_acciones(self):
        return len(self._acciones)

    def cantidad_de_copias(self):
        return len(self._copias)


    def acciones(self):
        return self._acciones

    def copias(self):
        return self._copias


    # ------------------------------------------------------------------
    # Registrar
    # ------------------------------------------------------------------

    def registrar_accion(self, nombre, argumento, reloj):
        """Anota una accion del jugador ya aceptada."""
        self._acciones.append(AccionRegistrada(nombre, argumento, reloj))

    def hace_falta_copia(self):
        """True si corresponde guardar una copia en este momento.

        La primera copia es la del estado inicial, antes de cualquier accion.
        Despues, una cada copias_cada acciones.
        """
        if not self._copias:
            return True

        return len(self._acciones) - self._copias[-1].acciones >= self._copias_cada

    def guardar_copia(self, reloj, bloque):
        """Guarda una copia completa del estado en el punto actual."""
        acciones = len(self._acciones)

        if self._copias and self._copias[-1].acciones == acciones:
            self._copias[-1] = CopiaDelEstado(acciones, reloj, bloque)
            return

        self._copias.append(CopiaDelEstado(acciones, reloj, bloque))

    def restaurar_copias(self, copias):
        """Vuelve a poner las copias leidas de un archivo de partida.

        Se usa al cargar: las copias llegan ya hechas y no hay que volver a
        aplicarles la regla de una cada K.
        """
        self._copias = [
            CopiaDelEstado(acciones, reloj, bloque)
            for acciones, reloj, bloque in copias
        ]

    # ------------------------------------------------------------------
    # Recortar
    # ------------------------------------------------------------------

    def recortar_ultima_accion(self):
        """Quita la ultima accion, porque un pergamino la revirtio.

        Trabajo constante: quita una accion y, a lo sumo, una copia. No
        recorre la historia (FR-019).
        """
        if not self._acciones:
            return False

        self._acciones.pop()
        quedan = len(self._acciones)

        while len(self._copias) > 1 and self._copias[-1].acciones > quedan:
            self._copias.pop()

        return True

    # ------------------------------------------------------------------
    # Localizar
    # ------------------------------------------------------------------

    def copia_para_accion(self, numero_de_accion):
        """Ultima copia tomada en o antes de ese numero de accion.

        Busqueda binaria sobre las copias, que estan en orden creciente porque
        se crean en orden.
        """
        if not self._copias:
            return None

        izquierda = 0
        derecha = len(self._copias)

        while izquierda < derecha:
            medio = (izquierda + derecha) // 2

            if self._copias[medio].acciones <= numero_de_accion:
                izquierda = medio + 1
            else:
                derecha = medio

        if izquierda == 0:
            return None

        return self._copias[izquierda - 1]

    def accion_en_instante(self, instante):
        """Cuantas acciones del jugador habian ocurrido en ese instante.

        El estado en el instante t incluye todos los eventos de tiempo menor o
        igual que t, y si a t le corresponde una decision del jugador es el
        estado justo ANTES de tomarla (FR-002). Por eso una accion anotada con
        reloj igual a t todavia no ha ocurrido: cuentan las de reloj
        estrictamente menor.
        """
        izquierda = 0
        derecha = len(self._acciones)

        while izquierda < derecha:
            medio = (izquierda + derecha) // 2

            if self._acciones[medio].reloj < instante:
                izquierda = medio + 1
            else:
                derecha = medio

        return izquierda

    # ------------------------------------------------------------------
    # Memoria
    # ------------------------------------------------------------------

    def memoria_en_bytes(self):
        """Desglose de lo que ocupa la linea, para la medicion.

        Devuelve (copias, acciones). Las copias se miden de verdad, porque son
        bloques de bytes; las acciones se estiman por la cantidad de registros
        y lo que ocupa cada uno.
        """
        copias = 0

        for copia in self._copias:
            copias += len(copia.bloque)

        acciones = 0

        for accion in self._acciones:
            acciones += _TAMANO_DE_REGISTRO_DE_ACCION
            if isinstance(accion.argumento, str):
                acciones += len(accion.argumento)

        return copias, acciones


_TAMANO_DE_REGISTRO_DE_ACCION = 24

