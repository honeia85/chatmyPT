"""
Round 2 실험: KOI 누수 패턴의 합성 데이터 미니 재현
근거 문서: experiments/round-2/plan.md (반드시 함께 읽을 것)

⚠️ 이 스크립트는 실제 KOI cumulative table을 사용하지 않는다. 외부 네트워크 다운로드 없이
전부 인메모리로 합성 데이터를 생성한다 (plan.md 2절 "Data Source (pinned)").
데이터 버전: round-2-synth-v1 (파라미터를 바꾸면 v2로 승격하고 이 주석과 round_summary.md에 기록할 것).

실행: runner/.venv/bin/python experiments/round-2/experiment.py
출력:
  - experiments/round-2/results_fold_level.csv   (레짐×모델×seed×fold 원자료)
  - experiments/round-2/results_summary.csv      (레짐×모델별 3-seed 평균±표준편차)
  - experiments/round-2/calibration_log.csv      (gamma1 후보별 보정 시행 기록)
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
# 0. 고정 파라미터 (plan.md 3절, round-2-synth-v1)
# ---------------------------------------------------------------------------
DATA_SEED = 42
N_SYSTEMS = 6000
CANDIDATE_COUNT_PROBS = {1: 0.50, 2: 0.35, 3: 0.15}
TARGET_POSITIVE_RATE = 0.40   # 양성(CONFIRMED/CANDIDATE) : 음성(FALSE POSITIVE) = 40:60
FLAG_FLIP_PROB = 0.03         # koi_fpflag_* 노이즈율 (plan.md 3.5절)
SCORE_NOISE_STD = 0.05        # koi_score 노이즈 표준편차 (plan.md 3.6절)

# 물리 피처 loading과 단조 변환 (plan.md 3.3절 표)
PHYSICS_FEATURES = {
    # name: (loading b_k, transform(x_std) -> value)
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

CV_SEEDS = [0, 1, 2]
N_SPLITS = 5
GAMMA1_GRID = [0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
TARGET_PRAUC_CENTER = 0.72
TARGET_PRAUC_RANGE = (0.70, 0.74)
ACCEPTABLE_PRAUC_RANGE = (0.65, 0.78)

REGIMES = {
    "Clean (physics-only)": PHYSICS_COLS,
    "Suspect-added": PHYSICS_COLS + [SCORE_COL],
    "Leaked (leakage-inclusive)": PHYSICS_COLS + FLAG_COLS + [SCORE_COL],
}


# ---------------------------------------------------------------------------
# 1. gamma0 보정 (수치적분, plan.md 3.4절) — s_std ~ N(0,1) 이론값이므로 샘플링 대신
#    정규분포 확률밀도로 가중한 유한 그리드 적분 + 이분탐색을 사용한다 (더 정확·결정적).
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
# ---------------------------------------------------------------------------
def build_dataset(rng, gamma1, gamma0):
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
    noise = rng.normal(0, SCORE_NOISE_STD, size=n_rows)
    raw = 0.5 * (1.0 / (1.0 + np.exp(-2.0 * s_std))) + 0.5 * np.mean(1 - flag_mat, axis=1) + noise
    data[SCORE_COL] = np.clip(raw, 0, 1)

    df = pd.DataFrame(data)
    return df, s_std


# ---------------------------------------------------------------------------
# 3. gamma1 보정 — physics-only 레짐, RandomForest, seed=0, 5-fold 빠른 평가로
#    PR-AUC가 0.70~0.74 (허용 0.65~0.78) 범위에 들어오는 gamma1을 그리드에서 선택한다.
#    (plan.md 3.4절 "1~3회 시험 실행" 절차를 그리드 서치로 재현 가능하게 자동화)
# ---------------------------------------------------------------------------
def quick_physics_only_prauc(gamma1, gamma0):
    rng = np.random.default_rng(DATA_SEED)  # 매 시행마다 동일 시드로 재생성 -> 구조/피처 동일, 라벨만 gamma1/gamma0에 따라 변화
    df, _ = build_dataset(rng, gamma1, gamma0)
    X = df[PHYSICS_COLS].values
    y = df["y"].values
    groups = df["kepid_sim"].values

    cv = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=0)
    scores = []
    for train_idx, test_idx in cv.split(X, y, groups):
        model = RandomForestClassifier(n_estimators=200, random_state=0, n_jobs=-1)
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
            "in_target_range_0.70_0.74": in_target, "dist_to_center_0.72": dist,
        })
        print(f"[calibration] gamma1={gamma1:.2f} gamma0={gamma0:.4f} "
              f"quick physics-only PR-AUC={prauc:.4f} in_target={in_target}")
        if best is None or dist < best["dist_to_center_0.72"]:
            best = log_rows[-1]

    log_df = pd.DataFrame(log_rows)
    return best["gamma1"], best["gamma0"], log_df


# ---------------------------------------------------------------------------
# 4. 최종 평가: 3개 레짐 x 2개 모델 x 3 seed x 5 fold (plan.md 6절)
# ---------------------------------------------------------------------------
def build_model(model_name, seed):
    if model_name == "Logistic Regression":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=seed)),
        ])
    elif model_name == "Random Forest":
        return RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=-1)
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
    # seed-level: 각 seed 내 5-fold 평균
    seed_level = fold_df.groupby(["regime", "model", "seed"])["pr_auc"].mean().reset_index()
    # regime x model: 3-seed 평균 ± 표준편차
    summary = seed_level.groupby(["regime", "model"])["pr_auc"].agg(["mean", "std"]).reset_index()
    summary.columns = ["regime", "model", "pr_auc_mean_3seed", "pr_auc_std_3seed"]

    clean_lookup = summary[summary["regime"] == "Clean (physics-only)"].set_index("model")["pr_auc_mean_3seed"]
    summary["delta_vs_clean"] = summary.apply(
        lambda row: np.nan if row["regime"] == "Clean (physics-only)"
        else row["pr_auc_mean_3seed"] - clean_lookup[row["model"]],
        axis=1,
    )
    return summary


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    out_dir = "experiments/round-2"

    print("=" * 70)
    print("Round 2 실험: 합성 KOI 데이터로 label-leakage 패턴 미니 재현")
    print("데이터 버전: round-2-synth-v1 (plan.md 참고)")
    print("=" * 70)

    print("\n--- Step 1: gamma1/gamma0 보정 (physics-only PR-AUC 0.70~0.74 목표) ---")
    gamma1_star, gamma0_star, calib_log = select_gamma1()
    calib_log.to_csv(f"{out_dir}/calibration_log.csv", index=False)
    print(f"\n선택된 파라미터: gamma1={gamma1_star:.3f}, gamma0={gamma0_star:.4f}")

    print("\n--- Step 2: 최종 데이터셋 생성 (round-2-synth-v1) ---")
    rng_final = np.random.default_rng(DATA_SEED)
    df, s_std = build_dataset(rng_final, gamma1_star, gamma0_star)
    n_rows = len(df)
    n_systems_realized = df["kepid_sim"].nunique()
    pos_rate = df["y"].mean()
    print(f"총 행 수: {n_rows} (시스템 수: {n_systems_realized}, 기대 시스템 수: {N_SYSTEMS})")
    print(f"양성 비율(y=1): {pos_rate:.4f} (목표 {TARGET_POSITIVE_RATE})")
    df.to_csv(f"{out_dir}/synthetic_dataset_v1.csv", index=False)

    print("\n--- Step 3: 3개 레짐 x 2개 모델 x 3 seed x 5 fold 평가 ---")
    fold_df = run_full_evaluation(df)
    fold_df.to_csv(f"{out_dir}/results_fold_level.csv", index=False)

    print("\n--- Step 4: 결과 집계 ---")
    summary = summarize(fold_df)
    summary.to_csv(f"{out_dir}/results_summary.csv", index=False)
    print(summary.to_string(index=False))

    print("\n--- Step 5: 성공/실패 판정 (plan.md 8절) ---")
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

    secondary_orderings = {}
    for model_name in ["Logistic Regression", "Random Forest"]:
        c = summary[(summary["regime"] == "Clean (physics-only)") & (summary["model"] == model_name)]["pr_auc_mean_3seed"].iloc[0]
        s = summary[(summary["regime"] == "Suspect-added") & (summary["model"] == model_name)]["pr_auc_mean_3seed"].iloc[0]
        l = summary[(summary["regime"] == "Leaked (leakage-inclusive)") & (summary["model"] == model_name)]["pr_auc_mean_3seed"].iloc[0]
        ordered = c < s < l
        secondary_orderings[model_name] = (c, s, l, ordered)
        print(f"[2차 성공기준] {model_name}: Clean({c:.4f}) < Suspect({s:.4f}) < Leaked({l:.4f}) -> {ordered}")

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
    print(f"\n최종 판정: {verdict}")

    print("\n완료. 산출물:")
    print(f"  - {out_dir}/calibration_log.csv")
    print(f"  - {out_dir}/synthetic_dataset_v1.csv")
    print(f"  - {out_dir}/results_fold_level.csv")
    print(f"  - {out_dir}/results_summary.csv")


if __name__ == "__main__":
    main()
