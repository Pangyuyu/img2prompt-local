"""
AI 描述生成模块
通过 HTTP API 调用 llama-server 多模态服务对图片进行描述
支持大图片自动压缩
"""

import base64
from typing import Optional, List, Tuple
import requests
from PIL import Image
import io


# 默认的图片描述 prompt 模板
DEFAULT_DESCRIPTION_PROMPT = """请详细描述这张图片的内容，包括：
1. 主要主体和物体
2. 场景和环境
3. 颜色和光线
4. 构图和视角
5. 氛围和情感

请用一段连贯的文字描述，适合用作 AI 绘画的 prompt。描述要具体、生动、详细。

图片描述："""


class ImageDescriber:
    """图片描述生成器 - 通过 llama-server API"""

    def __init__(
        self,
        api_url: str = "http://localhost:8080",
        temperature: float = 0.7,
        max_tokens: int = 512,
        n_ctx: int = 4096,
        api_key: Optional[str] = None,
        compress_size: int = 5 * 1024 * 1024,  # 5MB 默认压缩阈值
        compress_quality: int = 85
    ):
        """
        初始化图片描述生成器

        Args:
            api_url: llama-server API 地址
            temperature: 生成温度（越高越随机）
            max_tokens: 最大生成 token 数
            n_ctx: 上下文长度
            api_key: API 密钥（可选）
            compress_size: 超过此大小（字节）的图片会被压缩，默认 5MB
            compress_quality: 压缩质量 (1-100)，默认 85
        """
        self.api_url = api_url.rstrip('/')
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.n_ctx = n_ctx
        self.api_key = api_key
        self.compress_size = compress_size
        self.compress_quality = compress_quality
        self.session = requests.Session()

        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    def _encode_image_to_base64(self, image_path: str) -> Tuple[str, bool]:
        """
        将图片编码为 base64，如果图片过大则自动压缩

        Args:
            image_path: 图片路径

        Returns:
            (base64 编码的图片数据，是否被压缩)
        """
        import os
        file_size = os.path.getsize(image_path)
        compressed = False

        # 检查是否需要压缩
        if file_size > self.compress_size:
            return self._encode_compressed_image(image_path), True

        # 不需要压缩
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        return image_data, False

    def _encode_compressed_image(self, image_path: str) -> str:
        """
        压缩图片并编码为 base64

        Args:
            image_path: 图片路径

        Returns:
            base64 编码的压缩后图片数据
        """
        try:
            # 打开图片
            with Image.open(image_path) as img:
                # 转换为 RGB 模式（处理 PNG 透明等情况）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # 压缩并编码
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=self.compress_quality, optimize=True)
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return image_data
        except Exception as e:
            print(f"压缩图片失败：{e}")
            # 如果压缩失败，返回原图
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
    
    def _get_image_media_type(self, image_path: str) -> str:
        """
        获取图片的 MIME 类型
        
        Args:
            image_path: 图片路径
            
        Returns:
            MIME 类型
        """
        from pathlib import Path
        ext = Path(image_path).suffix.lower()
        
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.gif': 'image/gif'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def describe_image(
        self,
        image_path: str,
        prompt_template: Optional[str] = None
    ) -> dict:
        """
        对单张图片生成描述

        Args:
            image_path: 图片路径
            prompt_template: 自定义 prompt 模板（可选）

        Returns:
            包含 description、tags、compressed 的字典
        """
        prompt = prompt_template or DEFAULT_DESCRIPTION_PROMPT

        # 获取图片信息（包括是否被压缩）
        image_base64, compressed = self._encode_image_to_base64(image_path)
        media_type = self._get_image_media_type(image_path)
        data_uri = f"data:{media_type};base64,{image_base64}"

        try:
            # 调用 llama-server API (OpenAI 兼容格式)
            response = self.session.post(
                f"{self.api_url}/v1/chat/completions",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": data_uri}},
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                },
                timeout=120
            )
            response.raise_for_status()

            result = response.json()
            description = result["choices"][0]["message"]["content"].strip()

            # 从描述中提取标签（简单实现）
            tags = self._extract_tags(description)

            return {
                "description": description,
                "tags": tags,
                "compressed": compressed  # 标记是否被压缩处理
            }

        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"无法连接到 API 服务：{self.api_url}")
        except requests.exceptions.Timeout:
            raise RuntimeError("API 请求超时")
        except Exception as e:
            raise RuntimeError(f"生成描述失败：{e}")
    
    def _extract_tags(self, description: str) -> List[str]:
        """
        从描述中提取关键词标签
        
        Args:
            description: 图片描述文本
            
        Returns:
            标签列表
        """
        # 简单实现：可以后续使用 NLP 模型或关键词提取算法优化
        return []
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接是否成功
        """
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
