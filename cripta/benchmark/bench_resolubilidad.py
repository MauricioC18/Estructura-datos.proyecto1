import json
import random
import time
from pathlib import Path

from benchmark.utilidades_medicion import Measurement, calentar_procesador
from model.key_location import KeyLocation
from model.resolubilidad import PuertaDeFrontera, VerificacionDeResolubilidad, verificar_resolubilidad
from repository.traductor import Traductor
from structures.sorting import merge_sort
from structures.tabla_hash import TablaHash

CANTIDADES_DE_LLAVES = (25, 50, 100, 200, 400)
SALAS_POR_ZONA = 5
SEMILLA = 2026
REPETICIONES = 3
CARPETA_PAQUETE_SEGUNDA_PARTE = Path(__file__).resolve().parent.parent / "datos_offline_p2"


class VerificacionIngenua(VerificacionDeResolubilidad):

    def explorar_por_rondas(self):
        ronda = 0
        while True:
            alcanzadas = TablaHash()
            espera = TablaHash()
            cerradas_sin_llave = []
            nuevas = []
            vistas = TablaHash()
            frente = [self.sala_inicial]
            alcanzadas.insertar(self.sala_inicial, True)
            indice = 0
            while indice < len(frente):
                sala = frente[indice]
                indice += 1
                self.salas_examinadas += 1
                if not self.ronda_de_sala.contiene(sala):
                    self.ronda_de_sala.insertar(sala, ronda)
                for ubicacion in self.llaves_en_sala.obtener(sala, []):
                    llave = ubicacion.key_id
                    if not self.ronda_de_llave.contiene(llave) and not vistas.contiene(llave):
                        vistas.insertar(llave, True)
                        nuevas.append(llave)
                for salida in self.mapa.room(sala).exits():
                    self.salidas_examinadas += 1
                    destino = salida.destination
                    puerta = salida.door
                    if destino == self.sala_salida and puerta.key_id == self.llave_salida:
                        self.hay_puerta_hacia_la_salida = True
                    if alcanzadas.contiene(destino):
                        continue
                    if puerta.is_open or (puerta.key_id is not None
                                          and self.ronda_de_llave.contiene(puerta.key_id)):
                        alcanzadas.insertar(destino, True)
                        frente.append(destino)
                    else:
                        pendiente = _puerta_pendiente(sala, salida)
                        if puerta.key_id is None:
                            cerradas_sin_llave.append(pendiente)
                        else:
                            lista = espera.obtener(puerta.key_id)
                            if lista is None:
                                lista = []
                                espera.insertar(puerta.key_id, lista)
                            lista.append(pendiente)
            if not nuevas:
                self.espera = espera
                self.cerradas_sin_llave = cerradas_sin_llave
                return
            for llave in merge_sort(nuevas):
                self.ronda_de_llave.insertar(llave, ronda)
                self.orden.append(llave)
            ronda += 1


def _puerta_pendiente(sala, salida):
    return PuertaDeFrontera(sala, salida.direction, salida.destination, salida.door.key_id)


def verificar_resolubilidad_ingenua(mapa, sala_inicial, sala_salida, llave_salida, ubicaciones):
    return VerificacionIngenua(mapa, sala_inicial, sala_salida, llave_salida, ubicaciones).resolver()


def generar_cripta_encadenada(semilla, cantidad_de_llaves, salas_por_zona=SALAS_POR_ZONA):
    generador = random.Random(semilla)
    salas = []
    ubicaciones = []
    siguiente_id = 1
    primera_de_la_zona_anterior = None
    ultima_de_la_zona_anterior = None
    for zona in range(cantidad_de_llaves):
        ids = list(range(siguiente_id, siguiente_id + salas_por_zona))
        siguiente_id += salas_por_zona
        for posicion, id_sala in enumerate(ids):
            salidas = {}
            if posicion > 0:
                salidas["O"] = {"sala": ids[posicion - 1], "costo": generador.randint(1, 300)}
            if posicion < len(ids) - 1:
                salidas["E"] = {"sala": ids[posicion + 1]}
            salas.append({"id": id_sala, "nombre": f"Sala {id_sala}", "salidas": salidas})
        _copiar_costos_de_vuelta(salas, ids)
        if ultima_de_la_zona_anterior is not None:
            llave_anterior = _id_de_llave(zona - 1)
            _sala(salas, ultima_de_la_zona_anterior)["salidas"]["N"] = {
                "sala": ids[0], "cerrada": True, "llave": llave_anterior}
            _sala(salas, ids[0])["salidas"]["S"] = {"sala": ultima_de_la_zona_anterior}
        sala_de_la_llave = ids[generador.randrange(len(ids))]
        if generador.random() < 0.25:
            ubicaciones.append(KeyLocation(_id_de_llave(zona), sala_de_la_llave, f"e-{zona}"))
        else:
            ubicaciones.append(KeyLocation(_id_de_llave(zona), sala_de_la_llave))
        primera_de_la_zona_anterior = ids[0]
        ultima_de_la_zona_anterior = ids[-1]
    sala_salida = siguiente_id
    llave_salida = _id_de_llave(cantidad_de_llaves - 1)
    salas.append({"id": sala_salida, "nombre": "Salida", "salidas": {"S": {"sala": ultima_de_la_zona_anterior}}})
    _sala(salas, ultima_de_la_zona_anterior)["salidas"]["N"] = {
        "sala": sala_salida, "cerrada": True, "llave": llave_salida}
    generador.shuffle(ubicaciones)
    return {
        "salas": salas,
        "sala_inicial": 1 if primera_de_la_zona_anterior is not None else sala_salida,
        "sala_salida": sala_salida,
        "llave_salida": llave_salida,
        "ubicaciones": ubicaciones,
    }


