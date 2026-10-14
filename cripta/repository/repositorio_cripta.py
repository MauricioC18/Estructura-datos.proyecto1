"""
RepositorioCripta: el único punto de entrada del bloque 2 para el controlador.

Problema que resuelve
    El controlador (bloque 4) necesita datos de la cripta sin conocer HTTP,
    archivos, caché ni lotes (§6). Este repositorio une todo lo del bloque 2:
    la fuente (red u offline), el GestorCatalogo, el GestorContenido y las
    copias en disco, y ofrece pocas operaciones con nombres del juego.

Uso típico, desde el controlador
    repositorio = RepositorioCripta(fuente, "cache_cripta", capacidad_cache, consultar_ids_en_uso)

    repositorio.empezar_conteo_de_partida()          # la lista de criptas ya cuenta (§5.1)
    criptas = repositorio.listar_criptas()           # para que el jugador elija
    datos = repositorio.iniciar_partida(id_elegido)  # deja lista la sala inicial

    # Antes de confirmar que el jugador entra a una sala (§2.5):
    entrada = repositorio.preparar_entrada_a_sala(id_sala)
    # Después de cada acción del jugador:
    repositorio.despues_de_accion(id_sala_actual)
    # Cuando un enemigo muere y suelta objetos:
    repositorio.asegurar_fichas(ids_de_objetos_soltados)
    # Al terminar la partida (§5.1):
    reporte = repositorio.reporte_de_red()

Arranque en frío y en caliente (cripta-01)
    En frío: lista + datos generales + versión del catálogo + página del
    esqueleto + contenido + 2 lotes de catálogo = 7 de 9 solicitudes.
    En caliente (misma versión de cripta y catálogo ya guardadas): lista +
    datos generales + versión del catálogo = 3 solicitudes.

Precarga de fichas
    Después de cada acción, además de la precarga de contenido por BFS, se
    aseguran las fichas de la sala actual y de sus vecinas directas, si
    quedan más solicitudes que la reserva. Así entrar a una sala vecina no
    hace esperar por el catálogo.

Reproducción (--replay, §4.11)
    iniciar_partida recibe opcionalmente las versiones con que se grabó el
    log. Si la fuente tiene otras, lanza VersionesIncompatibles antes de
    cargar nada: no se reproduce en silencio contra datos distintos. Para
    reproducir un log viejo hay que usar --offline con una copia de datos
    de esas versiones (supuesto del grupo).

Persistencia
    Las fichas se guardan en <carpeta_cache>/catalogo (AlmacenFichas) y el
    esqueleto y el contenido en <carpeta_cache>/criptas (AlmacenCripta). Si
    el disco falla, el juego sigue y el reporte lo avisa.
"""
from pathlib import Path

from adapters.almacen_cripta import AlmacenCripta
from adapters.almacen_fichas import AlmacenFichas, ErrorAlmacenDisco
from adapters.fuente_datos import PresupuestoAgotado
from structures.cache_catalogo import CAPACIDAD_POR_DEFECTO, CacheCatalogo
from structures.grafo_salas import construir_grafo_desde_esqueleto
from structures.tabla_hash import TablaHash
from repository.gestor_catalogo import FichaNoDisponible, GestorCatalogo
from repository.gestor_contenido import (
    RESERVA_DE_SOLICITUDES,
    GestorContenido,
    descargar_salas_del_esqueleto,
    tipos_de_la_sala,
)


class VersionesIncompatibles(Exception):
    """La fuente no tiene las versiones con que se grabó un log (§4.11)."""


class DatosDePartida:
    """Datos generales de la cripta elegida (vienen del API, nunca quemados)."""

    def __init__(self, generales, version_catalogo):
        self.id_cripta = generales["id"]
        self.version_cripta = generales["version"]
        self.version_catalogo = version_catalogo
        self.salas_total = generales["salas_total"]
        self.sala_inicial = generales["sala_inicial"]
        self.sala_salida = generales["sala_salida"]
        self.llave_salida = generales["llave_salida"]
        self.presupuesto_solicitudes = generales["presupuesto_solicitudes"]
        self.inventario_max = generales["inventario_max"]
        self.jugador = generales["jugador"]  # {"vida_max", "ataque", "defensa", "velocidad"}


