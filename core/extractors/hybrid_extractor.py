# -*- coding: utf-8 -*-
"""
混合提取器

结合LLM和正则表达式的优势，提供更可靠的发票信息提取
"""

import re
import logging
from typing import Optional

from .base import BaseExtractor, InvoiceInfo
from .llm_extractor import LLMInvoiceExtractor
from ..llm.base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class HybridExtractor(BaseExtractor):
    """混合提取器：LLM + 正则验证/兜底"""
    
    def __init__(
        self, 
        text_adapter: Optional[BaseLLMAdapter] = None,
        vision_adapter: Optional[BaseLLMAdapter] = None
    ):
        """
        初始化混合提取器
        
        Args:
            text_adapter: 文本LLM适配器（用于PDF/OFD/XML文本提取）
            vision_adapter: 视觉LLM适配器（用于图片识别）
        """
        self.llm_extractor = LLMInvoiceExtractor(text_adapter, vision_adapter)
        
        # 预编译正则表达式
        self._patterns = {
            'invoice_number_20': re.compile(r'\b(24[4-8]\d{17})\b'),
            'invoice_number_8': re.compile(r'发票号码[：:]\s*(\d{8})'),
            'tax_id': re.compile(r'\b([0-9A-HJ-NPQRTUWXY]{2}[0-9]{6}[0-9A-HJ-NPQRTUWXY]{10})\b'),
            'amount': re.compile(r'[价合][税计][：:￥¥]?\s*(\d+\.?\d*)'),
        }
    
    def extract(self, text: str, file_path: Optional[str] = None) -> InvoiceInfo:
        """
        从文本中提取发票信息（混合策略）
        
        策略：
        1. 首先使用LLM提取
        2. 使用正则表达式验证和补全关键字段
        3. 计算最终置信度
        
        Args:
            text: 发票文本内容
            file_path: 原始文件路径
            
        Returns:
            提取的发票信息
        """
        logger.info(f"使用混合提取器: {file_path or '文本输入'}")
        
        # 步骤1: LLM提取
        info = self.llm_extractor.extract(text, file_path)
        
        # 步骤2: 正则验证和补全
        info = self._validate_and_enhance(info, text)
        
        # 更新提取方式
        info.提取方式 = "hybrid"
        
        logger.info(f"混合提取完成，最终置信度: {info.置信度:.2f}")
        return info
    
    def extract_from_image(self, image_path: str) -> InvoiceInfo:
        """
        从图片中提取发票信息
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            提取的发票信息
        """
        logger.info(f"使用混合提取器处理图片: {image_path}")
        
        # 对于图片，直接使用LLM视觉识别
        info = self.llm_extractor.extract_from_image(image_path)
        info.提取方式 = "hybrid_vision"
        
        return info
    
    def _validate_and_enhance(self, info: InvoiceInfo, text: str) -> InvoiceInfo:
        """
        使用正则表达式验证和增强LLM提取结果
        
        Args:
            info: LLM提取的信息
            text: 原始文本
            
        Returns:
            验证/增强后的信息
        """
        # 验证/补全发票号码
        if not info.发票号码:
            info.发票号码 = self._extract_invoice_number(text)
        elif not self._validate_invoice_number(info.发票号码):
            # LLM提取的发票号码格式不对，尝试正则提取
            regex_number = self._extract_invoice_number(text)
            if regex_number:
                logger.info(f"LLM发票号码格式异常，使用正则结果: {regex_number}")
                info.发票号码 = regex_number
        
        # 验证/补全纳税人识别号
        if not info.购买方纳税人识别号:
            tax_ids = self._extract_tax_ids(text)
            if len(tax_ids) >= 1:
                info.购买方纳税人识别号 = tax_ids[0]
        else:
            if not self._validate_tax_id(info.购买方纳税人识别号):
                info.购买方纳税人识别号 = None
        
        if not info.销售方纳税人识别号:
            tax_ids = self._extract_tax_ids(text)
            if len(tax_ids) >= 2:
                info.销售方纳税人识别号 = tax_ids[1]
        else:
            if not self._validate_tax_id(info.销售方纳税人识别号):
                info.销售方纳税人识别号 = None
        
        # 验证金额格式
        if info.价税合计:
            info.价税合计 = self._clean_amount(info.价税合计)
        if info.金额:
            info.金额 = self._clean_amount(info.金额)
        if info.税额:
            info.税额 = self._clean_amount(info.税额)
        
        # 重新计算置信度
        info.置信度 = info.get_completeness_score()
        
        return info
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """使用正则提取发票号码"""
        # 优先匹配20位电子发票号
        match = self._patterns['invoice_number_20'].search(text)
        if match:
            return match.group(1)
        
        # 匹配8位纸质发票号
        match = self._patterns['invoice_number_8'].search(text)
        if match:
            return match.group(1)
        
        return None
    
    def _validate_invoice_number(self, number: str) -> bool:
        """验证发票号码格式"""
        if not number:
            return False
        # 电子发票：20位数字
        if len(number) == 20 and number.isdigit():
            return True
        # 纸质发票：8位数字
        if len(number) == 8 and number.isdigit():
            return True
        return False
    
    def _extract_tax_ids(self, text: str) -> list:
        """使用正则提取所有纳税人识别号"""
        matches = self._patterns['tax_id'].findall(text)
        # 去重并保持顺序
        seen = set()
        result = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                result.append(m)
        return result
    
    def _validate_tax_id(self, tax_id: str) -> bool:
        """验证纳税人识别号格式"""
        if not tax_id:
            return False
        # 标准格式：18位统一社会信用代码
        if len(tax_id) == 18 and re.match(r'^[0-9A-HJ-NPQRTUWXY]{2}[0-9]{6}[0-9A-HJ-NPQRTUWXY]{10}$', tax_id):
            return True
        # 旧格式：15位纳税人识别号
        if len(tax_id) == 15 and tax_id.isalnum():
            return True
        return False
    
    def _clean_amount(self, amount: str) -> Optional[str]:
        """清理金额字符串"""
        if not amount:
            return None
        # 移除货币符号和空格
        amount = re.sub(r'[￥¥,，\s]', '', str(amount))
        # 验证是否为有效数字
        try:
            float(amount)
            return amount
        except ValueError:
            return None


