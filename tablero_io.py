"""
tablero_io.py
-------------
Permite guardar/cargar el estado del tablero (8x8) en un archivo de texto
plano, editable a mano. Sirve para:
  - Arrancar el bot a mitad de partida (editas el .txt con el estado real
    y el bot continúa desde ahí).
  - Retomar una sesión anterior sin perder el progreso.
  - Corregir a mano el estado interno si se desincroniza del real.

Formato del archivo: 8 líneas, 8 dígitos (0/1) cada una, separados por
espacios para que sea fácil de leer y editar:

    0 0 0 0 0 0 0 0
    0 0 0 0 0 0 0 0
    0 0 0 0 0 1 0 0
    ...

Si el archivo no existe, se crea vacío (todo ceros) automáticamente.
"""

import os
import numpy as np

RUTA_DEFECTO = "tablero_estado.txt"
N = 8


def _tablero_vacio():
    return np.zeros((N, N), dtype=int)


def guardar_tablero(tablero, ruta=RUTA_DEFECTO):
    with open(ruta, "w", encoding="utf-8") as f:
        for fila in tablero:
            f.write(" ".join(str(int(v)) for v in fila) + "\n")


def cargar_tablero(ruta=RUTA_DEFECTO):
    """
    Si el archivo existe, lo lee y valida que sea 8x8 con solo 0/1.
    Si no existe, crea uno vacío en esa ruta y lo devuelve.
    """
    if not os.path.exists(ruta):
        tablero = _tablero_vacio()
        guardar_tablero(tablero, ruta)
        print(f"No existía '{ruta}': creado vacío.")
        return tablero

    filas = []
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            digitos = [c for c in linea if c in "01"]
            if not digitos:
                continue  # ignora líneas en blanco / comentarios sueltos
            filas.append([int(d) for d in digitos])

    if len(filas) != N or any(len(fila) != N for fila in filas):
        raise ValueError(
            f"'{ruta}' no tiene el formato esperado (8 filas x 8 valores 0/1). "
            f"Se encontraron {len(filas)} filas."
        )

    tablero = np.array(filas, dtype=int)
    if not np.all((tablero == 0) | (tablero == 1)):
        raise ValueError(f"'{ruta}' contiene valores que no son 0 o 1.")

    return tablero


if __name__ == "__main__":
    t = cargar_tablero()
    print("Tablero cargado:")
    print(t)
