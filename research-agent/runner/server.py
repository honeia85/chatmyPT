#!/usr/bin/env python3
"""연구 워크스페이스 UI 백엔드 (Ch.7 Phase 2 — Rev2Agent 구조).

UI ↔ 에이전트 루프를 잇는 얇은 중계 서버:
- GET  /                      : ui/index.html
- GET  /api/rounds            : 라운드 목록과 아티팩트 존재 여부
- GET  /api/artifact/latest   : 가장 최근 round_summary.md (Latest Artifact 패널)
- GET  /api/run?instruction=  : 라운드 실행 — SDK 이벤트를 SSE로 스트리밍 (Live Run Console)

사용:
    pip install -r requirements.txt
    uvicorn server:app --port 8787
    → http://localhost:8787
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from run_agent import EXPERIMENTS, WORKSPACE, run_round

app = FastAPI(title="Research Agent Workspace")
UI_DIR = WORKSPACE / "ui"

RUN_LOCK = asyncio.Lock()  # 라운드는 한 번에 하나만


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/api/rounds")
async def rounds() -> JSONResponse:
    items = []
    if EXPERIMENTS.exists():
        for d in sorted(EXPERIMENTS.glob("round-*")):
            if not d.is_dir():
                continue
            review = d / "review.md"
            verdict = None
            if review.exists():
                first = review.read_text(encoding="utf-8").splitlines()[:1]
                verdict = first[0].replace("VERDICT:", "").strip() if first else None
            items.append(
                {
                    "round": int(d.name.split("-")[1]),
                    "has_plan": (d / "plan.md").exists(),
                    "has_summary": (d / "round_summary.md").exists(),
                    "verdict": verdict,
                }
            )
    return JSONResponse(sorted(items, key=lambda x: x["round"]))


@app.get("/api/artifact/latest")
async def latest_artifact() -> JSONResponse:
    if EXPERIMENTS.exists():
        for d in sorted(EXPERIMENTS.glob("round-*"), key=lambda p: int(p.name.split("-")[1]), reverse=True):
            summary = d / "round_summary.md"
            if summary.exists():
                return JSONResponse(
                    {"round": int(d.name.split("-")[1]), "path": str(summary.relative_to(WORKSPACE)),
                     "markdown": summary.read_text(encoding="utf-8")}
                )
    return JSONResponse({"round": None, "path": None, "markdown": "아직 아티팩트가 없습니다."})


@app.get("/api/run")
async def run(instruction: str) -> StreamingResponse:
    """SSE 스트림: 에이전트 루프의 이벤트를 실시간 전달한다."""

    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    def on_event(event: dict) -> None:
        queue.put_nowait(event)

    async def worker() -> None:
        async with RUN_LOCK:
            try:
                await run_round(instruction, on_event=on_event)
            except Exception as exc:  # noqa: BLE001 — UI에 오류를 그대로 보여준다
                queue.put_nowait({"type": "error", "message": str(exc)})
            finally:
                queue.put_nowait(None)

    async def stream():
        task = asyncio.create_task(worker())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        finally:
            await task

    return StreamingResponse(stream(), media_type="text/event-stream")
