"""
멀티에이전트 과학 연구소 (Multi-Agent Science Lab)

여러 AI 과학자 에이전트가 협력하여 과학 질문을 다각적으로 분석하고 답변합니다.

에이전트 구성:
  - 연구 총괄: 질문 분석 및 최종 결론 도출
  - 물리학자: 물리학적 관점 분석
  - 화학자:   화학적 관점 분석
  - 생물학자: 생명과학적 관점 분석
  - 수학자:   수학적 모델링 및 정량 분석

실행: python science_lab.py
접속: http://localhost:7861
"""

import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
import gc


# ═══════════════════════════════════════════════════════════════
# 디바이스 감지 및 모델 초기화
# ═══════════════════════════════════════════════════════════════

def get_device():
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def init_model():
    model_name = "Qwen/Qwen-1_8B-Chat"
    device = get_device()
    print(f"Using device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        use_cache=True
    ).to(device).eval()

    model.generation_config = GenerationConfig.from_pretrained(
        model_name,
        trust_remote_code=True,
        max_new_tokens=512,
        temperature=0.8,
        top_p=0.9,
        repetition_penalty=1.1
    )

    gc.collect()
    if device.type == "mps":
        torch.mps.empty_cache()
    elif device.type == "cuda":
        torch.cuda.empty_cache()

    return model, tokenizer, device


def clean_memory(device):
    gc.collect()
    if device.type == "mps":
        torch.mps.empty_cache()
    elif device.type == "cuda":
        torch.cuda.empty_cache()


# ═══════════════════════════════════════════════════════════════
# 에이전트 프로필 정의
# ═══════════════════════════════════════════════════════════════

