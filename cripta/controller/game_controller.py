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
from model.game import IN_PROGRESS


class GameController:
    """Traduce comandos del jugador en operaciones de Game.

    No sabe de donde vienen los comandos: el teclado y la reproduccion de un
    log le entregan el mismo Command. Por eso --replay no necesita la vista.

    replay_log es cualquier objeto con append(command). Solo se registran las
    acciones aceptadas, como acordo el grupo (ARQUITECTURA, seccion 6): una
    accion rechazada no consume tiempo, no cambia el estado ni consulta el
    azar, de modo que omitirla no cambia la partida reproducida.
    """

    def __init__(self, game, replay_log=None):
        self.game = game
        self.replay_log = replay_log

    def execute(self, command):
        if not is_game_action(command):
            raise ValueError(
                f"'{command.name}' no es una accion del modelo; la atiende la aplicacion."
            )

        result = self._dispatch(command)

        if result.accepted and self.replay_log is not None:
            self.replay_log.append(command)

        return result

    def visible_state(self):
        return self.game.visible_state()

    @property
    def is_over(self):
        return self.game.result != IN_PROGRESS

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
