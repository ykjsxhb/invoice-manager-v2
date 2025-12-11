# -*- coding: utf-8 -*-
"""
发票信息提取器基类

定义统一的提取器接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class InvoiceInfo:
    """发票信息数据类"""
    发票号码: Optional[str] = None
    发票类型: Optional[str] = None
    开票日期: Optional[str] = None
    购买方名称: Optional[str] = None
    购买方纳税人识别号: Optional[str] = None
    销售方名称: Optional[str] = None
    销售方纳税人识别号: Optional[str] = None
    金额: Optional[str] = None
    税额: Optional[str] = None
    价税合计: Optional[str] = None
    发票内容: Optional[str] = None
    备注: Optional[str] = None
    
    # 元数据
    提取方式: str = "unknown"
    置信度: float = 0.0
    原始响应: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "发票号码": self.发票号码,
            "发票类型": self.发票类型,
            "开票日期": self.开票日期,
            "购买方名称": self.购买方名称,
            "购买方纳税人识别号": self.购买方纳税人识别号,
            "销售方名称": self.销售方名称,
            "销售方纳税人识别号": self.销售方纳税人识别号,
            "金额": self.金额,
            "税额": self.税额,
            "价税合计": self.价税合计,
            "发票内容": self.发票内容,
            "备注": self.备注,
        }
    
    def is_complete(self) -> bool:
        """检查是否提取到了必要字段"""
        return bool(self.发票号码 and self.购买方名称 and self.销售方名称)
    
    def get_completeness_score(self) -> float:
        """计算完整度分数（0-1）"""
        fields = [
            self.发票号码,
            self.发票类型,
            self.开票日期,
            self.购买方名称,
            self.购买方纳税人识别号,
            self.销售方名称,
            self.销售方纳税人识别号,
            self.价税合计,
        ]
        filled = sum(1 for f in fields if f)
        return filled / len(fields)


class BaseExtractor(ABC):
    """发票信息提取器基类"""
    
    @abstractmethod
    def extract(self, text: str, file_path: Optional[str] = None) -> InvoiceInfo:
        """
        从文本中提取发票信息
        
        Args:
            text: 发票文本内容
            file_path: 原始文件路径（可选）
            
        Returns:
            提取的发票信息
        """
        pass
    
    @abstractmethod
    def extract_from_image(self, image_path: str) -> InvoiceInfo:
        """
        从图片中提取发票信息
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            提取的发票信息
        """
        pass
