"""
Frecuencia medida de las operaciones del bloque 2 (§8.1) y comparación de
estrategias para resolver el catálogo (§4.3).

Qué mide
    Recorre una cripta como lo hace el controlador: crea el mapa, carga cada
    sala antes de entrar (cargar_contenido_de_sala) y llama a
    despues_de_accion después de cada paso. Mientras tanto cuenta cuántas veces
    se ejecuta cada operación de los problemas 4.2, 4.3 y 4.4.

    No mide tiempo. Con semilla fija los conteos son exactos y dan lo mismo en
    cualquier computadora; los tiempos de cada operación están en los otros
    benchmarks del bloque 2.

Escenarios
    - cripta-01 con sus datos reales (tests/datos_cripta_01.py, descargados
      del API) y su presupuesto real de 9 solicitudes: los mismos 20 pasos al
      azar que tools.simular_partida_bloque2. La fuente cuenta las
      solicitudes igual que el API.
    - Cripta sintética: cuadrícula de 30x30 salas con 60 tipos de catálogo
      (20 enemigos, 30 objetos, 10 trampas) repartidos con semilla fija, y
      300 pasos al azar desde el centro.
      Su presupuesto es ilimitado: ahí solo se cuentan solicitudes.
    Cada uno se recorre con --cache-size 25 (el valor por defecto) y con 5,
    para forzar desalojos y lecturas de disco.

    Si una entrada a una sala lanza PresupuestoAgotado, el movimiento se
    rechaza y el jugador se queda donde estaba, como en el juego (S1).

Estrategias para resolver el catálogo (§4.3), en el mismo recorrido
    - lotes de 10 con relleno de ids conocidos (decisión D4);
    - lotes de 10 solo con lo que hace falta en ese momento;
    - una ficha por solicitud (lo que haría GET /catalogo/<id>).

Cómo se cuenta
    Se envuelven, solo durante la medición, los métodos de los objetos que
    arma RepositorioCripta. El código del programa no cambia.

Ejecutar desde la carpeta cripta/:  python -m benchmark.bench_frecuencia_bloque2
"""
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path

from adapters.fuente_datos import (
    FuenteDatos,
    PresupuestoAgotado,
    validar_ids_catalogo,
    validar_ids_salas,
    validar_numero_de_pagina,
)
from benchmark.utilidades_medicion import Measurement
from repository.gestor_catalogo import GestorCatalogo
from repository.repositorio_cripta import RepositorioCripta
from structures.tabla_hash import TablaHash
from tests.datos_cripta_01 import (
    CONTENIDO_CRIPTA_01,
    FICHAS_CRIPTA_01,
    GENERALES_CRIPTA_01,
    LISTA_DE_CRIPTAS,
    SALAS_CRIPTA_01,
    VERSION_CATALOGO_REAL,
    salas_de_cuadricula,
)

SEMILLA = 2026
PASOS_CRIPTA_01 = 20
PASOS_CRIPTA_SINTETICA = 300
LADO_DE_LA_CUADRICULA = 30
CAPACIDADES_DE_CACHE = (25, 5)


# ----------------------------------------------------------------------
# Fuentes que cuentan solicitudes como el API
# ----------------------------------------------------------------------

class FuenteCripta01(FuenteDatos):
    """Los datos reales de cripta-01, servidos desde memoria."""

    def listar_criptas(self):
        self._consumir_solicitud("listar las criptas")
        return LISTA_DE_CRIPTAS

    def datos_generales(self, id_cripta):
        self._consumir_solicitud("obtener datos generales")
        return dict(GENERALES_CRIPTA_01)

    def version_cripta(self, id_cripta):
        self._consumir_solicitud("obtener la versión de la cripta")
        return {"id": GENERALES_CRIPTA_01["id"], "version": GENERALES_CRIPTA_01["version"]}

    def pagina_salas(self, id_cripta, pagina):
        validar_numero_de_pagina(pagina)
        self._consumir_solicitud("descargar página")
        return {"pagina": 1, "total_paginas": 1, "salas": SALAS_CRIPTA_01}

    def contenido(self, id_cripta, ids_salas):
        validar_ids_salas(ids_salas)
        self._consumir_solicitud("descargar contenido")
        entradas = []
        for id_sala in ids_salas:
            for entrada in CONTENIDO_CRIPTA_01:
                if entrada["sala"] == id_sala:
                    entradas.append(entrada)
        return {"contenido": entradas}

    def catalogo(self, ids):
        validar_ids_catalogo(ids)
        self._consumir_solicitud("descargar fichas")
        return {"entidades": [ficha for ficha in FICHAS_CRIPTA_01 if ficha["id"] in ids]}

    def version_catalogo(self):
        self._consumir_solicitud("obtener la versión del catálogo")
        return {"version": VERSION_CATALOGO_REAL}

    def descripcion_del_origen(self):
        return "datos reales de cripta-01 en memoria"


