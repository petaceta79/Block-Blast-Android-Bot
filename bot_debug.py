"""
bot_debug.py
------------
Reproduce visualmente, paso a paso, el historial guardado por bot.py
(historial.jsonl). Por cada movimiento dibuja dos tableros lado a lado:

    ANTES  -> estado antes de colocar, con la pieza a colocar resaltada
              en naranja sobre las celdas donde va a caer
    DESPUÉS -> estado ya colocado (y con líneas limpiadas si las hubo)

Para cada colocación real de un movimiento en el móvil, así puedes ir
avanzando/retrocediendo y comparar visualmente contra lo que ves en
pantalla, hasta encontrar el paso EXACTO donde el tablero simulado deja
de coincidir con el real.

Uso:
    python bot_debug.py                      # todos los pasos del historial
    python bot_debug.py --desde 5 --hasta 8  # solo esos turnos
    python bot_debug.py --sin-gui            # no abre ventana, solo guarda
                                              # las imágenes en debug_pasos/

Controles en la ventana:
    n / flecha derecha / espacio / enter -> paso siguiente
    p / flecha izquierda                 -> paso anterior
    g                                    -> ir a un turno concreto (se
                                             pide por consola)
    q / ESC                              -> salir
"""

import argparse
import json
import os
import numpy as np
import cv2

RUTA_HISTORIAL = "historial.jsonl"
CARPETA_SALIDA = "debug_pasos"

N = 8
CELDA_PX = 48
MARGEN = 20
GAP_ENTRE_TABLEROS = 60
ALTO_CABECERA = 90

COLOR_FONDO = (245, 245, 245)
COLOR_VACIA = (255, 255, 255)
COLOR_OCUPADA = (90, 90, 90)
COLOR_PIEZA_NUEVA = (0, 140, 255)   # naranja: celdas que la pieza está a punto de ocupar / acaba de ocupar
COLOR_LINEA_GRID = (180, 180, 180)
COLOR_TEXTO = (20, 20, 20)


def cargar_pasos(ruta=RUTA_HISTORIAL, desde=None, hasta=None):
    """Lee historial.jsonl y devuelve solo los eventos de tipo 'movimiento', en orden."""
    if not os.path.exists(ruta):
        raise SystemExit(f"No existe '{ruta}'. Deja correr bot.py al menos un turno primero.")

    pasos = []
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            evento = json.loads(linea)
            if evento["tipo"] != "movimiento":
                continue
            if desde is not None and evento["turno"] < desde:
                continue
            if hasta is not None and evento["turno"] > hasta:
                continue
            pasos.append(evento)

    if not pasos:
        raise SystemExit("No hay movimientos que mostrar con esos filtros.")
    return pasos


def _dibujar_tablero(img, origen_x, origen_y, tablero, celdas_resaltadas=None):
    """Dibuja un tablero 8x8 en img, con esquina superior-izq en (origen_x, origen_y)."""
    celdas_resaltadas = celdas_resaltadas or set()
    for f in range(N):
        for c in range(N):
            x0 = origen_x + c * CELDA_PX
            y0 = origen_y + f * CELDA_PX
            x1, y1 = x0 + CELDA_PX, y0 + CELDA_PX

            if (f, c) in celdas_resaltadas:
                color = COLOR_PIEZA_NUEVA
            elif tablero[f][c]:
                color = COLOR_OCUPADA
            else:
                color = COLOR_VACIA

            cv2.rectangle(img, (x0, y0), (x1, y1), color, -1)
            cv2.rectangle(img, (x0, y0), (x1, y1), COLOR_LINEA_GRID, 1)


def _celdas_de_la_pieza(pieza, fila, col):
    alto = len(pieza)
    ancho = len(pieza[0]) if alto else 0
    celdas = set()
    for r in range(alto):
        for c in range(ancho):
            if pieza[r][c]:
                celdas.add((fila + r, col + c))
    return celdas


