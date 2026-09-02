import json
import subprocess
import os

def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)

def mover_pieza(indice_pieza, filas_pieza, cols_pieza, fila_destino, col_destino, duracion=800):
    if not os.path.exists("calibracion_mov.json"):
        print("Falta 'calibracion_mov.json'. Ejecuta calibrar_movimiento.py primero.")
        return

    calib_base = cargar_json("calibracion.json")
    calib_mov = cargar_json("calibracion_mov.json")

    # Origen en la bandeja
    try:
        pieza_origen = next(p for p in calib_base["piezas_bandeja"] if p["indice"] == indice_pieza)
        x_origen = int(pieza_origen["x"])
        y_origen = int(pieza_origen["y"])
    except StopIteration:
        print(f"Error: Índice {indice_pieza} no encontrado en bandeja.")
        return

    # Casilla objetivo
    try:
        celda = next(c for c in calib_base["tablero"]["celdas"] 
                     if c["fila"] == fila_destino and c["col"] == col_destino)
    except StopIteration:
        print(f"Error: Casilla [{fila_destino}][{col_destino}] fuera de rango.")
        return
    
    # Calcular centro de la cuadrícula
    ancho_celda = calib_base["tablero"]["ancho_celda"]
    alto_celda = calib_base["tablero"]["alto_celda"]
    centro_x_objetivo = celda["x"] + ((cols_pieza - 1) * (ancho_celda / 2.0))
    centro_y_objetivo = celda["y"] + ((filas_pieza - 1) * (alto_celda / 2.0))

    # Aplicar matemáticas específicas de la ranura
    fisicas = calib_mov.get(str(indice_pieza))
    if not fisicas:
        print(f"Error: No hay datos de calibración para la pieza {indice_pieza}.")
        return
        
    mx, my = fisicas["mx"], fisicas["my"]
    bx, by = fisicas["bx"], fisicas["by"]

    x_destino_dedo = int((centro_x_objetivo * mx) + bx)
    y_destino_dedo = int((centro_y_objetivo * my) + by)

    # Evitar salir de pantalla
    x_destino_dedo = max(0, min(calib_base["resolucion"]["ancho"], x_destino_dedo))
    y_destino_dedo = max(0, min(calib_base["resolucion"]["alto"], y_destino_dedo))

    print(f"\n[!] Moviendo Ranura {indice_pieza} ({filas_pieza}x{cols_pieza}) a [{fila_destino}][{col_destino}]")
    
    comando = f"adb shell input swipe {x_origen} {y_origen} {x_destino_dedo} {y_destino_dedo} {duracion}"
    subprocess.run(comando, shell=True)

if __name__ == "__main__":
    # Prueba final pasando solo las dimensiones: (indice, filas, columnas, fila_destino, col_destino)
    # Por ejemplo, una pieza que ocupe 2x2:
    mover_pieza(indice_pieza=0, filas_pieza=4, cols_pieza=1, fila_destino=0, col_destino=7)