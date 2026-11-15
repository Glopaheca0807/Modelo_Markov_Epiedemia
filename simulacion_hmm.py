import math
import random
import json

# Constantes del modelo (caso-epidemia.md)
STATES = ["S", "I", "R"] # 0: Susceptible, 1: Infectado, 2: Recuperado
OBS = ["bajos", "medios", "altos"] # 0: bajos, 1: medios, 2: altos

PI = [0.90, 0.08, 0.02]
A = [
    [0.70, 0.25, 0.05],
    [0.05, 0.55, 0.40],
    [0.20, 0.05, 0.75]
]
B = [
    [0.70, 0.25, 0.05],
    [0.10, 0.30, 0.60],
    [0.80, 0.15, 0.05]
]

def viterbi(obs_seq, pi, a, b):
    T = len(obs_seq)
    K = len(pi)
    
    # Usar log-probabilidades para evitar underflow numérico
    log_pi = [math.log(p) if p > 0 else -1e12 for p in pi]
    log_a = [[math.log(p) if p > 0 else -1e12 for p in row] for row in a]
    log_b = [[math.log(p) if p > 0 else -1e12 for p in row] for row in b]
    
    # viterbi_table[t][k] = max log-prob de secuencia que termina en estado k en tiempo t
    viterbi_table = [[0.0] * K for _ in range(T)]
    backpointer = [[0] * K for _ in range(T)]
    
    # Inicialización t = 0
    y0 = obs_seq[0]
    for k in range(K):
        viterbi_table[0][k] = log_pi[k] + log_b[k][y0]
        backpointer[0][k] = 0
        
    # Recursión t = 1 .. T-1
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
            
    # Terminación
    best_last_state = 0
    max_final_prob = -1e12
    for k in range(K):
        if viterbi_table[T-1][k] > max_final_prob:
            max_final_prob = viterbi_table[T-1][k]
            best_last_state = k
            
    # Reconstrucción de la trayectoria óptima (backtracking)
    opt_path = [0] * T
    opt_path[T-1] = best_last_state
    for t in range(T-2, -1, -1):
        opt_path[t] = backpointer[t+1][opt_path[t+1]]
        
    return opt_path, max_final_prob, viterbi_table, backpointer

def baseline_classifier(obs_seq, b):
    # argmax_j B_{j, y_t}
    path = []
    for yt in obs_seq:
        best_state = 0
        max_b = -1.0
        for j in range(len(b)):
            if b[j][yt] > max_b:
                max_b = b[j][yt]
                best_state = j
        path.append(best_state)
    return path

def sample_categorical(prob_dist, rng):
    r = rng.random()
    cum = 0.0
    for idx, p in enumerate(prob_dist):
        cum += p
        if r <= cum:
            return idx
    return len(prob_dist) - 1

