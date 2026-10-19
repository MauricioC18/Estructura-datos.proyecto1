"""
Datos reales de cripta-01 (descargados del API el 13/10/2026) para usar en
las pruebas sin depender de la carpeta datos_offline.

El código del programa nunca debe depender de estos datos (§9): solo las
pruebas los usan.
"""

VERSION_CATALOGO_REAL = "be68d322d2f5"

GENERALES_CRIPTA_01 = {
    "id": "cripta-01", "version": "fd58f7743b9e", "salas_total": 6, "paginas": 1,
    "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 6,
    "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 9, "inventario_max": 10,
    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100},
}

LISTA_DE_CRIPTAS = {"criptas": [{"id": "cripta-01", "nombre": "Osario menor", "salas": 6, "dificultad": 1}]}

FICHAS_CRIPTA_01 = [
    {"id": "itm_antorcha", "nombre": "Antorcha", "clase": "antorcha", "peso": 1, "valor": 5, "duracion": 2000},
    {"id": "ent_rata_gigante", "nombre": "Rata gigante", "clase": "enemigo", "vida_max": 12, "ataque": 5,
     "defensa": 1, "velocidad": 150, "comportamiento": "rastreador", "suelta": ["itm_pocion_menor"]},
    {"id": "itm_daga_oxidada", "nombre": "Daga oxidada", "clase": "arma", "peso": 2, "valor": 15, "ataque_bonus": 3},
    {"id": "trp_dardos", "nombre": "Dardos en la pared", "clase": "trampa", "daño": 4, "rearme": 300},
    {"id": "itm_llave_bronce", "nombre": "Llave de bronce", "clase": "llave", "peso": 1, "valor": 0,
     "abre": "puerta_2_7"},
    {"id": "itm_coraza_cuero", "nombre": "Coraza de cuero", "clase": "armadura", "peso": 4, "valor": 20,
     "defensa_bonus": 2},
    {"id": "ent_guardian_oseo", "nombre": "Guardián óseo", "clase": "enemigo", "vida_max": 20, "ataque": 7,
     "defensa": 3, "velocidad": 90, "comportamiento": "guardián"},
    {"id": "itm_llave_negra", "nombre": "Llave negra", "clase": "llave", "peso": 1, "valor": 0,
     "abre": "puerta_salida"},
    {"id": "itm_pocion_menor", "nombre": "Poción menor", "clase": "pocion", "peso": 1, "valor": 10, "cura": 8},
    {"id": "itm_pergamino_retroceso", "nombre": "Pergamino de retroceso", "clase": "pergamino_retroceso",
     "peso": 1, "valor": 40},
    {"id": "itm_antidoto", "nombre": "Antídoto", "clase": "antidoto", "peso": 1, "valor": 12},
]

SALAS_CRIPTA_01 = [
    {"id": 1, "nombre": "Entrada derruida", "salidas": {"N": {"sala": 2}}},
    {"id": 2, "nombre": "Pasillo de las urnas", "salidas": {
        "S": {"sala": 1}, "N": {"sala": 3},
        "E": {"sala": 5, "cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 500}}},
    {"id": 3, "nombre": "Cripta baja", "salidas": {"S": {"sala": 2}, "N": {"sala": 4}}},
    {"id": 4, "nombre": "Osario profundo", "salidas": {
        "S": {"sala": 3}, "E": {"sala": 6, "cerrada": True, "llave": "itm_llave_negra"}}},
    {"id": 5, "nombre": "Nicho sellado", "salidas": {"O": {"sala": 2}}},
    {"id": 6, "nombre": "Salida", "salidas": {"O": {"sala": 4}}},
]

CONTENIDO_CRIPTA_01 = [
    {"sala": 1, "enemigos": [], "objetos": ["itm_antorcha"], "trampas": []},
    {"sala": 2, "enemigos": [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": 12},
                             {"instancia": "e-202", "tipo": "ent_rata_gigante", "vida": 12}],
     "objetos": ["itm_daga_oxidada"], "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}]},
    {"sala": 3, "enemigos": [], "objetos": ["itm_llave_bronce", "itm_coraza_cuero"], "trampas": []},
    {"sala": 4, "enemigos": [{"instancia": "e-401", "tipo": "ent_guardian_oseo"}],
     "objetos": ["itm_llave_negra", "itm_pocion_menor"], "trampas": []},
    {"sala": 5, "enemigos": [], "objetos": ["itm_pergamino_retroceso", "itm_antidoto"], "trampas": []},
    {"sala": 6, "enemigos": [], "objetos": [], "trampas": []},
]


def salas_de_cuadricula(ancho, alto):
    """Esqueleto sintético: una cuadrícula de ancho x alto salas conectadas
    con sus vecinas. Sirve para probar criptas mucho más grandes."""
    salas = []
    for fila in range(alto):
        for columna in range(ancho):
            salidas = {}
            if fila > 0:
                salidas["N"] = {"sala": (fila - 1) * ancho + columna + 1}
            if fila < alto - 1:
                salidas["S"] = {"sala": (fila + 1) * ancho + columna + 1}
            if columna < ancho - 1:
                salidas["E"] = {"sala": fila * ancho + columna + 2}
            if columna > 0:
                salidas["O"] = {"sala": fila * ancho + columna}
            salas.append({"id": fila * ancho + columna + 1,
                          "nombre": f"Sala {fila},{columna}", "salidas": salidas})
    return salas
