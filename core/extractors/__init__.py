# -*- coding: utf-8 -*-
"""
提取器模块

提供多种发票信息提取器
"""

from .base import BaseExtractor, InvoiceInfo
from .llm_extractor import LLMInvoiceExtractor
from .hybrid_extractor import HybridExtractor, RegexFallbackExtractor
from .vision_extractor import VisionExtractor

__all__ = [
    "BaseExtractor",
    "InvoiceInfo",
    "LLMInvoiceExtractor",
    "HybridExtractor",
    "RegexFallbackExtractor",
    "VisionExtractor",
]


def get_extractor(mode: str = "hybrid", adapter=None):
    """
    获取提取器实例
    
    Args:
        mode: 提取模式
            - "llm": 纯LLM提取
            - "hybrid": 混合模式（推荐）
            - "vision": 视觉识别
            - "regex_fallback": 正则兜底
        adapter: LLM适配器实例
        
    Returns:
        对应的提取器实例
    """
    if mode == "llm":
        return LLMInvoiceExtractor(adapter)
    elif mode == "hybrid":
        return HybridExtractor(adapter)
    elif mode == "vision":
        return VisionExtractor(adapter)
    elif mode == "regex_fallback":
        return RegexFallbackExtractor()
    else:
        raise ValueError(f"不支持的提取模式: {mode}")
