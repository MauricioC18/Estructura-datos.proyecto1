from model.actor import Actor


class Enemy(Actor):
    """Instancia de enemigo.

    Los valores de behavior son los que entrega el catalogo. El enunciado solo
    confirma "rastreador" en su ejemplo; GUARDIAN y WANDERER deben verificarse
    contra el servicio real antes de confiar en ellos.
    """

    GUARDIAN = "guardian"
    WANDERER = "errante"
    TRACKER = "rastreador"

    ATTACK = "attack"
    WAIT = "wait"
    MOVE = "move"

    def __init__(
        self,
        actor_id,
        name,
        max_health,
        attack,
        defense,
        speed,
        room_id,
        behavior,
        health=None,
        drops=None,
        regeneration=0,
    ):
        super().__init__(
            actor_id,
            name,
            max_health,
            attack,
            defense,
            speed,
            room_id,
            health,
        )
        self.behavior = behavior
        self.drops = [] if drops is None else list(drops)
        self.regeneration = regeneration
        self.is_active = False

    def decide_action(
        self,
        player,
        room=None,
        random_generator=None,
        trail=None,
        current_time=0,
    ):
        """Accion del enemigo en su turno, segun la seccion 2.8.

        Devuelve el par (accion, salida). La salida solo viene con MOVE.

        Compartir sala con el jugador tiene prioridad sobre el comportamiento:
        si lo comparte ataca y no se mueve, sin importar cual sea.
        """
        if self.room_id == player.room_id:
            return self.ATTACK, None

        if self.behavior == self.WANDERER:
            return self._wander(room, random_generator)

        if self.behavior == self.TRACKER:
            return self._track(room, trail, current_time)

        return self.WAIT, None

    def _track(self, room, trail, current_time):
        """Sigue el rastro fresco mas reciente, o espera si no hay (§2.9).

        Las reglas de cual salida elegir viven en el rastro: examina solo las
        vecinas por salidas abiertas, descarta los rastros de 400 unidades o
        mas, y desempata por la sala de menor id.
        """
        if room is None or trail is None:
            return self.WAIT, None

        chosen = trail.freshest_exit(room, current_time)

        if chosen is None:
            return self.WAIT, None

        return self.MOVE, chosen

    def _wander(self, room, random_generator):
        """Escoge al azar una salida abierta, o espera si no hay ninguna.

        Un enemigo no puede abrir puertas cerradas (§2.5), asi que solo cuentan
        las salidas cuya puerta esta abierta.
        """
        if room is None or random_generator is None:
            return self.WAIT, None

        open_exits = []

        for exit_ in room.exits():
            if exit_.door.is_open:
                open_exits.append(exit_)

        if not open_exits:
            return self.WAIT, None

        return self.MOVE, random_generator.choice(open_exits)
