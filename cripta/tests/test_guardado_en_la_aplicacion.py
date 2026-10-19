"""
Guardar y cargar desde la aplicacion, con los datos offline (§4.10).

La prueba de fondo es test_guardar_y_cargar_da_lo_mismo_que_seguir_jugando:
se juega la misma partida de dos formas, de corrido y cortandola con un
guardado, y las dos tienen que terminar en el mismo estado. Si el archivo se
dejara algo afuera, los dos caminos se separarian.

Se usa el mismo andamio que tests/test_application.py: los datos de
datos_offline, una entrada de lineas fijas y una vista que escribe a un
StringIO.
"""
import io
import os
import tempfile
import unittest

from adapters.fuente_offline import FuenteOffline
from controller.application import InUseIds, play
from repository.repositorio_cripta import RepositorioCripta
from view.console_view import ConsoleView


OFFLINE_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_offline")

SEMILLA = 7
CRIPTA = "cripta-01"


class ScriptedInput:
    """Entrega lineas fijas como si las escribiera el jugador."""

    def __init__(self, lines):
        self.lines = list(lines)

    def __call__(self, prompt):
        if not self.lines:
            raise EOFError

        return self.lines.pop(0)


class PruebasGuardadoEnLaAplicacion(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.logs = os.path.join(self.directory.name, "partidas")
        self.guardado = os.path.join(self.directory.name, "partida.cripta")
        self._cuantas_caches = 0

    def tearDown(self):
        self.directory.cleanup()

    def repositorio(self):
        """Una cache distinta por partida, para que no se pisen."""
        self._cuantas_caches += 1
        in_use = InUseIds()
        repository = RepositorioCripta(
            FuenteOffline(OFFLINE_DATA),
            os.path.join(self.directory.name, f"cache{self._cuantas_caches}"),
            consultar_ids_en_uso=in_use,
        )
        in_use.repository = repository
        return repository, in_use

    def jugar(self, lineas, load_path=None, semilla=SEMILLA):
        repository, in_use = self.repositorio()
        salida = io.StringIO()
        view = ConsoleView(output=salida, read_line=ScriptedInput(lineas))
        game = play(
            repository,
            view,
            semilla,
            CRIPTA,
            None,
            in_use,
            self.logs,
            load_path=load_path,
        )
        return game, salida.getvalue()

    def estado(self, game):
        return (
            game.state.clock,
            game.player.health,
            game.player.room_id,
            game.player_actions,
            game.enemies_defeated,
            game.result,
        )

    # ------------------------------------------------------------------
    # El comando guardar
    # ------------------------------------------------------------------

    def test_guardar_escribe_el_archivo_y_lo_dice(self):
        _, salida = self.jugar(["esperar", f"guardar {self.guardado}", "salir"])

        self.assertTrue(os.path.isfile(self.guardado))
        self.assertIn("Partida guardada", salida)
        self.assertIn("bytes", salida)

    def test_guardar_no_consume_tiempo_ni_cuenta_como_accion(self):
        sin_guardar, _ = self.jugar(["esperar", "esperar", "salir"])
        con_guardado, _ = self.jugar(
            ["esperar", f"guardar {self.guardado}", "esperar", "salir"]
        )

        self.assertEqual(self.estado(sin_guardar), self.estado(con_guardado))

    def test_guardar_sin_nombre_de_archivo_se_rechaza(self):
        _, salida = self.jugar(["guardar", "salir"])

        self.assertIn("nombre del archivo", salida)

    def test_guardar_crea_la_carpeta_que_falte(self):
        dentro = os.path.join(self.directory.name, "guardados", "partida.cripta")

        self.jugar(["esperar", f"guardar {dentro}", "salir"])

        self.assertTrue(os.path.isfile(dentro))

    def test_guardar_en_una_ruta_imposible_se_reporta_sin_caerse(self):
        """Debajo de un archivo que ya existe no se puede crear una carpeta."""
        self.jugar(["esperar", f"guardar {self.guardado}", "salir"])
        imposible = os.path.join(self.guardado, "no", "existe.cripta")

        game, salida = self.jugar(["esperar", f"guardar {imposible}", "salir"])

        self.assertIn("No se pudo guardar", salida)
        self.assertIsNotNone(game)

    # ------------------------------------------------------------------
    # El comando cargar, que no se atiende en medio de la partida
    # ------------------------------------------------------------------

    def test_cargar_en_medio_de_la_partida_explica_por_que_no(self):
        _, salida = self.jugar(["esperar", f"cargar {self.guardado}", "salir"])

        self.assertIn("--cargar", salida)
        self.assertIn("bitacora", salida.lower())

    def test_cargar_en_medio_de_la_partida_no_cambia_el_estado(self):
        sin_intentar, _ = self.jugar(["esperar", "esperar", "salir"])
        intentando, _ = self.jugar(
            ["esperar", f"cargar {self.guardado}", "esperar", "salir"]
        )

        self.assertEqual(self.estado(sin_intentar), self.estado(intentando))

    # ------------------------------------------------------------------
    # Cargar al arrancar
    # ------------------------------------------------------------------

    def test_cargar_al_arrancar_continua_la_partida_guardada(self):
        guardada, _ = self.jugar(
            ["esperar", "esperar", f"guardar {self.guardado}", "salir"]
        )

        cargada, salida = self.jugar(["salir"], load_path=self.guardado)

        self.assertIn("Partida cargada", salida)
        self.assertEqual(cargada.state.clock, guardada.state.clock)
        self.assertEqual(cargada.player_actions, guardada.player_actions)
        self.assertEqual(cargada.player.health, guardada.player.health)
        self.assertEqual(cargada.player.room_id, guardada.player.room_id)

    def test_la_semilla_sale_del_archivo_y_no_de_la_bandera(self):
        self.jugar(["esperar", f"guardar {self.guardado}", "salir"])

        cargada, _ = self.jugar(["salir"], load_path=self.guardado, semilla=999)

        self.assertEqual(cargada.state.seed, SEMILLA)

    def test_cargar_abre_una_bitacora_propia(self):
        """La bitacora de la sesion cargada no es la de la original."""
        self.jugar(["esperar", f"guardar {self.guardado}", "salir"])
        primeras = set(os.listdir(self.logs))

        self.jugar(["esperar", "salir"], load_path=self.guardado)
        todas = set(os.listdir(self.logs))

        self.assertEqual(len(todas - primeras), 1)

    # ------------------------------------------------------------------
    # La prueba de fondo
    # ------------------------------------------------------------------

    def test_guardar_y_cargar_da_lo_mismo_que_seguir_jugando(self):
        """Las mismas acciones, de corrido y cortadas por un guardado."""
        de_corrido, _ = self.jugar(
            ["esperar", "esperar", "mover N", "esperar", "salir"]
        )

        self.jugar(["esperar", "esperar", "mover N", f"guardar {self.guardado}", "salir"])
        continuada, _ = self.jugar(["esperar", "salir"], load_path=self.guardado)

        self.assertEqual(self.estado(de_corrido), self.estado(continuada))

    def test_la_partida_cargada_anota_para_el_retroceso(self):
        """El historial de una partida cargada empieza vacio pero anota.

        Es el punto fragil del cargado: el inventario sale del archivo sin
        historial y hay que volver a armarlo. Si quedara sin el, las acciones
        posteriores a cargar no se desharian y el pergamino fallaria en
        silencio. En cripta-01 el jugador empieza sin pergaminos, asi que aca
        se comprueba el historial; que el retroceso en si funcione despues de
        cargar lo fija tests/test_almacen_partida.py.
        """
        self.jugar(["esperar", f"guardar {self.guardado}", "salir"])

        recien_cargada, _ = self.jugar(["salir"], load_path=self.guardado)

        self.assertFalse(recien_cargada.history.can_undo())

        despues_de_actuar, _ = self.jugar(
            ["esperar", "salir"], load_path=self.guardado
        )

        self.assertTrue(despues_de_actuar.history.can_undo())


if __name__ == "__main__":
    unittest.main()
