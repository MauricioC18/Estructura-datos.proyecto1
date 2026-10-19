"""Tabla de puntajes local (§2.12).

Cada partida terminada agrega una linea a un archivo de texto: nombre del
jugador, id y version de la cripta, resultado, acciones del jugador, enemigos
derrotados y tiempo final del reloj virtual. Agregar no reescribe el archivo.

El archivo guarda las partidas en el orden en que se jugaron. El ranking se
calcula al mostrarlo con structures.sorting.sort, que es uno de los contextos
de ordenamiento de §4.9; no se usa sorted() ni list.sort().

Orden del ranking: primero las victorias; entre ellas, menor reloj final,
despues menos acciones y despues mas enemigos derrotados. Las derrotas van
despues con el mismo criterio. El ordenamiento es estable, asi que dos
partidas empatadas quedan en el orden en que se jugaron.
"""
import os
from dataclasses import dataclass

from structures.sorting import sort


FORMAT_VERSION = 1
TITLE = f"# CRIPTA puntajes formato={FORMAT_VERSION}"
SEPARATOR = "\t"
DEFAULT_PATH = "puntajes.txt"

VICTORY = "victoria"


class ScoreboardError(ValueError):
    """El archivo de puntajes no tiene el formato que este programa lee."""


@dataclass
class ScoreEntry:
    player_name: str
    crypt_id: str
    crypt_version: str
    result: str
    player_actions: int
    enemies_defeated: int
    final_clock: int

    def to_line(self):
        fields = (
            _clean(self.player_name),
            _clean(self.crypt_id),
            _clean(self.crypt_version),
            _clean(self.result),
            str(self.player_actions),
            str(self.enemies_defeated),
            str(self.final_clock),
        )
        return SEPARATOR.join(fields)

    @classmethod
    def from_line(cls, text, line_number):
        fields = text.split(SEPARATOR)

        if len(fields) != 7:
            raise ScoreboardError(
                f"Linea {line_number}: se esperaban 7 campos y hay {len(fields)}."
            )

        try:
            return cls(
                fields[0], fields[1], fields[2], fields[3],
                int(fields[4]), int(fields[5]), int(fields[6]),
            )
        except ValueError as error:
            raise ScoreboardError(f"Linea {line_number}: {error}") from error


def ranking_key(entry):
    """Menor clave, mejor puesto."""
    return (
        0 if entry.result == VICTORY else 1,
        entry.final_clock,
        entry.player_actions,
        -entry.enemies_defeated,
    )


class Scoreboard:

    def __init__(self, path=DEFAULT_PATH):
        self.path = path

    def add(self, entry):
        """Agrega una partida al final del archivo; lo crea si no existe."""
        is_new = not os.path.exists(self.path) or os.path.getsize(self.path) == 0

        with open(self.path, "a", encoding="utf-8", newline="\n") as file:
            if is_new:
                file.write(TITLE + "\n")
            file.write(entry.to_line() + "\n")

    def entries(self):
        """Las partidas en el orden en que se jugaron."""
        if not os.path.exists(self.path):
            return []

        with open(self.path, encoding="utf-8") as file:
            lines = file.read().splitlines()

        if not lines:
            return []

        if lines[0].strip() != TITLE:
            raise ScoreboardError(
                f"'{self.path}' no es una tabla de puntajes de formato {FORMAT_VERSION}."
            )

        result = []
        for index in range(1, len(lines)):
            if lines[index].strip():
                result.append(ScoreEntry.from_line(lines[index], index + 1))

        return result

    def ranking(self, crypt_id=None, limit=None):
        """Las mejores partidas, de una cripta o de todas."""
        entries = self.entries()

        if crypt_id is not None:
            entries = [entry for entry in entries if entry.crypt_id == crypt_id]

        ordered = sort(entries, ranking_key)

        return ordered if limit is None else ordered[:limit]


def _clean(text):
    """Un nombre con tabulador o salto de linea romperia el formato."""
    return " ".join(str(text).split()) or "-"
