"""
Mediciones de la linea de tiempo (seccion 3.6 y 5.5 del enunciado).

Que se mide y por que
    1. Memoria y tiempo de consulta para K = 1, 10, 50 y 200. K=1 es la
       alternativa ingenua, una copia completa por accion, y es la referencia
       contra la que se mide el ahorro: el principio VI de la constitucion
       pide medir la alternativa descartada. La memoria se reporta desglosada
       entre copias y acciones.
    2. El costo de una consulta en partidas de largo creciente, con K fijo.
       Debe quedar plano: el costo de una consulta no depende del largo de la
       partida (SC-002).
    3. El recorte por pergamino en partidas de largo creciente. Debe quedar
       plano (SC-008).
    4. El ciclo completo de eventos con la linea activa, contra el limite de
       20 ms (FR-024, SC-009).
    5. Una partida de 5 000 acciones con K por omision: promedio y peor
       consulta contra el limite de 50 ms de la seccion 6.1. Y la alternativa
       sin puntos de control (solo la copia inicial), que pide la seccion
       6.3, en partidas de 300 y 5 000 acciones.

El valor por omision de K sale de la medicion 1, como exige la seccion 3.6:
se busca la rodilla de la curva, donde bajar mas K ya casi no acelera la
consulta pero sigue costando memoria.

Las criptas sinteticas son deterministas por semilla.
"""
import time

from adapters.almacen_partida import (
    reconstruir_desde_copia,
    tomar_copia_del_estado,
)
from benchmark.scheduler_bench import build_synthetic_crypt
from benchmark.utilidades_medicion import Measurement, calentar_procesador
from model.consulta_historia import consultar_accion
from model.enemy import Enemy
from model.game import Game
from model.game_state import GameState
from model.player import Player
from structures.history import History, ReversibleEventQueue
from structures.inventory import Inventory
from structures.linea_de_tiempo import COPIAS_CADA, LineaDeTiempo
from structures.trail import PlayerTrail


SEED = 2026
# La cripta de referencia publicada es cripta-06: 300 salas. El tamano de una
# copia completa crece con la cripta, asi que la memoria de la linea se mide a
# esa escala y no a la de las criptas de prueba.
ROOMS = 300
ENEMIES = 6


def build_game(copias_cada, seed=SEED, rooms=ROOMS):
    """Partida con linea de tiempo, enemigos y azar de verdad."""
    room_map = build_synthetic_crypt(rooms, closed_every=0)
    state = GameState(seed=seed)
    history = History(state)

    player = Player("p-1", "Heroe", 10 ** 9, 6, 10 ** 6, 100, 1)
    player.inventory = Inventory(20, history=history)

    enemies = []

    for number in range(ENEMIES):
        enemies.append(
            Enemy(
                f"e-{number}",
                f"Rata {number}",
                30,
                1,
                1,
                90 + number * 5,
                2 + (number % max(1, rooms - 2)),
                Enemy.WANDERER,
            )
        )

    timeline = LineaDeTiempo(copias_cada=copias_cada)

    game = Game(
        state,
        player,
        enemies,
        room_map=room_map,
        trail=PlayerTrail(history),
        history=history,
        event_queue=ReversibleEventQueue(history),
        timeline=timeline,
        snapshot=tomar_copia_del_estado,
    )

    return game, timeline


def play(game, decisions):
    """Camina de ida y vuelta, abriendo lo que encuentre cerrado."""
    direction = "N"

    while game.timeline.cantidad_de_acciones() < decisions and not game.is_over:
        if game.move(direction).accepted:
            continue

        if game.open_door(direction).accepted:
            continue

        direction = "S" if direction == "N" else "N"

        if not game.wait().accepted:
            return


# ----------------------------------------------------------------------
# 1. Memoria y tiempo de consulta para varios K
# ----------------------------------------------------------------------

