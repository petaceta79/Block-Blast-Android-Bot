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

### `calibrar_tablero.py` (Mapeo Espacial y Escala)

Para que el bot sea independiente del dispositivo, no puede depender de coordenadas de píxeles puestas "a mano" en el código. Este script actúa como un asistente de configuración visual (`GUI` usando OpenCV) que genera un mapa espacial preciso del juego en menos de 10 segundos[cite: 4].

El proceso resuelve tres problemas fundamentales de la visión artificial:

* **Mapeo de Cuadrícula (Interpolación Lineal):** 
  En lugar de obligar al usuario a marcar las 64 casillas del tablero, el script solo pide hacer clic en los centros de dos casillas extremas: la superior izquierda `[0][0]` y la inferior derecha `[7][7]`[cite: 4]. Mediante interpolación lineal, el script calcula automáticamente el centro exacto de las 64 celdas del tablero y la distancia relativa entre ellas[cite: 4].
* **Resolución de Escala (El "Pitch" del Bloque):** 
  En muchos juegos, el tamaño de los bloques en la bandeja inferior es distinto al tamaño de los bloques una vez colocados en el tablero principal. El script pide al usuario marcar las esquinas de un *único bloque individual* en la bandeja[cite: 4]. Esto mide el tamaño real en píxeles (`pitch_ancho`, `pitch_alto`) para que luego el módulo de visión (`leer_piezas.py`) sepa recortar y aislar las piezas correctamente sin confundirse con el tamaño del tablero[cite: 4].
* **Auditoría Visual (Failsafe):** 
  Tras procesar los clics de las 64 celdas y los 3 centros de las ranuras, el script no solo escupe un archivo `calibracion.json`, sino que renderiza y exporta una imagen `calibracion_debug.png` dibujando la matriz matemática calculada sobre el juego real[cite: 4]. Esto permite al desarrollador comprobar visualmente que no hay desalineaciones provocadas por la perspectiva de la pantalla[cite: 4].

### `captura.py` (Extracción de Pantalla y Streaming USB)

Este es el primer eslabón de la cadena visual del bot. Su objetivo no es solo tomar una foto de la pantalla del móvil, sino hacerlo con la **menor latencia posible** para no ralentizar el bucle de juego principal.

Para lograr una captura instantánea, este script evita los cuellos de botella clásicos de I/O (lectura/escritura en disco) aplicando la siguiente técnica:

* **Streaming Directo a RAM (Bypass del Almacenamiento):** 
  La forma habitual (y lenta) de tomar capturas en Android es usar `adb shell screencap`, guardar la imagen en la memoria interna del teléfono y luego extraerla con `adb pull`. Este script descarta ese método y utiliza `adb exec-out screencap -p` para volcar los datos binarios de la imagen directamente a través del cable USB[cite: 5].
* **Decodificación Binaria en Vivo:** 
  El flujo de bytes que viaja por el cable es interceptado por Python y cargado directamente en la memoria RAM mediante un búfer de `numpy` (`np.frombuffer`)[cite: 5]. Inmediatamente después, OpenCV (`cv2.imdecode`) reconstruye la matriz de la imagen al vuelo[cite: 5]. 

Gracias a esta arquitectura, el bot no desgasta la memoria flash del teléfono con miles de capturas temporales y la imagen llega a los "ojos" del algoritmo en una fracción del tiempo habitual.

### `historial.py` (Debug)

En proyectos donde la lógica interna corre a ciegas confiando en una matriz de RAM, si ocurre una desincronización (por ejemplo, el bot cree que puso una pieza pero el juego no lo registró), es imposible saber en qué turno ocurrió el fallo. Este script soluciona eso actuando como la "caja negra" de un avión.

Su arquitectura de guardado está diseñada para priorizar el rendimiento y la trazabilidad:

* **Estructura Append-Only (JSON Lines):** 
  En lugar de guardar un archivo `.json` tradicional gigante, el registro utiliza el formato `JSON Lines` (`.jsonl`)[cite: 6]. Esto significa que cada línea del archivo es un objeto JSON independiente[cite: 6]. Esta decisión de ingeniería permite añadir nuevos eventos (`f.write` en modo `"a"`) instantáneamente sin tener que cargar, parsear y reescribir todo el historial en cada turno, ahorrando operaciones de I/O (lectura/escritura) y memoria[cite: 6].
