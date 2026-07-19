---
name: experiment-log
description: 실험 로그/결과 정리 스킬. 실험 실행 로그와 결과 파일을 읽어 결과 표, 실패 원인 분석, 다음 실험 제안이 담긴 round_summary.md를 생성한다. "실험 결과 정리해줘", "라운드 요약 만들어줘" 요청 시 사용.
---

# 실험 로그 정리 Skill

## 입력

- 실험 라운드 디렉토리 (`experiments/round-<n>/`) — 로그, 결과 CSV/JSON, 계획서(plan.md)

## 출력

- `experiments/round-<n>/round_summary.md`

## 절차

1. 해당 라운드의 `plan.md`(있으면)와 실행 로그·결과 파일을 모두 읽는다.
2. 다음 4개 섹션으로 `round_summary.md`를 작성한다:

   ```markdown
   # Round <n> Summary — <라운드 한 줄 제목>

   ## Objective
   (이 라운드가 확인하려던 가설. plan.md에서 가져온다)

   ## Experiments
   (실제 실행된 설정: 모델, 피처 레짐(Clean/Suspect/Leaked), 검증 설계(fold×seed), 데이터 버전)

   ## Results
   (지표별 결과 표. 레짐 간 델타(Δ)를 함께 표기. 실패한 실행은 실패 원인과 함께 기록)

   ## Next
   (결과가 시사하는 다음 실험 제안 1~3개, 우선순위 순)
   ```

3. 이전 라운드 요약(`round-<n-1>/round_summary.md`)이 있으면 결과를 비교해
   Results 섹션에 변화 방향을 한 줄로 명시한다.
4. 새로 확인된 사실이 위키의 기존 서술과 충돌하면 해당 위키 페이지를 갱신하고
   Summary에 갱신한 페이지 경로를 적는다.

## 품질 기준 체크리스트

- [ ] 결과 표의 모든 수치에 검증 설계(fold/seed)가 병기되어 있다
- [ ] 계획에 있었으나 실행되지 않은 항목이 누락 없이 기록되어 있다
- [ ] 실패한 실행이 성공한 것처럼 보이지 않는다
- [ ] Next 제안이 Results의 구체적 수치를 근거로 한다
