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

    def decide_action(self, player):
        """Accion que ejecuta el enemigo en su turno, segun la seccion 2.8.

        Compartir sala con el jugador tiene prioridad sobre el comportamiento.
        Mientras no existan las salas, el errante y el rastreador no pueden
        examinar salidas ni rastros, de modo que esperan, que es lo que el
        enunciado indica cuando no hay ninguna opcion disponible.
        """
        if self.room_id == player.room_id:
            return self.ATTACK

        return self.WAIT
