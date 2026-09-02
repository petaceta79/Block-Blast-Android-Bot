"""
solver.py
---------
Backtracking simple para decidir dónde colocar las 3 piezas de un turno.

No depende de captura, calibración ni de leer_piezas: solo trabaja con
matrices numpy (0/1), tanto para el tablero como para las piezas. Esto lo
hace fácil de testear aislado y de reutilizar desde bot.py.

Complejidad: 3 piezas -> como mucho 3! = 6 órdenes distintos, y cada
pieza tiene <=64 posiciones candidatas (normalmente muchas menos por
solape/bordes). El backtracking corta en cuanto una posición no es
válida, así que en la práctica es instantáneo para un tablero 8x8.
Suficiente para este tamaño de problema sin necesitar heurísticas.
"""

import itertools
import numpy as np

N = 8


def cabe(tablero, pieza, fila, col):
    """¿La pieza cabe en (fila, col) sin salirse del tablero ni solapar?"""
    alto, ancho = pieza.shape
    if fila + alto > N or col + ancho > N:
        return False
    region = tablero[fila:fila + alto, col:col + ancho]
    return not np.any((region == 1) & (pieza == 1))


def posiciones_validas(tablero, pieza):
    """Todas las (fila, col) donde esta pieza cabe ahora mismo."""
    if pieza.size == 0:
        return []
    alto, ancho = pieza.shape
    return [
        (f, c)
        for f in range(N - alto + 1)
        for c in range(N - ancho + 1)
        if cabe(tablero, pieza, f, c)
    ]


def colocar(tablero, pieza, fila, col):
    """
    Coloca la pieza en (fila, col), limpia líneas completas y devuelve
    (nuevo_tablero, num_lineas_limpiadas). No modifica 'tablero' original.
    """
    nuevo = tablero.copy()
    alto, ancho = pieza.shape
    nuevo[fila:fila + alto, col:col + ancho] = np.maximum(
        nuevo[fila:fila + alto, col:col + ancho], pieza
    )

    filas_completas = [f for f in range(N) if nuevo[f].all()]
    cols_completas = [c for c in range(N) if nuevo[:, c].all()]
    for f in filas_completas:
        nuevo[f, :] = 0
    for c in cols_completas:
        nuevo[:, c] = 0

    return nuevo, len(filas_completas) + len(cols_completas)


def _backtrack(tablero, piezas, restantes):
    """
    restantes: lista de índices de pieza pendientes de colocar, en el
    orden en que se intentan en ESTA rama.
    Devuelve (movimientos, lineas_totales) de la PRIMERA combinación de
    posiciones que consigue colocar todas las piezas de 'restantes', o
    None si esta rama no lleva a ninguna solución completa.
    """
    if not restantes:
        return [], 0

    idx = restantes[0]
    pieza = piezas[idx]
    for (f, c) in posiciones_validas(tablero, pieza):
        nuevo_tablero, lineas = colocar(tablero, pieza, f, c)
        resto = _backtrack(nuevo_tablero, piezas, restantes[1:])
        if resto is not None:
            movimientos_resto, lineas_resto = resto
            return [(idx, f, c)] + movimientos_resto, lineas + lineas_resto

    return None


def resolver(tablero, piezas):
    """
    Punto de entrada del solver.

    tablero: array numpy 8x8 (0/1), estado actual.
    piezas: lista de hasta 3 arrays numpy (0/1), tamaño mínimo real
            (tal como los devuelve leer_piezas). Un slot vacío puede
            venir como array de shape (0, 0); se ignora.

    Devuelve (solucion, lineas_totales):
      - solucion: lista de tuplas (indice_pieza, fila, col) en el orden
        de ejecución, o None si no existe ninguna forma de colocar todas
        las piezas válidas (fin de partida).
      - lineas_totales: cuántas líneas (filas+columnas) se limpian en
        total a lo largo de esa secuencia. 0 si solucion es [] o None.

    Se queda con la PRIMERA combinación de orden/posiciones que consiga
    colocar todas las piezas, probando las permutaciones de orden (3! = 6
    como mucho) en orden hasta que una tenga solución completa. No busca
    la mejor por líneas limpiadas -> resultado más predecible y rápido.
    """
    indices_validos = [i for i, p in enumerate(piezas) if p.size > 0]
    if not indices_validos:
        return [], 0

    for orden in itertools.permutations(indices_validos):
        resultado = _backtrack(tablero, piezas, list(orden))
        if resultado is not None:
            return resultado

    return None, 0  # ninguna combinación de orden/posiciones permite colocar las 3


if __name__ == "__main__":
    # Prueba rápida con piezas de ejemplo, sin depender de captura ni calibración.
    tablero_vacio = np.zeros((8, 8), dtype=int)
    pieza_cuadrado = np.array([[1, 1], [1, 1]])
    pieza_linea = np.array([[1, 1, 1, 1]])
    pieza_L = np.array([[1, 0], [1, 0], [1, 1]])

    sol, lineas = resolver(tablero_vacio, [pieza_cuadrado, pieza_linea, pieza_L])
    print("Solución de ejemplo:", sol)
    print("Líneas totales limpiadas:", lineas)
