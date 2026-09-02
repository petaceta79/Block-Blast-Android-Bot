# Block Blast! Android Bot

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![ADB](https://img.shields.io/badge/Android-ADB-success.svg)

<div align="center">
  <img src="videos/demo.gif" alt="Demo del Bot jugando a Block Blast" width="300"/>
  <p><i>El bot analizando el tablero y ejecutando combos de forma totalmente autónoma.</i></p>
</div>

---

## Sobre el Proyecto

Un bot autónomo y determinista desarrollado en Python capaz de jugar al popular juego **Block Blast** en dispositivos Android reales. 

Lejos de ser un simple *auto-clicker*, este proyecto es un sistema completo de automatización que fusiona:
* **Visión Artificial (OpenCV)** para extraer el estado de la partida y leer las formas de las piezas, aislando los bloques reales del ruido visual (brillos, sombras 3D y colores).
* Algoritmos de **Backtracking** que exploran el multiverso de jugadas posibles (permutaciones y posiciones) para calcular la estrategia óptima que destruya el mayor número de líneas.
* Automatización mediante **ADB (Android Debug Bridge)** para traducir el tablero lógico a movimientos táctiles físicos.

---

## Características Principales (Features)

* **Visión Artificial Robusta (Anti-Sombras):** El bot utiliza OpenCV para analizar la pantalla. Al convertir la imagen al espacio de color CIELAB y aplicar umbralización dinámica (Otsu), aísla las piezas reales ignorando por completo el color de los bloques. Además, recorta los márgenes internos de cada celda para evitar falsos positivos causados por las sombras y brillos 3D del juego.
* **Cerebro Analítico (Maximizador de Combos):** El motor lógico (`solver2.py`) no se conforma con el primer hueco disponible. Mediante un algoritmo de **Backtracking**, evalúa todos los universos paralelos (calculando todas las posiciones y las permutaciones de orden de las 3 piezas) para ejecutar siempre la secuencia exacta que destruya la mayor cantidad de líneas posibles.
* **Interpolación Táctil Paramétrica:** En Android, el píxel visual rara vez coincide con el píxel táctil necesario debido a la perspectiva y la inercia del arrastre. El bot soluciona esto aplicando una **regresión lineal (y = mx + b)** para cada ranura de la bandeja, traduciendo coordenadas visuales a comandos físicos de ADB.
* **Gestión de Memoria y Guardado Seguro:** Para maximizar la velocidad, la matriz 8x8 del tablero se mantiene y actualiza en la memoria RAM (evitando lecturas constantes de pantalla). Si el usuario pulsa `Ctrl+C`, el bot intercepta la señal, termina de colocar las piezas del turno actual de forma segura y guarda el estado en un archivo `.txt` para evitar la desincronización.
