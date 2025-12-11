# 发票管理系统 V2 - 大模型智能识别

> 基于大语言模型（LLM）的智能发票信息提取与整理系统

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

---

## 🎯 系统简介

这是一个基于大模型（LLM）的智能发票管理系统，支持自动识别、提取、分类发票信息，并生成 Excel 汇总报告。

### ✨ 核心功能

- **🤖 大模型识别**：使用 Gemini/GPT/Ollama 等大模型智能提取发票信息
- **🔀 混合提取模式**：LLM + 正则验证，兼顾准确性和可靠性
- **👁️ 多模态视觉识别**：直接从发票图片识别，无需 OCR 预处理
- **🔌 多模型支持**：支持 Gemini、OpenAI、Ollama 本地/远程模型
- **� 智能分类**：自动按 `销售方/购买方` 创建文件夹结构整理发票
- **�📊 Excel 报告**：自动生成发票汇总 Excel 表格
- **⚡ 多线程处理**：支持并行处理，大幅提升效率
- **💾 断点续传**：中断后可继续上次进度
- **🌐 远程调用**：支持远程调用 Ollama 服务器

### 📝 支持格式

| 格式 | 说明 |
|------|------|
| PDF | 标准电子发票 PDF |
| OFD | 国家标准版式文件 |
| 图片 | PNG/JPG/JPEG 扫描件 |
| XML | 电子发票数据文件 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/invoice-manager-v2.git
cd invoice-manager-v2

# 安装基础依赖
pip install pdfplumber pillow openpyxl

# LLM 依赖（选择一个）
pip install google-generativeai  # Gemini（推荐）
pip install openai               # OpenAI
# Ollama 无需 pip 安装，直接运行 ollama serve
```

### 2. 配置 API Key

**方式一：环境变量**
```bash
# Windows
set GEMINI_API_KEY=your_api_key

# 或 Linux/Mac
export GEMINI_API_KEY=your_api_key
```

**方式二：.env 文件**（推荐）
```bash
# 复制示例配置
copy .env.example .env

# 编辑 .env 文件，填入 API Key
GEMINI_API_KEY=your_api_key
```

**使用 Ollama（本地/远程）**
```bash
# 本地运行
ollama serve
ollama pull qwen2.5:7b

# 远程服务器需配置防火墙开放 11434 端口
```

### 3. 运行程序

```bash
# 启动图形界面（推荐）
python gui.py

# 命令行模式
python main.py --cli <发票文件夹>

# 检查 LLM 可用性
python main.py --check

# 运行测试
python main.py --test
```

---

## �️ 使用方法

### 图形界面

1. 运行 `python gui.py` 启动界面
2. 选择 **LLM 提供商**（Gemini/OpenAI/Ollama）
3. 选择 **提取模式**（推荐 hybrid 混合模式）
4. 选择 **发票文件夹** 和 **输出文件夹**
5. 可选配置：多线程、断点续传、批处理大小
6. 点击 **"开始处理"**

### 远程 Ollama 配置

当选择 Ollama 提供商时，可以配置远程服务器地址：
- 选择 "本机" 使用 localhost
- 选择 "自定义" 输入远程地址（如 `http://192.168.1.3:11434`）

### 命令行模式

```bash
# 基本使用
python main.py --cli D:/发票文件夹

# 指定提供商和模式
python main.py --cli D:/发票文件夹 --provider gemini --mode hybrid

# 指定输出目录
python main.py --cli D:/发票文件夹 --output D:/整理后
```

### 编程接口

```python
from main_processor import InvoiceProcessor, process_invoices

# 方式一：使用处理器
processor = InvoiceProcessor(
    extraction_mode="hybrid",
    llm_provider="gemini",
    llm_model="gemini-2.5-flash"
)

# 处理单个文件
result = processor.process_file("invoice.pdf")
print(result["info"])

# 方式二：使用便捷函数
result = process_invoices(
    source_folder="D:/发票文件夹",
    output_folder="D:/整理后",
    llm_provider="ollama",
    llm_model="qwen2.5:7b",
    ollama_base_url="http://192.168.1.3:11434",  # 远程 Ollama
    max_workers=4,  # 多线程
    batch_size=10,  # 批处理大小
    resume=True     # 断点续传
)
```

