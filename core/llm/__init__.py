# -*- coding: utf-8 -*-
"""
LLM模块

提供LLM适配器和工厂函数
"""

from .base_adapter import BaseLLMAdapter
from .gemini_adapter import GeminiAdapter
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter
from .deepseek_adapter import DeepSeekAdapter
from .factory import LLMFactory, get_llm

__all__ = [
    "BaseLLMAdapter",
    "GeminiAdapter",
    "OllamaAdapter", 
    "OpenAIAdapter",
    "DeepSeekAdapter",
    "LLMFactory",
    "get_llm",
]
