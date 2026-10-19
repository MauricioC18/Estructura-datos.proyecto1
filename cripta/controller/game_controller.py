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
from adapters.fuente_datos import ErrorFuenteDatos
from model.game import IN_PROGRESS, ActionResult


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

    def __init__(self, game, replay_log=None, repository=None):
        self.game = game
        self.replay_log = replay_log
        self.repository = repository

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
