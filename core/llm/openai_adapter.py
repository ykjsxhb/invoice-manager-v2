# -*- coding: utf-8 -*-
"""
OpenAI API 适配器

支持 OpenAI GPT 模型的文本和多模态调用
"""

import os
import base64
import logging
from typing import Optional

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI API 适配器"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None, **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._client = None
        
    def _ensure_client(self):
        """确保客户端已初始化"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                logger.info(f"OpenAI客户端初始化成功，模型：{self.model_name}")
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
            except Exception as e:
                logger.error(f"OpenAI客户端初始化失败: {e}")
                raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        发送文本请求
        
        Args:
            prompt: 输入提示词
            **kwargs: 可选参数
            
        Returns:
            模型生成的文本
        """
        self._ensure_client()
        
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    def generate_with_image(self, prompt: str, image_path: str, **kwargs) -> str:
        """
        多模态：发送图片+文本请求（GPT-4V）
        
        Args:
            prompt: 输入提示词
            image_path: 图片文件路径
            **kwargs: 可选参数
            
        Returns:
            模型生成的文本
        """
        self._ensure_client()
        
        try:
            # 读取并编码图片
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # 确定图片MIME类型
            ext = os.path.splitext(image_path)[1].lower()
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_types.get(ext, "image/jpeg")
            
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI 多模态API调用失败: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查OpenAI API是否可用"""
        if not self.api_key:
            logger.warning("未配置 OPENAI_API_KEY")
            return False
        try:
            self._ensure_client()
            return True
        except Exception:
            return False
