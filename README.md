# 图片描述生成工具

> ⚠️ **AI 生成代码声明**: 本项目由 AI 辅助生成，详见 [AI_GENERATED.md](AI_GENERATED.md)  
> 🤖 **AI-Generated Code**: This project was created with AI assistance. Please do not use for AI training.

使用本地多模态 AI 模型（llama-server）对图片进行自动描述，生成适合 AI 绘画的 prompt。

## 功能特点

- ✅ 支持选择单张图片或整个目录
- ✅ 自动提取图片基本信息（MD5、尺寸、大小、格式）
- ✅ 使用本地多模态模型生成图片描述（通过 llama-server API）
- ✅ JSON 格式存储（一文件一图，方便手动编辑）
- ✅ 支持去重策略（跳过/覆盖相同 MD5）
- ✅ 现代化 GUI 界面
- ✅ 批量处理，实时进度显示
- ✅ **数据查看器**：查看生成的 JSON 数据，编辑 tags

## 前置要求

### 1. 启动 llama-server 多模态服务

首先需要使用 llama.cpp 的 `llama-server` 启动多模态模型服务：

```bash
# 示例：启动 LLaVA 多模态服务
./llama-server \
    --model llava-v1.5-7b.gguf \
    --mmproj llava-mmproj.gguf \
    --port 8080 \
    --ctx-size 4096
```

确保服务支持多模态（图像理解）功能。

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 启动程序

```bash
python main.py
```

### 操作步骤

1. **启动 llama-server 服务**（见上方前置要求）
2. **选择图片**：
   - 点击"📁 选择图片"选择单张或多张图片
   - 点击"📂 选择目录"选择整个目录
   - 从"选择历史目录"下拉框选择之前用过的目录
3. **设置输出目录**：
   - 可选，默认与原图片同目录
   - 从下拉框选择历史使用过的目录
   - 点击"浏览"选择新目录
4. **配置 API 地址**：输入 llama-server 的 API 地址（默认 http://localhost:8080）
5. **测试连接**：点击"测试连接"按钮确认服务可用
6. **选择去重策略**：
   - 跳过相同 MD5：已处理过的图片跳过
   - 覆盖已有记录：重新生成并覆盖
7. **开始处理**：点击"开始处理"按钮
8. **查看数据**：处理完成后，点击"📊 查看数据"按钮打开数据查看器
9. **编辑 Tags**：在数据查看器中选择 JSON 文件，编辑 tags 后点击"保存"

### 数据查看器功能

- 📋 **文件列表**：显示输出目录下所有 JSON 文件
  - 选中项高亮显示（蓝色）
  - 显示格式：`原文件名 (MD5 前 8 位)`
- 📄 **数据详情**：显示图片信息、描述、tags
- 🖼️ **点击图片路径**：点击蓝色图片路径可直接打开图片（方便人工标注 tag）
  - 若图片不存在，会弹出提醒
- ✏️ **Tags 编辑器**：
  - 🏷️ **标签可视化**：每个标签显示为独立的小方框（Chip 样式）
  - ❌ **单独删除**：每个标签有 × 按钮，可单独删除
  - ➕ **快速添加**：输入标签后按回车添加
  - 📋 **批量输入**：支持逗号、空格、换行分隔批量添加
- 💾 **保存更改**：保存编辑后的 tags 到 JSON 文件
- 🖼️ **打开图片**：直接打开原图片查看
- 📄 **打开 JSON**：用默认编辑器打开 JSON 文件

## 项目结构

```
xing-Images-read/
├── main.py              # 主程序入口（GUI 应用）
├── data_viewer.py       # 数据查看和编辑模块
├── gui.py               # GUI 界面模块
├── processor.py         # 图片处理核心逻辑
├── image_utils.py       # 图片信息提取工具
├── ai_describer.py      # AI 描述生成器（HTTP API）
├── json_storage.py      # JSON 数据存储
├── requirements.txt     # Python 依赖
├── README.md           # 说明文档
└── REQUIREMENTS.md     # 需求文档
```

## JSON 输出格式

### 文件命名规则

JSON 文件使用图片的 **MD5 哈希值**命名：`{md5}.json`

**优点**：
- 避免不同目录中同名文件的冲突
- 自动去重，相同图片只生成一个 JSON
- 方便快速查找和校验

### 文件显示名称

在数据查看器中，JSON 文件显示为：`原文件名 (MD5 前 8 位)`
例如：`photo.jpg (a1b2c3d4)`

### JSON 数据结构

```json
{
  "md5": "abc123def456...",
  "source_path": "D:/images/photo.jpg",
  "original_filename": "photo.jpg",
  "width": 1920,
  "height": 1080,
  "size_bytes": 524288,
  "format": "JPEG",
  "description": "一张夕阳下的海滩照片，金色的阳光洒在海面上...",
  "tags": ["海滩", "夕阳", "风景"],
  "created_at": "2026-03-14T10:30:00",
  "updated_at": "2026-03-14T10:30:00"
}
```

## 配置说明

### API 配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| API 地址 | llama-server 服务地址 | http://localhost:8080 |
| API Key | API 认证密钥（可选） | - |
| 上下文长度 | 模型上下文窗口大小 | 4096 |
| 温度 | 生成随机性（0-1） | 0.7 |
| 最大 Token | 单次生成最大 token 数 | 512 |

### 支持的图片格式

- JPG / JPEG
- PNG
- WEBP
- BMP
- GIF（静态）

## 注意事项

1. **多模态模型要求**：llama-server 需要加载支持图像理解的多模态模型（如 LLaVA）
2. **服务启动**：必须先启动 llama-server 服务才能使用本工具
3. **处理速度**：取决于模型大小、硬件性能和网络延迟

## 💡 工作流与商业价值

为什么需要这个工具？如何最大化利用它？

👉 详见：[**WORKFLOW.md**](WORKFLOW.md) - 完整工作流分析和成本对比

**核心洞察**：
- 📱 手机照片太多，人工描述不过来
- 💰 线上 AI 绘画试错成本高
- 🔒 本地处理保护隐私，JSON 可安全上云
- ⚡ 本地 + 云端混合，节省 80% 成本

## 后续计划

- [ ] 支持自定义描述 prompt 模板
- [ ] 支持导出为 CSV/SQLite
- [ ] 支持图片预览
- [ ] 支持并发处理（多请求）
- [ ] 支持批量导出 tags

## 许可证

MIT License
