import subprocess
import re

def obtener_resolucion():
    """Obtiene la resolución actual de la pantalla mediante ADB."""
    resultado = subprocess.run(["adb", "shell", "wm", "size"], capture_output=True, text=True)
    match = re.search(r'(\d+)x(\d+)', resultado.stdout)
    if match:
        ancho, alto = int(match.group(1)), int(match.group(2))
        return ancho, alto
    return 1080, 2400  # Resolución por defecto por si falla

def cambiar_pantalla_derecha():
    ancho, alto = obtener_resolucion()
    
    # Coordenadas (Y en la mitad para evitar tocar menús superiores o inferiores)
    x_origen = int(ancho * 0.90)  # 90% a la derecha
    x_destino = int(ancho * 0.10) # 10% a la izquierda
    y = alto // 2                 # Mitad exacta de la altura
    
    # Duración en milisegundos (300ms es una velocidad natural para cambiar de página)
    duracion = 300
    
    print(f"Resolución detectada: {ancho}x{alto}")
    print(f"Haciendo swipe de derecha a izquierda: X:{x_origen} -> X:{x_destino}")
    
    comando = f"adb shell input swipe {x_origen} {y} {x_destino} {y} {duracion}"
    subprocess.run(comando, shell=True)
    
    print("¡Swipe completado!")

if __name__ == "__main__":
    cambiar_pantalla_derecha()

