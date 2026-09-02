"""
leer_tablero.py
----------------
Lee el estado del tablero 8x8 (ocupado / vacío) a partir de una captura,
usando el JSON generado por calibrar_tablero.py.

Idea clave: en vez de comparar contra colores de pieza concretos (que
cambian según el tema del juego: morado, verde, madera...), se mide el
BRILLO de cada celda. El fondo (vacío) es siempre oscuro y poco
contrastado; una pieza colocada siempre es notablemente más clara.

Para no tener que ajustar un umbral fijo por tema, se usa umbral
automático (Otsu) sobre las 64 muestras de brillo de la propia captura:
el algoritmo encuentra solo el punto de corte entre "grupo oscuro"
(fondo) y "grupo claro" (piezas) en cada lectura.

Uso:
    python leer_tablero.py captura.png [--umbral N] [--debug]

    --umbral N   fuerza un umbral manual de brillo (0-255) en vez de
                 Otsu automático. Útil si un tema concreto da problemas.
    --debug      guarda leer_tablero_debug.png con cada celda marcada
                 en verde (vacía) o rojo (ocupada), y su valor de brillo.
"""

import sys
import json
import argparse
import cv2
import numpy as np

CALIBRACION_PATH = "calibracion.json"
RADIO_MUESTRA = 12  # medio-lado del parche de píxeles que se analiza por celda


def brillo_celda(img, x, y, radio=RADIO_MUESTRA):
    """Brillo (mediana del canal V de HSV) de un parche centrado en (x, y)."""
    h, w = img.shape[:2]
    x0, x1 = max(0, x - radio), min(w, x + radio)
    y0, y1 = max(0, y - radio), min(h, y + radio)
    parche = img[y0:y1, x0:x1]
    hsv = cv2.cvtColor(parche, cv2.COLOR_BGR2HSV)
    return float(np.median(hsv[:, :, 2]))  # V = brillo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("captura", help="Ruta de la captura a leer")
    ap.add_argument("--umbral", type=float, default=None,
                     help="Umbral manual de brillo (si no, se usa Otsu automático)")
    ap.add_argument("--debug", action="store_true",
                     help="Guardar imagen de verificación")
    args = ap.parse_args()

    with open(CALIBRACION_PATH, encoding="utf-8") as f:
        calib = json.load(f)

    img = cv2.imread(args.captura)
    if img is None:
        raise SystemExit(f"No se pudo abrir la captura: {args.captura}")

    celdas = calib["tablero"]["celdas"]
    brillos = np.array([brillo_celda(img, c["x"], c["y"]) for c in celdas],
                        dtype=np.uint8)

    if args.umbral is not None:
        umbral = args.umbral
    else:
        # Otsu necesita la forma de imagen; se lo damos como columna de 64x1
        umbral, _ = cv2.threshold(brillos.reshape(-1, 1), 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Salvaguarda: si el contraste entre min y max es muy bajo, probablemente
    # el tablero está completamente vacío (o completamente lleno) y Otsu
    # puede inventarse un umbral arbitrario en medio del ruido.
    contraste = float(brillos.max()) - float(brillos.min())
    tablero_uniforme = contraste < 15

    tablero = np.zeros((8, 8), dtype=int)
    for c, b in zip(celdas, brillos):
        ocupada = 0 if tablero_uniforme else int(b > umbral)
        tablero[c["fila"]][c["col"]] = ocupada

    print(f"Umbral usado: {umbral:.1f}  (contraste min-max: {contraste:.1f})")
    if tablero_uniforme:
        print("Aviso: brillo casi uniforme en todas las celdas -> asumiendo tablero vacío.")
    print("\nMatriz del tablero (0 = vacío, 1 = ocupado):\n")
    for fila in tablero:
        print(" ".join(str(v) for v in fila))

    if args.debug:
        debug = img.copy()
        for c, b in zip(celdas, brillos):
            ocupada = tablero[c["fila"]][c["col"]]
            color = (0, 0, 255) if ocupada else (0, 255, 0)
            cv2.circle(debug, (c["x"], c["y"]), 6, color, -1)
            cv2.putText(debug, f"{int(b)}", (c["x"] - 14, c["y"] - 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.imwrite("leer_tablero_debug.png", debug)
        print("\nImagen de verificación guardada en leer_tablero_debug.png")

    return tablero


if __name__ == "__main__":
    main()
