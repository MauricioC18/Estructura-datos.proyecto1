"""
Inventario del jugador (§2.7, §4.5).

Problema que resuelve
    Recorrer hacia adelante y hacia atras desde la posicion actual, soltar el
    objeto que se esta viendo sin que el costo dependa de su posicion, mover al
    frente el objeto que se equipa y mostrar vistas ordenadas por peso, valor o
    nombre sin alterar el orden real.

Estructura
    Lista doblemente enlazada con dos nodos centinela y un cursor que apunta al
    nodo que se esta viendo. Con el nodo en la mano, quitarlo o moverlo al
    frente solo reenlaza punteros vecinos: O(1) en cualquier posicion. Una list
    de Python desplazaria los elementos de detras (O(n) segun la posicion).

Complejidad (n = objetos en el inventario)
    pick_up, drop_current, equip_current, next, previous: O(1).
    sorted_view: la del algoritmo de structures/sorting.py sobre una copia.
    consume_scroll: O(n), con n acotado por inventario_max.
    Espacio: O(n).

Equipo
    El arma y la armadura equipadas siguen viviendo en Player
    (equipped_weapon, equipped_armor), que es quien las usa para calcular el
    ataque y la defensa. El inventario solo las actualiza.

Cursor
    Recoger deja el cursor sobre el objeto recogido, para que "recoger" y
    despues "equipar" o "usar" actuen sobre el sin un "sig" en medio. El
    enunciado no define este caso; es una decision de implementacion.

Retroceso
    Con un History, cada cambio anota su inversa. Los movimientos de un
    pergamino de retroceso no se anotan: §2.11 los deja fuera del retroceso.
    El cursor no es estado del juego y no se restaura, salvo al deshacer un
    soltar, donde vuelve al objeto restaurado.
"""
from model.item import Item
from structures.history import Change
from structures.sorting import sort

SORT_CRITERIA = ("peso", "valor", "nombre")


def is_rewind_scroll(item):
    return item.item_class == Item.REWIND_SCROLL


def _by_weight(item):
    return item.weight


def _by_value(item):
    return item.value


def _by_name(item):
    return item.name.lower()


def _key_for(criterion):
    if criterion == "peso":
        return _by_weight
    if criterion == "valor":
        return _by_value
    if criterion == "nombre":
        return _by_name

    raise ValueError(f"Criterio de orden invalido: {criterion}. Se esperaba peso, valor o nombre.")


class _Node:
    __slots__ = ("item", "previous", "next", "linked")

    def __init__(self, item):
        self.item = item
        self.previous = None
        self.next = None
        self.linked = False


class DoublyLinkedList:
    """Lista doble con centinelas: no hay casos especiales en los extremos."""

    def __init__(self):
        self._head = _Node(None)
        self._tail = _Node(None)
        self._head.next = self._tail
        self._tail.previous = self._head
        self._size = 0

    def __len__(self):
        return self._size

    def first(self):
        return None if self._size == 0 else self._head.next

    def next_of(self, node):
        return None if node.next is self._tail else node.next

    def previous_of(self, node):
        return None if node.previous is self._head else node.previous

    def append(self, node):
        self._link_after(self._tail.previous, node)

    def push_front(self, node):
        self._link_after(self._head, node)

    def insert_after(self, reference, node):
        self._require_linked(reference)
        self._link_after(reference, node)

    def insert_before(self, reference, node):
        self._require_linked(reference)
        self._link_after(reference.previous, node)

    def remove(self, node):
        self._require_linked(node)
        node.previous.next = node.next
        node.next.previous = node.previous
        node.previous = None
        node.next = None
        node.linked = False
        self._size -= 1

    def move_to_front(self, node):
        self.remove(node)
        self._link_after(self._head, node)

    def nodes(self):
        node = self._head.next
        while node is not self._tail:
            following = node.next
            yield node
            node = following

    def __iter__(self):
        for node in self.nodes():
            yield node.item

    def reversed_items(self):
        node = self._tail.previous
        while node is not self._head:
            yield node.item
            node = node.previous

    def _link_after(self, anchor, node):
        if node.linked:
            raise ValueError("El nodo ya esta en la lista.")

        following = anchor.next
        node.previous = anchor
        node.next = following
        anchor.next = node
        following.previous = node
        node.linked = True
        self._size += 1

    def _require_linked(self, node):
        if node is None or not node.linked:
            raise ValueError("El nodo no esta en la lista.")


class _PickUpChange(Change):
    __slots__ = ("inventory", "node")

    def __init__(self, inventory, node):
        self.inventory = inventory
        self.node = node

    def undo(self):
        self.inventory._unlink(self.node)


class _PositionChange(Change):
    """Devuelve un nodo a donde estaba: deshace soltar y equipar."""

    __slots__ = ("inventory", "node", "previous", "following", "was_dropped")

    def __init__(self, inventory, node, previous, following, was_dropped):
        self.inventory = inventory
        self.node = node
        self.previous = previous
        self.following = following
        self.was_dropped = was_dropped

    def undo(self):
        if not self.was_dropped:
            self.inventory._items.remove(self.node)

        self.inventory._relink(self.node, self.previous, self.following)

        if self.was_dropped:
            self.inventory._cursor = self.node


