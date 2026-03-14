# PyInstaller 打包配置

## 📦 打包为 EXE

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 一键打包命令

```bash
# 在项目根目录执行
pyinstaller --name="图片描述生成工具" ^
            --windowed ^
            --onefile ^
            --icon=icon.ico ^
            --add-data "README.md;." ^
            --hidden-import customtkinter ^
            --hidden-import PIL ^
            --hidden-import requests ^
            main.py
```

### 3. 分步打包（推荐）

#### 第一步：生成 spec 文件

```bash
pyi-makespec --windowed --onefile main.py
```

#### 第二步：编辑 `main.spec`

```python
# main.spec
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('REQUIREMENTS.md', '.'),
        ('WORKFLOW.md', '.'),
        ('.ai-metadata.toml', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'requests',
        'ctk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='图片描述生成工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # 图标文件
)
```

#### 第三步：执行打包

```bash
pyinstaller main.spec
```

---

## 📁 打包后的文件结构

### 开发环境
```
xing-Images-read/
├── main.py
├── data_viewer.py
├── processor.py
├── ai_describer.py
├── image_utils.py
├── json_storage.py
├── requirements.txt
├── ...
└── dist/
    └── 图片描述生成工具.exe  ← 打包后的单文件
```

### 用户环境
```
用户电脑/
└── 图片描述生成工具.exe  ← 双击即可运行
```

---

## ⚙️ 打包选项说明

| 参数 | 说明 | 推荐 |
|------|------|------|
| `--name` | EXE 文件名 | 图片描述生成工具 |
| `--windowed` | 无控制台窗口 | ✅ 必须 |
| `--onefile` | 打包为单文件 | ✅ 推荐 |
| `--onefile` | 打包为文件夹 | ❌ 不推荐（文件多） |
| `--icon` | 程序图标 | 可选 |
| `--console` | 显示控制台 | ❌ 不要 |
| `--hidden-import` | 隐藏导入 | 按需添加 |

---

## 🎨 添加程序图标

### 准备图标文件

1. 准备 256x256 PNG 图片
2. 转换为 ICO 格式：
   ```bash
   pip install pillow
   python -c "from PIL import Image; img=Image.open('icon.png'); img.save('icon.ico')"
   ```

### 使用图标

```bash
pyinstaller --icon=icon.ico ...
```

---

## 📦 打包大小估算

### 包含内容
- Python 运行时：~15MB
- customtkinter：~5MB
- Pillow：~8MB
- requests + 依赖：~3MB
- 你的代码：~0.5MB

### 总计
- **压缩后（UPX）**：~25-30MB
- **未压缩**：~35-40MB

---

## ⚡ 优化建议

### 1. 使用 UPX 压缩

```bash
# 安装 UPX
# 下载地址：https://github.com/upx/upx/releases

# 打包时自动压缩
pyinstaller --upx-dir=upx ...
```

**效果**：减少 30-50% 体积

### 2. 排除不必要的模块

```python
# main.spec
excludes=[
    'tkinter',  # 使用 customtkinter，排除 tkinter
    'matplotlib',
    'numpy',  # 如果没用到
    'scipy',
]
```

### 3. 分离数据文件

```bash
# 不打包文档，单独分发
--add-data "README.md;."
```

---

## 🚨 常见问题

### 1. 打包后运行报错

**问题**：找不到模块

**解决**：
```bash
# 添加隐藏导入
--hidden-import 模块名
```

### 2. 打包后图片不显示

**问题**：数据文件未打包

**解决**：
```bash
--add-data "source_path;dest_path"
# Windows 用分号，Mac/Linux 用冒号
```

### 3. 启动速度慢

**问题**：单文件解压慢

**解决**：
```bash
# 改为单目录模式
pyinstaller --onedir ...
```

**对比**：
- `--onefile`：单文件，启动慢（需解压），便于分发
- `--onedir`：多文件，启动快，体积稍大

### 4. 杀毒软件误报

**原因**：PyInstaller 打包的 EXE 常被误报

**解决**：
1. 添加数字签名
2. 加入杀毒软件白名单
3. 使用代码签名证书

---

## 📋 完整打包脚本

### Windows 批处理

```batch
@echo off
echo 开始打包...

:: 清理旧文件
rmdir /s /q build dist
del /q main.spec

:: 安装依赖
pip install -r requirements.txt
pip install pyinstaller

:: 打包
pyinstaller --name="图片描述生成工具" ^
            --windowed ^
            --onefile ^
            --icon=icon.ico ^
            --add-data "README.md;." ^
            --add-data "REQUIREMENTS.md;." ^
            --add-data "WORKFLOW.md;." ^
            --hidden-import customtkinter ^
            --hidden-import PIL ^
            --hidden-import requests ^
            main.py

echo 打包完成！
echo EXE 文件位置：dist\图片描述生成工具.exe
pause
```

### 保存为 `build.bat`，双击即可打包

---

## 🎯 推荐配置

### 个人使用（最小体积）

```bash
pyinstaller --name="图片描述生成工具" ^
            --windowed ^
            --onefile ^
            --upx-dir=upx ^
            main.py
```

### 分发使用（包含文档）

```bash
pyinstaller --name="图片描述生成工具" ^
            --windowed ^
            --onefile ^
            --icon=icon.ico ^
            --add-data "README.md;." ^
            --add-data "PERFORMANCE.md;." ^
            main.py
```

### 开发调试（多文件模式）

```bash
pyinstaller --name="图片描述生成工具" ^
            --windowed ^
            --onedir ^
            --console ^
            main.py
```

---

## 📤 分发建议

### 1. GitHub Release

```
Release v1.0.0/
├── 图片描述生成工具.exe
├── README.md
├── 使用说明.pdf
└── 更新日志.md
```

### 2. 压缩包分发

```
图片描述生成工具_v1.0.0.zip
├── 图片描述生成工具.exe
├── README.md
└── 示例图片/
    └── sample.jpg
```

---

## 🔐 代码保护（可选）

### 1. 字节码混淆

```bash
pip install pyarmor
pyarmor gen main.py
```

### 2. 加密打包

```bash
pyinstaller --key=your_secret_key ...
```

**注意**：加密会影响性能，一般不需要

---

*最后更新：2026-03-14*
