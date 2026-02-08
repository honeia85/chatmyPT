"""
멀티에이전트 오케스트레이터 - 진입점

실행: python orchestrate.py
접속: http://localhost:7861
"""

from orchestrator import create_demo

if __name__ == "__main__":
    demo = create_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=True,
        inbrowser=True,
    )
