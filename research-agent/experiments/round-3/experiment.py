"""
Round 3 실험: KOI 누수 패턴의 합성 데이터 재현 (Round 2 이월 과제 반영판)
근거 문서: experiments/round-3/plan.md (반드시 함께 읽을 것)

⚠️ 이 스크립트는 실제 KOI cumulative table을 사용하지 않는다. 외부 네트워크 다운로드 없이
전부 인메모리로 합성 데이터를 생성한다 (plan.md 2절 "Data Source (pinned)").
데이터 버전: round-3-synth-v1 (파라미터를 바꾸면 v2로 승격하고 이 주석과 round_summary.md에 기록할 것).

Round 2 대비 변경점 (plan.md 0절 표, 이월 과제 #1/#2/#3):
  1. koi_score 공식 재설계: 플래그 가중치 0.5 -> 0.15 (alpha=0.85), 노이즈 표준편차 0.05 -> 0.25.
     alpha/sigma 자체도 그리드 탐색으로 확정한다 (Round 2는 고정값을 그대로 채택해 조기 포화됨).
  2. gamma1 그리드를 [0.8,2.0]에서 [2.0,4.0]으로 확장. 탐색 전용 EXPLORATION_SEED=99를
     최종 보고 seed{0,1,2}와 명시적으로 분리 (Round 2는 탐색에 seed=0을 재사용해 경미한
     이중사용 문제가 있었음 — 이번에는 구조적으로 차단).
  3. 탐색(gamma1, koi_score) 단계와 최종 평가 단계 모두 RandomForestClassifier(n_estimators=300)로
     통일 (Round 2는 탐색 200 vs 최종 300으로 달라 리뷰 지적을 받음).

실행: runner/.venv/bin/python experiments/round-3/experiment.py
출력:
  - experiments/round-3/results_fold_level.csv        (레짐×모델×seed×fold 원자료, 최종 3-seed만)
  - experiments/round-3/results_summary.csv           (레짐×모델별 3-seed 평균±표준편차)
  - experiments/round-3/calibration_log_gamma1.csv     (gamma1 그리드 탐색 기록, exploration seed=99)
  - experiments/round-3/calibration_log_koi_score.csv  (koi_score alpha/sigma 그리드 탐색 기록, exploration seed=99)
  - experiments/round-3/synthetic_dataset_v1.csv       (최종 채택 데이터셋)
  - stdout (run 시 리다이렉트하여 experiment_run.log로 보관)
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# 0. 고정 파라미터 (plan.md 3절, round-3-synth-v1)
# ---------------------------------------------------------------------------
DATA_SEED = 42
N_SYSTEMS = 6000
CANDIDATE_COUNT_PROBS = {1: 0.50, 2: 0.35, 3: 0.15}
TARGET_POSITIVE_RATE = 0.40   # 양성(CONFIRMED/CANDIDATE) : 음성(FALSE POSITIVE) = 40:60
FLAG_FLIP_PROB = 0.03         # koi_fpflag_* 노이즈율 (plan.md 3.5절, Round 2와 동일 유지)

# 물리 피처 loading과 단조 변환 (plan.md 3.3절 표, Round 2와 동일 유지)
PHYSICS_FEATURES = {
    "koi_period":    (0.15, lambda x: np.exp(2.5 + 0.7 * x)),
    "koi_duration":  (0.25, lambda x: np.exp(1.0 + 0.4 * x)),
    "koi_depth":     (0.45, lambda x: np.exp(6.5 + 0.9 * x)),
    "koi_prad":      (0.50, lambda x: np.exp(0.7 + 0.6 * x)),
    "koi_impact":    (-0.30, lambda x: np.clip(0.5 + 0.25 * x, 0, 1.5)),
    "koi_steff":     (0.10, lambda x: 5500 + 700 * x),
    "koi_srad":      (0.20, lambda x: np.exp(0.0 + 0.3 * x)),
    "koi_model_snr": (0.55, lambda x: np.exp(2.0 + 0.5 * x)),
}
PHYSICS_COLS = list(PHYSICS_FEATURES.keys())
FLAG_COLS = [f"koi_fpflag_{k}" for k in range(1, 5)]
SCORE_COL = "koi_score"

CV_SEEDS = [0, 1, 2]              # 최종 보고 seed (plan.md 6절)
EXPLORATION_SEED = 99             # 탐색 전용 seed — 최종 보고 seed와 명시적으로 분리 (plan.md 3.4/6절)
N_SPLITS = 5
N_ESTIMATORS = 300                # 탐색·최종 평가 공통 (plan.md 6절 "설정 일치")

GAMMA1_GRID = [2.0, 2.3, 2.6, 3.0, 3.4, 3.8, 4.0]
TARGET_PRAUC_CENTER = 0.72
TARGET_PRAUC_RANGE = (0.70, 0.74)
ACCEPTABLE_PRAUC_RANGE = (0.65, 0.78)

# koi_score (alpha, sigma) 그리드 — plan.md 3.6절 사전 시험에서 유력했던 조합 + 주변 격자
KOI_SCORE_GRID = [
    (0.90, 0.15),
    (0.85, 0.15),
    (0.85, 0.25),
    (0.80, 0.25),
]
SUSPECT_TARGET_RANGE = (0.80, 0.90)   # Suspect-added PR-AUC 목표 대역 (plan.md 3.6/8절)
MIN_DELTA_LEAKED_SUSPECT = 0.04       # 2차 성공기준 (b) 정량 간격 조건 (plan.md 8절)

REGIMES = {
    "Clean (physics-only)": PHYSICS_COLS,
    "Suspect-added": PHYSICS_COLS + [SCORE_COL],
    "Leaked (leakage-inclusive)": PHYSICS_COLS + FLAG_COLS + [SCORE_COL],
}


# ---------------------------------------------------------------------------
# 1. gamma0 보정 (수치적분, plan.md 3.4절) — Round 2와 동일 (결정적, 표본 추출 아님)
# ---------------------------------------------------------------------------
def calibrate_gamma0(gamma1, target_rate=TARGET_POSITIVE_RATE, tol=1e-4):
    s_grid = np.linspace(-8, 8, 20001)
    weights = norm.pdf(s_grid)
    weights = weights / weights.sum()

    def mean_rate(gamma0):
        p = 1.0 / (1.0 + np.exp(-(gamma1 * s_grid + gamma0)))
        return float(np.sum(p * weights))

    lo, hi = -6.0, 6.0
    for _ in range(200):
        mid = (lo + hi) / 2
        rate = mean_rate(mid)
        if abs(rate - target_rate) < tol:
            return mid
        if rate < target_rate:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------------------
# 2. 합성 데이터 생성 (plan.md 3.1~3.6절) — 단일 rng를 순차적으로 소비한다.
#    koi_score는 이제 (alpha, sigma) 파라미터를 받는다 (Round 2는 0.5/0.05 고정값이었음).
# ---------------------------------------------------------------------------
def build_dataset(rng, gamma1, gamma0, alpha, sigma):
    counts = rng.choice(
        list(CANDIDATE_COUNT_PROBS.keys()),
        size=N_SYSTEMS,
        p=list(CANDIDATE_COUNT_PROBS.values()),
    )
    u = rng.normal(0, 1, size=N_SYSTEMS)

    sys_idx = np.repeat(np.arange(N_SYSTEMS), counts)
    n_rows = sys_idx.shape[0]

    v = rng.normal(0, 1, size=n_rows)
    s = 0.5 * u[sys_idx] + 0.7 * v
    s_std = s / np.sqrt(0.74)

    data = {"kepid_sim": sys_idx}
    for name, (b_k, transform) in PHYSICS_FEATURES.items():
        eps_k = rng.normal(0, 1, size=n_rows)
        x_std = b_k * s_std + np.sqrt(max(1 - b_k ** 2, 0.0)) * eps_k
        data[name] = transform(x_std)

    p_label = 1.0 / (1.0 + np.exp(-(gamma1 * s_std + gamma0)))
    y = rng.binomial(1, p_label)
    data["y"] = y

    for k in range(1, 5):
        flip = rng.binomial(1, FLAG_FLIP_PROB, size=n_rows)
        fpflag = np.logical_xor((1 - y).astype(bool), flip.astype(bool)).astype(int)
        data[f"koi_fpflag_{k}"] = fpflag

    flag_mat = np.column_stack([data[c] for c in FLAG_COLS])
    noise = rng.normal(0, sigma, size=n_rows)
    raw = alpha * (1.0 / (1.0 + np.exp(-2.0 * s_std))) + (1 - alpha) * np.mean(1 - flag_mat, axis=1) + noise
    data[SCORE_COL] = np.clip(raw, 0, 1)

    df = pd.DataFrame(data)
    return df, s_std


# ---------------------------------------------------------------------------
# 3. gamma1 그리드 탐색 — physics-only 레짐, RandomForest(n_estimators=300),
#    EXPLORATION_SEED=99, 5-fold 단일 시행으로 PR-AUC가 0.70~0.74(허용 0.65~0.78)에
#    들어오는 gamma1을 선택한다. 최종 보고 seed{0,1,2}는 사용하지 않는다 (이중사용 차단).
# ---------------------------------------------------------------------------
def quick_physics_only_prauc(gamma1, gamma0, alpha_placeholder=0.85, sigma_placeholder=0.25):
    # koi_score는 physics-only 평가에 쓰이지 않으므로 placeholder 값으로 데이터만 생성한다.
    rng = np.random.default_rng(DATA_SEED)
    df, _ = build_dataset(rng, gamma1, gamma0, alpha_placeholder, sigma_placeholder)
    X = df[PHYSICS_COLS].values
    y = df["y"].values
    groups = df["kepid_sim"].values

    cv = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=EXPLORATION_SEED)
    scores = []
    for train_idx, test_idx in cv.split(X, y, groups):
        model = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=EXPLORATION_SEED, n_jobs=-1)
        model.fit(X[train_idx], y[train_idx])
        proba = model.predict_proba(X[test_idx])[:, 1]
        scores.append(average_precision_score(y[test_idx], proba))
    return float(np.mean(scores))


def select_gamma1():
    log_rows = []
    best = None
    for gamma1 in GAMMA1_GRID:
        gamma0 = calibrate_gamma0(gamma1)
        prauc = quick_physics_only_prauc(gamma1, gamma0)
        in_target = TARGET_PRAUC_RANGE[0] <= prauc <= TARGET_PRAUC_RANGE[1]
        dist = abs(prauc - TARGET_PRAUC_CENTER)
        log_rows.append({
            "gamma1": gamma1, "gamma0": gamma0, "quick_physics_only_prauc": prauc,
            "n_estimators": N_ESTIMATORS, "exploration_seed": EXPLORATION_SEED,
            "in_target_range_0.70_0.74": in_target, "dist_to_center_0.72": dist,
        })
        print(f"[gamma1 calibration] gamma1={gamma1:.2f} gamma0={gamma0:.4f} "
              f"quick physics-only PR-AUC={prauc:.4f} (n_est={N_ESTIMATORS}, "
              f"exploration_seed={EXPLORATION_SEED}) in_target={in_target}")
        if best is None or dist < best["dist_to_center_0.72"]:
            best = log_rows[-1]

    log_df = pd.DataFrame(log_rows)
    return best["gamma1"], best["gamma0"], log_df


# ---------------------------------------------------------------------------
# 4. koi_score (alpha, sigma) 그리드 탐색 — 확정된 gamma1*/gamma0*로 3개 레짐을
#    EXPLORATION_SEED=99, n_estimators=300, 5-fold 단일 시행으로 평가하고,
#    Suspect-added PR-AUC가 [0.80,0.90]에 들고 Δ(Leaked-Suspect)>=0.04인 조합을 선택한다.
#    (plan.md 3.6/8절 — Round 2의 "형식적 통과, 실질적 미달" 재발 방지)
# ---------------------------------------------------------------------------
def quick_three_regime_prauc(gamma1, gamma0, alpha, sigma):
    rng = np.random.default_rng(DATA_SEED)
    df, _ = build_dataset(rng, gamma1, gamma0, alpha, sigma)
    y = df["y"].values
    groups = df["kepid_sim"].values

    out = {}
    for regime_name, cols in REGIMES.items():
        X = df[cols].values
        cv = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=EXPLORATION_SEED)
        scores = []
        for train_idx, test_idx in cv.split(X, y, groups):
            model = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=EXPLORATION_SEED, n_jobs=-1)
            model.fit(X[train_idx], y[train_idx])
            proba = model.predict_proba(X[test_idx])[:, 1]
            scores.append(average_precision_score(y[test_idx], proba))
        out[regime_name] = float(np.mean(scores))
    return out


def select_koi_score_params(gamma1_star, gamma0_star):
    log_rows = []
    candidates = []
    for alpha, sigma in KOI_SCORE_GRID:
        res = quick_three_regime_prauc(gamma1_star, gamma0_star, alpha, sigma)
        clean = res["Clean (physics-only)"]
        suspect = res["Suspect-added"]
        leaked = res["Leaked (leakage-inclusive)"]
        delta_suspect_clean = suspect - clean
        delta_leaked_suspect = leaked - suspect
        in_suspect_target = SUSPECT_TARGET_RANGE[0] <= suspect <= SUSPECT_TARGET_RANGE[1]
        meets_min_gap = delta_leaked_suspect >= MIN_DELTA_LEAKED_SUSPECT
        row = {
            "alpha": alpha, "sigma": sigma, "flag_weight_1_minus_alpha": round(1 - alpha, 4),
            "n_estimators": N_ESTIMATORS, "exploration_seed": EXPLORATION_SEED,
            "clean_prauc": clean, "suspect_prauc": suspect, "leaked_prauc": leaked,
            "delta_suspect_clean": delta_suspect_clean, "delta_leaked_suspect": delta_leaked_suspect,
            "suspect_in_target_0.80_0.90": in_suspect_target,
            "meets_min_gap_0.04": meets_min_gap,
        }
        log_rows.append(row)
        print(f"[koi_score calibration] alpha={alpha:.2f}(flag_w={1-alpha:.2f}) sigma={sigma:.2f} "
              f"Clean={clean:.4f} Suspect={suspect:.4f} Leaked={leaked:.4f} "
              f"Δ(Susp-Clean)={delta_suspect_clean:+.4f} Δ(Leaked-Susp)={delta_leaked_suspect:+.4f} "
              f"in_target={in_suspect_target} meets_min_gap={meets_min_gap}")
        if in_suspect_target and meets_min_gap:
            candidates.append(row)

    log_df = pd.DataFrame(log_rows)

    if candidates:
        # 목표 대역 중심(0.85)에 가장 가까운 suspect_prauc를 우선, 동률이면 delta_leaked_suspect가 큰 쪽
        target_center = sum(SUSPECT_TARGET_RANGE) / 2
        best = min(candidates, key=lambda r: (abs(r["suspect_prauc"] - target_center), -r["delta_leaked_suspect"]))
        selection_note = "목표 대역+최소간격 조건을 모두 만족하는 후보 중 선택"
    else:
        # 조건을 만족하는 후보가 없으면, delta_leaked_suspect가 가장 큰 조합을 채택하고 투명하게 기록
        best = max(log_rows, key=lambda r: r["delta_leaked_suspect"])
        selection_note = ("목표 대역+최소간격 조건을 만족하는 후보 없음 — "
                           "delta_leaked_suspect 최대인 조합을 차선책으로 채택 (round_summary.md에 한계로 기록 필요)")

    print(f"[koi_score calibration] 선택 근거: {selection_note}")
    return best["alpha"], best["sigma"], log_df, selection_note


# ---------------------------------------------------------------------------
# 5. 최종 평가: 3개 레짐 x 2개 모델 x 3 seed x 5 fold (plan.md 6절, 최종 보고 seed만 사용)
# ---------------------------------------------------------------------------
def build_model(model_name, seed):
    if model_name == "Logistic Regression":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=seed)),
        ])
    elif model_name == "Random Forest":
        return RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=seed, n_jobs=-1)
    raise ValueError(model_name)


def run_full_evaluation(df):
    y = df["y"].values
    groups = df["kepid_sim"].values

    fold_records = []
    for regime_name, cols in REGIMES.items():
        X_full = df[cols].values
        for model_name in ["Logistic Regression", "Random Forest"]:
            for seed in CV_SEEDS:
                cv = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=seed)
                for fold_i, (train_idx, test_idx) in enumerate(cv.split(X_full, y, groups)):
                    model = build_model(model_name, seed)
                    model.fit(X_full[train_idx], y[train_idx])
                    proba = model.predict_proba(X_full[test_idx])[:, 1]
                    pr_auc = average_precision_score(y[test_idx], proba)
                    fold_records.append({
                        "regime": regime_name, "model": model_name, "seed": seed,
                        "fold": fold_i, "pr_auc": pr_auc,
                    })
                    print(f"[eval] regime={regime_name!r} model={model_name} seed={seed} "
                          f"fold={fold_i} PR-AUC={pr_auc:.4f}")

    fold_df = pd.DataFrame(fold_records)
    return fold_df


def summarize(fold_df):
    seed_level = fold_df.groupby(["regime", "model", "seed"])["pr_auc"].mean().reset_index()
    summary = seed_level.groupby(["regime", "model"])["pr_auc"].agg(["mean", "std"]).reset_index()
    summary.columns = ["regime", "model", "pr_auc_mean_3seed", "pr_auc_std_3seed"]

    clean_lookup = summary[summary["regime"] == "Clean (physics-only)"].set_index("model")["pr_auc_mean_3seed"]
    suspect_lookup = summary[summary["regime"] == "Suspect-added"].set_index("model")["pr_auc_mean_3seed"]

    def delta_vs_clean(row):
        if row["regime"] == "Clean (physics-only)":
            return np.nan
        return row["pr_auc_mean_3seed"] - clean_lookup[row["model"]]

    def delta_vs_suspect(row):
        if row["regime"] != "Leaked (leakage-inclusive)":
            return np.nan
        return row["pr_auc_mean_3seed"] - suspect_lookup[row["model"]]

    summary["delta_vs_clean"] = summary.apply(delta_vs_clean, axis=1)
    summary["delta_leaked_vs_suspect"] = summary.apply(delta_vs_suspect, axis=1)
    return summary


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    out_dir = "experiments/round-3"

    print("=" * 70)
    print("Round 3 실험: 합성 KOI 데이터로 label-leakage 패턴 재현 (Round 2 이월 과제 반영)")
    print("데이터 버전: round-3-synth-v1 (plan.md 참고)")
    print(f"탐색 전용 seed={EXPLORATION_SEED} / 최종 보고 seed={CV_SEEDS} (명시적으로 분리됨)")
    print(f"탐색·최종 평가 공통 n_estimators={N_ESTIMATORS} (Round 2의 200 vs 300 불일치 제거)")
    print("=" * 70)

    print("\n--- Step 1: gamma1/gamma0 보정 (확장 그리드 [2.0,4.0], exploration_seed=99) ---")
    gamma1_star, gamma0_star, gamma1_log = select_gamma1()
    gamma1_log.to_csv(f"{out_dir}/calibration_log_gamma1.csv", index=False)
    print(f"\n선택된 파라미터: gamma1*={gamma1_star:.3f}, gamma0*={gamma0_star:.4f}")

    print("\n--- Step 2: koi_score (alpha, sigma) 재보정 (gamma1*/gamma0* 기준, exploration_seed=99) ---")
    alpha_star, sigma_star, koi_score_log, selection_note = select_koi_score_params(gamma1_star, gamma0_star)
    koi_score_log.to_csv(f"{out_dir}/calibration_log_koi_score.csv", index=False)
    print(f"\n선택된 파라미터: alpha*={alpha_star:.3f} (flag 가중치={1-alpha_star:.3f}), sigma*={sigma_star:.3f}")
    print(f"선택 근거: {selection_note}")

    print("\n--- Step 3: 최종 데이터셋 생성 (round-3-synth-v1) ---")
    rng_final = np.random.default_rng(DATA_SEED)
    df, s_std = build_dataset(rng_final, gamma1_star, gamma0_star, alpha_star, sigma_star)
    n_rows = len(df)
    n_systems_realized = df["kepid_sim"].nunique()
    pos_rate = df["y"].mean()
    print(f"총 행 수: {n_rows} (시스템 수: {n_systems_realized}, 기대 시스템 수: {N_SYSTEMS})")
    print(f"양성 비율(y=1): {pos_rate:.4f} (목표 {TARGET_POSITIVE_RATE})")
    df.to_csv(f"{out_dir}/synthetic_dataset_v1.csv", index=False)

    print("\n--- Step 4: 3개 레짐 x 2개 모델 x 3 seed x 5 fold 최종 평가 (seed in {0,1,2}만 사용) ---")
    fold_df = run_full_evaluation(df)
    fold_df.to_csv(f"{out_dir}/results_fold_level.csv", index=False)

    print("\n--- Step 5: 결과 집계 ---")
    summary = summarize(fold_df)
    summary.to_csv(f"{out_dir}/results_summary.csv", index=False)
    print(summary.to_string(index=False))

    print("\n--- Step 6: 성공/실패 판정 (plan.md 8절) ---")
    clean_row = summary[(summary["regime"] == "Clean (physics-only)")]
    clean_ok = clean_row["pr_auc_mean_3seed"].between(*ACCEPTABLE_PRAUC_RANGE).all()
    print(f"[보정 사전조건] Clean PR-AUC가 허용범위 {ACCEPTABLE_PRAUC_RANGE} 안에 있는가: {clean_ok}")
    print(clean_row.to_string(index=False))

    primary_success = {}
    for model_name in ["Logistic Regression", "Random Forest"]:
        clean_v = summary[(summary["regime"] == "Clean (physics-only)") & (summary["model"] == model_name)]["pr_auc_mean_3seed"].iloc[0]
        leaked_v = summary[(summary["regime"] == "Leaked (leakage-inclusive)") & (summary["model"] == model_name)]["pr_auc_mean_3seed"].iloc[0]
        delta = leaked_v - clean_v
        primary_success[model_name] = delta
        print(f"[1차 성공기준] {model_name}: PR-AUC(Leaked)-PR-AUC(Clean) = {delta:.4f} "
              f"(>= +0.15 이면 성공, RF 기준 필수)")

    secondary = {}
    for model_name in ["Logistic Regression", "Random Forest"]:
        c = summary[(summary["regime"] == "Clean (physics-only)") & (summary["model"] == model_name)]["pr_auc_mean_3seed"].iloc[0]
        s = summary[(summary["regime"] == "Suspect-added") & (summary["model"] == model_name)]["pr_auc_mean_3seed"].iloc[0]
        l = summary[(summary["regime"] == "Leaked (leakage-inclusive)") & (summary["model"] == model_name)]["pr_auc_mean_3seed"].iloc[0]
        ordered = c < s < l
        gap = l - s
        meets_gap = gap >= MIN_DELTA_LEAKED_SUSPECT
        secondary[model_name] = (c, s, l, ordered, gap, meets_gap)
        verdict_2nd = "실질 성공 (a)+(b) 모두 충족" if (ordered and meets_gap) else (
            "형식적 통과, 실질적 미달 (b) 미충족" if ordered else "순서(a) 자체가 성립하지 않음")
        print(f"[2차 성공기준] {model_name}: Clean({c:.4f}) < Suspect({s:.4f}) < Leaked({l:.4f}) -> "
              f"순서(a)={ordered}, Δ(Leaked-Suspect)={gap:+.4f} (>=0.04 기준 (b)={meets_gap}) => {verdict_2nd}")

    rf_delta = primary_success["Random Forest"]
    lr_delta = primary_success["Logistic Regression"]
    if rf_delta >= 0.15:
        verdict = "1차 성공기준 충족 (RF 기준 재현 성공)"
        if lr_delta >= 0.15:
            verdict += " + 모델 전반 일관성도 재현됨 (LR도 충족)"
    elif rf_delta < 0.05 and lr_delta < 0.05:
        verdict = "재현 실패 (두 모델 모두 Δ<0.05) — 재설계 필요"
    else:
        verdict = "부분 재현 (성공기준 미충족, 실패기준도 미충족 — 회색지대)"
    print(f"\n최종 판정 (1차): {verdict}")

    any_secondary_real_success = any(ordered and meets_gap for (_, _, _, ordered, _, meets_gap) in secondary.values())
    print(f"최종 판정 (2차, 실질 기준): {'적어도 한 모델에서 실질 성공' if any_secondary_real_success else '실질 성공 모델 없음'}")

    print("\n완료. 산출물:")
    print(f"  - {out_dir}/calibration_log_gamma1.csv")
    print(f"  - {out_dir}/calibration_log_koi_score.csv")
    print(f"  - {out_dir}/synthetic_dataset_v1.csv")
    print(f"  - {out_dir}/results_fold_level.csv")
    print(f"  - {out_dir}/results_summary.csv")


if __name__ == "__main__":
    main()
