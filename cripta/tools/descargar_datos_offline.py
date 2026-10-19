"""
Descarga criptas completas del API y las guarda en el formato de FuenteOffline.

Para qué sirve
    - Comprobar que el programa puede consultar el API desde Python, que es
      lo primero que pide el enunciado.
    - Tener datos para desarrollar y probar con --offline sin gastar el
      presupuesto de una partida ni provocar HTTP 429.

No es una partida, así que no aplica presupuesto_solicitudes. Usa
FuenteHttp, por lo que respeta los HTTP 429 igual que el programa.

Uso, desde la carpeta cripta/:
    python -m tools.descargar_datos_offline
        descarga todas las criptas publicadas en la carpeta datos_offline
    python -m tools.descargar_datos_offline cripta-01
        descarga solo esa cripta
    python -m tools.descargar_datos_offline --carpeta otra cripta-01 cripta-02
"""
import argparse
import sys

from adapters.fuente_datos import MAXIMO_POR_LOTE, ErrorFuenteDatos
from adapters.fuente_http import FuenteHttp
from adapters.fuente_offline import GuardadorDatosOffline
from structures.lista_sin_repetidos import ListaSinRepetidos

CARPETA_POR_DEFECTO = "datos_offline"


class ResumenDescarga:
    def __init__(self):
        self.criptas_descargadas = []
        self.fichas_descargadas = 0
        self.lotes_de_catalogo_fallidos = []  # (lista de ids, mensaje de error)
        self.solicitudes_realizadas = 0


def descargar_datos_offline(fuente, guardador, ids_criptas=None, mostrar=print):
    """Descarga las criptas indicadas (o todas) y el catálogo que usan."""
    resumen = ResumenDescarga()
    ids_de_fichas = ListaSinRepetidos()

    lista_criptas = fuente.listar_criptas()
    guardador.guardar_lista_criptas(lista_criptas)
    if not ids_criptas:
        ids_criptas = [cripta["id"] for cripta in lista_criptas["criptas"]]

    for id_cripta in ids_criptas:
        _descargar_una_cripta(fuente, guardador, id_cripta, ids_de_fichas, mostrar)
        resumen.criptas_descargadas.append(id_cripta)

    _descargar_catalogo(fuente, guardador, ids_de_fichas, resumen, mostrar)
    guardador.guardar_version_catalogo(fuente.version_catalogo())

    resumen.solicitudes_realizadas = fuente.solicitudes_realizadas()
    return resumen


def _descargar_una_cripta(fuente, guardador, id_cripta, ids_de_fichas, mostrar):
    generales = fuente.datos_generales(id_cripta)
    guardador.guardar_datos_generales(generales)

    ids_salas = []
    pagina = 1
    total_paginas = generales["paginas"]
    while pagina <= total_paginas:
        respuesta = fuente.pagina_salas(id_cripta, pagina)
        guardador.guardar_pagina_salas(id_cripta, respuesta)
        total_paginas = respuesta["total_paginas"]
        for sala in respuesta["salas"]:
            ids_salas.append(sala["id"])
        pagina += 1

    for inicio in range(0, len(ids_salas), MAXIMO_POR_LOTE):
        respuesta = fuente.contenido(id_cripta, ids_salas[inicio:inicio + MAXIMO_POR_LOTE])
        guardador.guardar_contenido(id_cripta, respuesta)
        for entrada in respuesta["contenido"]:
            for enemigo in entrada.get("enemigos") or []:
                ids_de_fichas.agregar(enemigo["tipo"])
            for id_objeto in entrada.get("objetos") or []:
                ids_de_fichas.agregar(id_objeto)
            for trampa in entrada.get("trampas") or []:
                ids_de_fichas.agregar(trampa["tipo"])

    mostrar(f"  {id_cripta}: versión {generales['version']}, {len(ids_salas)} salas")


def _descargar_catalogo(fuente, guardador, ids_de_fichas, resumen, mostrar):
    """Pide las fichas en lotes de 10. Lo que sueltan los enemigos se agrega
    a la misma lista, así que el ciclo sigue hasta que no aparecen ids nuevos."""
    siguiente = 0
    while siguiente < len(ids_de_fichas.elementos):
        lote = ids_de_fichas.elementos[siguiente:siguiente + MAXIMO_POR_LOTE]
        siguiente += len(lote)
        try:
            respuesta = fuente.catalogo(lote)
        except ErrorFuenteDatos as error:
            # Se continúa con los demás lotes y se informa al final.
            resumen.lotes_de_catalogo_fallidos.append((lote, str(error)))
            continue
        guardador.guardar_catalogo(respuesta)
        for ficha in respuesta["entidades"]:
            resumen.fichas_descargadas += 1
            if ficha.get("clase") == "enemigo":
                for id_suelta in ficha.get("suelta") or []:
                    ids_de_fichas.agregar(id_suelta)
    mostrar(f"  catálogo: {resumen.fichas_descargadas} fichas")


def main():
    analizador = argparse.ArgumentParser(
        description="Descarga criptas del API en el formato que lee --offline."
    )
    analizador.add_argument("criptas", nargs="*", help="ids de criptas (por defecto, todas)")
    analizador.add_argument("--carpeta", default=CARPETA_POR_DEFECTO, help="carpeta de destino")
    argumentos = analizador.parse_args()

    fuente = FuenteHttp()
    guardador = GuardadorDatosOffline(argumentos.carpeta)
    print(f"Identificador de cliente de esta ejecución: {fuente.identificador_cliente()}")
    print(f"Descargando en la carpeta {argumentos.carpeta} ...")
    try:
        resumen = descargar_datos_offline(fuente, guardador, argumentos.criptas)
    except ErrorFuenteDatos as error:
        print(f"Error: {error}")
        print(f"Solicitudes realizadas antes del error: {fuente.solicitudes_realizadas()}")
        sys.exit(1)

    print(f"Listo: {len(resumen.criptas_descargadas)} criptas, "
          f"{resumen.fichas_descargadas} fichas, "
          f"{resumen.solicitudes_realizadas} solicitudes realizadas.")
    for lote, mensaje in resumen.lotes_de_catalogo_fallidos:
        print(f"Aviso: no se descargaron las fichas {', '.join(lote)}: {mensaje}")


if __name__ == "__main__":
    main()
