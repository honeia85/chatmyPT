"""
SharedModel - 모든 에이전트가 공유하는 단일 모델 인스턴스 (싱글턴)
"""

import gc
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig


def _get_device():
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class SharedModel:
    """Qwen-1.8B-Chat 싱글턴. 모든 에이전트가 이 인스턴스를 공유합니다."""

    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        model_name = "Qwen/Qwen-1_8B-Chat"
        self.device = _get_device()
        print(f"Using device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            trust_remote_code=True,
            use_cache=True,
        ).to(self.device).eval()

        self.model.generation_config = GenerationConfig.from_pretrained(
            model_name,
            trust_remote_code=True,
            max_new_tokens=512,
            temperature=0.8,
            top_p=0.9,
            repetition_penalty=1.1,
        )
        self.clean_memory()

    def chat(self, query, history=None, system=""):
        """model.chat() 래퍼. torch.no_grad() 자동 적용."""
        with torch.no_grad():
            response, new_history = self.model.chat(
                self.tokenizer,
                query,
                history=history or [],
                system=system,
            )
        return response, new_history

    def clean_memory(self):
        gc.collect()
        if self.device.type == "mps":
            torch.mps.empty_cache()
        elif self.device.type == "cuda":
            torch.cuda.empty_cache()
