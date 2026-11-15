# Caso didáctico: dinámica de una epidemia

Una autoridad de salud registra el número de casos diarios reportados, clasificados como bajos, medios o altos. Explorar si un HMM permite inferir fases supuestas de la población: susceptible, infectado o recuperado. No se aporta un dataset real. El nivel de casos reportados por sí solo no demuestra en qué fase se encuentra la población.

Observaciones ilustrativas: bajos, bajos, medios, altos, medios.

Parámetros hipotéticos para una simulación (no estimados de una epidemia real):
A = [[0.70, 0.25, 0.05], [0.05, 0.55, 0.40], [0.20, 0.05, 0.75]]
B = [[0.70, 0.25, 0.05], [0.10, 0.30, 0.60], [0.80, 0.15, 0.05]]
pi = [0.90, 0.08, 0.02]

A: filas/columnas susceptible, infectado, recuperado. B: filas susceptible, infectado, recuperado; columnas casos diarios bajos, medios, altos.

Tareas: formular pregunta, justificar HMM, proponer método sencillo de comparación, datos, métrica y experimento controlado. Distinguir decodificación con parámetros conocidos de entrenamiento. No inventar hallazgos, fuentes ni cifras.