* **Snapshots de Estado (Antes y Después):** 
  Por cada movimiento ejecutado, el script serializa las matrices de NumPy convirtiéndolas en listas de Python y guarda un bloque de datos inmutable[cite: 6]. Registra exactamente qué pieza se eligió, las coordenadas de destino, y una fotografía del tablero *antes* y *después* de la acción (junto con las líneas limpiadas)[cite: 6]. 
* **Lectura Rápida por Consola:** 
  Además de servir como motor para el sistema de Replay visual, el archivo puede ejecutarse directamente desde la terminal (`python historial.py N`) para leer de forma rápida los últimos $N$ turnos directamente en la consola sin necesidad de levantar interfaces gráficas[cite: 6].

### `leer_piezas.py` (Visión Artificial y Filtro Anti-Sombras 3D)

Extraer las matrices binarias (0/1) de las piezas directamente de la pantalla es el mayor reto perceptivo del bot. 

#### El Problema (Artefactos e Ilusiones Ópticas)
Los juegos modernos de puzzle no son planos. Utilizan fuertes biseles 3D, reflejos de luz y sombras proyectadas muy oscuras. Si intentamos detectar las piezas buscando "colores" o usando umbrales estáticos, la sombra proyectada por un bloque vertical de 1x3 invadirá la casilla adyacente, haciendo que el bot crea erróneamente que está viendo un bloque de 2x3.

#### La Solución (Pipeline de Computer Vision)
Para garantizar una precisión absoluta independientemente del tema de color del juego o la iluminación, el script implementa una tubería de 4 fases mediante OpenCV[cite: 7]:

* **Fase 1: Aislamiento en CIELAB y Umbral Dinámico (Otsu):** 
  El script descarta el formato RGB y convierte la imagen al espacio *CIELAB*, separando la luminosidad de los cromatismos[cite: 7]. Calcula la mediana del color del fondo y mide la distancia euclidiana de cada píxel[cite: 7]. Finalmente, aplica el método de Otsu (`cv2.THRESH_OTSU`) que calcula matemáticamente el umbral de corte perfecto para separar las piezas del fondo de forma dinámica[cite: 7].
* **Fase 2: Clustering Espacial (Componentes Conectados):** 
  Aísla los píxeles sólidos y agrupa las cajas delimitadoras cercanas basándose en el parámetro `GAP_CLUSTER_FRACCION`[cite: 7]. De todos los grupos, selecciona el *cluster* geométricamente más cercano a la coordenada de la bandeja calibrada[cite: 7].
* **Fase 3: Muestreo de Cuadrícula y la Estrategia "Inset":** 
  Esta es la barrera definitiva contra las sombras. El script divide la caja delimitadora en una cuadrícula utilizando el tamaño de bloque real (`pitch`)[cite: 7]. Para decidir si una casilla está ocupada, **nunca** lee el recuadro entero. Aplica un margen interno (`INSET_CELDA = 0.35`), ignorando por completo el **35%** exterior de la casilla, donde habitan las sombras y los biseles[cite: 7]. Si el **65%** (`FRACCION_OCUPADA_MIN`) del núcleo central restante es sólido, lo marca como `1`[cite: 7].
* **Fase 4: Recorte Dimensional (Trim):** 
  Por último, el algoritmo elimina cualquier fila o columna periférica compuesta exclusivamente por ceros[cite: 7]. Esto garantiza que una pieza en forma de cruz se exporte como una matriz ajustada y pura, lista para que el motor lógico pruebe sus encajes sin tener que calcular desplazamientos adicionales[cite: 7].

### `mover_pieza.py` 

Este módulo es el puente final entre las matemáticas del bot y el mundo físico. Su única responsabilidad es recibir una instrucción de alto nivel (por ejemplo: *"Mueve la pieza de la ranura 0 a la fila 2, columna 5"*) y traducirla a una orden táctil precisa en el sistema Android.

Para lograr una tasa de error del 0% en los arrastres físicos, el script automatiza el siguiente proceso:

