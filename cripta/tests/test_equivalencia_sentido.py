"""Equivalencia del primer paso de «ir a» con salidas de un solo sentido (T051).

El cableado final en model/viaje.py espera a que RutasMasBaratas acepte la
parada anticipada junto con el proveedor de salidas (T052). Mientras tanto,
esta prueba comprueba, en mapas asimétricos aleatorios deterministas por
semilla, con empates de costo, salidas paralelas y puertas cerradas:

1. que la búsqueda de Carlos, expandida con entrantes_conocidas y con el
   primer paso por vecinas_conocidas (sin parada, que es lo que hoy acepta),
   da el mismo primer paso que una búsqueda de referencia escrita aquí;
2. que la referencia con parada en la sala del jugador da el mismo primer
   paso que sin parada, que es el argumento de la mejora (b) con salidas
   dirigidas;
3. que las distancias de la referencia coinciden con Bellman-Ford sobre las
   salidas conocidas, armadas solo con vecinas_conocidas, para no depender
   del índice de entrantes que se está probando.

La búsqueda de Carlos no se modifica. Cada prueba cita sus requisitos.
"""
import random
import unittest

from model.room import DIRECTIONS, Door, Exit, Room, RoomMap
from structures.mapa_conocido import MapaConocido
from structures.rutas_mas_baratas import RutasMasBaratas
from structures.tabla_hash import TablaHash


MAPAS = 300
COSTOS = (1, 1, 2, 3)  # repetidos a propósito, para que haya empates


def mapa_asimetrico(semilla):
    """Devuelve (room_map, contadores) con contadores de lo que ejercita."""
    azar = random.Random(semilla)
    cantidad = azar.randint(4, 9)
    room_map = RoomMap()
    for id_sala in range(1, cantidad + 1):
        room_map.add(Room(id_sala, f"Sala {id_sala}"))

    un_sentido = 0
    paralelas = 0

    for id_a in range(1, cantidad + 1):
        destinos = []
        for direccion in DIRECTIONS:
            sala_a = room_map.room(id_a)
            if sala_a.exit_towards(direccion) is not None or azar.random() < 0.35:
                continue
            id_b = azar.randint(1, cantidad - 1)
            if id_b >= id_a:
                id_b += 1
            puerta = Door(id_a, id_b, closed=azar.random() < 0.15, cost=azar.choice(COSTOS))
            sala_a.add_exit(Exit(direccion, id_b, puerta))
            if id_b in destinos:
                paralelas += 1
            destinos.append(id_b)

            libres = [d for d in DIRECTIONS if room_map.room(id_b).exit_towards(d) is None]
            if libres and azar.random() < 0.5:
                room_map.room(id_b).add_exit(Exit(azar.choice(libres), id_a, puerta))
            else:
                un_sentido += 1

    return room_map, un_sentido, paralelas


def conocimiento_al_azar(room_map, semilla):
    """Explora un subconjunto de salas, sin historial."""
    azar = random.Random(semilla * 7 + 1)
    mapa = MapaConocido(room_map)
    for id_sala in room_map.room_ids():
        if azar.random() < 0.8:
            mapa.jugador_entro(id_sala)
    return mapa


def distancias_de_referencia(mapa, destino, parar_en=None):
    """Dijkstra hacia atrás con selección lineal del mínimo, sin montículo.

    Devuelve (distancias, asentadas) en TablaHash. Con parar_en se detiene al
    asentar esa sala, como la mejora (b).
    """
    distancias = TablaHash()
    asentadas = TablaHash()
    distancias.insertar(destino, 0)
    pendientes = [destino]

    while pendientes:
        mejor = 0
        for i in range(1, len(pendientes)):
            a = (distancias.obtener(pendientes[i]), pendientes[i])
            b = (distancias.obtener(pendientes[mejor]), pendientes[mejor])
            if a < b:
                mejor = i
        id_sala = pendientes.pop(mejor)
        asentadas.insertar(id_sala, True)
        if id_sala == parar_en:
            break
        base = distancias.obtener(id_sala)
        for origen, costo, _ in mapa.entrantes_conocidas(id_sala):
            if asentadas.contiene(origen):
                continue
            actual = distancias.obtener(origen)
            if actual is None:
                distancias.insertar(origen, base + costo)
                pendientes.append(origen)
            elif base + costo < actual:
                distancias.insertar(origen, base + costo)

    return distancias, asentadas


