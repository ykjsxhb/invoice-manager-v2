# -*- coding: utf-8 -*-
"""
Gemini API 适配器

支持 Google Gemini 模型的文本和多模态调用
"""

import os
import base64
import logging
from typing import Optional

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini API 适配器"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None, **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._client = None
        self._model = None
        
    def _ensure_client(self):
        """确保客户端已初始化"""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
                self._model = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini客户端初始化成功，模型：{self.model_name}")
            except ImportError:
                raise ImportError("请安装 google-generativeai: pip install google-generativeai")
            except Exception as e:
                logger.error(f"Gemini客户端初始化失败: {e}")
                raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        发送文本请求
        
        Args:
            prompt: 输入提示词
            **kwargs: 可选参数
                - temperature: 生成温度 (0-1)
                - max_output_tokens: 最大输出token数
                
        Returns:
            模型生成的文本
        """
        self._ensure_client()
        
        try:
            # 配置生成参数
            generation_config = {
                "temperature": kwargs.get("temperature", 0.1),
                "max_output_tokens": kwargs.get("max_output_tokens", 2048),
            }
            
            response = self._model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            raise
    
    def generate_with_image(self, prompt: str, image_path: str, **kwargs) -> str:
        """
        多模态：发送图片+文本请求
        
        Args:
            prompt: 输入提示词
            image_path: 图片文件路径
            **kwargs: 可选参数
            
        Returns:
            模型生成的文本
        """
        self._ensure_client()
        
        try:
            import PIL.Image
            
            # 加载图片
            image = PIL.Image.open(image_path)
            
            # 配置生成参数
            generation_config = {
                "temperature": kwargs.get("temperature", 0.1),
                "max_output_tokens": kwargs.get("max_output_tokens", 2048),
            }
            
            # 发送多模态请求
            response = self._model.generate_content(
                [prompt, image],
                generation_config=generation_config
            )
            
            return response.text
            
        except ImportError:
            raise ImportError("请安装 Pillow: pip install Pillow")
        except Exception as e:
            logger.error(f"Gemini 多模态API调用失败: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查Gemini API是否可用"""
        if not self.api_key:
            logger.warning("未配置 GEMINI_API_KEY")
            return False
        try:
            self._ensure_client()
            return True
        except Exception:
            return False
