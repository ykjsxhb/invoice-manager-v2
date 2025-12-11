# -*- coding: utf-8 -*-
"""
发票管理系统 V2 - 主入口

使用大模型进行智能发票识别
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="发票管理系统 V2 - 大模型智能识别",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 启动GUI界面
  python main.py --cli <文件夹>      # 命令行处理
  python main.py --test             # 运行测试

提取模式:
  hybrid        混合模式（推荐）：LLM + 正则验证
  llm           纯LLM模式
  vision        视觉识别模式（适合图片发票）
  regex_fallback 正则兜底模式（无需API）

LLM提供商:
  gemini        Google Gemini（推荐）
  openai        OpenAI GPT
  ollama        Ollama本地模型
        """
    )
    
    parser.add_argument(
        "--cli", 
        metavar="PATH",
        help="命令行模式：指定要处理的文件夹路径"
    )
    parser.add_argument(
        "--mode",
        choices=["hybrid", "llm", "vision", "regex_fallback"],
        default="hybrid",
        help="提取模式（默认: hybrid）"
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "openai", "ollama"],
        default=None,
        help="LLM提供商（默认从配置读取）"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="运行测试"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查LLM可用性"
    )
    
    args = parser.parse_args()
    
    if args.check:
        # 检查LLM可用性
        check_llm_availability()
        return
    
    if args.test:
        # 运行测试
        run_tests()
        return
    
    if args.cli:
        # 命令行模式
        run_cli(args.cli, args.mode, args.provider)
        return
    
    # 默认启动GUI
    run_gui()


def check_llm_availability():
    """检查LLM可用性"""
    print("检查LLM可用性...\n")
    
    from core.llm import LLMFactory
    
    providers = ["gemini", "openai", "ollama"]
    
    for provider in providers:
        try:
            adapter = LLMFactory.create(provider)
            available = adapter.is_available()
            status = "✓ 可用" if available else "✗ 不可用"
            print(f"  {provider.upper():10} {status} ({adapter.model_name})")
        except Exception as e:
            print(f"  {provider.upper():10} ✗ 错误: {e}")
    
    print()


def run_cli(folder: str, mode: str, provider: str):
    """命令行处理模式"""
    from main_processor import process_invoices
    from pathlib import Path
    
    print(f"发票管理系统 V2 - 命令行模式")
    print(f"文件夹: {folder}")
    print(f"提取模式: {mode}")
    print(f"LLM提供商: {provider or '默认'}")
    print("-" * 40)
    
    results = process_invoices(folder, extraction_mode=mode, llm_provider=provider)
    
    print(f"\n处理完成，共 {len(results)} 个文件")
    
    success_count = 0
    for r in results:
        if r.get("success"):
            success_count += 1
            info = r.get("info", {})
            filename = Path(r['file_path']).name
            invoice_num = info.get('发票号码', '未识别')
            confidence = r.get('confidence', 0)
            print(f"✓ {filename}: {invoice_num} (置信度: {confidence:.0%})")
        else:
            print(f"✗ 失败: {r.get('error', '未知错误')}")
    
    print(f"\n成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")


def run_tests():
    """运行测试"""
    print("运行测试...\n")
    
    # 测试1: LLM适配器
    print("[测试1] LLM适配器初始化")
    try:
        from core.llm import get_llm
        adapter = get_llm("ollama", "qwen2.5:7b")
        print(f"  ✓ Ollama适配器创建成功: {adapter.model_name}")
    except Exception as e:
        print(f"  ✗ 创建失败: {e}")
    
    # 测试2: 提取器
    print("\n[测试2] 提取器初始化")
    try:
        from core.extractors import get_extractor
        extractor = get_extractor("regex_fallback")
        print(f"  ✓ 正则兜底提取器创建成功")
    except Exception as e:
        print(f"  ✗ 创建失败: {e}")
    
    # 测试3: 正则提取
    print("\n[测试3] 正则提取测试")
    test_text = """
    增值税电子普通发票
    发票号码：24421000123456789012
    购买方名称：测试公司
    纳税人识别号：91310000MA1A2B3C4D
    销售方名称：供应商公司
    纳税人识别号：91310000MA5E6F7G8H
    价税合计：￥1234.56
    """
    try:
        from core.extractors import RegexFallbackExtractor
        extractor = RegexFallbackExtractor()
        info = extractor.extract(test_text)
        print(f"  ✓ 发票号码: {info.发票号码}")
        print(f"  ✓ 购买方: {info.购买方名称}")
        print(f"  ✓ 销售方: {info.销售方名称}")
    except Exception as e:
        print(f"  ✗ 提取失败: {e}")
    
    print("\n测试完成!")


def run_gui():
    """启动GUI界面"""
    try:
        from gui import InvoiceGUI
        app = InvoiceGUI()
        app.run()
    except ImportError as e:
        print(f"GUI模块导入失败: {e}")
        print("请确保已安装tkinter")
    except Exception as e:
        print(f"GUI启动失败: {e}")


if __name__ == "__main__":
    main()