* **Desplazamiento del Centro Geométrico:** 
  Las coordenadas de las celdas en el tablero señalan a la esquina superior izquierda, pero las piezas tienen volumen. Antes de mover nada, el script lee las dimensiones de la ficha (`filas_pieza`, `cols_pieza`) e incrementa el destino visual sumando la mitad del tamaño de las celdas implicadas para hallar el `centro_x_objetivo` y `centro_y_objetivo` reales[cite: 8].
* **Aplicación del Modelo Paramétrico:** 
  Una vez definido el centro visual al que queremos que caiga la pieza, el script consulta `calibracion_mov.json` para cargar el perfil de físicas específico de la ranura de origen (`indice_pieza`)[cite: 8]. A continuación, inyecta la coordenada visual en la ecuación de la recta calculada previamente para obtener la coordenada táctil ciega[cite: 8]:
  
  `x_destino_dedo = (centro_x_objetivo * mx) + bx`
  
  *(Aplicando la misma fórmula para el eje Y)[cite: 8]*
* **Límites de Seguridad (Clipping):** 
  Para evitar que los cálculos expulsen el toque fuera de la pantalla (lo que provocaría un error fatal en Android), el resultado se recorta matemáticamente (`max` / `min`) contra los límites de resolución del dispositivo guardados en `calibracion.json`[cite: 8].
* **Ejecución vía ADB:** 
  Con la coordenada origen y la coordenada táctil calculadas, el bot invoca un proceso secundario que ejecuta el comando `adb shell input swipe` con una duración controlada (800 ms por defecto), permitiendo que el juego renderice la animación de arrastre sin que el toque sea considerado un "toque fantasma"[cite: 8].

### `solver.py` (El Motor Lógico y Árbol de Backtracking)

Este archivo es la inteligencia artificial pura del bot. Está diseñado bajo un principio de **desacoplamiento total**: no sabe nada de capturas de pantalla, colores ni ADB[cite: 9]. Solo recibe matrices abstractas de NumPy (0/1) y devuelve coordenadas matemáticas, lo que permite testearlo de forma aislada y unitaria[cite: 9].

El reto computacional de este juego es que el orden en el que colocas las 3 piezas altera drásticamente el resultado. Para resolverlo sin saturar la CPU, el motor implementa las siguientes mecánicas:

* **Simulación de Universos (Permutaciones):** 
  Al recibir un turno con 3 piezas, el script genera todas las secuencias de orden posibles usando `itertools.permutations`[cite: 9]. Esto significa evaluar hasta $3! = 6$ ramas principales o "universos" distintos[cite: 9].
* **Búsqueda en Profundidad (Backtracking y Pruning):** 
  Para cada pieza en el orden actual, el algoritmo calcula una lista de `posiciones_validas` (hasta $\le 64$ coordenadas candidatas) comprobando que no haya colisiones matriciales mediante la evaluación `(region == 1) & (pieza == 1)`[cite: 9]. Si una pieza no cabe en ninguna parte, el algoritmo corta esa rama del multiverso inmediatamente (pruning) y retrocede un paso, ahorrando miles de cálculos inútiles[cite: 9].
* **Limpieza Matricial Predictiva:** 
  Antes de evaluar la siguiente pieza de la recursividad, el sistema coloca temporalmente la matriz de la pieza en una copia del tablero y rastrea las filas y columnas completas (`nuevo[f].all()`)[cite: 9]. Si encuentra alguna, las pone a `0` temporalmente, simulando la física real del juego para que la siguiente pieza encaje en los nuevos huecos[cite: 9].
* **Estrategia "First-Match" (La Versión Más Básica):** 
  En su iteración actual, esta es la versión más básica y ligera del motor lógico. En lugar de evaluar exhaustivamente el árbol de decisiones para puntuar escenarios y buscar la jugada "perfecta" (la que limpie más líneas), el algoritmo está diseñado para detenerse y devolver la **primera solución viable que encuentra**[cite: 9]. En el momento exacto en el que halla una combinación donde las 3 piezas encajan en el tablero sin colisionar, corta la búsqueda de raíz y ejecuta el turno[cite: 9]. Esto garantiza un tiempo de respuesta prácticamente instantáneo, evitando que el móvil se quede "pensando".

### `solver2.py` (El Motor Lógico y Maximizador de Combos)

