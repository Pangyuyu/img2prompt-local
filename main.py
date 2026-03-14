#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片描述生成工具 - 主程序入口
使用本地多模态 AI 模型对图片进行自动描述
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional, Dict
import json
import os

from image_utils import get_images_from_directory
from processor import ImageProcessor, ProcessingStatus, ProcessingThread
from data_viewer import open_data_viewer


# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "config.json"


class ImageDescriberApp(ctk.CTk):
    """图片描述生成工具主应用"""

    def __init__(self):
        super().__init__()

        # 窗口配置
        self.title("图片描述生成工具 - SDXL 提示词生成器")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 状态变量
        self.selected_images: List[str] = []
        self.processor: Optional[ImageProcessor] = None
        self.processing_thread: Optional[ProcessingThread] = None

        # 加载配置
        self.config = self._load_config()

        # 创建界面
        self._create_widgets()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "image_dirs": [],  # 图片目录历史
            "output_dirs": [],  # 输出目录历史
            "api_url": "http://localhost:8080",
            "api_key": "",
            "n_ctx": 4096,
            "temperature": 0.7,
            "max_tokens": 512,
            "duplicate_strategy": "skip"
        }

        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                pass

        return default_config

    def _save_config(self):
        """保存配置文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败：{e}")

    def _add_to_history(self, history_list: List[str], item: str, max_items: int = 10):
        """添加到历史记录"""
        if item and item not in history_list:
            history_list.insert(0, item)
            # 限制历史记录数量
            while len(history_list) > max_items:
                history_list.pop()

    def _create_widgets(self):
        """创建界面组件"""
        # 配置网格布局
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # 创建各部分
        self._create_selection_section(0)
        self._create_output_section(1)
        self._create_api_section(2)
        self._create_options_section(3)
        self._create_action_section(4)
        self._create_progress_section(5)
        self._create_result_section(6)

    def _create_selection_section(self, row: int):
        """图片选择区域"""
        selection_frame = ctk.CTkFrame(self)
        selection_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        selection_frame.grid_columnconfigure(1, weight=1)

        # 选择模式下拉框 - 使用中文显示
        ctk.CTkLabel(selection_frame, text="选择方式:", width=70).grid(row=0, column=0, padx=(0, 5), pady=5)
        
        self.selection_mode_var = ctk.StringVar(value="dir")  # 默认选择目录
        self.combo_selection_mode = ctk.CTkComboBox(
            selection_frame,
            values=["single", "multi", "dir"],
            variable=self.selection_mode_var,
            command=self._on_selection_mode_changed,
            width=150
        )
        self.combo_selection_mode.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="w")
        # 设置默认显示文字
        self.combo_selection_mode.set("📂 选择目录")
        
        # 模式说明标签
        self.lbl_mode_hint = ctk.CTkLabel(
            selection_frame,
            text="📂 选择目录",
            text_color="#4da6ff",
            width=100
        )
        self.lbl_mode_hint.grid(row=0, column=2, padx=(0, 10), pady=5, sticky="w")

        # 选择按钮
        self.btn_select = ctk.CTkButton(
            selection_frame,
            text="📂 选择目录",
            command=self._select_directory,
            width=120,
            height=32
        )
        self.btn_select.grid(row=0, column=3, padx=(0, 10), pady=5)

        self.lbl_selection_info = ctk.CTkLabel(
            selection_frame,
            text="未选择图片",
            text_color="gray",
            anchor="w"
        )
        self.lbl_selection_info.grid(row=1, column=0, columnspan=4, sticky="w", pady=2)

    def _create_output_section(self, row: int):
        """输出目录区域"""
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        output_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(output_frame, text="输出目录:").grid(row=0, column=0, padx=(0, 10))

        self.output_dir_var = ctk.StringVar(value="")
        self.combo_output_dir = ctk.CTkComboBox(
            output_frame,
            values=self.config.get("output_dirs", []),
            variable=self.output_dir_var
        )
        self.combo_output_dir.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        self.combo_output_dir.set("默认与原图片同目录")

        self.btn_browse_output = ctk.CTkButton(
            output_frame,
            text="浏览",
            command=self._browse_output_dir,
            width=60
        )
        self.btn_browse_output.grid(row=0, column=2)

    def _create_api_section(self, row: int):
        """API 配置区域"""
        api_frame = ctk.CTkFrame(self)
        api_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        api_frame.grid_columnconfigure(1, weight=1)

        # 标题
        ctk.CTkLabel(
            api_frame,
            text="服务配置:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))

        # API 地址
        ctk.CTkLabel(api_frame, text="API 地址:", width=80).grid(row=1, column=0, padx=(0, 10))

        self.entry_api_url = ctk.CTkEntry(api_frame, placeholder_text="http://localhost:8080")
        self.entry_api_url.grid(row=1, column=1, padx=(0, 10), sticky="ew", columnspan=2)
        self.entry_api_url.insert(0, self.config.get("api_url", "http://localhost:8080"))

        self.btn_test_connection = ctk.CTkButton(
            api_frame,
            text="测试连接",
            command=self._test_connection,
            width=80
        )
        self.btn_test_connection.grid(row=1, column=3, padx=(5, 0))

        # API Key（可选）
        ctk.CTkLabel(api_frame, text="API Key:", width=80).grid(row=2, column=0, padx=(0, 10))

        self.entry_api_key = ctk.CTkEntry(api_frame, placeholder_text="可选")
        self.entry_api_key.grid(row=2, column=1, padx=(0, 10), sticky="ew", columnspan=2)
        self.entry_api_key.insert(0, self.config.get("api_key", ""))

        # 模型参数
        params_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        params_frame.grid(row=3, column=0, columnspan=4, sticky="w")

        ctk.CTkLabel(params_frame, text="上下文长度:", width=80).pack(side="left", padx=(0, 10))
        self.entry_n_ctx = ctk.CTkEntry(params_frame, width=80)
        self.entry_n_ctx.pack(side="left", padx=(0, 20))
        self.entry_n_ctx.insert(0, str(self.config.get("n_ctx", 4096)))

        ctk.CTkLabel(params_frame, text="温度:", width=40).pack(side="left", padx=(0, 10))
        self.entry_temperature = ctk.CTkEntry(params_frame, width=60)
        self.entry_temperature.pack(side="left", padx=(0, 20))
        self.entry_temperature.insert(0, str(self.config.get("temperature", 0.7)))

        ctk.CTkLabel(params_frame, text="最大 Token:", width=80).pack(side="left", padx=(0, 10))
        self.entry_max_tokens = ctk.CTkEntry(params_frame, width=60)
        self.entry_max_tokens.pack(side="left")
        self.entry_max_tokens.insert(0, str(self.config.get("max_tokens", 512)))

    def _create_options_section(self, row: int):
        """选项区域"""
        options_frame = ctk.CTkFrame(self)
        options_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(options_frame, text="去重策略:", width=80).pack(side="left", padx=(0, 10))

        self.strategy_var = ctk.StringVar(value=self.config.get("duplicate_strategy", "skip"))

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

    def _create_action_section(self, row: int):
        """操作按钮区域"""
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

        self.btn_start = ctk.CTkButton(
            action_frame,
            text="▶ 开始处理",
            command=self._start_processing,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green"
        )
        self.btn_start.pack(side="left", padx=(0, 10))

        self.btn_stop = ctk.CTkButton(
            action_frame,
            text="⏹ 停止",
            command=self._stop_processing,
            height=35,
            state="disabled",
            fg_color="#cc2222",  # 红色背景
            text_color="#ffffff",  # 白色文字
            hover_color="#aa1111"
        )
        self.btn_stop.pack(side="left")

        self.btn_view_data = ctk.CTkButton(
            action_frame,
            text="📊 查看数据",
            command=self._open_data_viewer,
            height=35
        )
        self.btn_view_data.pack(side="left", padx=(10, 10))

        self.btn_clear = ctk.CTkButton(
            action_frame,
            text="🗑 清空列表",
            command=self._clear_results,
            height=35
        )
        self.btn_clear.pack(side="right")

    def _create_progress_section(self, row: int):
        """进度显示区域"""
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(
            progress_frame,
            text="处理进度:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)

        self.lbl_progress = ctk.CTkLabel(
            progress_frame,
            text="就绪 - 请选择图片和模型后点击开始处理",
            text_color="gray"
        )
        self.lbl_progress.pack(anchor="w")

    def _create_result_section(self, row: int):
        """结果列表区域"""
        result_frame = ctk.CTkFrame(self)
        result_frame.grid(row=row, column=0, sticky="nsew", padx=10, pady=5)
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            result_frame,
            text="处理结果:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        # 结果列表框
        self.result_text = ctk.CTkTextbox(result_frame, state="disabled")
        self.result_text.grid(row=1, column=0, sticky="nsew")

        # 操作按钮
        btn_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="e", pady=(5, 0))

        self.btn_open_json = ctk.CTkButton(
            btn_frame,
            text="📄 打开 JSON",
            command=self._open_json_file,
            width=100
        )
        self.btn_open_json.pack(side="right", padx=(0, 10))

        self.btn_edit = ctk.CTkButton(
            btn_frame,
            text="✏️ 编辑描述",
            command=self._edit_description,
            width=100
        )
        self.btn_edit.pack(side="right")

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
            self._log_result(f"✓ 已选择 {len(files)} 张图片")

    def _select_directory(self):
        """选择目录"""
        directory = filedialog.askdirectory(title="选择图片目录")
        if directory:
            self.selected_images = get_images_from_directory(directory)
            self.lbl_selection_info.configure(
                text=f"目录：{directory} ({len(self.selected_images)} 张图片)"
            )
            # 添加到历史记录
            self._add_to_history(self.config["image_dirs"], directory)
            self._save_config()
            self._log_result(f"✓ 从目录加载 {len(self.selected_images)} 张图片：{directory}")

    def _on_selection_mode_changed(self, event=None):
        """选择模式切换"""
        mode = self.selection_mode_var.get()
        
        if mode == "single":
            self.btn_select.configure(text="📁 选择单张图片", command=self._select_single_image)
            self.lbl_mode_hint.configure(text="📁 选择单张图片")
            self.combo_selection_mode.set("📁 选择单张图片")
        elif mode == "multi":
            self.btn_select.configure(text="📁 选择多张图片", command=self._select_multi_images)
            self.lbl_mode_hint.configure(text="📁 选择多张图片")
            self.combo_selection_mode.set("📁 选择多张图片")
        else:  # dir
            self.btn_select.configure(text="📂 选择目录", command=self._select_directory)
            self.lbl_mode_hint.configure(text="📂 选择目录")
            self.combo_selection_mode.set("📂 选择目录")

    def _select_single_image(self):
        """选择单张图片"""
        file = filedialog.askopenfilename(
            title="选择单张图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.webp *.bmp *.gif"),
                ("所有文件", "*.*")
            ]
        )
        if file:
            self.selected_images = [file]
            self.lbl_selection_info.configure(text=f"已选择 1 张图片：{Path(file).name}")
            self._log_result(f"✓ 已选择 1 张图片：{Path(file).name}")

    def _select_multi_images(self):
        """选择多张图片"""
        files = filedialog.askopenfilenames(
            title="选择多张图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.webp *.bmp *.gif"),
                ("所有文件", "*.*")
            ]
        )
        if files:
            self.selected_images = list(files)
            self.lbl_selection_info.configure(text=f"已选择 {len(files)} 张图片")
            self._log_result(f"✓ 已选择 {len(files)} 张图片")

    def _select_directory(self):
        """选择目录"""
        directory = filedialog.askdirectory(title="选择图片目录")
        if directory:
            self.selected_images = get_images_from_directory(directory)
            self.lbl_selection_info.configure(
                text=f"目录：{directory} ({len(self.selected_images)} 张图片)"
            )
            # 添加到历史记录
            self._add_to_history(self.config["image_dirs"], directory)
            self._save_config()
            self._log_result(f"✓ 从目录加载 {len(self.selected_images)} 张图片：{directory}")

    def _browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            # 添加到历史记录
            self._add_to_history(self.config["output_dirs"], directory)
            self._update_combo_box(self.combo_output_dir, self.config["output_dirs"])
            self.output_dir_var.set(directory)
            self._save_config()

    def _update_combo_box(self, combo: ctk.CTkComboBox, values: List[str]):
        """更新下拉框选项"""
        combo.configure(values=values)

    def _test_connection(self):
        """测试 API 连接"""
        api_url = self.entry_api_url.get().strip()
        if not api_url:
            messagebox.showwarning("警告", "请输入 API 地址")
            return

        from ai_describer import ImageDescriber
        describer = ImageDescriber(api_url=api_url)

        if describer.test_connection():
            messagebox.showinfo("成功", f"已连接到 API 服务：{api_url}")
            self._log_result(f"✓ API 连接成功：{api_url}")
        else:
            messagebox.showerror("失败", f"无法连接到 API 服务：{api_url}\n\n请确保 llama-server 已启动")
            self._log_result(f"✗ API 连接失败：{api_url}")

    def _start_processing(self):
        """开始处理"""
        # 验证输入
        if not self.selected_images:
            messagebox.showwarning("警告", "请先选择图片或目录")
            return

        api_url = self.entry_api_url.get().strip()
        if not api_url:
            messagebox.showwarning("警告", "请输入 API 地址")
            return

        # 测试连接
        from ai_describer import ImageDescriber
        describer_test = ImageDescriber(api_url=api_url)
        if not describer_test.test_connection():
            messagebox.showerror("错误", f"无法连接到 API 服务：{api_url}\n\n请确保 llama-server 已启动")
            return

        # 获取配置
        output_dir = self.output_dir_var.get().strip()
        if output_dir in ["默认与原图片同目录", ""]:
            output_dir = None

        api_key = self.entry_api_key.get().strip() or None
        n_ctx = int(self.entry_n_ctx.get() or "4096")
        temperature = float(self.entry_temperature.get() or "0.7")
        max_tokens = int(self.entry_max_tokens.get() or "512")
        duplicate_strategy = self.strategy_var.get()

        # 保存配置
        self.config["api_url"] = api_url
        self.config["api_key"] = api_key or ""
        self.config["n_ctx"] = n_ctx
        self.config["temperature"] = temperature
        self.config["max_tokens"] = max_tokens
        self.config["duplicate_strategy"] = duplicate_strategy
        self._save_config()

        # 创建处理器
        self.processor = ImageProcessor(
            api_url=api_url,
            output_dir=output_dir,
            n_ctx=n_ctx,
            temperature=temperature,
            max_tokens=max_tokens,
            duplicate_strategy=duplicate_strategy,
            api_key=api_key,
            verbose=False
        )

        # 更新 UI 状态
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_select.configure(state="disabled")
        self.progress_bar.set(0)

        # 创建并启动处理线程
        self.processing_thread = ProcessingThread(
            processor=self.processor,
            image_paths=self.selected_images,
            progress_callback=self._on_progress,
            result_callback=self._on_result
        )
        self.processing_thread.start()

        self._log_result(f"▶ 开始处理 {len(self.selected_images)} 张图片...")

    def _stop_processing(self):
        """停止处理"""
        if self.processor:
            self.processor.stop()
            self._log_result("⏹ 用户请求停止处理")

    def _on_progress(self, current: int, total: int, status: str, image_path: str):
        """进度回调（在后台线程中调用）"""
        # 使用 after 方法在主线程中更新 UI
        self.after(0, lambda: self._update_progress_ui(current, total, status, image_path))

    def _update_progress_ui(self, current: int, total: int, status: str, image_path: str):
        """更新进度 UI"""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)

        image_name = Path(image_path).name if image_path else ""
        self.lbl_progress.configure(text=f"{status} - {image_name} ({current}/{total})")

    def _on_result(self, status: str, image_path: str, data: dict):
        """结果回调（在后台线程中调用）"""
        self.after(0, lambda: self._update_result_ui(status, image_path, data))

    def _update_result_ui(self, status: str, image_path: str, data: dict):
        """更新结果 UI"""
        image_name = Path(image_path).name
        status_icon = {
            ProcessingStatus.COMPLETED: "✓",
            ProcessingStatus.SKIPPED: "⊘",
            ProcessingStatus.ERROR: "✗",
        }.get(status, "○")

        error_msg = ""
        if status == ProcessingStatus.ERROR and "error" in data:
            error_msg = f" - {data['error']}"

        json_path = data.get("json_path", "")
        self._log_result(f"{status_icon} {image_name} - {self._get_status_text(status)}{error_msg}")

        # 如果是最后一个，恢复按钮
        if self.progress_bar.get() >= 1.0:
            self._processing_finished()

    def _processing_finished(self):
        """处理完成"""
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.btn_select.configure(state="normal")
        self.lbl_progress.configure(text="处理完成")
        self._log_result("✓ 所有图片处理完成")

    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            ProcessingStatus.PENDING: "待处理",
            ProcessingStatus.PROCESSING: "处理中",
            ProcessingStatus.COMPLETED: "已完成",
            ProcessingStatus.SKIPPED: "已跳过",
            ProcessingStatus.ERROR: "出错"
        }
        return status_map.get(status, status)

    def _log_result(self, message: str):
        """记录结果到列表框"""
        self.result_text.configure(state="normal")
        self.result_text.insert("end", message + "\n")
        self.result_text.see("end")
        self.result_text.configure(state="disabled")

    def _clear_results(self):
        """清空结果列表"""
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.configure(state="disabled")
        self.selected_images = []
        self.lbl_selection_info.configure(text="未选择图片")
        self.progress_bar.set(0)
        self.lbl_progress.configure(text="就绪")

    def _open_json_file(self):
        """打开 JSON 文件"""
        # TODO: 获取选中的行并打开对应的 JSON
        messagebox.showinfo("提示", "请在结果列表中选中一项后使用此功能（开发中...）")

    def _edit_description(self):
        """编辑描述"""
        # TODO: 打开编辑对话框
        messagebox.showinfo("提示", "编辑功能开发中...")

    def _open_data_viewer(self):
        """打开数据查看器"""
        output_dir = self.output_dir_var.get().strip()
        if output_dir in ["默认与原图片同目录", ""]:
            output_dir = None
        open_data_viewer(self, output_dir)

    def on_closing(self):
        """窗口关闭事件"""
        if self.processor and self.processor._current_image:
            if messagebox.askokcancel("确认", "处理正在进行中，确定要退出吗？"):
                self.processor.stop()
                self.destroy()
        else:
            self.destroy()


def main():
    """主函数"""
    app = ImageDescriberApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