def _copiar_costos_de_vuelta(salas, ids):
    for posicion in range(1, len(ids)):
        costo = _sala(salas, ids[posicion])["salidas"]["O"]["costo"]
        _sala(salas, ids[posicion - 1])["salidas"]["E"]["costo"] = costo


def _sala(salas, id_sala):
    return salas[id_sala - 1]


def _id_de_llave(zona):
    return f"itm_llave_{zona:04d}"


def mapa_de(cripta):
    return Traductor(lambda id_ficha: None).crear_mapa(cripta["salas"])


def _verificar(funcion, mapa, cripta):
    return funcion(mapa, cripta["sala_inicial"], cripta["sala_salida"], cripta["llave_salida"],
                   cripta["ubicaciones"])


def _mejor_tiempo(funcion, mapa, cripta, repeticiones=REPETICIONES):
    mejor = None
    reporte = None
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        reporte = _verificar(funcion, mapa, cripta)
        total = time.perf_counter() - inicio
        if mejor is None or total < mejor:
            mejor = total
    return mejor, reporte


def contar_operaciones(clase, mapa, cripta):
    verificacion = clase(mapa, cripta["sala_inicial"], cripta["sala_salida"], cripta["llave_salida"],
                         cripta["ubicaciones"])
    reporte = verificacion.resolver()
    return verificacion.salas_examinadas + verificacion.salidas_examinadas, reporte


def cripta_mas_grande_del_paquete(carpeta=CARPETA_PAQUETE_SEGUNDA_PARTE):
    criptas = carpeta / "criptas"
    if not criptas.is_dir():
        return None, "no hay paquete offline de la segunda parte en datos_offline_p2"
    elegida = None
    for carpeta_de_cripta in criptas.iterdir():
        general = carpeta_de_cripta / "general.json"
        if not general.is_file():
            continue
        datos = json.loads(general.read_text(encoding="utf-8"))
        if elegida is None or datos["salas_total"] > elegida[1]["salas_total"]:
            elegida = (carpeta_de_cripta, datos)
    if elegida is None:
        return None, "el paquete no trae criptas"
    carpeta_de_cripta, generales = elegida
    archivo_de_llaves = carpeta_de_cripta / "llaves.json"
    if not archivo_de_llaves.is_file():
        return None, f"el paquete no trae la ubicación de llaves de {generales['id']}"
    salas = []
    for pagina in range(1, generales["paginas"] + 1):
        respuesta = json.loads((carpeta_de_cripta / "salas" / f"pagina_{pagina}.json").read_text(encoding="utf-8"))
        salas.extend(respuesta["salas"])
    llaves = json.loads(archivo_de_llaves.read_text(encoding="utf-8"))
    existe = TablaHash()
    for sala in salas:
        existe.insertar(sala["id"], True)
    ubicaciones = Traductor(lambda id_ficha: None).crear_ubicaciones_de_llaves(llaves, existe.contiene)
    return {
        "id": generales["id"],
        "salas": salas,
        "sala_inicial": generales["sala_inicial"],
        "sala_salida": generales["sala_salida"],
        "llave_salida": generales["llave_salida"],
        "ubicaciones": ubicaciones,
    }, ""


def run():
    calentar_procesador()
    mediciones = []
    for cantidad in CANTIDADES_DE_LLAVES:
        cripta = generar_cripta_encadenada(SEMILLA + cantidad, cantidad)
        mapa = mapa_de(cripta)
        segundos_incremental, reporte_incremental = _mejor_tiempo(verificar_resolubilidad, mapa, cripta)
        segundos_ingenua, reporte_ingenuo = _mejor_tiempo(verificar_resolubilidad_ingenua, mapa, cripta)
        operaciones_incremental, _ = contar_operaciones(VerificacionDeResolubilidad, mapa, cripta)
        operaciones_ingenua, _ = contar_operaciones(VerificacionIngenua, mapa, cripta)
        iguales = reporte_incremental.lineas_de_texto() == reporte_ingenuo.lineas_de_texto()
        salas = len(cripta["salas"])
        mediciones.append(Measurement(
            f"Incremental, {cantidad} llaves encadenadas", segundos_incremental,
            f"{salas} salas; {operaciones_incremental} salas y salidas examinadas"))
        mediciones.append(Measurement(
            f"Ingenua, {cantidad} llaves encadenadas", segundos_ingenua,
            f"{salas} salas; {operaciones_ingenua} salas y salidas examinadas; "
            f"mismo reporte: {'sí' if iguales else 'NO'}"))
    cripta, motivo = cripta_mas_grande_del_paquete()
    if cripta is None:
        mediciones.append(Measurement("Cripta publicada más grande", None, f"no se midió: {motivo}"))
    else:
        mapa = mapa_de(cripta)
        segundos, reporte = _mejor_tiempo(verificar_resolubilidad, mapa, cripta, repeticiones=5)
        mediciones.append(Measurement(
            f"Cripta publicada más grande ({cripta['id']})", segundos,
            f"{len(cripta['salas'])} salas; límite de §6.1: 0.2 s; resoluble: "
            f"{'sí' if reporte.es_resoluble else 'no'}"))
    return mediciones


def main():
    print(f"Python {__import__('sys').version.split()[0]}\n")
    for medicion in run():
        if medicion.seconds is None:
            print(f"{medicion.name}: {medicion.detail}")
        else:
            print(f"{medicion.name}: {medicion.seconds:.4f} s  ({medicion.detail})")


if __name__ == "__main__":
    main()
