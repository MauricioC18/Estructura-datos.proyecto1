# Contrato: ubicación de llaves

Formatos que el programa lee y escribe para la ubicación de llaves. El contrato HTTP de referencia es `cripta/docs/contrato/openapi-1.1.0.json` (esquemas `LlavesResponse` y `KeyLocation`).

## 1. Servicio

`GET /v1/criptas/{id_cripta}/llaves`, con el encabezado `X-Cripta-Client-Id` como el resto de las solicitudes. Cuenta como una solicitud del presupuesto, y cada reintento tras HTTP 429 cuenta aparte.

```json
{
  "llaves": [
    { "id": "itm_llave_bronce", "sala": 4 },
    { "id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203" }
  ]
}
```

Obligatorios: `llaves`; en cada entrada, `id` y `sala`. `enemigo` es opcional y puede venir en `null`. El esquema de la entrada no prohíbe campos adicionales.

## 2. Operación del contrato de fuentes de datos

`ubicacion_de_llaves(id_cripta)` devuelve el cuerpo JSON de la respuesta anterior, sin interpretarlo.

- Fuente HTTP: la ruta del punto 1.
- Fuente offline: el archivo del punto 3. Si no existe, lanza `UbicacionDeLlavesNoDisponible` (subclase de `ErrorFuenteDatos`).
- Cualquier otra falla se informa con `ErrorFuenteDatos` (o `PresupuestoAgotado`), con la operación que falló.

## 3. Paquete offline

`<carpeta>/criptas/<id_cripta>/llaves.json`: la respuesta del servicio tal cual. Lo escribe la herramienta `tools/descargar_datos_offline.py`.

## 4. Copia en disco de la partida

`cache_cripta/<id_cripta>/llaves.json`: la respuesta del servicio tal cual. Se escribe de forma atómica y se borra junto con el resto de la copia cuando cambia la versión de la cripta.

## 5. Reporte final

Una línea propia:

```text
Ubicación de llaves: descargada del servicio | recuperada de disco | leída del paquete offline | no disponible
```
