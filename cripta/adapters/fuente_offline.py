"""
FuenteOffline: lee desde disco las respuestas del API ya guardadas (bloque 2).

Requisitos del enunciado que cumple
    - --offline lee los datos desde disco a través del mismo contrato que el
      cliente de red, y el modelo no sabe de dónde vienen (§3.4).
    - Leer de disco no cuenta como solicitud de red (§5.1): esta clase nunca
      llama a _consumir_solicitud.

Formato de la carpeta (propio del grupo, mientras el curso publica su paquete)
    <carpeta>/criptas.json                              respuesta de GET /criptas
    <carpeta>/criptas/<id_cripta>/general.json          respuesta de GET /criptas/<id>
    <carpeta>/criptas/<id_cripta>/salas/pagina_<n>.json respuesta de GET .../salas?pagina=n
    <carpeta>/criptas/<id_cripta>/contenido/sala_<n>.json  UNA entrada de contenido
    <carpeta>/catalogo/version.json                     respuesta de GET /catalogo/version
    <carpeta>/catalogo/fichas/<id_ficha>.json           UNA ficha del catálogo

    El contenido y las fichas se guardan uno por archivo para poder armar
    cualquier lote que se pida, igual que el API. La versión de la cripta no
    tiene archivo propio: sale de general.json, que ya la incluye.

    El formato se define en un solo lugar (RutasDatosOffline), que usan tanto
    FuenteOffline para leer como GuardadorDatosOffline para escribir. Cuando
    el curso publique su paquete, solo hay que adaptar esa clase o convertir
    el paquete a este formato.
"""
import json
from pathlib import Path

from adapters.fuente_datos import (
    ErrorFuenteDatos,
    FuenteDatos,
    validar_ids_catalogo,
    validar_ids_salas,
    validar_numero_de_pagina,
)

_CARACTERES_NO_PERMITIDOS_EN_NOMBRES = '<>:"/\\|?*'


class RutasDatosOffline:
    """Dónde vive cada dato dentro de la carpeta offline."""

    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)

    def lista_criptas(self):
        return self.carpeta / "criptas.json"

    def datos_generales(self, id_cripta):
        return self._carpeta_de_cripta(id_cripta) / "general.json"

    def pagina_salas(self, id_cripta, pagina):
        return self._carpeta_de_cripta(id_cripta) / "salas" / f"pagina_{pagina}.json"

    def contenido_de_sala(self, id_cripta, id_sala):
        return self._carpeta_de_cripta(id_cripta) / "contenido" / f"sala_{id_sala}.json"

    def version_catalogo(self):
        return self.carpeta / "catalogo" / "version.json"

    def ficha_catalogo(self, id_ficha):
        return self.carpeta / "catalogo" / "fichas" / f"{nombre_de_archivo_seguro(id_ficha)}.json"

    def _carpeta_de_cripta(self, id_cripta):
        return self.carpeta / "criptas" / nombre_de_archivo_seguro(id_cripta)


def nombre_de_archivo_seguro(texto):
    """Rechaza ids que no sirven como nombre de archivo o que intentarían
    salir de la carpeta (por ejemplo "../otra"). Los ids reales del API,
    como "cripta-01" o "ent_rata_gigante", pasan sin cambios."""
    texto = str(texto)
    if texto in ("", ".", "..") or texto.strip() != texto:
        raise ValueError(f"Id no válido como nombre de archivo: {texto!r}")
    for caracter in texto:
        if caracter in _CARACTERES_NO_PERMITIDOS_EN_NOMBRES or ord(caracter) < 32:
            raise ValueError(f"Id no válido como nombre de archivo: {texto!r}")
    return texto


