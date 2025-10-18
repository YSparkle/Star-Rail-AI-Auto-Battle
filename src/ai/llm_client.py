import json
import os
import ssl
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


class LLMClient:
    """
    A minimal provider-agnostic LLM client that supports a few common backends via HTTP.
    If provider == 'mock', it returns a deterministic, local plan for offline development.
    """

    def __init__(self, provider: str = "mock", api_key: str = "", base_url: str = "", model: str = "", timeout: int = 60):
        self.provider = provider.lower().strip() if provider else "mock"
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.model = model
        self.timeout = timeout

        # Some servers may have self-signed certs (e.g., local ollama proxy). Allow override via env.
        self._ssl_context = ssl.create_default_context()
        if os.environ.get("LLM_INSECURE_SKIP_TLS_VERIFY") == "1":
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE

    def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Return assistant text for given messages.
        messages: list of {role: 'system'|'user'|'assistant', content: str}
        """
        if self.provider == "mock":
            return self._mock_response(system_prompt, messages)
        if self.provider in {"openai", "azure"}:
            return self._openai_compatible(system_prompt, messages)
        if self.provider in {"ollama"}:
            return self._ollama(system_prompt, messages)
        if self.provider == "custom":
            return self._custom_json_api(system_prompt, messages)
        # Fallback to mock
        return self._mock_response(system_prompt, messages)

    # --- Providers ---
    def _openai_compatible(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        url = self.base_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": ([{"role": "system", "content": system_prompt}] if system_prompt else []) + messages,
            "temperature": 0.2,
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=self.timeout) as resp:
                data = json.load(resp)
                # OpenAI format
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except urllib.error.HTTPError as e:
            return f"[LLM HTTPError {e.code}] {e.read().decode(errors='ignore')}"
        except Exception as e:
            return f"[LLM Error] {e}"

    def _ollama(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        url = self.base_url or "http://localhost:11434/api/chat"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model or "llama3",
            "messages": ([{"role": "system", "content": system_prompt}] if system_prompt else []) + messages,
            "stream": False,
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=self.timeout) as resp:
                data = json.load(resp)
                # Ollama format
                return data.get("message", {}).get("content", "")
        except Exception as e:
            return f"[LLM Error] {e}"

    def _custom_json_api(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """
        Generic JSON API: POST to base_url with payload {system, messages, model} and expect {text}
        """
        url = self.base_url
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"system": system_prompt, "messages": messages, "model": self.model}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=self.timeout) as resp:
                data = json.load(resp)
                return data.get("text", "")
        except Exception as e:
            return f"[LLM Error] {e}"

    # --- Mock ---
    def _mock_response(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        # A simple deterministic plan response
        return (
            "计划A: 两轮结束战斗。策略: 优先充能 -> 群攻 -> 单体收尾; RNG: 需要1次暴击。\n"
            "计划B: 三轮稳定通关。策略: 开局上增伤 -> 单体速杀精英 -> 群攻清场; RNG: 无需凹。\n"
            "请在配置中选择 plan_choice = 0 或 1。"
        )
