"""
Gradio UI - 멀티에이전트 오케스트레이터 인터페이스

레이아웃:
  좌측 (30%): 입력 파일 목록 + 파일 업로드 + 조직도(에이전트 트리)
  우측 (70%): 대화 챗봇 + 상태 표시 + 메시지 입력
"""

import shutil
from pathlib import Path

import gradio as gr

from .task import Orchestrator
from .file_reader import FileReader
from .departments import ORGANIZATION


INPUT_FOLDER = "input"


def _build_org_chart():
    """전체 조직도 텍스트를 생성합니다."""
    lines = ["```", "🏢 대표이사 (CEO)  ⏸"]
    for div in ORGANIZATION.values():
        _org_lines(div, lines, indent=0, is_last=False)
    lines.append("```")
    return "\n".join(lines)


def _org_lines(unit, lines, indent, is_last):
    prefix = "│  " * indent + ("└─ " if is_last else "├─ ")
    lines.append(f"{prefix}{unit['icon']} {unit['name']}")
    subs = list(unit.get("units", {}).values())
    for i, sub in enumerate(subs):
        _org_lines(sub, lines, indent + 1, is_last=(i == len(subs) - 1))


def _refresh_file_list():
    files = FileReader.scan_folder(INPUT_FOLDER)
    if not files:
        return "파일 없음 — `input/` 폴더에 파일을 넣거나 아래에서 업로드하세요."
    lines = []
    for fi in files:
        badge = {"text": "TXT", "csv": "CSV", "pdf": "PDF",
                 "json": "JSON", "image": "IMG"}.get(fi.file_type, "???")
        lines.append(f"- **{fi.name}** `{badge}`")
    return "\n".join(lines)


def create_demo():
    lab = Orchestrator(input_folder=INPUT_FOLDER)
    initial_org = _build_org_chart()

    with gr.Blocks(
        title="멀티에이전트 오케스트레이터",
        css="footer {visibility: hidden}",
    ) as demo:

        gr.Markdown(
            "# 멀티에이전트 연구소\n\n"
            "`input/` 폴더에 파일을 넣거나 업로드한 후, 질문을 입력하세요.\n"
            "CEO가 본부에 업무를 배정하고, 본부장은 팀장에게, 팀장은 연구원에게 위임합니다."
        )

        with gr.Row():
            # ── 좌측: 파일 + 조직도 ──
            with gr.Column(scale=3):
                gr.Markdown("### 입력 파일")
                file_list = gr.Markdown(_refresh_file_list())
                file_upload = gr.File(
                    label="파일 업로드 (input/ 폴더에 복사됨)",
                    file_count="multiple",
                    file_types=[".pdf", ".csv", ".txt", ".json", ".md", ".tsv", ".log"],
                )
                refresh_btn = gr.Button("파일 목록 새로고침", size="sm")

                gr.Markdown("### 조직도 (실시간)")
                agent_tree = gr.Markdown(initial_org)

            # ── 우측: 대화 ──
            with gr.Column(scale=7):
                chatbot = gr.Chatbot(
                    label="대화",
                    height=550,
                    bubble_full_width=False,
                    show_copy_button=True,
                )
                status = gr.Markdown("")

                with gr.Row():
                    msg = gr.Textbox(
                        label="메시지",
                        placeholder="파일에 대해 질문하세요...",
                        scale=4,
                        lines=2,
                    )
                    submit_btn = gr.Button("전송", variant="primary", scale=1)

                clear_btn = gr.Button("초기화")

        with gr.Accordion("사용 방법", open=False):
            gr.Markdown(
                "1. `input/` 폴더에 분석할 파일(PDF, CSV, TXT 등)을 넣습니다.\n"
                "2. 또는 위 '파일 업로드'로 직접 업로드합니다.\n"
                "3. 메시지 입력창에 원하는 분석을 요청합니다.\n"
                "4. **CEO**가 요청을 분석하고 적절한 **본부**에 업무를 배정합니다.\n"
                "5. **본부장**이 필요시 **팀장**에게, 팀장은 **연구원**에게 위임합니다.\n"
                "6. 모든 결과가 계층을 따라 종합되어 최종 답변이 제공됩니다.\n\n"
                "**예시 질문:**\n"
                "- 이 CSV 파일의 주요 통계를 분석해주세요\n"
                "- 이 보고서의 핵심 내용을 요약해주세요\n"
                "- 두 파일을 비교 분석해주세요\n"
                "- 이 데이터에서 이상한 패턴이 있나요?\n"
            )

        # ── 이벤트 핸들러 ──

        def on_upload(uploaded):
            if not uploaded:
                return _refresh_file_list()
            Path(INPUT_FOLDER).mkdir(parents=True, exist_ok=True)
            for f in uploaded:
                dest = Path(INPUT_FOLDER) / Path(f.name).name
                shutil.copy2(f.name, str(dest))
            return _refresh_file_list()

        def on_submit(message, history):
            if not message.strip():
                yield history or [], "", initial_org, ""
                return

            current = list(history or [])
            current.append((message, None))
            yield current, "", initial_org, "**🏢 대표이사** 요청을 분석하고 있습니다..."

            for update in lab.process(message):
                phase = update["phase"]
                title = update["agent_title"]
                content = update["content"]
                tree = update["tree"]

                entry = f"**{title}** _[{phase}]_\n\n{content}"
                current.append((None, entry))

                tree_display = f"```\n{tree}\n```"
                status_text = f"**{update['agent_name']}** 처리 중..."
                yield current, "", tree_display, status_text

            yield current, "", tree_display, "**완료!**"

        def on_clear():
            lab.clear()
            return [], "", initial_org, ""

        refresh_btn.click(_refresh_file_list, outputs=[file_list])
        file_upload.change(on_upload, inputs=[file_upload], outputs=[file_list])

        submit_btn.click(
            on_submit,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg, agent_tree, status],
        )
        msg.submit(
            on_submit,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg, agent_tree, status],
        )
        clear_btn.click(on_clear, outputs=[chatbot, msg, agent_tree, status])

        demo.load(_refresh_file_list, outputs=[file_list])

    return demo
