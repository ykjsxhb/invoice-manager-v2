# -*- coding: utf-8 -*-
"""
LLM模型工厂

根据配置创建对应的LLM适配器实例
"""

import logging
from typing import Optional

from .base_adapter import BaseLLMAdapter
from .gemini_adapter import GeminiAdapter
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter
from .deepseek_adapter import DeepSeekAdapter

logger = logging.getLogger(__name__)


class LLMFactory:
    """LLM模型工厂"""
    
    _adapters = {
        "gemini": GeminiAdapter,
        "openai": OpenAIAdapter,
        "ollama": OllamaAdapter,
        "deepseek": DeepSeekAdapter,
    }
    
    @classmethod
    def create(
        cls, 
        provider: str = "gemini", 
        model_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLMAdapter:
        """
        创建LLM适配器实例
        
        Args:
            provider: 提供商名称 (gemini/openai/ollama)
            model_name: 模型名称，为None时使用默认模型
            **kwargs: 传递给适配器的额外参数
            
        Returns:
            对应的LLM适配器实例
        """
        provider = provider.lower()
        
        if provider not in cls._adapters:
            raise ValueError(f"不支持的LLM提供商: {provider}，支持的选项: {list(cls._adapters.keys())}")
        
        adapter_class = cls._adapters[provider]
        
        # 设置默认模型名称
        default_models = {
            "gemini": "gemini-2.5-flash",
            "openai": "gpt-4o-mini",
            "ollama": "qwen2.5:7b",
            "deepseek": "deepseek-chat",
        }
        
        # 如果model_name为None或空字符串，使用默认值
        if not model_name:
            model_name = default_models.get(provider)
        
        logger.info(f"创建LLM适配器: {provider} / {model_name}")
        
        return adapter_class(model_name=model_name, **kwargs)
    
    @classmethod
    def create_from_config(cls) -> BaseLLMAdapter:
        """
        从配置文件创建LLM适配器
        
        Returns:
            根据配置创建的LLM适配器实例
        """
        from ..config.settings import (
            LLM_PROVIDER, 
            LLM_MODEL, 
            GEMINI_API_KEY,
            OPENAI_API_KEY,
            OLLAMA_BASE_URL,
            OLLAMA_MODEL,
            DEEPSEEK_API_KEY,
            DEEPSEEK_BASE_URL
        )
        
        if LLM_PROVIDER == "gemini":
            return cls.create("gemini", LLM_MODEL, api_key=GEMINI_API_KEY)
        elif LLM_PROVIDER == "openai":
            return cls.create("openai", LLM_MODEL, api_key=OPENAI_API_KEY)
        elif LLM_PROVIDER == "ollama":
            model = LLM_MODEL if LLM_MODEL else OLLAMA_MODEL
            return cls.create("ollama", model, base_url=OLLAMA_BASE_URL)
        elif LLM_PROVIDER == "deepseek":
            return cls.create("deepseek", LLM_MODEL, api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        else:
            raise ValueError(f"未知的LLM提供商: {LLM_PROVIDER}")
    
    @classmethod
    def list_providers(cls) -> list:
        """列出支持的提供商"""
        return list(cls._adapters.keys())


def get_llm(provider: str = None, model_name: str = None, **kwargs) -> BaseLLMAdapter:
    """
    便捷函数：获取LLM适配器
    
    Args:
        provider: 提供商名称，为None时从配置读取
        model_name: 模型名称，为None时使用默认值
        **kwargs: 额外参数
        
    Returns:
        LLM适配器实例
    """
    if provider is None:
        return LLMFactory.create_from_config()
    return LLMFactory.create(provider, model_name, **kwargs)
