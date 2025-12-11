# -*- coding: utf-8 -*-
"""
发票管理系统 V2 - 报告生成器

生成Excel报告和分类保存发票文件
"""

import os
import re
import shutil
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


def _check_file_locked(filepath: str) -> bool:
    """
    检查文件是否被锁定（如被Excel打开）
    
    Args:
        filepath: 文件路径
        
    Returns:
        True表示文件被锁定，False表示可以写入
    """
    if not os.path.exists(filepath):
        return False
    
    try:
        # 尝试以追加模式打开文件
        with open(filepath, 'a'):
            pass
        return False
    except (IOError, PermissionError):
        return True


def _wait_for_file_unlock(
    filepath: str, 
    prompt_callback: Callable[[str], bool] = None,
    check_interval: float = 1.0
) -> bool:
    """
    等待文件解锁
    
    Args:
        filepath: 文件路径
        prompt_callback: 提示用户的回调函数，接收消息返回是否继续等待
        check_interval: 检查间隔（秒）
        
    Returns:
        True表示文件已解锁，False表示用户取消
    """
    filename = os.path.basename(filepath)
    
    while _check_file_locked(filepath):
        if prompt_callback:
            message = f"文件 '{filename}' 正被其他程序占用（可能是Excel）。\n请关闭该文件后点击确定继续。"
            should_continue = prompt_callback(message)
            if not should_continue:
                return False
        else:
            # 没有回调时，等待一段时间后重试
            logger.warning(f"文件被锁定: {filename}，等待 {check_interval} 秒后重试...")
            time.sleep(check_interval)
    
    return True


def normalize_company_name(name: str) -> str:
    """
    标准化公司名称作为文件夹名
    
    Args:
        name: 公司名称
        
    Returns:
        可用于文件夹名的标准化名称
    """
    if not name:
        return "未知销方"
    
    # 移除文件名中不允许的字符
    invalid_chars = r'<>:"/\\|?*'
    cleaned = name
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '')
    
    # 去除多余空格
    cleaned = ' '.join(cleaned.split())
    
    # 限制长度
    if len(cleaned) > 50:
        cleaned = cleaned[:50]
    
    return cleaned.strip() or "未知销方"


def classify_and_copy_files(
    results: List[Dict[str, Any]],
    output_folder: str,
    group_by: str = "销售方名称"
) -> Dict[str, Any]:
    """
    按指定字段分类并复制发票文件
    
    Args:
        results: 处理结果列表
        output_folder: 输出文件夹路径
        group_by: 分组字段（默认按销售方名称）
        
    Returns:
        分类结果统计
    """
    stats = {
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "folders_created": 0,
        "errors": []
    }
    
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 跟踪已处理的发票号码，用于去重
    processed_invoices = set()
    
    for result in results:
        if not result.get("success"):
            continue
        
        try:
            source_file = result.get("file_path")
            if not source_file or not os.path.exists(source_file):
                continue
            
            info = result.get("info", {})
            
            # 验证是否为发票：必须有发票号码
            invoice_no = info.get("发票号码", "")
            if not invoice_no or invoice_no == "None" or len(str(invoice_no).strip()) < 6:
                # 记录图片类型文件的过滤情况
                source_ext = Path(source_file).suffix.lower() if source_file else ""
                if source_ext in {'.jpg', '.jpeg', '.png', '.bmp'}:
                    logger.warning(f"图片识别结果被过滤 [{source_file}]: 发票号码='{invoice_no}', 销售方='{info.get('销售方名称', '')}', 购买方='{info.get('购买方名称', '')}', 提取方式={result.get('extraction_mode', '')}")
                else:
                    logger.debug(f"跳过非发票文件: {source_file}")
                continue
            
            # 检查是否已处理过该发票号码（去重）
            invoice_no_normalized = str(invoice_no).strip()
            if invoice_no_normalized in processed_invoices:
                logger.info(f"跳过重复发票: {invoice_no_normalized}")
                stats["skipped"] += 1
                continue
            
            processed_invoices.add(invoice_no_normalized)
            
            # 获取销售方和购买方名称
            seller_name = info.get("销售方名称", "")
            buyer_name = info.get("购买方名称", "")
            seller_folder = normalize_company_name(seller_name)
            buyer_folder = normalize_company_name(buyer_name) if buyer_name else "未知购买方"
            
            # 创建目标文件夹：销售方/购买方
            target_folder = output_path / seller_folder / buyer_folder
            if not target_folder.exists():
                target_folder.mkdir(parents=True)
                stats["folders_created"] += 1
                logger.info(f"创建文件夹: {seller_folder}/{buyer_folder}")
            
            # 复制文件
            source = Path(source_file)
            target = target_folder / source.name
            
            # 避免覆盖同名文件
            if target.exists():
                stem = target.stem
                suffix = target.suffix
                counter = 1
                while target.exists():
                    target = target_folder / f"{stem}_{counter}{suffix}"
                    counter += 1
            
            shutil.copy2(source_file, target)
            stats["success"] += 1
            logger.info(f"复制文件: {source.name} -> {seller_folder}/{buyer_folder}/")
            
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(str(e))
            logger.error(f"复制文件失败: {e}")
    
    return stats