def measure_k(copias_cada, decisions, queries):
    game, timeline = build_game(copias_cada)
    play(game, decisions)

    cuantas = timeline.cantidad_de_acciones()
    puntos = [cuantas * numero // max(1, queries - 1) for numero in range(queries)]

    start = time.perf_counter()

    for numero in puntos:
        consultar_accion(game, numero, reconstruir_desde_copia)

    seconds = time.perf_counter() - start
    copias, acciones = timeline.memoria_en_bytes()

    return seconds, len(puntos), copias, acciones, timeline.cantidad_de_copias()


# ----------------------------------------------------------------------
# 2. El costo de una consulta frente al largo de la partida
# ----------------------------------------------------------------------

def measure_query_against_length(copias_cada, decisions, queries):
    """Consulta puntos repartidos, no siempre el ultimo.

    Consultar la ultima accion cae justo despues de una copia y casi no
    repite nada: seria el caso mas facil y no probaria nada. Repartiendo los
    puntos, el promedio pasa por replays de 0 a K acciones, que es lo que de
    verdad ocurre.
    """
    game, timeline = build_game(copias_cada)
    play(game, decisions)

    cuantas = timeline.cantidad_de_acciones()
    puntos = [cuantas * numero // max(1, queries - 1) for numero in range(queries)]

    start = time.perf_counter()

    for numero in puntos:
        consultar_accion(game, numero, reconstruir_desde_copia)

    return time.perf_counter() - start, cuantas


# ----------------------------------------------------------------------
# 3. El recorte por pergamino frente al largo de la partida
# ----------------------------------------------------------------------

def measure_trim_against_length(decisions, repetitions=2000):
    game, timeline = build_game(50)
    play(game, decisions)

    cuantas = timeline.cantidad_de_acciones()
    start = time.perf_counter()

    for _ in range(repetitions):
        timeline.registrar_accion("esperar", None, 0)
        timeline.recortar_ultima_accion()

    return time.perf_counter() - start, cuantas


# ----------------------------------------------------------------------
# 4. El ciclo de eventos con la linea activa
# ----------------------------------------------------------------------

def measure_event_cycle(copias_cada, decisions):
    game, timeline = build_game(copias_cada)

    start = time.perf_counter()
    play(game, decisions)
    seconds = time.perf_counter() - start

    return seconds, timeline.cantidad_de_acciones()


# ----------------------------------------------------------------------
# 5. Partida larga y alternativa sin puntos de control (6.1 y 6.3)
# ----------------------------------------------------------------------

def measure_queries_one_by_one(copias_cada, decisions, queries):
    """Promedio y peor consulta, en puntos repartidos de la partida.

    El limite de 6.1 es por consulta (50 ms con al menos 5 000 acciones y K
    por omision), asi que se reporta tambien la peor, no solo el promedio.
    """
    game, timeline = build_game(copias_cada)
    play(game, decisions)

    cuantas = timeline.cantidad_de_acciones()
    puntos = [cuantas * numero // max(1, queries - 1) for numero in range(queries)]
    total = 0.0
    peor = 0.0

    for numero in puntos:
        start = time.perf_counter()
        consultar_accion(game, numero, reconstruir_desde_copia)
        seconds = time.perf_counter() - start
        total += seconds
        peor = max(peor, seconds)

    return total / len(puntos), peor, cuantas, timeline.cantidad_de_copias()


VALORES_DE_K = (1, 10, 50, 200)
DECISIONES = 300
CONSULTAS = 40
DECISIONES_PARTIDA_LARGA = 5000
# Sin puntos de control solo existe la copia inicial: K mayor que cualquier partida.
SIN_PUNTOS_DE_CONTROL = 10 ** 9
CONSULTAS_SIN_PUNTOS = 5


def run():
    """Devuelve las mediciones de este modulo, para el ejecutor de --bench."""
    calentar_procesador(0.3)

    measurements = []

    for copias_cada in VALORES_DE_K:
        seconds, cuantas, copias, acciones, cantidad = measure_k(
            copias_cada, DECISIONES, CONSULTAS
        )
        measurements.append(
            Measurement(
                f"Consulta con K={copias_cada}",
                seconds,
                f"{cuantas} consultas, {seconds / cuantas * 1000:.4f} ms por "
                f"consulta; {cantidad} copias, "
                f"{copias / 1024:.1f} KiB en copias y "
                f"{acciones / 1024:.2f} KiB en acciones",
            )
        )

    for decisiones in (50, 150, 300):
        seconds, cuantas = measure_query_against_length(50, decisiones, CONSULTAS)
        measurements.append(
            Measurement(
                f"Consulta en una partida de {cuantas} acciones (K=50)",
                seconds,
                f"{CONSULTAS} consultas, "
                f"{seconds / CONSULTAS * 1000:.4f} ms por consulta",
            )
        )

    promedio, peor, cuantas, copias = measure_queries_one_by_one(
        COPIAS_CADA, DECISIONES_PARTIDA_LARGA, CONSULTAS
    )
    measurements.append(
        Measurement(
            f"Consulta en una partida de {cuantas} acciones (K={COPIAS_CADA})",
            peor,
            f"{CONSULTAS} consultas, promedio {promedio * 1000:.2f} ms, peor "
            f"{peor * 1000:.2f} ms ({peor * 1000 / 50 * 100:.0f}% del limite de "
            f"50 ms); {copias} copias",
        )
    )

    for decisiones in (DECISIONES, DECISIONES_PARTIDA_LARGA):
        promedio, peor, cuantas, copias = measure_queries_one_by_one(
            SIN_PUNTOS_DE_CONTROL, decisiones, CONSULTAS_SIN_PUNTOS
        )
        measurements.append(
            Measurement(
                f"Consulta sin puntos de control, partida de {cuantas} acciones",
                peor,
                f"{CONSULTAS_SIN_PUNTOS} consultas, promedio {promedio * 1000:.2f} ms, "
                f"peor {peor * 1000:.2f} ms; {copias} copia (la inicial)",
            )
        )

    for decisiones in (50, 300):
        seconds, cuantas = measure_trim_against_length(decisiones)
        measurements.append(
            Measurement(
                f"Recorte por pergamino en una partida de {cuantas} acciones",
                seconds,
                f"2000 recortes, {seconds / 2000 * 1e6:.3f} us por recorte",
            )
        )

    for copias_cada in (0, 50):
        if copias_cada == 0:
            game, _ = build_game(10 ** 9)
            start = time.perf_counter()
            play(game, DECISIONES)
            seconds = time.perf_counter() - start
            cuantas = game.player_actions
            etiqueta = "Ciclo de eventos con la linea casi sin copias"
        else:
            seconds, cuantas = measure_event_cycle(copias_cada, DECISIONES)
            etiqueta = f"Ciclo de eventos con la linea activa (K={copias_cada})"

        por_ciclo = seconds / max(1, cuantas) * 1000
        measurements.append(
            Measurement(
                etiqueta,
                seconds,
                f"{cuantas} decisiones, {por_ciclo:.4f} ms por ciclo, "
                f"{por_ciclo / 20 * 100:.2f}% del limite de 20 ms",
            )
        )

    return measurements


def main():
    print(f"Python {__import__('sys').version.split()[0]}\n")

    for measurement in run():
        if measurement.seconds is None:
            print(f"{measurement.name}: {measurement.detail}")
        else:
            print(
                f"{measurement.name}: {measurement.seconds:.4f} s  "
                f"({measurement.detail})"
            )


if __name__ == "__main__":
    main()
