"""
Esqueleto y contenido de criptas guardados en disco (§4.4).

Problema que resuelve
    §4.4 permite persistir el esqueleto y el contenido de una cripta
    mientras coincida su versión. Con eso, una segunda partida en la misma
    cripta no vuelve a descargar páginas ni contenido: solo pide los datos
    generales (que traen la versión) y la versión del catálogo.

Archivos, dentro de la carpeta del almacén
    <id_cripta>/general.json            datos generales (incluyen la versión)
    <id_cripta>/esqueleto.json          {"salas": [...]} con todas las páginas juntas
    <id_cripta>/contenido/sala_<n>.json una entrada de contenido por sala

    El contenido va un archivo por sala porque se descarga de a pocas salas
    a la vez, y así cada lote solo escribe lo nuevo.

Validación por versión
    preparar(datos_generales) compara la versión guardada con la vigente.
    Si no coinciden, borra la copia de esa cripta y guarda los datos nuevos.
    Nada de otra versión se usa nunca.

Seguridad ante fallos
    Cada archivo se escribe primero en un temporal y luego se reemplaza de
    una sola vez (os.replace), así nunca queda un archivo a medio escribir.
    Los problemas de disco se reportan con ErrorAlmacenDisco; quien usa el
    almacén puede seguir jugando sin persistencia.
"""
import json
import os
import shutil
from pathlib import Path

from adapters.almacen_fichas import ErrorAlmacenDisco
from adapters.fuente_offline import nombre_de_archivo_seguro


class AlmacenCripta:
    """Copia local del esqueleto y del contenido de las criptas."""

    def __init__(self, carpeta):
        self._carpeta = Path(carpeta)

    # ------------------------------------------------------------------
    # Versión
    # ------------------------------------------------------------------

    def preparar(self, datos_generales):
        """Deja lista la copia de la cripta para la versión vigente.
        Devuelve True si ya había una copia de esa misma versión."""
        id_cripta = datos_generales["id"]
        guardados = self._leer_json(self._ruta_general(id_cripta))
        if isinstance(guardados, dict) and guardados.get("version") == datos_generales["version"]:
            return True
        try:
            carpeta_cripta = self._carpeta_de_cripta(id_cripta)
            if carpeta_cripta.exists():
                shutil.rmtree(carpeta_cripta)  # copia de otra versión: no sirve
        except OSError as error:
            raise ErrorAlmacenDisco(f"borrar la copia vieja de {id_cripta}", str(error)) from error
        self._escribir_json(self._ruta_general(id_cripta), datos_generales,
                            f"guardar los datos generales de {id_cripta}")
        return False

    # ------------------------------------------------------------------
    # Esqueleto
    # ------------------------------------------------------------------

    def leer_esqueleto(self, id_cripta):
        """Las salas guardadas, o None si no hay esqueleto completo."""
        datos = self._leer_json(self._ruta_esqueleto(id_cripta))
        if isinstance(datos, dict) and isinstance(datos.get("salas"), list):
            return datos["salas"]
        return None

    def guardar_esqueleto(self, id_cripta, salas):
        self._escribir_json(self._ruta_esqueleto(id_cripta), {"salas": salas},
                            f"guardar el esqueleto de {id_cripta}")

    # ------------------------------------------------------------------
    # Contenido
    # ------------------------------------------------------------------

    def leer_contenido_guardado(self, id_cripta, ids_salas):
        """Las entradas guardadas de esas salas, en el mismo orden de
        ids_salas (así el resultado no depende del orden en que el sistema
        operativo lista los archivos). Las salas sin archivo, o con un
        archivo dañado, se omiten: simplemente se volverán a pedir."""
        carpeta = self._carpeta_de_cripta(id_cripta) / "contenido"
        entradas = []
        for id_sala in ids_salas:
            entrada = self._leer_json(carpeta / f"sala_{int(id_sala)}.json")
            if isinstance(entrada, dict) and entrada.get("sala") == id_sala:
                entradas.append(entrada)
        return entradas

    def guardar_contenido(self, id_cripta, entradas):
        for entrada in entradas:
            ruta = self._carpeta_de_cripta(id_cripta) / "contenido" / f"sala_{int(entrada['sala'])}.json"
            self._escribir_json(ruta, entrada, f"guardar el contenido de {id_cripta}")

    # ------------------------------------------------------------------
    # Archivos
    # ------------------------------------------------------------------

    def _carpeta_de_cripta(self, id_cripta):
        return self._carpeta / nombre_de_archivo_seguro(id_cripta)

    def _ruta_general(self, id_cripta):
        return self._carpeta_de_cripta(id_cripta) / "general.json"

    def _ruta_esqueleto(self, id_cripta):
        return self._carpeta_de_cripta(id_cripta) / "esqueleto.json"

    @staticmethod
    def _leer_json(ruta):
        """El contenido del archivo, o None si no existe o no se puede leer."""
        try:
            with open(ruta, encoding="utf-8") as archivo:
                return json.load(archivo)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _escribir_json(ruta, datos, operacion):
        ruta_temporal = ruta.with_name(ruta.name + ".tmp")
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta_temporal, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False)
            os.replace(ruta_temporal, ruta)
        except OSError as error:
            raise ErrorAlmacenDisco(operacion, str(error)) from error
