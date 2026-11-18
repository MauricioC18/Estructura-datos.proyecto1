# Quickstart: validar los datos nuevos del servicio

Todos los comandos se corren desde la carpeta `cripta/`.

## 1. Pruebas de aceptación

```bash
python -m unittest tests.test_datos_nuevos_servicio -v
```

El nombre de cada prueba empieza con el requisito que cubre (por ejemplo `test_fr013_...`). Resultado esperado: todas pasan.

## 2. Pruebas de la primera parte

```bash
python -m unittest discover -s tests -t .
```

Resultado esperado: todas pasan (SC-005); en `main` eran 1010 antes de esta especificación. Las únicas pruebas que cambian son las que cuentan las solicitudes exactas de un inicio de partida, que ahora suman la consulta de llaves (FR-013).

## 3. Datos reales de la segunda parte, sin tocar `datos_offline/`

```bash
python -m tools.descargar_datos_offline --carpeta datos_offline_p2
```

Resultado esperado: además de lo de la primera parte, cada cripta queda con su `llaves.json`.

## 4. Partida offline con una cripta que tiene cazadores

```bash
python main.py --offline datos_offline_p2 --cripta cripta-06
```

Resultado esperado: la partida inicia y se puede entrar a salas con cazadores (SC-001). Al terminar, el reporte final muestra `Ubicación de llaves: leída del paquete offline` y ningún aviso de campo desconocido por `costo` ni por `rango` (SC-003).

## 5. Paquete de la primera parte

```bash
python main.py --offline --cripta cripta-01
```

Resultado esperado: la partida inicia igual que antes; el reporte final muestra `Ubicación de llaves: no disponible` y un aviso de datos (FR-016).
