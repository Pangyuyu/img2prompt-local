"""
图片信息提取模块
提取图片的 MD5、尺寸、大小、格式等基本信息
"""

import hashlib
import os
from pathlib import Path
from PIL import Image


def calculate_md5(file_path: str) -> str:
    """计算文件的 MD5 哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_image_info(file_path: str) -> dict:
    """
    获取图片的完整信息
    
    Args:
        file_path: 图片文件路径
        
    Returns:
        包含图片信息的字典
    """
    path = Path(file_path)
    
    # 基本信息
    file_size = path.stat().st_size
    file_format = path.suffix.lower().lstrip('.')
    
    # 计算 MD5
    md5_hash = calculate_md5(file_path)
    
    # 使用 Pillow 获取图片尺寸和格式
    with Image.open(file_path) as img:
        width, height = img.size
        img_format = img.format or file_format.upper()
    
    return {
        "md5": md5_hash,
        "source_path": str(path.absolute()),
        "width": width,
        "height": height,
        "size_bytes": file_size,
        "format": img_format
    }


def is_supported_image(file_path: str) -> bool:
    """
    检查文件是否是支持的图片格式
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否是支持的图片格式
    """
    supported_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
    return Path(file_path).suffix.lower() in supported_extensions


def get_images_from_directory(directory: str) -> list:
    """
    从目录中获取所有支持的图片文件
    
    Args:
        directory: 目录路径
        
    Returns:
        图片文件路径列表
    """
    images = []
    dir_path = Path(directory)
    
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.bmp', '*.gif']:
        images.extend(dir_path.glob(ext))
        images.extend(dir_path.glob(ext.upper()))
    
    return [str(img) for img in images]
