from dataclasses import dataclass, field

from model.room import direction_index
from structures.sorting import merge_sort
from structures.tabla_hash import TablaHash

CODIGO_RESOLUBLE = 0
CODIGO_NO_RESOLUBLE = 1
CODIGO_SIN_VERIFICAR = 2

MOTIVO_DEPENDE = "depende"
MOTIVO_SIN_UBICACION = "sin_ubicacion"
MOTIVO_SIN_ACCESO = "sin_acceso"


@dataclass(frozen=True)
class LlaveEnElOrden:
    ronda: int
    ubicacion: object

    @property
    def llave(self):
        return self.ubicacion.key_id


@dataclass(frozen=True)
class PuertaDeFrontera:
    sala_origen: int
    direccion: str
    sala_destino: int
    llave: str | None


@dataclass(frozen=True)
class LlaveNoObtenible:
    llave: str
    motivo: str
    depende_de: str | None = None


@dataclass
class ReporteDeResolubilidad:
    se_pudo_verificar: bool
    es_resoluble: bool | None
    llave_salida: str | None = None
    sala_salida: int | None = None
    orden_de_llaves: list = field(default_factory=list)
    llaves_no_obtenibles: list = field(default_factory=list)
    puertas_de_la_frontera: list = field(default_factory=list)
    ubicaciones_de_la_frontera: list = field(default_factory=list)
    ciclos: list = field(default_factory=list)
    falta_puerta_hacia_la_salida: bool = False
    motivo_sin_verificar: str = ""

    def codigo_de_salida(self):
        if not self.se_pudo_verificar:
            return CODIGO_SIN_VERIFICAR
        if self.es_resoluble:
            return CODIGO_RESOLUBLE
        return CODIGO_NO_RESOLUBLE

    def lineas_de_texto(self):
        if not self.se_pudo_verificar:
            return [
                "Verificación de resolubilidad: no se pudo verificar.",
                f"Motivo: {self.motivo_sin_verificar}",
            ]
        if self.es_resoluble:
            lineas = ["Verificación de resolubilidad: la cripta es resoluble."]
            lineas.extend(self._lineas_del_orden("Orden de obtención de llaves:"))
            if self.llaves_no_obtenibles:
                lineas.append("Aviso: estas llaves no se pueden obtener:")
                lineas.extend(self._lineas_de_llaves_no_obtenibles())
            return lineas
        lineas = ["Verificación de resolubilidad: la cripta no es resoluble."]
        if self.falta_puerta_hacia_la_salida:
            lineas.append(
                f"Se puede obtener {self.llave_salida}, pero desde la región alcanzable ninguna "
                f"puerta que la pida lleva a la sala de salida ({self.sala_salida})."
            )
        if self.orden_de_llaves:
            lineas.extend(self._lineas_del_orden("Llaves que sí se pueden obtener, en orden:"))
        if self.llaves_no_obtenibles:
            lineas.append("Llaves que no se pueden obtener:")
            lineas.extend(self._lineas_de_llaves_no_obtenibles())
        if self.puertas_de_la_frontera:
            lineas.append("Puertas de la frontera:")
            for puerta in self.puertas_de_la_frontera:
                lineas.append(f"  {_texto_de_puerta(puerta)}")
        if self.ubicaciones_de_la_frontera:
            lineas.append("Dónde están esas llaves:")
            for llave, ubicaciones in self.ubicaciones_de_la_frontera:
                lineas.append(f"  {llave}: {_texto_de_ubicaciones(ubicaciones)}")
        if self.ciclos:
            lineas.append("Ciclos de dependencias:")
            for ciclo in self.ciclos:
                lineas.append(f"  {_texto_de_ciclo(ciclo)}")
        return lineas

    def _lineas_del_orden(self, titulo):
        lineas = [titulo]
        for posicion, entrada in enumerate(self.orden_de_llaves, start=1):
            lineas.append(f"  {posicion}. {entrada.llave}: {_texto_de_ubicacion(entrada.ubicacion)}")
        return lineas

    def _lineas_de_llaves_no_obtenibles(self):
        lineas = []
        for llave in self.llaves_no_obtenibles:
            lineas.append(f"  {llave.llave}: {_texto_de_motivo(llave)}")
        return lineas


def reporte_sin_verificar(motivo):
    return ReporteDeResolubilidad(se_pudo_verificar=False, es_resoluble=None,
                                  motivo_sin_verificar=motivo)


def verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, ubicaciones):
    return VerificacionDeResolubilidad(
        mapa, sala_inicial, sala_salida, llave_salida, ubicaciones).resolver()


