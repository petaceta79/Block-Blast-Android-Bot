"""
bot.py
------
Loop principal. Mantiene el estado del tablero EN MEMORIA (nunca lo vuelve
a leer de la pantalla, ver conversación previa sobre por qué), partiendo
del contenido de tablero_estado.txt (vacío si no existe, o editable a
mano para empezar a mitad de partida). En cada iteración:

  1. Captura la pantalla.
  2. Lee las 3 piezas disponibles (leer_piezas).
  3. Resuelve con backtracking la PRIMERA combinación de orden/posiciones
     que consiga colocar las 3 piezas (no busca la de más líneas, ver
     solver.py).
  4. Ejecuta los movimientos en el móvil (mover_pieza) y actualiza el
     tablero interno en el mismo orden, para que quede sincronizado con
     lo que el solver asumió.
  5. Guarda el tablero actualizado en tablero_estado.txt SOLO si el
     usuario pulsa Ctrl+C, esperando a que termine el turno actual.
  6. Espera 1s (a que terminen animaciones) y repite.

Uso:
    python bot.py [n_iteraciones]
"""

import sys
import time
import numpy as np
import signal  # <-- Importamos signal para controlar el Ctrl+C con elegancia

from captura import capturar_pantalla
from leer_piezas import leer_piezas
from mover_pieza import mover_pieza
from solver2 import resolver, colocar
from tablero_io import cargar_tablero, guardar_tablero
import historial

ARCHIVO_CAPTURA = "captura_juego.png"
N_ITERACIONES_DEFECTO = 10
ESPERA_ENTRE_TURNOS_S = 1

# Variable global para avisar al bot de que debe parar al final del turno
detener_bot = False

def manejador_interrupcion(sig, frame):
    """
    Esta función se ejecuta mágicamente cuando pulsas Ctrl+C, 
    sin romper el bucle en el que esté Python.
    """
    global detener_bot
    if not detener_bot:
        print("\n\n[!] Ctrl+C detectado. El bot terminará de colocar las piezas de este turno, guardará el tablero y se detendrá...")
        detener_bot = True
    else:
        # Si el usuario se desespera y pulsa Ctrl+C dos veces seguidas, cerramos de golpe
        print("\n[!] Segundo Ctrl+C detectado. Forzando cierre inmediato sin guardar...")
        sys.exit(1)


def ejecutar_solucion(tablero, piezas, solucion, turno):
    """
    Ejecuta cada movimiento de la solución.
    Ya no guarda en disco aquí para ahorrar memoria/disco, todo se hace en RAM.
    """
    for indice_pieza, fila, col in solucion:
        pieza = piezas[indice_pieza]
        alto, ancho = pieza.shape
        tablero_antes = tablero

        print(f"\n  -> Pieza {indice_pieza} ({alto}x{ancho}) a (fila={fila}, col={col})")
        # Dibujar la pieza con #
        for fila_matriz in pieza:
            # Reemplaza los 1 por "#" y los 0 por un espacio vacío
            dibujo = "".join(["[#]" if valor else "   " for valor in fila_matriz])
            print(f"       {dibujo}")
            
        mover_pieza(
            indice_pieza=indice_pieza,
            filas_pieza=alto,
            cols_pieza=ancho,
            fila_destino=fila,
            col_destino=col,
        )

        tablero, lineas = colocar(tablero, pieza, fila, col)
        if lineas > 0:
            print(f"     ({lineas} línea(s) completada(s))")

        historial.registrar_movimiento(turno, indice_pieza, pieza, fila, col,
                                        tablero_antes, tablero, lineas)

        time.sleep(1)

    return tablero


def main():
    # Enganchamos nuestra función al evento de pulsar Ctrl+C (SIGINT)
    signal.signal(signal.SIGINT, manejador_interrupcion)

    n_iteraciones = int(sys.argv[1]) if len(sys.argv) > 1 else N_ITERACIONES_DEFECTO

    tablero = cargar_tablero()  # vacío por defecto, o lo que haya en tablero_estado.txt
    print("Tablero inicial:")
    print(tablero)

    for iteracion in range(1, n_iteraciones + 1):
        # Si detecta que pulsaste Ctrl+C durante la pausa anterior, rompe el bucle
        if detener_bot:
            break

        print(f"\n=== Turno {iteracion}/{n_iteraciones} ===")

        capturar_pantalla(ARCHIVO_CAPTURA)
        piezas = leer_piezas(ARCHIVO_CAPTURA)
        historial.registrar_piezas_leidas(iteracion, piezas)

        for i, p in enumerate(piezas):
            forma = f"{p.shape[0]}x{p.shape[1]}" if p.size else "vacío"
            print(f"  Pieza {i}: {forma}")

        solucion, lineas_previstas = resolver(tablero, piezas)
        if solucion is None:
            print("No hay forma de colocar las piezas actuales. Fin de partida (probablemente).")
            historial.registrar_evento(iteracion, "sin_solucion_fin_de_partida")
            break
        if not solucion:
            print("No hay piezas que colocar este turno.")
        else:
            print(f"  Combinación encontrada: {lineas_previstas} línea(s) en total")
            # Esto se ejecutará hasta el final aunque pulses Ctrl+C a medias
            tablero = ejecutar_solucion(tablero, piezas, solucion, iteracion)

        # Si pulsaste Ctrl+C mientras ponía las piezas, salimos del bucle principal
        if detener_bot:
            break

        time.sleep(ESPERA_ENTRE_TURNOS_S)

    # === ZONA DE GUARDADO FINAL ===
    # El código solo llega aquí si han acabado los turnos, si se ha quedado sin solución, 
    # o si has pulsado Ctrl+C y ha roto el bucle tras poner su última ficha.

    print("\nGuardando estado del tablero antes de salir...")
    guardar_tablero(tablero)

    if detener_bot: 
        print("Tablero guardado en tablero_estado.txt. Bot detenido con éxito.")
    else:
        print("\nBot ha finalizado todos sus turnos.")


if __name__ == "__main__":
    main()