Este archivo es el verdadero cerebro analítico del bot. A diferencia de algoritmos más básicos que se conforman con la primera jugada viable, este sistema actúa como un oráculo matemático: evalúa todos los futuros posibles para encontrar la jugada perfecta[cite: 10]. 

Trabajando puramente con matrices de NumPy (completamente desacoplado de la visión y de ADB), implementa las siguientes mecánicas:

* **Multiverso de Permutaciones:** 
  En este juego, el orden en el que colocas las piezas altera drásticamente los huecos resultantes. El motor utiliza `itertools.permutations` para evaluar exhaustivamente todas las secuencias de orden posibles para las piezas en mano (hasta $3! = 6$ ramas principales)[cite: 10].
* **Backtracking Profundo (Búsqueda Exhaustiva):** 
  Para cada permutación, el algoritmo recursivo explora absolutamente *todas* las `posiciones_validas` en el tablero[cite: 10]. Si una rama de la simulación lleva a un callejón sin salida (una pieza no cabe), corta la ejecución de esa rama y retrocede.
* **Simulación Predictiva de Físicas:** 
  Durante la exploración del árbol, el algoritmo coloca virtualmente las matrices y simula la destrucción de bloques (`colocar`)[cite: 10]. Al detectar filas o columnas completas (`nuevo[f].all()`), las pone a `0`, permitiendo que la siguiente pieza en la simulación encaje en los huecos recién creados[cite: 10].
* **El Maximizador de Puntuación:** 
  A medida que recorre las ramas de decisión, el sistema suma las líneas limpiadas (`lineas_totales`) y las compara constantemente con su récord (`max_lineas_global`)[cite: 10]. Tras evaluar el árbol completo, devuelve de forma determinista la secuencia exacta (`mejor_solucion_global`) que garantiza la mayor destrucción posible de líneas[cite: 10].

### `swipe_derecha.py` (Diagnóstico de Conexión ADB)

Este script no forma parte del bucle principal de inteligencia o visión del bot. Es una utilidad de diagnóstico (*sanity check*) diseñada para que el usuario pueda verificar que el puente de comunicación entre el PC y el teléfono Android funciona correctamente antes de iniciar una partida.

A pesar de ser un script de prueba, mantiene un diseño robusto:

* **Detección Dinámica de Resolución:** En lugar de enviar toques ciegos a coordenadas programadas "a fuego" (hardcoded), el script interroga al dispositivo mediante `adb shell wm size` y utiliza expresiones regulares (`re`) para extraer la resolución real de la pantalla[cite: 11].
* **Swipe Proporcional Seguro:** Calcula matemáticamente un deslizamiento desde el 90% del ancho de la pantalla hasta el 10%[cite: 11]. Además, sitúa el toque exactamente en el 50% de la altura vertical (`alto // 2`) para garantizar que el arrastre no despliegue accidentalmente la barra de notificaciones ni los gestos de navegación del sistema operativo[cite: 11]. El movimiento se ejecuta en 300 ms, simulando la velocidad natural de un dedo humano[cite: 11].

### `tablero_io.py` (Persistencia de Estado y Human-in-the-Loop)

Dado que el bot no lee la matriz del tablero en vivo (para evitar confusiones con las animaciones), necesita una forma segura de guardar su progreso y permitir al usuario intervenir si hay algún problema. Este módulo gestiona la entrada/salida (I/O) del estado del tablero hacia el disco duro.

Sus características de diseño incluyen:

* **Serialización Legible (Human-in-the-Loop):** 
  En lugar de exportar el estado como un archivo binario incomprensible (como un `.pkl` de Python), el script guarda la matriz en un formato de texto plano simple: 8 líneas de 8 dígitos (`0` o `1`) separados por espacios[cite: 12]. Esto permite a un humano abrir `tablero_estado.txt`, editarlo a mano para reflejar una partida ya empezada en el móvil, y arrancar el bot a mitad de juego[cite: 12].
* **Manejo de Errores e Inicialización Segura (Failsafe):** 
  Si el usuario ejecuta el bot por primera vez y el archivo de guardado no existe, el script no lanza una excepción que rompa el programa; automáticamente genera una matriz `_tablero_vacio` (todo ceros) y crea el archivo en disco[cite: 12].
