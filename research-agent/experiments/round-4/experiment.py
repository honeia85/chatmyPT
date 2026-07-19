"""
Round 4 실험: 독립 데이터 실현 재검증 (calibration-evaluation circularity 해소)
근거 문서: experiments/round-4/plan.md (반드시 함께 읽을 것)

⚠️ 이 스크립트는 실제 KOI cumulative table을 사용하지 않는다. 외부 네트워크 다운로드 없이
전부 인메모리로 합성 데이터를 생성한다 (plan.md 2절 "Data Source (pinned)").

Round 3 리뷰(experiments/round-3/review.md, VERDICT: REVISE)의 핵심 지적: koi_score/gamma1
파라미터 탐색과 최종 confirmatory 평가가 동일한 DATA_SEED=42 기반 단일 데이터 실현을
공유하는 "검증 설계 순환성"이 있었다. 이번 라운드는 그리드 탐색 자체를 하지 않는다 —
Round 3에서 이미 확정된 GAMMA1_STAR/GAMMA0_STAR/ALPHA_STAR/SIGMA_STAR를 상수로 고정하고
(select_gamma1/select_koi_score_params 같은 탐색 함수는 이 스크립트에 아예 없음),
DATA_SEED=42와는 완전히 무관한 새로운 DATA_SEED in {43, 44, 45}로 3개의 독립적인 데이터
실현을 만들어 동일한 3-seed x 5-fold 평가를 반복한다 (plan.md 0/1/2절).

실행: runner/.venv/bin/python experiments/round-4/experiment.py
출력:
  - experiments/round-4/synthetic_dataset_seed43.csv / seed44.csv / seed45.csv
  - experiments/round-4/results_fold_level.csv       (data_seed 컬럼 포함, 3x90=270행)
  - experiments/round-4/results_summary.csv          (data_seed 컬럼 포함, 3x6=18행)
  - experiments/round-4/results_comparison_with_seed42.csv (Round 3 data_seed=42 값 포함 비교표)
  - stdout (실행 시 리다이렉트하여 experiment_run.log로 보관)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# 0. 고정 파라미터 (plan.md 2절 — Round 3에서 확정된 값을 그대로 하드코딩, 재탐색 없음)
# ---------------------------------------------------------------------------
GAMMA1_STAR = 3.4
GAMMA0_STAR = -0.9697265625   # experiments/round-3/calibration_log_gamma1.csv 5행
ALPHA_STAR = 0.85             # flag 가중치 1-alpha = 0.15
SIGMA_STAR = 0.25             # experiments/round-3/calibration_log_koi_score.csv 3행

DATA_SEEDS = [43, 44, 45]     # Round 3의 DATA_SEED=42와 완전히 무관한 독립 실현 (plan.md 2절)
N_SYSTEMS = 6000
CANDIDATE_COUNT_PROBS = {1: 0.50, 2: 0.35, 3: 0.15}
FLAG_FLIP_PROB = 0.03

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

CV_SEEDS = [0, 1, 2]          # 최종 보고 seed — Round 2/3와 동일 (plan.md 6절)
N_SPLITS = 5
N_ESTIMATORS = 300

TARGET_PRAUC_RANGE = (0.70, 0.74)
ACCEPTABLE_PRAUC_RANGE = (0.65, 0.78)
SUSPECT_TARGET_RANGE = (0.80, 0.90)
SUSPECT_ACCEPTABLE_RANGE = (0.75, 0.95)   # plan.md 8.2절 "부분 성공" 판정용 완화 범위
MIN_DELTA_LEAKED_SUSPECT = 0.04
MIN_PRIMARY_DELTA = 0.15

REGIMES = {
    "Clean (physics-only)": PHYSICS_COLS,
    "Suspect-added": PHYSICS_COLS + [SCORE_COL],
    "Leaked (leakage-inclusive)": PHYSICS_COLS + FLAG_COLS + [SCORE_COL],
}

# 참고용: Round 3(DATA_SEED=42)의 확정 결과 (experiments/round-3/results_summary.csv 그대로 인용)
ROUND3_SEED42_RESULTS = {
    ("Logistic Regression", "Clean (physics-only)"): 0.731840,
    ("Logistic Regression", "Suspect-added"): 0.869604,
    ("Logistic Regression", "Leaked (leakage-inclusive)"): 0.999963,
    ("Random Forest", "Clean (physics-only)"): 0.723134,
    ("Random Forest", "Suspect-added"): 0.856524,
    ("Random Forest", "Leaked (leakage-inclusive)"): 0.999978,
}


# ---------------------------------------------------------------------------
# 1. 합성 데이터 생성 (plan.md 3절) — Round 3 experiment.py의 build_dataset을 그대로 복사,
#    수정 없음. gamma1/gamma0/alpha/sigma는 이제 항상 고정 상수로만 전달된다.
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
    return df


# ---------------------------------------------------------------------------
# 2. 최종 평가: 3개 레짐 x 2개 모델 x 3 seed x 5 fold, 각 DATA_SEED마다 반복 (plan.md 6절)
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


def run_full_evaluation(df, data_seed):
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
                        "data_seed": data_seed, "regime": regime_name, "model": model_name,
                        "seed": seed, "fold": fold_i, "pr_auc": pr_auc,
                    })
                    print(f"[eval] data_seed={data_seed} regime={regime_name!r} model={model_name} "
                          f"seed={seed} fold={fold_i} PR-AUC={pr_auc:.4f}")

    return pd.DataFrame(fold_records)


def summarize(fold_df):
    seed_level = fold_df.groupby(["data_seed", "regime", "model", "seed"])["pr_auc"].mean().reset_index()
    summary = seed_level.groupby(["data_seed", "regime", "model"])["pr_auc"].agg(["mean", "std"]).reset_index()
    summary.columns = ["data_seed", "regime", "model", "pr_auc_mean_3seed", "pr_auc_std_3seed"]

    out_rows = []
    for data_seed in summary["data_seed"].unique():
        sub = summary[summary["data_seed"] == data_seed]
        clean_lookup = sub[sub["regime"] == "Clean (physics-only)"].set_index("model")["pr_auc_mean_3seed"]
        suspect_lookup = sub[sub["regime"] == "Suspect-added"].set_index("model")["pr_auc_mean_3seed"]
        for _, row in sub.iterrows():
            r = row.to_dict()
            r["delta_vs_clean"] = np.nan if row["regime"] == "Clean (physics-only)" else row["pr_auc_mean_3seed"] - clean_lookup[row["model"]]
            r["delta_leaked_vs_suspect"] = row["pr_auc_mean_3seed"] - suspect_lookup[row["model"]] if row["regime"] == "Leaked (leakage-inclusive)" else np.nan
            out_rows.append(r)
    return pd.DataFrame(out_rows)


# ---------------------------------------------------------------------------
# 3. 개별 DATA_SEED 판정 (plan.md 8.1절) + 3개 실현 전체 "안정적 성질" 판정 (plan.md 8.2절)
# ---------------------------------------------------------------------------
def judge_single_data_seed(summary_for_seed):
    def val(regime, model):
        row = summary_for_seed[(summary_for_seed["regime"] == regime) & (summary_for_seed["model"] == model)]
        return float(row["pr_auc_mean_3seed"].iloc[0])

    result = {}
    for model_name in ["Logistic Regression", "Random Forest"]:
        clean = val("Clean (physics-only)", model_name)
        suspect = val("Suspect-added", model_name)
        leaked = val("Leaked (leakage-inclusive)", model_name)
        primary_delta = leaked - clean
        secondary_gap = leaked - suspect
        ordered = clean < suspect < leaked
        result[model_name] = {
            "clean": clean, "suspect": suspect, "leaked": leaked,
            "clean_in_acceptable": ACCEPTABLE_PRAUC_RANGE[0] <= clean <= ACCEPTABLE_PRAUC_RANGE[1],
            "clean_in_target": TARGET_PRAUC_RANGE[0] <= clean <= TARGET_PRAUC_RANGE[1],
            "suspect_in_target": SUSPECT_TARGET_RANGE[0] <= suspect <= SUSPECT_TARGET_RANGE[1],
            "suspect_in_acceptable": SUSPECT_ACCEPTABLE_RANGE[0] <= suspect <= SUSPECT_ACCEPTABLE_RANGE[1],
            "primary_delta": primary_delta,
            "primary_success": primary_delta >= MIN_PRIMARY_DELTA,
            "ordered": ordered,
            "secondary_gap": secondary_gap,
            "secondary_success": ordered and secondary_gap >= MIN_DELTA_LEAKED_SUSPECT,
        }
    return result


def main():
    out_dir = "experiments/round-4"

    print("=" * 70)
    print("Round 4 실험: 독립 데이터 실현 재검증 (calibration-evaluation circularity 해소)")
    print(f"고정 파라미터 (재탐색 없음): GAMMA1_STAR={GAMMA1_STAR}, GAMMA0_STAR={GAMMA0_STAR}, "
          f"ALPHA_STAR={ALPHA_STAR}, SIGMA_STAR={SIGMA_STAR}")
    print(f"독립 DATA_SEEDS={DATA_SEEDS} (Round 3의 DATA_SEED=42와 완전히 무관)")
    print("=" * 70)

    all_fold_dfs = []
    per_seed_judgements = {}

    for data_seed in DATA_SEEDS:
        print(f"\n--- DATA_SEED={data_seed}: 데이터셋 생성 (round-4-synth-seed{data_seed}) ---")
        rng = np.random.default_rng(data_seed)
        df = build_dataset(rng, GAMMA1_STAR, GAMMA0_STAR, ALPHA_STAR, SIGMA_STAR)
        n_rows = len(df)
        n_systems_realized = df["kepid_sim"].nunique()
        pos_rate = df["y"].mean()
        print(f"총 행 수: {n_rows} (시스템 수: {n_systems_realized}, 기대 시스템 수: {N_SYSTEMS})")
        print(f"양성 비율(y=1): {pos_rate:.4f} (목표 0.40)")
        df.to_csv(f"{out_dir}/synthetic_dataset_seed{data_seed}.csv", index=False)

        print(f"--- DATA_SEED={data_seed}: 3개 레짐 x 2개 모델 x 3 seed x 5 fold 평가 ---")
        fold_df = run_full_evaluation(df, data_seed)
        all_fold_dfs.append(fold_df)

    fold_df_all = pd.concat(all_fold_dfs, ignore_index=True)
    fold_df_all.to_csv(f"{out_dir}/results_fold_level.csv", index=False)

    print("\n--- 결과 집계 (data_seed별) ---")
    summary_all = summarize(fold_df_all)
    summary_all.to_csv(f"{out_dir}/results_summary.csv", index=False)
    print(summary_all.to_string(index=False))

    print("\n--- 개별 DATA_SEED 판정 (plan.md 8.1절) ---")
    for data_seed in DATA_SEEDS:
        sub = summary_all[summary_all["data_seed"] == data_seed]
        judgement = judge_single_data_seed(sub)
        per_seed_judgements[data_seed] = judgement
        for model_name, j in judgement.items():
            print(f"[DATA_SEED={data_seed}] {model_name}: Clean={j['clean']:.4f}(target_in={j['clean_in_target']}, "
                  f"acceptable_in={j['clean_in_acceptable']}) Suspect={j['suspect']:.4f}(target_in={j['suspect_in_target']}, "
                  f"acceptable_in={j['suspect_in_acceptable']}) Leaked={j['leaked']:.4f} "
                  f"primary_delta={j['primary_delta']:+.4f}(success={j['primary_success']}) "
                  f"ordered={j['ordered']} secondary_gap={j['secondary_gap']:+.4f}(success={j['secondary_success']})")

    print("\n--- DATA_SEED=42(Round 3) 대비 비교표 (plan.md 7절) ---")
    comparison_rows = []
    for model_name in ["Logistic Regression", "Random Forest"]:
        for regime_name in REGIMES.keys():
            seed42_val = ROUND3_SEED42_RESULTS[(model_name, regime_name)]
            new_vals = []
            for data_seed in DATA_SEEDS:
                row = summary_all[(summary_all["data_seed"] == data_seed) &
                                   (summary_all["model"] == model_name) &
                                   (summary_all["regime"] == regime_name)]
                new_vals.append(float(row["pr_auc_mean_3seed"].iloc[0]))
            comparison_rows.append({
                "model": model_name, "regime": regime_name,
                "data_seed_42_round3": seed42_val,
                "data_seed_43": new_vals[0], "data_seed_44": new_vals[1], "data_seed_45": new_vals[2],
                "new_seeds_min": min(new_vals), "new_seeds_max": max(new_vals),
                "seed42_within_new_range": min(new_vals) <= seed42_val <= max(new_vals),
            })
            print(f"{model_name} / {regime_name}: seed42(Round3)={seed42_val:.4f} vs "
                  f"seed43={new_vals[0]:.4f} seed44={new_vals[1]:.4f} seed45={new_vals[2]:.4f} "
                  f"(new range=[{min(new_vals):.4f},{max(new_vals):.4f}], "
                  f"seed42_within_range={min(new_vals) <= seed42_val <= max(new_vals)})")
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(f"{out_dir}/results_comparison_with_seed42.csv", index=False)

    print("\n--- 3개 실현 전체에 걸친 '안정적 성질' 최종 판정 (plan.md 8.2절) ---")
    n_seeds = len(DATA_SEEDS)
    fully_pass_count = 0
    per_seed_pass_detail = {}
    for data_seed in DATA_SEEDS:
        j = per_seed_judgements[data_seed]
        clean_ok = all(j[m]["clean_in_acceptable"] for m in j)
        suspect_target_ok = all(j[m]["suspect_in_target"] for m in j)
        primary_ok = all(j[m]["primary_success"] for m in j)   # RF와 LR 모두
        secondary_ok_any = any(j[m]["secondary_success"] for m in j)  # 적어도 한 모델
        seed_pass = clean_ok and primary_ok and secondary_ok_any and suspect_target_ok
        per_seed_pass_detail[data_seed] = {
            "clean_ok": clean_ok, "suspect_target_ok": suspect_target_ok,
            "primary_ok": primary_ok, "secondary_ok_any": secondary_ok_any, "seed_pass": seed_pass,
        }
        if seed_pass:
            fully_pass_count += 1
        print(f"[DATA_SEED={data_seed}] clean_ok={clean_ok} suspect_target_ok={suspect_target_ok} "
              f"primary_ok(RF+LR)={primary_ok} secondary_ok(>=1 model)={secondary_ok_any} => seed_pass={seed_pass}")

    if fully_pass_count == n_seeds:
        final_verdict = "강한 성공 (파라미터가 안정적 성질) — 3개 실현 모두 전 기준 충족"
    elif fully_pass_count == n_seeds - 1:
        final_verdict = "부분 성공 (대체로 안정적이나 경계 사례 존재) — 3개 중 2개만 전 기준 충족"
    else:
        final_verdict = f"실패 (우연한 단일 실현 의존 가능성) — 3개 중 {fully_pass_count}개만 전 기준 충족"
    print(f"\n[최종 판정 8.2] {final_verdict}")

    print("\n완료. 산출물:")
    print(f"  - {out_dir}/synthetic_dataset_seed43.csv / seed44.csv / seed45.csv")
    print(f"  - {out_dir}/results_fold_level.csv")
    print(f"  - {out_dir}/results_summary.csv")
    print(f"  - {out_dir}/results_comparison_with_seed42.csv")


if __name__ == "__main__":
    main()
