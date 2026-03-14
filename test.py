#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证基本功能
"""

import sys
from pathlib import Path

# 测试导入
print("=" * 50)
print("测试模块导入...")
print("=" * 50)

try:
    from image_utils import get_image_info, is_supported_image, calculate_md5
    print("✓ image_utils 导入成功")
except ImportError as e:
    print(f"✗ image_utils 导入失败：{e}")
    sys.exit(1)

try:
    from json_storage import save_image_data, load_image_data, get_json_path
    print("✓ json_storage 导入成功")
except ImportError as e:
    print(f"✗ json_storage 导入失败：{e}")
    sys.exit(1)

try:
    from ai_describer import ImageDescriber, DEFAULT_DESCRIPTION_PROMPT
    print("✓ ai_describer 导入成功")
except ImportError as e:
    print(f"⚠ ai_describer 导入失败：{e} (跳过 AI 功能测试)")

try:
    from processor import ImageProcessor, ProcessingStatus
    print("✓ processor 导入成功")
except ImportError as e:
    print(f"⚠ processor 导入失败：{e} (跳过)")

# 测试 GUI 导入
print("\n" + "=" * 50)
print("测试 GUI 模块导入...")
print("=" * 50)

try:
    import customtkinter as ctk
    print(f"✓ customtkinter 导入成功 (版本：{ctk.__version__})")
except ImportError as e:
    print(f"✗ customtkinter 导入失败：{e}")

try:
    from PIL import Image
    print(f"✓ Pillow 导入成功 (版本：{Image.__version__})")
except ImportError as e:
    print(f"✗ Pillow 导入失败：{e}")

# 测试图片信息提取
print("\n" + "=" * 50)
print("测试图片信息提取...")
print("=" * 50)

# 查找测试图片
test_image = None
for ext in ['*.jpg', '*.png', '*.jpeg', '*.webp', '*.bmp']:
    images = list(Path('.').glob(ext))
    if images:
        test_image = str(images[0])
        break

if test_image:
    print(f"找到测试图片：{test_image}")
    try:
        info = get_image_info(test_image)
        print(f"✓ 图片信息提取成功:")
        print(f"  - MD5: {info['md5'][:16]}...")
        print(f"  - 尺寸：{info['width']}x{info['height']}")
        print(f"  - 大小：{info['size_bytes']} 字节")
        print(f"  - 格式：{info['format']}")
    except Exception as e:
        print(f"✗ 图片信息提取失败：{e}")
else:
    print("⚠ 未找到测试图片，跳过此测试")

# 测试 JSON 存储
print("\n" + "=" * 50)
print("测试 JSON 存储...")
print("=" * 50)

test_data = {
    "md5": "test1234567890",
    "source_path": "D:/test/image.jpg",
    "width": 1920,
    "height": 1080,
    "size_bytes": 524288,
    "format": "JPEG"
}

# 使用新的 API，传入 MD5
json_path = get_json_path("D:/test/image.jpg", "test1234567890", "./output")
print(f"JSON 保存路径：{json_path}")

try:
    save_image_data(
        image_info=test_data,
        description="测试描述",
        tags=["测试", "标签"],
        json_path=json_path + ".json"
    )
    print("✓ JSON 保存成功")
    
    loaded = load_image_data(json_path + ".json")
    if loaded:
        print(f"✓ JSON 读取成功，描述：{loaded['description']}")
except Exception as e:
    print(f"✗ JSON 操作失败：{e}")

# 测试 API 连接
print("\n" + "=" * 50)
print("测试 API 连接...")
print("=" * 50)

try:
    from ai_describer import ImageDescriber
    
    api_url = "http://localhost:8080"
    describer = ImageDescriber(api_url=api_url)
    
    print(f"测试 API 地址：{api_url}")
    if describer.test_connection():
        print("✓ API 连接成功")
    else:
        print("⚠ API 未连接（llama-server 可能未启动）")
except Exception as e:
    print(f"⚠ API 测试失败：{e}")

print("\n" + "=" * 50)
print("测试完成！")
print("=" * 50)
