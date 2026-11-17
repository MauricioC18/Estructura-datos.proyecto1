"""Equivalencia de la parada anticipada de RutasMasBaratas (specs/005-niebla-ir-a).

La mejora (b) del plan agrega a la búsqueda un parámetro opcional, parar_en,
que la detiene al asentar la sala del jugador. Estas pruebas comprueban, sobre
muchos mapas sintéticos deterministas por semilla, con empates de costo y con
salidas paralelas entre las mismas dos salas, que:

- el primer paso con parada es IDÉNTICO al del cálculo completo (FR-024,
  FR-026), y también desde cualquier otra sala que haya quedado asentada,
  que es lo que permite reutilizar la búsqueda durante el viaje;
- sin parar_en, la búsqueda que usa el cazador sigue dando las mismas
  distancias y el mismo primer paso que un cálculo de referencia
  independiente, con y sin corte por rango (FR-004, FR-008 y FR-017 de la
  capacidad 002).

El cálculo de referencia relaja todas las aristas hasta que nada cambia: es
lento y no usa ninguna estructura del proyecto, justamente para no compartir
errores con lo que se prueba.
"""
import random
import unittest

from model.room import Door, Exit, Room, RoomMap
from structures.rutas_mas_baratas import RutasMasBaratas

DIRECCIONES = ("N", "S", "E", "O")
OPUESTA = ("S", "N", "O", "E")
SEMILLAS = range(300)


def mapa_aleatorio(semilla):
    """Entre 2 y 25 salas con ids no consecutivos, costos de 1 a 3 (muchos
    empates), algunas puertas cerradas y, cuando hay direcciones libres,
    salidas paralelas entre las mismas dos salas."""
    azar = random.Random(semilla)
    cantidad = azar.randint(2, 25)
    ids = azar.sample(range(1, 200), cantidad)
    room_map = RoomMap()

    for id_sala in ids:
        room_map.add(Room(id_sala, f"Sala {id_sala}"))

    for _ in range(cantidad * 3):
        a, b = azar.sample(ids, 2)
        libres = [
            i for i in range(4)
            if room_map.room(a).exit_towards(DIRECCIONES[i]) is None
            and room_map.room(b).exit_towards(OPUESTA[i]) is None
        ]
        if not libres:
            continue
        i = azar.choice(libres)
        puerta = Door(a, b, closed=azar.random() < 0.15, cost=azar.randint(1, 3))
        room_map.room(a).add_exit(Exit(DIRECCIONES[i], b, puerta))
        room_map.room(b).add_exit(Exit(OPUESTA[i], a, puerta))

    return room_map, ids


def vecinas_abiertas(room_map):
    def vecinas(id_sala):
        return [
            (salida.destination, salida.cost, salida)
            for salida in room_map.room(id_sala).exits()
            if salida.door.is_open
        ]
    return vecinas


def distancias_de_referencia(room_map, ids, origen):
    """Relaja todas las aristas abiertas hasta que nada cambia. Devuelve una
    lista de pares (id, distancia) solo con las salas alcanzables."""
    distancias = [(origen, 0)]

    def distancia(id_sala):
        for clave, valor in distancias:
            if clave == id_sala:
                return valor
        return None

    cambio = True
    while cambio:
        cambio = False
        for id_sala in ids:
            base = distancia(id_sala)
            if base is None:
                continue
            for salida in room_map.room(id_sala).exits():
                if not salida.door.is_open:
                    continue
                nueva = base + salida.cost
                actual = distancia(salida.destination)
                if actual is None or nueva < actual:
                    distancias = [par for par in distancias if par[0] != salida.destination]
                    distancias.append((salida.destination, nueva))
                    cambio = True

    return distancia


def primer_paso_de_referencia(room_map, distancia, id_sala):
    d = distancia(id_sala)
    if d is None or d == 0:
        return None
    mejor = None
    for salida in room_map.room(id_sala).exits():
        if not salida.door.is_open:
            continue
        resto = distancia(salida.destination)
        if resto is None or salida.cost + resto != d:
            continue
        if mejor is None or salida.destination < mejor.destination or (
            salida.destination == mejor.destination and salida.cost < mejor.cost
        ):
            mejor = salida
    return mejor


