import math
import random
import json

# Constantes del modelo didáctico (caso-epidemia.md)
STATES = ["S", "I", "R"] # 0: Susceptible, 1: Infectado, 2: Recuperado
OBS = ["bajos", "medios", "altos"] # 0: bajos, 1: medios, 2: altos

PI = [0.90, 0.08, 0.02]

# E1: Nominal
A_NOM = [
    [0.70, 0.25, 0.05],
    [0.05, 0.55, 0.40],
    [0.20, 0.05, 0.75]
]
B_NOM = [
    [0.70, 0.25, 0.05],
    [0.10, 0.30, 0.60],
    [0.80, 0.15, 0.05]
]

# E2: Perturbación del 20% en Matriz de Transición A (simula cambios en transmisibilidad y pérdida de inmunidad)
# Mezcla convexa: 0.80 * A_nom + 0.20 * Uniforme(3)
A_PERT = [
    [round(0.70 * 0.8 + 0.2 / 3, 4), round(0.25 * 0.8 + 0.2 / 3, 4), round(0.05 * 0.8 + 0.2 / 3, 4)],
    [round(0.05 * 0.8 + 0.2 / 3, 4), round(0.55 * 0.8 + 0.2 / 3, 4), round(0.40 * 0.8 + 0.2 / 3, 4)],
    [round(0.20 * 0.8 + 0.2 / 3, 4), round(0.05 * 0.8 + 0.2 / 3, 4), round(0.75 * 0.8 + 0.2 / 3, 4)]
]

# E3: Perturbación del 20% en Matriz de Emisión B (simula aumento de subregistro y confusión en reportes)
# Mezcla convexa: 0.80 * B_nom + 0.20 * Uniforme(3)
B_PERT = [
    [round(0.70 * 0.8 + 0.2 / 3, 4), round(0.25 * 0.8 + 0.2 / 3, 4), round(0.05 * 0.8 + 0.2 / 3, 4)],
    [round(0.10 * 0.8 + 0.2 / 3, 4), round(0.30 * 0.8 + 0.2 / 3, 4), round(0.60 * 0.8 + 0.2 / 3, 4)],
    [round(0.80 * 0.8 + 0.2 / 3, 4), round(0.15 * 0.8 + 0.2 / 3, 4), round(0.05 * 0.8 + 0.2 / 3, 4)]
]

def viterbi(obs_seq, pi, a, b):
    T = len(obs_seq)
    K = len(pi)
    log_pi = [math.log(p) if p > 0 else -1e12 for p in pi]
    log_a = [[math.log(p) if p > 0 else -1e12 for p in row] for row in a]
    log_b = [[math.log(p) if p > 0 else -1e12 for p in row] for row in b]
    
    viterbi_table = [[0.0] * K for _ in range(T)]
    backpointer = [[0] * K for _ in range(T)]
    
    for k in range(K):
        viterbi_table[0][k] = log_pi[k] + log_b[k][obs_seq[0]]
        backpointer[0][k] = 0
        
    for t in range(1, T):
        yt = obs_seq[t]
        for k in range(K):
            max_prob = -1e12
            best_prev = 0
            for j in range(K):
                prob = viterbi_table[t-1][j] + log_a[j][k] + log_b[k][yt]
                if prob > max_prob:
                    max_prob = prob
                    best_prev = j
            viterbi_table[t][k] = max_prob
            backpointer[t][k] = best_prev
            
    best_last_state = 0
    max_final_prob = -1e12
    for k in range(K):
        if viterbi_table[T-1][k] > max_final_prob:
            max_final_prob = viterbi_table[T-1][k]
            best_last_state = k
            
    opt_path = [0] * T
    opt_path[T-1] = best_last_state
    for t in range(T-2, -1, -1):
        opt_path[t] = backpointer[t+1][opt_path[t+1]]
        
    return opt_path, max_final_prob

def sample_categorical(prob_dist, rng):
    r = rng.random()
    cum = 0.0
    for idx, p in enumerate(prob_dist):
        cum += p
        if r <= cum:
            return idx
    return len(prob_dist) - 1

def run_scenario(A_gen, B_gen, A_dec, B_dec, N=100, T=50, seed=42):
    rng = random.Random(seed)
    acc_list = []
    
    for _ in range(N):
        true_states = [sample_categorical(PI, rng)]
        obs_seq = [sample_categorical(B_gen[true_states[0]], rng)]
        
        for t in range(1, T):
            st = sample_categorical(A_gen[true_states[-1]], rng)
            yt = sample_categorical(B_gen[st], rng)
            true_states.append(st)
            obs_seq.append(yt)
            
        pred, _ = viterbi(obs_seq, PI, A_dec, B_dec)
        acc = sum(1 for yt, yp in zip(true_states, pred) if yt == yp) / T
        acc_list.append(acc)
        
    mean_val = sum(acc_list) / N
    variance = sum((x - mean_val) ** 2 for x in acc_list) / (N - 1)
    s = math.sqrt(variance)
    min_val = min(acc_list)
    max_val = max(acc_list)
    margin = 1.96 * (s / math.sqrt(N))
    ci95 = (mean_val - margin, mean_val + margin)
    
    return {
        "mean": mean_val,
        "std": s,
        "min": min_val,
        "max": max_val,
        "margin": margin,
        "ci95": ci95,
        "raw_acc": acc_list
    }

if __name__ == "__main__":
    N_SIM = 100
    T_LEN = 50
    SEED = 42
    
    print(f"=== SIMULACIÓN DE SENSIBILIDAD EN 3 ESCENARIOS (N={N_SIM}, T={T_LEN}, SEED={SEED}) ===")
    
    # 1. E1: Nominal (A_nom, B_nom)
    e1 = run_scenario(A_NOM, B_NOM, A_NOM, B_NOM, N=N_SIM, T=T_LEN, seed=SEED)
    
    # 2. E2: Perturbación en Transición (Generador con A_pert, B_nom; decodificador evalúa degradación intrínseca)
    e2 = run_scenario(A_PERT, B_NOM, A_PERT, B_NOM, N=N_SIM, T=T_LEN, seed=SEED)
    
    # 3. E3: Perturbación en Emisión (Generador con A_nom, B_pert; decodificador evalúa degradación por entropía de emisión)
    e3 = run_scenario(A_NOM, B_PERT, A_NOM, B_PERT, N=N_SIM, T=T_LEN, seed=SEED)
    
    print("\n--- RESULTADOS TABLA 3 ---")
    print(f"E1: Nominal      | Media: {e1['mean']:.4f} | s: {e1['std']:.4f} | Min: {e1['min']:.4f} | Max: {e1['max']:.4f} | IC95%: [{e1['ci95'][0]:.4f}, {e1['ci95'][1]:.4f}]")
    print(f"E2: Perturbado A | Media: {e2['mean']:.4f} | s: {e2['std']:.4f} | Min: {e2['min']:.4f} | Max: {e2['max']:.4f} | IC95%: [{e2['ci95'][0]:.4f}, {e2['ci95'][1]:.4f}]")
    print(f"E3: Perturbado B | Media: {e3['mean']:.4f} | s: {e3['std']:.4f} | Min: {e3['min']:.4f} | Max: {e3['max']:.4f} | IC95%: [{e3['ci95'][0]:.4f}, {e3['ci95'][1]:.4f}]")