class VerificacionDeResolubilidad:

    def __init__(self, mapa, sala_inicial, sala_salida, llave_salida, ubicaciones):
        self.mapa = mapa
        self.sala_inicial = sala_inicial
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida
        self.llaves_en_sala = TablaHash()
        self.ubicaciones_de_llave = TablaHash()
        for ubicacion in ubicaciones:
            _agregar_a_la_lista(self.llaves_en_sala, ubicacion.room_id, ubicacion)
            _agregar_a_la_lista(self.ubicaciones_de_llave, ubicacion.key_id, ubicacion)
        self.ronda_de_sala = TablaHash()
        self.ronda_de_llave = TablaHash()
        self.orden = []
        self.espera = TablaHash()
        self.cerradas_sin_llave = []
        self.hay_puerta_hacia_la_salida = False
        self.salas_examinadas = 0
        self.salidas_examinadas = 0

    def resolver(self):
        self.explorar_por_rondas()
        return self.armar_reporte()

    def explorar_por_rondas(self):
        ronda = 0
        frente = [self.sala_inicial]
        self.ronda_de_sala.insertar(self.sala_inicial, 0)
        while True:
            halladas = TablaHash()
            nuevas = []
            indice = 0
            while indice < len(frente):
                sala = frente[indice]
                indice += 1
                self.salas_examinadas += 1
                for ubicacion in self.llaves_en_sala.obtener(sala, []):
                    llave = ubicacion.key_id
                    if not self.ronda_de_llave.contiene(llave) and not halladas.contiene(llave):
                        halladas.insertar(llave, True)
                        nuevas.append(llave)
                for salida in self.mapa.room(sala).exits():
                    self.examinar_salida(sala, salida, ronda, frente)
            if not nuevas:
                return
            siguiente = []
            for llave in merge_sort(nuevas):
                self.ronda_de_llave.insertar(llave, ronda)
                self.orden.append(llave)
                for puerta in self.espera.obtener(llave, []):
                    if not self.ronda_de_sala.contiene(puerta.sala_destino):
                        self.ronda_de_sala.insertar(puerta.sala_destino, ronda + 1)
                        siguiente.append(puerta.sala_destino)
                if self.espera.contiene(llave):
                    self.espera.eliminar(llave)
            ronda += 1
            frente = siguiente

    def examinar_salida(self, sala, salida, ronda, frente):
        self.salidas_examinadas += 1
        destino = salida.destination
        puerta = salida.door
        if destino == self.sala_salida and puerta.key_id == self.llave_salida:
            self.hay_puerta_hacia_la_salida = True
        if self.ronda_de_sala.contiene(destino):
            return
        if puerta.is_open or (puerta.key_id is not None and self.ronda_de_llave.contiene(puerta.key_id)):
            self.ronda_de_sala.insertar(destino, ronda)
            frente.append(destino)
            return
        pendiente = PuertaDeFrontera(sala, salida.direction, destino, puerta.key_id)
        if puerta.key_id is None:
            self.cerradas_sin_llave.append(pendiente)
        else:
            _agregar_a_la_lista(self.espera, puerta.key_id, pendiente)

    def armar_reporte(self):
        es_resoluble = self.ronda_de_llave.contiene(self.llave_salida) and self.hay_puerta_hacia_la_salida
        reporte = ReporteDeResolubilidad(
            se_pudo_verificar=True,
            es_resoluble=es_resoluble,
            llave_salida=self.llave_salida,
            sala_salida=self.sala_salida,
            orden_de_llaves=self._orden_con_ubicaciones(),
            falta_puerta_hacia_la_salida=(
                self.ronda_de_llave.contiene(self.llave_salida) and not self.hay_puerta_hacia_la_salida
            ),
        )
        no_obtenibles = self._llaves_no_obtenibles()
        if not no_obtenibles:
            return reporte
        frontera = self._puertas_de_la_frontera()
        dependencia = self._explicar_bloqueos()
        reporte.llaves_no_obtenibles = self._motivos(no_obtenibles, dependencia)
        reporte.ciclos = self._ciclos(reporte.llaves_no_obtenibles)
        if not es_resoluble:
            reporte.puertas_de_la_frontera = frontera
            reporte.ubicaciones_de_la_frontera = self._ubicaciones_de_la_frontera(frontera)
        return reporte

    def _orden_con_ubicaciones(self):
        orden = []
        for llave in self.orden:
            ronda = self.ronda_de_llave.obtener(llave)
            elegida = None
            for ubicacion in self.ubicaciones_de_llave.obtener(llave, []):
                if self.ronda_de_sala.obtener(ubicacion.room_id) != ronda:
                    continue
                if elegida is None or _clave_de_ubicacion(ubicacion) < _clave_de_ubicacion(elegida):
                    elegida = ubicacion
            orden.append(LlaveEnElOrden(ronda, elegida))
        return orden

    def _llaves_no_obtenibles(self):
        vistas = TablaHash()
        llaves = []
        for llave in self.ubicaciones_de_llave.claves():
            self._anotar_no_obtenible(llave, vistas, llaves)
        for id_sala in self.mapa.room_ids():
            for salida in self.mapa.room(id_sala).exits():
                if salida.door.key_id is not None:
                    self._anotar_no_obtenible(salida.door.key_id, vistas, llaves)
        return merge_sort(llaves)

    def _anotar_no_obtenible(self, llave, vistas, llaves):
        if self.ronda_de_llave.contiene(llave) or vistas.contiene(llave):
            return
        vistas.insertar(llave, True)
        llaves.append(llave)

    def _puertas_de_la_frontera(self):
        puertas = list(self.cerradas_sin_llave)
        for llave in self.espera.claves():
            puertas.extend(self.espera.obtener(llave))
        alcanzan_fuera = []
        for puerta in puertas:
            if not self.ronda_de_sala.contiene(puerta.sala_destino):
                alcanzan_fuera.append(puerta)
        return merge_sort(alcanzan_fuera, key=_clave_de_puerta)

    def _explicar_bloqueos(self):
        guardia_de_sala = TablaHash()
        dependencia = TablaHash()
        abiertas = TablaHash()
        en_monticulo = TablaHash()
        monticulo = MonticuloDeLlaves()
        for llave in self.espera.claves():
            self._encolar_llave(llave, monticulo, en_monticulo)
        while not monticulo.esta_vacio():
            llave = monticulo.sacar()
            abiertas.insertar(llave, True)
            for puerta in merge_sort(self.espera.obtener(llave, []), key=_clave_de_puerta):
                if self._ya_visitada(puerta.sala_destino, guardia_de_sala):
                    continue
                self._recorrer_custodiada(puerta.sala_destino, llave, guardia_de_sala, dependencia,
                                          abiertas, monticulo, en_monticulo)
        return dependencia

    def _recorrer_custodiada(self, inicio, guardia, guardia_de_sala, dependencia, abiertas,
                             monticulo, en_monticulo):
        guardia_de_sala.insertar(inicio, guardia)
        cola = [inicio]
        indice = 0
        while indice < len(cola):
            sala = cola[indice]
            indice += 1
            self.salas_examinadas += 1
            guardia_actual = guardia_de_sala.obtener(sala)
            for ubicacion in self.llaves_en_sala.obtener(sala, []):
                if not dependencia.contiene(ubicacion.key_id):
                    dependencia.insertar(ubicacion.key_id, guardia_actual)
            for salida in self.mapa.room(sala).exits():
                self.salidas_examinadas += 1
                destino = salida.destination
                if self._ya_visitada(destino, guardia_de_sala):
                    continue
                llave_de_la_puerta = salida.door.key_id
                if salida.door.is_open or (
                        llave_de_la_puerta is not None and self.ronda_de_llave.contiene(llave_de_la_puerta)):
                    guardia_de_sala.insertar(destino, guardia_actual)
                    cola.append(destino)
                elif llave_de_la_puerta is None:
                    continue
                elif abiertas.contiene(llave_de_la_puerta):
                    guardia_de_sala.insertar(destino, llave_de_la_puerta)
                    cola.append(destino)
                else:
                    _agregar_a_la_lista(self.espera, llave_de_la_puerta,
                                        PuertaDeFrontera(sala, salida.direction, destino, llave_de_la_puerta))
                    self._encolar_llave(llave_de_la_puerta, monticulo, en_monticulo)

    def _ya_visitada(self, sala, guardia_de_sala):
        return self.ronda_de_sala.contiene(sala) or guardia_de_sala.contiene(sala)

    def _encolar_llave(self, llave, monticulo, en_monticulo):
        if en_monticulo.contiene(llave):
            return
        en_monticulo.insertar(llave, True)
        tiene_ubicacion = 1 if self.ubicaciones_de_llave.contiene(llave) else 0
        monticulo.meter((tiene_ubicacion, llave))

    def _motivos(self, no_obtenibles, dependencia):
        motivos = []
        for llave in no_obtenibles:
            if not self.ubicaciones_de_llave.contiene(llave):
                motivos.append(LlaveNoObtenible(llave, MOTIVO_SIN_UBICACION))
            elif dependencia.contiene(llave):
                motivos.append(LlaveNoObtenible(llave, MOTIVO_DEPENDE, dependencia.obtener(llave)))
            else:
                motivos.append(LlaveNoObtenible(llave, MOTIVO_SIN_ACCESO))
        return motivos

    def _ciclos(self, motivos):
        depende_de = TablaHash()
        for motivo in motivos:
            if motivo.motivo == MOTIVO_DEPENDE:
                depende_de.insertar(motivo.llave, motivo.depende_de)
        estado = TablaHash()
        ciclos = []
        for motivo in motivos:
            if estado.contiene(motivo.llave):
                continue
            camino = []
            posicion_en_camino = TablaHash()
            actual = motivo.llave
            while actual is not None and not estado.contiene(actual):
                estado.insertar(actual, True)
                posicion_en_camino.insertar(actual, len(camino))
                camino.append(actual)
                actual = depende_de.obtener(actual)
            if actual is not None and posicion_en_camino.contiene(actual):
                ciclos.append(_rotar_al_menor(camino[posicion_en_camino.obtener(actual):]))
        return merge_sort(ciclos, key=lambda ciclo: ciclo[0])

    def _ubicaciones_de_la_frontera(self, frontera):
        vistas = TablaHash()
        llaves = []
        for puerta in frontera:
            if puerta.llave is not None and not vistas.contiene(puerta.llave):
                vistas.insertar(puerta.llave, True)
                llaves.append(puerta.llave)
        resultado = []
        for llave in merge_sort(llaves):
            ubicaciones = merge_sort(self.ubicaciones_de_llave.obtener(llave, []), key=_clave_de_ubicacion)
            resultado.append((llave, ubicaciones))
        return resultado


