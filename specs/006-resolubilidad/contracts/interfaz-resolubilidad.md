# Interfaz de la verificación de resolubilidad

Lo que necesita la especificación 005 para conectar `--verificar`, `--forzar` y el reporte al iniciar. Los requisitos están en `specs/006-resolubilidad/spec.md`: FR-016 (`--forzar`), FR-017 (reporte al iniciar), FR-018 (`--verificar`), FR-019 (carga de partida guardada) y FR-020 (ubicación de llaves no disponible).

## Qué llamar

Todo está en `RepositorioCripta` (`cripta/repository/repositorio_cripta.py`):

| Llamada | Devuelve o lanza | Cuándo usarla |
| --- | --- | --- |
| `iniciar_partida(id, exigir_resolubilidad=not forzar)` | Lanza `CriptaNoResoluble` (con `.reporte`) si la cripta no es resoluble y se exige | Partida nueva |
| `reporte_de_resolubilidad()` | `ReporteDeResolubilidad`, o `None` si no se verificó | Después de iniciar, para mostrar el reporte antes de la primera acción |
| `verificar_cripta(id)` | `ReporteDeResolubilidad` | `--verificar <cripta>` |

`CriptaNoResoluble` se importa de `repository.repositorio_cripta`.

## El reporte

| Operación | Qué da |
| --- | --- |
| `lineas_de_texto()` | `list[str]` listas para mostrar, una por línea |
| `codigo_de_salida()` | `0` resoluble, `1` no resoluble, `2` no se pudo verificar (falta la ubicación de llaves) |
| `es_resoluble` | `True`, `False`, o `None` si no se pudo verificar |
| `se_pudo_verificar` | `False` solo cuando falta la ubicación de llaves |

## Cómo conectarlo

Partida nueva, con o sin `--forzar`:

```python
try:
    repository.iniciar_partida(id_cripta, exigir_resolubilidad=not argumentos.forzar)
except CriptaNoResoluble as error:
    mostrar(error.reporte.lineas_de_texto())
    return
mostrar(repository.reporte_de_resolubilidad().lineas_de_texto())
```

`--verificar <cripta>`, sin instanciar la vista:

```python
reporte = repository.verificar_cripta(id_cripta)
for linea in reporte.lineas_de_texto():
    print(linea)
sys.exit(reporte.codigo_de_salida())
```

## Tres cosas que no hay que hacer

1. **No pasar `exigir_resolubilidad=True` en `--replay`.** La reproducción nunca se detiene por la verificación (FR-016, aclaración P4). La llamada actual de `replay` ya no lo pasa.
2. **No llamar a la verificación al cargar una partida guardada.** La carga ya llama a `iniciar_partida(..., obtener_ubicacion_de_llaves=False)`; en ese caso `reporte_de_resolubilidad()` devuelve `None` y no hay nada que mostrar (FR-019).
3. **No tratar el código 2 como «no resoluble».** Si falta la ubicación de llaves, la partida inicia igual, sin `--forzar`, y el reporte dice por qué no se pudo verificar (FR-020).

## Un ejemplo de reporte

```text
Verificación de resolubilidad: la cripta no es resoluble.
Llaves que sí se pueden obtener, en orden:
  1. itm_llave_bronce: sala 2
Llaves que no se pueden obtener:
  itm_llave_hierro: depende de itm_llave_negra
  itm_llave_negra: depende de itm_llave_hierro
Puertas de la frontera:
  sala 7 (salida E) hacia la sala 22: pide itm_llave_hierro
  sala 12 (salida E) hacia la sala 24: pide itm_llave_negra
  sala 19 (salida N) hacia la sala 20: pide itm_llave_negra
Dónde están esas llaves:
  itm_llave_hierro: sala 24
  itm_llave_negra: sala 23
Ciclos de dependencias:
  itm_llave_hierro → itm_llave_negra → itm_llave_hierro
```
