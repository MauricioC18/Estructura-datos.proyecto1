POISON_PULSE = "poison_pulse"
REGENERATION_PULSE = "regeneration_pulse"
SPEED_END = "speed_end"
TORCH_END = "torch_end"
DOOR_CLOSE = "door_close"
TRAP_REARM = "trap_rearm"

POISON_PULSE_INTERVAL = 80
POISON_DURATION = 400
REGENERATION_INTERVAL = 200

POISON = "veneno"
SPEED = "velocidad"
TORCH = "antorcha"


class ActiveEffect:
    """Un efecto en curso sobre un actor.

    Guarda los eventos que todavia puede activar, para poder cancelarlos todos
    cuando el efecto se interrumpe, y el instante en que termina, para mostrarlo
    en la interfaz.
    """

    def __init__(self, name, target, events, ends_at=None):
        self.name = name
        self.target = target
        self.events = list(events)
        self.ends_at = ends_at
        self.cancelled = False
