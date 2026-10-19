"""
Almacén de fichas del catálogo en disco (problema 4.4, decisión D6).

Problema que resuelve
    §4.4 exige que la caché sobreviva al cierre del programa, que una ficha
    liberada de memoria se recupere con una lectura de disco (no con una
    solicitud de red) y que la versión del catálogo valide lo guardado sin
    volver a descargarlo todo.

Cómo funciona
    Se usan dos archivos dentro de la carpeta del almacén:

    fichas.datos   Las fichas, una detrás de otra, cada una como JSON en
                   UTF-8. Solo se agregan datos al final.
    fichas.indice  Archivo binario (módulo struct) con:
                     - un encabezado: firma "CRIPTAFI", versión del formato
                       y versión del catálogo;
                     - una entrada por ficha, ORDENADAS POR ID: el id, la
                       posición donde empieza la ficha en fichas.datos y
                       cuántos bytes mide.

    Al abrir, el índice completo se carga en memoria como tres listas
    paralelas ordenadas por id. Para leer una ficha:
      1. búsqueda binaria del id en el índice: O(log n);
      2. se salta a su posición en fichas.datos y se leen solo sus bytes,
         sin leer el resto del archivo.

    Para guardar fichas nuevas se agregan al final de fichas.datos, se
    insertan en su lugar del índice (búsqueda binaria + list.insert, así el
    índice nunca necesita reordenarse) y se reescribe fichas.indice.

Seguridad ante fallos
    fichas.indice se escribe primero en un archivo temporal y luego se
    reemplaza de una sola vez (os.replace). Si el programa se cierra a medio
    guardar, el índice viejo sigue intacto y nunca apunta a datos
    incompletos; lo peor que pasa es que algunas fichas se vuelvan a
    descargar.

Versiones
    - Si la versión del catálogo guardada no coincide con la vigente, todo
      se descarta y se empieza vacío (§4.4).
    - Si la firma o la versión del formato no coinciden, o el índice está
      dañado, también se descarta todo. motivo_del_ultimo_descarte() explica
      qué pasó, para mostrarlo en el reporte.

Por qué un índice ordenado y no una TablaHash
    La búsqueda en el índice no es lo que cuesta: leer la ficha del disco es
    mucho más lento (ver benchmark/bench_almacen_fichas.py). El índice ordenado
    se guarda en disco exactamente como se usa en memoria, así que se carga
    sin reconstruir nada, y si el catálogo creciera mucho permitiría buscar
    directamente en el archivo sin cargarlo.

Complejidad (n = fichas guardadas)
    contiene_ficha: O(log n)
    leer_ficha: O(log n) + leer los bytes de una sola ficha
    guardar_fichas (k fichas): O(k·n) por las inserciones en las listas,
        más reescribir el índice, O(n). Ocurre una vez por lote descargado.
    abrir: O(n), una sola vez al iniciar.
    espacio en memoria: O(n) para el índice; las fichas quedan en disco.

Límite conocido
    Si una ficha se vuelve a guardar, sus bytes viejos quedan sin uso en
    fichas.datos. El archivo se reinicia cuando cambia la versión del
    catálogo, que es cuando las fichas se vuelven a descargar.
"""
import json
import os
import struct
from pathlib import Path

FIRMA_DEL_INDICE = b"CRIPTAFI"
VERSION_DEL_FORMATO = 1

_NOMBRE_ARCHIVO_DATOS = "fichas.datos"
_NOMBRE_ARCHIVO_INDICE = "fichas.indice"

# "<" = little-endian, sin relleno. 8s = 8 bytes, H = entero de 2 bytes,
# I = entero de 4 bytes, Q = entero de 8 bytes.
_FORMATO_ENCABEZADO = "<8sH"
_FORMATO_LARGO_DE_TEXTO = "<H"
_FORMATO_CANTIDAD = "<I"
_FORMATO_POSICION_Y_LONGITUD = "<QI"


class ErrorAlmacenDisco(Exception):
    """Error al leer o escribir el almacén, con la operación que falló."""

    def __init__(self, operacion, detalle):
        self.operacion = operacion
        self.detalle = detalle
        super().__init__(f"No se pudo {operacion}: {detalle}")


class _IndiceDanado(Exception):
    """Uso interno: el archivo de índice no se pudo interpretar."""


