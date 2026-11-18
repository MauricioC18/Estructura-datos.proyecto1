"""
Reglas del viaje automático «ir a» (§3.4 de la segunda parte).

Este módulo dice qué está permitido y qué ocurre, pero no mueve a nadie: el
bucle de pasos vive en el controlador, porque cada paso tiene que cargar el
contenido de la sala destino y el modelo no puede hacerlo (P1 §6). Aquí van
las tres reglas:

    validar_orden       se acepta o se rechaza la orden (FR-022)
    siguiente_paso      por qué salida se da el próximo paso (FR-023,
                        FR-024, FR-026, FR-027)
    motivos_de_parada   por qué se detiene el viaje, en el orden de FR-028

Todas reciben la partida y el mapa conocido explícitamente. Ninguna modifica
nada.

Siguiente paso
    Se reutiliza la búsqueda de costo mínimo del cazador
    (structures/rutas_mas_baratas.py), pasándole el mapa conocido en lugar
    de las salidas abiertas reales. Se busca desde el destino y se pide el
    primer paso desde la sala del jugador: la búsqueda aplica sola el
    desempate de §3.2 (vecina de menor id; entre dos salidas a la misma
    vecina, la más barata).

    Salidas de un solo sentido (FR-023, FR-024; plan, alternativa 9): como
    la búsqueda va desde el destino, se expande por las salidas conocidas
    que ENTRAN a cada sala (entrantes_conocidas), y el primer paso se toma
    por una salida que SALE de la sala del jugador (vecinas_conocidas). Así
    una salida sin vuelta solo se recorre en su sentido.

Enemigos al entrar
    FR-028 (b) habla de la sala a la que el jugador entra. Por eso la
    pregunta «¿hay enemigos vivos ahí?» se hace justo antes del movimiento,
    con el contenido de esa sala ya cargado, y no después del ciclo de
    eventos: un enemigo que llega sin atacar no detiene el viaje, y uno que
    estaba al entrar sí, aunque se haya ido.
"""
from model.game import ActionResult
from structures.rutas_mas_baratas import RutasMasBaratas

LLEGADA = "llegada"
ENEMIGOS = "enemigos"
DANO = "daño"
SIN_RUTA = "sin_ruta"
PARTIDA_TERMINADA = "partida_terminada"
CONTENIDO_NO_DISPONIBLE = "contenido_no_disponible"

ORDEN_DE_LOS_MOTIVOS = (
    LLEGADA,
    ENEMIGOS,
    DANO,
    SIN_RUTA,
    PARTIDA_TERMINADA,
    CONTENIDO_NO_DISPONIBLE,
)


def validar_orden(game, mapa, destino):
    """Acepta la orden solo hacia una sala explorada distinta de la actual.

    Una sala no explorada y un id que no existe se rechazan con el mismo
    mensaje, para no revelar si la sala existe (FR-022). Un rechazo no
    consume tiempo ni toca nada.
    """
    if game.is_over:
        return ActionResult(False, "La partida ya termino.")

    if not mapa.esta_explorada(destino):
        return ActionResult(False, f"La sala {destino} no esta en tu mapa.")

    if destino == game.player.room_id:
        return ActionResult(False, f"Ya estas en la sala {destino}.")

    return ActionResult(True, f"Viajas hacia la sala {destino}.")


class RutaDelViaje:
    """La búsqueda de un viaje en curso, para reutilizarla entre pasos.

    Vale mientras el destino y la versión del mapa conocido sean los mismos y
    la sala del jugador haya quedado asentada en ella (mejora c del plan). La
    crea el controlador al empezar un viaje y la descarta al terminarlo; no
    es estado del juego.
    """

    def __init__(self):
        self.destino = None
        self.version = None
        self.rutas = None


def siguiente_paso(game, mapa, destino, ruta_del_viaje=None):
    """La salida por la que se da el próximo paso, o None si no hay ruta conocida.

    La búsqueda se detiene en cuanto asienta la sala del jugador (mejora b
    del plan): el primer paso es el mismo que con la búsqueda completa.

    Con ruta_del_viaje se reutiliza la búsqueda del paso anterior si el
    conocimiento no cambió desde entonces (mejora c). Las salas siguientes de
    la ruta tienen distancia menor que la de la sala donde se detuvo, así que
    ya están asentadas y su paso es el mismo que daría recalcular (FR-026).
    Si el conocimiento cambió, o la sala no quedó asentada, se busca de nuevo.
    """
    sala = game.player.room_id

    if ruta_del_viaje is not None and ruta_del_viaje.rutas is not None:
        if ruta_del_viaje.destino == destino and ruta_del_viaje.version == mapa.version:
            try:
                return ruta_del_viaje.rutas.primer_paso_desde(sala)
            except ValueError:
                pass  # la sala no quedó asentada en la búsqueda guardada

    rutas = RutasMasBaratas(
        mapa.entrantes_conocidas, destino, parar_en=sala, salidas_de=mapa.vecinas_conocidas
    )

    if ruta_del_viaje is not None:
        ruta_del_viaje.destino = destino
        ruta_del_viaje.version = mapa.version
        ruta_del_viaje.rutas = rutas

    return rutas.primer_paso_desde(sala)


def hay_enemigos_vivos_en(game, id_sala):
    """Si la sala tiene enemigos vivos, activos o dormidos (FR-028 (b)).

    Se pregunta antes de entrar, con el contenido de la sala ya cargado.
    """
    for enemy in game.enemies:
        if enemy.is_alive and enemy.room_id == id_sala:
            return True

    return False


def motivos_de_parada(game, destino, vida_antes, enemigos_al_entrar,
                      sin_ruta=False, contenido_no_disponible=False):
    """Los motivos que se cumplieron, en el orden de FR-028.

    vida_antes es la vida del jugador antes del paso; enemigos_al_entrar,
    la respuesta de hay_enemigos_vivos_en para la sala del paso. sin_ruta y
    contenido_no_disponible indican que el paso no llegó a darse. Una lista
    vacía significa que el viaje sigue.
    """
    se_movio = not sin_ruta and not contenido_no_disponible
    cumplidos = []

    for motivo in ORDEN_DE_LOS_MOTIVOS:
        if motivo == LLEGADA:
            cumple = se_movio and game.player.room_id == destino
        elif motivo == ENEMIGOS:
            cumple = se_movio and enemigos_al_entrar
        elif motivo == DANO:
            cumple = game.player.health < vida_antes
        elif motivo == SIN_RUTA:
            cumple = sin_ruta
        elif motivo == PARTIDA_TERMINADA:
            cumple = game.is_over
        else:
            cumple = contenido_no_disponible

        if cumple:
            cumplidos.append(motivo)

    return cumplidos
