#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows本地水印处理应用
支持文本和图片水印，批量处理，实时预览等功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance
import os
import json
import threading
from pathlib import Path
import sys

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("水印处理工具")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 初始化变量
        self.images = []  # 存储导入的图片信息
        self.current_image_index = 0
        self.watermark_settings = self.get_default_settings()
        self.preview_image = None
        self.watermark_position = (50, 50)  # 水印位置
        self.dragging = False
        
        # 创建界面
        self.create_widgets()
        self.load_last_settings()
        self.update_export_status()
        
    def show_help(self):
        """显示使用帮助"""
        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        help_window.transient(self.root)
        
        # 居中显示
        help_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 100,
            self.root.winfo_rooty() + 50
        ))
        
        # 创建滚动文本框
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                             font=('Arial', 10), padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        # 帮助内容
        help_text = """水印处理工具使用指南

操作步骤：

1. 导入图片
   - 点击"选择图片"选择单张或多张图片
   - 点击"选择文件夹"导入整个文件夹
   - 支持格式：JPEG, PNG, BMP, TIFF

2. 设置水印
   [文本水印]
   - 输入水印文字（支持中文）
   - 选择字体（推荐"微软雅黑"）
   - 调整大小、颜色、透明度
   - 可添加阴影或描边效果
   
   [图片水印]
   - 选择水印图片（建议PNG格式）
   - 调整缩放比例和透明度

3. 调整位置
   - 使用九宫格快速定位
   - 或直接在预览区拖拽水印
   - 可调整旋转角度

4. 配置导出
   - 选择输出格式（PNG/JPEG）
   - 选择输出文件夹（不能与原文件夹相同）
   - 设置文件命名规则

5. 开始处理
   - 点击"开始批量导出"按钮
   - 等待处理完成

使用技巧：
   - 实时预览：所有更改立即显示
   - 模板功能：保存常用设置
   - 拖拽定位：精确调整水印位置

注意事项：
   - 必须选择不同的输出文件夹
   - 中文显示方框请更换字体
   - PNG格式保持最佳质量

如有问题，请检查Python版本和Pillow库安装"""
        
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)  # 只读
        
        # 关闭按钮
        ttk.Button(help_window, text="关闭", 
                  command=help_window.destroy).pack(pady=10)
        
    def update_export_status(self):
        """更新导出状态提示"""
        if hasattr(self, 'status_label'):
            if not self.images:
                self.status_label.config(text="请先导入图片", foreground='orange')
                self.export_button.config(state='disabled')
            elif not self.output_folder_var.get():
                self.status_label.config(text="请选择输出文件夹", foreground='orange')
                self.export_button.config(state='disabled')
            else:
                self.status_label.config(text=f"准备导出 {len(self.images)} 张图片", foreground='green')
                self.export_button.config(state='normal')
        
    def get_default_settings(self):
        """获取默认水印设置"""
        return {
            'text': '水印文本',
            'font_family': '微软雅黑',
            'font_size': 36,
            'font_bold': False,
            'font_italic': False,
            'text_color': '#FFFFFF',
            'text_opacity': 80,
            'shadow': True,
            'stroke': True,
            'stroke_width': 2,
            'stroke_color': '#000000',
            'watermark_type': 'text',  # 'text' or 'image'
            'image_path': '',
            'image_opacity': 80,
            'image_scale': 100,
            'position_preset': 'bottom_right',
            'rotation': 0,
            'output_format': 'PNG',
            'jpeg_quality': 95,
            'output_folder': '',
            'naming_rule': 'suffix',  # 'original', 'prefix', 'suffix'
            'custom_prefix': 'wm_',
            'custom_suffix': '_watermarked'
        }
    
    def create_widgets(self):
        """创建主界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧面板 - 图片列表和控制
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # 右侧面板 - 预览和设置
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_left_panel(left_panel)
        self.create_right_panel(right_panel)
        
    def create_left_panel(self, parent):
        """创建左侧面板"""
        # 文件导入区域
        import_frame = ttk.LabelFrame(parent, text="图片导入", padding=10)
        import_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(import_frame, text="选择图片", 
                  command=self.select_images).pack(fill=tk.X, pady=2)
        ttk.Button(import_frame, text="选择文件夹", 
                  command=self.select_folder).pack(fill=tk.X, pady=2)
        
        button_row = ttk.Frame(import_frame)
        button_row.pack(fill=tk.X, pady=2)
        ttk.Button(button_row, text="清空列表", 
                  command=self.clear_images).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(button_row, text="帮助", width=6,
                  command=self.show_help).pack(side=tk.RIGHT)
        
        # 图片列表
        list_frame = ttk.LabelFrame(parent, text="图片列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建列表框和滚动条
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        
        scrollbar.config(command=self.image_listbox.yview)
        
        # 导出设置
        export_frame = ttk.LabelFrame(parent, text="导出设置", padding=10)
        export_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 输出格式
        ttk.Label(export_frame, text="输出格式:").pack(anchor=tk.W)
        format_frame = ttk.Frame(export_frame)
        format_frame.pack(fill=tk.X, pady=2)
        
        self.output_format_var = tk.StringVar(value=self.watermark_settings['output_format'])
        ttk.Radiobutton(format_frame, text="PNG", variable=self.output_format_var, 
                       value="PNG").pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="JPEG", variable=self.output_format_var, 
                       value="JPEG").pack(side=tk.LEFT)
        
        # JPEG质量
        ttk.Label(export_frame, text="JPEG质量:").pack(anchor=tk.W, pady=(10, 0))
        self.quality_var = tk.IntVar(value=self.watermark_settings['jpeg_quality'])
        quality_scale = ttk.Scale(export_frame, from_=1, to=100, 
                                 variable=self.quality_var, orient=tk.HORIZONTAL)
        quality_scale.pack(fill=tk.X, pady=2)
        
        quality_label = ttk.Label(export_frame, text="95")
        quality_label.pack(anchor=tk.W)
        
        def update_quality_label(val):
            quality_label.config(text=str(int(float(val))))
        quality_scale.config(command=update_quality_label)
        
        # 输出文件夹
        ttk.Label(export_frame, text="输出文件夹:").pack(anchor=tk.W, pady=(10, 0))
        folder_frame = ttk.Frame(export_frame)
        folder_frame.pack(fill=tk.X, pady=2)
        
        self.output_folder_var = tk.StringVar(value=self.watermark_settings['output_folder'])
        ttk.Entry(folder_frame, textvariable=self.output_folder_var, 
                 state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(folder_frame, text="选择", width=8,
                  command=self.select_output_folder).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 文件命名规则
        ttk.Label(export_frame, text="命名规则:").pack(anchor=tk.W, pady=(10, 0))
        self.naming_var = tk.StringVar(value=self.watermark_settings['naming_rule'])
        ttk.Radiobutton(export_frame, text="保留原名", variable=self.naming_var, 
                       value="original").pack(anchor=tk.W)
        ttk.Radiobutton(export_frame, text="添加前缀", variable=self.naming_var, 
                       value="prefix").pack(anchor=tk.W)
        ttk.Radiobutton(export_frame, text="添加后缀", variable=self.naming_var, 
                       value="suffix").pack(anchor=tk.W)
        
        # 自定义前缀/后缀
        self.prefix_var = tk.StringVar(value=self.watermark_settings['custom_prefix'])
        self.suffix_var = tk.StringVar(value=self.watermark_settings['custom_suffix'])
        
        prefix_frame = ttk.Frame(export_frame)
        prefix_frame.pack(fill=tk.X, pady=2)
        ttk.Label(prefix_frame, text="前缀:", width=6).pack(side=tk.LEFT)
        ttk.Entry(prefix_frame, textvariable=self.prefix_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        suffix_frame = ttk.Frame(export_frame)
        suffix_frame.pack(fill=tk.X, pady=2)
        ttk.Label(suffix_frame, text="后缀:", width=6).pack(side=tk.LEFT)
        ttk.Entry(suffix_frame, textvariable=self.suffix_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 导出按钮
        export_btn_frame = ttk.Frame(export_frame)
        export_btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.export_button = ttk.Button(export_btn_frame, text="开始批量导出", 
                                       command=self.export_images)
        self.export_button.pack(fill=tk.X, pady=5)
        
        # 状态提示
        self.status_label = ttk.Label(export_btn_frame, text="请先导入图片并设置水印", 
                                     foreground='gray', font=('Arial', 8))
        self.status_label.pack(pady=2)
    
    def create_right_panel(self, parent):
        """创建右侧面板"""
        # 预览区域
        preview_frame = ttk.LabelFrame(parent, text="预览", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', cursor='hand2')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind('<Button-1>', self.on_canvas_click)
        self.preview_canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.preview_canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
        # 水印设置区域
        settings_frame = ttk.LabelFrame(parent, text="水印设置", padding=10)
        settings_frame.pack(fill=tk.X)
        
        # 创建笔记本控件用于分页
        notebook = ttk.Notebook(settings_frame)
        notebook.pack(fill=tk.X, expand=True)
        
        # 文本水印页面
        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="文本水印")
        self.create_text_watermark_settings(text_frame)
        
        # 图片水印页面
        image_frame = ttk.Frame(notebook)
        notebook.add(image_frame, text="图片水印")
        self.create_image_watermark_settings(image_frame)
        
        # 位置和样式页面
        position_frame = ttk.Frame(notebook)
        notebook.add(position_frame, text="位置样式")
        self.create_position_settings(position_frame)
        
        # 模板管理页面
        template_frame = ttk.Frame(notebook)
        notebook.add(template_frame, text="模板管理")
        self.create_template_settings(template_frame)
        
    def create_text_watermark_settings(self, parent):
        """创建文本水印设置"""
        # 水印文本
        ttk.Label(parent, text="水印文本:").pack(anchor=tk.W, pady=(5, 0))
        self.text_var = tk.StringVar(value=self.watermark_settings['text'])
        text_entry = ttk.Entry(parent, textvariable=self.text_var)
        text_entry.pack(fill=tk.X, pady=2)
        text_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        
        # 字体设置
        font_frame = ttk.Frame(parent)
        font_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 字体族
        ttk.Label(font_frame, text="字体:").pack(anchor=tk.W)
        self.font_family_var = tk.StringVar(value=self.watermark_settings['font_family'])
        font_combo = ttk.Combobox(font_frame, textvariable=self.font_family_var, 
                                 values=['微软雅黑', '宋体', '黑体', '楷体', '仿宋',
                                        'Arial', 'Times New Roman', 'Courier New', 
                                        'Helvetica', 'Georgia', 'Verdana', 'Tahoma'])
        font_combo.pack(fill=tk.X, pady=2)
        font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # 字体大小
        size_frame = ttk.Frame(font_frame)
        size_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(size_frame, text="大小:", width=8).pack(side=tk.LEFT)
        self.font_size_var = tk.IntVar(value=self.watermark_settings['font_size'])
        size_scale = ttk.Scale(size_frame, from_=12, to=200, variable=self.font_size_var, 
                              orient=tk.HORIZONTAL, command=lambda v: self.update_preview())
        size_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        size_label = ttk.Label(size_frame, text="36", width=4)
        size_label.pack(side=tk.RIGHT)
        
        def update_size_label(val):
            size_label.config(text=str(int(float(val))))
        size_scale.config(command=lambda v: (update_size_label(v), self.update_preview()))
        
        # 字体样式
        style_frame = ttk.Frame(font_frame)
        style_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.font_bold_var = tk.BooleanVar(value=self.watermark_settings['font_bold'])
        self.font_italic_var = tk.BooleanVar(value=self.watermark_settings['font_italic'])
        
        ttk.Checkbutton(style_frame, text="粗体", variable=self.font_bold_var,
                       command=self.update_preview).pack(side=tk.LEFT)
        ttk.Checkbutton(style_frame, text="斜体", variable=self.font_italic_var,
                       command=self.update_preview).pack(side=tk.LEFT, padx=(10, 0))
        
        # 颜色设置
        color_frame = ttk.Frame(parent)
        color_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(color_frame, text="文字颜色:").pack(anchor=tk.W)
        color_button_frame = ttk.Frame(color_frame)
        color_button_frame.pack(fill=tk.X, pady=2)
        
        self.text_color_var = tk.StringVar(value=self.watermark_settings['text_color'])
        self.color_button = tk.Button(color_button_frame, text="选择颜色", 
                                     bg=self.text_color_var.get(), width=12,
                                     command=self.choose_text_color)
        self.color_button.pack(side=tk.LEFT)
        
        # 透明度
        ttk.Label(color_frame, text="透明度:").pack(anchor=tk.W, pady=(10, 0))
        self.text_opacity_var = tk.IntVar(value=self.watermark_settings['text_opacity'])
        opacity_scale = ttk.Scale(color_frame, from_=0, to=100, variable=self.text_opacity_var,
                                 orient=tk.HORIZONTAL, command=lambda v: self.update_preview())
        opacity_scale.pack(fill=tk.X, pady=2)
        
        # 效果设置
        effect_frame = ttk.Frame(parent)
        effect_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.shadow_var = tk.BooleanVar(value=self.watermark_settings['shadow'])
        self.stroke_var = tk.BooleanVar(value=self.watermark_settings['stroke'])
        
        ttk.Checkbutton(effect_frame, text="阴影", variable=self.shadow_var,
                       command=self.update_preview).pack(anchor=tk.W)
        ttk.Checkbutton(effect_frame, text="描边", variable=self.stroke_var,
                       command=self.update_preview).pack(anchor=tk.W)
    
    def create_image_watermark_settings(self, parent):
        """创建图片水印设置"""
        # 选择水印图片
        ttk.Label(parent, text="水印图片:").pack(anchor=tk.W, pady=(5, 0))
        image_frame = ttk.Frame(parent)
        image_frame.pack(fill=tk.X, pady=2)
        
        self.watermark_image_var = tk.StringVar(value=self.watermark_settings['image_path'])
        ttk.Entry(image_frame, textvariable=self.watermark_image_var, 
                 state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(image_frame, text="选择", width=8,
                  command=self.select_watermark_image).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 图片缩放
        ttk.Label(parent, text="缩放比例:").pack(anchor=tk.W, pady=(10, 0))
        self.image_scale_var = tk.IntVar(value=self.watermark_settings['image_scale'])
        scale_frame = ttk.Frame(parent)
        scale_frame.pack(fill=tk.X, pady=2)
        
        scale_scale = ttk.Scale(scale_frame, from_=10, to=200, variable=self.image_scale_var,
                               orient=tk.HORIZONTAL, command=lambda v: self.update_preview())
        scale_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scale_label = ttk.Label(scale_frame, text="100%", width=6)
        scale_label.pack(side=tk.RIGHT)
        
        def update_scale_label(val):
            scale_label.config(text=f"{int(float(val))}%")
        scale_scale.config(command=lambda v: (update_scale_label(v), self.update_preview()))
        
        # 图片透明度
        ttk.Label(parent, text="透明度:").pack(anchor=tk.W, pady=(10, 0))
        self.image_opacity_var = tk.IntVar(value=self.watermark_settings['image_opacity'])
        opacity_scale = ttk.Scale(parent, from_=0, to=100, variable=self.image_opacity_var,
                                 orient=tk.HORIZONTAL, command=lambda v: self.update_preview())
        opacity_scale.pack(fill=tk.X, pady=2)
        
    def create_position_settings(self, parent):
        """创建位置设置"""
        # 预设位置
        ttk.Label(parent, text="预设位置:").pack(anchor=tk.W, pady=(5, 0))
        
        position_frame = ttk.Frame(parent)
        position_frame.pack(fill=tk.X, pady=5)
        
        self.position_var = tk.StringVar(value=self.watermark_settings['position_preset'])
        
        # 创建九宫格按钮
        positions = [
            ('左上', 'top_left'), ('上中', 'top_center'), ('右上', 'top_right'),
            ('左中', 'middle_left'), ('正中', 'center'), ('右中', 'middle_right'),
            ('左下', 'bottom_left'), ('下中', 'bottom_center'), ('右下', 'bottom_right')
        ]
        
        for i, (text, value) in enumerate(positions):
            row, col = divmod(i, 3)
            btn = ttk.Radiobutton(position_frame, text=text, variable=self.position_var,
                                 value=value, command=self.apply_position_preset)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
        
        # 配置列权重
        for i in range(3):
            position_frame.columnconfigure(i, weight=1)
        
        # 旋转角度
        ttk.Label(parent, text="旋转角度:").pack(anchor=tk.W, pady=(15, 0))
        self.rotation_var = tk.IntVar(value=self.watermark_settings['rotation'])
        rotation_frame = ttk.Frame(parent)
        rotation_frame.pack(fill=tk.X, pady=2)
        
        rotation_scale = ttk.Scale(rotation_frame, from_=-180, to=180, variable=self.rotation_var,
                                  orient=tk.HORIZONTAL, command=lambda v: self.update_preview())
        rotation_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        rotation_label = ttk.Label(rotation_frame, text="0°", width=6)
        rotation_label.pack(side=tk.RIGHT)
        
        def update_rotation_label(val):
            rotation_label.config(text=f"{int(float(val))}°")
        rotation_scale.config(command=lambda v: (update_rotation_label(v), self.update_preview()))
        
        # 手动位置提示
        ttk.Label(parent, text="提示: 可在预览区域直接拖拽水印位置", 
                 foreground='gray').pack(anchor=tk.W, pady=(15, 0))
        
    def create_template_settings(self, parent):
        """创建模板管理设置"""
        # 保存模板
        save_frame = ttk.Frame(parent)
        save_frame.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(save_frame, text="模板名称:").pack(anchor=tk.W)
        self.template_name_var = tk.StringVar()
        name_frame = ttk.Frame(save_frame)
        name_frame.pack(fill=tk.X, pady=2)
        
        ttk.Entry(name_frame, textvariable=self.template_name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(name_frame, text="保存", width=8,
                  command=self.save_template).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 模板列表
        ttk.Label(parent, text="已保存模板:").pack(anchor=tk.W, pady=(10, 0))
        
        template_frame = ttk.Frame(parent)
        template_frame.pack(fill=tk.X, pady=2)
        
        self.template_listbox = tk.Listbox(template_frame, height=6)
        self.template_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        template_btn_frame = ttk.Frame(template_frame)
        template_btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        ttk.Button(template_btn_frame, text="加载", width=8,
                  command=self.load_template).pack(pady=2)
        ttk.Button(template_btn_frame, text="删除", width=8,
                  command=self.delete_template).pack(pady=2)
        
        self.load_templates()
    
    # 文件处理方法
    def select_images(self):
        """选择图片文件"""
        filetypes = [
            ('图片文件', '*.jpg *.jpeg *.png *.bmp *.tiff *.tif'),
            ('JPEG文件', '*.jpg *.jpeg'),
            ('PNG文件', '*.png'),
            ('BMP文件', '*.bmp'),
            ('TIFF文件', '*.tiff *.tif'),
            ('所有文件', '*.*')
        ]
        
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=filetypes
        )
        
        if files:
            self.add_images(files)
    
    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择包含图片的文件夹")
        if folder:
            # 支持的图片格式
            extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
            files = []
            
            for file_path in Path(folder).rglob('*'):
                if file_path.suffix.lower() in extensions:
                    files.append(str(file_path))
            
            if files:
                self.add_images(files)
            else:
                messagebox.showinfo("提示", "所选文件夹中没有找到支持的图片文件")
    
    def add_images(self, file_paths):
        """添加图片到列表"""
        for file_path in file_paths:
            try:
                # 验证图片文件
                with Image.open(file_path) as img:
                    img.verify()
                
                # 添加到列表
                image_info = {
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'size': os.path.getsize(file_path)
                }
                
                # 避免重复添加
                if not any(img['path'] == file_path for img in self.images):
                    self.images.append(image_info)
                    self.image_listbox.insert(tk.END, image_info['name'])
                    
            except Exception as e:
                print(f"无法加载图片 {file_path}: {e}")
        
        # 选择第一张图片
        if self.images and self.image_listbox.size() > 0:
            self.image_listbox.selection_set(0)
            self.current_image_index = 0
            self.update_preview()
        
        # 更新导出状态
        self.update_export_status()
    
    def clear_images(self):
        """清空图片列表"""
        self.images.clear()
        self.image_listbox.delete(0, tk.END)
        self.preview_canvas.delete("all")
        self.current_image_index = 0
        self.update_export_status()
    
    def on_image_select(self, event):
        """图片列表选择事件"""
        selection = self.image_listbox.curselection()
        if selection:
            self.current_image_index = selection[0]
            self.update_preview()
    
    def select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder_var.set(folder)
            self.update_export_status()
    
    def select_watermark_image(self):
        """选择水印图片"""
        filetypes = [
            ('图片文件', '*.png *.jpg *.jpeg *.bmp *.tiff *.tif'),
            ('PNG文件', '*.png'),
            ('所有文件', '*.*')
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择水印图片",
            filetypes=filetypes
        )
        
        if file_path:
            self.watermark_image_var.set(file_path)
            self.update_preview()
    
    def choose_text_color(self):
        """选择文字颜色"""
        color = colorchooser.askcolor(
            color=self.text_color_var.get(),
            title="选择文字颜色"
        )
        
        if color[1]:  # color[1] 是十六进制颜色值
            self.text_color_var.set(color[1])
            self.color_button.config(bg=color[1])
            self.update_preview()
    
    # 预览和水印处理方法
    def update_preview(self):
        """更新预览"""
        if not self.images or self.current_image_index >= len(self.images):
            return
        
        try:
            image_path = self.images[self.current_image_index]['path']
            
            # 加载原图
            with Image.open(image_path) as original_img:
                # 转换为RGBA模式以支持透明度
                if original_img.mode != 'RGBA':
                    original_img = original_img.convert('RGBA')
                
                # 创建水印图像
                watermarked_img = self.apply_watermark(original_img.copy())
                
                # 调整预览大小
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                if canvas_width <= 1 or canvas_height <= 1:
                    self.root.after(100, self.update_preview)
                    return
                
                # 计算缩放比例
                img_width, img_height = watermarked_img.size
                scale_x = (canvas_width - 20) / img_width
                scale_y = (canvas_height - 20) / img_height
                scale = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
                
                if scale < 1.0:
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    watermarked_img = watermarked_img.resize((new_width, new_height), Image.LANCZOS)
                
                # 转换为PhotoImage
                self.preview_image = ImageTk.PhotoImage(watermarked_img)
                
                # 清空画布并显示图片
                self.preview_canvas.delete("all")
                canvas_x = canvas_width // 2
                canvas_y = canvas_height // 2
                self.preview_canvas.create_image(canvas_x, canvas_y, image=self.preview_image)
                
        except Exception as e:
            print(f"预览更新失败: {e}")
    
    def apply_watermark(self, img):
        """应用水印到图片"""
        # 创建一个透明层用于绘制水印
        watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # 根据水印类型绘制
        if self.watermark_image_var.get() and os.path.exists(self.watermark_image_var.get()):
            # 图片水印
            self.draw_image_watermark(watermark_layer, img.size)
        else:
            # 文本水印
            self.draw_text_watermark(draw, img.size)
        
        # 合并水印层
        watermarked = Image.alpha_composite(img, watermark_layer)
        return watermarked
    
    def draw_text_watermark(self, draw, img_size):
        """绘制文本水印"""
        text = self.text_var.get()
        if not text:
            return
        
        # 获取字体
        try:
            font_size = self.font_size_var.get()
            font_path = self.get_font_path()
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        
        # 计算文本大小
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算位置
        x, y = self.calculate_watermark_position(img_size, (text_width, text_height))
        
        # 获取颜色和透明度
        color = self.text_color_var.get()
        opacity = int(self.text_opacity_var.get() * 255 / 100)
        
        # 转换颜色
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            text_color = (r, g, b, opacity)
        else:
            text_color = (255, 255, 255, opacity)
        
        # 绘制阴影
        if self.shadow_var.get():
            shadow_offset = max(1, font_size // 20)
            shadow_color = (0, 0, 0, opacity // 2)
            draw.text((x + shadow_offset, y + shadow_offset), text, 
                     font=font, fill=shadow_color)
        
        # 绘制描边
        if self.stroke_var.get():
            stroke_width = max(1, font_size // 30)
            stroke_color = (0, 0, 0, opacity)
            
            # 简单描边实现
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, 
                                 font=font, fill=stroke_color)
        
        # 绘制主文本
        draw.text((x, y), text, font=font, fill=text_color)
    
    def draw_image_watermark(self, watermark_layer, img_size):
        """绘制图片水印"""
        watermark_path = self.watermark_image_var.get()
        if not watermark_path or not os.path.exists(watermark_path):
            return
        
        try:
            with Image.open(watermark_path) as watermark_img:
                # 转换为RGBA
                if watermark_img.mode != 'RGBA':
                    watermark_img = watermark_img.convert('RGBA')
                
                # 缩放水印
                scale = self.image_scale_var.get() / 100.0
                new_width = int(watermark_img.width * scale)
                new_height = int(watermark_img.height * scale)
                watermark_img = watermark_img.resize((new_width, new_height), Image.LANCZOS)
                
                # 调整透明度
                opacity = self.image_opacity_var.get() / 100.0
                if opacity < 1.0:
                    # 创建透明度蒙版
                    alpha = watermark_img.split()[-1]  # 获取alpha通道
                    alpha = alpha.point(lambda p: int(p * opacity))
                    watermark_img.putalpha(alpha)
                
                # 计算位置
                x, y = self.calculate_watermark_position(img_size, watermark_img.size)
                
                # 粘贴水印
                watermark_layer.paste(watermark_img, (x, y), watermark_img)
                
        except Exception as e:
            print(f"绘制图片水印失败: {e}")
    
    def calculate_watermark_position(self, img_size, watermark_size):
        """计算水印位置"""
        img_width, img_height = img_size
        wm_width, wm_height = watermark_size
        
        # 边距
        margin = 20
        
        position = self.position_var.get()
        
        # 预设位置
        positions = {
            'top_left': (margin, margin),
            'top_center': ((img_width - wm_width) // 2, margin),
            'top_right': (img_width - wm_width - margin, margin),
            'middle_left': (margin, (img_height - wm_height) // 2),
            'center': ((img_width - wm_width) // 2, (img_height - wm_height) // 2),
            'middle_right': (img_width - wm_width - margin, (img_height - wm_height) // 2),
            'bottom_left': (margin, img_height - wm_height - margin),
            'bottom_center': ((img_width - wm_width) // 2, img_height - wm_height - margin),
            'bottom_right': (img_width - wm_width - margin, img_height - wm_height - margin)
        }
        
        if position in positions:
            return positions[position]
        else:
            # 使用手动位置
            return self.watermark_position
    
    def get_font_path(self):
        """获取字体路径"""
        font_family = self.font_family_var.get()
        
        # Windows系统字体路径
        font_paths = {
            # 中文字体
            '微软雅黑': 'C:/Windows/Fonts/msyh.ttc',
            '宋体': 'C:/Windows/Fonts/simsun.ttc',
            '黑体': 'C:/Windows/Fonts/simhei.ttf',
            '楷体': 'C:/Windows/Fonts/simkai.ttf',
            '仿宋': 'C:/Windows/Fonts/simfang.ttf',
            # 英文字体
            'Arial': 'C:/Windows/Fonts/arial.ttf',
            'Times New Roman': 'C:/Windows/Fonts/times.ttf',
            'Courier New': 'C:/Windows/Fonts/cour.ttf',
            'Helvetica': 'C:/Windows/Fonts/arial.ttf',  # 使用Arial替代
            'Georgia': 'C:/Windows/Fonts/georgia.ttf',
            'Verdana': 'C:/Windows/Fonts/verdana.ttf',
            'Tahoma': 'C:/Windows/Fonts/tahoma.ttf'
        }
        
        font_path = font_paths.get(font_family, 'C:/Windows/Fonts/msyh.ttc')
        
        # 检查字体文件是否存在
        if os.path.exists(font_path):
            return font_path
        else:
            # 尝试其他中文字体作为备选
            fallback_fonts = [
                'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/arial.ttf'   # Arial作为最后备选
            ]
            
            for fallback_font in fallback_fonts:
                if os.path.exists(fallback_font):
                    return fallback_font
            
            # 如果都不存在，返回系统默认
            return 'C:/Windows/Fonts/arial.ttf'
    
    # 鼠标交互方法
    def on_canvas_click(self, event):
        """画布点击事件"""
        self.dragging = True
        
    def on_canvas_drag(self, event):
        """画布拖拽事件"""
        if self.dragging and self.images:
            # 计算相对位置
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            # 获取原图尺寸
            image_path = self.images[self.current_image_index]['path']
            with Image.open(image_path) as img:
                img_width, img_height = img.size
                
                # 计算缩放比例
                scale_x = (canvas_width - 20) / img_width
                scale_y = (canvas_height - 20) / img_height
                scale = min(scale_x, scale_y, 1.0)
                
                # 计算实际图片在画布中的位置和大小
                scaled_width = int(img_width * scale)
                scaled_height = int(img_height * scale)
                img_x = (canvas_width - scaled_width) // 2
                img_y = (canvas_height - scaled_height) // 2
                
                # 转换鼠标位置到原图坐标
                mouse_x = event.x - img_x
                mouse_y = event.y - img_y
                
                if 0 <= mouse_x <= scaled_width and 0 <= mouse_y <= scaled_height:
                    # 转换到原图坐标系
                    orig_x = int(mouse_x / scale)
                    orig_y = int(mouse_y / scale)
                    
                    self.watermark_position = (orig_x, orig_y)
                    self.position_var.set('custom')  # 设置为自定义位置
                    self.update_preview()
    
    def on_canvas_release(self, event):
        """画布释放事件"""
        self.dragging = False
    
    def apply_position_preset(self):
        """应用预设位置"""
        self.update_preview()
    
    # 导出方法
    def export_images(self):
        """批量导出图片"""
        if not self.images:
            messagebox.showwarning("警告", "请先导入图片")
            return
        
        if not self.output_folder_var.get():
            messagebox.showwarning("警告", "请选择输出文件夹")
            return
        
        # 检查输出文件夹是否与原文件夹相同
        output_folder = self.output_folder_var.get()
        for image_info in self.images:
            original_folder = os.path.dirname(image_info['path'])
            if os.path.samefile(output_folder, original_folder):
                if not messagebox.askyesno("确认", "输出文件夹与原文件夹相同，可能会覆盖原文件。是否继续？"):
                    return
                break
        
        # 开始导出
        self.export_progress_window()
    
    def export_progress_window(self):
        """显示导出进度窗口"""
        progress_window = tk.Toplevel(self.root)
        progress_window.title("导出进度")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # 居中显示
        progress_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # 进度条
        ttk.Label(progress_window, text="正在导出图片...").pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, 
                                      maximum=len(self.images))
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_label = ttk.Label(progress_window, text="准备中...")
        status_label.pack(pady=5)
        
        # 取消按钮
        cancel_var = tk.BooleanVar()
        ttk.Button(progress_window, text="取消", 
                  command=lambda: cancel_var.set(True)).pack(pady=10)
        
        # 在新线程中执行导出
        def export_thread():
            try:
                success_count = 0
                total_count = len(self.images)
                
                for i, image_info in enumerate(self.images):
                    if cancel_var.get():
                        break
                    
                    # 更新状态
                    self.root.after(0, lambda: status_label.config(
                        text=f"正在处理: {image_info['name']}"))
                    
                    try:
                        # 处理单张图片
                        self.export_single_image(image_info)
                        success_count += 1
                    except Exception as e:
                        print(f"导出失败 {image_info['name']}: {e}")
                    
                    # 更新进度
                    self.root.after(0, lambda i=i: progress_var.set(i + 1))
                
                # 完成
                if not cancel_var.get():
                    self.root.after(0, lambda: messagebox.showinfo(
                        "完成", f"导出完成！成功: {success_count}/{total_count}"))
                
                self.root.after(0, progress_window.destroy)
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"导出过程中发生错误: {e}"))
                self.root.after(0, progress_window.destroy)
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def export_single_image(self, image_info):
        """导出单张图片"""
        # 加载原图
        with Image.open(image_info['path']) as original_img:
            # 转换为RGBA模式
            if original_img.mode != 'RGBA':
                original_img = original_img.convert('RGBA')
            
            # 应用水印
            watermarked_img = self.apply_watermark(original_img.copy())
            
            # 生成输出文件名
            output_filename = self.generate_output_filename(image_info['name'])
            output_path = os.path.join(self.output_folder_var.get(), output_filename)
            
            # 根据输出格式保存
            output_format = self.output_format_var.get()
            if output_format == 'JPEG':
                # JPEG不支持透明度，转换为RGB
                if watermarked_img.mode == 'RGBA':
                    # 创建白色背景
                    background = Image.new('RGB', watermarked_img.size, (255, 255, 255))
                    background.paste(watermarked_img, mask=watermarked_img.split()[-1])
                    watermarked_img = background
                
                watermarked_img.save(output_path, 'JPEG', 
                                   quality=self.quality_var.get(), 
                                   optimize=True)
            else:  # PNG
                watermarked_img.save(output_path, 'PNG', optimize=True)
    
    def generate_output_filename(self, original_name):
        """生成输出文件名"""
        name_without_ext = os.path.splitext(original_name)[0]
        
        naming_rule = self.naming_var.get()
        output_format = self.output_format_var.get().lower()
        
        if naming_rule == 'original':
            return f"{name_without_ext}.{output_format}"
        elif naming_rule == 'prefix':
            prefix = self.prefix_var.get()
            return f"{prefix}{name_without_ext}.{output_format}"
        else:  # suffix
            suffix = self.suffix_var.get()
            return f"{name_without_ext}{suffix}.{output_format}"
    
    # 模板管理方法
    def save_template(self):
        """保存水印模板"""
        template_name = self.template_name_var.get().strip()
        if not template_name:
            messagebox.showwarning("警告", "请输入模板名称")
            return
        
        # 收集当前设置
        template_data = {
            'text': self.text_var.get(),
            'font_family': self.font_family_var.get(),
            'font_size': self.font_size_var.get(),
            'font_bold': self.font_bold_var.get(),
            'font_italic': self.font_italic_var.get(),
            'text_color': self.text_color_var.get(),
            'text_opacity': self.text_opacity_var.get(),
            'shadow': self.shadow_var.get(),
            'stroke': self.stroke_var.get(),
            'image_path': self.watermark_image_var.get(),
            'image_opacity': self.image_opacity_var.get(),
            'image_scale': self.image_scale_var.get(),
            'position_preset': self.position_var.get(),
            'rotation': self.rotation_var.get(),
            'output_format': self.output_format_var.get(),
            'jpeg_quality': self.quality_var.get(),
            'naming_rule': self.naming_var.get(),
            'custom_prefix': self.prefix_var.get(),
            'custom_suffix': self.suffix_var.get()
        }
        
        # 保存到文件
        templates_dir = 'templates'
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        
        template_file = os.path.join(templates_dir, f"{template_name}.json")
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"模板 '{template_name}' 保存成功")
            self.template_name_var.set("")
            self.load_templates()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存模板失败: {e}")
    
    def load_templates(self):
        """加载模板列表"""
        self.template_listbox.delete(0, tk.END)
        
        templates_dir = 'templates'
        if not os.path.exists(templates_dir):
            return
        
        try:
            for filename in os.listdir(templates_dir):
                if filename.endswith('.json'):
                    template_name = os.path.splitext(filename)[0]
                    self.template_listbox.insert(tk.END, template_name)
        except Exception as e:
            print(f"加载模板列表失败: {e}")
    
    def load_template(self):
        """加载选中的模板"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要加载的模板")
            return
        
        template_name = self.template_listbox.get(selection[0])
        template_file = os.path.join('templates', f"{template_name}.json")
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # 应用模板设置
            self.apply_template_settings(template_data)
            messagebox.showinfo("成功", f"模板 '{template_name}' 加载成功")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载模板失败: {e}")
    
    def delete_template(self):
        """删除选中的模板"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的模板")
            return
        
        template_name = self.template_listbox.get(selection[0])
        
        if messagebox.askyesno("确认", f"确定要删除模板 '{template_name}' 吗？"):
            template_file = os.path.join('templates', f"{template_name}.json")
            
            try:
                os.remove(template_file)
                messagebox.showinfo("成功", f"模板 '{template_name}' 删除成功")
                self.load_templates()
                
            except Exception as e:
                messagebox.showerror("错误", f"删除模板失败: {e}")
    
    def apply_template_settings(self, template_data):
        """应用模板设置"""
        # 文本设置
        self.text_var.set(template_data.get('text', ''))
        self.font_family_var.set(template_data.get('font_family', 'Arial'))
        self.font_size_var.set(template_data.get('font_size', 36))
        self.font_bold_var.set(template_data.get('font_bold', False))
        self.font_italic_var.set(template_data.get('font_italic', False))
        self.text_color_var.set(template_data.get('text_color', '#FFFFFF'))
        self.text_opacity_var.set(template_data.get('text_opacity', 80))
        self.shadow_var.set(template_data.get('shadow', True))
        self.stroke_var.set(template_data.get('stroke', True))
        
        # 图片设置
        self.watermark_image_var.set(template_data.get('image_path', ''))
        self.image_opacity_var.set(template_data.get('image_opacity', 80))
        self.image_scale_var.set(template_data.get('image_scale', 100))
        
        # 位置设置
        self.position_var.set(template_data.get('position_preset', 'bottom_right'))
        self.rotation_var.set(template_data.get('rotation', 0))
        
        # 导出设置
        self.output_format_var.set(template_data.get('output_format', 'PNG'))
        self.quality_var.set(template_data.get('jpeg_quality', 95))
        self.naming_var.set(template_data.get('naming_rule', 'suffix'))
        self.prefix_var.set(template_data.get('custom_prefix', 'wm_'))
        self.suffix_var.set(template_data.get('custom_suffix', '_watermarked'))
        
        # 更新颜色按钮
        self.color_button.config(bg=self.text_color_var.get())
        
        # 更新预览
        self.update_preview()
    
    def save_last_settings(self):
        """保存最后使用的设置"""
        settings_file = 'last_settings.json'
        
        settings_data = {
            'text': self.text_var.get(),
            'font_family': self.font_family_var.get(),
            'font_size': self.font_size_var.get(),
            'font_bold': self.font_bold_var.get(),
            'font_italic': self.font_italic_var.get(),
            'text_color': self.text_color_var.get(),
            'text_opacity': self.text_opacity_var.get(),
            'shadow': self.shadow_var.get(),
            'stroke': self.stroke_var.get(),
            'image_path': self.watermark_image_var.get(),
            'image_opacity': self.image_opacity_var.get(),
            'image_scale': self.image_scale_var.get(),
            'position_preset': self.position_var.get(),
            'rotation': self.rotation_var.get(),
            'output_format': self.output_format_var.get(),
            'jpeg_quality': self.quality_var.get(),
            'output_folder': self.output_folder_var.get(),
            'naming_rule': self.naming_var.get(),
            'custom_prefix': self.prefix_var.get(),
            'custom_suffix': self.suffix_var.get()
        }
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def load_last_settings(self):
        """加载最后使用的设置"""
        settings_file = 'last_settings.json'
        
        if not os.path.exists(settings_file):
            return
        
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
            
            self.apply_template_settings(settings_data)
            
        except Exception as e:
            print(f"加载设置失败: {e}")


def main():
    """主函数"""
    root = tk.Tk()
    app = WatermarkApp(root)
    
    # 程序退出时保存设置
    def on_closing():
        app.save_last_settings()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 绑定窗口大小变化事件
    def on_configure(event):
        if event.widget == root:
            app.root.after(100, app.update_preview)
    
    root.bind('<Configure>', on_configure)
    
    root.mainloop()


if __name__ == "__main__":
    main()