class FuenteOffline(FuenteDatos):
    """Fuente de datos que lee la carpeta offline."""

    def __init__(self, carpeta):
        super().__init__()
        self._rutas = RutasDatosOffline(carpeta)
        if not self._rutas.carpeta.is_dir():
            raise ErrorFuenteDatos(
                "abrir los datos offline", f"no existe la carpeta {self._rutas.carpeta}"
            )

    def descripcion_del_origen(self):
        return f"datos offline ({self._rutas.carpeta})"

    # ------------------------------------------------------------------
    # Operaciones del contrato FuenteDatos
    # ------------------------------------------------------------------

    def listar_criptas(self):
        return self._leer_json("listar las criptas", lambda: self._rutas.lista_criptas())

    def datos_generales(self, id_cripta):
        return self._leer_json(
            f"obtener los datos generales de {id_cripta}",
            lambda: self._rutas.datos_generales(id_cripta),
        )

    def version_cripta(self, id_cripta):
        generales = self.datos_generales(id_cripta)
        return {"id": generales["id"], "version": generales["version"]}

    def pagina_salas(self, id_cripta, pagina):
        validar_numero_de_pagina(pagina)
        return self._leer_json(
            f"descargar la página {pagina} de salas de {id_cripta}",
            lambda: self._rutas.pagina_salas(id_cripta, pagina),
        )

    def contenido(self, id_cripta, ids_salas):
        validar_ids_salas(ids_salas)
        entradas = []
        for id_sala in ids_salas:
            entradas.append(
                self._leer_json(
                    f"descargar el contenido de la sala {id_sala} de {id_cripta}",
                    lambda: self._rutas.contenido_de_sala(id_cripta, id_sala),
                )
            )
        return {"contenido": entradas}

    def catalogo(self, ids):
        validar_ids_catalogo(ids)
        fichas = []
        for id_ficha in ids:
            fichas.append(
                self._leer_json(
                    f"descargar la ficha {id_ficha} del catálogo",
                    lambda: self._rutas.ficha_catalogo(id_ficha),
                )
            )
        return {"entidades": fichas}

    def version_catalogo(self):
        return self._leer_json(
            "obtener la versión del catálogo", lambda: self._rutas.version_catalogo()
        )

    # ------------------------------------------------------------------
    # Lectura de archivos
    # ------------------------------------------------------------------

    def _leer_json(self, operacion, obtener_ruta):
        """Lee un archivo JSON y convierte cualquier problema en ErrorFuenteDatos.

        obtener_ruta es una función para que un id inválido también se
        reporte como ErrorFuenteDatos con la operación que falló.
        """
        try:
            ruta = obtener_ruta()
        except ValueError as error:
            raise ErrorFuenteDatos(operacion, str(error)) from error
        try:
            with open(ruta, encoding="utf-8") as archivo:
                return json.load(archivo)
        except FileNotFoundError as error:
            raise ErrorFuenteDatos(
                operacion, f"el dato no está en la carpeta offline ({ruta})"
            ) from error
        except json.JSONDecodeError as error:
            raise ErrorFuenteDatos(
                operacion, f"el archivo {ruta} no contiene JSON válido"
            ) from error
        except OSError as error:
            raise ErrorFuenteDatos(operacion, f"no se pudo leer {ruta} ({error})") from error


class GuardadorDatosOffline:
    """Escribe respuestas del API en el formato que lee FuenteOffline.

    Lo usa la herramienta tools/descargar_datos_offline.py. Cada
    método recibe la respuesta tal como la devolvió la fuente.
    """

    def __init__(self, carpeta):
        self._rutas = RutasDatosOffline(carpeta)

    def guardar_lista_criptas(self, respuesta):
        _escribir_json(self._rutas.lista_criptas(), respuesta)

    def guardar_datos_generales(self, respuesta):
        _escribir_json(self._rutas.datos_generales(respuesta["id"]), respuesta)

    def guardar_pagina_salas(self, id_cripta, respuesta):
        _escribir_json(self._rutas.pagina_salas(id_cripta, respuesta["pagina"]), respuesta)

    def guardar_contenido(self, id_cripta, respuesta):
        """Separa la respuesta en un archivo por sala."""
        for entrada in respuesta["contenido"]:
            _escribir_json(self._rutas.contenido_de_sala(id_cripta, entrada["sala"]), entrada)

    def guardar_catalogo(self, respuesta):
        """Separa la respuesta en un archivo por ficha."""
        for ficha in respuesta["entidades"]:
            _escribir_json(self._rutas.ficha_catalogo(ficha["id"]), ficha)

    def guardar_version_catalogo(self, respuesta):
        _escribir_json(self._rutas.version_catalogo(), respuesta)


def _escribir_json(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        # ensure_ascii=False conserva las tildes legibles ("guardián").
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
