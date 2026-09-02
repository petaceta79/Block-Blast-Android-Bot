import cv2
import numpy as np
import subprocess

def capturar_pantalla(nombre_archivo="tablero_juego.png"):
    print("Capturando pantalla del móvil...")
    
    # Ejecuta el comando de ADB para tomar la captura
    proceso = subprocess.Popen(["adb", "exec-out", "screencap", "-p"], stdout=subprocess.PIPE)
    salida, _ = proceso.communicate()
    
    # Si la salida está vacía, algo falló
    if not salida:
        print("Error: No se recibió ninguna imagen. Revisa la conexión USB.")
        return

    # Convertir el flujo de bytes a una matriz de imagen de OpenCV
    img_array = np.frombuffer(salida, dtype=np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    # Comprobar que OpenCV pudo leer bien la imagen
    if frame is not None:
        cv2.imwrite(nombre_archivo, frame)
        alto, ancho, _ = frame.shape
        print(f"¡Éxito! Imagen guardada como '{nombre_archivo}'.")
        print(f"Resolución de la imagen: {ancho}x{alto} píxeles.")
    else:
        print("Error: La imagen se corrompió al decodificarla.")

if __name__ == "__main__":
    capturar_pantalla()