class TestParadaAnticipada(unittest.TestCase):

    def test_el_primer_paso_con_parada_es_identico_al_completo(self):
        """FR-024, FR-026: en 300 mapas, para cada destino y cada sala del
        jugador, la salida elegida es exactamente la misma."""
        comparados = 0
        for semilla in SEMILLAS:
            room_map, ids = mapa_aleatorio(semilla)
            vecinas = vecinas_abiertas(room_map)
            for destino in ids[:4]:
                completa = RutasMasBaratas(vecinas, destino)
                for jugador in ids:
                    con_parada = RutasMasBaratas(vecinas, destino, parar_en=jugador)
                    self.assertIs(
                        con_parada.primer_paso_desde(jugador),
                        completa.primer_paso_desde(jugador),
                        f"semilla {semilla}, destino {destino}, jugador {jugador}",
                    )
                    self.assertEqual(
                        con_parada.distancia_a(jugador), completa.distancia_a(jugador)
                    )
                    comparados += 1
        self.assertGreater(comparados, 3000)

    def test_las_salas_asentadas_dan_el_mismo_paso_que_el_completo(self):
        """FR-026: lo que habilita reutilizar la búsqueda durante el viaje.
        Cada sala de la ruta desde el jugador tiene distancia menor, así que
        quedó asentada y su paso es el mismo que el del cálculo completo."""
        for semilla in SEMILLAS:
            room_map, ids = mapa_aleatorio(semilla)
            vecinas = vecinas_abiertas(room_map)
            destino, jugador = ids[0], ids[-1]
            completa = RutasMasBaratas(vecinas, destino)
            con_parada = RutasMasBaratas(vecinas, destino, parar_en=jugador)

            sala = jugador
            pasos = 0
            while sala != destino and pasos < len(ids):
                salida = con_parada.primer_paso_desde(sala)
                self.assertIs(salida, completa.primer_paso_desde(sala), f"semilla {semilla}")
                if salida is None:
                    break
                sala = salida.destination
                pasos += 1

    def test_pedir_el_paso_desde_una_sala_no_asentada_es_un_error(self):
        """FR-026: con parada, solo las asentadas tienen distancia definitiva."""
        room_map = RoomMap()
        for id_sala in (1, 2, 3):
            room_map.add(Room(id_sala, f"Sala {id_sala}"))
        for a, b, i in ((1, 2, 2), (2, 3, 2)):
            puerta = Door(a, b, cost=5)
            room_map.room(a).add_exit(Exit(DIRECCIONES[i], b, puerta))
            room_map.room(b).add_exit(Exit(OPUESTA[i], a, puerta))

        rutas = RutasMasBaratas(vecinas_abiertas(room_map), 1, parar_en=2)

        self.assertEqual(rutas.primer_paso_desde(2).destination, 1)
        with self.assertRaises(ValueError):
            rutas.primer_paso_desde(3)

    def test_sin_parada_la_busqueda_del_cazador_no_cambia(self):
        """FR-004, FR-008 y FR-017 de la capacidad 002: sin parar_en, mismas
        distancias y mismo primer paso que el cálculo de referencia, con y sin
        corte por rango."""
        for semilla in SEMILLAS:
            room_map, ids = mapa_aleatorio(semilla)
            vecinas = vecinas_abiertas(room_map)
            origen = ids[0]
            distancia = distancias_de_referencia(room_map, ids, origen)
            corte = random.Random(semilla + 1000).choice((None, 0, 2, 4))

            rutas = RutasMasBaratas(vecinas, origen, corte)

            for id_sala in ids:
                esperada = distancia(id_sala)
                if corte is not None and esperada is not None and esperada > corte:
                    esperada = None
                self.assertEqual(rutas.distancia_a(id_sala), esperada,
                                 f"semilla {semilla}, sala {id_sala}")
                if corte is None:
                    self.assertIs(
                        rutas.primer_paso_desde(id_sala),
                        primer_paso_de_referencia(room_map, distancia, id_sala),
                        f"semilla {semilla}, sala {id_sala}",
                    )


if __name__ == "__main__":
    unittest.main()
