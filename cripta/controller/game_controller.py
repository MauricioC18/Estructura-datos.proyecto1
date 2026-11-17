from controller.commands import (
    ATTACK,
    DROP,
    EQUIP,
    MOVE,
    NEXT,
    OPEN,
    PICK_UP,
    PREVIOUS,
    REWIND,
    USE,
    WAIT,
    is_game_action,
)
from dataclasses import dataclass

from adapters.fuente_datos import ErrorFuenteDatos
from controller.commands import Command, TRAVEL
from model import viaje
from model.game import IN_PROGRESS, ActionResult


@dataclass
class TravelResult:
    """Resultado de una orden «ir a».

    accepted dice si la orden se acepto. steps son los movimientos que se
    ejecutaron. reasons son los motivos de parada, en el orden de FR-028.
    message explica un rechazo o el error de carga de una sala.
    """

    accepted: bool
    message: str
    steps: int = 0
    reasons: list = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []


class GameController:
    """Traduce comandos del jugador en operaciones de Game.

    No sabe de donde vienen los comandos: el teclado y la reproduccion de un
    log le entregan el mismo Command. Por eso --replay no necesita la vista.

    replay_log es cualquier objeto con append(command). Solo se registran las
    acciones aceptadas, como acordo el grupo (ARQUITECTURA, seccion 6): una
    accion rechazada no consume tiempo, no cambia el estado ni consulta el
    azar, de modo que omitirla no cambia la partida reproducida.

    repository es el RepositorioCripta de la partida. El modelo no puede pedir
    el contenido de una sala (§6), asi que antes de mover lo carga el
    controlador, y despues de cada accion aceptada le pide que precargue
    alrededor del jugador (§4.2). Como --replay pasa por aqui, la reproduccion
    carga las mismas salas en el mismo orden. Sin repositorio, el controlador
    solo despacha, que es lo que usan las pruebas del modelo.
    """

    def __init__(self, game, replay_log=None, repository=None, known_map=None):
        self.game = game
        self.replay_log = replay_log
        self.repository = repository
        self._known_map = known_map

    @property
    def known_map(self):
        """El mapa conocido que se le paso, o el de la partida si lo tiene."""
        if self._known_map is not None:
            return self._known_map

        return getattr(self.game, "known_map", None)

    def travel(self, destination):
        """Viaje automatico «ir a» (§3.4): una secuencia de movimientos ordinarios.

        Las reglas (si se acepta, cual es el siguiente paso, por que se
        detiene) son del modelo, en model/viaje.py. Aqui solo se orquestan los
        pasos, porque cada uno tiene que cargar el contenido de la sala
        destino antes de moverse, y eso el modelo no puede hacerlo.

        Cada paso pasa por execute(mover), el mismo camino que un mover escrito
        a mano: carga el contenido, queda en la bitacora y precarga. La orden
        queda ademas como comentario en la bitacora (FR-031).

        Los enemigos de la sala destino se cuentan justo antes de moverse, con
        su contenido ya cargado: es la sala a la que el jugador entra
        (FR-028 (b)). Entre esa pregunta y la entrada no corre ningun evento.
        """
        known_map = self.known_map

        if known_map is None:
            return TravelResult(
                False,
                "Todavia no se puede viajar: la partida no tiene el mapa conocido.",
            )

        validation = viaje.validar_orden(self.game, known_map, destination)

        if not validation.accepted:
            return TravelResult(False, validation.message)

        if self.replay_log is not None and hasattr(self.replay_log, "comment"):
            self.replay_log.comment(Command(TRAVEL, destination).to_text())

        steps = 0

        while True:
            exit_ = viaje.siguiente_paso(self.game, known_map, destination)

            if exit_ is None:
                return self._stopped(destination, steps, sin_ruta=True)

            rejection = self._load_destination(exit_.direction)

            if rejection is not None:
                return self._stopped(
                    destination, steps, rejection.message, contenido_no_disponible=True
                )

            enemies_on_entry = viaje.hay_enemigos_vivos_en(self.game, exit_.destination)
            health_before = self.game.player.health
            result = self.execute(Command(MOVE, exit_.direction))

            if not result.accepted:
                # Solo pasa si la puerta de la sala actual cambio sin que el
                # mapa conocido lo observara, es decir, sin los avisos del
                # motor. El mapa ya no tiene una ruta que de verdad exista.
                return self._stopped(destination, steps, result.message, sin_ruta=True)

            steps += 1
            reasons = viaje.motivos_de_parada(
                self.game, destination, health_before, enemies_on_entry
            )

            if reasons:
                return TravelResult(True, "", steps, reasons)

    def _stopped(self, destination, steps, message="", sin_ruta=False,
                 contenido_no_disponible=False):
        reasons = viaje.motivos_de_parada(
            self.game,
            destination,
            self.game.player.health,
            False,
            sin_ruta=sin_ruta,
            contenido_no_disponible=contenido_no_disponible,
        )

        return TravelResult(True, message, steps, reasons)

    def execute(self, command):
        if not is_game_action(command):
            raise ValueError(
                f"'{command.name}' no es una accion del modelo; la atiende la aplicacion."
            )

        if command.name == MOVE:
            rejection = self._load_destination(command.argument)

            if rejection is not None:
                return rejection

        result = self._dispatch(command)

        if result.accepted:
            if self.replay_log is not None:
                self.replay_log.append(command)

            self._preload_around_player()

        return result

    def visible_state(self):
        return self.game.visible_state()

    @property
    def is_over(self):
        return self.game.result != IN_PROGRESS

    def _load_destination(self, direction):
        """Carga la sala destino antes de confirmar el movimiento (§2.5, §4.2).

        Si no hay salida o la puerta esta cerrada no carga nada: move() ya
        rechaza esos casos con su propio mensaje. Si la red falla o se acabo el
        presupuesto, el movimiento se rechaza sin consumir tiempo y la sala
        queda sin cargar, igual que antes de intentarlo.
        """
        if self.repository is None or self.game.room_map is None:
            return None

        room = self.game.room_map.room(self.game.player.room_id)
        exit_ = room.exit_towards(direction)

        if exit_ is None or not exit_.door.is_open:
            return None

        destination = self.game.room_map.room(exit_.destination)

        try:
            enemies = self.repository.cargar_contenido_de_sala(destination)
        except ErrorFuenteDatos as error:
            # Incluye PresupuestoAgotado. El mensaje ya dice que operacion fallo.
            return ActionResult(False, str(error))

        self.game.enemies.extend(enemies)

        return None

    def _preload_around_player(self):
        """Precarga contenido y fichas cerca del jugador (§4.2).

        Con la partida terminada no tiene sentido gastar presupuesto. Nunca
        lanza PresupuestoAgotado: sin presupuesto simplemente no precarga.
        """
        if self.repository is None or self.is_over:
            return

        try:
            self.repository.despues_de_accion(self.game.player.room_id)
        except ErrorFuenteDatos:
            # La precarga es una optimizacion: si la red falla, la sala se
            # pedira de nuevo cuando el jugador intente entrar.
            pass

    def _dispatch(self, command):
        name = command.name

        if name == MOVE:
            return self.game.move(command.argument)
        if name == OPEN:
            return self.game.open_door(command.argument)
        if name == ATTACK:
            return self.game.attack(command.argument)
        if name == WAIT:
            return self.game.wait()
        if name == PICK_UP:
            return self.game.pick_up(command.argument)
        if name == DROP:
            return self.game.drop()
        if name == USE:
            return self.game.use_item()
        if name == EQUIP:
            return self.game.equip_item()
        if name == NEXT:
            return self.game.inventory_next()
        if name == PREVIOUS:
            return self.game.inventory_previous()
        if name == REWIND:
            return self.game.rewind()

        raise ValueError(f"Accion sin despachar: '{name}'.")
