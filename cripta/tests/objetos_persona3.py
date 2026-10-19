"""Objetos del modelo para las pruebas de inventario, historial y rastro."""
from model.item import Item
from model.player import Player


def make_item(name, item_class=Item.POTION, weight=1, value=1, attack_bonus=0, defense_bonus=0):
    return Item(
        instance_id=f"o-{name}",
        type_id=f"itm_{name}",
        name=name,
        item_class=item_class,
        weight=weight,
        value=value,
        attack_bonus=attack_bonus,
        defense_bonus=defense_bonus,
    )


def make_weapon(name, attack_bonus=3):
    return make_item(name, Item.WEAPON, attack_bonus=attack_bonus)


def make_armor(name, defense_bonus=2):
    return make_item(name, Item.ARMOR, defense_bonus=defense_bonus)


def make_scroll(name="pergamino"):
    return make_item(name, Item.REWIND_SCROLL)


def make_player(room_id=1):
    return Player("p-1", "Heroe", 30, 6, 2, 100, room_id)


def names(items):
    return [item.name for item in items]
