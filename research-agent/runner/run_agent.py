#!/usr/bin/env python3
"""Python에서 연구 에이전트 실행하기 (Ch.7 Phase 1-2).

Claude Agent SDK로 워크스페이스의 연구 에이전트를 프로그램처럼 실행한다.
- 워크스페이스의 CLAUDE.md / subagents / skills / hooks가 그대로 적용된다
  (setting_sources=["project"], cwd=워크스페이스 루트).
- 실행마다 experiments/round-<n>/ 를 만들고 run.log에 전 과정을 남긴다.
- 라운드 종료 시 round_summary.md 생성을 프롬프트로 요구한다.

사용:
    pip install -r requirements.txt
    python run_agent.py "physics-only 레짐으로 베이스라인 3종을 돌리고 라운드를 요약해줘"
"""
from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Callable

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    query,
)

WORKSPACE = Path(__file__).resolve().parent.parent
EXPERIMENTS = WORKSPACE / "experiments"


@dataclass
class RoundContext:
    """연구 컨텍스트: 현재 라운드 번호와 산출물 경로."""

    number: int
    directory: Path
    previous_summary: str | None = None
    events: list[dict] = field(default_factory=list)

    @property
    def summary_path(self) -> Path:
        return self.directory / "round_summary.md"

    @property
    def log_path(self) -> Path:
        return self.directory / "run.log"


def next_round() -> RoundContext:
    """다음 라운드 디렉토리를 만들고, 이전 라운드 요약을 컨텍스트로 로드한다."""
    EXPERIMENTS.mkdir(exist_ok=True)
    existing = sorted(
        (int(p.name.split("-")[1]) for p in EXPERIMENTS.glob("round-*") if p.is_dir()),
        reverse=True,
    )
    number = (existing[0] + 1) if existing else 1
    directory = EXPERIMENTS / f"round-{number}"
    directory.mkdir()

    previous_summary = None
    if existing:
        prev = EXPERIMENTS / f"round-{existing[0]}" / "round_summary.md"
        if prev.exists():
            previous_summary = prev.read_text(encoding="utf-8")

    return RoundContext(number=number, directory=directory, previous_summary=previous_summary)


def build_prompt(ctx: RoundContext, instruction: str) -> str:
    """연구 컨텍스트(라운드 번호, 이전 요약)를 프롬프트로 전달한다."""
    parts = [
        f"[연구 라운드 {ctx.number}]",
        f"이 라운드의 작업 디렉토리는 experiments/round-{ctx.number}/ 다.",
    ]
    if ctx.previous_summary:
        parts.append(
            "이전 라운드 요약은 다음과 같다. 이것을 출발점으로 삼아라:\n"
            f"<previous_round_summary>\n{ctx.previous_summary}\n</previous_round_summary>"
        )
    parts.append(f"이번 라운드 지시: {instruction}")
    parts.append(
        "작업을 마치면 반드시 experiment-log 스킬의 형식대로 "
        f"experiments/round-{ctx.number}/round_summary.md 를 작성하라."
    )
    return "\n\n".join(parts)


def agent_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(WORKSPACE),
        setting_sources=["project"],  # CLAUDE.md, .claude/{agents,skills,settings.json} 로드
        permission_mode="acceptEdits",
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebSearch", "WebFetch", "Task"],
    )


async def run_round(
    instruction: str,
    on_event: Callable[[dict], None] | None = None,
) -> RoundContext:
    """한 라운드를 실행한다. on_event 콜백으로 실행 과정을 스트리밍한다 (UI 연결 지점)."""
    ctx = next_round()

    def emit(event: dict) -> None:
        ctx.events.append(event)
        with ctx.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        if on_event:
            on_event(event)

    emit({"type": "round_start", "round": ctx.number, "instruction": instruction})

    async for message in query(prompt=build_prompt(ctx, instruction), options=agent_options()):
        for event in message_to_events(message):
            emit(event)

    emit(
        {
            "type": "round_end",
            "round": ctx.number,
            "summary_exists": ctx.summary_path.exists(),
        }
    )
    return ctx


def message_to_events(message: object) -> AsyncIterator[dict] | list[dict]:
    """SDK 메시지를 UI/로그용 이벤트 dict로 변환한다."""
    events: list[dict] = []
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                events.append({"type": "text", "text": block.text})
            elif isinstance(block, ThinkingBlock):
                if block.thinking:
                    events.append({"type": "thinking", "text": block.thinking})
            elif isinstance(block, ToolUseBlock):
                events.append({"type": "tool_use", "name": block.name, "input": block.input})
    elif isinstance(message, ResultMessage):
        events.append(
            {
                "type": "result",
                "subtype": message.subtype,
                "result": getattr(message, "result", None),
            }
        )
    return events


async def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    instruction = " ".join(sys.argv[1:])

    def print_event(event: dict) -> None:
        kind = event["type"]
        if kind == "text":
            print(event["text"])
        elif kind == "tool_use":
            print(f"  ⚙ {event['name']}")
        elif kind == "round_start":
            print(f"=== Round {event['round']} 시작 ===")
        elif kind == "round_end":
            status = "생성됨" if event["summary_exists"] else "누락!"
            print(f"=== Round {event['round']} 종료 — round_summary.md {status} ===")

    ctx = await run_round(instruction, on_event=print_event)
    if ctx.summary_path.exists():
        print("\n--- Latest Artifact: round_summary.md ---\n")
        print(ctx.summary_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
