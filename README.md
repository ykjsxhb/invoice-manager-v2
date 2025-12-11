# 发票管理系统 V2 - 大模型智能识别

> 基于大语言模型（LLM）的智能发票信息提取系统

---

## 🎯 系统简介

这是发票管理系统的 **V2 版本**，采用大模型（LLM）替代传统正则表达式进行发票信息识别。

### V2 新特性 ✨

- **🤖 大模型识别**：使用 Gemini/GPT/Ollama 等大模型智能提取发票信息
- **🔀 混合提取模式**：LLM + 正则验证，兼顾准确性和可靠性
- **👁️ 多模态视觉识别**：直接从发票图片识别，无需 OCR 预处理
- **🔌 多模型支持**：支持 Gemini、OpenAI、Ollama 本地模型
- **📊 向后兼容**：支持正则兜底模式，无需 API 也可使用

### 对比 V1

| 特性 | V1 (正则) | V2 (LLM) |
|------|-----------|----------|
| 识别准确率 | 85-95% | **95%+** |
| 新格式适应性 | 需手动添加规则 | **自动适应** |
| 维护成本 | 高 | **低** |
| 离线运行 | ✓ 支持 | ✓ 支持 (Ollama) |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd 发票项目V2版本

# 基础依赖
pip install pdfplumber

# LLM依赖（选择一个）
pip install google-generativeai  # Gemini
pip install openai               # OpenAI
# Ollama 无需 pip 安装，直接运行 ollama serve
```

### 2. 配置 API Key

```bash
# Gemini (推荐)
set GEMINI_API_KEY=your_api_key

# 或 OpenAI
set OPENAI_API_KEY=your_api_key

# 或 Ollama (无需配置，确保服务运行)
ollama serve
ollama pull qwen2.5:7b
```

### 3. 运行程序

```bash
# 启动 GUI
python gui.py

# 或命令行模式
python main.py --cli <发票文件夹>

# 运行测试
python main.py --test

# 检查 LLM 可用性
python main.py --check
```

---

## 📖 使用方法

### 方法1：图形界面

1. 运行 `python gui.py`
2. 选择 LLM 提供商（Gemini/OpenAI/Ollama）
3. 选择提取模式（推荐 hybrid）
4. 选择发票文件夹
5. 点击"开始处理"

### 方法2：命令行

```bash
# 使用默认配置
python main.py --cli D:/发票文件夹

# 指定提供商和模式
python main.py --cli D:/发票文件夹 --provider gemini --mode hybrid
```

### 方法3：编程接口

```python
from main_processor import InvoiceProcessor

# 创建处理器
processor = InvoiceProcessor(
    extraction_mode="hybrid",
    llm_provider="gemini"
)

# 处理单个文件
result = processor.process_file("invoice.pdf")
print(result["info"])

# 处理整个文件夹
results = processor.process_folder("D:/发票文件夹")
```

---

## ⚙️ 配置选项

### 提取模式

| 模式 | 说明 | 推荐场景 |
|------|------|----------|
| `hybrid` | LLM + 正则验证（**推荐**） | 日常使用 |
| `llm` | 纯 LLM 提取 | 信任 LLM 输出 |
| `vision` | 多模态视觉识别 | 图片发票 |
| `regex_fallback` | 仅正则提取 | 无 API/离线 |

### LLM 提供商

| 提供商 | 模型 | 特点 |
|--------|------|------|
| `gemini` | gemini-2.5-flash | 快速、免费配额、中文好 |
| `openai` | gpt-4o-mini | 效果好、成本适中 |
| `ollama` | qwen2.5:7b | 离线运行、无 API 费用 |

### 环境变量

```bash
# API Keys
GEMINI_API_KEY=xxx
OPENAI_API_KEY=xxx

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
├── main.py                 # 程序入口
├── gui.py                  # 图形界面
├── main_processor.py       # 主处理器
├── core/
│   ├── config/
│   │   ├── settings.py     # 系统配置
│   │   └── prompts.py      # Prompt模板
│   ├── llm/
│   │   ├── base_adapter.py # 适配器基类
│   │   ├── gemini_adapter.py
│   │   ├── openai_adapter.py
│   │   ├── ollama_adapter.py
│   │   └── factory.py      # 模型工厂
│   └── extractors/
│       ├── base.py         # 提取器基类
│       ├── llm_extractor.py
│       ├── hybrid_extractor.py
│       └── vision_extractor.py
└── tests/
    └── test_extractors.py  # 单元测试
```

---

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 或使用内置测试
python main.py --test
```

---

## 💰 费用说明

| 提供商 | 费用 | 1000张发票预估 |
|--------|------|----------------|
| Gemini | 有免费配额 | $0.05-0.10 |
| OpenAI | 按量计费 | $0.20-0.50 |
| Ollama | **免费** | $0 |

---

## 📝 更新日志

### V2.0 (2024-12)

**全新架构**:
- 🤖 采用大模型进行发票信息识别
- 🔀 支持 Gemini/OpenAI/Ollama 三种提供商
- 👁️ 新增多模态视觉识别能力
- 🔌 模块化适配器架构，易于扩展

**继承自 V1**:
- 📄 支持 PDF/OFD/图片/XML 多种格式
- 📊 Excel 报告生成
- 🖥️ 图形界面

---

## 📞 技术支持

如有问题，请检查：
1. API Key 是否正确配置
2. LLM 服务是否可用（`python main.py --check`）
3. 文件格式是否支持

---

**版本**: V2.0  
**更新日期**: 2024年12月  
**维护状态**: ✅ 活跃维护
