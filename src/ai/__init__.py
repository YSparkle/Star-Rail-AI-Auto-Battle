"""
AI 接入模块
提供统一的对话式大模型调用接口，支持自定义提供商与 API Key
"""

from .client import AIClient, AIConfig, AIProviderType

__all__ = [
    "AIClient",
    "AIConfig",
    "AIProviderType",
]