AGENT_PROFILES = {
    "director": {
        "name": "연구 총괄",
        "icon": "🔬",
        "role": "연구 총괄 디렉터",
        "system_prompt": (
            "당신은 과학 연구소의 연구 총괄 디렉터입니다. "
            "과학 질문을 분석하고, 어떤 분야의 전문 지식이 필요한지 파악하며, "
            "여러 전문가의 의견을 종합하여 명확하고 체계적인 결론을 도출합니다. "
            "항상 한국어로 답변하세요."
        ),
    },
    "physicist": {
        "name": "물리학자",
        "icon": "⚛️",
        "role": "이론물리학 전문가",
        "system_prompt": (
            "당신은 이론물리학 전문가입니다. "
            "양자역학, 상대성이론, 열역학, 전자기학, 입자물리학 등 "
            "물리학의 관점에서 현상을 분석합니다. "
            "물리 법칙과 수식을 인용하며 물리학적 직관으로 설명하세요. "
            "항상 한국어로 답변하세요."
        ),
    },
    "chemist": {
        "name": "화학자",
        "icon": "🧪",
        "role": "화학 전문가",
        "system_prompt": (
            "당신은 화학 전문가입니다. "
            "유기화학, 무기화학, 물리화학, 생화학, 분석화학 등 "
            "화학의 관점에서 물질과 반응을 분석합니다. "
            "분자 구조, 화학 결합, 반응 메커니즘 등의 개념을 활용하여 설명하세요. "
            "항상 한국어로 답변하세요."
        ),
    },
    "biologist": {
        "name": "생물학자",
        "icon": "🧬",
        "role": "생명과학 전문가",
        "system_prompt": (
            "당신은 생명과학 전문가입니다. "
            "분자생물학, 유전학, 세포생물학, 생태학, 진화생물학 등 "
            "생물학의 관점에서 생명 현상을 분석합니다. "
            "생명의 메커니즘과 진화적 관점에서 설명하세요. "
            "항상 한국어로 답변하세요."
        ),
    },
    "mathematician": {
        "name": "수학자",
        "icon": "📐",
        "role": "응용수학 전문가",
        "system_prompt": (
            "당신은 응용수학 전문가입니다. "
            "미적분학, 선형대수, 확률통계, 미분방정식, 위상수학 등 "
            "수학적 도구를 활용하여 과학 문제를 분석합니다. "
            "수학적 모델링과 정량적 분석 관점에서 설명하세요. "
            "항상 한국어로 답변하세요."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════
# 과학자 에이전트 클래스
# ═══════════════════════════════════════════════════════════════

class ScientistAgent:
    """개별 과학자 에이전트. 고유한 시스템 프롬프트로 전문 분야 역할을 수행합니다."""

    def __init__(self, key, profile, model, tokenizer, device):
        self.key = key
        self.name = profile["name"]
        self.icon = profile["icon"]
        self.role = profile["role"]
        self.system_prompt = profile["system_prompt"]
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.history = []

    @property
    def display_name(self):
        return f"{self.icon} {self.name}"

    def respond(self, query):
        """에이전트의 전문 관점에서 응답을 생성합니다."""
        try:
            with torch.no_grad():
                response, self.history = self.model.chat(
                    self.tokenizer,
                    query,
                    history=self.history,
                    system=self.system_prompt,
                )

            if len(self.history) > 3:
                self.history = self.history[-3:]

            return response
        except Exception as e:
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"

    def clear_history(self):
        self.history = []


# ═══════════════════════════════════════════════════════════════
# 과학 연구소 오케스트레이터
# ═══════════════════════════════════════════════════════════════

class ScienceLab:
    """
    멀티에이전트 과학 연구소.

    토론 흐름:
      1. 연구 총괄이 질문을 분석
      2. 4명의 전문가(물리학자, 화학자, 생물학자, 수학자)가 각자의 관점에서 분석
      3. 연구 총괄이 모든 의견을 종합하여 최종 결론 도출
    """

    SPECIALIST_KEYS = ["physicist", "chemist", "biologist", "mathematician"]

    def __init__(self):
        print("=" * 50)
        print("  멀티에이전트 과학 연구소 초기화 중...")
        print("=" * 50)

        self.model, self.tokenizer, self.device = init_model()
        self.agents = {}

        for key, profile in AGENT_PROFILES.items():
            self.agents[key] = ScientistAgent(
                key=key,
                profile=profile,
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device,
            )
            print(f"  {profile['icon']} {profile['name']} 에이전트 준비 완료")

        print("=" * 50)
        print("  과학 연구소 준비 완료!")
        print("=" * 50)

    @property
    def director(self):
        return self.agents["director"]

    def discuss(self, question):
        """
        멀티에이전트 토론을 실행합니다.
        각 단계마다 현재까지의 토론 결과를 yield합니다.
        """
        discussion = []

        # ── 1단계: 연구 총괄의 질문 분석 ──
        analysis = self.director.respond(
            f"다음 과학 질문을 분석해주세요. "
            f"어떤 과학 분야가 관련되는지, 핵심 쟁점은 무엇인지 정리해주세요.\n\n"
            f"질문: {question}"
        )
        discussion.append({
            "agent": self.director.display_name,
            "role": self.director.role,
            "phase": "질문 분석",
            "content": analysis,
        })
        yield list(discussion)

        # ── 2단계: 각 전문가의 관점 ──
        for key in self.SPECIALIST_KEYS:
            agent = self.agents[key]
            response = agent.respond(
                f"당신의 전문 분야({agent.role})의 관점에서 "
                f"다음 질문을 분석하고 답변해주세요.\n\n"
                f"질문: {question}"
            )
            discussion.append({
                "agent": agent.display_name,
                "role": agent.role,
                "phase": "전문가 분석",
                "content": response,
            })
            yield list(discussion)
            clean_memory(self.device)

        # ── 3단계: 연구 총괄의 종합 결론 ──
        expert_opinions = "\n\n".join(
            f"[{entry['agent']}] {entry['content']}"
            for entry in discussion[1:]  # 전문가 의견만
        )
        synthesis = self.director.respond(
            f"원래 질문: {question}\n\n"
            f"각 전문가의 분석 결과:\n{expert_opinions}\n\n"
            f"위 전문가들의 분석을 종합하여 최종 결론을 도출해주세요. "
            f"각 분야의 핵심 기여를 요약하고, 통합적인 답변을 제시하세요."
        )
        discussion.append({
            "agent": self.director.display_name,
            "role": self.director.role,
            "phase": "종합 결론",
            "content": synthesis,
        })
        yield list(discussion)

    def clear_all(self):
        """모든 에이전트의 대화 히스토리를 초기화합니다."""
        for agent in self.agents.values():
            agent.clear_history()
        clean_memory(self.device)


# ═══════════════════════════════════════════════════════════════
# Gradio UI
# ═══════════════════════════════════════════════════════════════

PHASE_COLORS = {
    "질문 분석": "#4A90D9",
    "전문가 분석": "#7B68EE",
    "종합 결론": "#2ECC71",
}


def format_discussion(discussion):
    """토론 결과를 Gradio Chatbot 튜플 형식으로 변환합니다."""
    chat_history = []
    for entry in discussion:
        phase = entry["phase"]
        color = PHASE_COLORS.get(phase, "#888")
        header = (
            f"**{entry['agent']}** · {entry['role']}\n"
            f"_\\[{phase}\\]_"
        )
        msg = f"{header}\n\n---\n\n{entry['content']}"
        chat_history.append((None, msg))
    return chat_history


def create_science_lab_demo():
    lab = ScienceLab()

    with gr.Blocks(
        title="멀티에이전트 과학 연구소",
        css="footer {visibility: hidden}",
    ) as demo:
        gr.Markdown(
            "# 멀티에이전트 과학 연구소\n\n"
            "**5명의 AI 과학자 에이전트가 협력하여 과학 질문에 답합니다.**\n\n"
            "| 에이전트 | 역할 | 전문 분야 |\n"
            "|---------|------|----------|\n"
            "| 🔬 연구 총괄 | 분석 & 종합 | 질문 분석, 최종 결론 도출 |\n"
            "| ⚛️ 물리학자 | 전문가 분석 | 양자역학, 상대성이론, 열역학 |\n"
            "| 🧪 화학자 | 전문가 분석 | 유기화학, 물리화학, 생화학 |\n"
            "| 🧬 생물학자 | 전문가 분석 | 분자생물학, 유전학, 생태학 |\n"
            "| 📐 수학자 | 전문가 분석 | 수학적 모델링, 확률통계 |\n\n"
            "---"
        )

        chatbot = gr.Chatbot(
            label="연구소 토론",
            height=600,
            bubble_full_width=False,
            show_copy_button=True,
        )

        status = gr.Markdown("")

        with gr.Row():
            question_input = gr.Textbox(
                label="과학 질문",
                placeholder="예: 블랙홀 근처에서 시간은 왜 느리게 흐르나요?",
                scale=4,
                lines=2,
            )
            submit_btn = gr.Button("연구 시작", variant="primary", scale=1)

        clear_btn = gr.Button("초기화")

        with gr.Accordion("예시 질문", open=False):
            gr.Markdown(
                "- 물은 왜 100도에서 끓나요?\n"
                "- DNA는 어떻게 복제되나요?\n"
                "- 우주의 엔트로피는 왜 항상 증가하나요?\n"
                "- 광합성의 화학적 메커니즘은 무엇인가요?\n"
                "- 슈뢰딩거 방정식은 무엇을 설명하나요?\n"
                "- 지구의 자기장은 어떻게 만들어지나요?\n"
                "- 암세포는 정상세포와 어떻게 다른가요?\n"
                "- 빛의 이중성이란 무엇인가요?\n"
            )

        # ── 이벤트 핸들러 ──

        agent_order = [
            ("🔬 연구 총괄", "질문을 분석하고 있습니다..."),
            ("⚛️ 물리학자", "물리학적 관점에서 분석 중..."),
            ("🧪 화학자", "화학적 관점에서 분석 중..."),
            ("🧬 생물학자", "생명과학적 관점에서 분석 중..."),
            ("📐 수학자", "수학적 관점에서 분석 중..."),
            ("🔬 연구 총괄", "전문가 의견을 종합하는 중..."),
        ]

        def on_submit(question, history):
            if not question.strip():
                yield history or [], "", ""
                return

            base = history or []
            step = 0

            for discussion in lab.discuss(question):
                formatted = format_discussion(discussion)
                current = base + [(question, None)] + formatted
                # 첫 번째 항목에 사용자 질문 포함
                current = base.copy()
                current.append((question, None))
                for entry in formatted:
                    current.append(entry)

                if step < len(agent_order):
                    icon, desc = agent_order[step]
                    status_text = f"**{icon}** {desc}"
                else:
                    status_text = ""
                step += 1

                yield current, "", status_text

            yield current, "", "**연구 완료!**"

        def on_clear():
            lab.clear_all()
            return [], "", ""

        submit_btn.click(
            on_submit,
            inputs=[question_input, chatbot],
            outputs=[chatbot, question_input, status],
        )

        question_input.submit(
            on_submit,
            inputs=[question_input, chatbot],
            outputs=[chatbot, question_input, status],
        )

        clear_btn.click(
            on_clear,
            outputs=[chatbot, question_input, status],
        )

    return demo


# ═══════════════════════════════════════════════════════════════
# 메인 실행
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo = create_science_lab_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=True,
        inbrowser=True,
    )
