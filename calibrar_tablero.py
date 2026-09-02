"""
calibrar_tablero.py
--------------------
Herramienta de calibración para el bot de Block Blast.

Uso:
    python calibrar_tablero.py [ruta_captura.png]

Flujo:
  PASO 1 (2 clicks): esquina superior-izquierda del tablero
                      (centro de la celda fila=0, col=0)
                      y esquina inferior-derecha del tablero
                      (centro de la celda fila=7, col=7).

  PASO 2 (3 clicks): centro de cada una de las 3 piezas de la
                      bandeja inferior, de izquierda a derecha.

  PASO 3 (2 clicks): esquina superior-izquierda y esquina inferior-derecha
                      de UN SOLO bloque de cualquier pieza de la bandeja
                      (elige uno grande y bien visible). Esto mide el
                      tamaño real en píxeles de un bloque de pieza,
                      que NO tiene por qué coincidir exactamente con el
                      tamaño de celda del tablero, y que leer_piezas.py
                      necesita para no repartir mal el ancho entre bloques.

  ESC en cualquier momento cancela sin guardar.

Salida:
  - calibracion.json      -> coordenadas de las 64 celdas, las 3 piezas,
                              y el tamaño de bloque de pieza (pitch_pieza)
  - calibracion_debug.png -> captura con la rejilla dibujada encima,
                              para verificar visualmente el resultado
"""

import sys
import json
import cv2

GRID_SIZE = 8
IMG_PATH = sys.argv[1] if len(sys.argv) > 1 else "tablero_juego.png"
JSON_PATH = "calibracion.json"
DEBUG_PATH = "calibracion_debug.png"

puntos_tablero = []   # 2 clicks
puntos_piezas = []    # 3 clicks
puntos_escala = []    # 2 clicks: esquinas de UN bloque de pieza
fase = "tablero"


def click_event(event, x, y, flags, params):
    global fase
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    if fase == "tablero":
        puntos_tablero.append((x, y))
        cv2.circle(img, (x, y), 10, (0, 255, 0), -1)
        cv2.putText(img, f"T{len(puntos_tablero)}", (x + 12, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        print(f"Tablero punto {len(puntos_tablero)}: ({x}, {y})")
        if len(puntos_tablero) == 2:
            fase = "piezas"
            print("\n--- Ahora haz click en el CENTRO de cada pieza de la bandeja "
                  "(de izquierda a derecha) ---\n")

    elif fase == "piezas":
        puntos_piezas.append((x, y))
        cv2.circle(img, (x, y), 10, (255, 0, 255), -1)
        cv2.putText(img, f"P{len(puntos_piezas)}", (x + 12, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
        print(f"Pieza {len(puntos_piezas)}: ({x}, {y})")
        if len(puntos_piezas) == 3:
            fase = "escala"
            print("\n--- Ahora haz click en la esquina SUPERIOR-IZQUIERDA de UN SOLO "
                  "bloque de cualquier pieza, y luego en su esquina INFERIOR-DERECHA "
                  "(elige un bloque grande y bien visible) ---\n")

    elif fase == "escala":
        puntos_escala.append((x, y))
        cv2.circle(img, (x, y), 8, (0, 165, 255), -1)
        cv2.putText(img, f"E{len(puntos_escala)}", (x + 12, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
        print(f"Escala punto {len(puntos_escala)}: ({x}, {y})")

    cv2.imshow("Calibracion", img)


img = cv2.imread(IMG_PATH)
if img is None:
    raise SystemExit(f"No se pudo abrir la imagen: {IMG_PATH}")

cv2.namedWindow("Calibracion", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Calibracion", img.shape[1] // 2, img.shape[0] // 2)
cv2.imshow("Calibracion", img)
cv2.setMouseCallback("Calibracion", click_event)

print("PASO 1: click en el centro de la celda SUPERIOR-IZQUIERDA (0,0)")
print("        y luego en el centro de la celda INFERIOR-DERECHA (7,7).\n")

while True:
    key = cv2.waitKey(20) & 0xFF
    if key == 27:  # ESC
        print("Cancelado, no se ha guardado nada.")
        cv2.destroyAllWindows()
        sys.exit(0)
    if len(puntos_tablero) == 2 and len(puntos_piezas) == 3 and len(puntos_escala) == 2:
        break

cv2.destroyAllWindows()

# --- Calcular el centro de las 64 celdas por interpolación lineal ---
(x1, y1), (x2, y2) = puntos_tablero
ancho_celda = (x2 - x1) / (GRID_SIZE - 1)
alto_celda = (y2 - y1) / (GRID_SIZE - 1)

celdas = []
for fila in range(GRID_SIZE):
    for col in range(GRID_SIZE):
        cx = round(x1 + col * ancho_celda)
        cy = round(y1 + fila * alto_celda)
        celdas.append({"fila": fila, "col": col, "x": cx, "y": cy})

piezas = [{"indice": i, "x": px, "y": py}
          for i, (px, py) in enumerate(puntos_piezas)]

# --- Tamaño real de un bloque de pieza (pitch), en píxeles ---
(ex1, ey1), (ex2, ey2) = puntos_escala
pitch_ancho = abs(ex2 - ex1)
pitch_alto = abs(ey2 - ey1)

calibracion = {
    "imagen_referencia": IMG_PATH,
    "resolucion": {"ancho": img.shape[1], "alto": img.shape[0]},
    "tablero": {
        "filas": GRID_SIZE,
        "columnas": GRID_SIZE,
        "esquina_sup_izq": {"x": x1, "y": y1},
        "esquina_inf_der": {"x": x2, "y": y2},
        "ancho_celda": ancho_celda,
        "alto_celda": alto_celda,
        "celdas": celdas,
    },
    "piezas_bandeja": piezas,
    "pieza_bloque": {
        "ancho": pitch_ancho,
        "alto": pitch_alto,
    },
}

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(calibracion, f, indent=2, ensure_ascii=False)

# --- Imagen de verificación con la rejilla dibujada ---
debug = cv2.imread(IMG_PATH)
for c in celdas:
    cv2.circle(debug, (c["x"], c["y"]), 6, (0, 255, 0), -1)
for p in piezas:
    cv2.circle(debug, (p["x"], p["y"]), 10, (255, 0, 255), -1)
    cv2.putText(debug, str(p["indice"]), (p["x"] + 12, p["y"]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)
cv2.rectangle(debug, (ex1, ey1), (ex2, ey2), (0, 165, 255), 2)
cv2.imwrite(DEBUG_PATH, debug)

print(f"\n¡Calibración guardada en '{JSON_PATH}'!")
print(f"Tamaño de bloque de pieza detectado: {pitch_ancho}x{pitch_alto} px")
print(f"Revisa '{DEBUG_PATH}' para confirmar que los puntos verdes caen "
      "en el centro de cada celda del tablero, y el rectángulo naranja "
      "encaja justo con un bloque de pieza.")
