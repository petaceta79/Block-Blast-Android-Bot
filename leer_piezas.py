"""
leer_piezas.py
---------------
Lee las 3 piezas de la bandeja inferior y devuelve la forma real de cada
una, a partir de calibracion.json.

API para usar desde otro script:

    from leer_piezas import leer_piezas
    matrices = leer_piezas("captura.png")
    # matrices es una lista de 3 arrays 2D (0/1), cada uno recortado a su
    # tamaño mínimo real (sin relleno alrededor) -> la pieza "ocupa el
    # máximo" de su propia matriz. Por ejemplo una pieza en L de 3 bloques
    # sale como una matriz 2x2, no como un 5x5 con huecos.
    # matrices[i].shape da (filas, columnas) de esa pieza.

Uso desde línea de comandos (para depurar):
    python leer_piezas.py captura.png [--debug]

CÓMO SE DETECTA (resumen, ver versiones anteriores para el porqué de cada
decisión):
  1) Recorte generoso alrededor del centro calibrado de cada pieza.
  2) Máscara "pieza vs fondo" con umbral automático (Otsu) sobre la
     distancia de color Lab -> se adapta al contraste real de cada pieza.
  3) Componentes conectados agrupados en clusters por cercanía -> aísla
     la pieza correcta de piezas vecinas o ruido.
  4) Se elige el cluster más cercano al punto de calibración (el click
     puede caer en un hueco vacío de la propia pieza).
  5) La caja de ese cluster se divide en filas/columnas usando el tamaño
     de bloque real medido en calibración (pitch), muestreando solo la
     zona CENTRAL de cada celda (con un margen/inset) para no contaminarse
     con la sombra/bisel de bloques vecinos.
"""

import json
import argparse
import cv2
import numpy as np

CALIBRACION_PATH = "calibracion.json"

MARGEN_BLOQUES = 3.2        # radio del recorte alrededor del centro, en BLOQUES de pieza (pitch)
FRACCION_OCUPADA_MIN = 0.65  # Ahora exige que el 65% de la celda tenga color sólido
INSET_CELDA = 0.35          # % de margen interior por celda que se IGNORA al medir ocupación
AREA_MINIMA_FRACCION = 0.20
GAP_CLUSTER_FRACCION = 0.65
MAX_BLOQUES_LADO = 5        # tope de seguridad para filas/columnas de una pieza


def recorte_seguro(img, cx, cy, radio_px):
    h, w = img.shape[:2]
    x0, x1 = max(0, cx - radio_px), min(w, cx + radio_px)
    y0, y1 = max(0, cy - radio_px), min(h, cy + radio_px)
    return img[y0:y1, x0:x1], (x0, y0)