def construir_imagen(paso, indice, total):
    ancho_tablero = N * CELDA_PX
    alto_tablero = N * CELDA_PX
    ancho_total = MARGEN * 2 + ancho_tablero * 2 + GAP_ENTRE_TABLEROS
    alto_total = ALTO_CABECERA + alto_tablero + MARGEN

    img = np.full((alto_total, ancho_total, 3), COLOR_FONDO, dtype=np.uint8)

    tablero_antes = paso["tablero_antes"]
    tablero_despues = paso["tablero_despues"]
    pieza = paso["pieza"]
    fila, col = paso["fila"], paso["col"]
    celdas_pieza = _celdas_de_la_pieza(pieza, fila, col)

    x_izq = MARGEN
    x_der = MARGEN + ancho_tablero + GAP_ENTRE_TABLEROS
    y_tableros = ALTO_CABECERA

    # ANTES: tablero previo + la pieza resaltada donde va a caer
    _dibujar_tablero(img, x_izq, y_tableros, tablero_antes, celdas_resaltadas=celdas_pieza)
    # DESPUÉS: tablero ya colocado y limpio; resaltamos igualmente las
    # celdas de la pieza que SIGAN ocupadas (si no se limpiaron)
    celdas_pieza_supervivientes = {(f, c) for (f, c) in celdas_pieza if tablero_despues[f][c] == 1}
    _dibujar_tablero(img, x_der, y_tableros, tablero_despues, celdas_resaltadas=celdas_pieza_supervivientes)

    cv2.putText(img, "ANTES", (x_izq, y_tableros - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_TEXTO, 2)
    cv2.putText(img, "DESPUES", (x_der, y_tableros - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_TEXTO, 2)

    alto, ancho = len(pieza), len(pieza[0]) if pieza else 0
    info = (f"Paso {indice + 1}/{total}   Turno {paso['turno']}   "
            f"Pieza {paso['indice_pieza']} ({alto}x{ancho})   "
            f"Destino (fila={fila}, col={col})   "
            f"Lineas limpiadas: {paso['lineas']}")
    cv2.putText(img, info, (MARGEN, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_TEXTO, 1)
    cv2.putText(img, "n/-> siguiente   p/<- anterior   g ir a turno   q salir",
                (MARGEN, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90, 90, 90), 1)

    return img


def guardar_todas(pasos, carpeta=CARPETA_SALIDA):
    os.makedirs(carpeta, exist_ok=True)
    for i, paso in enumerate(pasos):
        img = construir_imagen(paso, i, len(pasos))
        ruta = os.path.join(carpeta, f"paso_{i:04d}_turno{paso['turno']}_pieza{paso['indice_pieza']}.png")
        cv2.imwrite(ruta, img)
    print(f"Guardadas {len(pasos)} imágenes en '{carpeta}/'.")


def modo_interactivo(pasos):
    idx = 0
    cv2.namedWindow("Debug bot", cv2.WINDOW_NORMAL)
    while True:
        img = construir_imagen(pasos[idx], idx, len(pasos))
        cv2.imshow("Debug bot", img)
        key = cv2.waitKey(0) & 0xFF

        if key in (ord('q'), 27):
            break
        elif key in (ord('n'), ord(' '), 13, 83, 3):  # n, espacio, enter, flecha derecha (varía por SO)
            idx = min(idx + 1, len(pasos) - 1)
        elif key in (ord('p'), 81, 2):  # p, flecha izquierda
            idx = max(idx - 1, 0)
        elif key == ord('g'):
            try:
                turno_objetivo = int(input("\nIr a turno número: "))
                candidatos = [i for i, p in enumerate(pasos) if p["turno"] == turno_objetivo]
                if candidatos:
                    idx = candidatos[0]
                else:
                    print(f"No hay pasos del turno {turno_objetivo} en el rango cargado.")
            except ValueError:
                print("Número de turno no válido.")

    cv2.destroyAllWindows()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", type=int, default=None, help="turno inicial a mostrar")
    ap.add_argument("--hasta", type=int, default=None, help="turno final a mostrar")
    ap.add_argument("--sin-gui", action="store_true",
                     help="no abrir ventana interactiva, solo guardar todas las imágenes en debug_pasos/")
    args = ap.parse_args()

    pasos = cargar_pasos(desde=args.desde, hasta=args.hasta)
    print(f"{len(pasos)} movimiento(s) cargados del historial.")

    if args.sin_gui:
        guardar_todas(pasos)
    else:
        guardar_todas(pasos)  # las dejamos guardadas de paso, por si acaso
        modo_interactivo(pasos)


if __name__ == "__main__":
    main()
