#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据查看和编辑模块
用于查看生成的 JSON 数据和编辑 tags
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import json
import re
from typing import Optional, List, Dict


class TagFrame(ctk.CTkFrame):
    """单个标签组件"""
    
    def __init__(self, parent, text: str, on_remove, **kwargs):
        super().__init__(parent, fg_color="#2a5a8a", corner_radius=10, height=30, **kwargs)
        
        self.text = text
        self.on_remove = on_remove
        
        # 标签文本
        self.label = ctk.CTkLabel(
            self,
            text=text,
            fg_color="transparent",
            text_color="white"
        )
        self.label.pack(side="left", padx=(8, 4), pady=4)
        
        # 删除按钮
        self.btn_remove = ctk.CTkButton(
            self,
            text="×",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color="#ff4444",
            text_color="white",
            command=self._on_remove,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.btn_remove.pack(side="right", padx=(0, 4), pady=4)
    
    def _on_remove(self):
        """删除标签"""
        self.on_remove(self.text)


class TagsEditor(ctk.CTkFrame):
    """标签编辑器组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        self.tags: List[str] = []
        self.tag_widgets: List[TagFrame] = []
        self.on_tags_changed = None
        
        # 标签容器（可滚动）
        self.tags_container = ctk.CTkScrollableFrame(
            self,
            height=120,
            fg_color="#1a1a1a",
            corner_radius=5
        )
        self.tags_container.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # 输入行
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # 输入框
        self.entry_new_tag = ctk.CTkEntry(
            input_frame,
            placeholder_text="输入标签后按回车添加...",
            height=30
        )
        self.entry_new_tag.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # 添加按钮
        self.btn_add = ctk.CTkButton(
            input_frame,
            text="+ 添加",
            width=80,
            height=30,
            command=self._add_tag_from_entry
        )
        self.btn_add.pack(side="left", padx=(0, 10))
        
        # 批量输入
        self.btn_batch = ctk.CTkButton(
            input_frame,
            text="📋 批量输入",
            width=100,
            height=30,
            fg_color="#444444",
            command=self._batch_add_tags
        )
        self.btn_batch.pack(side="left")
    
    def set_tags(self, tags: List[str]):
        """设置标签列表"""
        self.tags = tags if tags else []
        self._refresh_tags()
    
    def get_tags(self) -> List[str]:
        """获取标签列表"""
        return self.tags
    
    def _refresh_tags(self):
        """刷新标签显示"""
        # 清空现有标签
        for widget in self.tag_widgets:
            widget.destroy()
        self.tag_widgets.clear()
        
        # 重新创建标签（使用 pack 实现自动换行）
        for tag in self.tags:
            tag_frame = TagFrame(
                self.tags_container,
                text=tag,
                on_remove=self._remove_tag
            )
            tag_frame.pack(side="left", padx=3, pady=3)
            self.tag_widgets.append(tag_frame)
    
    def _add_tag_from_entry(self, event=None):
        """从输入框添加标签"""
        text = self.entry_new_tag.get().strip()
        if text:
            # 支持一次输入多个（逗号、空格分隔）
            new_tags = [t.strip() for t in re.split(r'[,\s;]+', text) if t.strip()]
            for tag in new_tags:
                if tag not in self.tags:
                    self.tags.append(tag)
            self._refresh_tags()
            self.entry_new_tag.delete(0, "end")
            
            if self.on_tags_changed:
                self.on_tags_changed()
    
    def _batch_add_tags(self):
        """批量添加标签"""
        dialog = BatchTagDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            new_tags = [t.strip() for t in re.split(r'[,\s;\n]+', dialog.result) if t.strip()]
            for tag in new_tags:
                if tag not in self.tags:
                    self.tags.append(tag)
            self._refresh_tags()
            
            if self.on_tags_changed:
                self.on_tags_changed()
    
    def _remove_tag(self, tag_text: str):
        """删除标签"""
        if tag_text in self.tags:
            self.tags.remove(tag_text)
            self._refresh_tags()
            
            if self.on_tags_changed:
                self.on_tags_changed()


class BatchTagDialog(ctk.CTkToplevel):
    """批量输入标签对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("批量添加标签")
        self.geometry("400x300")
        self.resizable(False, False)
        
        self.result = None
        
        # 居中显示
        self.transient(parent)
        self.grab_set()
        
        # 内容
        ctk.CTkLabel(
            self,
            text="请输入标签（支持逗号、空格、换行分隔）:",
            font=ctk.CTkFont(weight="bold")
        ).pack(padx=20, pady=(20, 10))
        
        self.txt_input = ctk.CTkTextbox(self, height=150)
        self.txt_input.pack(padx=20, pady=10, fill="both", expand=True)
        
        # 按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            btn_frame,
            text="取消",
            command=self.destroy,
            width=80
        ).pack(side="right", padx=(10, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="确定",
            command=self._confirm,
            width=80,
            fg_color="green"
        ).pack(side="right")
    
    def _confirm(self):
        """确认输入"""
        self.result = self.txt_input.get("1.0", "end").strip()
        self.destroy()


class DataViewerWindow(ctk.CTkToplevel):
    """数据查看和编辑窗口"""
    
    def __init__(self, parent, json_dir: Optional[str] = None):
        super().__init__(parent)
        
        self.title("数据查看器")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        self.json_dir = json_dir
        self.current_data: Optional[Dict] = None
        self.current_json_path: Optional[str] = None
        self.json_files_map: Dict[str, str] = {}  # 显示名 -> 实际路径
        self.selected_button: Optional[ctk.CTkButton] = None
        
        self._create_widgets()
        self._load_json_list()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 配置网格布局
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 左侧：文件列表
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(10, 5), pady=10)
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # 目录选择
        dir_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        dir_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ctk.CTkLabel(dir_frame, text="JSON 目录:").pack(side="left")
        
        self.btn_change_dir = ctk.CTkButton(
            dir_frame,
            text="浏览",
            command=self._change_directory,
            width=60
        )
        self.btn_change_dir.pack(side="right")
        
        self.lbl_current_dir = ctk.CTkLabel(
            dir_frame,
            text=str(self.json_dir) if self.json_dir else "未设置",
            text_color="gray",
            anchor="w"
        )
        self.lbl_current_dir.pack(side="left", padx=5, fill="x", expand=True)
        
        # 文件数量标签
        self.lbl_file_count = ctk.CTkLabel(
            left_frame,
            text="JSON 文件列表:",
            font=ctk.CTkFont(weight="bold")
        )
        self.lbl_file_count.grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        # JSON 文件列表（可滚动）
        self.list_frame = ctk.CTkScrollableFrame(left_frame, width=280)
        self.list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        # 刷新按钮
        self.btn_refresh = ctk.CTkButton(
            left_frame,
            text="刷新",
            command=self._load_json_list,
            width=80
        )
        self.btn_refresh.grid(row=3, column=0, pady=(0, 10))
        
        # 右侧：数据显示和编辑
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 10), pady=10)
        right_frame.grid_columnconfigure(1, weight=1)
        right_frame.grid_rowconfigure(4, weight=1)
        
        # 标题
        ctk.CTkLabel(
            right_frame,
            text="数据详情:",
            font=ctk.CTkFont(weight="bold", size=14)
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # 图片信息
        info_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(info_frame, text="图片:", width=60).grid(row=0, column=0, sticky="w", pady=2)
        
        # 图片路径标签（可点击）
        self.lbl_image_path = ctk.CTkLabel(
            info_frame,
            text="-",
            anchor="w",
            wraplength=600,
            text_color="#4da6ff",
            cursor="hand2"
        )
        self.lbl_image_path.grid(row=0, column=1, sticky="ew", pady=2)
        self.lbl_image_path.bind("<Button-1>", lambda e: self._open_image_from_label())
        
        # 提示标签
        ctk.CTkLabel(
            info_frame,
            text="← 点击打开图片",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=2, sticky="w", padx=(10, 0), pady=2)

        ctk.CTkLabel(info_frame, text="尺寸:", width=60).grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_image_size = ctk.CTkLabel(info_frame, text="-", anchor="w")
        self.lbl_image_size.grid(row=1, column=1, sticky="w", pady=2)

        ctk.CTkLabel(info_frame, text="大小:", width=60).grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_image_filesize = ctk.CTkLabel(info_frame, text="-", anchor="w")
        self.lbl_image_filesize.grid(row=2, column=1, sticky="w", pady=2)

        ctk.CTkLabel(info_frame, text="MD5:", width=60).grid(row=3, column=0, sticky="w", pady=2)
        self.lbl_image_md5 = ctk.CTkLabel(info_frame, text="-", anchor="w")
        self.lbl_image_md5.grid(row=3, column=1, sticky="w", pady=2)

        # 压缩标记
        self.lbl_compressed = ctk.CTkLabel(
            info_frame,
            text="",
            text_color="#ffa500",
            font=ctk.CTkFont(weight="bold")
        )
        self.lbl_compressed.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)
        
        # 描述
        desc_label_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        desc_label_frame.grid(row=2, column=0, sticky="nw", pady=(0, 5))
        
        ctk.CTkLabel(desc_label_frame, text="描述:", width=60).pack(anchor="w")
        
        self.txt_description = ctk.CTkTextbox(
            right_frame,
            height=150,
            state="disabled",
            wrap="word"
        )
        self.txt_description.grid(row=2, column=1, sticky="ew", pady=(0, 10), padx=(0, 20))
        
        # Tags 编辑器
        ctk.CTkLabel(right_frame, text="Tags:", width=60).grid(row=3, column=0, sticky="nw", pady=(0, 5))
        
        self.tags_editor = TagsEditor(right_frame)
        self.tags_editor.grid(row=3, column=1, sticky="ew", pady=(0, 10))
        self.tags_editor.on_tags_changed = self._on_tags_changed
        
        # 操作按钮
        btn_frame = ctk.CTkFrame(right_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="se")
        
        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 保存",
            command=self._save_changes,
            width=100,
            fg_color="green"
        )
        self.btn_save.pack(side="right", padx=(10, 5), pady=10)
        
        self.btn_open_image = ctk.CTkButton(
            btn_frame,
            text="🖼️ 打开图片",
            command=self._open_image,
            width=100
        )
        self.btn_open_image.pack(side="right", padx=(10, 5), pady=10)
        
        self.btn_open_json = ctk.CTkButton(
            btn_frame,
            text="📄 打开 JSON",
            command=self._open_json,
            width=100
        )
        self.btn_open_json.pack(side="right", padx=(10, 5), pady=10)
    
    def _change_directory(self):
        """更改 JSON 目录"""
        directory = filedialog.askdirectory(title="选择 JSON 文件目录")
        if directory:
            self.json_dir = directory
            self.lbl_current_dir.configure(text=directory)
            self._load_json_list()
    
    def _load_json_list(self):
        """加载 JSON 文件列表"""
        # 清空列表
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.json_files_map.clear()
        
        # 重置选中状态
        self.selected_button = None
        
        if not self.json_dir:
            # 默认使用 output 目录
            self.json_dir = str(Path(__file__).parent / "output")
            self.lbl_current_dir.configure(text=self.json_dir)
        
        json_path = Path(self.json_dir)
        if not json_path.exists():
            label = ctk.CTkLabel(self.list_frame, text="目录不存在", text_color="red")
            label.grid(row=0, column=0, sticky="ew", pady=5)
            return
        
        json_files = list(json_path.glob("*.json"))
        if not json_files:
            label = ctk.CTkLabel(self.list_frame, text="未找到 JSON 文件")
            label.grid(row=0, column=0, sticky="ew", pady=5)
            return
        
        # 更新文件数量
        self.lbl_file_count.configure(text=f"JSON 文件列表 ({len(json_files)} 个):")
        
        # 加载所有 JSON 文件
        for idx, jf in enumerate(sorted(json_files, key=lambda x: x.name.lower())):
            display_name = self._get_display_name(str(jf))
            self.json_files_map[display_name] = str(jf)

            # 创建按钮（默认非选中状态）
            btn = ctk.CTkButton(
                self.list_frame,
                text=display_name,
                command=lambda name=display_name: self._on_file_select(name),
                anchor="w",
                height=32,
                corner_radius=8,
                fg_color="#3a3a3a",  # 默认非选中颜色
                hover_color="#4a4a4a"
            )
            btn.grid(row=idx, column=0, sticky="ew", pady=2)
    
    def _get_display_name(self, json_path: str) -> str:
        """获取显示名称"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            source_path = data.get("source_path", "")
            md5 = data.get("md5", "")
            original_filename = data.get("original_filename", "")
            
            if original_filename and md5:
                return f"{original_filename} ({md5[:8]})"
            elif source_path and md5:
                return f"{Path(source_path).name} ({md5[:8]})"
        except:
            pass
        
        return Path(json_path).name
    
    def _on_file_select(self, display_name: str):
        """文件选择事件"""
        json_path = self.json_files_map.get(display_name)
        if json_path:
            # 更新按钮样式 - 取消之前的选中
            if self.selected_button:
                self.selected_button.configure(fg_color="#3a3a3a", hover_color="#4a4a4a")
            
            # 找到当前按钮并高亮
            for widget in self.list_frame.winfo_children():
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") == display_name:
                    widget.configure(fg_color="#2a5a8a", hover_color="#3a6a9a")
                    self.selected_button = widget
                    break
            
            self._load_json_data(json_path)
    
    def _load_json_data(self, json_path: str):
        """加载 JSON 数据"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_data = data
            self.current_json_path = json_path
            
            # 显示图片信息
            self.lbl_image_path.configure(text=data.get("source_path", "-"))
            self.lbl_image_size.configure(text=f"{data.get('width', '-')}x{data.get('height', '-')}")
            self.lbl_image_filesize.configure(text=f"{data.get('size_bytes', 0):,} 字节")
            self.lbl_image_md5.configure(text=data.get("md5", "-"))

            # 显示压缩标记
            compressed = data.get("compressed", False)
            if compressed:
                self.lbl_compressed.configure(text="⚠️ 此图片已压缩处理（原图过大）")
            else:
                self.lbl_compressed.configure(text="")
            
            # 显示描述
            self.txt_description.configure(state="normal")
            self.txt_description.delete("1.0", "end")
            self.txt_description.insert("1.0", data.get("description", ""))
            self.txt_description.configure(state="disabled")
            
            # 加载 tags
            tags = data.get("tags", [])
            self.tags_editor.set_tags(tags)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载 JSON 失败：{e}")
            self.current_data = None
            self.current_json_path = None
    
    def _on_tags_changed(self):
        """Tags 变化时的回调"""
        pass  # 可以在这里添加自动保存逻辑
    
    def _save_changes(self):
        """保存更改"""
        if not self.current_data or not self.current_json_path:
            messagebox.showwarning("警告", "没有可保存的数据")
            return
        
        try:
            # 获取 tags
            tags = self.tags_editor.get_tags()
            
            # 更新数据
            self.current_data["tags"] = tags
            
            # 保存
            from datetime import datetime
            self.current_data["updated_at"] = datetime.now().isoformat()
            
            with open(self.current_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "已保存")
            
            # 刷新列表显示
            self._load_json_list()
            
            # 重新选中当前项
            if self.current_data:
                original_filename = self.current_data.get("original_filename", "")
                md5 = self.current_data.get("md5", "")
                if original_filename and md5:
                    display_name = f"{original_filename} ({md5[:8]})"
                    self._on_file_select(display_name)
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")

    def _open_image_from_label(self):
        """从图片路径标签打开图片"""
        self._open_image()

    def _open_image(self):
        """打开图片"""
        if not self.current_data:
            messagebox.showwarning("警告", "请先选择一条数据")
            return

        image_path = self.current_data.get("source_path")
        if not image_path:
            messagebox.showwarning("警告", "图片路径无效")
            return

        if Path(image_path).exists():
            import os
            os.startfile(image_path)
        else:
            # 图片不存在，给予提醒
            messagebox.showwarning(
                "警告",
                f"图片文件不存在：\n{image_path}\n\n"
                f"可能已被移动或删除。"
            )

    def _open_json(self):
        """打开 JSON 文件"""
        if not self.current_json_path:
            messagebox.showwarning("警告", "请先选择一条数据")
            return

        if Path(self.current_json_path).exists():
            import os
            os.startfile(self.current_json_path)
        else:
            messagebox.showwarning("警告", "JSON 文件不存在")


def open_data_viewer(parent, json_dir: Optional[str] = None):
    """打开数据查看器窗口"""
    viewer = DataViewerWindow(parent, json_dir)
    viewer.transient(parent)
    viewer.lift()
