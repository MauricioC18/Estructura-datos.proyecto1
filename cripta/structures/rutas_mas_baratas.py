"""
Costos mínimos sobre un grafo de salas con pesos, y el primer paso de una ruta.

Problema que resuelve
    El cazador (§3.2) necesita, en cada turno, el costo mínimo de llegar desde
    su sala hasta la sala del jugador sumando el costo de cada salida y usando
    solo salidas abiertas, y la vecina por la que empieza una ruta de ese
    costo. Contar salas no basta: con costos distintos, una ruta de más salas
    puede ser más barata (§5.1).

Se busca desde la sala del jugador, no desde la del cazador
    El desempate que fija el enunciado está escrito como
    costo(u, v) + dist(v, jugador) = d. Buscar desde el jugador entrega
    dist(v, jugador) para todas las vecinas de golpe, que es justo lo que esa
    fórmula pide; buscando desde el cazador habría que reconstruir rutas para
    recuperar ese número.
    Además el grafo no tiene dirección: el costo de una salida es el mismo en
    ambos sentidos y una puerta abierta lo está para los dos lados, así que la
    distancia desde el jugador es la distancia hasta el jugador. Eso permite
    que una sola búsqueda sirva a todos los cazadores activos.

Quién provee las vecinas
    La búsqueda no conoce el modelo. Recibe desde afuera una función que, dada
    una sala, devuelve tripletas (id_vecina, costo, referencia) contando solo
    las salidas abiertas en ese instante. La referencia es opaca: la búsqueda
    la devuelve tal cual en el primer paso y nunca la mira. Así el motor le
    pasa salidas reales y el viaje automático «ir a» (§3.4) podría pasarle el
    mapa que el jugador conoce, sin que la estructura cambie.

Estructuras, todas propias
    Cola de prioridad: el montículo binario mínimo de la agenda de eventos
        (structures/event_queue.py). Ordena por el par (time, sequence); se le
        entrega (distancia, id de sala) y queda ordenando por distancia y
        desempatando por id. El montículo no sabe qué ordena.
        No tiene «disminuir clave», así que se inserta de nuevo y se descarta
        al extraer lo ya asentado: el mismo recurso de la cancelación perezosa
        que la agenda ya usa.
    Distancias y salas asentadas: TablaHash. No se usa dict como índice ni
        set, que el proyecto prohíbe (P1 §7).

Corte por rango
    Se deja de expandir en cuanto la distancia pasa del corte, así que el
    trabajo depende de la región dentro del corte y no del tamaño de la
    cripta. Un cazador de rango pequeño no paga por la cripta entera.
    El corte nunca esconde el primer paso: si una sala quedó dentro, la vecina
    que empieza su ruta óptima está a distancia menor, así que también quedó.

Determinismo
    No hay azar. El montículo da un orden total, (distancia, id), y el
    desempate del enunciado se aplica aparte, sobre las vecinas de la sala
    consultada, de modo que el resultado no depende del orden de expansión.

Complejidad (Vr y Er = salas y salidas dentro del corte)
    costos_minimos: O((Vr + Er) log Vr).
    distancia_a: O(1) promedio.
    primer_paso_desde: O(grado de la sala); en esta cripta el grado es a lo
        sumo 4.
    espacio: O(Vr).
"""
from structures.event_queue import EventQueue
from structures.tabla_hash import TablaHash


class _Candidata:
    """Sala pendiente de asentar, con los nombres que el montículo compara.

    El montículo ordena por (time, sequence). Aquí time es la distancia y
    sequence es el id de la sala, así que ordena por distancia y desempata por
    id sin que haya que tocarlo. cancelled existe porque el montículo lo
    consulta; en esta búsqueda nada se cancela.
    """

    __slots__ = ("time", "sequence", "cancelled")

    def __init__(self, distancia, id_sala):
        self.time = distancia
        self.sequence = id_sala
        self.cancelled = False


class RutasMasBaratas:
    """Costos mínimos desde una sala, cortados en un presupuesto de costo."""

    def __init__(self, vecinas_abiertas, origen, corte=None):
        if corte is not None and (isinstance(corte, bool) or not isinstance(corte, int)):
            raise ValueError(f"El corte debe ser un entero o None: {corte!r}")
        if corte is not None and corte < 0:
            raise ValueError(f"El corte no puede ser negativo: {corte!r}")

        self._vecinas_abiertas = vecinas_abiertas
        self._origen = origen
        self._corte = corte
        self._distancias = TablaHash()
        self._calcular()

    @property
    def origen(self):
        return self._origen

    @property
    def corte(self):
        return self._corte

    def distancia_a(self, id_sala):
        """Costo mínimo desde el origen, o None si quedó fuera del corte."""
        return self._distancias.obtener(id_sala)

    def alcanza(self, id_sala):
        return self._distancias.contiene(id_sala)

    def primer_paso_desde(self, id_sala):
        """Primera salida de la ruta más barata de id_sala hacia el origen.

        Devuelve la referencia que entregó el proveedor de vecinas, o None si
        la sala quedó fuera del corte o ya es el origen.

        Entre las vecinas v con costo(id_sala, v) + distancia(v) igual al
        costo mínimo, gana la de menor id; entre dos salidas abiertas hacia
        esa misma vecina, la más barata.
        """
        distancia = self._distancias.obtener(id_sala)

        if distancia is None or distancia == 0:
            return None

        mejor_id = None
        mejor_costo = None
        mejor_referencia = None

        for id_vecina, costo, referencia in self._vecinas_abiertas(id_sala):
            distancia_vecina = self._distancias.obtener(id_vecina)

            if distancia_vecina is None or costo + distancia_vecina != distancia:
                continue

            if mejor_id is None or id_vecina < mejor_id or (
                id_vecina == mejor_id and costo < mejor_costo
            ):
                mejor_id = id_vecina
                mejor_costo = costo
                mejor_referencia = referencia

        return mejor_referencia

    def _calcular(self):
        self._distancias.insertar(self._origen, 0)
        pendientes = EventQueue()
        pendientes.push(_Candidata(0, self._origen))
        asentadas = TablaHash()

        while True:
            candidata = pendientes.pop()

            if candidata is None:
                return

            id_sala = candidata.sequence

            if asentadas.contiene(id_sala):
                continue

            asentadas.insertar(id_sala, True)

            for id_vecina, costo, _ in self._vecinas_abiertas(id_sala):
                if asentadas.contiene(id_vecina):
                    continue

                distancia = candidata.time + costo

                if self._corte is not None and distancia > self._corte:
                    continue

                conocida = self._distancias.obtener(id_vecina)

                if conocida is None or distancia < conocida:
                    self._distancias.insertar(id_vecina, distancia)
                    pendientes.push(_Candidata(distancia, id_vecina))
