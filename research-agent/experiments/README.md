# experiments/

실험 라운드 단위로 관리한다.

```
experiments/
  round-1/
    plan.md            # experiment-planner가 작성 (데이터 소스 고정, 피처 누수 등급표, 검증 설계)
    run.log            # runner가 저장하는 실행 로그
    round_summary.md   # experiment-log 스킬이 생성 (Objective/Experiments/Results/Next)
    review.md          # writing-reviewer가 생성 (VERDICT: APPROVE|REVISE)
  round-2/
    ...
```

라운드 번호는 `runner/run_agent.py`가 자동으로 증가시킨다.
