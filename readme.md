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

## Arquitectura y Lógica del Proyecto

El código fuente está estrictamente modularizado para separar la percepción visual, el razonamiento matemático y la acción física. En lugar de explicar el código línea por línea, esta sección detalla los **conceptos lógicos y matemáticos** que resuelven los retos específicos de cada módulo.

A continuación, se desglosa el funcionamiento interno de cada uno de ellos:

### `bot.py` (El Orquestador y la Memoria)

Este es el script principal (`main`) que mantiene el bucle de juego vivo. Su mayor reto no es llamar a otras funciones, sino **mantener la sincronización absoluta** entre lo que hay en la memoria del PC y lo que ocurre físicamente en la pantalla del móvil.

Para lograrlo, implementa dos conceptos clave:

* **Manejo de Estado en RAM:** 
  El bot *nunca* lee el estado del tablero central de la pantalla durante la partida[cite: 2]. Solo lee un archivo local `tablero_estado.txt` al arrancar[cite: 2]. A partir de ahí, la matriz 8x8 vive exclusivamente en la memoria RAM de Python. Cada vez que el brazo ejecuta un movimiento, la matriz se actualiza matemáticamente[cite: 2]. Esto evita que, a medida que la partida avanza, OpenCV se confunda leyendo la pantalla si un bloque físico brilla o hace una animación rara.
* **Cierre Limpio (Graceful Exit) y Sincronización:**
  Si el usuario detiene el bot bruscamente (`Ctrl+C`) a mitad de un turno, Python normalmente cortaría la ejecución al instante. Esto dejaría una pieza colocada en el móvil, pero no registrada en la memoria, corrompiendo la partida. Para evitarlo, `bot.py` utiliza la librería `signal` para atrapar la interrupción[cite: 2]. Al pulsar `Ctrl+C`, el bot activa una bandera, termina pacientemente de colocar las piezas que le queden en la mano, actualiza la matriz, la guarda de forma segura en disco y se despide[cite: 2].

### `bot_debug.py` 

Cuando el bot falla en el turno 45, es imposible saber qué salió mal mirando una matriz de números. Este script actúa como una "caja negra" de avión, permitiendo auditar y reproducir visualmente cada decisión que tomó el bot a lo largo de la partida[cite: 2].

Su lógica se basa en dos pilares fundamentales:

* **Trazabilidad de Estados (Side-by-Side):** 
  El script lee el registro estructurado `historial.jsonl` y utiliza OpenCV para generar una interfaz gráfica[cite: 2]. Por cada movimiento, renderiza dos tableros paralelos ("ANTES" y "DESPUÉS")[cite: 2]. Su mayor virtud es que proyecta geométricamente la pieza a colocar resaltándola en color naranja sobre las coordenadas exactas de caída[cite: 2]. Esto permite confirmar visualmente si la limpieza de líneas se calculó correctamente.
* **Depuración Quirúrgica (Navegación de Frames):** 
  En lugar de ver la partida en tiempo real, el sistema permite avanzar o retroceder frame a frame (como en un editor de vídeo), e incluso saltar directamente a un turno específico mediante el comando `g`[cite: 2]. Además, cuenta con un modo *headless* (`--sin-gui`) que exporta todos los pasos a imágenes PNG, ideal para documentar fallos sin necesidad de levantar ventanas interactivas[cite: 2].

### `calibracion_move.py` (La Física del Arrastre y el Offset Táctil)

Automatizar toques en Android (`ADB shell input swipe`) parece fácil en teoría, pero en la práctica, los juegos de puzzles móviles implementan mecánicas visuales que rompen por completo la relación 1:1 entre la pantalla y el toque táctil. Este script es la solución a ese problema.

#### El Problema (La Ilusión Táctil)
Si intentas arrastrar una pieza directamente a la coordenada visual donde quieres que caiga, la pieza quedará desencajada por dos motivos físicos del juego:
1. **El "Offset" del Dedo:** Para evitar que la mano del jugador tape la casilla donde va a soltar la ficha, el juego siempre dibuja la pieza unos centímetros *por encima* del punto táctil real.
2. **El Ángulo de Origen (Paralaje):** La fricción y la inercia cambian dependiendo de dónde provenga la pieza. Arrastrar una ficha desde la ranura 0 (extremo izquierdo) hasta el centro del tablero requiere un recorrido táctil distinto que arrastrarla desde la ranura 2 (extremo derecho), a pesar de que el destino final sea el mismo.
3. **El Centro de Gravedad:** Las piezas tienen distintos tamaños (1x1, 3x3, etc.). Si soltamos la pieza tomando como referencia solo su esquina superior izquierda, las piezas grandes quedarán descentradas.

#### La Solución (Geometría y Regresión Lineal)
Para que el bot pueda jugar en cualquier resolución y dispositivo sin usar "números mágicos", este script genera un modelo matemático personalizado para cada una de las 3 ranuras[cite: 3].

**Paso 1: Compensación del Centro Geométrico**
Antes de calibrar, el script calcula dinámicamente el centro real de la pieza basándose en sus dimensiones[cite: 3]:
$$comp\_x = (cols - 1) \times \frac{ancho\_celda}{2.0}$$
$$comp\_y = (filas - 1) \times \frac{alto\_celda}{2.0}$$

**Paso 2: Muestreo de los Extremos**
El script guía al usuario para que arrastre manualmente una pieza a la casilla superior izquierda `[0][0]` y luego a la inferior derecha `[7][7]`[cite: 3]. En ambos casos, registra dónde está apoyando el dedo el usuario (`dedo_x`, `dedo_y`) en relación con el centro visual donde ha caído la pieza (`centro_obj_x`, `centro_obj_y`)[cite: 3].

**Paso 3: La Fórmula de la Recta**
Con estos dos puntos extremos, el sistema calcula una **interpolación lineal paramétrica** ($y = mx + b$) calculando la pendiente de corrección ($m$) y el desfase de origen ($b$) para ambos ejes[cite: 3]:

$$m_x = \frac{dedo\_x2 - dedo\_x1}{centro\_obj\_x2 - centro\_obj\_x1}$$

$$b_x = dedo\_x1 - (centro\_obj\_x1 \cdot m_x)$$

*(Esta misma fórmula se aplica idéntica para el eje Y calculando $m_y$ y $b_y$[cite: 3])*

**El Resultado Final:**
Estos parámetros se calculan individualmente para las 3 ranuras y se guardan en `calibracion_mov.json`[cite: 3]. En partida, cuando el bot quiere mover una ficha, el script `mover_pieza.py` simplemente mete la coordenada visual deseada en esta ecuación, devolviendo la coordenada táctil ciega exacta que ADB debe pulsar para que el movimiento sea perfecto.

---