class MonticuloDeLlaves:

    def __init__(self):
        self._elementos = []

    def esta_vacio(self):
        return not self._elementos

    def meter(self, elemento):
        self._elementos.append(elemento)
        hijo = len(self._elementos) - 1
        while hijo > 0:
            padre = (hijo - 1) // 2
            if self._elementos[padre] <= self._elementos[hijo]:
                break
            self._elementos[padre], self._elementos[hijo] = self._elementos[hijo], self._elementos[padre]
            hijo = padre

    def sacar(self):
        raiz = self._elementos[0]
        ultimo = self._elementos.pop()
        if self._elementos:
            self._elementos[0] = ultimo
            padre = 0
            while True:
                izquierdo = 2 * padre + 1
                menor = padre
                if izquierdo < len(self._elementos) and self._elementos[izquierdo] < self._elementos[menor]:
                    menor = izquierdo
                derecho = izquierdo + 1
                if derecho < len(self._elementos) and self._elementos[derecho] < self._elementos[menor]:
                    menor = derecho
                if menor == padre:
                    break
                self._elementos[padre], self._elementos[menor] = self._elementos[menor], self._elementos[padre]
                padre = menor
        return raiz[1]


def _agregar_a_la_lista(tabla, clave, elemento):
    lista = tabla.obtener(clave)
    if lista is None:
        lista = []
        tabla.insertar(clave, lista)
    lista.append(elemento)