class FuenteCriptaSintetica(FuenteDatos):
    """Cripta en cuadrícula con contenido y catálogo generados con semilla
    fija. Cuenta las solicitudes igual que el API real."""

    ID_CRIPTA = "cripta-sintetica"
    SALAS_POR_PAGINA = 50
    TIPOS_DE_ENEMIGO = 20
    TIPOS_DE_OBJETO = 30
    TIPOS_DE_TRAMPA = 10
    COMPORTAMIENTOS = ("guardián", "errante", "rastreador")

    def __init__(self, lado=LADO_DE_LA_CUADRICULA):
        super().__init__()
        self._lado = lado
        self._salas = salas_de_cuadricula(lado, lado)
        self._fichas_por_id = TablaHash()
        for ficha in self._fichas():
            self._fichas_por_id.insertar(ficha["id"], ficha)

    def sala_del_centro(self):
        return (self._lado // 2) * self._lado + self._lado // 2 + 1

    def listar_criptas(self):
        self._consumir_solicitud("listar las criptas")
        return {"criptas": [{"id": self.ID_CRIPTA, "nombre": "Cuadrícula sintética",
                             "salas": len(self._salas), "dificultad": 1}]}

    def datos_generales(self, id_cripta):
        self._consumir_solicitud("obtener datos generales")
        paginas = (len(self._salas) + self.SALAS_POR_PAGINA - 1) // self.SALAS_POR_PAGINA
        return {
            "id": self.ID_CRIPTA, "version": "v1", "salas_total": len(self._salas),
            "paginas": paginas, "salas_por_pagina": self.SALAS_POR_PAGINA,
            "sala_inicial": self.sala_del_centro(), "sala_salida": len(self._salas),
            "llave_salida": "itm_sint_00", "presupuesto_solicitudes": 100_000,
            "inventario_max": 10,
            "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100},
        }

    def version_cripta(self, id_cripta):
        self._consumir_solicitud("obtener la versión de la cripta")
        return {"id": self.ID_CRIPTA, "version": "v1"}

    def pagina_salas(self, id_cripta, pagina):
        validar_numero_de_pagina(pagina)
        self._consumir_solicitud("descargar página")
        total = (len(self._salas) + self.SALAS_POR_PAGINA - 1) // self.SALAS_POR_PAGINA
        inicio = (pagina - 1) * self.SALAS_POR_PAGINA
        return {"pagina": pagina, "total_paginas": total,
                "salas": self._salas[inicio:inicio + self.SALAS_POR_PAGINA]}

    def contenido(self, id_cripta, ids_salas):
        validar_ids_salas(ids_salas)
        self._consumir_solicitud("descargar contenido")
        return {"contenido": [self._contenido_de_la_sala(id_sala) for id_sala in ids_salas]}

    def catalogo(self, ids):
        validar_ids_catalogo(ids)
        self._consumir_solicitud("descargar fichas")
        fichas = []
        for id_ficha in ids:
            ficha = self._fichas_por_id.obtener(id_ficha)
            if ficha is not None:
                fichas.append(ficha)
        return {"entidades": fichas}

    def version_catalogo(self):
        self._consumir_solicitud("obtener la versión del catálogo")
        return {"version": "cat-sintetico"}

    def descripcion_del_origen(self):
        return "cripta sintética en memoria"

    def _contenido_de_la_sala(self, id_sala):
        azar = random.Random(SEMILLA * 100_003 + id_sala)
        enemigos = []
        for posicion in range(azar.randint(0, 2)):
            enemigos.append({"instancia": f"e-{id_sala}-{posicion}",
                             "tipo": f"ent_sint_{azar.randrange(self.TIPOS_DE_ENEMIGO):02d}"})
        objetos = []
        for _ in range(azar.randint(0, 2)):
            objetos.append(f"itm_sint_{azar.randrange(self.TIPOS_DE_OBJETO):02d}")
        trampas = []
        if azar.random() < 0.2:
            trampas.append({"instancia": f"t-{id_sala}",
                            "tipo": f"trp_sint_{azar.randrange(self.TIPOS_DE_TRAMPA):02d}"})
        return {"sala": id_sala, "enemigos": enemigos, "objetos": objetos, "trampas": trampas}

    def _fichas(self):
        for numero in range(self.TIPOS_DE_ENEMIGO):
            suelta = [f"itm_sint_{(numero * 7) % self.TIPOS_DE_OBJETO:02d}"] if numero % 2 == 0 else None
            yield {"id": f"ent_sint_{numero:02d}", "nombre": f"Enemigo {numero}", "clase": "enemigo",
                   "vida_max": 10, "ataque": 3, "defensa": 1, "velocidad": 100,
                   "comportamiento": self.COMPORTAMIENTOS[numero % 3], "suelta": suelta}
        for numero in range(self.TIPOS_DE_OBJETO):
            yield {"id": f"itm_sint_{numero:02d}", "nombre": f"Arma {numero}", "clase": "arma",
                   "peso": 1 + numero % 5, "valor": numero, "ataque_bonus": 1 + numero % 3}
        for numero in range(self.TIPOS_DE_TRAMPA):
            yield {"id": f"trp_sint_{numero:02d}", "nombre": f"Trampa {numero}", "clase": "trampa",
                   "daño": 2, "rearme": 300}


# ----------------------------------------------------------------------
# Estrategias para resolver el catálogo (§4.3)
# ----------------------------------------------------------------------

class CatalogoLotesSinRelleno(GestorCatalogo):
    """Alternativa: cada lote lleva solo los ids que hacen falta en ese momento."""

    def _completar_lote_con_conocidos(self, lote):
        return None


class CatalogoUnaFichaPorSolicitud(CatalogoLotesSinRelleno):
    """Alternativa: una solicitud por cada ficha que falte."""

    def asegurar_fichas(self, ids):
        for id_ficha in ids:
            super().asegurar_fichas([id_ficha])


ESTRATEGIAS_DE_CATALOGO = (
    ("lotes de 10 con relleno (decisión)", GestorCatalogo),
    ("lotes de 10 sin relleno", CatalogoLotesSinRelleno),
    ("una ficha por solicitud", CatalogoUnaFichaPorSolicitud),
)


# ----------------------------------------------------------------------
# Conteo
# ----------------------------------------------------------------------

class Contador:
    def __init__(self):
        self.llamadas = 0
        self.con_resultado = 0


def contar_llamadas(objeto, nombre_del_metodo):
    """Reemplaza el método del objeto por uno que cuenta sus llamadas y
    cuántas devolvieron algo distinto de None o False."""
    contador = Contador()
    original = getattr(objeto, nombre_del_metodo)

    def metodo_que_cuenta(*argumentos):
        contador.llamadas += 1
        resultado = original(*argumentos)
        if resultado is not None and resultado is not False:
            contador.con_resultado += 1
        return resultado

    setattr(objeto, nombre_del_metodo, metodo_que_cuenta)
    return contador


@dataclass
class ResultadoDelRecorrido:
    escenario: str
    capacidad: int
    estrategia: str
    acciones: int
    consultas_de_disponibilidad: int
    busquedas_en_memoria: int
    lecturas_de_memoria: int
    aciertos_en_memoria: int
    inserciones_en_memoria: int
    desalojos: int
    exceso_maximo_sobre_el_tope: int
    busquedas_en_el_indice: int
    lecturas_de_disco: int
    revisiones_de_precarga: int
    movimientos_rechazados: int
    lotes_de_contenido: int
    salas_descargadas: int
    esperas_en_la_puerta: int
    lotes_de_catalogo: int
    fichas_descargadas: int
    fallos_de_cache: int
    solicitudes: int


def recorrer(fuente, pasos, sala_inicial=None, capacidad=25, clase_de_catalogo=GestorCatalogo,
             escenario="", estrategia=""):
    """Recorre la cripta al azar contando operaciones. Usa una carpeta de
    caché nueva, así que es siempre un arranque en frío."""
    with tempfile.TemporaryDirectory() as carpeta:
        enemigos = []
        estado = Contador()  # estado.llamadas guarda la sala actual

        repositorio = RepositorioCripta(fuente, Path(carpeta) / "cache", capacidad,
                                        lambda: ids_en_uso(repositorio, mapa_actual, enemigos, estado))
        original = repositorio._gestor_catalogo
        repositorio._gestor_catalogo = clase_de_catalogo(original._fuente, original._almacen,
                                                         original._cache)
        gestor = repositorio._gestor_catalogo
        consultas = contar_llamadas(gestor, "_esta_disponible")
        busquedas_en_memoria = contar_llamadas(gestor._cache, "contiene_ficha")
        lecturas_de_memoria = contar_llamadas(gestor._cache, "obtener_ficha")
        inserciones = contar_llamadas(gestor._cache, "agregar_ficha")
        busquedas_en_indice = contar_llamadas(gestor._almacen, "contiene_ficha")
        lecturas_de_disco = contar_llamadas(gestor._almacen, "leer_ficha")

        mapa_actual = []
        repositorio.empezar_conteo_de_partida()
        id_cripta = repositorio.listar_criptas()[0]["id"]
        datos = repositorio.iniciar_partida(id_cripta)
        revisiones = contar_llamadas(repositorio._gestor_contenido, "precargar_alrededor_de")
        mapa = repositorio.crear_mapa()
        mapa_actual.append(mapa)
        actual = datos.sala_inicial if sala_inicial is None else sala_inicial
        estado.llamadas = actual
        enemigos.extend(repositorio.cargar_contenido_de_sala(mapa.room(actual)))

        azar = random.Random(SEMILLA)
        acciones = 0
        rechazados = 0
        for _ in range(pasos):
            salidas = mapa.room(actual).exits()
            if not salidas:
                break
            siguiente = azar.choice(salidas).destination
            try:
                enemigos.extend(repositorio.cargar_contenido_de_sala(mapa.room(siguiente)))
            except PresupuestoAgotado:
                rechazados += 1  # el movimiento se rechaza sin consumir tiempo (S1)
                continue
            actual = siguiente
            estado.llamadas = actual
            acciones += 1
            repositorio.despues_de_accion(actual)

        reporte = repositorio.reporte_de_red()
        estadisticas = gestor.estadisticas()
        return ResultadoDelRecorrido(
            escenario, capacidad, estrategia, acciones,
            consultas.llamadas, busquedas_en_memoria.llamadas,
            lecturas_de_memoria.llamadas, lecturas_de_memoria.con_resultado,
            inserciones.llamadas, reporte.desalojos_de_memoria,
            estadisticas.exceso_maximo_sobre_capacidad,
            busquedas_en_indice.llamadas, lecturas_de_disco.llamadas,
            # + 1: la precarga de iniciar_partida, que ocurre antes de empezar a contar.
            revisiones.llamadas + 1, rechazados,
            reporte.lotes_de_contenido, reporte.salas_descargadas, reporte.esperas_en_la_puerta,
            reporte.lotes_de_catalogo, reporte.fichas_descargadas, reporte.fallos_de_cache,
            reporte.solicitudes_realizadas,
        )


def ids_en_uso(repositorio, mapa_actual, enemigos, estado):
    """Lo mismo que cuenta el controlador del juego: enemigos vivos y los
    objetos y trampas de la sala actual (aquí el jugador no lleva inventario)."""
    if not mapa_actual:
        return TablaHash()
    sala = mapa_actual[0].room(estado.llamadas)
    return repositorio.ids_en_uso(enemigos, sala.floor_items, sala.traps)


# ----------------------------------------------------------------------
# Ejecución
# ----------------------------------------------------------------------

def escenarios():
    """(nombre, función que crea la fuente, pasos, sala inicial)."""
    yield (f"cripta-01 real (presupuesto 9), {PASOS_CRIPTA_01} pasos",
           FuenteCripta01, PASOS_CRIPTA_01, None)
    lado = LADO_DE_LA_CUADRICULA
    yield (f"cripta sintética {lado}x{lado} ({lado * lado} salas, 60 tipos), "
           f"{PASOS_CRIPTA_SINTETICA} pasos",
           lambda: FuenteCriptaSintetica(lado), PASOS_CRIPTA_SINTETICA, None)


def ejecutar_frecuencias():
    resultados = []
    for nombre, crear_fuente, pasos, sala_inicial in escenarios():
        for capacidad in CAPACIDADES_DE_CACHE:
            resultados.append(recorrer(crear_fuente(), pasos, sala_inicial, capacidad,
                                       escenario=nombre, estrategia=ESTRATEGIAS_DE_CATALOGO[0][0]))
    return resultados


def ejecutar_estrategias():
    resultados = []
    for nombre, crear_fuente, pasos, sala_inicial in escenarios():
        for nombre_estrategia, clase in ESTRATEGIAS_DE_CATALOGO:
            resultados.append(recorrer(crear_fuente(), pasos, sala_inicial, 25, clase,
                                       escenario=nombre, estrategia=nombre_estrategia))
    return resultados


def _por_accion(total, acciones):
    return total / acciones if acciones else 0.0


def lineas_de_frecuencia(resultado):
    r = resultado
    return [
        f"{r.escenario}, --cache-size {r.capacidad}: {r.acciones} acciones del jugador, "
        f"{r.movimientos_rechazados} movimientos rechazados por presupuesto",
        f"  4.3 consultas de disponibilidad (¿memoria o disco?): {r.consultas_de_disponibilidad} "
        f"({_por_accion(r.consultas_de_disponibilidad, r.acciones):.1f} por acción)",
        f"  4.4 búsquedas en memoria (TablaHash de la caché): {r.busquedas_en_memoria} "
        f"({_por_accion(r.busquedas_en_memoria, r.acciones):.1f} por acción)",
        f"  4.4 lecturas de fichas desde memoria: {r.lecturas_de_memoria} "
        f"(aciertos {r.aciertos_en_memoria})",
        f"  4.4 inserciones en memoria: {r.inserciones_en_memoria}; desalojos: {r.desalojos}; "
        f"exceso máximo sobre el tope: {r.exceso_maximo_sobre_el_tope}",
        f"  4.4 búsquedas binarias en el índice de disco: {r.busquedas_en_el_indice}; "
        f"lecturas de disco: {r.lecturas_de_disco}",
        f"  4.2 revisiones de precarga: {r.revisiones_de_precarga}; lotes de contenido: "
        f"{r.lotes_de_contenido} ({r.salas_descargadas} salas); esperas en la puerta: "
        f"{r.esperas_en_la_puerta}",
        f"  4.3 lotes de catálogo: {r.lotes_de_catalogo} ({r.fichas_descargadas} fichas); "
        f"fallos de caché: {r.fallos_de_cache}; solicitudes en total: {r.solicitudes}",
    ]


def imprimir(frecuencias, estrategias):
    print("Frecuencia de las operaciones del bloque 2 (arranque en frío)")
    for resultado in frecuencias:
        print()
        for linea in lineas_de_frecuencia(resultado):
            print(linea)
    print()
    print("Resolución del catálogo (§4.3): solicitudes de catálogo en el mismo recorrido")
    escenario_actual = None
    for r in estrategias:
        if r.escenario != escenario_actual:
            escenario_actual = r.escenario
            print()
            print(r.escenario)
        print(f"  {r.estrategia:>36} | {r.lotes_de_catalogo:>4} solicitudes de catálogo | "
              f"{r.solicitudes:>4} en total | {r.acciones:>3} movimientos hechos, "
              f"{r.movimientos_rechazados} rechazados por presupuesto")


def run():
    """Mediciones para el ejecutor de --bench. Son conteos: seconds es None."""
    mediciones = []
    for r in ejecutar_frecuencias():
        mediciones.append(Measurement(
            f"4.2-4.4 frecuencia: {r.escenario}, caché {r.capacidad}",
            None,
            f"{r.acciones} acciones, {r.movimientos_rechazados} rechazadas; por acción: "
            f"{_por_accion(r.consultas_de_disponibilidad, r.acciones):.1f} consultas de "
            f"disponibilidad, {_por_accion(r.busquedas_en_memoria, r.acciones):.1f} búsquedas en "
            f"memoria; total: {r.inserciones_en_memoria} inserciones, {r.desalojos} desalojos, "
            f"{r.lecturas_de_disco} lecturas de disco, {r.lotes_de_contenido} lotes de contenido, "
            f"{r.lotes_de_catalogo} lotes de catálogo",
        ))
    for r in ejecutar_estrategias():
        mediciones.append(Measurement(
            f"4.3 catálogo: {r.estrategia}, {r.escenario}",
            None,
            f"{r.lotes_de_catalogo} solicitudes de catálogo, {r.solicitudes} en total, "
            f"{r.acciones} movimientos hechos, {r.movimientos_rechazados} rechazados por presupuesto",
        ))
    return mediciones


if __name__ == "__main__":
    imprimir(ejecutar_frecuencias(), ejecutar_estrategias())
