"""
Simula el recorrido de una partida usando solo el bloque 2 (sin motor ni interfaz).

Para qué sirve
    - Verificar contra el API real el presupuesto de solicitudes: la primera
      corrida es un arranque en frío y la segunda, con la misma carpeta de
      caché, un arranque en caliente.
    - Mostrarle al grupo cómo se usa el RepositorioCripta desde el controlador.

Cómo recorre la cripta
    No conoce ningún id de sala (§9): empieza en la sala inicial que indica
    el API y en cada paso elige al azar, con semilla fija, una salida de la
    sala actual. No aplica reglas del juego (puertas cerradas, enemigos):
    solo carga los datos que el juego necesitaría.

    Usa el Traductor como lo hará el controlador: crea el jugador y el mapa
    (salas y puertas) y llena cada sala antes de entrar, así que al final
    muestra cuántos enemigos, objetos y trampas del modelo se crearon.

Uso, desde la carpeta cripta/:
    python -m tools.simular_partida_bloque2
        con el API real y la caché en la carpeta cache_cripta
    python -m tools.simular_partida_bloque2 --offline datos_offline
        con los datos guardados (no usa la red)
    python -m tools.simular_partida_bloque2 --borrar-cache
        borra la caché antes de empezar (fuerza un arranque en frío)

Otras opciones: --cripta ID, --pasos N, --semilla N, --cache-size N, --cache CARPETA
"""
import argparse
import random
import shutil
import sys
from pathlib import Path

from adapters.fuente_datos import ErrorFuenteDatos
from adapters.fuente_http import FuenteHttp
from adapters.fuente_offline import FuenteOffline
from structures.cache_catalogo import CAPACIDAD_POR_DEFECTO
from repository.repositorio_cripta import RepositorioCripta

CARPETA_DE_CACHE_POR_DEFECTO = "cache_cripta"


def simular_partida(repositorio, id_cripta=None, pasos=20, semilla=2026, mostrar=print):
    """Recorre la cripta al azar y devuelve el reporte de red final."""
    repositorio.empezar_conteo_de_partida()
    criptas = repositorio.listar_criptas()
    if id_cripta is None:
        id_cripta = criptas[0]["id"]
    datos = repositorio.iniciar_partida(id_cripta)
    mostrar(f"Partida en {datos.id_cripta} (versión {datos.version_cripta}, "
            f"catálogo {datos.version_catalogo}), presupuesto {datos.presupuesto_solicitudes}")

    jugador = repositorio.crear_jugador()
    mapa = repositorio.crear_mapa()
    enemigos = repositorio.cargar_contenido_de_sala(mapa.room(jugador.room_id))

    azar = random.Random(semilla)
    recorrido = [jugador.room_id]
    for _ in range(pasos):
        salidas = mapa.room(jugador.room_id).exits()
        if not salidas:
            break
        siguiente = azar.choice(salidas).destination
        # Antes de confirmar la entrada: puede usar la red.
        enemigos.extend(repositorio.cargar_contenido_de_sala(mapa.room(siguiente)))
        jugador.room_id = siguiente
        recorrido.append(siguiente)
        repositorio.despues_de_accion(siguiente)  # después de la acción
    mostrar("Recorrido: " + " → ".join(str(sala) for sala in recorrido))
    mostrar(resumen_del_modelo(mapa, enemigos))
    return repositorio.reporte_de_red()


def resumen_del_modelo(mapa, enemigos):
    """Cuántos objetos del modelo creó el Traductor durante el recorrido."""
    salas_cargadas = objetos = trampas = 0
    for id_sala in mapa.room_ids():
        sala = mapa.room(id_sala)
        if sala.content_loaded:
            salas_cargadas += 1
            objetos += len(sala.floor_items)
            trampas += len(sala.traps)
    soltados = 0
    for enemigo in enemigos:
        soltados += len(enemigo.drops)
    return (f"Modelo creado por el Traductor: salas {len(mapa)} (con contenido {salas_cargadas}), "
            f"enemigos {len(enemigos)}, objetos en el suelo {objetos}, "
            f"objetos que sueltan los enemigos {soltados}, trampas {trampas}")


def main():
    analizador = argparse.ArgumentParser(description="Simula una partida usando solo el bloque 2.")
    analizador.add_argument("--offline", metavar="CARPETA", help="usar datos guardados en vez del API")
    analizador.add_argument("--cache", default=CARPETA_DE_CACHE_POR_DEFECTO, help="carpeta de la caché")
    analizador.add_argument("--cache-size", type=int, default=CAPACIDAD_POR_DEFECTO)
    analizador.add_argument("--cripta", help="id de la cripta (por defecto, la primera publicada)")
    analizador.add_argument("--pasos", type=int, default=20)
    analizador.add_argument("--semilla", type=int, default=2026)
    analizador.add_argument("--borrar-cache", action="store_true", help="empezar sin caché en disco")
    argumentos = analizador.parse_args()

    if argumentos.borrar_cache and Path(argumentos.cache).exists():
        shutil.rmtree(argumentos.cache)
        print(f"Caché borrada: {argumentos.cache}")

    try:
        fuente = FuenteOffline(argumentos.offline) if argumentos.offline else FuenteHttp()
        repositorio = RepositorioCripta(fuente, argumentos.cache, argumentos.cache_size)
        reporte = simular_partida(repositorio, argumentos.cripta, argumentos.pasos, argumentos.semilla)
    except ErrorFuenteDatos as error:
        print(f"Error: {error}")
        sys.exit(1)

    print()
    for linea in reporte.lineas_de_texto():
        print(linea)


if __name__ == "__main__":
    main()
