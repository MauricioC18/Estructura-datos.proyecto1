# Interfaz de la línea de tiempo, para integrar las banderas nuevas

**Para**: quien integre las banderas de línea de comandos (Persona 4)
**De**: Carlos, capacidad `specs/003-linea-de-tiempo`
**Fecha**: 2026-11-16

El modelo ya responde consultas de instantes pasados y ya guarda la línea en el archivo de partida. Lo que falta son dos banderas, que son de integración. Esta nota es para que conectarlas sea mecánico y no haya que leer el plan completo.

## Lo que ya está hecho

- El comando en partida `historia <t>` y `historia #k`, con su impresión. Funciona y tiene pruebas.
- Una partida nueva ya lleva línea de tiempo: `build_game(...)` la crea.
- Guardar y cargar conserva la línea completa.
- `--replay` sigue funcionando igual: la consulta no es una acción del juego, así que no entra en la bitácora.

## Bandera 1: `--checkpoint-cada K`

Son las acciones del jugador entre dos copias completas del estado. Ya es un parámetro:

```python
build_game(repository, seed, player_name, in_use, copias_cada=K)
```

El valor por omisión está en `structures/linea_de_tiempo.COPIAS_CADA` y vale **50**. Está justificado con mediciones en `specs/003-linea-de-tiempo/plan.md`; si cambian el valor por omisión, hay que mover también esa justificación.

Validación: tiene que ser un entero mayor o igual que 1. `LineaDeTiempo` ya lo rechaza con `ValueError` si no lo es, así que basta con mostrar el mensaje.

## Bandera 2: `--replay partida.log --hasta <t>`

Hay que reproducir la bitácora como ya se hace y, al terminar, imprimir el resumen del instante `t` en vez de, o además de, lo que se imprime hoy. Sin instanciar la vista interactiva.

```python
from adapters.almacen_partida import reconstruir_desde_copia
from model.consulta_historia import ConsultaRechazada, consultar_instante

resumen = consultar_instante(juego, t, reconstruir_desde_copia)
```

`ConsultaRechazada` trae el mensaje ya redactado para mostrar: lo levanta cuando `t` es posterior al reloj, cuando es negativo, cuando no es entero o cuando la partida no lleva línea.

Para imprimir, `ConsoleView.show_history(resumen)` ya existe. Si para el modo sin interacción conviene otro formato, el resumen es un **dato** con atributos, no texto: `instante`, `acciones_del_jugador`, `sala`, `nombre_de_la_sala`, `vida`, `vida_maxima`, `ataque`, `defensa`, `velocidad`, `inventario`, `efectos`, `enemigos`, `mapa_conocido`, `resultado`.

## Las dos funciones de consulta

```python
from adapters.almacen_partida import reconstruir_desde_copia
from model.consulta_historia import (
    ConsultaRechazada, consultar_accion, consultar_instante,
)

consultar_instante(juego, 1500, reconstruir_desde_copia)   # por reloj
consultar_accion(juego, 10, reconstruir_desde_copia)       # por numero de accion
```

El tercer argumento es la función que sabe reconstruir una copia. Va desde afuera a propósito: el modelo no conoce el adaptador. No hay que inventarla, ya está escrita.

## Tres cosas que NO hay que hacer

1. **No llamar a la consulta dentro del ciclo de eventos.** Es una consulta del jugador, no parte del turno.
2. **No registrar la consulta en la bitácora de reproducción.** El comando ya está marcado como «no es acción de juego», así que si se respeta ese camino no hay nada que hacer.
3. **No pasar la partida viva a `reconstruir_desde_copia`.** La consulta trabaja sobre objetos nuevos; por eso no puede alterar nada.

## Aviso para todo el grupo

**El formato del archivo de partida subió a la versión 3.** Los guardados anteriores se rechazan con un mensaje claro, que es lo que pide §4.3 del enunciado. Subió dos veces en esta tanda: a 2 por el rango del cazador y a 3 por la línea de tiempo y por el costo de las salidas.

**Y un defecto que había que arreglar**: el archivo de partida **nunca guardaba el costo de las salidas**. La capacidad 001 agregó el costo al modelo y no al guardado, así que guardar y cargar devolvía todas las salidas a costo 100 en silencio. Ya está corregido. Si alguien probó guardar y cargar con costos declarados antes de hoy, lo que vio estaba mal.

## Lo que falta y es de otro

El resumen debe incluir **el mapa conocido del jugador** en ese instante, que es de la niebla de guerra (§3.3). Todavía no existe, así que el resumen informa `"todavia no implementado"` en ese campo y se construye igual, para no bloquear esta capacidad con una ajena.

Cuando exista, conectarlo es **una línea**: `_mapa_conocido_de` en `model/consulta_historia.py` lee el atributo `known_map` del juego reconstruido por duck typing. Si la niebla de guerra lo expone con otro nombre, se cambia ahí y nada más. Hay una prueba que lo comprueba: `test_el_mapa_conocido_se_lee_de_quien_lo_tenga`.
