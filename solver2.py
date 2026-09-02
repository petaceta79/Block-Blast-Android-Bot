"""
solver.py
---------
Backtracking completo para decidir dónde colocar las 3 piezas de un turno.

Explora TODAS las combinaciones de posiciones y todos los órdenes posibles 
(hasta 3! = 6 permutaciones) y devuelve la secuencia exacta que logra 
destruir el MAYOR número de líneas (filas + columnas).
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

def _backtrack_mejor(tablero, piezas, restantes):
    """
    Explora en profundidad TODAS las posiciones para las piezas restantes.
    Devuelve (mejor_secuencia, lineas_maximas) o None si es imposible.
    """
    if not restantes:
        return [], 0

    idx = restantes[0]
    pieza = piezas[idx]
    
    mejor_movimientos = None
    max_lineas = -1

    for (f, c) in posiciones_validas(tablero, pieza):
        nuevo_tablero, lineas = colocar(tablero, pieza, f, c)
        resto = _backtrack_mejor(nuevo_tablero, piezas, restantes[1:])
        
        if resto is not None:
            movimientos_resto, lineas_resto = resto
            lineas_totales = lineas + lineas_resto
            
            # Si esta rama rompe más líneas que nuestro récord actual, la guardamos
            if lineas_totales > max_lineas:
                max_lineas = lineas_totales
                mejor_movimientos = [(idx, f, c)] + movimientos_resto

    if mejor_movimientos is None:
        return None
    return mejor_movimientos, max_lineas

def resolver(tablero, piezas):
    """
    Punto de entrada del solver.
    Prueba todos los órdenes posibles y se queda con el mejor resultado global.
    """
    indices_validos = [i for i, p in enumerate(piezas) if p.size > 0]
    if not indices_validos:
        return [], 0

    mejor_solucion_global = None
    max_lineas_global = -1

    # Probamos en qué orden colocar las 3 piezas (ej: 0-1-2, 2-0-1, etc.)
    for orden in itertools.permutations(indices_validos):
        resultado = _backtrack_mejor(tablero, piezas, list(orden))
        
        if resultado is not None:
            solucion, lineas = resultado
            if lineas > max_lineas_global:
                max_lineas_global = lineas
                mejor_solucion_global = solucion

    if mejor_solucion_global is None:
        return None, 0  # No hay forma de colocar las 3 piezas

    return mejor_solucion_global, max_lineas_global

if __name__ == "__main__":
    tablero_vacio = np.zeros((8, 8), dtype=int)
    pieza_cuadrado = np.array([[1, 1], [1, 1]])
    pieza_linea = np.array([[1, 1, 1, 1]])
    pieza_L = np.array([[1, 0], [1, 0], [1, 1]])

    sol, lineas = resolver(tablero_vacio, [pieza_cuadrado, pieza_linea, pieza_L])
    print("Mejor Solución de ejemplo:", sol)
    print("Líneas totales limpiadas:", lineas)