"""
GUI 界面模块
使用 CustomTkinter 创建现代化的用户界面
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, Callable, List
import json


class ImageDescriberGUI(ctk.CTk):
    """图片描述生成工具 GUI"""
    
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.title("图片描述生成工具")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 状态变量
        self.selected_images: List[str] = []
        self.output_dir: str = ""
        self.model_path: str = ""
        self.duplicate_strategy: str = "skip"  # skip or overwrite
        
        # 创建界面
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建各部分
        self._create_selection_section()
        self._create_output_section()
        self._create_model_section()
        self._create_options_section()
        self._create_action_section()
        self._create_progress_section()
        self._create_result_section()
    
    def _create_selection_section(self):
        """图片选择区域"""
        selection_frame = ctk.CTkFrame(self.main_frame)
        selection_frame.pack(fill="x", pady=(0, 10))
        
        self.btn_select_image = ctk.CTkButton(
            selection_frame,
            text="📁 选择图片",
            command=self._select_images,
            width=120
        )
        self.btn_select_image.pack(side="left", padx=(0, 10))
        
        self.btn_select_dir = ctk.CTkButton(
            selection_frame,
            text="📂 选择目录",
            command=self._select_directory,
            width=120
        )
        self.btn_select_dir.pack(side="left")
        
        self.lbl_selection_info = ctk.CTkLabel(
            selection_frame,
            text="未选择图片",
            text_color="gray"
        )
        self.lbl_selection_info.pack(side="left", padx=10)
    
    def _create_output_section(self):
        """输出目录区域"""
        output_frame = ctk.CTkFrame(self.main_frame)
        output_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(output_frame, text="输出目录:").pack(side="left", padx=(0, 10))
        
        self.entry_output_dir = ctk.CTkEntry(
            output_frame,
            width=500,
            placeholder_text="默认与原图片同目录"
        )
        self.entry_output_dir.pack(side="left", padx=(0, 10))
        
        self.btn_browse_output = ctk.CTkButton(
            output_frame,
            text="浏览",
            command=self._browse_output_dir,
            width=60
        )
        self.btn_browse_output.pack(side="left")
    
    def _create_model_section(self):
        """模型配置区域"""
        model_frame = ctk.CTkFrame(self.main_frame)
        model_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(model_frame, text="模型配置:", font=ctk.CTkFont(weight="bold")).pack(
            side="top", anchor="w", padx=5, pady=(0, 5)
        )
        
        # 模型路径
        path_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        path_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(path_frame, text="模型路径:", width=80).pack(side="left", padx=(0, 10))
        
        self.entry_model_path = ctk.CTkEntry(
            path_frame,
            width=550,
            placeholder_text="选择 GGUF 模型文件"
        )
        self.entry_model_path.pack(side="left", padx=(0, 10))
        
        self.btn_browse_model = ctk.CTkButton(
            path_frame,
            text="浏览",
            command=self._browse_model,
            width=60
        )
        self.btn_browse_model.pack(side="left")
        
        # 模型参数
        params_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        params_frame.pack(fill="x")
        
        ctk.CTkLabel(params_frame, text="上下文长度:", width=80).pack(side="left", padx=(0, 10))
        self.entry_n_ctx = ctk.CTkEntry(params_frame, width=80)
        self.entry_n_ctx.pack(side="left", padx=(0, 20))
        self.entry_n_ctx.insert(0, "4096")
        
        ctk.CTkLabel(params_frame, text="温度:", width=40).pack(side="left", padx=(0, 10))
        self.entry_temperature = ctk.CTkEntry(params_frame, width=60)
        self.entry_temperature.pack(side="left", padx=(0, 20))
        self.entry_temperature.insert(0, "0.7")
        
        ctk.CTkLabel(params_frame, text="最大 Token:", width=80).pack(side="left", padx=(0, 10))
        self.entry_max_tokens = ctk.CTkEntry(params_frame, width=60)
        self.entry_max_tokens.pack(side="left")
        self.entry_max_tokens.insert(0, "512")
    
    def _create_options_section(self):
        """选项区域"""
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(options_frame, text="去重策略:", width=80).pack(side="left", padx=(0, 10))
        
        self.strategy_var = ctk.StringVar(value="skip")
        
        self.radio_skip = ctk.CTkRadioButton(
            options_frame,
            text="跳过相同 MD5",
            variable=self.strategy_var,
            value="skip"
        )
        self.radio_skip.pack(side="left", padx=(0, 20))
        
        self.radio_overwrite = ctk.CTkRadioButton(
            options_frame,
            text="覆盖已有记录",
            variable=self.strategy_var,
            value="overwrite"
        )
        self.radio_overwrite.pack(side="left")
    
    def _create_action_section(self):
        """操作按钮区域"""
        action_frame = ctk.CTkFrame(self.main_frame)
        action_frame.pack(fill="x", pady=(0, 10))
        
        self.btn_start = ctk.CTkButton(
            action_frame,
            text="▶ 开始处理",
            command=self._start_processing,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.btn_start.pack(side="left", padx=(0, 10))
        
        self.btn_stop = ctk.CTkButton(
            action_frame,
            text="⏹ 停止",
            command=self._stop_processing,
            height=40,
            state="disabled"
        )
        self.btn_stop.pack(side="left")
    
    def _create_progress_section(self):
        """进度显示区域"""
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(progress_frame, text="处理进度:", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=5, pady=(0, 5)
        )
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=5, pady=(0, 5))
        self.progress_bar.set(0)
        
        self.lbl_progress = ctk.CTkLabel(
            progress_frame,
            text="就绪",
            text_color="gray"
        )
        self.lbl_progress.pack(anchor="w", padx=5)
    
    def _create_result_section(self):
        """结果列表区域"""
        result_frame = ctk.CTkFrame(self.main_frame)
        result_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(result_frame, text="处理结果:", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=5, pady=(0, 5)
        )
        
        # 结果列表框
        self.result_listbox = ctk.CTkTextbox(result_frame, state="disabled")
        self.result_listbox.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # 操作按钮
        btn_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        self.btn_preview = ctk.CTkButton(
            btn_frame,
            text="预览",
            command=self._preview_selected,
            width=80
        )
        self.btn_preview.pack(side="left", padx=(0, 10))
        
        self.btn_edit = ctk.CTkButton(
            btn_frame,
            text="编辑描述",
            command=self._edit_description,
            width=100
        )
        self.btn_edit.pack(side="left")
    
    # ==================== 事件处理方法 ====================
    
    def _select_images(self):
        """选择单张或多张图片"""
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.webp *.bmp *.gif"),
                ("所有文件", "*.*")
            ]
        )
        if files:
            self.selected_images = list(files)
            self.lbl_selection_info.configure(text=f"已选择 {len(files)} 张图片")
    
    def _select_directory(self):
        """选择目录"""
        directory = filedialog.askdirectory(title="选择图片目录")
        if directory:
            from image_utils import get_images_from_directory
            self.selected_images = get_images_from_directory(directory)
            self.lbl_selection_info.configure(
                text=f"目录：{directory} ({len(self.selected_images)} 张图片)"
            )
    
    def _browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.entry_output_dir.delete(0, "end")
            self.entry_output_dir.insert(0, directory)
    
    def _browse_model(self):
        """浏览模型文件"""
        file_path = filedialog.askopenfilename(
            title="选择 GGUF 模型文件",
            filetypes=[("GGUF 文件", "*.gguf"), ("所有文件", "*.*")]
        )
        if file_path:
            self.entry_model_path.delete(0, "end")
            self.entry_model_path.insert(0, file_path)
    
    def _start_processing(self):
        """开始处理"""
        # 验证输入
        if not self.selected_images:
            messagebox.showwarning("警告", "请先选择图片或目录")
            return
        
        model_path = self.entry_model_path.get().strip()
        if not model_path:
            messagebox.showwarning("警告", "请选择模型文件")
            return
        
        if not Path(model_path).exists():
            messagebox.showerror("错误", f"模型文件不存在：{model_path}")
            return
        
        # 获取配置
        self.output_dir = self.entry_output_dir.get().strip() or None
        self.model_path = model_path
        self.duplicate_strategy = self.strategy_var.get()
        
        # 更新 UI 状态
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_bar.set(0)
        
        # 启动处理线程（在后台运行）
        self._run_processing()
    
    def _stop_processing(self):
        """停止处理"""
        # TODO: 实现停止逻辑
        messagebox.showinfo("提示", "停止功能开发中...")
    
    def _run_processing(self):
        """运行处理逻辑（后台线程）"""
        # TODO: 实现实际处理逻辑
        self.lbl_progress.configure(text="处理逻辑开发中...")
    
    def _preview_selected(self):
        """预览选中的结果"""
        # TODO: 实现预览功能
        messagebox.showinfo("提示", "预览功能开发中...")
    
    def _edit_description(self):
        """编辑描述"""
        # TODO: 实现编辑功能
        messagebox.showinfo("提示", "编辑功能开发中...")
    
    def log_result(self, message: str):
        """记录结果到列表框"""
        self.result_listbox.configure(state="normal")
        self.result_listbox.insert("end", message + "\n")
        self.result_listbox.configure(state="disabled")
    
    def update_progress(self, current: int, total: int, status: str):
        """更新进度"""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.lbl_progress.configure(text=f"{status} ({current}/{total})")
