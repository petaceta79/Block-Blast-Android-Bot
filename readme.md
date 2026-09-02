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