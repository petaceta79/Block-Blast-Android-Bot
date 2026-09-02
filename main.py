import os
from captura import capturar_pantalla
from leer_piezas import leer_piezas

def main():
    # Definimos el nombre del archivo temporal para la captura
    archivo_captura = "captura_juego.png"
    
    print("--- 1. INICIANDO CAPTURA ---")
    # Llamamos a la función de captura y le pasamos el nombre del archivo
    capturar_pantalla(archivo_captura)
    
    # Comprobamos si la imagen se generó correctamente antes de continuar
    if not os.path.exists(archivo_captura):
        print("Error: No se pudo encontrar la captura. Abortando.")
        return

    print("\n--- 2. LEYENDO PIEZAS ---")
    try:
        # Llamamos a la función que procesa la imagen y devuelve las matrices
        matrices_piezas = leer_piezas(archivo_captura)
        
        # Iteramos sobre la lista de matrices devuelta
        for i, matriz in enumerate(matrices_piezas):
            print(f"\n[ Pieza {i + 1} ]")
            
            # Si el tamaño es 0, significa que el hueco está vacío (no se detectó pieza)
            if matriz.size == 0:
                print("  (Ranura vacía)")
            else:
                # Imprimimos las dimensiones de la pieza detectada
                print(f"  Dimensiones: {matriz.shape[0]} filas x {matriz.shape[1]} columnas")
                print("  Forma:")
                
                # Dibujamos la matriz de forma visual para entender qué pieza es
                for fila in matriz:
                    # Reemplaza el 1 por '#' y el 0 por '.' para verlo gráficamente
                    dibujo_fila = " ".join("#" if valor == 1 else "." for valor in fila)
                    print("    " + dibujo_fila)
                    
    except Exception as e:
        print(f"Ocurrió un error al intentar leer las piezas: {e}")

if __name__ == "__main__":
    main()