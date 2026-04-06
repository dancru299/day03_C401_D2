import json
import time
from typing import Any, Dict, Generator, Optional

import requests

from src.core.llm_provider import LLMProvider


class OllamaProvider(LLMProvider):
    """LLM Provider for self-hosted Ollama models via HTTP API."""

    def __init__(
        self,
        model_name: str = "qwen2.5:7b-instruct-q3_k_L",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        super().__init__(model_name=model_name)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _build_prompt(self, prompt: str, system_prompt: Optional[str]) -> str:
        if system_prompt:
            return f"System: {system_prompt}\n\nUser: {prompt}"
        return prompt

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        payload = {
            "model": self.model_name,
            "prompt": self._build_prompt(prompt, system_prompt),
            "stream": False,
        }

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        }

        return {
            "content": data.get("response", ""),
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "ollama",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        payload = {
            "model": self.model_name,
            "prompt": self._build_prompt(prompt, system_prompt),
            "stream": True,
        }

        with requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            stream=True,
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except ValueError:
                    continue

                token = chunk.get("response", "")
                if token:
                    yield token
