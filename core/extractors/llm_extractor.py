# -*- coding: utf-8 -*-
"""
LLM发票信息提取器

使用大模型从发票文本中提取结构化信息
"""

import re
import json
import logging
from typing import Optional, Dict, Any

from .base import BaseExtractor, InvoiceInfo
from ..llm.base_adapter import BaseLLMAdapter
from ..llm.factory import get_llm
from ..config.prompts import build_extraction_prompt, build_vision_prompt

logger = logging.getLogger(__name__)


class LLMInvoiceExtractor(BaseExtractor):
    """LLM发票信息提取器"""
    
    def __init__(self, adapter: Optional[BaseLLMAdapter] = None):
        """
        初始化LLM提取器
        
        Args:
            adapter: LLM适配器实例，为None时从配置创建
        """
        self.adapter = adapter or get_llm()
    
    def extract(self, text: str, file_path: Optional[str] = None) -> InvoiceInfo:
        """
        从文本中提取发票信息
        
        Args:
            text: 发票文本内容
            file_path: 原始文件路径
            
        Returns:
            提取的发票信息
        """
        logger.info(f"使用LLM提取发票信息: {file_path or '文本输入'}")
        
        # 构建Prompt
        prompt = build_extraction_prompt(text)
        
        try:
            # 调用LLM
            response = self.adapter.generate(prompt, temperature=0.1)
            
            # 解析响应
            info = self._parse_response(response)
            info.提取方式 = "llm"
            info.原始响应 = response
            info.置信度 = info.get_completeness_score()
            
            logger.info(f"LLM提取完成，完整度: {info.置信度:.2f}")
            return info
            
        except Exception as e:
            logger.error(f"LLM提取失败: {e}")
            return InvoiceInfo(提取方式="llm_failed", 原始响应=str(e))
    
    def extract_from_image(self, image_path: str) -> InvoiceInfo:
        """
        从图片中提取发票信息（多模态）
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            提取的发票信息
        """
        logger.info(f"使用LLM视觉识别: {image_path}")
        
        # 构建视觉Prompt
        prompt = build_vision_prompt()
        
        try:
            # 调用多模态API
            response = self.adapter.generate_with_image(prompt, image_path, temperature=0.1)
            
            # 解析响应
            info = self._parse_response(response)
            info.提取方式 = "llm_vision"
            info.原始响应 = response
            info.置信度 = info.get_completeness_score()
            
            logger.info(f"LLM视觉识别完成，完整度: {info.置信度:.2f}")
            return info
            
        except Exception as e:
            logger.error(f"LLM视觉识别失败: {e}")
            return InvoiceInfo(提取方式="llm_vision_failed", 原始响应=str(e))
    
    def _parse_response(self, response: str) -> InvoiceInfo:
        """
        解析LLM响应，提取JSON数据
        
        Args:
            response: LLM的原始响应文本
            
        Returns:
            解析后的发票信息
        """
        # 尝试提取JSON块
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析整个响应
            json_str = response
        
        # 清理JSON字符串
        json_str = json_str.strip()
        
        # 尝试修复常见的JSON问题
        json_str = self._fix_json(json_str)
        
        try:
            data = json.loads(json_str)
            
            return InvoiceInfo(
                发票号码=self._clean_value(data.get("发票号码")),
                发票类型=self._clean_value(data.get("发票类型")),
                开票日期=self._clean_value(data.get("开票日期")),
                购买方名称=self._clean_value(data.get("购买方名称")),
                购买方纳税人识别号=self._clean_value(data.get("购买方纳税人识别号")),
                销售方名称=self._clean_value(data.get("销售方名称")),
                销售方纳税人识别号=self._clean_value(data.get("销售方纳税人识别号")),
                金额=self._clean_value(data.get("金额") or data.get("金额（不含税）")),
                税额=self._clean_value(data.get("税额")),
                价税合计=self._clean_value(data.get("价税合计")),
                发票内容=self._clean_value(data.get("发票内容") or data.get("发票内容/商品名称")),
                备注=self._clean_value(data.get("备注")),
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            # 尝试使用正则表达式提取关键信息
            return self._fallback_parse(response)
    
    def _fix_json(self, json_str: str) -> str:
        """修复常见的JSON格式问题"""
        # 移除BOM
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
        
        # 处理单引号
        # 注意：这个简单替换可能破坏包含单引号的字符串
        if "'" in json_str and '"' not in json_str:
            json_str = json_str.replace("'", '"')
        
        # 移除尾部逗号
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        return json_str
    
    def _clean_value(self, value: Any) -> Optional[str]:
        """清理提取的值"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ("null", "none", "n/a", ""):
                return None
            return value
        return str(value)
    
    def _fallback_parse(self, response: str) -> InvoiceInfo:
        """
        备用解析方法：使用正则表达式从响应中提取信息
        """
        logger.info("使用备用正则解析")
        
        def extract_field(pattern: str, text: str) -> Optional[str]:
            match = re.search(pattern, text)
            return match.group(1).strip() if match else None
        
        return InvoiceInfo(
            发票号码=extract_field(r'"发票号码"[：:]\s*"?([^",\n]+)"?', response),
            购买方名称=extract_field(r'"购买方名称"[：:]\s*"([^"]+)"', response),
            销售方名称=extract_field(r'"销售方名称"[：:]\s*"([^"]+)"', response),
            购买方纳税人识别号=extract_field(r'"购买方纳税人识别号"[：:]\s*"?([A-Za-z0-9]+)"?', response),
            销售方纳税人识别号=extract_field(r'"销售方纳税人识别号"[：:]\s*"?([A-Za-z0-9]+)"?', response),
            价税合计=extract_field(r'"价税合计"[：:]\s*"?([0-9.]+)"?', response),
            发票类型=extract_field(r'"发票类型"[：:]\s*"([^"]+)"', response),
        )
