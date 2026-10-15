from dataclasses import dataclass


@dataclass
class Item:
    """Instancia de un objeto: en el suelo de una sala, en el inventario o equipado.

    Varias instancias pueden ser del mismo tipo (§2.7). Cada una tiene su propio
    instance_id; type_id es el id de su ficha en el catalogo.

    La clase es plana, con campos que valen 0 o None cuando no aplican a la
    clase del objeto, por la misma razon que Event: el guardado binario de
    §4.10 la puede empaquetar con struct sin inventar un formato por clase.

    attack_bonus y defense_bonus tienen esos nombres porque Player los usa por
    duck typing al calcular el ataque y la defensa efectivos (§2.7).

    La crea el traductor del bloque 2 (repository/traductor.py) a partir de la
    ficha del catalogo.
    """

    WEAPON = "arma"
    ARMOR = "armadura"
    POTION = "pocion"
    ANTIDOTE = "antidoto"
    KEY = "llave"
    TORCH = "antorcha"
    REWIND_SCROLL = "pergamino_retroceso"

    instance_id: str
    type_id: str
    name: str
    item_class: str
    weight: int
    value: int
    attack_bonus: int = 0
    defense_bonus: int = 0
    heal: int = 0
    speed_modifier: int = 0
    duration: int = 0
    opens: str | int | None = None
