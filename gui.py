# -*- coding: utf-8 -*-
"""
发票管理系统 V2 - 图形界面

支持LLM模型选择和提取模式配置
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class InvoiceGUI:
    """发票管理系统V2图形界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("发票管理系统 V2 - 大模型智能识别")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 状态变量
        self.source_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.llm_provider = tk.StringVar(value="gemini")
        self.llm_model = tk.StringVar(value="")
        self.extraction_mode = tk.StringVar(value="hybrid")
        self.enable_multithread = tk.BooleanVar(value=False)
        self.thread_count = tk.StringVar(value="4")
        self.ollama_server = tk.StringVar(value="本机")
        self.ollama_custom_url = tk.StringVar(value="http://192.168.1.3:11434")
        # Ollama 双模型配置
        self.ollama_text_model = tk.StringVar(value="")
        self.ollama_vision_model = tk.StringVar(value="")
        self.resume_progress = tk.BooleanVar(value=False)
        self.batch_size = tk.StringVar(value="10")
        self.processing = False
        
        self._create_widgets()
        
        # 绑定提供商变化事件
        self.llm_provider.trace_add("write", self._on_provider_change)
        
        # 初始化模型列表
        self._on_provider_change()
    
    def _create_widgets(self):
        """创建界面控件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== 标题 =====
        title_label = ttk.Label(
            main_frame, 
            text="发票管理系统 V2", 
            font=("微软雅黑", 18, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(
            main_frame, 
            text="大模型智能识别 | 支持PDF/OFD/图片/XML", 
            font=("微软雅黑", 10)
        )
        subtitle_label.pack(pady=(0, 15))
        
        # ===== 文件夹选择 =====
        folder_frame = ttk.LabelFrame(main_frame, text="文件夹设置", padding="10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 源文件夹
        source_row = ttk.Frame(folder_frame)
        source_row.pack(fill=tk.X, pady=5)
        ttk.Label(source_row, text="发票文件夹:", width=12).pack(side=tk.LEFT)
        ttk.Entry(source_row, textvariable=self.source_folder, width=50).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(source_row, text="浏览...", command=self._browse_source).pack(side=tk.LEFT)
        
        # 输出文件夹
        output_row = ttk.Frame(folder_frame)
        output_row.pack(fill=tk.X, pady=5)
        ttk.Label(output_row, text="输出文件夹:", width=12).pack(side=tk.LEFT)
        ttk.Entry(output_row, textvariable=self.output_folder, width=50).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(output_row, text="浏览...", command=self._browse_output).pack(side=tk.LEFT)
        
        # ===== LLM配置 =====
        config_frame = ttk.LabelFrame(main_frame, text="LLM配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_row = ttk.Frame(config_frame)
        config_row.pack(fill=tk.X)
        
        # LLM提供商
        ttk.Label(config_row, text="LLM提供商:").pack(side=tk.LEFT)
        self.provider_combo = ttk.Combobox(
            config_row, 
            textvariable=self.llm_provider,
            values=["gemini", "deepseek", "openai", "ollama"],
            state="readonly",
            width=10
        )
        self.provider_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # 模型选择
        ttk.Label(config_row, text="模型:").pack(side=tk.LEFT)
        self.model_combo = ttk.Combobox(
            config_row, 
            textvariable=self.llm_model,
            values=[],
            width=20
        )
        self.model_combo.pack(side=tk.LEFT, padx=(5, 5))
        
        # 刷新模型列表按钮
        ttk.Button(config_row, text="刷新", command=self._refresh_models, width=5).pack(side=tk.LEFT, padx=(0, 10))
        
        # 提取模式
        ttk.Label(config_row, text="提取模式:").pack(side=tk.LEFT)
        mode_combo = ttk.Combobox(
            config_row,
            textvariable=self.extraction_mode,
            values=["hybrid", "llm", "vision", "regex_fallback"],
            state="readonly",
            width=12
        )
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        # 检查按钮
        ttk.Button(config_row, text="检查LLM", command=self._check_llm).pack(side=tk.RIGHT)
        
        # 第二行：模式说明 + 多线程设置
        config_row2 = ttk.Frame(config_frame)
        config_row2.pack(fill=tk.X, pady=(5, 0))
        
        mode_desc = ttk.Label(
            config_row2,
            text="hybrid=混合模式(推荐) | llm=纯LLM | vision=视觉识别 | regex_fallback=正则兜底",
            font=("微软雅黑", 9),
            foreground="gray"
        )
        mode_desc.pack(side=tk.LEFT)
        
        # 多线程设置
        ttk.Separator(config_row2, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        self.multithread_check = ttk.Checkbutton(
            config_row2,
            text="多线程",
            variable=self.enable_multithread,
            command=self._toggle_multithread
        )
        self.multithread_check.pack(side=tk.LEFT)
        
        ttk.Label(config_row2, text="线程数:").pack(side=tk.LEFT, padx=(5, 0))
        self.thread_spinbox = ttk.Spinbox(
            config_row2,
            from_=2,
            to=16,
            width=4,
            textvariable=self.thread_count,
            state="disabled"
        )
        self.thread_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 批处理设置
        ttk.Separator(config_row2, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Label(config_row2, text="批次大小:").pack(side=tk.LEFT)
        self.batch_spinbox = ttk.Spinbox(
            config_row2,
            from_=1,
            to=100,
            width=4,
            textvariable=self.batch_size
        )
        self.batch_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 继续上次进度
        self.resume_check = ttk.Checkbutton(
            config_row2,
            text="继续上次进度",
            variable=self.resume_progress
        )
        self.resume_check.pack(side=tk.LEFT, padx=(10, 0))
        
        # 第三行：Ollama服务器设置（仅当选择Ollama时显示）
        self.ollama_config_frame = ttk.Frame(config_frame)
        # 初始不显示，待选择Ollama时才显示
        
        ttk.Label(self.ollama_config_frame, text="Ollama服务器:").pack(side=tk.LEFT)
        self.server_combo = ttk.Combobox(
            self.ollama_config_frame,
            textvariable=self.ollama_server,
            values=["本机", "自定义"],
            state="readonly",
            width=8
        )
        self.server_combo.pack(side=tk.LEFT, padx=5)
        self.server_combo.bind("<<ComboboxSelected>>", self._on_server_change)
        
        ttk.Label(self.ollama_config_frame, text="地址:").pack(side=tk.LEFT, padx=(10, 0))
        self.custom_url_entry = ttk.Entry(
            self.ollama_config_frame,
            textvariable=self.ollama_custom_url,
            width=30,
            state="disabled"
        )
        self.custom_url_entry.pack(side=tk.LEFT, padx=5)
        
        # 第四行：Ollama双模型选择（文本模型 + 图片模型）
        self.ollama_model_frame = ttk.Frame(config_frame)
        # 初始不显示
        
        ttk.Label(self.ollama_model_frame, text="文本模型:").pack(side=tk.LEFT)
        self.text_model_combo = ttk.Combobox(
            self.ollama_model_frame,
            textvariable=self.ollama_text_model,
            values=[],
            width=18
        )
        self.text_model_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(self.ollama_model_frame, text="图片模型:").pack(side=tk.LEFT)
        self.vision_model_combo = ttk.Combobox(
            self.ollama_model_frame,
            textvariable=self.ollama_vision_model,
            values=[],
            width=18
        )
        self.vision_model_combo.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        ttk.Button(
            self.ollama_model_frame, 
            text="刷新模型", 
            command=self._refresh_ollama_models,
            width=10
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # 多模态模型提示
        vision_hint = ttk.Label(
            self.ollama_model_frame,
            text="(图片需多模态模型如llava)",
            font=("微软雅黑", 8),
            foreground="gray"
        )
        vision_hint.pack(side=tk.LEFT, padx=(10, 0))
        
        # ===== 操作按钮 =====
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="开始处理", 
            command=self._start_processing,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="停止", 
            command=self._stop_processing,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="清空日志", command=self._clear_log).pack(side=tk.RIGHT, padx=5)
        
        # ===== 进度条 =====
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # ===== 日志区域 =====
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=15, 
            font=("Consolas", 10),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ===== 状态栏 =====
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN,
            padding=5
        )
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def _browse_source(self):
        """选择源文件夹"""
        folder = filedialog.askdirectory(title="选择发票文件夹")
        if folder:
            self.source_folder.set(folder)
            if not self.output_folder.get():
                self.output_folder.set(os.path.join(folder, "已处理"))
    
    def _browse_output(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)
    
    def _on_provider_change(self, *args):
        """提供商改变时更新模型列表"""
        provider = self.llm_provider.get()
        
        if provider == "gemini":
            models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]
            self.model_combo['values'] = models
            self.llm_model.set(models[0])
            self.model_combo['state'] = 'readonly'
            # 隐藏Ollama配置
            self.ollama_config_frame.pack_forget()
            self.ollama_model_frame.pack_forget()
        elif provider == "deepseek":
            # DeepSeek 模型列表
            models = ["deepseek-chat", "deepseek-reasoner"]
            self.model_combo['values'] = models
            self.llm_model.set(models[0])
            self.model_combo['state'] = 'readonly'
            # 隐藏Ollama配置
            self.ollama_config_frame.pack_forget()
            self.ollama_model_frame.pack_forget()
        elif provider == "openai":
            models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
            self.model_combo['values'] = models
            self.llm_model.set(models[0])
            self.model_combo['state'] = 'readonly'
            # 隐藏Ollama配置
            self.ollama_config_frame.pack_forget()
            self.ollama_model_frame.pack_forget()
        elif provider == "ollama":
            # 显示Ollama配置（服务器 + 双模型选择）
            self.ollama_config_frame.pack(fill=tk.X, pady=(5, 0))
            self.ollama_model_frame.pack(fill=tk.X, pady=(5, 0))
            # 隐藏单模型选择（对Ollama使用双模型选择）
            self.model_combo['state'] = 'disabled'
            self.llm_model.set("（使用下方双模型）")
            # 刷新双模型列表
            self._refresh_ollama_models()
    
    def _refresh_models(self):
        """刷新模型列表（云端API用）"""
        provider = self.llm_provider.get()
        
        if provider == "ollama":
            # Ollama使用专门的双模型刷新
            self._refresh_ollama_models()
            return
        
        # 其他提供商直接触发provider change
        self._on_provider_change()
    
    def _refresh_ollama_models(self):
        """刷新Ollama双模型列表"""
        base_url = self._get_ollama_url()
        self._log(f"正在获取Ollama模型列表 ({base_url})...")
        
        try:
            from core.llm import OllamaAdapter
            adapter = OllamaAdapter(base_url=base_url)
            models = adapter.list_models()
            
            if models:
                # 更新文本模型下拉框
                self.text_model_combo['values'] = models
                if not self.ollama_text_model.get() or self.ollama_text_model.get() not in models:
                    # 优先选择 qwen 系列作为文本模型
                    text_default = next((m for m in models if 'qwen' in m.lower()), models[0])
                    self.ollama_text_model.set(text_default)
                
                # 更新图片模型下拉框
                self.vision_model_combo['values'] = models
                if not self.ollama_vision_model.get() or self.ollama_vision_model.get() not in models:
                    # 优先选择多模态模型（llava/bakllava/minicpm-v等）作为图片模型
                    vision_keywords = ['llava', 'bakllava', 'minicpm', 'gemma3']
                    vision_default = next(
                        (m for m in models if any(k in m.lower() for k in vision_keywords)), 
                        models[0]
                    )
                    self.ollama_vision_model.set(vision_default)
                
                self._log(f"找到 {len(models)} 个Ollama模型: {', '.join(models[:5])}{'...' if len(models) > 5 else ''}")
            else:
                default_models = ["qwen2.5:7b", "llava:7b"]
                self.text_model_combo['values'] = default_models
                self.vision_model_combo['values'] = default_models
                self.ollama_text_model.set("qwen2.5:7b")
                self.ollama_vision_model.set("llava:7b")
                self._log("未找到Ollama模型，请确保Ollama服务已启动")
        except Exception as e:
            self._log(f"获取模型列表失败: {e}")
            default_models = ["qwen2.5:7b", "llava:7b"]
            self.text_model_combo['values'] = default_models
            self.vision_model_combo['values'] = default_models
            self.ollama_text_model.set("qwen2.5:7b")
            self.ollama_vision_model.set("llava:7b")
    
    def _get_ollama_url(self) -> str:
        """获取当前配置的Ollama服务器URL"""
        if self.ollama_server.get() == "本机":
            return "http://localhost:11434"
        else:
            return self.ollama_custom_url.get()
    
    def _on_server_change(self, event=None):
        """Ollama服务器选择改变"""
        if self.ollama_server.get() == "自定义":
            self.custom_url_entry.config(state="normal")
            self._log("已切换到自定义服务器，请输入地址")
        else:
            self.custom_url_entry.config(state="disabled")
            self._log("已切换到本机服务器")
        # 刷新模型列表
        self._refresh_ollama_models()
    
    def _toggle_multithread(self):
        """切换多线程开关"""
        if self.enable_multithread.get():
            self.thread_spinbox.config(state="normal")
            self._log("多线程已启用")
        else:
            self.thread_spinbox.config(state="disabled")
            self._log("多线程已禁用")
    
    def _check_llm(self):
        """检查LLM可用性"""
        self._log("正在检查LLM可用性...")
        
        try:
            from core.llm import LLMFactory
            provider = self.llm_provider.get()
            model = self.llm_model.get()
            
            self._log(f"检查: {provider} / {model}")
            adapter = LLMFactory.create(provider, model)
            
            if adapter.is_available():
                self._log(f"✓ {provider.upper()} 可用 ({adapter.model_name})")
                messagebox.showinfo("检查结果", f"{provider.upper()} 服务可用！\n模型: {adapter.model_name}")
            else:
                self._log(f"✗ {provider.upper()} 不可用 (模型: {adapter.model_name})")
                messagebox.showwarning("检查结果", f"{provider.upper()} 服务不可用\n模型 {adapter.model_name} 可能未下载")
        except Exception as e:
            self._log(f"✗ 检查失败: {e}")
            messagebox.showerror("错误", f"检查失败: {e}")
    
    def _start_processing(self):
        """开始处理"""
        source = self.source_folder.get()
        if not source or not os.path.isdir(source):
            messagebox.showerror("错误", "请选择有效的发票文件夹")
            return
        
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start()
        self.status_var.set("处理中...")
        
        # 在后台线程处理
        thread = threading.Thread(target=self._process_thread)
        thread.daemon = True
        thread.start()
    
    def _process_thread(self):
        """后台处理线程"""
        try:
            from main_processor import process_invoices
            
            provider = self.llm_provider.get()
            model = self.llm_model.get()
            source = self.source_folder.get()
            output = self.output_folder.get()
            
            self._log(f"开始处理: {source}")
            self._log(f"输出文件夹: {output}")
            self._log(f"LLM提供商: {provider}")
            self._log(f"提取模式: {self.extraction_mode.get()}")
            
            # Ollama服务器设置和双模型配置
            ollama_url = None
            ollama_text_model = None
            ollama_vision_model = None
            if provider == "ollama":
                ollama_url = self._get_ollama_url()
                ollama_text_model = self.ollama_text_model.get()
                ollama_vision_model = self.ollama_vision_model.get()
                self._log(f"Ollama服务器: {ollama_url}")
                self._log(f"文本模型: {ollama_text_model}")
                self._log(f"图片模型: {ollama_vision_model}")
            else:
                self._log(f"模型: {model}")
            
            # 多线程设置
            use_multithread = self.enable_multithread.get()
            thread_count = int(self.thread_count.get()) if use_multithread else 1
            if use_multithread:
                self._log(f"多线程: 启用 ({thread_count} 线程)")
            else:
                self._log("多线程: 禁用")
            self._log("-" * 50)
            
            # 断点续传和批处理设置
            resume = self.resume_progress.get()
            batch_size = int(self.batch_size.get())
            if resume:
                self._log("继续上次进度: 启用")
            self._log(f"批处理大小: {batch_size}")
            
            # 文件锁定回调（弹窗提示用户关闭Excel）
            def on_file_locked(message: str) -> bool:
                import tkinter.messagebox as mb
                return mb.askokcancel("文件被占用", message)
            
            # 调用处理函数
            result = process_invoices(
                source_folder=source,
                output_folder=output,
                extraction_mode=self.extraction_mode.get(),
                llm_provider=provider,
                llm_model=model,
                generate_report=True,
                classify_files=True,
                max_workers=thread_count if use_multithread else 1,
                ollama_base_url=ollama_url,
                ollama_text_model=ollama_text_model,
                ollama_vision_model=ollama_vision_model,
                batch_size=batch_size,
                resume=resume,
                file_lock_callback=on_file_locked
            )
            
            results = result.get("results", [])
            stats = result.get("stats", {})
            classify_result = result.get("classify_result")
            report_result = result.get("report_result")
            
            self._log("-" * 50)
            self._log(f"处理完成: 成功 {stats.get('success', 0)}/{stats.get('total_files', 0)}")
            self._log(f"耗时: {stats.get('total_time', 0):.2f} 秒")
            
            # 显示各发票识别结果
            for r in results:
                if r.get("success"):
                    info = r.get("info", {})
                    filename = Path(r['file_path']).name
                    seller = info.get('销售方名称') or '未识别'
                    invoice_no = info.get('发票号码') or '未识别'
                    self._log(f"✓ {filename}")
                    self._log(f"  → 发票号: {invoice_no}, 销方: {seller[:20]}")
            
            # 显示分类结果
            if classify_result:
                self._log("-" * 50)
                self._log(f"文件分类: 复制成功 {classify_result['success']} 个")
                self._log(f"创建文件夹: {classify_result['folders_created']} 个")
            
            # 显示报告结果
            if report_result and report_result.get('success'):
                self._log(f"Excel报告: {report_result['record_count']} 条记录")
                self._log(f"报告路径: {result.get('output_folder')}/发票汇总报告.xlsx")
            
            success_msg = f"处理完成！\n\n" \
                          f"成功识别: {stats.get('success', 0)} 个发票\n" \
                          f"文件分类: {classify_result['success'] if classify_result else 0} 个\n" \
                          f"Excel报告: {report_result['record_count'] if report_result and report_result.get('success') else 0} 条\n\n" \
                          f"输出目录: {result.get('output_folder')}"
            
            self.root.after(0, lambda: messagebox.showinfo("完成", success_msg))
            
        except Exception as e:
            error_msg = str(e)
            self._log(f"处理出错: {error_msg}")
            import traceback
            self._log(traceback.format_exc())
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"处理失败: {msg}"))
        
        finally:
            self.root.after(0, self._processing_done)
    
    def _processing_done(self):
        """处理完成"""
        self.processing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()
        self.status_var.set("就绪")
    
    def _stop_processing(self):
        """停止处理"""
        self.processing = False
        self._log("用户请求停止处理...")
    
    def _log(self, message: str):
        """添加日志"""
        def _append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _append)
    
    def _clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def run(self):
        """运行GUI"""
        self._log("发票管理系统 V2 已启动")
        self._log("请选择发票文件夹并配置LLM选项")
        self.root.mainloop()


if __name__ == "__main__":
    app = InvoiceGUI()
    app.run()
