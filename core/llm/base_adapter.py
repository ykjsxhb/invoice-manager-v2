# -*- coding: utf-8 -*-
"""
LLM适配器基类

定义所有LLM模型适配器的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """LLM模型适配器基类"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
        
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        发送文本请求并获取模型响应
        
        Args:
            prompt: 输入提示词
            **kwargs: 额外参数（temperature, max_tokens等）
            
        Returns:
            模型生成的文本响应
        """
        pass
    
    @abstractmethod
    def generate_with_image(self, prompt: str, image_path: str, **kwargs) -> str:
        """
        多模态：发送图片+文本请求
        
        Args:
            prompt: 输入提示词
            image_path: 图片文件路径
            **kwargs: 额外参数
            
        Returns:
            模型生成的文本响应
        """
        pass
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.model_name,
            "provider": self.__class__.__name__,
            "available": self.is_available()
        }