def primer_paso_de_referencia(mapa, distancias, desde):
    """(destino, costo) del primer paso según FR-024, o None."""
    d = distancias.obtener(desde)
    if d is None or d == 0:
        return None
    mejor = None
    for vecina, costo, _ in mapa.vecinas_conocidas(desde):
        dv = distancias.obtener(vecina)
        if dv is None or costo + dv != d:
            continue
        if mejor is None or (vecina, costo) < mejor:
            mejor = (vecina, costo)
    return mejor


def bellman_ford(mapa, room_map, destino):
    """Distancia de cada sala al destino sobre las salidas conocidas."""
    aristas = []
    for id_sala in room_map.room_ids():
        for vecina, costo, _ in mapa.vecinas_conocidas(id_sala):
            aristas.append((id_sala, vecina, costo))
    distancias = TablaHash()
    distancias.insertar(destino, 0)
    for _ in range(len(room_map)):
        for origen, vecina, costo in aristas:
            dv = distancias.obtener(vecina)
            if dv is None:
                continue
            actual = distancias.obtener(origen)
            if actual is None or dv + costo < actual:
                distancias.insertar(origen, dv + costo)
    return distancias


def como_par(salida):
    return None if salida is None else (salida.destination, salida.cost)


class TestEquivalenciaConSentido(unittest.TestCase):

    def test_primer_paso_identico_en_mapas_asimetricos(self):
        """FR-023, FR-024, FR-026: en todos los pares de salas exploradas, el
        primer paso de la búsqueda de Carlos con salidas entrantes y salientes
        conocidas, el de la referencia completa y el de la referencia con
        parada coinciden; las distancias coinciden con Bellman-Ford."""
        casos = 0
        un_sentido = 0
        paralelas = 0
        empates = 0

        for semilla in range(MAPAS):
            room_map, sin_vuelta, dobles = mapa_asimetrico(semilla)
            un_sentido += sin_vuelta
            paralelas += dobles
            mapa = conocimiento_al_azar(room_map, semilla)
            exploradas = mapa.salas_exploradas()

            for destino in exploradas:
                completas, _ = distancias_de_referencia(mapa, destino)
                control = bellman_ford(mapa, room_map, destino)
                rutas = RutasMasBaratas(
                    mapa.entrantes_conocidas, destino, salidas_de=mapa.vecinas_conocidas
                )

                for desde in exploradas:
                    self.assertEqual(completas.obtener(desde), control.obtener(desde),
                                     (semilla, destino, desde))
                    if desde == destino:
                        continue
                    esperado = primer_paso_de_referencia(mapa, completas, desde)
                    detenidas, _ = distancias_de_referencia(mapa, destino, parar_en=desde)
                    con_parada = primer_paso_de_referencia(mapa, detenidas, desde)

                    self.assertEqual(como_par(rutas.primer_paso_desde(desde)), esperado,
                                     (semilla, destino, desde))
                    self.assertEqual(con_parada, esperado, (semilla, destino, desde))

                    candidatas = [
                        v for v, c, _ in mapa.vecinas_conocidas(desde)
                        if completas.obtener(v) is not None
                        and c + completas.obtener(v) == completas.obtener(desde)
                    ]
                    if len(candidatas) > 1:
                        empates += 1
                    casos += 1

        # La prueba solo vale si el generador ejercitó lo que dice ejercitar.
        self.assertGreater(casos, 1000)
        self.assertGreater(un_sentido, 100)
        self.assertGreater(paralelas, 10)
        self.assertGreater(empates, 10)

    def test_con_vecinas_salientes_para_expandir_falla(self):
        """FR-023: control de la prueba. Expandir por las salidas que salen,
        como hace hoy «ir a», no coincide con la referencia en algún mapa
        asimétrico; si coincidiera siempre, la prueba de arriba no probaría
        nada sobre el sentido."""
        distintos = 0

        for semilla in range(MAPAS):
            room_map, _, _ = mapa_asimetrico(semilla)
            mapa = conocimiento_al_azar(room_map, semilla)
            exploradas = mapa.salas_exploradas()
            for destino in exploradas:
                completas, _ = distancias_de_referencia(mapa, destino)
                al_reves = RutasMasBaratas(mapa.vecinas_conocidas, destino)
                for desde in exploradas:
                    if desde == destino:
                        continue
                    if como_par(al_reves.primer_paso_desde(desde)) != \
                            primer_paso_de_referencia(mapa, completas, desde):
                        distintos += 1

        self.assertGreater(distintos, 0)


if __name__ == "__main__":
    unittest.main()
