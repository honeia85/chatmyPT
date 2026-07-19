# [샘플 논문] Tabular Machine Learning for Kepler KOI Candidate Vetting

> ⚠️ 이것은 파이프라인 테스트용 **가상 논문**입니다 (강의 예시 도메인을 본뜬 합성 텍스트).
> 실제 문헌 인용에 사용하지 마세요.

**Authors:** J. Doe, A. Researcher (2024)

## Abstract

We present a reproducible baseline study for classifying Kepler Objects of Interest (KOI)
into planetary candidates versus false positives using only the KOI cumulative table.
We show that commonly used disposition flag features (koi_fpflag_*) leak the label,
inflating PR-AUC from 0.72 to 0.97, and propose a leakage-controlled evaluation protocol.

## 1. Introduction

Exoplanet candidate vetting has been approached with deep learning on light curves and
with tabular ML on catalog features. Tabular approaches are attractive for reproducibility
but frequently reuse features derived from the vetting pipeline itself.

## 2. Method

We train logistic regression, decision tree, and random forest models under two feature
regimes: physics-only (stellar and orbital observables) and leakage-inclusive
(adding koi_fpflag_* and koi_score). Validation uses 5-fold grouped cross-validation,
grouped by target star (kepid) to prevent transit-sibling leakage, repeated over 5 seeds.

## 3. Data

KOI cumulative table (2024-01 snapshot), 9,564 rows. Labels: CONFIRMED+CANDIDATE vs
FALSE POSITIVE. Identifier columns excluded.

## 4. Results

| Model | physics-only PR-AUC | leakage-inclusive PR-AUC |
|-------|--------------------:|-------------------------:|
| Logistic Regression | 0.723 | 0.965 |
| Decision Tree | 0.701 | 0.958 |
| Random Forest | 0.741 | 0.971 |

Permutation importance under the leakage-inclusive regime attributes >75% of predictive
power to the four koi_fpflag_* columns.

## 5. Limitations

Single catalog snapshot; no comparison against light-curve deep learning baselines;
hyperparameters were not extensively tuned.
