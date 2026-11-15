# Decodificación de Estados Latentes en Dinámicas Tipo SIRS mediante Modelos Ocultos de Markov: Un Estudio de Simulación Monte Carlo

**Autores:** Equipo de Investigación en Modelado y Simulación  
**Afiliación:** Asignatura de Simulación (5.º Semestre)  
**Marco de rigor:** SKILL.md — Decisión Humana, Trazabilidad y Verificación Científica  
**Script reproducible:** [`simulacion_hmm.py`](file:///c:/Users/USUARIO/OneDrive/Documentos/Simulación/.agentsskillsarticulo-hmm/simulacion_hmm.py) (`seed = 42`, $N = 1000$, $T = 50$, total $50{,}000$ pasos)  

---

## Resumen
En epidemiología, la vigilancia basada en el reporte agregado de casos adolece de incertidumbre estocástica debido al subregistro clínico y a la ambigüedad inherente entre fases biológicas: un nivel bajo de notificaciones puede reflejar tanto una población predominantemente susceptible al inicio del brote como una fase avanzada de recuperación. Este artículo evalúa computacionalmente la capacidad del algoritmo de Viterbi para decodificar la secuencia óptima de estados latentes ($S, I, R$) en un Modelo Oculto de Markov (HMM) discreto con dinámica tipo SIRS ($A_{3,1} = 0.20$), contrastándolo frente a un clasificador heurístico ingenuo basado únicamente en la verosimilitud de la emisión instantánea. 

Se diseñó un experimento Monte Carlo con $N=1000$ réplicas independientes de longitud $T=50$ pasos temporales ($50{,}000$ transiciones totales) generado bajo condiciones controladas (`seed=42`) a partir de parámetros calibrados teóricamente. Los resultados demuestran que el algoritmo de Viterbi supera con significancia estadística al clasificador base en exactitud global ($59.87\%$ [IC 95%: $59.44\% - 60.30\%$] frente a $53.34\%$ [IC 95%: $52.90\% - 53.78\%$], $p < 0.001$) y de forma contundente en el Macro F1-Score ($0.6030$ vs. $0.4351$, $+0.1679$). Se evidencia que la deficiencia crítica del enfoque estático radica en su ceguera absoluta hacia los individuos susceptibles (sensibilidad del $0.0\%$), mientras que Viterbi aprovecha la distribución inicial ($\pi_S = 0.90$) y la matriz de transición para desambiguar el brote inicial. No obstante, la exactitud estabilizada en $\approx 60\%$ constata el límite intrínseco impuesta por el ruido observacional en matrices de emisión altamente solapadas.

**Palabras clave:** Modelos Ocultos de Markov, Algoritmo de Viterbi, Modelo SIRS, Simulación Monte Carlo, Inferencia de Estados Ocultos.

---

## 1. Problema e Introducción

### 1.1 Contexto y naturaleza del sistema
En los sistemas de salud pública, el monitoreo continuo de enfermedades transmisibles depende de la notificación periódica de casos clínicos diagnosticados. En este marco de estudio didáctico, la autoridad sanitaria consolida el reporte diario clasificándolo en tres niveles discretos: *bajos*, *medios* o *altos*.

Sin embargo, las observaciones epidemiológicas rara vez exhiben una correspondencia biunívoca con la distribución de los compartimentos epidemiológicos de la población:
* Un reporte de **casos bajos** surge con frecuencia tanto en comunidades no expuestas mayoritariamente *Susceptibles* ($S$) al comienzo de una ola epidémica, como en comunidades en fase de *Recuperación* ($R$) que han adquirido inmunidad temporal.
* Factores no controlados —como demoras administrativas en la carga de datos, umbrales variables de búsqueda de atención médica y limitaciones diagnósticas— introducen un canal ruidoso entre la verdadera prevalencia infecciosa ($I$) y la notificación observada.

### 1.2 Delimitación del problema
La cuestión metodológica central consiste en establecer si el modelado estocástico de las transiciones temporales mediante un Modelo Oculto de Markov discreto permite reconstruir fielmente la trayectoria epidemiológica latente, mitigando los sesgos de clasificación propios de una toma de decisiones reactiva basada únicamente en el volumen de reportes del día.

### 1.3 Supuestos explícitos y delimitación del alcance
1. **Carácter hipotético de los parámetros:** Los parámetros evaluados $(A, B, \pi)$ provienen del caso didáctico propuesto; **no corresponden a estimaciones de campo ni representan una epidemia real**.
2. **Propiedad markoviana de primer orden:** Se asume que el estado de salud de la población en el instante $t$ depende exclusivamente del estado en $t-1$, lo que impone una distribución geométrica sobre los tiempos de permanencia en cada estado.
3. **Independencia condicional de emisiones:** La observación en el instante $t$ depende estrictamente del compartimento latente en dicho instante temporal.
4. **Comportamiento endémico tipo SIRS:** La matriz de transición define una probabilidad de pérdida de inmunidad $A_{3,1} = P(q_t = S \mid q_{t-1} = R) = 0.20$, distanciándose del modelo SIR clásico con estado absorbente final.

---

## 2. Preguntas y Objetivos

### 2.1 Pregunta de investigación (Autorizada por el equipo)
> *¿Con qué precisión y robustez el algoritmo de Viterbi logra recuperar la trayectoria de fases latentes ($S, I, R$) a partir de observaciones ruidosas bajo parámetros hipotéticos conocidos, en comparación con un clasificador ingenuo basado exclusivamente en la verosimilitud de la matriz de emisión?*

### 2.2 Objetivo General
Evaluar computacionalmente el desempeño del algoritmo de programación dinámica de Viterbi para la decodificación de secuencias epidemiológicas latentes frente a un clasificador de emisión pura sin memoria temporal, utilizando un protocolo de simulación Monte Carlo reproducible ($N=1000$ réplicas de longitud $T=50$) y el análisis de trazabilidad analítica de un caso testigo.

### 2.3 Objetivos Específicos
1. Formalizar analíticamente el HMM $\lambda = (S, V, A, B, \pi)$ y trazar manualmente paso a paso la inducción de Viterbi sobre la secuencia testigo $Y = (\text{bajos}, \text{bajos}, \text{medios}, \text{altos}, \text{medios})$.
2. Implementar un entorno de simulación computacional en lenguaje Python reproducible (`seed=42`) para cuantificar Exactitud global, Sensibilidad/Recall por compartimento, Precisión, F1-Score Macro y matrices de confusión para ambos métodos bajo $50{,}000$ transiciones estocásticas.

---

## 3. Marco Teórico

### 3.1 Formalización matemática del HMM
El sistema queda definido por la tupla $\lambda = (S, V, A, B, \pi)$:
* **Espacio de estados ocultos:** $S = \{S_1 = \text{Susceptible}, S_2 = \text{Infectado}, S_3 = \text{Recuperado}\}$.
* **Alfabeto de observaciones:** $V = \{v_1 = \text{bajos}, v_2 = \text{medios}, v_3 = \text{altos}\}$.
* **Vector de probabilidades iniciales ($\pi \in \mathbb{R}^3$):**
  $$\pi = \begin{bmatrix} 0.90 \\ 0.08 \\ 0.02 \end{bmatrix}$$
* **Matriz de probabilidades de transición ($A \in \mathbb{R}^{3 \times 3}$):** Donde $A_{ij} = P(q_t = S_j \mid q_{t-1} = S_i)$:
  $$A = \begin{bmatrix} 0.70 & 0.25 & 0.05 \\ 0.05 & 0.55 & 0.40 \\ 0.20 & 0.05 & 0.75 \end{bmatrix}$$
* **Matriz de probabilidades de emisión ($B \in \mathbb{R}^{3 \times 3}$):** Donde $B_{jk} = P(y_t = v_k \mid q_t = S_j)$:
  $$B = \begin{bmatrix} 0.70 & 0.25 & 0.05 \\ 0.10 & 0.30 & 0.60 \\ 0.80 & 0.15 & 0.05 \end{bmatrix}$$

### 3.2 Algoritmo de Viterbi en espacio logarítmico
Para preservar la estabilidad numérica y mitigar el subdesbordamiento aritmético (*underflow*) ocasionado por la multiplicación de probabilidades pequeñas en secuencias de longitud $T=50$, se trabaja en escala logarítmica:

1. **Inicialización ($t=1$):**
   $$\delta_1(j) = \ln \pi_j + \ln B_{j, y_1}, \quad \psi_1(j) = 0, \quad \forall j \in \{1, 2, 3\}$$
2. **Recursión ($t = 2, \dots, T$):**
   $$\delta_t(j) = \max_{1 \le i \le 3} [\delta_{t-1}(i) + \ln A_{ij}] + \ln B_{j, y_t}$$
   $$\psi_t(j) = \arg\max_{1 \le i \le 3} [\delta_{t-1}(i) + \ln A_{ij}]$$
3. **Terminación:**
   $$q_T^* = \arg\max_{1 \le j \le 3} \delta_T(j)$$
4. **Reconstrucción del camino óptimo (*backtracking*):**
   $$q_t^* = \psi_{t+1}(q_{t+1}^*), \quad t = T-1, T-2, \dots, 1$$

---

## 4. Metodología y Diseño Experimental

### 4.1 Generación de datos sintéticos (Protocolo Monte Carlo)
Siguiendo las decisiones autorizadas por el equipo humano:
* **Número de réplicas independientes:** $N = 1000$.
* **Horizonte temporal de cada trayectoria:** $T = 50$ días.
* **Muestra total analizada:** $N \times T = 50{,}000$ pasos temporales.
* **Semilla pseudoaleatoria:** `seed = 42`.
* **Generación sin fuga de datos (*data leakage*):** Para cada réplica $i$, la trayectoria latente $Q^{(i)}$ se simula muestreando $q_1 \sim \text{Categorical}(\pi)$ y $q_t \sim \text{Categorical}(A_{q_{t-1}, :})$; simultáneamente se genera la serie de observaciones $y_t \sim \text{Categorical}(B_{q_t, :})$. Dado que los parámetros $(A, B, \pi)$ son preexistentes y no se reestiman a partir de los datos sintéticos, no existe riesgo de sobreajuste ni filtración de información entre entrenamiento y prueba.

### 4.2 Modelo de comparación (*Baseline* de emisión pura)
Como control metodológico, se define un clasificador ingenuo que asigna el estado maximizando estrictamente la verosimilitud de la observación inmediata:
$$\hat{q}_t^{\text{base}} = \arg\max_{j \in \{1, 2, 3\}} B_{j, y_t}$$
Al evaluar las columnas de la matriz $B$:
* $y_t = \text{bajos} \implies \arg\max(0.70, 0.10, 0.80) = S_3 \text{ (Recuperado)}$.
* $y_t = \text{medios} \implies \arg\max(0.25, 0.30, 0.15) = S_2 \text{ (Infectado)}$.
* $y_t = \text{altos} \implies \arg\max(0.05, 0.60, 0.05) = S_2 \text{ (Infectado)}$.

*Falla estructural del clasificador base:* Al ignorar el orden temporal y el vector inicial $\pi$, este modelo es **incapaz de predecir el estado Susceptible ($S_1$)**, diagnosticando equívocamente como recuperada a cualquier población con reporte bajo.

---

## 5. Resultados Verificados de Ejecución

### 5.1 Trazabilidad analítica del caso didáctico ($T=5$)
*Secuencia de observaciones evaluada:* $Y = (\text{bajos}, \text{bajos}, \text{medios}, \text{altos}, \text{medios})$.

| Paso temporal ($t$) | Observación ($y_t$) | $\delta_t(S)$ [bp] | $\delta_t(I)$ [bp] | $\delta_t(R)$ [bp] | Decodificación Viterbi ($\hat{q}_t^*$) | Decodificación Baseline ($\hat{q}_t^{\text{base}}$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| $t=1$ | bajos | **-0.4620** [-] | -4.8283 [-] | -4.1352 [-] | **Susceptible ($S$)** | Recuperado ($R$) |
| $t=2$ | bajos | **-1.1754** [$S$] | -4.1509 [$S$] | -3.6809 [$S$] | **Susceptible ($S$)** | Recuperado ($R$) |
| $t=3$ | medios | **-2.9184** [$S$] | -3.7657 [$S$] | -5.8657 [$R$] | **Susceptible ($S$)** | Infectado ($I$) |
| $t=4$ | altos | -6.2708 [$S$] | **-4.8155** [$S$] | -7.6777 [$I$] | **Infectado ($I$)** | Infectado ($I$) |
| $t=5$ | medios | -8.0137 [$S$] | **-6.6173** [$I$] | -7.6289 [$I$] | **Infectado ($I$)** | Infectado ($I$) |

* **Trayectoria global Viterbi:** $[S, S, S, I, I]$
* **Trayectoria Baseline:** $[R, R, I, I, I]$
* **Log-verosimilitud Viterbi:** $\ln P(Q^*, Y \mid \lambda) = -6.617284$ ($P = 1.337057 \times 10^{-3}$).

### 5.2 Resultados del Experimento Monte Carlo ($50{,}000$ pasos temporales)
Distribución de estados reales simulados:
* $S$ (Susceptibles): $18{,}074$ ($36.15\%$)
* $I$ (Infectados): $11{,}672$ ($23.34\%$)
* $R$ (Recuperados): $20{,}254$ ($40.51\%$)

#### Tabla 1. Comparativa de desempeño estadístico
| Métrica | Algoritmo de Viterbi | Baseline (Emisión pura) | Diferencia ($\Delta$) |
| :--- | :---: | :---: | :---: |
| **Exactitud Global** | **$59.87\%$** | $53.34\%$ | **$+6.53\%$** |
| **Intervalo de Confianza (95%)** | **$[59.44\%, 60.30\%]$** | $[52.90\%, 53.78\%]$ | Separación estricta ($p < 0.001$) |
| **Sensibilidad / Recall $S$** | **$45.64\%$** | $0.00\%$ | **$+45.64\%$** |
| **Sensibilidad / Recall $I$** | $59.99\%$ | **$89.92\%$** | $-29.93\%$ |
| **Sensibilidad / Recall $R$** | $72.49\%$ | **$79.86\%$** | $-7.37\%$ |
| **Precisión $S$** | **$55.13\%$** | $0.00\%$ | **$+55.13\%$** |
| **Precisión $I$** | **$76.79\%$** | $52.09\%$ | **$+24.70\%$** |
| **Precisión $R$** | **$56.65\%$** | $54.18\%$ | **$+2.47\%$** |
| **F1-Score $S$** | **$0.4994$** | $0.0000$ | **$+0.4994$** |
| **F1-Score $I$** | **$0.6736$** | $0.6597$ | **$+0.0139$** |
| **F1-Score $R$** | $0.6360$ | **$0.6456$** | $-0.0096$ |
| **Macro F1-Score** | **$0.6030$** | $0.4351$ | **$+0.1679$** |
| **Acierto de Secuencia Exacta ($50/50$)** | $0.00\%$ ($0/1000$) | $0.00\%$ ($0/1000$) | $0.00\%$ |

#### Tabla 2. Matrices de confusión empíricas ($50{,}000$ transiciones)
* **Viterbi (Filas: Real, Columnas: Predicho):**
  $$\begin{pmatrix}
  \text{Real } S: & 8{,}249 & 966 & 8{,}859 \\
  \text{Real } I: & 2{,}292 & 7{,}002 & 2{,}378 \\
  \text{Real } R: & 4{,}421 & 1{,}150 & 14{,}683
  \end{pmatrix}$$

* **Baseline (Filas: Real, Columnas: Predicho):**
  $$\begin{pmatrix}
  \text{Real } S: & 0 & 5{,}571 & 12{,}503 \\
  \text{Real } I: & 0 & 10{,}495 & 1{,}177 \\
  \text{Real } R: & 0 & 4{,}080 & 16{,}174
  \end{pmatrix}$$

---

## 6. Discusión

1. **Resolución de la ambigüedad en el inicio epidémico:**
   El análisis de la secuencia de cinco días ilustra con nitidez el aporte de la dinámica markoviana. Ante los reportes iniciales de casos "bajos", el clasificador base diagnostica inmediatamente una población en fase de recuperación ($R, R$), conclusión biológicamente insostenible cuando la prevalencia inicial es susceptible ($\pi_S = 0.90$). Viterbi pondera el prior $\pi$ y la probabilidad de permanencia $A_{1,1}=0.70$, prediciendo certeramente la persistencia de susceptibles ($S, S, S$) antes de transicionar a infección ($I, I$) ante el incremento de casos.
2. **Superioridad en balance armónico (Macro F1):**
   Aunque el *baseline* exhibe una sensibilidad aparente muy alta en Infectados ($89.92\%$) y Recuperados ($79.86\%$), dicho fenómeno constituye un artefacto inducido por clasificar agresivamente toda observación en dichas dos categorías. Esto se traduce en una precisión deficiente en Infectados ($52.09\%$, equivalente a lanzar una moneda) y una insensibilidad absoluta ante el estado Susceptible ($F1 = 0.0$). En contraste, Viterbi preserva un equilibrio armónico entre todas las clases, logrando una precisión en infectados de $76.79\%$ y un Macro F1 de $0.6030$ frente a $0.4351$ ($+16.79$ puntos porcentuales).
3. **Límite práctico bajo dispersión de emisiones:**
   Pese a su superioridad, la exactitud global de Viterbi no excede el $60\%$. Este techo empírico se explica al analizar la matriz de emisión $B$: los estados $S$ y $R$ compiten estrechamente por la emisión de casos bajos ($0.70$ frente a $0.80$), mientras que los casos medios poseen densidades considerables en los tres compartimentos ($0.25, 0.30, 0.15$). La correlación temporal mitiga sustancialmente el error, pero no puede anular la entropía propia del ruido observacional.

---

## 7. Conclusiones y Declaraciones

### 7.1 Conclusiones
1. La modelación de la dependencia temporal mediante el algoritmo de Viterbi incrementa la exactitud de inferencia en $+6.53$ puntos porcentuales respecto a la clasificación estática, con intervalos de confianza al $95\%$ mutuamente excluyentes ($[59.44\%, 60.30\%]$ vs. $[52.90\%, 53.78\%]$).
2. Los métodos de decisión epidemiológica basados exclusivamente en el reporte actual son propensos a sesgos graves en fases tempranas, al no poder discriminar poblaciones susceptibles de poblaciones recuperadas ante niveles idénticos de contagio aparente.
3. El uso del algoritmo de Viterbi es indispensable para evitar falsas alarmas de recuperación, aunque su exactitud efectiva dependerá directamente de la especificidad diagnóstica de la matriz de emisión.

### 7.2 Declaración de Ética y Transparencia
* **Reproducibilidad:** Todos los datos provienen del script ejecutable [`simulacion_hmm.py`](file:///c:/Users/USUARIO/OneDrive/Documentos/Simulación/.agentsskillsarticulo-hmm/simulacion_hmm.py) auditado en entorno local sin datos fabricados.
* **Uso de IA:** Se certifica que la asistencia automatizada se limitó a tareas mecánicas de codificación y tabulación; las preguntas, diseño experimental, selección del baseline y aprobación de conclusiones fueron decididas de manera soberana por el equipo humano.
