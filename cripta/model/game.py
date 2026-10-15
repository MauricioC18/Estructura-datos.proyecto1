from dataclasses import dataclass

from model.effects import (
    ActiveEffect,
    DOOR_CLOSE,
    POISON,
    POISON_DURATION,
    POISON_PULSE,
    POISON_PULSE_INTERVAL,
    REGENERATION_INTERVAL,
    REGENERATION_PULSE,
    SPEED,
    SPEED_END,
    TORCH,
    TORCH_END,
    TRAP_REARM,
)
from model.enemy import Enemy
from model.event import Event
from model.item import Item
from model.room import DIRECTIONS
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

INVENTORY = "el inventario"
REVERSIBLE_HISTORY = "el historial reversible"


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
class EffectView:
    name: str
    ends_at: int | None


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
    effects: list
    torch_lit: bool
    messages: list


class Game:
    """Coordina el reloj, la agenda, los actores y los efectos temporales.

    Cada accion del jugador ejecuta la accion y despues procesa todos los
    eventos pendientes hasta que vuelva a tocarle decidir. El controlador no
    administra el reloj ni la agenda.

    Solo implementa esperar y atacar. Moverse, abrir puertas y las acciones de
    inventario esperan a que existan las salas y el inventario.

    message_log se recibe desde fuera. Cualquier estructura con append() y que
    se pueda recorrer sirve, de modo que la bitacora circular del proyecto
    encaje sin modificar esta clase. Si no se pasa ninguna se usa una list, que
    es provisional porque no cumple el limite de memoria de la seccion 4.8.
    """

    def __init__(
        self,
        state,
        player,
        enemies=None,
        room_map=None,
        exit_room_id=None,
        message_log=None,
        event_queue=None,
    ):
        self.state = state
        self.player = player
        self.enemies = [] if enemies is None else list(enemies)
        self.room_map = room_map
        self.exit_room_id = exit_room_id
        self.events = EventQueue() if event_queue is None else event_queue
        self.messages = [] if message_log is None else message_log
        self.effects = []
        self.torch_lit = False
        self.result = IN_PROGRESS
        self.player_actions = 0
        self.enemies_defeated = 0
        self.events_processed = 0

        self._schedule(self.player, self.state.clock)
        self._activate_enemies_in(self.player.room_id)
        self._advance_to_player_turn()

    def wait(self):
        if self.is_over:
            return self._game_already_ended()

        return self._player_acts(WAIT_COST, "Esperas.")

    def attack(self, enemy_id):
        if self.is_over:
            return self._game_already_ended()

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
            self._check_death(target)
            message = f"{message} {target.name} muere."

        return self._player_acts(ATTACK_COST, message)

    def move(self, direction):
        """Mueve al jugador a la sala vecina en esa direccion (§2.5).

        El contenido de la sala destino tiene que estar ya en memoria. El
        modelo no sabe de donde sale: quien lo carga antes de llamar es el
        controlador, con el repositorio del bloque 2 (§4.2 y §6).
        """
        if self.is_over:
            return self._game_already_ended()

        rejection, exit_ = self._exit_towards(direction)

        if rejection is not None:
            return rejection

        if not exit_.door.is_open:
            return ActionResult(
                False, f"La puerta hacia {direction} esta cerrada."
            )

        destination = self.room_map.room(exit_.destination)

        if not destination.content_loaded:
            return ActionResult(
                False,
                f"El contenido de la sala {destination.room_id} todavia no esta "
                "disponible.",
            )

        self.player.room_id = destination.room_id
        self._activate_enemies_in(destination.room_id)
        message = f"Entras a {destination.name}."
        self._log(message)

        if destination.room_id == self.exit_room_id:
            self.result = VICTORY
            self._log("Has encontrado la salida de la cripta.")
            self.player_actions += 1

            return ActionResult(True, message)

        self._trigger_traps(destination)

        if self.is_over:
            self.player_actions += 1

            return ActionResult(True, message)

        return self._finish_player_action(MOVE_COST, message)

    def open_door(self, direction):
        """Abre la puerta de esa salida si el jugador tiene la llave (§2.5).

        La llave no se consume. Si la salida declara cierre automatico, se
        programa el cierre para el intervalo que indica la cripta (§2.10).
        """
        if self.is_over:
            return self._game_already_ended()

        rejection, exit_ = self._exit_towards(direction)

        if rejection is not None:
            return rejection

        door = exit_.door

        if door.is_open:
            return ActionResult(
                False, f"La puerta hacia {direction} ya esta abierta."
            )

        if not self._player_has_key(door.key_id):
            return ActionResult(
                False, f"No tienes la llave de la puerta hacia {direction}."
            )

        door.closed = False
        message = f"Abres la puerta hacia {direction}."

        if door.auto_close is not None:
            self._schedule_door_close(
                self.player.room_id, direction, door.auto_close
            )

        return self._player_acts(OPEN_DOOR_COST, message)

    def pick_up(self, floor_index):
        return self._not_available_yet("recoger objetos", INVENTORY)

    def drop(self):
        return self._not_available_yet("soltar objetos", INVENTORY)

    def use_item(self):
        return self._not_available_yet("usar objetos", INVENTORY)

    def equip_item(self):
        return self._not_available_yet("equipar objetos", INVENTORY)

    def inventory_next(self):
        return self._not_available_yet("recorrer el inventario", INVENTORY)

    def inventory_previous(self):
        return self._not_available_yet("recorrer el inventario", INVENTORY)

    def rewind(self):
        return self._not_available_yet("usar un pergamino", REVERSIBLE_HISTORY)

    def apply_poison(self, target, damage):
        """Programa de una vez todas las activaciones del veneno (seccion 2.10).

        La duracion y el intervalo son fijos, de modo que al aplicarlo ya se
        conocen los cinco instantes en que hara dano. Programarlos juntos deja
        cada pulso sin estado propio y convierte el antidoto en la cancelacion
        de unos eventos concretos.
        """
        events = []
        end_time = self.state.clock + POISON_DURATION
        pulse_time = self.state.clock + POISON_PULSE_INTERVAL

        while pulse_time <= end_time:
            events.append(
                self._schedule_effect(POISON_PULSE, target, pulse_time, damage)
            )
            pulse_time += POISON_PULSE_INTERVAL

        effect = ActiveEffect(POISON, target, events, end_time)
        self.effects.append(effect)

        return effect

    def cancel_poison(self, target):
        """Efecto del antidoto: impide las activaciones futuras del veneno."""
        cancelled = False

        for effect in self.effects:
            if effect.name == POISON and effect.target is target:
                if not effect.cancelled:
                    self._cancel_effect(effect)
                    cancelled = True

        return cancelled

    def apply_regeneration(self, target, amount):
        """Un enemigo que declare regeneracion se cura cada 200 unidades.

        No se registra como efecto cancelable: se detiene sola cuando el actor
        muere, porque el bucle descarta los eventos de los actores sin vida, y
        cada pulso programa el siguiente a partir del propio evento.
        """
        return self._schedule_effect(
            REGENERATION_PULSE,
            target,
            self.state.clock + REGENERATION_INTERVAL,
            amount,
        )

    def apply_speed_change(self, actor, new_speed, duration):
        """Cambio temporal de velocidad, con reajuste al comenzar y al terminar.

        Un efecto nuevo reemplaza al anterior en lugar de encimarse. Antes de
        aplicarlo se devuelve la velocidad original, de modo que el evento de fin
        del efecto nuevo restaure esa velocidad y no la del efecto anterior.
        """
        self._end_previous_speed_effect(actor)

        previous_speed = actor.speed
        self.change_actor_speed(actor, new_speed)

        end_time = self.state.clock + duration
        event = self._schedule_effect(SPEED_END, actor, end_time, previous_speed)
        effect = ActiveEffect(SPEED, actor, [event], end_time)
        self.effects.append(effect)

        return effect

    def light_torch(self, duration):
        self.torch_lit = True
        end_time = self.state.clock + duration
        event = self._schedule_effect(TORCH_END, self.player, end_time)
        effect = ActiveEffect(TORCH, self.player, [event], end_time)
        self.effects.append(effect)

        return effect

    @property
    def is_over(self):
        return self.result != IN_PROGRESS

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

        effects = [
            EffectView(effect.name, effect.ends_at)
            for effect in self.effects
            if effect.target is self.player and not effect.cancelled
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
            effects=effects,
            torch_lit=self.torch_lit,
            messages=list(self.messages),
        )

    def _player_acts(self, cost, message):
        self._log(message)

        return self._finish_player_action(cost, message)

    def _finish_player_action(self, cost, message):
        """Programa la siguiente accion del jugador y corre el ciclo.

        Esta separado de _player_acts porque moverse anota su mensaje antes de
        disparar las trampas, para que el jugador lea primero que entro a la
        sala y despues lo que le paso adentro.
        """
        self.player_actions += 1
        self._schedule(
            self.player,
            self.player.next_time_after(self.state.clock, cost),
        )
        self._advance_to_player_turn()
        self._forget_finished_effects()

        return ActionResult(True, message)

    def _advance_to_player_turn(self):
        while self.result == IN_PROGRESS:
            event = self.events.pop()

            if event is None:
                return

            if event.actor is not None and not event.actor.is_alive:
                continue

            self.state.advance_clock_to(event.time)
            self.events_processed += 1

            if event.event_type != ACTOR_ACTION:
                self._run_effect(event)
                continue

            event.actor.scheduled_event = None

            if event.actor is self.player:
                return

            self._run_enemy_turn(event.actor)

    def _run_effect(self, event):
        if event.event_type == POISON_PULSE:
            event.actor.take_damage(event.amount)
            self._log(f"El veneno le quita {event.amount} de vida a {event.actor.name}.")
            self._check_death(event.actor)
        elif event.event_type == REGENERATION_PULSE:
            event.actor.heal(event.amount)
            self._schedule_effect(
                REGENERATION_PULSE,
                event.actor,
                self.state.clock + REGENERATION_INTERVAL,
                event.amount,
            )
        elif event.event_type == SPEED_END:
            self.change_actor_speed(event.actor, event.amount)
        elif event.event_type == TORCH_END:
            self.torch_lit = False
            self._log("La antorcha se apaga.")
        elif event.event_type == DOOR_CLOSE:
            self._close_door(event.room_id, event.direction)
        elif event.event_type == TRAP_REARM:
            self._rearm_trap(event.room_id, event.instance_id)

    def _run_enemy_turn(self, enemy):
        action, chosen_exit = enemy.decide_action(
            self.player,
            self._room_of(enemy),
            self.state.random_generator,
        )

        if action == Enemy.ATTACK:
            damage = self._damage_from(enemy, self.player)
            self.player.take_damage(damage)
            self._log(f"{enemy.name} te ataca y te quita {damage} de vida.")
            self._check_death(self.player)

            if self.result == DEFEAT:
                return

            cost = ATTACK_COST
        elif action == Enemy.MOVE:
            enemy.room_id = chosen_exit.destination
            cost = MOVE_COST
        else:
            cost = WAIT_COST

        self._schedule(enemy, enemy.next_time_after(self.state.clock, cost))

    def _room_of(self, actor):
        if self.room_map is None:
            return None

        return self.room_map.room(actor.room_id)

    def _check_death(self, actor):
        if actor.is_alive:
            return

        if actor is self.player:
            self.result = DEFEAT
            self._log("Has muerto.")
            return

        self.enemies_defeated += 1
        self._drop_what_it_carries(actor)
        self._remove_from_play(actor)

    def _drop_what_it_carries(self, enemy):
        """Los objetos que suelta un enemigo van al suelo de su sala (§2.6)."""
        if not enemy.drops or self.room_map is None:
            return

        self.room_map.room(enemy.room_id).floor_items.extend(enemy.drops)
        names = ", ".join(item.name for item in enemy.drops)
        self._log(f"{enemy.name} suelta: {names}.")

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

    def _schedule_effect(
        self,
        event_type,
        actor,
        time,
        amount=None,
        room_id=None,
        direction=None,
        instance_id=None,
    ):
        event = Event(
            time,
            self.state.next_sequence(),
            event_type,
            actor,
            amount=amount,
            room_id=room_id,
            direction=direction,
            instance_id=instance_id,
        )
        self.events.push(event)

        return event

    def _game_already_ended(self):
        return ActionResult(False, "La partida ya termino.")

    def _not_available_yet(self, what, missing_module):
        """Rechazo de una accion que el motor todavia no puede ejecutar.

        No es un rechazo por una regla del juego: la accion existe en el
        enunciado y falta la estructura de otro integrante. Se devuelve un
        rechazo en lugar de dejar que el controlador reviente, y como toda
        accion rechazada no consume tiempo ni se registra en la bitacora de
        reproduccion. Al llegar la estructura se reemplaza el cuerpo del
        metodo y la interfaz no cambia.
        """
        return ActionResult(
            False, f"Todavia no se puede {what}: falta {missing_module}."
        )

    def _exit_towards(self, direction):
        """Devuelve (rechazo, salida). Uno de los dos es siempre None."""
        if self.room_map is None:
            return ActionResult(False, "La cripta todavia no esta cargada."), None

        if direction not in DIRECTIONS:
            return ActionResult(False, f"Direccion invalida: {direction}."), None

        room = self.room_map.room(self.player.room_id)
        exit_ = room.exit_towards(direction)

        if exit_ is None:
            return ActionResult(False, f"No hay salida hacia {direction}."), None

        return None, exit_

    def _player_has_key(self, key_id):
        """La puerta declara el id de la ficha de la llave que la abre.

        §2.7 dice que una llave abre las puertas cuya llave coincide con su id,
        asi que se compara contra type_id y no contra el campo `abre` de la
        ficha, que en los datos reales nombra la puerta y no la llave.
        """
        if key_id is None:
            return True

        if self.player.inventory is None:
            return False

        for item in self.player.inventory:
            if item.item_class == Item.KEY and item.type_id == key_id:
                return True

        return False

    def _trigger_traps(self, room):
        """Activa las trampas armadas de la sala en la que entra el jugador.

        Ocurre en el instante actual, justo despues de completar el movimiento
        y antes de procesar el siguiente evento del reloj (§2.10).
        """
        for trap in room.traps:
            if not trap.armed:
                continue

            trap.armed = False
            self.player.take_damage(trap.damage)
            self._log(f"{trap.name} te quita {trap.damage} de vida.")
            self._schedule_effect(
                TRAP_REARM,
                None,
                self.state.clock + trap.rearm_interval,
                room_id=room.room_id,
                instance_id=trap.instance_id,
            )
            self._check_death(self.player)

            if self.is_over:
                return

    def _schedule_door_close(self, room_id, direction, interval):
        return self._schedule_effect(
            DOOR_CLOSE,
            None,
            self.state.clock + interval,
            room_id=room_id,
            direction=direction,
        )

    def _close_door(self, room_id, direction):
        exit_ = self.room_map.room(room_id).exit_towards(direction)

        if exit_ is None or exit_.door.closed:
            return

        exit_.door.closed = True
        self._log(f"La puerta hacia {direction} se cierra sola.")

    def _rearm_trap(self, room_id, instance_id):
        for trap in self.room_map.room(room_id).traps:
            if trap.instance_id == instance_id:
                trap.armed = True
                return

    def _end_previous_speed_effect(self, actor):
        for effect in self.effects:
            if (
                effect.name != SPEED
                or effect.target is not actor
                or effect.cancelled
                or effect.ends_at <= self.state.clock
            ):
                continue

            original_speed = effect.events[0].amount
            self.change_actor_speed(actor, original_speed)
            self._cancel_effect(effect)

    def _cancel_effect(self, effect):
        for event in effect.events:
            self.events.cancel(event)

        effect.cancelled = True

    def _forget_finished_effects(self):
        self.effects = [
            effect
            for effect in self.effects
            if not effect.cancelled
            and (effect.ends_at is None or effect.ends_at > self.state.clock)
        ]

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

            if enemy.regeneration > 0:
                self.apply_regeneration(enemy, enemy.regeneration)

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