class Inventory:
    """Se asigna a Player.inventory. Recorrerlo da los Item en el orden real."""

    def __init__(self, capacity, history=None):
        if capacity < 1:
            raise ValueError(f"La capacidad del inventario debe ser al menos 1, se recibio {capacity}.")

        self._items = DoublyLinkedList()
        self._capacity = capacity
        self._cursor = None
        self._scrolls = 0
        self._history = history

    @property
    def capacity(self):
        return self._capacity

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def is_empty(self):
        return len(self._items) == 0

    def is_full(self):
        return len(self._items) >= self._capacity

    def current(self):
        return None if self._cursor is None else self._cursor.item

    def next(self):
        if self._cursor is None:
            return False

        following = self._items.next_of(self._cursor)
        if following is None:
            return False

        self._cursor = following
        return True

    def previous(self):
        if self._cursor is None:
            return False

        previous = self._items.previous_of(self._cursor)
        if previous is None:
            return False

        self._cursor = previous
        return True

    def go_to_start(self):
        self._cursor = self._items.first()

    def scroll_count(self):
        return self._scrolls

    def pick_up(self, item):
        """Agrega al final del orden real y deja el cursor sobre el objeto.

        Devuelve False si esta lleno (Apendice B).
        """
        if self.is_full():
            return False

        node = _Node(item)
        self._items.append(node)
        self._cursor = node

        if is_rewind_scroll(item):
            self._scrolls += 1
        else:
            self._record(_PickUpChange(self, node))

        return True

    def drop_current(self, player=None):
        """Quita el objeto que se esta viendo y lo devuelve, o None si no hay.

        Si estaba equipado, el jugador lo deja de tener equipado. Colocarlo en
        el suelo de la sala le corresponde al motor.
        """
        node = self._cursor
        if node is None:
            return None

        item = node.item
        previous = self._items.previous_of(node)
        following = self._items.next_of(node)

        if not is_rewind_scroll(item):
            self._record(_PositionChange(self, node, previous, following, True))

        if player is not None:
            if player.equipped_weapon is item:
                self._assign(player, "equipped_weapon", None)
            if player.equipped_armor is item:
                self._assign(player, "equipped_armor", None)

        self._unlink(node)
        return item

    def can_equip_current(self):
        item = self.current()
        return item is not None and item.item_class in (Item.WEAPON, Item.ARMOR)

    def equip_current(self, player):
        """Equipa el objeto actual y lo mueve al frente del orden real.

        Devuelve el objeto que fue sustituido, que permanece en el inventario,
        o None. Lanza ValueError si el objeto actual no es arma ni armadura.
        """
        if not self.can_equip_current():
            raise ValueError("El objeto que se esta viendo no se puede equipar.")

        node = self._cursor
        item = node.item
        self._record(
            _PositionChange(
                self,
                node,
                self._items.previous_of(node),
                self._items.next_of(node),
                False,
            )
        )
        self._items.move_to_front(node)

        attribute = "equipped_weapon" if item.item_class == Item.WEAPON else "equipped_armor"
        replaced = getattr(player, attribute)
        self._assign(player, attribute, item)

        return None if replaced is item else replaced

    def consume_scroll(self):
        """Quita un pergamino sin anotarlo en el historial (§2.11)."""
        for node in self._items.nodes():
            if is_rewind_scroll(node.item):
                self._unlink(node)
                return node.item

        return None

    def sorted_view(self, criterion, reverse=False):
        """Copia ordenada por peso, valor o nombre. No altera el orden real."""
        return sort(list(self._items), _key_for(criterion), reverse)

    def _record(self, change):
        if self._history is not None:
            self._history.record(change)

    def _assign(self, target, attribute, value):
        if self._history is None:
            setattr(target, attribute, value)
        else:
            self._history.assign(target, attribute, value)

    def _unlink(self, node):
        if self._cursor is node:
            following = self._items.next_of(node)
            self._cursor = following if following is not None else self._items.previous_of(node)

        self._items.remove(node)

        if is_rewind_scroll(node.item):
            self._scrolls -= 1

    def _relink(self, node, previous, following):
        """Reinserta junto a sus vecinos de antes.

        Si el vecino anterior ya no esta, porque era un pergamino que salio sin
        anotarse, se usa el siguiente; si tampoco esta, va al final.
        """
        if previous is None:
            self._items.push_front(node)
        elif previous.linked:
            self._items.insert_after(previous, node)
        elif following is not None and following.linked:
            self._items.insert_before(following, node)
        else:
            self._items.append(node)

        if is_rewind_scroll(node.item):
            self._scrolls += 1

        if self._cursor is None:
            self._cursor = node
