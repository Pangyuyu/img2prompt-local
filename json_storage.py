"""
JSON 数据存取模块
负责保存和读取图片描述数据

JSON 文件命名规则：使用 MD5 哈希值作为文件名
格式：{md5}.json
这样可以避免不同目录中同名文件的冲突
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict


def get_json_path(image_path: str, md5_hash: str, output_dir: Optional[str] = None) -> str:
    """
    获取 JSON 文件的保存路径

    Args:
        image_path: 原图片路径
        md5_hash: 图片 MD5 哈希值（用于文件名）
        output_dir: 输出目录（可选，默认与原图片同目录）

    Returns:
        JSON 文件路径
    """
    # 使用 MD5 作为文件名，避免不同目录中同名文件的冲突
    json_filename = f"{md5_hash}.json"

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return str(output_path / json_filename)
    else:
        return str(Path(image_path).parent / json_filename)


def get_json_display_name(json_path: str) -> str:
    """
    获取 JSON 文件的显示名称（用于列表显示）
    格式：原图片名 (MD5 前 8 位).json

    Args:
        json_path: JSON 文件路径

    Returns:
        显示名称
    """
    try:
        data = load_image_data(json_path)
        if data:
            source_path = data.get("source_path", "")
            md5 = data.get("md5", "")
            if source_path:
                original_name = Path(source_path).name
                md5_short = md5[:8] if md5 else "unknown"
                return f"{original_name} ({md5_short})"
    except:
        pass

    # 如果无法读取，返回文件名
    return Path(json_path).name


def save_image_data(
    image_info: Dict,
    description: str,
    tags: list,
    json_path: str,
    compressed: bool = False
) -> bool:
    """
    保存图片描述数据到 JSON 文件

    Args:
        image_info: 图片基本信息（来自 image_utils.get_image_info）
        description: AI 生成的描述
        tags: 标签列表
        json_path: JSON 文件保存路径
        compressed: 图片是否被压缩处理

    Returns:
        保存是否成功
    """
    now = datetime.now().isoformat()

    data = {
        "md5": image_info["md5"],
        "source_path": image_info["source_path"],
        "width": image_info["width"],
        "height": image_info["height"],
        "size_bytes": image_info["size_bytes"],
        "format": image_info["format"],
        "original_filename": Path(image_info["source_path"]).name,
        "description": description,
        "tags": tags,
        "compressed": compressed,  # 标记是否被压缩处理
        "created_at": now,
        "updated_at": now
    }

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存 JSON 失败：{e}")
        return False


def load_image_data(json_path: str) -> Optional[Dict]:
    """
    从 JSON 文件加载图片描述数据
    
    Args:
        json_path: JSON 文件路径
        
    Returns:
        数据字典，如果文件不存在或解析失败则返回 None
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def update_image_data(
    json_path: str,
    description: Optional[str] = None,
    tags: Optional[list] = None
) -> bool:
    """
    更新已有的图片描述数据
    
    Args:
        json_path: JSON 文件路径
        description: 新的描述（可选）
        tags: 新的标签（可选）
        
    Returns:
        更新是否成功
    """
    data = load_image_data(json_path)
    if data is None:
        return False
    
    if description is not None:
        data["description"] = description
    if tags is not None:
        data["tags"] = tags
    
    data["updated_at"] = datetime.now().isoformat()
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"更新 JSON 失败：{e}")
        return False


def check_exists_by_md5(md5_hash: str, output_dir: str) -> Optional[str]:
    """
    根据 MD5 检查是否已存在处理过的记录
    
    Args:
        md5_hash: 图片 MD5 哈希值
        output_dir: 输出目录
        
    Returns:
        如果存在则返回 JSON 文件路径，否则返回 None
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        return None
    
    for json_file in output_path.glob("*.json"):
        data = load_image_data(str(json_file))
        if data and data.get("md5") == md5_hash:
            return str(json_file)
    
    return None
