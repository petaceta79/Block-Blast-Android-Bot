"""
historial.py
-------------
Guarda un registro turno a turno (que NO se sobrescribe, a diferencia de
tablero_estado.txt) con las piezas leídas y cada movimiento ejecutado:
tablero antes, pieza colocada, posición, tablero después y líneas
limpiadas.

Sirve para, cuando se detecte una discrepancia en pantalla, poder mandar
el turno exacto y reproducirlo de forma aislada: colocar(tablero_antes,
pieza, fila, col) debería dar exactamente tablero_despues.

Formato: JSON Lines (un objeto JSON por línea) en historial.jsonl, fácil
de crecer sin reescribir todo el archivo cada vez y fácil de filtrar por
número de turno.
"""

import json

RUTA_HISTORIAL = "historial.jsonl"


def _matriz_a_lista(m):
    """numpy array -> lista de listas; array vacío (slot sin pieza) -> None."""
    if m is None or m.size == 0:
        return None
    return m.tolist()


def _escribir(evento):
    with open(RUTA_HISTORIAL, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")


def registrar_piezas_leidas(turno, piezas):
    """Piezas que se leyeron ese turno (antes de decidir nada)."""
    _escribir({
        "turno": turno,
        "tipo": "piezas_leidas",
        "piezas": [_matriz_a_lista(p) for p in piezas],
    })


def registrar_movimiento(turno, indice_pieza, pieza, fila, col, tablero_antes, tablero_despues, lineas):
    """Un movimiento individual ya ejecutado, con el tablero antes/después."""
    _escribir({
        "turno": turno,
        "tipo": "movimiento",
        "indice_pieza": indice_pieza,
        "pieza": _matriz_a_lista(pieza),
        "fila": fila,
        "col": col,
        "tablero_antes": tablero_antes.tolist(),
        "tablero_despues": tablero_despues.tolist(),
        "lineas": lineas,
    })


def registrar_evento(turno, mensaje):
    """Eventos sueltos (fin de partida, sin solución, etc.), para dar contexto."""
    _escribir({
        "turno": turno,
        "tipo": "evento",
        "mensaje": mensaje,
    })


if __name__ == "__main__":
    # Lectura rápida por consola: muestra los últimos N turnos registrados.
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    try:
        with open(RUTA_HISTORIAL, encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        print(f"No existe todavía '{RUTA_HISTORIAL}'.")
        raise SystemExit

    turnos_vistos = []
    for linea in reversed(lineas):
        evento = json.loads(linea)
        if evento["turno"] not in turnos_vistos:
            turnos_vistos.append(evento["turno"])
        if len(turnos_vistos) > n:
            break

    for linea in lineas:
        evento = json.loads(linea)
        if evento["turno"] in turnos_vistos:
            print(json.dumps(evento, ensure_ascii=False))
