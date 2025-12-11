# -*- coding: utf-8 -*-
"""
发票处理主入口

整合文件处理、LLM提取、报告生成等功能
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.config.settings import EXTRACTION_MODE, OUTPUT_DIR
from core.extractors import get_extractor, InvoiceInfo
from core.llm import get_llm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InvoiceProcessor:
    """发票处理器 V2"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.ofd', '.jpg', '.jpeg', '.png', '.bmp', '.xml'}
    
    def __init__(
        self, 
        extraction_mode: str = None, 
        llm_provider: str = None, 
        llm_model: str = None,
        ollama_base_url: str = None
    ):
        """
        初始化发票处理器
        
        Args:
            extraction_mode: 提取模式 (llm/hybrid/vision/regex_fallback)
            llm_provider: LLM提供商 (gemini/openai/ollama)
            llm_model: 模型名称 (可选，为空时使用默认值)
            ollama_base_url: Ollama服务器地址 (可选)
        """
        self.extraction_mode = extraction_mode or EXTRACTION_MODE
        
        # 初始化LLM适配器
        try:
            if llm_provider:
                # 传递额外参数给Ollama适配器
                extra_kwargs = {}
                if llm_provider == "ollama" and ollama_base_url:
                    extra_kwargs['base_url'] = ollama_base_url
                self.adapter = get_llm(provider=llm_provider, model_name=llm_model, **extra_kwargs)
            else:
                self.adapter = get_llm()
            logger.info(f"LLM适配器初始化成功: {self.adapter.model_name}")
        except Exception as e:
            logger.warning(f"LLM适配器初始化失败，使用正则兜底模式: {e}")
            self.adapter = None
            self.extraction_mode = "regex_fallback"
        
        # 初始化提取器
        self.extractor = get_extractor(self.extraction_mode, self.adapter)
        logger.info(f"提取器初始化完成，模式: {self.extraction_mode}")
    
    # 预过滤配置
    MAX_FILE_SIZE_MB = 5  # 最大文件大小（MB）
    INVOICE_KEYWORDS = {'发票', '税号', '纳税人识别号', '价税合计', '税额', '开票日期', '发票代码', '发票号码'}
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理单个发票文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理结果字典
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"success": False, "error": f"文件不存在: {file_path}"}
        
        ext = file_path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return {"success": False, "error": f"不支持的文件格式: {ext}"}
        
        # 预过滤1: 文件大小检查
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            logger.info(f"跳过大文件 ({file_size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB): {file_path.name}")
            return {"success": False, "error": f"文件过大 ({file_size_mb:.1f}MB)，跳过处理", "skipped": True}
        
        logger.info(f"处理文件: {file_path}")
        
        try:
            # 根据文件类型选择处理方式
            if ext in {'.jpg', '.jpeg', '.png', '.bmp'}:
                # 图片发票：直接使用视觉识别
                info = self.extractor.extract_from_image(str(file_path))
            else:
                # PDF/OFD/XML：先提取文本
                text = self._extract_text(str(file_path))
                if not text:
                    return {"success": False, "error": "无法提取文本内容"}
                
                # 预过滤2: 关键词检测（仅对文本类文件）
                if not self._is_likely_invoice(text):
                    logger.info(f"跳过非发票文件（未检测到发票关键词）: {file_path.name}")
                    return {"success": False, "error": "未检测到发票关键词，跳过处理", "skipped": True}
                
                info = self.extractor.extract(text, str(file_path))
            
            return {
                "success": True,
                "file_path": str(file_path),
                "info": info.to_dict(),
                "confidence": info.置信度,
                "extraction_mode": info.提取方式,
            }
            
        except Exception as e:
            logger.error(f"处理文件失败: {file_path}, 错误: {e}")
            return {"success": False, "error": str(e)}
    
    def _is_likely_invoice(self, text: str) -> bool:
        """
        检测文本是否可能是发票内容
        
        Args:
            text: 提取的文本内容
            
        Returns:
            是否包含发票关键词
        """
        if not text:
            return False
        
        # 检查是否包含至少2个发票关键词
        found_keywords = sum(1 for keyword in self.INVOICE_KEYWORDS if keyword in text)
        return found_keywords >= 2
    
    def process_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        处理文件夹中的所有发票文件
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            所有处理结果的列表
        """
        folder = Path(folder_path)
        if not folder.is_dir():
            logger.error(f"路径不是文件夹: {folder_path}")
            return []
        
        results = []
        files = self._collect_files(folder)
        
        logger.info(f"发现 {len(files)} 个文件待处理")
        
        for i, file_path in enumerate(files, 1):
            logger.info(f"处理进度: {i}/{len(files)}")
            result = self.process_file(str(file_path))
            results.append(result)
        
        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"处理完成: 成功 {success_count}/{len(results)}")
        
        return results
    
    def _collect_files(self, folder: Path) -> List[Path]:
        """递归收集文件夹及子文件夹中的发票文件"""
        files = []
        
        # 使用os.walk递归遍历所有子文件夹
        try:
            for root, dirs, filenames in os.walk(folder):
                # 跳过"已处理"文件夹，避免重复处理
                dirs[:] = [d for d in dirs if d != "已处理"]
                
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in self.SUPPORTED_EXTENSIONS:
                        full_path = Path(root) / filename
                        files.append(full_path)
                        # 显示相对路径
                        rel_path = full_path.relative_to(folder) if full_path.is_relative_to(folder) else full_path
                        logger.info(f"找到文件: {rel_path}")
        except Exception as e:
            logger.error(f"读取文件夹失败: {e}")
        
        logger.info(f"共找到 {len(files)} 个支持的文件（包含子文件夹）")
        return sorted(files)
    
    def _extract_text(self, file_path: str) -> Optional[str]:
        """
        从文件中提取文本内容
        
        支持PDF、OFD、XML格式
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return self._extract_text_from_pdf(file_path)
        elif ext == '.ofd':
            return self._extract_text_from_ofd(file_path)
        elif ext == '.xml':
            return self._extract_text_from_xml(file_path)
        else:
            return None
    
    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """从PDF提取文本"""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                texts = []
                for page in pdf.pages[:5]:  # 最多处理5页
                    text = page.extract_text()
                    if text:
                        texts.append(text)
                return "\n".join(texts)
        except ImportError:
            logger.error("需要安装pdfplumber: pip install pdfplumber")
            return None
        except Exception as e:
            logger.error(f"PDF文本提取失败: {e}")
            return None
    
    def _extract_text_from_ofd(self, file_path: str) -> Optional[str]:
        """从OFD提取文本"""
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            
            with zipfile.ZipFile(file_path, 'r') as zf:
                texts = []
                for name in zf.namelist():
                    if name.endswith('.xml'):
                        content = zf.read(name).decode('utf-8', errors='ignore')
                        # 简单提取XML中的文本内容
                        try:
                            root = ET.fromstring(content)
                            for elem in root.iter():
                                if elem.text and elem.text.strip():
                                    texts.append(elem.text.strip())
                        except ET.ParseError:
                            pass
                return "\n".join(texts)
        except Exception as e:
            logger.error(f"OFD文本提取失败: {e}")
            return None
    
    def _extract_text_from_xml(self, file_path: str) -> Optional[str]:
        """从XML提取文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import xml.etree.ElementTree as ET
            texts = []
            try:
                root = ET.fromstring(content)
                for elem in root.iter():
                    if elem.text and elem.text.strip():
                        texts.append(elem.text.strip())
            except ET.ParseError:
                # 如果XML解析失败，返回原始内容
                return content
            
            return "\n".join(texts)
        except Exception as e:
            logger.error(f"XML文本提取失败: {e}")
            return None


def process_invoices(
    source_folder: str,
    output_folder: str = None,
    extraction_mode: str = None,
    llm_provider: str = None,
    llm_model: str = None,
    generate_report: bool = True,
    classify_files: bool = True,
    max_workers: int = 1,
    ollama_base_url: str = None,
    batch_size: int = 10,
    resume: bool = False,
    progress_callback: callable = None,
    file_lock_callback: callable = None
) -> Dict[str, Any]:
    """
    便捷函数：处理发票并生成报告
    
    Args:
        source_folder: 源文件夹路径
        output_folder: 输出文件夹路径（可选，默认在源文件夹下创建"已处理"）
        extraction_mode: 提取模式
        llm_provider: LLM提供商
        llm_model: LLM模型名称
        generate_report: 是否生成Excel报告
        classify_files: 是否按销方分类复制文件
        max_workers: 最大并行线程数（默认1，即单线程）
        ollama_base_url: Ollama服务器地址（可选）
        batch_size: 批处理大小，每处理N个文件后写入Excel（默认10）
        resume: 是否继续上次未完成的进度（默认False）
        progress_callback: 进度回调函数 callback(current, total, message)
        file_lock_callback: 文件锁定回调函数 callback(message) -> bool，返回False取消等待
        
    Returns:
        处理结果汇总
    """
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from report_generator import (
        generate_excel_report, 
        classify_and_copy_files,
        generate_stats_report
    )
    from core.progress_manager import ProgressManager
    
    start_time = datetime.now()
    
    # 设置输出文件夹
    if not output_folder:
        output_folder = os.path.join(source_folder, "已处理")
    
    # 初始化进度管理器
    progress_mgr = ProgressManager(output_folder)
    
    # 创建处理器
    processor = InvoiceProcessor(extraction_mode, llm_provider, llm_model, ollama_base_url)
    
    # 收集所有文件
    folder = Path(source_folder)
    all_files = processor._collect_files(folder)
    all_files_str = [str(f) for f in all_files]
    
    # 处理断点续传
    if resume and progress_mgr.has_existing_progress():
        progress_mgr.load_progress()
        files_to_process = progress_mgr.get_pending_files(all_files_str)
        logger.info(f"继续上次进度: 已处理 {progress_mgr.processed_count}, 待处理 {len(files_to_process)}")
    else:
        # 初始化新进度
        files_to_process = all_files_str
        progress_mgr.init_new_progress(
            source_folder=source_folder,
            total_files=len(files_to_process),
            settings={
                "extraction_mode": extraction_mode,
                "llm_provider": llm_provider,
                "batch_size": batch_size
            }
        )
    
    if not files_to_process:
        logger.info("没有待处理的文件")
        progress_mgr.mark_completed()
        return {
            "results": [],
            "stats": generate_stats_report(start_time, datetime.now(), 0, 0),
            "classify_result": None,
            "report_result": None,
            "output_folder": output_folder
        }
    
    # 所有结果（用于最终统计）
    all_results = []
    total_files = len(files_to_process)
    excel_path = os.path.join(output_folder, "发票汇总报告.xlsx")
    
    # 批量处理文件
    def process_batch(batch_files: List[str]) -> List[Dict[str, Any]]:
        """处理一批文件"""
        batch_results = []
        
        if max_workers > 1 and len(batch_files) > 1:
            # 多线程处理批次
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(processor.process_file, f): f 
                    for f in batch_files
                }
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        batch_results.append(result)
                        # 记录进度
                        progress_mgr.add_processed(file_path, result.get("success", False))
                    except Exception as e:
                        logger.error(f"处理失败 {file_path}: {e}")
                        batch_results.append({"file_path": file_path, "success": False, "error": str(e)})
                        progress_mgr.add_processed(file_path, False)
        else:
            # 单线程处理
            for file_path in batch_files:
                try:
                    result = processor.process_file(file_path)
                    batch_results.append(result)
                    progress_mgr.add_processed(file_path, result.get("success", False))
                except Exception as e:
                    logger.error(f"处理失败 {file_path}: {e}")
                    batch_results.append({"file_path": file_path, "success": False, "error": str(e)})
                    progress_mgr.add_processed(file_path, False)
        
        return batch_results
    
    # 分批处理
    processed_count = 0
    batch_classify_total = {"success": 0, "failed": 0, "folders_created": 0}
    
    for batch_start in range(0, total_files, batch_size):
        batch_end = min(batch_start + batch_size, total_files)
        batch_files = files_to_process[batch_start:batch_end]
        batch_num = batch_start // batch_size + 1
        total_batches = (total_files + batch_size - 1) // batch_size
        
        logger.info(f"处理批次 {batch_num}/{total_batches} ({len(batch_files)} 文件)")
        
        # 处理当前批次
        batch_results = process_batch(batch_files)
        all_results.extend(batch_results)
        
        # 统计本批次成功数
        batch_success = sum(1 for r in batch_results if r.get("success"))
        processed_count += len(batch_results)
        
        # 进度回调
        if progress_callback:
            try:
                progress_callback(
                    processed_count, 
                    total_files, 
                    f"批次 {batch_num}/{total_batches} 完成"
                )
            except Exception:
                pass
        
        # 批次结束后立即写入Excel和复制文件
        if batch_success > 0:
            # 分类复制文件
            if classify_files:
                classify_result = classify_and_copy_files(batch_results, output_folder)
                batch_classify_total["success"] += classify_result.get("success", 0)
                batch_classify_total["failed"] += classify_result.get("failed", 0)
                batch_classify_total["folders_created"] += classify_result.get("folders_created", 0)
                logger.info(f"批次 {batch_num}: 复制 {classify_result['success']} 个文件")
            
            # 追加写入Excel
            if generate_report:
                report_result = generate_excel_report(
                    batch_results, 
                    excel_path, 
                    append=True,
                    file_lock_callback=file_lock_callback
                )
                if report_result['success']:
                    logger.info(f"批次 {batch_num}: 写入Excel {report_result['record_count']} 条")
                else:
                    logger.warning(f"批次 {batch_num}: Excel写入失败 - {report_result.get('error')}")
        
        logger.info(f"进度: {processed_count}/{total_files} ({processed_count/total_files*100:.1f}%)")
    
    # 处理完成，标记进度
    progress_mgr.mark_completed()
    
    # 统计
    success_count = sum(1 for r in all_results if r.get("success"))
    failed_count = len(all_results) - success_count
    
    end_time = datetime.now()
    stats = generate_stats_report(start_time, end_time, success_count, failed_count)
    
    # 最终报告结果
    final_report_result = None
    if generate_report and os.path.exists(excel_path):
        try:
            import pandas as pd
            df = pd.read_excel(excel_path, engine='openpyxl')
            final_report_result = {"success": True, "record_count": len(df)}
        except Exception:
            final_report_result = {"success": True, "record_count": success_count}
    
    return {
        "results": all_results,
        "stats": stats,
        "classify_result": batch_classify_total if classify_files else None,
        "report_result": final_report_result,
        "output_folder": output_folder
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python main_processor.py <发票文件夹路径>")
        sys.exit(1)
    
    folder = sys.argv[1]
    results = process_invoices(folder)
    
    print(f"\n处理完成，共 {len(results)} 个文件")
    for r in results:
        if r.get("success"):
            info = r.get("info", {})
            print(f"✓ {Path(r['file_path']).name}: {info.get('发票号码', '未知')}")
        else:
            print(f"✗ {r.get('error', '未知错误')}")
