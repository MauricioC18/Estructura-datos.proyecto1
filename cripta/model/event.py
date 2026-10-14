from dataclasses import dataclass

from model.actor import Actor


@dataclass
class Event:
    """Evento programado en el reloj virtual.

    actor y target guardan la referencia al objeto, no su identificador, para
    que el motor no tenga que buscarlos al procesar cada evento. El
    identificador sigue disponible como actor.actor_id.

    Los campos de carga son opcionales y cada tipo de evento usa los que
    necesita: amount para el dano del veneno, la regeneracion o el
    modificador de velocidad; room_id y direction para el cierre de una
    puerta; room_id e instance_id para el rearme de una trampa.
    """

    time: int
    sequence: int
    event_type: str
    actor: Actor | None = None
    target: Actor | None = None
    amount: int | None = None
    room_id: int | None = None
    direction: str | None = None
    instance_id: str | None = None
    cancelled: bool = False
