"""
Grafo de salas de una cripta y recorrido en anchura (BFS).

Problema que resuelve
    El esqueleto de la cripta se descarga completo al iniciar (§3.2), así
    que se conoce el mapa entero. Para precargar contenido (§4.2) hace falta
    saber qué salas están más cerca de la sala actual.

Representación: lista de adyacencia
    Una TablaHash guarda, para cada id de sala, la lista de salas vecinas en
    un orden fijo de direcciones (N, S, E, O). Se usan todas las salidas
    declaradas, también las cerradas con llave, porque el jugador puede
    abrirlas.
    Alternativa: matriz de adyacencia. Ocupa O(V²) aunque cada sala tenga a
    lo sumo 4 salidas, así que se descartó.

Recorrido en anchura (BFS)
    Visita primero la sala de origen, luego las que están a 1 paso, luego
    las que están a 2, y así. Usa:
      - una cola de salas por visitar. Se guarda en una list y, en lugar de
        borrar el primer elemento (que desplazaría a todos los demás), se
        avanza un índice que marca el frente: sacar de la cola cuesta O(1).
      - una TablaHash de salas ya vistas, para no visitar dos veces la misma.
    Como los vecinos siempre se recorren en el orden N, S, E, O, el
    resultado es determinista.

Complejidad (V = salas, E = salidas)
    vecinos(sala): O(1) promedio.
    salas_en_orden_de_distancia: O(V + E) en el peor caso, pero se detiene
        apenas junta la cantidad pedida de salas.
    espacio: O(V + E).
"""
from structures.tabla_hash import TablaHash

ORDEN_DE_DIRECCIONES = ("N", "S", "E", "O")


class GrafoSalas:
    """Salas de una cripta y sus conexiones."""

    def __init__(self):
        self._vecinos_por_sala = TablaHash()
        self._ids_en_orden_de_llegada = []

    def agregar_sala(self, id_sala, vecinos_en_orden):
        """Registra una sala con sus vecinas (ya en orden N, S, E, O)."""
        if isinstance(id_sala, bool) or not isinstance(id_sala, int):
            raise ValueError(f"El id de una sala debe ser un entero: {id_sala!r}")
        if self._vecinos_por_sala.contiene(id_sala):
            raise ValueError(f"La sala {id_sala} aparece dos veces en el esqueleto")
        self._vecinos_por_sala.insertar(id_sala, list(vecinos_en_orden))
        self._ids_en_orden_de_llegada.append(id_sala)

    def contiene_sala(self, id_sala):
        return self._vecinos_por_sala.contiene(id_sala)

    def cantidad_de_salas(self):
        return len(self._ids_en_orden_de_llegada)

    def ids_de_salas(self):
        """Ids en el orden en que llegaron en el esqueleto."""
        return list(self._ids_en_orden_de_llegada)

    def vecinos(self, id_sala):
        """Salas a las que lleva alguna salida de id_sala, en orden N, S, E, O."""
        vecinos = self._vecinos_por_sala.obtener(id_sala)
        if vecinos is None:
            raise ValueError(f"La sala {id_sala} no está en el esqueleto")
        return list(vecinos)

    def salas_en_orden_de_distancia(self, origen, cantidad_maxima, incluir=None):
        """Recorre el grafo en anchura desde origen (incluido) y devuelve
        hasta cantidad_maxima salas, de la más cercana a la más lejana.

        incluir es una función opcional que decide qué salas van en el
        resultado. Las que no se incluyen igual se atraviesan: el recorrido
        pasa por ellas para llegar a las que están detrás.
        """
        if not self.contiene_sala(origen):
            raise ValueError(f"La sala {origen} no está en el esqueleto")
        resultado = []
        cola = [origen]
        frente_de_la_cola = 0
        vistas = TablaHash()
        vistas.insertar(origen, True)

        while frente_de_la_cola < len(cola) and len(resultado) < cantidad_maxima:
            sala = cola[frente_de_la_cola]
            frente_de_la_cola += 1
            if incluir is None or incluir(sala):
                resultado.append(sala)
            for vecina in self._vecinos_por_sala.obtener(sala):
                # Una salida hacia una sala que no existe en el esqueleto se ignora.
                if not vistas.contiene(vecina) and self.contiene_sala(vecina):
                    vistas.insertar(vecina, True)
                    cola.append(vecina)
        return resultado


def construir_grafo_desde_esqueleto(salas):
    """Arma el grafo a partir de las salas del esqueleto (el JSON del API,
    todas las páginas juntas)."""
    grafo = GrafoSalas()
    for sala in salas:
        salidas = sala.get("salidas") or {}
        vecinos = []
        for direccion in ORDEN_DE_DIRECCIONES:
            salida = salidas.get(direccion)
            if salida is not None:
                vecinos.append(salida["sala"])
        grafo.agregar_sala(sala["id"], vecinos)
    return grafo
