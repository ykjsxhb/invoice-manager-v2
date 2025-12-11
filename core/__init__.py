# -*- coding: utf-8 -*-
"""
发票管理系统V2 - 核心模块
"""

from .config import settings
from .llm import get_llm, LLMFactory
from .extractors import get_extractor, InvoiceInfo

__all__ = [
    "settings",
    "get_llm",
    "LLMFactory",
    "get_extractor",
    "InvoiceInfo",
]
