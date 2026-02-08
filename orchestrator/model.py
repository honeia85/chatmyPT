"""
SharedModel - Anthropic Claude API 클라이언트 (싱글턴)

환경변수 ANTHROPIC_API_KEY 필요.
"""

import os
from anthropic import Anthropic

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 1024


class SharedModel:
    """Claude API 싱글턴. 모든 에이전트가 이 클라이언트를 공유합니다."""

    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.\n"
                "export ANTHROPIC_API_KEY='your-api-key' 를 실행하세요."
            )
        self.client = Anthropic(api_key=api_key)
        self.model = os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL)
        self.max_tokens = int(os.environ.get("CLAUDE_MAX_TOKENS", MAX_TOKENS))
        print(f"Claude API 연결 완료 (model: {self.model})")

    def chat(self, query, history=None, system=""):
        """
        Claude API를 호출하여 응답을 생성합니다.

        Args:
            query: 사용자 메시지
            history: 이전 대화 기록 [{"role": ..., "content": ...}, ...]
            system: 시스템 프롬프트

        Returns:
            (response_text, updated_history)
        """
        messages = list(history or [])
        messages.append({"role": "user", "content": query})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
        )

        assistant_text = response.content[0].text
        messages.append({"role": "assistant", "content": assistant_text})

        return assistant_text, messages

    def clean_memory(self):
        """API 기반이므로 로컬 메모리 정리 불필요. 호환성 유지용."""
        pass
