class Actor:
    """Atributos y comportamiento comunes del jugador y de los enemigos.

    scheduled_event guarda la referencia al evento pendiente del actor, para
    que el motor pueda cancelarlo en O(1) cuando el actor muere.
    """

    SPEED_REFERENCE = 100

    def __init__(
        self,
        actor_id,
        name,
        max_health,
        attack,
        defense,
        speed,
        room_id,
        health=None,
    ):
        self.actor_id = actor_id
        self.name = name
        self.max_health = max_health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.room_id = room_id
        self.health = max_health if health is None else health
        self.scheduled_event = None

    @property
    def actor_id(self):
        return self._actor_id

    @actor_id.setter
    def actor_id(self, value):
        if not value:
            raise ValueError("El identificador del actor no puede estar vacio.")

        self._actor_id = value

    @property
    def max_health(self):
        return self._max_health

    @max_health.setter
    def max_health(self, value):
        if value <= 0:
            raise ValueError(
                f"La vida maxima debe ser mayor que cero, se recibio {value}."
            )

        self._max_health = value

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        self._health = min(max(value, 0), self._max_health)

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        if value <= 0:
            raise ValueError(
                f"La velocidad debe ser mayor que cero, se recibio {value}."
            )

        self._speed = value

    @property
    def is_alive(self):
        return self._health > 0

    @property
    def effective_attack(self):
        return self.attack

    @property
    def effective_defense(self):
        return self.defense

    def interval_for(self, cost):
        return max(1, cost * self.SPEED_REFERENCE // self._speed)

    def next_time_after(self, current_time, cost):
        return current_time + self.interval_for(cost)

    def change_speed(self, current_time, new_speed):
        """Cambia la velocidad y devuelve el instante reprogramado, o None.

        Calcula con la velocidad anterior antes de reemplazarla, segun la
        seccion 2.3 del enunciado. Devuelve None si el actor no tiene una
        accion pendiente. El motor se encarga de cancelar el evento anterior y
        de programar el nuevo con un numero de secuencia nuevo.
        """
        if self.scheduled_event is None:
            self.speed = new_speed
            return None

        remaining = self.scheduled_event.time - current_time
        rescaled = max(1, remaining * self._speed // new_speed)
        self.speed = new_speed

        return current_time + rescaled

    def take_damage(self, amount):
        self.health = self._health - amount

    def heal(self, amount):
        self.health = self._health + amount

    def __str__(self):
        return f"{self.name} ({self._health}/{self._max_health})"
