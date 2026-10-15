from dataclasses import dataclass

DEFAULT_REARM_INTERVAL = 300


@dataclass
class Trap:
    """Instancia de una trampa en una sala (§2.10).

    Una trampa armada se activa cuando el jugador entra a la sala: aplica su
    dano, queda desarmada y se rearma rearm_interval unidades despues. Si la
    ficha no indica el intervalo, se usa DEFAULT_REARM_INTERVAL.

    instance_id y room_id son los mismos datos que usa Event para programar el
    rearme. Las reglas las aplica el motor; esta clase solo guarda el estado.

    La crea el traductor del bloque 2 (repository/traductor.py).
    """

    instance_id: str
    type_id: str
    name: str
    damage: int
    rearm_interval: int
    room_id: int
    armed: bool = True
