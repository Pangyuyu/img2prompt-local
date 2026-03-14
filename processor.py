"""
主处理模块
整合各模块功能，实现完整的图片描述生成流程
"""

import threading
from pathlib import Path
from typing import List, Optional, Callable

from image_utils import get_image_info, is_supported_image
from ai_describer import ImageDescriber
from json_storage import save_image_data, load_image_data, check_exists_by_md5, get_json_path


class ProcessingStatus:
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    ERROR = "error"


class ImageProcessor:
    """图片处理器"""
    
    def __init__(
        self,
        api_url: str,
        output_dir: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        n_ctx: int = 4096,
        duplicate_strategy: str = "skip",
        api_key: Optional[str] = None,
        verbose: bool = False
    ):
        """
        初始化图片处理器
        
        Args:
            api_url: llama-server API 地址
            output_dir: 输出目录（None 表示与原图片同目录）
            temperature: 生成温度
            max_tokens: 最大生成 token 数
            n_ctx: 上下文长度
            duplicate_strategy: 去重策略（skip/overwrite）
            api_key: API 密钥（可选）
            verbose: 是否输出详细信息
        """
        self.api_url = api_url
        self.output_dir = output_dir
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.n_ctx = n_ctx
        self.duplicate_strategy = duplicate_strategy
        self.verbose = verbose
        self.api_key = api_key
        
        self.describer = ImageDescriber(
            api_url=api_url,
            temperature=temperature,
            max_tokens=max_tokens,
            n_ctx=n_ctx,
            api_key=api_key
        )
        
        self._stop_flag = False
        self._current_image: Optional[str] = None
    
    def process_images(
        self,
        image_paths: List[str],
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
        result_callback: Optional[Callable[[str, str, dict], None]] = None
    ):
        """
        批量处理图片
        
        Args:
            image_paths: 图片路径列表
            progress_callback: 进度回调函数 (current, total, status, image_path)
            result_callback: 结果回调函数 (status, image_path, data)
        """
        self._stop_flag = False
        
        # 过滤支持的图片格式
        valid_images = [p for p in image_paths if is_supported_image(p)]
        total = len(valid_images)
        
        if total == 0:
            if progress_callback:
                progress_callback(0, 0, "没有支持的图片格式", "")
            return
        
        # 测试连接
        if progress_callback:
            progress_callback(0, total, "正在连接服务...", "")
        
        if not self.describer.test_connection():
            if progress_callback:
                progress_callback(0, total, "无法连接到 API 服务", "")
            return
        
        try:
            for i, image_path in enumerate(valid_images):
                if self._stop_flag:
                    break
                
                self._current_image = image_path
                status, data = self._process_single_image(image_path)
                
                if progress_callback:
                    progress_callback(i + 1, total, self._get_status_text(status), image_path)
                
                if result_callback:
                    result_callback(status, image_path, data)
        
        finally:
            self._current_image = None
    
    def _process_single_image(self, image_path: str) -> tuple:
        """
        处理单张图片

        Args:
            image_path: 图片路径

        Returns:
            (status, data) 状态和数据
        """
        try:
            # 获取图片信息
            image_info = get_image_info(image_path)
            md5_hash = image_info["md5"]

            # 获取 JSON 保存路径（使用 MD5 作为文件名）
            json_path = get_json_path(image_path, md5_hash, self.output_dir)
            
            # 检查是否已存在
            existing_data = load_image_data(json_path)
            if existing_data:
                if self.duplicate_strategy == "skip":
                    return ProcessingStatus.SKIPPED, existing_data
                # overwrite: 继续处理
            
            # 生成描述
            result = self.describer.describe_image(image_path)

            # 保存数据
            save_image_data(
                image_info=image_info,
                description=result["description"],
                tags=result["tags"],
                json_path=json_path,
                compressed=result.get("compressed", False)
            )

            data = {
                **image_info,
                "description": result["description"],
                "tags": result["tags"],
                "compressed": result.get("compressed", False),
                "json_path": json_path
            }
            
            return ProcessingStatus.COMPLETED, data
            
        except Exception as e:
            return ProcessingStatus.ERROR, {"error": str(e)}
    
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
    
    def stop(self):
        """停止处理"""
        self._stop_flag = True


class ProcessingThread(threading.Thread):
    """处理线程"""
    
    def __init__(
        self,
        processor: ImageProcessor,
        image_paths: List[str],
        progress_callback: Optional[Callable] = None,
        result_callback: Optional[Callable] = None
    ):
        super().__init__()
        self.processor = processor
        self.image_paths = image_paths
        self.progress_callback = progress_callback
        self.result_callback = result_callback
    
    def run(self):
        """线程运行方法"""
        self.processor.process_images(
            image_paths=self.image_paths,
            progress_callback=self.progress_callback,
            result_callback=self.result_callback
        )