def _clave_de_ubicacion(ubicacion):
    return (ubicacion.room_id, ubicacion.enemy_id or "")


def _clave_de_puerta(puerta):
    return (puerta.sala_origen, direction_index(puerta.direccion))


def _rotar_al_menor(ciclo):
    menor = 0
    for indice in range(1, len(ciclo)):
        if ciclo[indice] < ciclo[menor]:
            menor = indice
    return ciclo[menor:] + ciclo[:menor]


def _texto_de_ubicacion(ubicacion):
    if ubicacion.enemy_id is not None:
        return f"la suelta {ubicacion.enemy_id}, que inicia en la sala {ubicacion.room_id}"
    return f"sala {ubicacion.room_id}"


def _texto_de_ubicaciones(ubicaciones):
    if not ubicaciones:
        return "no tiene ubicación"
    textos = []
    for ubicacion in ubicaciones:
        textos.append(_texto_de_ubicacion(ubicacion))
    return "; ".join(textos)


def _texto_de_puerta(puerta):
    destino = f"sala {puerta.sala_origen} (salida {puerta.direccion}) hacia la sala {puerta.sala_destino}"
    if puerta.llave is None:
        return f"{destino}: cerrada y sin llave"
    return f"{destino}: pide {puerta.llave}"


def _texto_de_motivo(llave):
    if llave.motivo == MOTIVO_SIN_UBICACION:
        return "no tiene ubicación"
    if llave.motivo == MOTIVO_SIN_ACCESO:
        return "está en una zona a la que no lleva ninguna salida"
    return f"depende de {llave.depende_de}"


def _texto_de_ciclo(ciclo):
    texto = " → ".join(ciclo + [ciclo[0]])
    if len(ciclo) == 1:
        return f"{texto} (está detrás de puertas que solo ella abre)"
    return texto
