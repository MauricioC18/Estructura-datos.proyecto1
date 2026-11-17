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
    Eso permite además que una sola búsqueda sirva a todos los cazadores
    activos, en vez de una por cazador.
    Buscar desde el jugador exige cuidado con el sentido de las salidas: ver
    «Grafos de un solo sentido».

Quién provee las vecinas
    La búsqueda no conoce el modelo. Recibe desde afuera una función que, dada
    una sala, devuelve tripletas (id_vecina, costo, referencia) contando solo
    las salidas abiertas en ese instante. La referencia es opaca: la búsqueda
    la devuelve tal cual en el primer paso y nunca la mira. Así el motor le
    pasa salidas reales y el viaje automático «ir a» (§3.4) puede pasarle el
    mapa que el jugador conoce, sin que la estructura cambie.

Grafos de un solo sentido
    El contrato del servicio describe cada salida como dirigida («One directed
    exit from a room») y no exige que la sala destino declare la vuelta, así
    que el esqueleto puede producir un grafo asimétrico. Con un grafo así hay
    que distinguir dos cosas que en uno simétrico coinciden:
      - para EXPANDIR la búsqueda desde el origen, y obtener así el costo de
        llegar DESDE cada sala HASTA el origen, hacen falta las salidas que
        ENTRAN a cada sala. Ese es el primer parámetro.
      - para dar el PRIMER PASO desde una sala hay que atravesar una salida
        que SALGA de ella. Ese es salidas_de.
    Si no se pasa salidas_de, se usa el mismo proveedor para las dos cosas,
    que es exactamente lo correcto en un grafo simétrico y es como quedan
    todas las llamadas que ya existían.
    El desempate sigue siendo el de FR-008: entre las salidas que salen de la
    sala, las que cumplen costo + distancia = d, y de esas la vecina de menor
    id.

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

Parada anticipada (parar_en), de la capacidad 003
    Quien solo necesita el primer paso desde una sala puede pedir que la
    busqueda se detenga al asentar esa sala. El resultado es el mismo: las
    vecinas que cumplen costo + distancia = d tienen distancia menor que d,
    porque todo costo es al menos 1, asi que ya estan asentadas; y una no
    asentada tiene distancia de al menos d, asi que nunca cumple la igualdad.
    Detenida la busqueda, solo las salas asentadas tienen distancia
    definitiva, y preguntar por cualquier otra es un error en vez de una
    respuesta a medias.

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

    def __init__(self, vecinas_abiertas, origen, corte=None, *, parar_en=None,
                 salidas_de=None):
        """parar_en es opcional y solo se pasa por nombre. Sin él, la búsqueda
        es exactamente la de siempre (la que usa el cazador).

        Con parar_en, la búsqueda se detiene en cuanto asienta esa sala. Lo
        usa el viaje «ir a», que solo necesita el primer paso desde la sala
        del jugador. El primer paso sigue siendo el mismo que con la búsqueda
        completa: las vecinas que cumplen costo + distancia = d tienen
        distancia menor que d, porque todo costo es al menos 1, así que ya
        están asentadas cuando se asienta la sala; y una vecina no asentada
        tiene distancia de al menos d, así que nunca cumple la igualdad. Si la
        búsqueda se detuvo, solo son definitivas las distancias de las salas
        asentadas, y pedir el primer paso desde una sala no asentada es un
        error. Si la sala nunca se alcanza, la búsqueda llega al final como
        sin parar_en y todo es definitivo.
        """
        if salidas_de is not None and parar_en is not None:
            raise ValueError(
                "parar_en y salidas_de juntos todavia no estan probados: la "
                "parada anticipada asienta solo una parte del grafo y el "
                "primer paso desde otra sala podria no ser definitivo."
            )

        if corte is not None and (isinstance(corte, bool) or not isinstance(corte, int)):
            raise ValueError(f"El corte debe ser un entero o None: {corte!r}")
        if corte is not None and corte < 0:
            raise ValueError(f"El corte no puede ser negativo: {corte!r}")

        self._vecinas_abiertas = vecinas_abiertas
        self._salidas_de = vecinas_abiertas if salidas_de is None else salidas_de
        self._origen = origen
        self._corte = corte
        self._parar_en = parar_en
        self._distancias = TablaHash()
        self._asentadas = TablaHash()
        self._se_detuvo = False
        self._calcular()

    @property
    def origen(self):
        return self._origen

    @property
    def corte(self):
        return self._corte

    def distancia_a(self, id_sala):
        """Costo mínimo desde el origen, o None si quedó fuera del corte.

        Con una búsqueda detenida por parar_en, solo las salas asentadas
        tienen distancia definitiva: las demás pueden tener una tentativa, que
        es mayor o igual que la verdadera. Pedirla es un error, igual que
        pedir el primer paso, para que esta clase nunca devuelva una
        distancia que no sea definitiva.
        """
        self._exigir_definitiva(id_sala)

        return self._distancias.obtener(id_sala)

    def alcanza(self, id_sala):
        self._exigir_definitiva(id_sala)

        return self._distancias.contiene(id_sala)

    def se_detuvo(self):
        """True si la búsqueda paró por parar_en antes de agotar la región."""
        return self._se_detuvo

    def esta_asentada(self, id_sala):
        """True si la distancia de esa sala es definitiva."""
        return self._asentadas.contiene(id_sala)

    def _exigir_definitiva(self, id_sala):
        if self._se_detuvo and not self._asentadas.contiene(id_sala):
            raise ValueError(
                f"La búsqueda se detuvo en la sala {self._parar_en} y la sala "
                f"{id_sala} no quedó asentada: su distancia no es definitiva."
            )

    def primer_paso_desde(self, id_sala):
        """Primera salida de la ruta más barata de id_sala hacia el origen.

        Devuelve la referencia que entregó el proveedor de vecinas, o None si
        la sala quedó fuera del corte o ya es el origen.

        Entre las vecinas v con costo(id_sala, v) + distancia(v) igual al
        costo mínimo, gana la de menor id; entre dos salidas abiertas hacia
        esa misma vecina, la más barata.
        """
        self._exigir_definitiva(id_sala)

        distancia = self._distancias.obtener(id_sala)

        if distancia is None or distancia == 0:
            return None

        mejor_id = None
        mejor_costo = None
        mejor_referencia = None

        for id_vecina, costo, referencia in self._salidas_de(id_sala):
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
        asentadas = self._asentadas

        while True:
            candidata = pendientes.pop()

            if candidata is None:
                return

            id_sala = candidata.sequence

            if asentadas.contiene(id_sala):
                continue

            asentadas.insertar(id_sala, True)

            if id_sala == self._parar_en:
                self._se_detuvo = True
                return

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
