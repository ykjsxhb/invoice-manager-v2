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


def get_extractor(mode: str = "hybrid", adapter=None, text_adapter=None, vision_adapter=None):
    """
    获取提取器实例
    
    Args:
        mode: 提取模式
            - "llm": 纯LLM提取
            - "hybrid": 混合模式（推荐）
            - "vision": 视觉识别
            - "regex_fallback": 正则兜底
        adapter: LLM适配器实例（兼容旧接口）
        text_adapter: 文本LLM适配器（用于处理PDF/OFD/XML的文本）
        vision_adapter: 视觉LLM适配器（用于处理图片）
        
    Returns:
        对应的提取器实例
    """
    # 兼容旧接口：如果只传了 adapter，则两者都使用它
    if adapter is not None and text_adapter is None:
        text_adapter = adapter
    if adapter is not None and vision_adapter is None:
        vision_adapter = adapter
    
    if mode == "llm":
        return LLMInvoiceExtractor(text_adapter, vision_adapter)
    elif mode == "hybrid":
        return HybridExtractor(text_adapter, vision_adapter)
    elif mode == "vision":
        return VisionExtractor(vision_adapter)
    elif mode == "regex_fallback":
        return RegexFallbackExtractor()
    else:
        raise ValueError(f"不支持的提取模式: {mode}")