def generate_excel_report(
    results: List[Dict[str, Any]],
    excel_path: str,
    append: bool = True,
    file_lock_callback: Callable[[str], bool] = None
) -> Dict[str, Any]:
    """
    生成Excel发票汇总报告
    
    Args:
        results: 处理结果列表
        excel_path: Excel文件路径
        append: 是否追加到现有文件
        file_lock_callback: 文件锁定时的回调函数，接收提示消息，返回是否继续等待
        
    Returns:
        生成结果
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("需要安装pandas: pip install pandas openpyxl")
        return {"success": False, "error": "pandas未安装"}
    
    report_result = {
        "success": False,
        "record_count": 0,
        "error": None
    }
    
    try:
        # 提取成功的记录，只包含有效发票
        records = []
        for r in results:
            if not r.get("success"):
                continue
            
            info = r.get("info", {})
            
            # 验证是否为发票：必须有发票号码
            invoice_no = info.get("发票号码", "")
            if not invoice_no or invoice_no == "None" or len(str(invoice_no).strip()) < 6:
                # 记录图片类型文件的过滤情况
                file_path = r.get("file_path", "")
                file_ext = Path(file_path).suffix.lower() if file_path else ""
                if file_ext in {'.jpg', '.jpeg', '.png', '.bmp'}:
                    logger.warning(f"图片识别结果未写入Excel [{file_path}]: 发票号码='{invoice_no}', 销售方='{info.get('销售方名称', '')}', 购买方='{info.get('购买方名称', '')}'")
                continue
            
            record = {
                "文件名": Path(r.get("file_path", "")).name,
                "发票号码": invoice_no,
                "发票代码": info.get("发票代码", ""),
                "发票类型": info.get("发票类型", ""),
                "开票日期": info.get("开票日期", ""),
                "购买方名称": info.get("购买方名称", ""),
                "购买方税号": info.get("购买方纳税人识别号", ""),
                "销售方名称": info.get("销售方名称", ""),
                "销售方税号": info.get("销售方纳税人识别号", ""),
                "金额": info.get("金额", ""),
                "税额": info.get("税额", ""),
                "价税合计": info.get("价税合计", ""),
                "置信度": f"{r.get('confidence', 0):.0%}",
                "提取方式": r.get("extraction_mode", ""),
                "文件路径": r.get("file_path", ""),
            }
            records.append(record)
        
        if not records:
            report_result["error"] = "没有成功识别的发票记录"
            return report_result
        
        # 创建DataFrame
        df = pd.DataFrame(records)
        
        # 清理数据
        df = _clean_excel_data(df)
        
        # 首次去重：当前批次内按发票号码去重
        if '发票号码' in df.columns:
            df = df.drop_duplicates(subset=['发票号码'], keep='first')
        
        # 确保文件扩展名正确
        if not excel_path.endswith('.xlsx'):
            excel_path += '.xlsx'
        
        # 如果追加模式且文件存在，合并数据
        if append and os.path.exists(excel_path):
            try:
                existing_df = pd.read_excel(excel_path, engine='openpyxl')
                existing_df = _clean_excel_data(existing_df)
                df = pd.concat([existing_df, df], ignore_index=True)
                
                # 合并后再次去重
                if '发票号码' in df.columns:
                    df = df.drop_duplicates(subset=['发票号码'], keep='last')
            except Exception as e:
                logger.warning(f"读取现有Excel失败，创建新文件: {e}")
        
        # 写入Excel（检查文件锁定）
        if _check_file_locked(excel_path):
            logger.warning(f"Excel文件被锁定: {excel_path}")
            if not _wait_for_file_unlock(excel_path, file_lock_callback):
                report_result["error"] = "用户取消操作，文件仍被锁定"
                return report_result
        
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        report_result["success"] = True
        report_result["record_count"] = len(df)
        logger.info(f"Excel报告生成成功: {excel_path}, 共 {len(df)} 条记录")
        
    except Exception as e:
        report_result["error"] = str(e)
        logger.error(f"生成Excel报告失败: {e}")
    
    return report_result


def _clean_excel_data(df) -> "pd.DataFrame":
    """清理DataFrame中的数据"""
    import pandas as pd
    
    # 复制避免修改原数据
    cleaned = df.copy()
    
    # 清理文件路径
    if '文件路径' in cleaned.columns:
        cleaned['文件路径'] = cleaned['文件路径'].astype(str)
        cleaned['文件路径'] = cleaned['文件路径'].apply(
            lambda x: x.replace('\\', '/') if pd.notna(x) else x
        )
    
    # 清理非法字符
    for column in cleaned.select_dtypes(include=['object']).columns:
        cleaned[column] = cleaned[column].astype(str)
        cleaned[column] = cleaned[column].apply(
            lambda x: re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', x) if pd.notna(x) else x
        )
    
    return cleaned


def generate_stats_report(
    start_time: datetime,
    end_time: datetime,
    success_count: int,
    failed_count: int,
    skipped_count: int = 0
) -> Dict[str, Any]:
    """
    生成处理统计报告
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        success_count: 成功数量
        failed_count: 失败数量
        skipped_count: 跳过数量
        
    Returns:
        统计信息字典
    """
    total_time = (end_time - start_time).total_seconds()
    total_files = success_count + failed_count + skipped_count
    
    return {
        "total_time": total_time,
        "total_files": total_files,
        "success": success_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "success_rate": (success_count / total_files * 100) if total_files > 0 else 0
    }
