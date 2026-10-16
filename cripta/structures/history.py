"""
Historial reversible del pergamino de retroceso (§2.11, §4.6).

Problema que resuelve
    Volver al estado inmediatamente anterior a la ultima accion del jugador,
    incluyendo todo lo que ocurrio despues de ella y antes de su siguiente
    decision, sin guardar copias del estado.

Como funciona
    Es un registro de cambios inversos. Cada accion del jugador abre un
    intervalo; cada modificacion del estado anota lo minimo para deshacerse:
    el valor anterior de un atributo, o la operacion que la revierte. Deshacer
    aplica las anotaciones del ultimo intervalo en orden inverso.

    Los intervalos van en un CircularBuffer de 5: al abrir el sexto, el mas
    antiguo se descarta solo.

    El reloj se guarda una vez por intervalo, al abrirlo, y se devuelve con
    GameState.rewind_clock_to(). El contador de secuencia no se guarda
    (Documento de Decisiones, "El reloj virtual y la numeracion de eventos").

Complejidad (c = cambios del intervalo)
    begin_action, record, assign: O(1). undo: O(c).
    Espacio: proporcional a los cambios de las ultimas 5 acciones, no al
    tamano de la partida.

Quien modifica el estado del juego entre dos decisiones del jugador debe
anotarlo aqui. La agenda lo hace sola si se usa ReversibleEventQueue.
"""
from structures.circular_log import CircularBuffer
from structures.event_queue import EventQueue

MAX_REWIND_ACTIONS = 5
ACTOR_ACTION = "actor_action"


class Change:

    def undo(self):
        raise NotImplementedError


class AttributeChange(Change):
    """Devuelve un atributo a su valor anterior. Sirve tambien con propiedades."""

    __slots__ = ("target", "attribute", "previous")

    def __init__(self, target, attribute, previous):
        self.target = target
        self.attribute = attribute
        self.previous = previous

    def undo(self):
        setattr(self.target, self.attribute, self.previous)


class CallbackChange(Change):
    """Ejecuta la operacion inversa, por ejemplo devolver un evento a la agenda."""

    __slots__ = ("function", "arguments")

    def __init__(self, function, *arguments):
        self.function = function
        self.arguments = arguments

    def undo(self):
        self.function(*self.arguments)


class _Interval:
    __slots__ = ("clock", "changes")

    def __init__(self, clock):
        self.clock = clock
        self.changes = []


class History:

    def __init__(self, state, max_actions=MAX_REWIND_ACTIONS):
        self._state = state
        self._intervals = CircularBuffer(max_actions)
        self._current = None
        self._undoing = False

    @property
    def max_actions(self):
        return self._intervals.capacity

    def available_actions(self):
        return len(self._intervals)

    def can_undo(self):
        return not self._intervals.is_empty()

    @property
    def is_undoing(self):
        return self._undoing

    @property
    def is_recording(self):
        return self._current is not None and not self._undoing

    def begin_action(self):
        """Se llama cuando una accion del jugador ya fue aceptada, antes de
        modificar nada. Las acciones rechazadas no abren intervalo."""
        self._current = _Interval(self._state.clock)
        self._intervals.append(self._current)

    def record(self, change):
        if self.is_recording:
            self._current.changes.append(change)

    def assign(self, target, attribute, value):
        """Cambia un atributo y anota su valor anterior."""
        if self.is_recording:
            self._current.changes.append(
                AttributeChange(target, attribute, getattr(target, attribute))
            )

        setattr(target, attribute, value)

    def list_append(self, items, element):
        items.append(element)
        self.record(CallbackChange(_pop_last, items))

    def list_pop(self, items, index):
        element = items.pop(index)
        self.record(CallbackChange(items.insert, index, element))
        return element

    def undo(self):
        """Revierte la ultima accion del jugador. Devuelve False si no hay."""
        if self._intervals.is_empty():
            return False

        interval = self._intervals.pop_last()
        self._current = None
        self._undoing = True

        try:
            changes = interval.changes
            for index in range(len(changes) - 1, -1, -1):
                changes[index].undo()
            self._state.rewind_clock_to(interval.clock)
        finally:
            self._undoing = False

        return True

    def recorded_changes(self):
        total = 0
        for interval in self._intervals:
            total += len(interval.changes)

        return total

    def clear(self):
        """Al cargar una partida guardada el historial anterior ya no aplica."""
        self._intervals.clear()
        self._current = None


def _pop_last(items):
    items.pop()


class ReversibleEventQueue(EventQueue):
    """Agenda que anota en el historial lo necesario para revertirse.

    Es una subclase, igual que CountingEventQueue, para no tocar EventQueue.
    Game la recibe por su parametro event_queue.

    Cada operacion anota su inversa:
        push(e)           -> marcar e como cancelado
        sacar e del heap  -> volver a insertar e, con su mismo time y sequence
        cancel(e)         -> devolver e.cancelled a su valor anterior

    "Sacar del heap" incluye los pop() del motor y tambien los eventos
    cancelados que el monticulo descarta por dentro, por eso se intercepta
    _remove_root. Un evento reinsertado conserva su time y sequence, asi que
    el monticulo recupera el mismo orden.

    Para las acciones de actores tambien se restaura actor.scheduled_event,
    que el motor pone en None al sacar el evento y reemplaza al programar.
    """

    def __init__(self, history, actor_action_type=ACTOR_ACTION):
        super().__init__()
        self._history = history
        self._actor_action_type = actor_action_type

    def push(self, event):
        super().push(event)
        self._history.record(CallbackChange(self._undo_push, event))

    def cancel(self, event):
        self._history.record(AttributeChange(event, "cancelled", event.cancelled))
        super().cancel(event)

        if self._is_actor_action(event):
            self._history.record(CallbackChange(self._restore_scheduled, event))

    def _remove_root(self, *args):
        root = super()._remove_root(*args)
        self._history.record(CallbackChange(self._undo_remove, root))
        return root

    def _undo_push(self, event):
        event.cancelled = True

        if self._is_actor_action(event) and event.actor.scheduled_event is event:
            event.actor.scheduled_event = None

    def _undo_remove(self, event):
        EventQueue.push(self, event)

        if self._is_actor_action(event) and not event.cancelled:
            event.actor.scheduled_event = event

    def _restore_scheduled(self, event):
        event.actor.scheduled_event = event

    def _is_actor_action(self, event):
        return event.event_type == self._actor_action_type and event.actor is not None


def use_rewind_scroll(inventory, history):
    """Usa un pergamino: revierte la ultima accion y despues lo consume.

    No consume tiempo ni abre intervalo (§2.11). Devuelve False, sin tocar
    nada, si no hay pergamino o no hay acciones por revertir.
    """
    if inventory.scroll_count() == 0 or not history.can_undo():
        return False

    history.undo()
    inventory.consume_scroll()
    return True
