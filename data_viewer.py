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
        super().__init__(parent, fg_color="#2a5a8a", corner_radius=8, height=24, **kwargs)
        
        self.text = text
        self.on_remove = on_remove
        
        self.label = ctk.CTkLabel(
            self,
            text=text,
            fg_color="transparent",
            text_color="white"
        )
        self.label.pack(side="left", padx=(6, 2), pady=2)
        
        self.btn_remove = ctk.CTkButton(
            self,
            text="×",
            width=18,
            height=18,
            fg_color="transparent",
            hover_color="#ff4444",
            text_color="white",
            command=self._on_remove,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_remove.pack(side="right", padx=(0, 2), pady=2)
    
    def _on_remove(self):
        self.on_remove(self.text)


class TagsEditor(ctk.CTkFrame):
    """标签编辑器组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        self.tags: List[str] = []
        self.tag_widgets: List[TagFrame] = []
        self.on_tags_changed = None
        
        self.tags_container = ctk.CTkScrollableFrame(
            self,
            height=60,
            fg_color="#1a1a1a",
            corner_radius=5
        )
        self.tags_container.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 3))
        
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 0))
        
        self.entry_new_tag = ctk.CTkEntry(
            input_frame,
            placeholder_text="输入标签后按回车添加...",
            height=26
        )
        self.entry_new_tag.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        self.btn_add = ctk.CTkButton(
            input_frame,
            text="+ 添加",
            width=60,
            height=26,
            command=self._add_tag_from_entry
        )
        self.btn_add.pack(side="left", padx=(0, 8))
        
        self.btn_batch = ctk.CTkButton(
            input_frame,
            text="📋 批量",
            width=60,
            height=26,
            fg_color="#444444",
            command=self._batch_add_tags
        )
        self.btn_batch.pack(side="left")
    
    def set_tags(self, tags: List[str]):
        self.tags = tags if tags else []
        self._refresh_tags()
    
    def get_tags(self) -> List[str]:
        return self.tags
    
    def _refresh_tags(self):
        for widget in self.tag_widgets:
            widget.destroy()
        self.tag_widgets.clear()
        
        for tag in self.tags:
            tag_frame = TagFrame(
                self.tags_container,
                text=tag,
                on_remove=self._remove_tag
            )
            tag_frame.pack(side="left", padx=3, pady=3)
            self.tag_widgets.append(tag_frame)
    
    def _add_tag_from_entry(self, event=None):
        text = self.entry_new_tag.get().strip()
        if text:
            new_tags = [t.strip() for t in re.split(r'[,\s;]+', text) if t.strip()]
            for tag in new_tags:
                if tag not in self.tags:
                    self.tags.append(tag)
            self._refresh_tags()
            self.entry_new_tag.delete(0, "end")
            if self.on_tags_changed:
                self.on_tags_changed()
    
    def _batch_add_tags(self):
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
        if tag_text in self.tags:
            self.tags.remove(tag_text)
            self._refresh_tags()
            if self.on_tags_changed:
                self.on_tags_changed()


class BatchTagDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("批量添加标签")
        self.geometry("400x300")
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()
        
        ctk.CTkLabel(
            self,
            text="请输入标签（支持逗号、空格、换行分隔）:",
            font=ctk.CTkFont(weight="bold")
        ).pack(padx=20, pady=(20, 10))
        
        self.txt_input = ctk.CTkTextbox(self, height=150)
        self.txt_input.pack(padx=20, pady=10, fill="both", expand=True)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(0, 20))
        
        ctk.CTkButton(btn_frame, text="取消", command=self.destroy, width=80).pack(side="right", padx=(10, 0))
        ctk.CTkButton(btn_frame, text="确定", command=self._confirm, width=80, fg_color="green").pack(side="right")
    
    def _confirm(self):
        self.result = self.txt_input.get("1.0", "end").strip()
        self.destroy()


class DataViewerWindow(ctk.CTkToplevel):
    def __init__(self, parent, json_dir: Optional[str] = None):
        super().__init__(parent)
        
        self.title("数据查看器 - SDXL 提示词")
        self.geometry("1600x950+100+100")  # 增大窗口
        self.minsize(1400, 850)
        
        self.json_dir = json_dir
        self.current_data: Optional[Dict] = None
        self.current_json_path: Optional[str] = None
        self.json_files_map: Dict[str, str] = {}
        self.selected_button: Optional[ctk.CTkButton] = None
        
        self._create_widgets()
        self._load_json_list()
    
    def _create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 左侧文件列表
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(10, 5), pady=10)
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # 目录选择
        dir_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        dir_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ctk.CTkLabel(dir_frame, text="JSON 目录:").pack(side="left")
        
        self.btn_change_dir = ctk.CTkButton(dir_frame, text="浏览", command=self._change_directory, width=60)
        self.btn_change_dir.pack(side="right")
        
        self.lbl_current_dir = ctk.CTkLabel(dir_frame, text=str(self.json_dir) if self.json_dir else "未设置", text_color="gray", anchor="w")
        self.lbl_current_dir.pack(side="left", padx=5, fill="x", expand=True)
        
        self.lbl_file_count = ctk.CTkLabel(left_frame, text="JSON 文件列表:", font=ctk.CTkFont(weight="bold"))
        self.lbl_file_count.grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        self.list_frame = ctk.CTkScrollableFrame(left_frame, width=280)
        self.list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        self.btn_refresh = ctk.CTkButton(left_frame, text="刷新", command=self._load_json_list, width=80)
        self.btn_refresh.grid(row=3, column=0, pady=(0, 10))
        
        # 右侧数据显示 - 添加滚动容器
        right_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        right_scroll.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 10), pady=10)
        right_scroll.grid_columnconfigure(0, weight=1)
        
        # 在滚动容器内创建一个容器来放置所有内容
        right_frame = ctk.CTkFrame(right_scroll, fg_color="transparent")
        right_frame.grid(row=0, column=0, sticky="ew")
        right_frame.grid_columnconfigure(1, weight=1)
        
        # 使用 pack 布局简化
        # 标题
        ctk.CTkLabel(right_frame, text="数据详情:", font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", pady=(0, 10))
        
        # 图片信息容器
        info_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))
        info_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(info_frame, text="图片:", width=60).grid(row=0, column=0, sticky="w", pady=2)
        self.lbl_image_path = ctk.CTkLabel(info_frame, text="-", anchor="w", wraplength=600, text_color="#4da6ff", cursor="hand2")
        self.lbl_image_path.grid(row=0, column=1, sticky="ew", pady=2)
        self.lbl_image_path.bind("<Button-1>", lambda e: self._open_image_from_label())
        ctk.CTkLabel(info_frame, text="← 点击打开图片", text_color="gray", font=ctk.CTkFont(size=11)).grid(row=0, column=2, sticky="w", padx=(10, 0), pady=2)
        
        ctk.CTkLabel(info_frame, text="尺寸:", width=60).grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_image_size = ctk.CTkLabel(info_frame, text="-", anchor="w")
        self.lbl_image_size.grid(row=1, column=1, sticky="w", pady=2)
        
        ctk.CTkLabel(info_frame, text="大小:", width=60).grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_image_filesize = ctk.CTkLabel(info_frame, text="-", anchor="w")
        self.lbl_image_filesize.grid(row=2, column=1, sticky="w", pady=2)
        
        ctk.CTkLabel(info_frame, text="MD5:", width=60).grid(row=3, column=0, sticky="w", pady=2)
        self.lbl_image_md5 = ctk.CTkLabel(info_frame, text="-", anchor="w")
        self.lbl_image_md5.grid(row=3, column=1, sticky="w", pady=2)
        
        self.lbl_compressed = ctk.CTkLabel(info_frame, text="", text_color="#ffa500", font=ctk.CTkFont(weight="bold"))
        self.lbl_compressed.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)
        
        # 描述
        desc_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        desc_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(desc_frame, text="描述:", width=60).pack(anchor="w")
        
        self.txt_description = ctk.CTkTextbox(right_frame, height=120, state="disabled", wrap="word")
        self.txt_description.pack(fill="x", pady=(0, 10), padx=(0, 20))
        
        # SDXL 提示词 - 最重要，放在前面，占据最大空间
        sdxl_container = ctk.CTkFrame(right_frame, fg_color="#1a1a2e")
        sdxl_container.pack(fill="both", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(sdxl_container, text="📸 SDXL 提示词", font=ctk.CTkFont(weight="bold", size=13), text_color="#4da6ff").pack(anchor="w", padx=10, pady=(10, 5))
        
        # 正向提示词 - 增加高度到 250
        pos_frame = ctk.CTkFrame(sdxl_container, fg_color="transparent")
        pos_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(pos_frame, text="✅ 正向:", width=60, text_color="#44ff44").pack(side="left")
        self.txt_positive = ctk.CTkTextbox(pos_frame, height=250, wrap="word", fg_color="#0d1117")
        self.txt_positive.pack(fill="both", expand=True, padx=(0, 10))
        self.txt_positive.configure(state="disabled")
        
        # 反向提示词 - 增加高度到 150
        neg_frame = ctk.CTkFrame(sdxl_container, fg_color="transparent")
        neg_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(neg_frame, text="❌ 反向:", width=60, text_color="#ff4444").pack(side="left")
        self.txt_negative = ctk.CTkTextbox(neg_frame, height=150, wrap="word", fg_color="#0d1117")
        self.txt_negative.pack(fill="both", expand=True, padx=(0, 10))
        self.txt_negative.configure(state="disabled")
        
        # 复制按钮 - 放在提示词容器底部
        copy_frame = ctk.CTkFrame(sdxl_container, fg_color="transparent")
        copy_frame.pack(anchor="e", padx=10, pady=(0, 10))
        self.btn_copy_positive = ctk.CTkButton(copy_frame, text="📋 复制正向", command=self._copy_positive, width=100, height=30)
        self.btn_copy_positive.pack(side="left", padx=(0, 10))
        self.btn_copy_negative = ctk.CTkButton(copy_frame, text="📋 复制反向", command=self._copy_negative, width=100, height=30)
        self.btn_copy_negative.pack(side="left")
        
        # Tags - 放在后面，减小空间
        tags_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        tags_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(tags_frame, text="Tags:", width=60).pack(anchor="w")
        
        self.tags_editor = TagsEditor(right_frame)
        self.tags_editor.pack(fill="x", pady=(0, 10))
        self.tags_editor.on_tags_changed = self._on_tags_changed
        
        # 底部按钮
        btn_frame = ctk.CTkFrame(right_frame)
        btn_frame.pack(anchor="se", pady=(10, 0))
        self.btn_save = ctk.CTkButton(btn_frame, text="💾 保存", command=self._save_changes, width=100, fg_color="green")
        self.btn_save.pack(side="right", padx=(10, 5), pady=10)
        self.btn_open_image = ctk.CTkButton(btn_frame, text="🖼️ 打开图片", command=self._open_image, width=100)
        self.btn_open_image.pack(side="right", padx=(10, 5), pady=10)
        self.btn_open_json = ctk.CTkButton(btn_frame, text="📄 打开 JSON", command=self._open_json, width=100)
        self.btn_open_json.pack(side="right", padx=(10, 5), pady=10)
    
    def _change_directory(self):
        directory = filedialog.askdirectory(title="选择 JSON 文件目录")
        if directory:
            self.json_dir = directory
            self.lbl_current_dir.configure(text=directory)
            self._load_json_list()
    
    def _load_json_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.json_files_map.clear()
        self.selected_button = None
        
        if not self.json_dir:
            self.json_dir = str(Path(__file__).parent / "output")
            self.lbl_current_dir.configure(text=self.json_dir)
        
        json_path = Path(self.json_dir)
        if not json_path.exists():
            ctk.CTkLabel(self.list_frame, text="目录不存在", text_color="red").grid(row=0, column=0, sticky="ew", pady=5)
            return
        
        json_files = list(json_path.glob("*.json"))
        if not json_files:
            ctk.CTkLabel(self.list_frame, text="未找到 JSON 文件").grid(row=0, column=0, sticky="ew", pady=5)
            return
        
        self.lbl_file_count.configure(text=f"JSON 文件列表 ({len(json_files)} 个):")
        
        for idx, jf in enumerate(sorted(json_files, key=lambda x: x.name.lower())):
            display_name = self._get_display_name(str(jf))
            self.json_files_map[display_name] = str(jf)
            btn = ctk.CTkButton(self.list_frame, text=display_name, command=lambda name=display_name: self._on_file_select(name), anchor="w", height=32, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")
            btn.grid(row=idx, column=0, sticky="ew", pady=2)
    
    def _get_display_name(self, json_path: str) -> str:
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
        json_path = self.json_files_map.get(display_name)
        if json_path:
            if self.selected_button:
                self.selected_button.configure(fg_color="#3a3a3a", hover_color="#4a4a4a")
            for widget in self.list_frame.winfo_children():
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") == display_name:
                    widget.configure(fg_color="#2a5a8a", hover_color="#3a6a9a")
                    self.selected_button = widget
                    break
            self._load_json_data(json_path)
    
    def _load_json_data(self, json_path: str):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_data = data
            self.current_json_path = json_path
            
            self.lbl_image_path.configure(text=data.get("source_path", "-"))
            self.lbl_image_size.configure(text=f"{data.get('width', '-')}x{data.get('height', '-')}")
            self.lbl_image_filesize.configure(text=f"{data.get('size_bytes', 0):,} 字节")
            self.lbl_image_md5.configure(text=data.get("md5", "-"))
            
            compressed = data.get("compressed", False)
            if compressed:
                self.lbl_compressed.configure(text="⚠️ 此图片已压缩处理（原图过大）")
            else:
                self.lbl_compressed.configure(text="")
            
            self.txt_description.configure(state="normal")
            self.txt_description.delete("1.0", "end")
            self.txt_description.insert("1.0", data.get("description", ""))
            self.txt_description.configure(state="disabled")
            
            tags = data.get("tags", [])
            if hasattr(self, 'tags_editor') and self.tags_editor:
                self.tags_editor.set_tags(tags)
            
            if hasattr(self, 'txt_positive') and self.txt_positive:
                self.txt_positive.configure(state="normal")
                self.txt_positive.delete("1.0", "end")
                if data.get("positive_prompt"):
                    self.txt_positive.insert("1.0", data.get("positive_prompt", ""))
                else:
                    self.txt_positive.insert("1.0", "（未生成，请重新处理图片）")
                self.txt_positive.configure(state="disabled")
            
            if hasattr(self, 'txt_negative') and self.txt_negative:
                self.txt_negative.configure(state="normal")
                self.txt_negative.delete("1.0", "end")
                if data.get("negative_prompt"):
                    self.txt_negative.insert("1.0", data.get("negative_prompt", ""))
                else:
                    self.txt_negative.insert("1.0", "（未生成，请重新处理图片）")
                self.txt_negative.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载 JSON 失败：{e}")
            self.current_data = None
            self.current_json_path = None
    
    def _on_tags_changed(self):
        pass
    
    def _save_changes(self):
        if not self.current_data or not self.current_json_path:
            messagebox.showwarning("警告", "没有可保存的数据")
            return
        try:
            tags = self.tags_editor.get_tags()
            self.current_data["tags"] = tags
            from datetime import datetime
            self.current_data["updated_at"] = datetime.now().isoformat()
            with open(self.current_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "已保存")
            self._load_json_list()
            if self.current_data:
                display_name = f"{self.current_data.get('original_filename', '')} ({self.current_data.get('md5', '')[:8]})"
                self._on_file_select(display_name)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")
    
    def _open_image_from_label(self):
        self._open_image()
    
    def _open_image(self):
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
            messagebox.showwarning("警告", f"图片文件不存在：\n{image_path}\n\n可能已被移动或删除。")
    
    def _open_json(self):
        if not self.current_json_path:
            messagebox.showwarning("警告", "请先选择一条数据")
            return
        if Path(self.current_json_path).exists():
            import os
            os.startfile(self.current_json_path)
        else:
            messagebox.showwarning("警告", "JSON 文件不存在")
    
    def _copy_positive(self):
        text = self.txt_positive.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("成功", "正向提示词已复制到剪贴板")
        else:
            messagebox.showwarning("提示", "没有可复制的正向提示词")
    
    def _copy_negative(self):
        text = self.txt_negative.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("成功", "反向提示词已复制到剪贴板")
        else:
            messagebox.showwarning("提示", "没有可复制的反向提示词")


def open_data_viewer(parent, json_dir: Optional[str] = None):
    viewer = DataViewerWindow(parent, json_dir)
    viewer.transient(parent)
    viewer.lift()
    viewer.focus_force()
    viewer.grab_set()