* **Validación de Integridad Estricta:** 
  Al cargar el archivo, el módulo aplica una limpieza de datos (ignora líneas en blanco o caracteres extraños) y valida matemáticamente que la matriz resultante sea exactamente de 8x8 y contenga exclusivamente valores booleanos (`0` o `1`)[cite: 12]. Si detecta corrupción en el archivo, levanta un `ValueError` para evitar que el bot juegue con un estado inválido[cite: 12].

---

## Guía de Instalación y Uso

Sigue estos pasos para configurar el bot en tu entorno local y sincronizarlo con la resolución de tu dispositivo Android.

### 1. Preparación del Entorno

Antes de descargar el código, asegúrate de tener las herramientas base preparadas en tu sistema:

- **Depuración USB:** Activa las opciones de desarrollador en tu teléfono Android y habilita la "Depuración USB". Conecta el móvil al PC mediante cable.
- **ADB (Android Debug Bridge):** Instala ADB en tu ordenador y asegúrate de que reconoce tu dispositivo ejecutando `adb devices` en la terminal.
- **Dependencias de Python:** El bot requiere librerías modernas de visión artificial y manipulación de matrices. Instálalas ejecutando:

  ```bash
  pip install numpy opencv-python moviepy
  ```

### 2. Calibración del Dispositivo (solo la primera vez)

Como el bot está diseñado para ser universal, necesita aprender las proporciones de tu pantalla mediante dos asistentes de calibración.

- **Mapeo Visual (Geometría):** Abre una partida en tu móvil y ejecuta la herramienta de captura y el asistente visual. Sigue las instrucciones de clics en la ventana para generar `calibracion.json`:

  ```bash
  python captura.py
  python calibrar_tablero.py tablero_juego.png
  ```

- **Físicas de Arrastre (Offset Táctil):** A continuación, calibra la física del movimiento para las 3 ranuras respondiendo a las preguntas de la consola. Esto generará el archivo `calibracion_mov.json`:

  ```bash
  python calibracion_move.py
  ```
  
  >
  > Para calibrar esto, deberás activar «Mostrar ubicación de las pulsaciones» o alguna opción que permita ver dónde has pulsado en las opciones de desarrollador de Android.
  >
  > Es muy importante que, al momento de usar el bot, lo desactives si este deja algún tipo de marca visual, ya que rompe el script de leer piezas (al funcionar por color, no identifica bien las piezas).

### 3. Ejecución y Debugging

Con la calibración lista, el bot ya es completamente autónomo.

- **Iniciar Partida:** Abre el juego en tu móvil y lanza el orquestador principal. Puedes pasarle como argumento el número de turnos que quieres que juegue (ej. 50):

  ```bash
  python bot.py 50
  ```

- **Detención y Guardado Seguro:** Para parar el bot, pulsa `Ctrl+C` una sola vez en la consola. El bot no se cortará de golpe: terminará de colocar las fichas de su mano, guardará el estado en `tablero_estado.txt` y saldrá limpiamente.

- **Auditoría de Jugadas:** Si en algún momento la matriz virtual se desincroniza de la pantalla física, abre el sistema de Replay para auditar las jugadas paso a paso y detectar el error:

  ```bash
  python bot_debug.py
  ```

---

## Próximos Pasos (Roadmap)

- [ ] Optimizar el solver para maximizar puntuación (no solo colocar piezas), priorizando combos de líneas.
- [ ] Verificación periódica automática del tablero real contra el estado interno, para detectar desincronizaciones sin intervención manual.
- [ ] Soporte multi-tema robusto (colores/fondos distintos) sin necesidad de recalibrar.
- [ ] Panel de estadísticas por partida (puntuación, líneas totales, turnos jugados).

## Aviso Legal

Este proyecto se ha desarrollado con **fines educativos y de investigación personal** (visión por computador, automatización y algoritmos de backtracking). No está afiliado ni respaldado por los desarrolladores del juego original.

El uso de este bot para jugar de forma automatizada puede infringir los términos de servicio de la aplicación o de las plataformas de distribución (rankings, logros, etc.). El autor no se hace responsable del uso que se le dé a este código ni de las consecuencias derivadas de su uso en cuentas o dispositivos de terceros. Úsalo bajo tu propia responsabilidad.
