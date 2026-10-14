from dataclasses import dataclass

from model.enemy import Enemy
from model.event import Event
from structures.event_queue import EventQueue


MOVE_COST = 100
ATTACK_COST = 100
WAIT_COST = 100
USE_ITEM_COST = 50
EQUIP_ITEM_COST = 50
OPEN_DOOR_COST = 50
PICK_UP_COST = 25
DROP_COST = 25

ACTOR_ACTION = "actor_action"

IN_PROGRESS = "en_curso"
VICTORY = "victoria"
DEFEAT = "derrota"


@dataclass
class ActionResult:
    accepted: bool
    message: str


@dataclass
class EnemyView:
    actor_id: str
    name: str
    health: int
    max_health: int


@dataclass
class VisibleState:
    clock: int
    result: str
    player_name: str
    health: int
    max_health: int
    attack: int
    defense: int
    speed: int
    room_id: int
    enemies: list
    messages: list


class Game:
    """Coordina el reloj, la agenda y los actores.

    Cada accion del jugador ejecuta la accion y despues procesa todos los
    eventos pendientes hasta que vuelva a tocarle decidir. El controlador no
    administra el reloj ni la agenda.

    Solo implementa esperar y atacar. Moverse, abrir puertas y las acciones de
    inventario esperan a que existan las salas y el inventario.
    """

    def __init__(self, state, player, enemies=None):
        self.state = state
        self.player = player
        self.enemies = [] if enemies is None else list(enemies)
        self.events = EventQueue()
        self.messages = []
        self.result = IN_PROGRESS

        self._schedule(self.player, self.state.clock)
        self._activate_enemies_in(self.player.room_id)
        self._advance_to_player_turn()

    def wait(self):
        return self._player_acts(WAIT_COST, "Esperas.")

    def attack(self, enemy_id):
        target = self._find_enemy(enemy_id)

        if target is None or not target.is_alive:
            return ActionResult(
                False, f"No hay ningun enemigo con vida identificado como {enemy_id}."
            )

        if target.room_id != self.player.room_id:
            return ActionResult(False, f"{target.name} no esta en esta sala.")

        damage = self._damage_from(self.player, target)
        target.take_damage(damage)
        message = f"Atacas a {target.name} y le quitas {damage} de vida."

        if not target.is_alive:
            self._remove_from_play(target)
            message = f"{message} {target.name} muere."

        return self._player_acts(ATTACK_COST, message)

    def change_actor_speed(self, actor, new_speed):
        """Aplica un cambio de velocidad y reprograma la accion pendiente.

        No modifica el evento que ya esta en la agenda: lo cancela e inserta uno
        nuevo con un numero de secuencia nuevo, como exige la seccion 2.3.
        """
        rescheduled = actor.change_speed(self.state.clock, new_speed)

        if rescheduled is None:
            return

        self.events.cancel(actor.scheduled_event)
        self._schedule(actor, rescheduled)

    def visible_state(self):
        enemies = [
            EnemyView(
                enemy.actor_id,
                enemy.name,
                enemy.health,
                enemy.max_health,
            )
            for enemy in self.enemies
            if enemy.is_alive and enemy.room_id == self.player.room_id
        ]

        return VisibleState(
            clock=self.state.clock,
            result=self.result,
            player_name=self.player.name,
            health=self.player.health,
            max_health=self.player.max_health,
            attack=self.player.effective_attack,
            defense=self.player.effective_defense,
            speed=self.player.speed,
            room_id=self.player.room_id,
            enemies=enemies,
            messages=list(self.messages),
        )

    def _player_acts(self, cost, message):
        self._log(message)
        self._schedule(
            self.player,
            self.player.next_time_after(self.state.clock, cost),
        )
        self._advance_to_player_turn()

        return ActionResult(True, message)

    def _advance_to_player_turn(self):
        while self.result == IN_PROGRESS:
            event = self.events.pop()

            if event is None:
                return

            if event.actor is not None and not event.actor.is_alive:
                continue

            self.state.advance_clock_to(event.time)

            if event.actor is not None:
                event.actor.scheduled_event = None

            if event.actor is self.player:
                return

            self._run_enemy_turn(event.actor)

    def _run_enemy_turn(self, enemy):
        action = enemy.decide_action(self.player)

        if action == Enemy.ATTACK:
            damage = self._damage_from(enemy, self.player)
            self.player.take_damage(damage)
            self._log(f"{enemy.name} te ataca y te quita {damage} de vida.")

            if not self.player.is_alive:
                self.result = DEFEAT
                self._log("Has muerto.")
                return

            cost = ATTACK_COST
        else:
            cost = WAIT_COST

        self._schedule(enemy, enemy.next_time_after(self.state.clock, cost))

    def _damage_from(self, attacker, defender):
        roll = self.state.random_generator.randint(0, 4)

        return max(
            1,
            attacker.effective_attack + roll - defender.effective_defense,
        )

    def _schedule(self, actor, time):
        event = Event(time, self.state.next_sequence(), ACTOR_ACTION, actor)
        actor.scheduled_event = event
        self.events.push(event)

        return event

    def _remove_from_play(self, actor):
        if actor.scheduled_event is not None:
            self.events.cancel(actor.scheduled_event)
            actor.scheduled_event = None

    def _find_enemy(self, enemy_id):
        for enemy in self.enemies:
            if enemy.actor_id == enemy_id:
                return enemy

        return None

    def _activate_enemies_in(self, room_id):
        pending = [
            enemy
            for enemy in self.enemies
            if enemy.room_id == room_id and not enemy.is_active
        ]

        for enemy in self._by_ascending_id(pending):
            enemy.is_active = True
            self._schedule(
                enemy,
                enemy.next_time_after(self.state.clock, WAIT_COST),
            )

    def _by_ascending_id(self, enemies):
        """Orden de activacion de la seccion 2.4, por insercion.

        Se reemplazara por el modulo de ordenamiento del proyecto cuando exista.
        """
        ordered = []

        for enemy in enemies:
            position = len(ordered)

            while position > 0 and ordered[position - 1].actor_id > enemy.actor_id:
                position -= 1

            ordered.insert(position, enemy)

        return ordered

    def _log(self, message):
        self.messages.append(message)
