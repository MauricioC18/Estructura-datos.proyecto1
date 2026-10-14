from model.actor import Actor


class Player(Actor):
    """El jugador.

    El arma y la armadura equipadas se tratan por duck typing: cualquier objeto
    con attack_bonus o defense_bonus sirve, para no depender del catalogo.

    inventory se asigna desde fuera, para que la estructura de inventario encaje
    sin modificar esta clase.
    """

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
        self.equipped_weapon = None
        self.equipped_armor = None
        self.inventory = None

    @property
    def effective_attack(self):
        if self.equipped_weapon is None:
            return self.attack

        return self.attack + self.equipped_weapon.attack_bonus

    @property
    def effective_defense(self):
        if self.equipped_armor is None:
            return self.defense

        return self.defense + self.equipped_armor.defense_bonus
