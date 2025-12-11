# -*- coding: utf-8 -*-
"""
Ollama 本地模型适配器

支持通过 Ollama 运行本地大模型
"""

import os
import base64
import logging
import requests
from typing import Optional

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class OllamaAdapter(BaseLLMAdapter):
    """Ollama 本地模型适配器"""
    
    def __init__(
        self, 
        model_name: str = "qwen2.5:7b", 
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        super().__init__(model_name, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.timeout = kwargs.get("timeout", 120)  # 本地模型可能较慢
        
    def generate(self, prompt: str, **kwargs) -> str:
        """
        发送文本请求到Ollama
        
        Args:
            prompt: 输入提示词
            **kwargs: 可选参数
                - temperature: 生成温度
                - num_predict: 最大生成token数
                
        Returns:
            模型生成的文本
        """
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.1),
                    "num_predict": kwargs.get("num_predict", 2048),
                }
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"无法连接到Ollama服务: {self.base_url}")
            raise ConnectionError(f"Ollama服务未运行，请启动: ollama serve")
        except Exception as e:
            logger.error(f"Ollama API调用失败: {e}")
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
        try:
            url = f"{self.base_url}/api/generate"
            
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
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "images": [image_data],
                "options": {
                    "temperature": kwargs.get("temperature", 0.1),
                    "num_predict": kwargs.get("num_predict", 2048),
                }
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Ollama 多模态API调用失败: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.ok:
                # 检查模型是否已下载
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if self.model_name in model_names or self.model_name.split(":")[0] in [m.split(":")[0] for m in model_names]:
                    return True
                logger.warning(f"模型 {self.model_name} 未下载，请运行: ollama pull {self.model_name}")
                return False
            return False
        except Exception:
            return False
    
    def list_models(self) -> list:
        """列出Ollama中可用的模型"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.ok:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
            return []
        except Exception:
            return []