class ReporteDeRed:
    """Lo que §5.1 pide reportar al final, más detalles útiles."""

    def __init__(self):
        self.origen_de_los_datos = ""
        self.solicitudes_realizadas = 0
        self.presupuesto_solicitudes = None
        self.aciertos_de_cache = 0
        self.fallos_de_cache = 0
        self.aciertos_en_memoria = 0
        self.recuperaciones_desde_disco = 0
        self.fichas_descargadas = 0
        self.lotes_de_catalogo = 0
        self.lotes_de_contenido = 0
        self.salas_descargadas = 0
        self.salas_recuperadas_de_disco = 0
        self.esperas_en_la_puerta = 0
        self.desalojos_de_memoria = 0
        self.avisos = []

    def lineas_de_texto(self):
        """El reporte listo para mostrar, una línea por elemento."""
        presupuesto = "sin definir" if self.presupuesto_solicitudes is None else self.presupuesto_solicitudes
        lineas = [
            f"Origen de los datos: {self.origen_de_los_datos}",
            f"Solicitudes realizadas: {self.solicitudes_realizadas} de {presupuesto}",
            f"Aciertos de caché: {self.aciertos_de_cache} "
            f"({self.aciertos_en_memoria} en memoria, {self.recuperaciones_desde_disco} desde disco)",
            f"Fallos de caché: {self.fallos_de_cache}",
            f"Catálogo: fichas descargadas {self.fichas_descargadas} (lotes: {self.lotes_de_catalogo}), "
            f"liberadas de memoria {self.desalojos_de_memoria}",
            f"Contenido: salas descargadas {self.salas_descargadas} (lotes: {self.lotes_de_contenido}), "
            f"recuperadas de disco {self.salas_recuperadas_de_disco}",
            f"Esperas en la puerta: {self.esperas_en_la_puerta}",
        ]
        for aviso in self.avisos:
            lineas.append(f"Aviso: {aviso}")
        return lineas