def run_simulation(N=1000, T=50, seed=42):
    rng = random.Random(seed)
    
    total_steps = N * T
    
    correct_vit = 0
    correct_base = 0
    exact_seq_vit = 0
    exact_seq_base = 0
    
    # Exactitud por trayectoria para calcular s, min, max, IC95% como en Tabla 3 de articulo.pdf
    traj_acc_vit = []
    traj_acc_base = []
    
    # Matrices de confusión: conf[true_state][pred_state]
    conf_vit = [[0]*3 for _ in range(3)]
    conf_base = [[0]*3 for _ in range(3)]
    
    state_counts = [0, 0, 0]
    
    for i in range(N):
        # Generar trayectoria latente y observaciones
        true_states = [sample_categorical(PI, rng)]
        obs_seq = [sample_categorical(B[true_states[0]], rng)]
        
        for t in range(1, T):
            st = sample_categorical(A[true_states[-1]], rng)
            yt = sample_categorical(B[st], rng)
            true_states.append(st)
            obs_seq.append(yt)
            
        # Decodificación Viterbi
        pred_vit, _, _, _ = viterbi(obs_seq, PI, A, B)
        # Decodificación Baseline
        pred_base = baseline_classifier(obs_seq, B)
        
        # Comparación por trayectoria
        matches_vit = sum(1 for yt, yp in zip(true_states, pred_vit) if yt == yp)
        matches_base = sum(1 for yt, yp in zip(true_states, pred_base) if yt == yp)
        
        traj_acc_vit.append(matches_vit / T)
        traj_acc_base.append(matches_base / T)
        
        correct_vit += matches_vit
        correct_base += matches_base
        
        if matches_vit == T:
            exact_seq_vit += 1
        if matches_base == T:
            exact_seq_base += 1
            
        for yt, pv, pb in zip(true_states, pred_vit, pred_base):
            state_counts[yt] += 1
            conf_vit[yt][pv] += 1
            conf_base[yt][pb] += 1
            
    def compute_metrics(conf, total_steps, state_counts):
        acc = sum(conf[i][i] for i in range(3)) / total_steps
        recalls = []
        precisions = []
        f1s = []
        for i in range(3):
            tp = conf[i][i]
            fn = state_counts[i] - tp
            pred_count = sum(conf[r][i] for r in range(3))
            fp = pred_count - tp
            
            rec = tp / state_counts[i] if state_counts[i] > 0 else 0.0
            prec = tp / pred_count if pred_count > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            
            recalls.append(rec)
            precisions.append(prec)
            f1s.append(f1)
            
        macro_f1 = sum(f1s) / len(f1s)
        return acc, recalls, precisions, f1s, macro_f1

    acc_vit, rec_vit, prec_vit, f1_vit, macro_vit = compute_metrics(conf_vit, total_steps, state_counts)
    acc_base, rec_base, prec_base, f1_base, macro_base = compute_metrics(conf_base, total_steps, state_counts)
    
    def traj_stats(acc_list):
        n = len(acc_list)
        mean_val = sum(acc_list) / n
        variance = sum((x - mean_val) ** 2 for x in acc_list) / (n - 1)
        s = math.sqrt(variance)
        min_val = min(acc_list)
        max_val = max(acc_list)
        margin = 1.96 * (s / math.sqrt(n))
        ci95 = (mean_val - margin, mean_val + margin)
        return {
            "mean": mean_val,
            "std": s,
            "min": min_val,
            "max": max_val,
            "margin": margin,
            "ci95": ci95
        }
        
    stats_vit = traj_stats(traj_acc_vit)
    stats_base = traj_stats(traj_acc_base)
    
    return {
        "N": N,
        "T": T,
        "seed": seed,
        "total_steps": total_steps,
        "state_counts": state_counts,
        "state_prevalences": [c / total_steps for c in state_counts],
        "viterbi": {
            "accuracy": acc_vit,
            "stats": stats_vit,
            "exact_sequence_rate": exact_seq_vit / N,
            "recall": rec_vit,
            "precision": prec_vit,
            "f1": f1_vit,
            "macro_f1": macro_vit,
            "confusion_matrix": conf_vit
        },
        "baseline": {
            "accuracy": acc_base,
            "stats": stats_base,
            "exact_sequence_rate": exact_seq_base / N,
            "recall": rec_base,
            "precision": prec_base,
            "f1": f1_base,
            "macro_f1": macro_base,
            "confusion_matrix": conf_base
        }
    }

if __name__ == "__main__":
    obs_5 = [0, 0, 1, 2, 1]
    opt_path_5, max_p, v_table, bp = viterbi(obs_5, PI, A, B)
    base_path_5 = baseline_classifier(obs_5, B)
    
    print("=== TRAZADO CASO DIDÁCTICO T=5 ===")
    print(f"Observaciones: {[OBS[o] for o in obs_5]}")
    print(f"Viterbi óptimo: {[STATES[s] for s in opt_path_5]}")
    print(f"Baseline:       {[STATES[s] for s in base_path_5]}")
    print(f"Log-Probabilidad Viterbi: {max_p:.6f} (Probabilidad: {math.exp(max_p):.6e})")
    
    res = run_simulation(N=1000, T=50, seed=42)
    print("\n=== ESTADÍSTICAS TABLA 3 (PLANTILLA PDF) ===")
    v_st = res["viterbi"]["stats"]
    b_st = res["baseline"]["stats"]
    print(f"Viterbi:  Media={v_st['mean']:.4f}, s={v_st['std']:.4f}, Min={v_st['min']:.4f}, Max={v_st['max']:.4f}, IC95=[{v_st['ci95'][0]:.4f}, {v_st['ci95'][1]:.4f}]")
    print(f"Baseline: Media={b_st['mean']:.4f}, s={b_st['std']:.4f}, Min={b_st['min']:.4f}, Max={b_st['max']:.4f}, IC95=[{b_st['ci95'][0]:.4f}, {b_st['ci95'][1]:.4f}]")
