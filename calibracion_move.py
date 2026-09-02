import json

def cargar_calibracion(ruta="calibracion.json"):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)

def principal():
    print("=== CALIBRACIÓN POR RANURA (0, 1, 2) ===")
    calib = cargar_calibracion()
    
    ancho_celda = calib["tablero"]["ancho_celda"]
    alto_celda = calib["tablero"]["alto_celda"]
    
    # Coordenadas base de las esquinas extremas
    casilla_0_0 = next(c for c in calib["tablero"]["celdas"] if c["fila"] == 0 and c["col"] == 0)
    casilla_7_7 = next(c for c in calib["tablero"]["celdas"] if c["fila"] == 7 and c["col"] == 7)

    resultados = {}

    for indice in range(3):
        print(f"\n=========================================")
        print(f"       CALIBRANDO RANURA {indice}")
        print(f"=========================================")
        
        filas = int(input("¿Cuántas FILAS (altura en bloques) tiene la pieza?: "))
        cols = int(input("¿Cuántas COLUMNAS (ancho en bloques) tiene la pieza?: "))

        # Calculamos la distancia desde la esquina sup-izq hasta el centro de la matriz
        comp_x = (cols - 1) * (ancho_celda / 2.0)
        comp_y = (filas - 1) * (alto_celda / 2.0)

        # ---------------- PASO 1 ----------------
        print(f"\n--- PASO 1: Casilla [0][0] ---")
        print("Encaja la ESQUINA SUPERIOR IZQUIERDA en [0][0].")
        dedo_x1 = float(input("X de tu dedo (sin soltar): "))
        dedo_y1 = float(input("Y de tu dedo (sin soltar): "))
        
        # Centro real donde ha caído la pieza en el tablero
        centro_obj_x1 = casilla_0_0["x"] + comp_x
        centro_obj_y1 = casilla_0_0["y"] + comp_y
        
        # ---------------- PASO 2 ----------------
        print(f"\n--- PASO 2: Casilla [7][7] ---")
        print("Encaja la ESQUINA SUPERIOR IZQUIERDA en [7][7] (aunque sobresalga).")
        dedo_x2 = float(input("X de tu dedo (sin soltar): "))
        dedo_y2 = float(input("Y de tu dedo (sin soltar): "))
        
        centro_obj_x2 = casilla_7_7["x"] + comp_x
        centro_obj_y2 = casilla_7_7["y"] + comp_y
        
        # ---------------- MATEMÁTICAS ----------------
        # Interpolación lineal perfecta entre Destino -> Dedo para esta ranura
        mx = (dedo_x2 - dedo_x1) / (centro_obj_x2 - centro_obj_x1)
        my = (dedo_y2 - dedo_y1) / (centro_obj_y2 - centro_obj_y1)
        
        bx = dedo_x1 - (centro_obj_x1 * mx)
        by = dedo_y1 - (centro_obj_y1 * my)
        
        resultados[str(indice)] = {"mx": mx, "my": my, "bx": bx, "by": by}
        print(f"[OK] Matemáticas guardadas para la ranura {indice}.")

    with open("calibracion_mov.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2)
        
    print("\n¡Calibración guardada en 'calibracion_mov.json'!")

if __name__ == "__main__":
    principal()