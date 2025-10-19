"""
通用 AI 客户端
- 支持 OpenAI 兼容 API（如 OpenAI、DeepSeek、硅基流动、云厂商网关等）
- 通过配置指定 provider、base_url、model、api_key 与系统提示词
- 只在需要时调用，默认对项目其它模块零侵入
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

try:
    import requests  # type: ignore
except Exception:  # 在无 requests 环境下，延迟报错
    requests = None  # type: ignore


class AIProviderType(str, Enum):
    OPENAI_COMPATIBLE = "openai_compatible"  # 通用 /v1/chat/completions 兼容
    CUSTOM_HTTP = "custom_http"  # 自定义 HTTP，按 config 填写 endpoint


@dataclass
class AIConfig:
    enabled: bool = False
    provider: AIProviderType = AIProviderType.OPENAI_COMPATIBLE
    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    system_prompt: Optional[str] = None
    timeout: int = 60
    # 仅 CUSTOM_HTTP 时可用
    endpoint: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


class AIClient:
    """统一对话接口。当前实现了 OpenAI 兼容的 chat.completions。
    如果未启用或未配置，将在调用时抛出合理异常或返回兜底内容。
    """

    def __init__(self, config: AIConfig):
        self.logger = logging.getLogger(__name__)
        self.config = config

    def is_available(self) -> bool:
        return bool(self.config.enabled and self.config.api_key)

    def _ensure_requests(self):
        if requests is None:
            raise RuntimeError("缺少 requests 依赖，请先安装: pip install requests")

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None,
             temperature: float = 0.2, max_tokens: Optional[int] = None) -> str:
        """与大模型对话，返回 assistant 文本。
        messages: [{role, content}]，支持 system/assistant/user
        """
        if not self.is_available():
            self.logger.warning("AI 未启用或未配置，返回占位文本")
            return "[AI 未启用：无法生成计划，请在 config.json 配置 ai 字段]"

        self._ensure_requests()
        sys_prompt = system_prompt or self.config.system_prompt
        payload_msgs: List[Dict[str, str]] = []
        if sys_prompt:
            payload_msgs.append({"role": "system", "content": sys_prompt})
        payload_msgs.extend(messages)

        if self.config.provider == AIProviderType.OPENAI_COMPATIBLE:
            url = f"{self.config.base_url.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": self.config.model,
                "messages": payload_msgs,
                "temperature": temperature,
            }
            if max_tokens is not None:
                data["max_tokens"] = max_tokens

            resp = requests.post(url, headers=headers, json=data, timeout=self.config.timeout)
            resp.raise_for_status()
            j = resp.json()
            # OpenAI 格式
            content = j.get("choices", [{}])[0].get("message", {}).get("content")
            if not content:
                # 某些兼容网关返回 text 字段
                content = j.get("choices", [{}])[0].get("text")
            return content or "[AI 响应为空]"

        elif self.config.provider == AIProviderType.CUSTOM_HTTP:
            if not self.config.endpoint:
                raise ValueError("自定义 HTTP 模式需要提供 endpoint")
            headers = self.config.headers or {}
            if self.config.api_key:
                headers.setdefault("Authorization", f"Bearer {self.config.api_key}")
            data = {
                "model": self.config.model,
                "messages": payload_msgs,
                "temperature": temperature,
            }
            resp = requests.post(self.config.endpoint, headers=headers, json=data, timeout=self.config.timeout)
            resp.raise_for_status()
            j = resp.json()
            # 尝试兼容 OpenAI 格式
            return (
                j.get("choices", [{}])[0].get("message", {}).get("content")
                or j.get("choices", [{}])[0].get("text")
                or j.get("data")
                or json.dumps(j, ensure_ascii=False)
            )

        else:
            raise NotImplementedError(f"不支持的 provider: {self.config.provider}")

    def summarize_to_plan(self, context: Dict) -> str:
        """给定上下文，生成策略规划文本（由模型输出）。
        这是一个轻薄封装，方便策略模块调用。
        """
        prompt = (
            "你是《崩坏：星穹铁道》的战斗策略专家。\n"
            "根据给定角色、遗器、敌人与模式，输出可执行的最优方案，\n"
            "并给出至少两套供玩家选择的策略：\n"
            "- A 方案：追求稳定，不依赖凹点\n"
            "- B 方案：追求极限（可包含凹点，例如吃特定攻击、控敌、回能等）\n"
            "若 preferences.reroll_settings 存在，请在 B 方案中明确凹点条件（诱导对象、触发条件、最大重试次数）。\n"
            "每套方案请给出：先后手顺序、技能释放、站位/换位、目标选择、回合规划与预期回合数。\n"
            "输出以清晰的小标题和步骤列表呈现。"
        )
        msg = [
            {"role": "user", "content": prompt + "\n\n上下文 JSON:\n" + json.dumps(context, ensure_ascii=False)}
        ]
        try:
            return self.chat(msg)
        except Exception as e:
            self.logger.error(f"AI 生成计划失败: {e}")
            return "[AI 生成失败：请检查网络/配置]"