def distancia_rects(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(ax0 - bx1, bx0 - ax1, 0)
    dy = max(ay0 - by1, by0 - ay1, 0)
    return (dx ** 2 + dy ** 2) ** 0.5


def distancia_punto_rect(px, py, r):
    x0, y0, x1, y1 = r
    dx = max(x0 - px, px - x1, 0)
    dy = max(y0 - py, py - y1, 0)
    return (dx ** 2 + dy ** 2) ** 0.5


def agrupar_componentes(rects, gap_max):
    n = len(rects)
    padre = list(range(n))

    def find(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    def unir(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            padre[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            if distancia_rects(rects[i], rects[j]) < gap_max:
                unir(i, j)

    clusters = {}
    for i in range(n):
        raiz = find(i)
        clusters.setdefault(raiz, []).append(i)
    return list(clusters.values())


def _leer_pieza(img, cx, cy, pitch_w, pitch_h):
    """
    Devuelve (matriz_recortada, debug_info).
    matriz_recortada: array 2D (0/1) de tamaño MÍNIMO real (filas x cols),
    sin relleno -> la pieza ocupa el 100% de su propia matriz.
    """
    radio_px = int(MARGEN_BLOQUES * max(pitch_w, pitch_h))
    crop, (ox, oy) = recorte_seguro(img, cx, cy, radio_px)
    if crop.size == 0:
        return np.zeros((0, 0), dtype=int), None

    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2Lab).astype(np.float32)
    fondo = np.median(lab.reshape(-1, 3), axis=0)
    distancia = np.linalg.norm(lab - fondo, axis=2)

    distancia_u8 = np.clip(distancia, 0, 255).astype(np.uint8)
    _, mask = cv2.threshold(distancia_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    area_minima = AREA_MINIMA_FRACCION * pitch_w * pitch_h
    etiquetas_validas = [i for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= area_minima]

    if not etiquetas_validas:
        return np.zeros((0, 0), dtype=int), {"mask": mask, "origen": (ox, oy), "caja": None}

    rects = []
    for i in etiquetas_validas:
        x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], \
                     stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        rects.append((x, y, x + w, y + h))

    gap_max = GAP_CLUSTER_FRACCION * max(pitch_w, pitch_h)
    grupos = agrupar_componentes(rects, gap_max)

    px_local, py_local = cx - ox, cy - oy
    mejor_grupo, mejor_dist = None, None
    for grupo in grupos:
        xs0 = min(rects[i][0] for i in grupo)
        ys0 = min(rects[i][1] for i in grupo)
        xs1 = max(rects[i][2] for i in grupo)
        ys1 = max(rects[i][3] for i in grupo)
        d = distancia_punto_rect(px_local, py_local, (xs0, ys0, xs1, ys1))
        if mejor_dist is None or d < mejor_dist:
            mejor_dist = d
            mejor_grupo = (grupo, (xs0, ys0, xs1, ys1))

    grupo_indices, (bx0, by0, bx1, by1) = mejor_grupo
    etiquetas_elegidas = {etiquetas_validas[i] for i in grupo_indices}
    mask_cluster = np.isin(labels, list(etiquetas_elegidas)).astype(np.uint8) * 255

    bw, bh = bx1 - bx0, by1 - by0
    num_cols = int(np.clip(round(bw / pitch_w), 1, MAX_BLOQUES_LADO))
    num_rows = int(np.clip(round(bh / pitch_h), 1, MAX_BLOQUES_LADO))

    ocupacion = np.zeros((num_rows, num_cols), dtype=int)
    inset_w = pitch_w * INSET_CELDA
    inset_h = pitch_h * INSET_CELDA
    for r in range(num_rows):
        for c in range(num_cols):
            cx0 = int(bx0 + c * pitch_w + inset_w)
            cx1 = int(bx0 + (c + 1) * pitch_w - inset_w)
            cy0 = int(by0 + r * pitch_h + inset_h)
            cy1 = int(by0 + (r + 1) * pitch_h - inset_h)
            sub = mask_cluster[max(0, cy0):cy1, max(0, cx0):cx1]
            if sub.size == 0:
                continue
            fraccion = np.mean(sub > 0)
            ocupacion[r][c] = int(fraccion > FRACCION_OCUPADA_MIN)

    # --- Recortar al mínimo real: quitar filas/columnas totalmente vacías
    # en los bordes, para que la pieza "ocupe el máximo" de la matriz que
    # se devuelve (sin huecos de relleno alrededor). ---
    filas_con_bloque = np.where(ocupacion.any(axis=1))[0]
    cols_con_bloque = np.where(ocupacion.any(axis=0))[0]
    if len(filas_con_bloque) == 0 or len(cols_con_bloque) == 0:
        matriz_final = np.zeros((0, 0), dtype=int)
    else:
        r0, r1 = filas_con_bloque[0], filas_con_bloque[-1] + 1
        c0, c1 = cols_con_bloque[0], cols_con_bloque[-1] + 1
        matriz_final = ocupacion[r0:r1, c0:c1]

    debug_info = {
        "mask": mask,
        "mask_cluster": mask_cluster,
        "origen": (ox, oy),
        "caja": (bx0, by0, bw, bh),
        "todos_los_rects": rects,
        "rects_elegidos": [rects[i] for i in grupo_indices],
        "num_filas": num_rows,
        "num_cols": num_cols,
        "pitch_w": pitch_w,
        "pitch_h": pitch_h,
    }
    return matriz_final, debug_info


def leer_piezas(ruta_captura, ruta_calibracion=CALIBRACION_PATH, devolver_debug=False):
    """
    Función pública para importar desde otro script.

    Devuelve una lista de 3 matrices numpy (0/1), una por pieza de la
    bandeja, cada una recortada a su tamaño mínimo real (la pieza ocupa
    el 100% de las celdas de su matriz -> lista para probar colocaciones
    en el tablero empezando por una esquina, sin tener que descontar
    relleno). Una pieza no detectada (slot vacío) se devuelve como
    array de shape (0, 0).

    Si devolver_debug=True, devuelve (matrices, lista_de_debug_info)
    en vez de solo matrices.
    """
    with open(ruta_calibracion, encoding="utf-8") as f:
        calib = json.load(f)

    img = cv2.imread(ruta_captura)
    if img is None:
        raise FileNotFoundError(f"No se pudo abrir: {ruta_captura}")

    if "pieza_bloque" not in calib:
        raise KeyError(
            "Falta 'pieza_bloque' en calibracion.json. Ejecuta calibrar_tablero.py "
            "(versión con fase de medición de bloque) antes de usar este script."
        )
    pitch_w = calib["pieza_bloque"]["ancho"]
    pitch_h = calib["pieza_bloque"]["alto"]

    matrices, infos = [], []
    for pieza in calib["piezas_bandeja"]:
        matriz, info = _leer_pieza(img, pieza["x"], pieza["y"], pitch_w, pitch_h)
        matrices.append(matriz)
        infos.append(info)

    if devolver_debug:
        return matrices, infos
    return matrices


def _dibujar_debug(img, calib, infos):
    debug_img = img.copy()
    for pieza, info in zip(calib["piezas_bandeja"], infos):
        if info is None or info.get("caja") is None:
            continue
        ox, oy = info["origen"]
        elegidos = set(info["rects_elegidos"])
        for rect in info["todos_los_rects"]:
            x0, y0, x1, y1 = rect
            color = (0, 255, 0) if rect in elegidos else (120, 120, 120)
            cv2.rectangle(debug_img, (ox + x0, oy + y0), (ox + x1, oy + y1), color, 1)

        bx0, by0, bw, bh = info["caja"]
        p1 = (ox + bx0, oy + by0)
        p2 = (ox + bx0 + bw, oy + by0 + bh)
        cv2.rectangle(debug_img, p1, p2, (0, 0, 255), 2)
        for c in range(1, info["num_cols"]):
            x = int(ox + bx0 + c * info["pitch_w"])
            cv2.line(debug_img, (x, p1[1]), (x, p2[1]), (0, 255, 255), 1)
        for r in range(1, info["num_filas"]):
            y = int(oy + by0 + r * info["pitch_h"])
            cv2.line(debug_img, (p1[0], y), (p2[0], y), (0, 255, 255), 1)

        inset_w = info["pitch_w"] * INSET_CELDA
        inset_h = info["pitch_h"] * INSET_CELDA
        for r in range(info["num_filas"]):
            for c in range(info["num_cols"]):
                ix0 = int(ox + bx0 + c * info["pitch_w"] + inset_w)
                ix1 = int(ox + bx0 + (c + 1) * info["pitch_w"] - inset_w)
                iy0 = int(oy + by0 + r * info["pitch_h"] + inset_h)
                iy1 = int(oy + by0 + (r + 1) * info["pitch_h"] - inset_h)
                cv2.rectangle(debug_img, (ix0, iy0), (ix1, iy1), (255, 128, 0), 1)
        cv2.circle(debug_img, (pieza["x"], pieza["y"]), 4, (255, 0, 255), -1)
    return debug_img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("captura")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    matrices, infos = leer_piezas(args.captura, devolver_debug=True)

    for i, matriz in enumerate(matrices):
        print(f"\nPieza {i} (matriz {matriz.shape[0]}x{matriz.shape[1]}, recortada al máximo):")
        if matriz.size == 0:
            print("  (no se detectó ningún bloque)")
        else:
            for fila in matriz:
                print("  " + " ".join("#" if v else "." for v in fila))

    if args.debug:
        with open(CALIBRACION_PATH, encoding="utf-8") as f:
            calib = json.load(f)
        img = cv2.imread(args.captura)
        debug_img = _dibujar_debug(img, calib, infos)
        cv2.imwrite("leer_piezas_debug.png", debug_img)
        print("\nImagen de verificación guardada en leer_piezas_debug.png")
        print("(verde = bloques elegidos, gris = descartados, naranja = zona muestreada por celda)")

    return matrices


if __name__ == "__main__":
    main()
