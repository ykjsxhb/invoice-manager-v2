# -*- coding: utf-8 -*-
"""
发票管理系统 V2 - 测试文件

测试LLM提取器和混合提取器的功能
"""

import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_regex_fallback():
    """测试正则兜底提取器"""
    print("\n[测试] 正则兜底提取器")
    print("-" * 40)
    
    from core.extractors import RegexFallbackExtractor
    
    test_text = """
    增值税电子普通发票
    
    发票号码：24421000123456789012
    
    购买方名称：北京测试科技有限公司
    纳税人识别号：91110000MA1A2B3C4D
    
    销售方名称：上海供应商有限公司
    纳税人识别号：91310000MA5E6F7G8H
    
    价税合计：￥12,345.67
    """
    
    extractor = RegexFallbackExtractor()
    info = extractor.extract(test_text)
    
    print(f"发票号码: {info.发票号码}")
    print(f"购买方名称: {info.购买方名称}")
    print(f"购买方税号: {info.购买方纳税人识别号}")
    print(f"销售方名称: {info.销售方名称}")
    print(f"销售方税号: {info.销售方纳税人识别号}")
    print(f"价税合计: {info.价税合计}")
    print(f"完整度: {info.置信度:.0%}")
    
    # 断言
    assert info.发票号码 == "24421000123456789012", f"发票号码错误: {info.发票号码}"
    print("\n✓ 正则兜底提取器测试通过")


def test_llm_adapters():
    """测试LLM适配器初始化"""
    print("\n[测试] LLM适配器初始化")
    print("-" * 40)
    
    from core.llm import LLMFactory
    
    # 测试Ollama适配器
    try:
        adapter = LLMFactory.create("ollama", "qwen2.5:7b")
        print(f"✓ Ollama适配器创建成功: {adapter.model_name}")
        print(f"  可用性: {adapter.is_available()}")
    except Exception as e:
        print(f"✗ Ollama适配器创建失败: {e}")
    
    # 测试Gemini适配器
    try:
        adapter = LLMFactory.create("gemini")
        print(f"✓ Gemini适配器创建成功: {adapter.model_name}")
        # 不检查可用性，因为可能没有API Key
    except Exception as e:
        print(f"✗ Gemini适配器创建失败: {e}")
    
    print("\n✓ LLM适配器测试完成")


def test_hybrid_extractor_validation():
    """测试混合提取器的验证功能"""
    print("\n[测试] 混合提取器验证功能")
    print("-" * 40)
    
    from core.extractors.hybrid_extractor import HybridExtractor
    
    # 创建一个使用正则兜底的混合提取器（不需要LLM）
    extractor = HybridExtractor.__new__(HybridExtractor)
    extractor._patterns = {
        'invoice_number_20': __import__('re').compile(r'\b(24[4-8]\d{17})\b'),
        'invoice_number_8': __import__('re').compile(r'发票号码[：:]\s*(\d{8})'),
        'tax_id': __import__('re').compile(r'\b([0-9A-HJ-NPQRTUWXY]{2}[0-9]{6}[0-9A-HJ-NPQRTUWXY]{10})\b'),
        'amount': __import__('re').compile(r'[价合][税计][：:￥¥]?\s*(\d+\.?\d*)'),
    }
    
    # 测试发票号码验证
    assert extractor._validate_invoice_number("24421000123456789012") == True
    assert extractor._validate_invoice_number("12345678") == True
    assert extractor._validate_invoice_number("123") == False
    print("✓ 发票号码验证正确")
    
    # 测试税号验证
    assert extractor._validate_tax_id("91110000MA1A2B3C4D") == True
    assert extractor._validate_tax_id("123456789012345") == True  # 15位
    assert extractor._validate_tax_id("12345") == False
    print("✓ 税号验证正确")
    
    # 测试金额清理
    assert extractor._clean_amount("￥1,234.56") == "1234.56"
    assert extractor._clean_amount("¥ 999.00") == "999.00"
    print("✓ 金额清理正确")
    
    print("\n✓ 混合提取器验证测试通过")


def test_invoice_info_dataclass():
    """测试InvoiceInfo数据类"""
    print("\n[测试] InvoiceInfo数据类")
    print("-" * 40)
    
    from core.extractors import InvoiceInfo
    
    # 创建完整的发票信息
    info = InvoiceInfo(
        发票号码="24421000123456789012",
        发票类型="增值税电子普通发票",
        开票日期="2024-01-15",
        购买方名称="测试公司",
        购买方纳税人识别号="91110000MA1A2B3C4D",
        销售方名称="供应商公司",
        销售方纳税人识别号="91310000MA5E6F7G8H",
        价税合计="1234.56",
    )
    
    print(f"完整度分数: {info.get_completeness_score():.2f}")
    print(f"是否完整: {info.is_complete()}")
    
    # 转换为字典
    d = info.to_dict()
    print(f"字典字段数: {len(d)}")
    
    assert info.is_complete() == True
    assert info.get_completeness_score() == 1.0
    
    # 测试不完整的发票
    incomplete = InvoiceInfo(发票号码="12345678")
    assert incomplete.is_complete() == False
    print(f"不完整发票完整度: {incomplete.get_completeness_score():.2f}")
    
    print("\n✓ InvoiceInfo数据类测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("发票管理系统 V2 - 单元测试")
    print("=" * 50)
    
    try:
        test_invoice_info_dataclass()
        test_regex_fallback()
        test_llm_adapters()
        test_hybrid_extractor_validation()
        
        print("\n" + "=" * 50)
        print("所有测试通过! ✓")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
