import io
import unittest
from dataclasses import dataclass

from view.console_view import ConsoleView


@dataclass
class EnemyStub:
    actor_id: str
    name: str
    health: int
    max_health: int
    is_hunter: bool = False


@dataclass
class EffectStub:
    name: str
    ends_at: int | None


@dataclass
class StateStub:
    """Mismos campos que VisibleState en la rama del motor."""

    clock: int = 120
    result: str = "en_curso"
    player_name: str = "Heroe"
    health: int = 25
    max_health: int = 30
    attack: int = 9
    defense: int = 2
    speed: int = 100
    room_id: int = 2
    enemies: list = None
    effects: list = None
    torch_lit: bool = False
    messages: list = None

    def __post_init__(self):
        self.enemies = [] if self.enemies is None else self.enemies
        self.effects = [] if self.effects is None else self.effects
        self.messages = [] if self.messages is None else self.messages


def render(state):
    output = io.StringIO()
    ConsoleView(output=output).show_state(state)
    return output.getvalue()


class TestShowState(unittest.TestCase):

    def test_shows_clock_room_and_player_stats(self):
        text = render(StateStub())

        self.assertIn("Reloj 120", text)
        self.assertIn("Sala 2", text)
        self.assertIn("vida 25/30", text)
        self.assertIn("ataque 9", text)

    def test_each_enemy_is_identified_by_its_instance(self):
        enemies = [
            EnemyStub("e-201", "Rata gigante", 12, 12),
            EnemyStub("e-202", "Rata gigante", 5, 12),
        ]

        text = render(StateStub(enemies=enemies))

        self.assertIn("Rata gigante [e-201] vida 12/12", text)
        self.assertIn("Rata gigante [e-202] vida 5/12", text)

    def test_marks_the_hunter_apart_from_the_other_enemies(self):
        """FR-019 y SC-010: el jugador tiene que poder decir cual lo persigue.

        De un guardian puede alejarse y olvidarlo; de un cazador no, asi que
        la decision que le conviene es la opuesta.
        """
        enemies = [
            EnemyStub("e-201", "Sabueso oseo", 18, 18, is_hunter=True),
            EnemyStub("e-202", "Centinela", 20, 20),
        ]

        text = render(StateStub(enemies=enemies))
        lineas = [linea for linea in text.splitlines() if "vida" in linea]
        del_cazador = [linea for linea in lineas if "e-201" in linea][0]
        del_otro = [linea for linea in lineas if "e-202" in linea][0]

        self.assertIn("cazador", del_cazador)
        self.assertNotIn("cazador", del_otro)

    def test_the_hunter_still_shows_its_name_id_and_health(self):
        """Historia 6, escenario 3: se agrega la marca, no se quita nada."""
        enemies = [EnemyStub("e-201", "Sabueso oseo", 7, 18, is_hunter=True)]

        text = render(StateStub(enemies=enemies))

        self.assertIn("Sabueso oseo", text)
        self.assertIn("[e-201]", text)
        self.assertIn("vida 7/18", text)

    def test_without_hunters_the_list_looks_like_before(self):
        """Historia 6, escenario 2: no se agrega ruido donde no hay cazador."""
        enemies = [EnemyStub("e-202", "Centinela", 20, 20)]

        text = render(StateStub(enemies=enemies))

        self.assertIn("Centinela [e-202] vida 20/20", text)
        self.assertNotIn("cazador", text)

    def test_without_enemies(self):
        self.assertIn("No hay enemigos", render(StateStub()))

    def test_shows_active_effects(self):
        effects = [EffectStub("veneno", 400), EffectStub("antorcha", 2100)]

        text = render(StateStub(effects=effects))

        self.assertIn("veneno hasta 400", text)
        self.assertIn("antorcha hasta 2100", text)

    def test_shows_the_messages(self):
        text = render(StateStub(messages=["Esperas.", "La rata te ataca."]))

        self.assertIn("Esperas.", text)
        self.assertIn("La rata te ataca.", text)


class TestInput(unittest.TestCase):

    def test_reads_the_line_written_by_the_player(self):
        view = ConsoleView(output=io.StringIO(), read_line=lambda prompt: "mover N")

        self.assertEqual(view.read_command(), "mover N")

    def test_closed_input_returns_none(self):
        def closed(prompt):
            raise EOFError

        view = ConsoleView(output=io.StringIO(), read_line=closed)

        self.assertIsNone(view.read_command())

    def test_help_lists_every_command(self):
        output = io.StringIO()
        ConsoleView(output=output).show_help()

        for name in ("mover", "abrir", "atacar", "esperar", "recoger", "soltar",
                     "usar", "equipar", "sig", "retroceder", "guardar",
                     "cargar", "salir"):
            self.assertIn(name, output.getvalue())


if __name__ == "__main__":
    unittest.main()