class AlmacenFichas:
    """Fichas del catálogo guardadas en disco, validadas por versión."""

    def __init__(self, carpeta):
        self._carpeta = Path(carpeta)
        self._ruta_datos = self._carpeta / _NOMBRE_ARCHIVO_DATOS
        self._ruta_indice = self._carpeta / _NOMBRE_ARCHIVO_INDICE
        self._abierto = False
        self._version_catalogo = None
        self._motivo_del_ultimo_descarte = None
        # Índice en memoria: tres listas paralelas, ordenadas por id.
        self._ids_ordenados = []
        self._posiciones = []
        self._longitudes = []

    # ------------------------------------------------------------------
    # Apertura y versiones
    # ------------------------------------------------------------------

    def abrir(self, version_catalogo_vigente):
        """Carga el índice si su versión coincide con la vigente; si no,
        descarta lo guardado y empieza vacío."""
        if not isinstance(version_catalogo_vigente, str) or not version_catalogo_vigente:
            raise ValueError("La versión del catálogo debe ser un texto no vacío")
        self._version_catalogo = version_catalogo_vigente
        self._vaciar_indice_en_memoria()
        self._motivo_del_ultimo_descarte = None
        self._abierto = True

        if not self._ruta_indice.exists():
            return
        try:
            version_guardada, ids, posiciones, longitudes = self._leer_archivo_indice()
        except _IndiceDanado as error:
            self._descartar_todo(f"el índice estaba dañado o tenía otro formato ({error})")
            return
        except OSError as error:
            self._descartar_todo(f"no se pudo leer el índice ({error})")
            return

        if version_guardada != version_catalogo_vigente:
            self._descartar_todo(
                f"cambió la versión del catálogo ({version_guardada} → {version_catalogo_vigente}); "
                f"se descartaron {len(ids)} fichas"
            )
            return
        self._ids_ordenados = ids
        self._posiciones = posiciones
        self._longitudes = longitudes

    def version_catalogo(self):
        return self._version_catalogo

    def motivo_del_ultimo_descarte(self):
        """Por qué se descartó lo guardado al abrir, o None si no se descartó."""
        return self._motivo_del_ultimo_descarte

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def cantidad_de_fichas(self):
        self._exigir_abierto()
        return len(self._ids_ordenados)

    def contiene_ficha(self, id_ficha):
        self._exigir_abierto()
        encontrado, _ = self._buscar_en_indice(id_ficha)
        return encontrado

    def ids_ordenados(self):
        """Copia de los ids guardados, en orden alfabético."""
        self._exigir_abierto()
        return list(self._ids_ordenados)

    def leer_ficha(self, id_ficha):
        """Devuelve la ficha (el JSON del API) o None si no está guardada o
        sus bytes no se pueden leer. Lee solo los bytes de esa ficha."""
        self._exigir_abierto()
        encontrado, posicion_en_indice = self._buscar_en_indice(id_ficha)
        if not encontrado:
            return None
        posicion = self._posiciones[posicion_en_indice]
        longitud = self._longitudes[posicion_en_indice]
        try:
            with open(self._ruta_datos, "rb") as archivo:
                archivo.seek(posicion)
                contenido = archivo.read(longitud)
            if len(contenido) != longitud:
                return None  # el archivo de datos quedó más corto de lo esperado
            return json.loads(contenido.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None  # quien llama la volverá a descargar

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    def guardar_fichas(self, fichas):
        """Guarda una lista de fichas (tal como las devuelve el API). Si un id
        ya estaba guardado, se reemplaza por la versión nueva."""
        self._exigir_abierto()
        for ficha in fichas:
            if not isinstance(ficha, dict) or not isinstance(ficha.get("id"), str) or not ficha["id"]:
                raise ValueError(f"Cada ficha debe traer un id de texto: {ficha!r}")
        if not fichas:
            return
        try:
            self._carpeta.mkdir(parents=True, exist_ok=True)
            with open(self._ruta_datos, "ab") as archivo:
                archivo.seek(0, os.SEEK_END)
                for ficha in fichas:
                    contenido = json.dumps(ficha, ensure_ascii=False).encode("utf-8")
                    posicion = archivo.tell()
                    archivo.write(contenido)
                    self._registrar_en_indice(ficha["id"], posicion, len(contenido))
            self._escribir_archivo_indice()
        except OSError as error:
            raise ErrorAlmacenDisco("guardar fichas del catálogo en disco", str(error)) from error

    # ------------------------------------------------------------------
    # Índice en memoria
    # ------------------------------------------------------------------

    def _buscar_en_indice(self, id_ficha):
        """Búsqueda binaria. Devuelve (encontrado, posición). Si no está, la
        posición es donde habría que insertarlo para mantener el orden."""
        izquierda = 0
        derecha = len(self._ids_ordenados)
        while izquierda < derecha:
            medio = (izquierda + derecha) // 2
            if self._ids_ordenados[medio] < id_ficha:
                izquierda = medio + 1
            else:
                derecha = medio
        encontrado = (izquierda < len(self._ids_ordenados)
                      and self._ids_ordenados[izquierda] == id_ficha)
        return encontrado, izquierda

    def _registrar_en_indice(self, id_ficha, posicion, longitud):
        encontrado, lugar = self._buscar_en_indice(id_ficha)
        if encontrado:
            self._posiciones[lugar] = posicion
            self._longitudes[lugar] = longitud
        else:
            self._ids_ordenados.insert(lugar, id_ficha)
            self._posiciones.insert(lugar, posicion)
            self._longitudes.insert(lugar, longitud)

    def _vaciar_indice_en_memoria(self):
        self._ids_ordenados = []
        self._posiciones = []
        self._longitudes = []

    def _exigir_abierto(self):
        if not self._abierto:
            raise RuntimeError("Primero hay que llamar a abrir(version_catalogo)")

    def _descartar_todo(self, motivo):
        """Empieza vacío: borra los datos y deja un índice vacío con la
        versión vigente."""
        self._motivo_del_ultimo_descarte = motivo
        self._vaciar_indice_en_memoria()
        try:
            self._carpeta.mkdir(parents=True, exist_ok=True)
            with open(self._ruta_datos, "wb"):
                pass  # abrir en modo "wb" deja el archivo vacío
            self._escribir_archivo_indice()
        except OSError as error:
            raise ErrorAlmacenDisco("reiniciar el almacén de fichas", str(error)) from error

    # ------------------------------------------------------------------
    # Archivo de índice (binario)
    # ------------------------------------------------------------------

    def _escribir_archivo_indice(self):
        partes = [struct.pack(_FORMATO_ENCABEZADO, FIRMA_DEL_INDICE, VERSION_DEL_FORMATO)]
        partes.append(_empaquetar_texto(self._version_catalogo))
        partes.append(struct.pack(_FORMATO_CANTIDAD, len(self._ids_ordenados)))
        for posicion_en_indice in range(len(self._ids_ordenados)):
            partes.append(_empaquetar_texto(self._ids_ordenados[posicion_en_indice]))
            partes.append(struct.pack(
                _FORMATO_POSICION_Y_LONGITUD,
                self._posiciones[posicion_en_indice],
                self._longitudes[posicion_en_indice],
            ))
        ruta_temporal = self._ruta_indice.with_name(_NOMBRE_ARCHIVO_INDICE + ".tmp")
        with open(ruta_temporal, "wb") as archivo:
            archivo.write(b"".join(partes))
        os.replace(ruta_temporal, self._ruta_indice)  # reemplazo de una sola vez

    def _leer_archivo_indice(self):
        with open(self._ruta_indice, "rb") as archivo:
            contenido = archivo.read()
        try:
            firma, version_formato = struct.unpack_from(_FORMATO_ENCABEZADO, contenido, 0)
            if firma != FIRMA_DEL_INDICE:
                raise _IndiceDanado("la firma no es la de CRIPTA")
            if version_formato != VERSION_DEL_FORMATO:
                raise _IndiceDanado(
                    f"formato {version_formato}, se esperaba {VERSION_DEL_FORMATO}"
                )
            desplazamiento = struct.calcsize(_FORMATO_ENCABEZADO)
            version_catalogo, desplazamiento = _desempaquetar_texto(contenido, desplazamiento)
            (cantidad,) = struct.unpack_from(_FORMATO_CANTIDAD, contenido, desplazamiento)
            desplazamiento += struct.calcsize(_FORMATO_CANTIDAD)

            ids, posiciones, longitudes = [], [], []
            for _ in range(cantidad):
                id_ficha, desplazamiento = _desempaquetar_texto(contenido, desplazamiento)
                posicion, longitud = struct.unpack_from(
                    _FORMATO_POSICION_Y_LONGITUD, contenido, desplazamiento
                )
                desplazamiento += struct.calcsize(_FORMATO_POSICION_Y_LONGITUD)
                if ids and not ids[-1] < id_ficha:
                    raise _IndiceDanado("las entradas no están ordenadas por id")
                ids.append(id_ficha)
                posiciones.append(posicion)
                longitudes.append(longitud)
        except (struct.error, UnicodeDecodeError) as error:
            raise _IndiceDanado(str(error)) from error
        if desplazamiento != len(contenido):
            raise _IndiceDanado("sobran bytes al final del índice")
        return version_catalogo, ids, posiciones, longitudes


def _empaquetar_texto(texto):
    """Texto como [largo en 2 bytes][bytes UTF-8]."""
    contenido = texto.encode("utf-8")
    return struct.pack(_FORMATO_LARGO_DE_TEXTO, len(contenido)) + contenido


def _desempaquetar_texto(contenido, desplazamiento):
    (largo,) = struct.unpack_from(_FORMATO_LARGO_DE_TEXTO, contenido, desplazamiento)
    desplazamiento += struct.calcsize(_FORMATO_LARGO_DE_TEXTO)
    fin = desplazamiento + largo
    if fin > len(contenido):
        raise _IndiceDanado("un texto se sale del archivo")
    return contenido[desplazamiento:fin].decode("utf-8"), fin
