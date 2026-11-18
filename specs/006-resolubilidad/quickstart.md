# Quickstart: validar la verificación de resolubilidad

Todos los comandos se corren desde la carpeta `cripta/`.

## 1. Pruebas de aceptación

```bash
python -m unittest tests.test_resolubilidad -v
```

El nombre de cada prueba empieza con el requisito que cubre (por ejemplo `test_fr012_...`), y las cuatro del Apéndice B lo dicen en su nombre (`apendice_b`). Resultado esperado: todas pasan.

## 2. Suite completa

```bash
python -m unittest discover -s tests -t .
```

Resultado esperado: todas pasan.

## 3. Medición de §5.4 y §6.1

```bash
python -m benchmark.bench_resolubilidad
```

Resultado esperado: para cada tamaño, la variante incremental examina un número de salas y salidas que crece en proporción al tamaño, la ingenua uno que crece mucho más rápido, y las dos dan el mismo reporte. Si existe `datos_offline_p2` con la ubicación de llaves, también se mide la cripta publicada más grande, que tiene que tardar menos de 0.2 s. La misma suite aparece en `python main.py --bench`.

## 4. Las banderas, cuando la especificación 005 las conecte

```bash
python main.py --offline datos_offline_p2 --verificar cripta-05
python main.py --offline datos_offline_p2 --cripta cripta-05
python main.py --offline datos_offline_p2 --cripta cripta-05 --forzar
```

Resultado esperado: el primero muestra el reporte y termina con código 1; el segundo muestra el reporte y no inicia; el tercero muestra el reporte e inicia.
