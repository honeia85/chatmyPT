#!/usr/bin/env python3
"""연구 Loop: 읽기 → 실행 → 평가 → 수정의 반복 (Ch.6 Phase 2).

한 사이클:
  1. 읽기+실행: run_agent.run_round()로 라운드를 수행하고 round_summary.md 생성
  2. 평가: writing-reviewer 서브에이전트가 요약을 검토하고 review.md 작성
     (첫 줄 "VERDICT: APPROVE" 또는 "VERDICT: REVISE")
  3. 수정: REVISE면 리뷰 지시를 다음 라운드의 지시로 삼아 반복

종료 조건: APPROVE 또는 max_rounds 도달.

사용:
    python loop.py "leakage-controlled 베이스라인을 확립해줘" --max-rounds 3
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from claude_agent_sdk import query

from run_agent import WORKSPACE, RoundContext, agent_options, run_round


async def evaluate_round(ctx: RoundContext) -> tuple[bool, str]:
    """writing-reviewer 서브에이전트로 라운드 요약을 평가한다."""
    review_path = ctx.directory / "review.md"
    rel_summary = ctx.summary_path.relative_to(WORKSPACE)
    rel_review = review_path.relative_to(WORKSPACE)

    prompt = (
        f"writing-reviewer 서브에이전트를 사용해 {rel_summary} 를 검토하고, "
        f"결과를 {rel_review} 에 저장하게 하라. 검토 외 다른 작업은 하지 마라."
    )
    async for _ in query(prompt=prompt, options=agent_options()):
        pass

    if not review_path.exists():
        return False, "리뷰 파일이 생성되지 않음 — 같은 지시로 재시도 필요"

    review = review_path.read_text(encoding="utf-8")
    approved = review.splitlines()[0].strip().upper().endswith("APPROVE")
    return approved, review


async def research_loop(goal: str, max_rounds: int = 3) -> None:
    instruction = goal
    for cycle in range(1, max_rounds + 1):
        print(f"\n########## Loop cycle {cycle}/{max_rounds} ##########")

        # 읽기 + 실행
        ctx = await run_round(instruction, on_event=_print_event)
        if not ctx.summary_path.exists():
            print("round_summary.md가 없어 평가를 건너뛰고 재시도합니다.")
            instruction = f"{goal}\n(직전 라운드에서 round_summary.md 작성이 누락됐다. 이번엔 반드시 작성하라.)"
            continue

        # 평가
        approved, review = await evaluate_round(ctx)
        print(f"\n--- Review (round {ctx.number}) ---\n{review[:2000]}")

        if approved:
            print(f"\n✅ APPROVE — {ctx.number} 라운드에서 Loop 종료")
            return

        # 수정: 리뷰 지시를 다음 라운드 입력으로
        instruction = (
            f"{goal}\n\n"
            f"직전 라운드(round-{ctx.number})는 리뷰에서 REVISE 판정을 받았다. "
            f"다음 리뷰 지시를 반영해 개선하라:\n<review>\n{review}\n</review>"
        )

    print(f"\n⚠️ {max_rounds} 라운드 안에 APPROVE에 도달하지 못했습니다. 마지막 리뷰를 확인하세요.")


def _print_event(event: dict) -> None:
    if event["type"] == "text":
        print(event["text"])
    elif event["type"] == "tool_use":
        print(f"  ⚙ {event['name']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goal", help="이 Loop가 달성할 연구 목표")
    parser.add_argument("--max-rounds", type=int, default=3)
    args = parser.parse_args()
    asyncio.run(research_loop(args.goal, args.max_rounds))


if __name__ == "__main__":
    main()