---

## ⚙️ 配置选项

### 提取模式

| 模式 | 说明 | 推荐场景 |
|------|------|----------|
| `hybrid` | LLM + 正则验证（**推荐**） | 日常使用，准确性高 |
| `llm` | 纯 LLM 提取 | 信任 LLM 输出 |
| `vision` | 多模态视觉识别 | 图片发票、扫描件 |
| `regex_fallback` | 仅正则提取 | 无 API / 离线使用 |

### LLM 提供商对比

| 提供商 | 推荐模型 | 特点 | 费用 |
|--------|----------|------|------|
| `gemini` | gemini-2.5-flash | 快速、免费配额、中文好 | 有免费额度 |
| `openai` | gpt-4o-mini | 效果稳定、支持广 | 按量计费 |
| `ollama` | qwen2.5:7b | 离线运行、隐私安全 | **完全免费** |

### 环境变量配置

```bash
# API Keys
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# 默认配置
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
EXTRACTION_MODE=hybrid
```

---

## 📁 项目结构

```
发票项目V2版本/
├── main.py                 # 程序入口（CLI）
├── gui.py                  # 图形界面
├── main_processor.py       # 主处理器
├── report_generator.py     # Excel 报告生成器
├── .env.example            # 环境变量示例
├── .gitignore              # Git 忽略配置
├── README.md               # 项目文档
│
├── core/                   # 核心模块
│   ├── config/
│   │   ├── settings.py     # 系统配置
│   │   └── prompts.py      # LLM Prompt 模板
│   │
│   ├── llm/                # LLM 适配器
│   │   ├── base_adapter.py # 适配器基类
│   │   ├── gemini_adapter.py
│   │   ├── openai_adapter.py
│   │   ├── ollama_adapter.py
│   │   └── factory.py      # 模型工厂
│   │
│   └── extractors/         # 信息提取器
│       ├── base.py         # 提取器基类
│       ├── llm_extractor.py
│       ├── hybrid_extractor.py
│       └── vision_extractor.py
│
└── tests/                  # 单元测试
    └── test_extractors.py
```

---

## 📊 输出结果

处理完成后，输出目录结构如下：

```
输出文件夹/
├── 发票汇总报告.xlsx      # 汇总 Excel 表格
├── 销售方A公司/
│   ├── 购买方X公司/
│   │   ├── 发票1.pdf
│   │   └── 发票2.pdf
│   └── 购买方Y公司/
│       └── 发票3.pdf
└── 销售方B公司/
    └── 购买方Z公司/
        └── 发票4.pdf
```

---

## 🧪 测试

```bash
# 运行内置测试
python main.py --test

# 使用 pytest
python -m pytest tests/ -v

# 检查 LLM 可用性
python main.py --check
```

---

## ❓ 常见问题

### Q: Gemini API 无法连接？
A: Gemini API 需要访问 Google 服务器，国内用户需要配置代理或 VPN。

### Q: 如何使用远程 Ollama？
A: 在 GUI 中选择 Ollama 后，将服务器设置为 "自定义"，输入远程地址如 `http://192.168.1.3:11434`。

### Q: 识别不准确怎么办？
A: 
1. 尝试使用 `vision` 模式处理图片发票
2. 确保发票图片清晰
3. 尝试更换 LLM 模型

### Q: 处理大量发票太慢？
A:
1. 启用多线程处理
2. 增加批处理大小
3. 使用本地 Ollama 模型避免网络延迟

---

## 📝 更新日志

### V2.1 (2025-12)

- 🌐 新增远程 Ollama 服务器支持
- ⚡ 新增多线程并行处理
- 💾 新增断点续传功能
- 📦 新增批处理模式
- 📁 优化文件分类结构（销售方/购买方）
- 🔧 改进代开发票识别

### V2.0 (2024-12)

- 🤖 采用大模型进行发票信息识别
- 🔀 支持 Gemini/OpenAI/Ollama 三种提供商
- 👁️ 新增多模态视觉识别能力
- 🔌 模块化适配器架构

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**: V2.1  
**更新日期**: 2025年12月  
**维护状态**: ✅ 活跃维护