class RegexFallbackExtractor(BaseExtractor):
    """正则表达式兜底提取器（当LLM不可用时使用）"""
    
    def __init__(self):
        self._patterns = {
            'invoice_number': re.compile(r'发票号码[：:]\s*(\d{8,20})'),
            'purchaser_name': re.compile(r'(购买方|购方|买方)\s*名\s*称[：:]\s*([^\n]+)'),
            'seller_name': re.compile(r'(销售方|销方|卖方)\s*名\s*称[：:]\s*([^\n]+)'),
            'tax_id': re.compile(r'纳税人识别号[：:]\s*([A-Za-z0-9]{15,20})'),
            'amount': re.compile(r'(价税合计|合计)[：:￥¥]?\s*(\d+\.?\d*)'),
        }
    
    def extract(self, text: str, file_path: Optional[str] = None) -> InvoiceInfo:
        """使用正则表达式提取发票信息"""
        logger.info("使用正则兜底提取器")
        
        def find(pattern_key: str, group: int = 1) -> Optional[str]:
            match = self._patterns[pattern_key].search(text)
            return match.group(group).strip() if match else None
        
        # 提取税号（可能有多个）
        tax_ids = self._patterns['tax_id'].findall(text)
        
        info = InvoiceInfo(
            发票号码=find('invoice_number'),
            购买方名称=find('purchaser_name', 2),
            销售方名称=find('seller_name', 2),
            购买方纳税人识别号=tax_ids[0] if len(tax_ids) >= 1 else None,
            销售方纳税人识别号=tax_ids[1] if len(tax_ids) >= 2 else None,
            价税合计=find('amount', 2),
            提取方式="regex_fallback",
        )
        info.置信度 = info.get_completeness_score()
        
        return info
    
    def extract_from_image(self, image_path: str) -> InvoiceInfo:
        """正则提取器不支持直接处理图片"""
        logger.warning("正则兜底提取器不支持图片处理")
        return InvoiceInfo(提取方式="regex_fallback_unsupported")
