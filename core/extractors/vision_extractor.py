# -*- coding: utf-8 -*-
"""
视觉提取器

直接使用多模态LLM识别发票图片
"""

import logging
from typing import Optional

from .base import BaseExtractor, InvoiceInfo
from .llm_extractor import LLMInvoiceExtractor
from ..llm.base_adapter import BaseLLMAdapter
from ..llm.factory import get_llm

logger = logging.getLogger(__name__)


class VisionExtractor(BaseExtractor):
    """视觉提取器：直接从图片识别发票信息"""
    
    def __init__(self, adapter: Optional[BaseLLMAdapter] = None):
        """
        初始化视觉提取器
        
        Args:
            adapter: LLM适配器实例（需支持多模态）
        """
        self.adapter = adapter or get_llm()
        self._llm_extractor = LLMInvoiceExtractor(self.adapter)
    
    def extract(self, text: str, file_path: Optional[str] = None) -> InvoiceInfo:
        """
        从文本提取（委托给LLM提取器）
        
        当输入是文本时，使用普通的LLM提取
        """
        return self._llm_extractor.extract(text, file_path)
    
    def extract_from_image(self, image_path: str) -> InvoiceInfo:
        """
        从图片中直接识别发票信息
        
        使用多模态LLM直接分析发票图片，无需OCR预处理
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            提取的发票信息
        """
        logger.info(f"使用视觉提取器处理: {image_path}")
        
        info = self._llm_extractor.extract_from_image(image_path)
        info.提取方式 = "vision"
        
        return info
    
    def extract_from_pdf_image(self, pdf_path: str, page: int = 0) -> InvoiceInfo:
        """
        将PDF页面转换为图片后识别
        
        Args:
            pdf_path: PDF文件路径
            page: 页码（从0开始）
            
        Returns:
            提取的发票信息
        """
        import tempfile
        import os
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("需要安装PyMuPDF: pip install pymupdf")
            return InvoiceInfo(提取方式="vision_error", 原始响应="缺少PyMuPDF依赖")
        
        try:
            # 打开PDF
            doc = fitz.open(pdf_path)
            
            if page >= len(doc):
                logger.error(f"页码超出范围: {page} >= {len(doc)}")
                return InvoiceInfo(提取方式="vision_error")
            
            # 将页面渲染为图片
            page_obj = doc[page]
            mat = fitz.Matrix(2, 2)  # 2x缩放以提高清晰度
            pix = page_obj.get_pixmap(matrix=mat)
            
            # 保存临时图片
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
                pix.save(tmp_path)
            
            # 识别图片
            try:
                info = self.extract_from_image(tmp_path)
            finally:
                # 清理临时文件
                os.unlink(tmp_path)
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"PDF转图片识别失败: {e}")
            return InvoiceInfo(提取方式="vision_error", 原始响应=str(e))
