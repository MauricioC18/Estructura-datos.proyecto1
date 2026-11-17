"""El resumen de «historia» informa el mapa conocido de ese instante (specs/005-niebla-ir-a, FR-016).

Usa la partida que arma la aplicación con los datos offline (la primera
cripta que se lista, sin depender de su id ni de su tamaño) y la consulta que
atiende el comando. Cada prueba cita en su docstring los requisitos que
comprueba.
"""
import os
import tempfile
import unittest

from adapters.fuente_offline import FuenteOffline
from controller.application import InUseIds, _consultar_historia, build_game
from controller.commands import MOVE, Command
from controller.game_controller import GameController
from model.consulta_historia import MAPA_CONOCIDO_NO_DISPONIBLE
from repository.repositorio_cripta import RepositorioCripta


OFFLINE_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_offline")


class TestHistoriaConMapaConocido(unittest.TestCase):

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        in_use = InUseIds()
        self.repository = RepositorioCripta(
            FuenteOffline(OFFLINE_DATA),
            os.path.join(self.directorio.name, "cache"),
            consultar_ids_en_uso=in_use,
        )
        in_use.repository = self.repository
        self.repository.iniciar_partida(self.repository.listar_criptas()[0]["id"])
        self.game = build_game(self.repository, 5, in_use=in_use, copias_cada=1)
        self.controller = GameController(self.game, repository=self.repository)

    def tearDown(self):
        self.directorio.cleanup()

    def mover_a_una_vecina(self):
        for salida in self.game.room_map.room(self.game.player.room_id).exits():
            if salida.door.is_open:
                self.assertTrue(self.controller.execute(Command(MOVE, salida.direction)).accepted)
                return salida.destination
        self.skipTest("la sala inicial no tiene ninguna salida abierta")

    def test_cada_instante_trae_lo_que_el_jugador_sabia_entonces(self):
        """FR-016: al principio solo la sala inicial estaba explorada; después
        de moverse, el resumen del instante actual incluye la vecina, y el del
        principio sigue sin incluirla."""
        inicio = self.game.player.room_id
        vecina = self.mover_a_una_vecina()
        if self.game.is_over:
            self.skipTest("la partida terminó al entrar a la sala vecina")

        al_principio = _consultar_historia(self.game, 0)
        ahora = _consultar_historia(self.game, self.game.state.clock)

        self.assertNotEqual(al_principio.mapa_conocido, MAPA_CONOCIDO_NO_DISPONIBLE)
        self.assertEqual(al_principio.mapa_conocido, (inicio,))
        self.assertIn(vecina, ahora.mapa_conocido)
        self.assertEqual(ahora.mapa_conocido, tuple(self.game.known_map.salas_exploradas()))

    def test_la_consulta_no_toca_el_mapa_vivo(self):
        """FR-016, FR-019: consultar un instante pasado no cambia el
        conocimiento de la partida en curso."""
        self.mover_a_una_vecina()
        antes = self.game.known_map.exportar()
        version = self.game.known_map.version

        _consultar_historia(self.game, 0)
        _consultar_historia(self.game, "#1")

        self.assertEqual(self.game.known_map.exportar(), antes)
        self.assertEqual(self.game.known_map.version, version)


if __name__ == "__main__":
    unittest.main()
