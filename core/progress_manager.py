# -*- coding: utf-8 -*-
"""
发票管理系统 V2 - 进度管理器

支持断点续传功能，记录处理进度并支持恢复
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


class ProgressManager:
    """
    进度管理器
    
    负责保存和加载处理进度，支持断点续传功能
    """
    
    PROGRESS_FILENAME = ".processing_progress.json"
    
    def __init__(self, output_folder: str):
        """
        初始化进度管理器
        
        Args:
            output_folder: 输出文件夹路径（进度文件将保存在此处）
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.output_folder / self.PROGRESS_FILENAME
        
        # 进度状态
        self._state: Dict[str, Any] = {
            "source_folder": "",
            "output_folder": str(self.output_folder),
            "total_files": 0,
            "processed_files": [],  # 已成功处理的文件路径列表
            "failed_files": [],     # 处理失败的文件路径列表
            "start_time": None,
            "last_update": None,
            "completed": False,
            "settings": {}
        }
        
        # 用于快速查找的集合
        self._processed_set: Set[str] = set()
        self._failed_set: Set[str] = set()
    
    @property
    def processed_count(self) -> int:
        """已处理的文件数量"""
        return len(self._processed_set)
    
    @property
    def failed_count(self) -> int:
        """失败的文件数量"""
        return len(self._failed_set)
    
    @property
    def total_files(self) -> int:
        """总文件数"""
        return self._state.get("total_files", 0)
    
    def has_existing_progress(self) -> bool:
        """检查是否存在未完成的进度"""
        if not self.progress_file.exists():
            return False
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            return not state.get("completed", True)
        except Exception:
            return False
    
    def load_progress(self) -> bool:
        """
        加载现有进度
        
        Returns:
            是否成功加载
        """
        if not self.progress_file.exists():
            logger.info("无现有进度文件，将从头开始处理")
            return False
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                self._state = json.load(f)
            
            # 重建查找集合
            self._processed_set = set(self._state.get("processed_files", []))
            self._failed_set = set(self._state.get("failed_files", []))
            
            logger.info(f"已加载进度: {self.processed_count}/{self.total_files} 文件已处理")
            return True
            
        except Exception as e:
            logger.error(f"加载进度文件失败: {e}")
            return False
    
    def init_new_progress(
        self,
        source_folder: str,
        total_files: int,
        settings: Optional[Dict[str, Any]] = None
    ):
        """
        初始化新的处理进度
        
        Args:
            source_folder: 源文件夹路径
            total_files: 待处理的总文件数
            settings: 处理设置（可选）
        """
        self._state = {
            "source_folder": source_folder,
            "output_folder": str(self.output_folder),
            "total_files": total_files,
            "processed_files": [],
            "failed_files": [],
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "completed": False,
            "settings": settings or {}
        }
        
        self._processed_set = set()
        self._failed_set = set()
        
        self._save()
        logger.info(f"初始化新进度: 共 {total_files} 个文件待处理")
    
    def is_processed(self, file_path: str) -> bool:
        """
        检查文件是否已处理
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否已处理
        """
        normalized = self._normalize_path(file_path)
        return normalized in self._processed_set
    
    def add_processed(self, file_path: str, success: bool = True):
        """
        添加已处理的文件
        
        Args:
            file_path: 文件路径
            success: 是否处理成功
        """
        normalized = self._normalize_path(file_path)
        
        if success:
            if normalized not in self._processed_set:
                self._processed_set.add(normalized)
                self._state["processed_files"].append(normalized)
        else:
            if normalized not in self._failed_set:
                self._failed_set.add(normalized)
                self._state["failed_files"].append(normalized)
        
        self._state["last_update"] = datetime.now().isoformat()
        self._save()
    
    def mark_completed(self):
        """标记处理完成"""
        self._state["completed"] = True
        self._state["last_update"] = datetime.now().isoformat()
        self._save()
        logger.info("处理已完成，进度已保存")
    
    def clear_progress(self):
        """清除进度文件"""
        if self.progress_file.exists():
            try:
                self.progress_file.unlink()
                logger.info("进度文件已清除")
            except Exception as e:
                logger.warning(f"清除进度文件失败: {e}")
    
    def get_pending_files(self, all_files: List[str]) -> List[str]:
        """
        获取待处理的文件列表（过滤掉已处理的）
        
        Args:
            all_files: 所有文件列表
            
        Returns:
            待处理的文件列表
        """
        pending = []
        for file_path in all_files:
            normalized = self._normalize_path(file_path)
            if normalized not in self._processed_set:
                pending.append(file_path)
        
        skipped = len(all_files) - len(pending)
        if skipped > 0:
            logger.info(f"跳过 {skipped} 个已处理的文件，剩余 {len(pending)} 个待处理")
        
        return pending
    
    def get_progress_info(self) -> Dict[str, Any]:
        """获取当前进度信息"""
        return {
            "total": self.total_files,
            "processed": self.processed_count,
            "failed": self.failed_count,
            "remaining": max(0, self.total_files - self.processed_count - self.failed_count),
            "completed": self._state.get("completed", False),
            "start_time": self._state.get("start_time"),
            "last_update": self._state.get("last_update")
        }
    
    def _normalize_path(self, file_path: str) -> str:
        """标准化文件路径用于比较"""
        return os.path.normpath(os.path.abspath(file_path)).replace('\\', '/')
    
    def _save(self):
        """保存进度到文件"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