class RepositorioCripta:
    """Punto de entrada del bloque 2 para el controlador."""

    def __init__(self, fuente, carpeta_cache, capacidad_cache=CAPACIDAD_POR_DEFECTO,
                 consultar_ids_en_uso=None):
        """
        fuente: FuenteHttp o FuenteOffline (según --offline).
        carpeta_cache: dónde se guardan las copias en disco.
        capacidad_cache: el valor de --cache-size.
        consultar_ids_en_uso: función sin argumentos que devuelve una TablaHash
            con los ids de catálogo en uso (§4.4): tipos de enemigos vivos,
            objetos del inventario, objetos y trampas de la sala actual.
            La entrega el controlador, armada con datos del modelo.
        """
        self._fuente = fuente
        carpeta_cache = Path(carpeta_cache)
        self._gestor_catalogo = GestorCatalogo(
            fuente,
            AlmacenFichas(carpeta_cache / "catalogo"),
            CacheCatalogo(capacidad_cache, consultar_ids_en_uso),
        )
        self._almacen_cripta = AlmacenCripta(carpeta_cache / "criptas")
        self._datos_de_partida = None
        self._gestor_contenido = None
        self._grafo = None
        self._salas_por_id = None
        self._avisos = []

    # ------------------------------------------------------------------
    # Inicio de la partida
    # ------------------------------------------------------------------

    def empezar_conteo_de_partida(self):
        """Reinicia la cuenta de solicitudes. Se llama antes de listar las
        criptas, porque la lista también cuenta en el presupuesto (§5.1)."""
        self._fuente.reiniciar_conteo()
        self._avisos = []

    def listar_criptas(self):
        """Lista de criptas publicadas: [{"id", "nombre", "salas", "dificultad"}, ...]."""
        return self._fuente.listar_criptas()["criptas"]

    def iniciar_partida(self, id_cripta, versiones_requeridas=None):
        """Carga lo necesario para empezar y deja lista la sala inicial.

        versiones_requeridas: (version_cripta, version_catalogo) de un log
        de --replay. Si la fuente tiene otras, lanza VersionesIncompatibles.

        Puede lanzar PresupuestoAgotado, ErrorFuenteDatos, FichaNoDisponible
        o ContenidoNoDisponible.
        """
        generales = self._fuente.datos_generales(id_cripta)
        self._fuente.establecer_presupuesto(generales["presupuesto_solicitudes"])
        version_catalogo = self._fuente.version_catalogo()["version"]

        if versiones_requeridas is not None:
            _comprobar_versiones(id_cripta, generales["version"], version_catalogo,
                                 versiones_requeridas)

        self._gestor_catalogo.iniciar(version_catalogo)
        self._datos_de_partida = DatosDePartida(generales, version_catalogo)

        copia_vigente = self._preparar_copia_en_disco(generales)
        salas = self._leer_esqueleto_guardado(id_cripta) if copia_vigente else None
        if salas is None:
            salas = descargar_salas_del_esqueleto(self._fuente, id_cripta, generales["paginas"])
            self._intentar_en_disco(lambda: self._almacen_cripta.guardar_esqueleto(id_cripta, salas))

        self._grafo = construir_grafo_desde_esqueleto(salas)
        self._salas_por_id = TablaHash()
        for sala in salas:
            self._salas_por_id.insertar(sala["id"], sala)

        self._gestor_contenido = GestorContenido(
            self._fuente, id_cripta, self._grafo, self._gestor_catalogo,
            guardar_contenido=lambda entradas: self._intentar_en_disco(
                lambda: self._almacen_cripta.guardar_contenido(id_cripta, entradas)),
        )
        if copia_vigente:
            guardadas = self._almacen_cripta.leer_contenido_guardado(id_cripta, self._grafo.ids_de_salas())
            self._gestor_contenido.incorporar_contenido_guardado(guardadas)

        # La sala inicial debe estar lista antes de la primera acción (§2.4).
        sala_inicial = self._datos_de_partida.sala_inicial
        self._gestor_contenido.precargar_alrededor_de(sala_inicial)
        self.preparar_entrada_a_sala(sala_inicial)
        self._precargar_fichas_cercanas(sala_inicial)
        return self._datos_de_partida

    # ------------------------------------------------------------------
    # Durante la partida
    # ------------------------------------------------------------------

    def preparar_entrada_a_sala(self, id_sala):
        """Garantiza el contenido de la sala y las fichas de todo lo que hay
        en ella. Se llama ANTES de confirmar que el jugador entra (§2.5).
        Devuelve la entrada de contenido (el JSON del API).

        Si lanza PresupuestoAgotado, el movimiento debe rechazarse sin
        consumir tiempo (supuesto del grupo)."""
        self._exigir_partida()
        self._gestor_contenido.asegurar_contenido(id_sala)
        entrada = self._gestor_contenido.contenido_de_sala(id_sala)
        self._gestor_catalogo.asegurar_fichas(tipos_de_la_sala(entrada))
        return entrada

    def despues_de_accion(self, id_sala_actual):
        """Precarga contenido y fichas alrededor del jugador. Se llama
        después de cada acción del jugador. Nunca lanza PresupuestoAgotado:
        si no hay presupuesto, simplemente no precarga."""
        self._exigir_partida()
        try:
            self._gestor_contenido.precargar_alrededor_de(id_sala_actual)
        except PresupuestoAgotado:
            return
        self._precargar_fichas_cercanas(id_sala_actual)

    def asegurar_fichas(self, ids):
        """Para objetos que aparecen durante la partida (lo que suelta un enemigo)."""
        self._exigir_partida()
        self._gestor_catalogo.asegurar_fichas(ids)

    def obtener_ficha(self, id_ficha):
        """La ficha del catálogo (el JSON del API). Nunca usa la red."""
        self._exigir_partida()
        return self._gestor_catalogo.obtener_ficha(id_ficha)

    def contenido_de_sala(self, id_sala):
        """La entrada de contenido de una sala ya preparada."""
        self._exigir_partida()
        return self._gestor_contenido.contenido_de_sala(id_sala)

    def sala_del_esqueleto(self, id_sala):
        """La sala del esqueleto con sus salidas (el JSON del API)."""
        self._exigir_partida()
        sala = self._salas_por_id.obtener(id_sala)
        if sala is None:
            raise ValueError(f"La sala {id_sala} no está en el esqueleto")
        return sala

    def ids_de_salas(self):
        self._exigir_partida()
        return self._grafo.ids_de_salas()

    def vecinos_de_sala(self, id_sala):
        """Salas a las que llevan las salidas de id_sala, en orden N, S, E, O."""
        self._exigir_partida()
        return self._grafo.vecinos(id_sala)

    def datos_de_partida(self):
        self._exigir_partida()
        return self._datos_de_partida

    def versiones_de_la_partida(self):
        """(id_cripta, version_cripta, version_catalogo) para el encabezado
        del log de --replay (§4.11)."""
        self._exigir_partida()
        datos = self._datos_de_partida
        return datos.id_cripta, datos.version_cripta, datos.version_catalogo

    # ------------------------------------------------------------------
    # Reporte final (§5.1)
    # ------------------------------------------------------------------

    def reporte_de_red(self):
        reporte = ReporteDeRed()
        reporte.origen_de_los_datos = self._fuente.descripcion_del_origen()
        reporte.solicitudes_realizadas = self._fuente.solicitudes_realizadas()
        reporte.presupuesto_solicitudes = self._fuente.presupuesto()

        catalogo = self._gestor_catalogo.estadisticas()
        reporte.aciertos_de_cache = catalogo.aciertos_de_cache()
        reporte.fallos_de_cache = catalogo.fallos_de_cache()
        reporte.aciertos_en_memoria = catalogo.aciertos_en_memoria
        reporte.recuperaciones_desde_disco = catalogo.recuperaciones_desde_disco
        reporte.fichas_descargadas = catalogo.fichas_descargadas
        reporte.lotes_de_catalogo = catalogo.lotes_de_catalogo_descargados
        reporte.desalojos_de_memoria = catalogo.desalojos_de_memoria
        reporte.avisos = list(catalogo.avisos) + list(self._avisos)

        if self._gestor_contenido is not None:
            contenido = self._gestor_contenido.estadisticas()
            reporte.lotes_de_contenido = contenido.lotes_de_contenido
            reporte.salas_descargadas = contenido.salas_descargadas
            reporte.salas_recuperadas_de_disco = contenido.salas_recuperadas_de_disco
            reporte.esperas_en_la_puerta = contenido.esperas_en_la_puerta
        return reporte

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _precargar_fichas_cercanas(self, id_sala):
        """Asegura las fichas de la sala y de sus vecinas que ya tienen
        contenido, si quedan más solicitudes que la reserva."""
        restantes = self._fuente.solicitudes_restantes()
        if restantes is not None and restantes <= RESERVA_DE_SOLICITUDES:
            return
        tipos = []
        for sala in [id_sala] + self._grafo.vecinos(id_sala):
            if self._gestor_contenido.tiene_contenido(sala):
                tipos.extend(tipos_de_la_sala(self._gestor_contenido.contenido_de_sala(sala)))
        try:
            self._gestor_catalogo.asegurar_fichas(tipos)
        except (PresupuestoAgotado, FichaNoDisponible):
            pass  # es solo precarga: si hace falta de verdad, se reintentará al entrar

    def _preparar_copia_en_disco(self, generales):
        try:
            return self._almacen_cripta.preparar(generales)
        except ErrorAlmacenDisco as error:
            self._avisos.append(f"Se juega sin copia en disco de la cripta: {error}")
            return False

    def _leer_esqueleto_guardado(self, id_cripta):
        return self._almacen_cripta.leer_esqueleto(id_cripta)

    def _intentar_en_disco(self, operacion):
        try:
            operacion()
        except ErrorAlmacenDisco as error:
            self._avisos.append(str(error))

    def _exigir_partida(self):
        if self._datos_de_partida is None or self._gestor_contenido is None:
            raise RuntimeError("Primero hay que llamar a iniciar_partida()")


def _comprobar_versiones(id_cripta, version_cripta, version_catalogo, versiones_requeridas):
    version_cripta_log, version_catalogo_log = versiones_requeridas
    if version_cripta != version_cripta_log or version_catalogo != version_catalogo_log:
        raise VersionesIncompatibles(
            f"El log se grabó con {id_cripta} versión {version_cripta_log} y catálogo "
            f"{version_catalogo_log}, pero la fuente tiene versión {version_cripta} y catálogo "
            f"{version_catalogo}. No se puede garantizar una reproducción fiel; use --offline "
            f"con una copia de los datos de esas versiones."
        )
