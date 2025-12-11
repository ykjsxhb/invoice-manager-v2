# -*- coding: utf-8 -*-
"""
发票管理系统 V2 - 配置模块

支持多种大模型提供商的配置
自动从 .env 文件加载环境变量
"""

import os
from pathlib import Path
from typing import Optional

# 自动加载 .env 文件
def _load_dotenv():
    """加载 .env 文件中的环境变量"""
    # 查找项目根目录的 .env 文件
    env_paths = [
        Path(__file__).parent.parent.parent / ".env",  # 项目根目录
        Path.cwd() / ".env",  # 当前工作目录
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # 跳过注释和空行
                        if not line or line.startswith('#'):
                            continue
                        # 解析 KEY=VALUE
                        if '=' in line:
                            key, _, value = line.partition('=')
                            key = key.strip()
                            value = value.strip()
                            # 不覆盖已存在的环境变量
                            if key and key not in os.environ:
                                os.environ[key] = value
                print(f"已加载配置文件: {env_path}")
                return True
            except Exception as e:
                print(f"加载 .env 失败: {e}")
    return False

# 在模块导入时自动加载
_load_dotenv()

# ===========================================
# LLM 配置
# ===========================================

# LLM提供商: gemini / openai / ollama
LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "gemini")

# 模型名称
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gemini-2.5-flash")

# API Keys
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "")

# API超时设置（秒）
LLM_TIMEOUT: int = 30

# 最大重试次数
LLM_MAX_RETRIES: int = 3

# ===========================================
# Ollama 本地模型配置
# ===========================================

OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

# ===========================================
# DeepSeek 配置
# ===========================================

DEEPSEEK_BASE_URL: str = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# ===========================================
# 提取模式配置
# ===========================================

# 提取模式: llm / vision / hybrid / regex_fallback
EXTRACTION_MODE: str = os.environ.get("EXTRACTION_MODE", "hybrid")

# 启用正则表达式兜底验证
ENABLE_REGEX_VALIDATION: bool = True

# ===========================================
# 文件处理配置 (继承自V1)
# ===========================================

MAX_FILE_SIZE_KB: int = 300
MAX_IMAGE_SIZE_KB: int = 10240
MAX_PAGES_TO_CHECK: int = 5
MAX_TEXT_LENGTH: int = 10000

# ===========================================
# 输出配置
# ===========================================

# 日志级别
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

# 输出目录
OUTPUT_DIR: str = "output"
